init_hospital();
describe("models", function() {
    describe("Initializing data", function() {
        it("should have the persons and wards set", function() {
            expect(models.persons.length).toBe(3);
            expect(models.wards.length).toBe(7);
            var person_a = models.persons.get('A');
            expect(person_a.get('name')).toBe('Anton');
            var ward_a = models.wards.get('A');
            expect(ward_a.get('name')).toBe('Ward A');
            expect(ward_a.get('min')).toBe(1);
            expect(ward_a.get('max')).toBe(2);
            expect(ward_a.get('continued')).toBe(true);
        });
    });
    describe("Person", function() {
        describe("calculating availability", function() {
            var before = new Date(2016, 1, 29);
            var firstday = new Date(2016, 2, 1);
            var lastday = new Date(2016, 2, 31);
            var after = new Date(2016, 3, 1);
            var start_date = [2016, 2, 1];
            var end_date = [2016, 2, 31];
            var person;
            it("should calculate availability for a person with start_date and end_date", function() {
                person = new models.Person({start_date: start_date, end_date: end_date, });
                expect(person.is_available(before  )).toBe(false);
                expect(person.is_available(firstday)).toBe(true);
                expect(person.is_available(lastday )).toBe(true);
                expect(person.is_available(after   )).toBe(false);
            });
            it("should calculate availability for a person with start_date", function() {
                person = new models.Person({ start_date: start_date });
                expect(person.is_available(before  )).toBe(false);
                expect(person.is_available(firstday)).toBe(true);
                expect(person.is_available(lastday )).toBe(true);
                expect(person.is_available(after   )).toBe(true);
            });
            it("should calculate availability for a person with end_date", function() {
                person = new models.Person({ end_date: end_date });
                expect(person.is_available(before  )).toBe(true);
                expect(person.is_available(firstday)).toBe(true);
                expect(person.is_available(lastday )).toBe(true);
                expect(person.is_available(after   )).toBe(false);
            });
            it("should calculate availability for a person without start_date or end_date", function() {
                person = new models.Person();
                expect(person.is_available(before  )).toBe(true);
                expect(person.is_available(firstday)).toBe(true);
                expect(person.is_available(lastday )).toBe(true);
                expect(person.is_available(after   )).toBe(true);
            });
        });
    });
    describe("Staffing", function() {
        describe("calculate who can be planned", function() {
            var today, yesterday, staffing_a, person_a;
            beforeEach(function() {
                yesterday = new models.Day({ date: new Date(2016, 8, 19) });
                today = new models.Day({ 
                    date: new Date(2016, 8, 20),
                    yesterday: yesterday,
                });
                staffing_a = today.ward_staffings.A;
                person_a = models.persons.get('A');
            });
            it("usually persons can be planned", function() {
                expect(staffing_a.can_be_planned(person_a)).toBeTruthy();
            });
            it("who is on leave, cannot be planned", function() {
                today.ward_staffings.L.add(person_a);
                expect(staffing_a.can_be_planned(person_a)).toBeFalsy();
            });
            it("who was on call last night, cannot be planned", function() {
                yesterday.ward_staffings.N.add(person_a);
                expect(staffing_a.can_be_planned(person_a)).toBeFalsy();
            });
            it("for 'on leave', everyone can be planned", function() {
                var staffing_l = today.ward_staffings.L;
                expect(staffing_l.can_be_planned(person_a)).toBeTruthy();
                // nightshift yesterday
                yesterday.ward_staffings.N.add(person_a);
                expect(staffing_l.can_be_planned(person_a)).toBeTruthy();
                // on leave
                today.ward_staffings.L.add(person_a);
                expect(staffing_l.can_be_planned(person_a)).toBeTruthy();
            });
            it("'anonymous' persons can be planned afer a call shift", function() {
                var anon = models.persons.get('Other');
                expect(staffing_a.can_be_planned(anon)).toBeTruthy();
                yesterday.ward_staffings.N.add(anon);
                expect(staffing_a.can_be_planned(anon)).toBeTruthy();
            });
        });
    });
    describe("Day", function() {
        it("should be initialized properly", function() {
            var today = new models.Day({ date: new Date(2015, 7, 7) });
            expect(today.id).toEqual('20150807');
            expect(today.persons_duties).toBeDefined();
            expect(today.persons_duties.A.length).toBe(0);
            expect(today.ward_staffings).toBeDefined();
            expect(today.ward_staffings.A.length).toBe(0);
        });
        describe("check availability:", function() {
            function check_availability (action, nr_avail, first_avail) {
                // perform an action
                // then check the number of available persons 
                // and the name of the first available (if given)
                var yesterday = new models.Day({
                    date: new Date(2015, 7, 6),  // Thursday
                });
                var today = new models.Day({
                    date: new Date(2015, 7, 7),  // Friday
                    yesterday: yesterday,
                });
                action(today, yesterday);
                var available = today.get_available(models.wards.get('A'));
                expect(available.length).toEqual(nr_avail);
                if (first_avail) {
                    expect(available[0].id).toEqual(first_avail);
                }
            }
            it("usually everybody is available", function() {
                check_availability(function(today, yesterday) {},
                3);
            });
            it("who is on leave isn't available", function() {
                check_availability(function(today, yesterday) {
                    today.ward_staffings.L.add(models.persons.get('A'));
                },
                2, 'B');
            });
            it("who was on nightshift yesterday isn't available", function() {
                check_availability(function(today, yesterday) {
                    yesterday.ward_staffings.N.add(models.persons.get('A'));
                },
                2, 'B');
            });
            it("who is on nightshift today is available", function() {
                check_availability(function(today, yesterday) {
                    today.ward_staffings.N.add(models.persons.get('A'));
                },
                3);
            });
            it("who is planned for a different ward today is available", function() {
                check_availability(function(today, yesterday) {
                    today.ward_staffings.B.add(models.persons.get('A'));
                },
                3);
            });
        });
        describe("need for staffing", function() {
            it("should respect free days", function() {
                var sunday = new models.Day({
                    date: new Date(2015, 7, 2),
                });
                var monday = new models.Day({
                    date: new Date(2015, 7, 3),
                });
                expect(sunday.ward_staffings.A.no_staffing).toBeTruthy();
                expect(sunday.ward_staffings.F.no_staffing).toBeFalsy();
                expect(monday.ward_staffings.A.no_staffing).toBeFalsy();
                expect(monday.ward_staffings.F.no_staffing).toBeTruthy();
            });
        });
        describe("interaction with previous planning", function() {
            var yesterday, today, tomorrow;
            beforeEach(function() {
                yesterday = new models.Day({
                    date: new Date(2015, 7, 3),
                });
                today = new models.Day({
                    date: new Date(2015, 7, 4),
                    yesterday: yesterday,
                });
                tomorrow = new models.Day({
                    date: new Date(2015, 7, 5),
                    yesterday: today,
                });
            });
            function test_staffing (day, staffing, total, displayed) {
                var st = day.ward_staffings[staffing];
                expect(st.length).toBe(total);
                expect(st.displayed.length).toBe(displayed);
            }
            it("should strike off yesterdays nightshift for today, "+
                "and continue the duties tomorrow, "+
                "if they are to be continued", function() {
                var person_a = models.persons.get('A');
                yesterday.ward_staffings.A.add(person_a, {continued: true});
                yesterday.ward_staffings.O.add(person_a, {continued: false});
                yesterday.ward_staffings.N.add(person_a, {continued: false});
                test_staffing(yesterday, 'A', 1, 1);
                test_staffing(yesterday, 'O', 1, 1);
                test_staffing(yesterday, 'N', 1, 1);
                test_staffing(today,     'A', 1, 0);
                test_staffing(today,     'O', 0, 0);
                test_staffing(today,     'N', 0, 0);
                test_staffing(tomorrow,  'A', 1, 1);
                test_staffing(tomorrow,  'O', 0, 0);
                test_staffing(tomorrow,  'N', 0, 0);
                yesterday.ward_staffings.N.remove(person_a);
                test_staffing(today,     'A', 1, 1);
                test_staffing(today,     'O', 0, 0);
            });
            it("should strike off persons for wards, "+
                "that are not possible after their yesterdays duties", function() {
                var person_a = models.persons.get('A');
                var person_b = models.persons.get('B');
                yesterday.ward_staffings.A.add(person_a, {continued: true});
                yesterday.ward_staffings.S.add(person_a);
                yesterday.ward_staffings.B.add(person_b, {continued: true});
                yesterday.ward_staffings.S.add(person_b);
                test_staffing(yesterday, 'A', 1, 1);
                test_staffing(yesterday, 'B', 1, 1);
                test_staffing(today,     'A', 1, 1);
                test_staffing(today,     'B', 1, 0);
                test_staffing(tomorrow,  'A', 1, 1);
                test_staffing(tomorrow,  'B', 1, 1);
            });
            it("should continue yesterdays planning", function() {
                var person_a = models.persons.get('A');
                yesterday.ward_staffings.A.add(person_a, {continued: true});
                expect(today.ward_staffings.A.length).toBe(1);
                expect(today.ward_staffings.A.models[0].id).toBe('A');
                expect(today.ward_staffings.B.length).toBe(0);
                today.ward_staffings.A.remove(person_a, {continued: true});
                expect(today.ward_staffings.A.length).toBe(0);
                expect(tomorrow.ward_staffings.A.length).toBe(0);
                // same thing for non-continued ward
                yesterday.ward_staffings.O.add(person_a, {continued: true});
                expect(today.ward_staffings.O.length).toBe(1);
            });
            describe("combination of previous changes", function() {
                var template = _.template(
                    "'<%= action1 %> <%= cont1 %>' <%= relation %> " +
                    "'<%= action2 %> <%= cont2 %>' <%= change %> '<%= result %>' " +
                    "(<%= sensible %>sensible change)");
                var person_a = models.persons.get('A');
                function do_test(action1, cont1, relation, action2, cont2, 
                                 change, result, sensible) {
                    
                    it(template({
                            action1: action1, 
                            cont1: cont1,
                            relation: relation,
                            action2: action2, 
                            cont2: cont2,
                            change: change,
                            result: result,
                            sensible: sensible ? '' : 'not ',
                        }),
                       function () {
                            (relation == 'then' ? yesterday : today).
                                ward_staffings.A[action1=='add' ? 'add' : 'remove'](
                                    person_a, {continued: cont1=='cont'});
                            var previous = tomorrow.ward_staffings.A.length;
                            (relation == 'then' ? today : yesterday).
                                ward_staffings.A[action2=='add' ? 'add' : 'remove'](
                                    person_a, {continued: cont2=='cont'});
                            expect(tomorrow.ward_staffings.A.length).toBe(
                                result=='planned' ? 1 : 0);
                            if (change=='stays')
                                expect(tomorrow.ward_staffings.A.length)
                                    .toBe(previous);
                            else
                                expect(tomorrow.ward_staffings.A.length)
                                    .not.toBe(previous);
                        });
                }
                do_test('add','cont','then','add','cont','stays',     'planned',    false);
                do_test('add','cont','then','add','once','stays',     'planned',    false);
                do_test('add','cont','then','rem','cont','changes to','not planned',true);
                do_test('add','cont','then','rem','once','stays',     'planned',    true);

                do_test('add','once','then','add','cont','changes to','planned',    true);
                do_test('add','once','then','add','once','stays',     'not planned',true);
                do_test('add','once','then','rem','cont','stays',     'not planned',false);
                do_test('add','once','then','rem','once','stays',     'not planned',false);

                do_test('rem','cont','then','add','cont','changes to','planned',    true);
                do_test('rem','cont','then','add','once','stays',     'not planned',true);
                do_test('rem','cont','then','rem','cont','stays',     'not planned',false);
                do_test('rem','cont','then','rem','once','stays',     'not planned',false);

                // To start with 'rem once' always seems unsensible
                do_test('rem','once','then','add','cont','changes to','planned',    false);
                do_test('rem','once','then','add','once','stays',     'not planned',false);
                do_test('rem','once','then','rem','cont','stays',     'not planned',false);
                do_test('rem','once','then','rem','once','stays',     'not planned',false);

                do_test('add','cont','then earlier','add','cont','stays',     'planned',    false);
                do_test('add','cont','then earlier','add','once','stays',     'planned',    true);
                do_test('add','cont','then earlier','rem','cont','stays',     'planned',    true);
                do_test('add','cont','then earlier','rem','once','stays',     'planned',    true);

                do_test('add','once','then earlier','add','cont','stays',     'not planned',true);
                do_test('add','once','then earlier','add','once','stays',     'not planned',true);
                do_test('add','once','then earlier','rem','cont','stays',     'not planned',false);
                do_test('add','once','then earlier','rem','once','stays',     'not planned',false);

                do_test('rem','cont','then earlier','add','cont','changes to','planned',    true);
                do_test('rem','cont','then earlier','add','once','stays',     'not planned',true);
                do_test('rem','cont','then earlier','rem','cont','stays',     'not planned',true);
                do_test('rem','cont','then earlier','rem','once','stays',     'not planned',true);

                // To start with 'rem once' always seems unsensible
                do_test('rem','once','then earlier','add','cont','changes to','planned',    false);
                do_test('rem','once','then earlier','add','once','stays',     'not planned',false);
                do_test('rem','once','then earlier','rem','cont','stays',     'not planned',false);
                do_test('rem','once','then earlier','rem','once','stays',     'not planned',false);

            });
            it("should set a persons duties", function() {
                var person_a = models.persons.get('A');
                expect(today.persons_duties.A.length).toBe(0);
                today.ward_staffings.A.add(person_a);
                expect(today.persons_duties.A.length).toBe(1);
                expect(today.persons_duties.A.models[0].id).toBe('A');
                today.ward_staffings.A.remove(person_a);
                expect(today.persons_duties.A.length).toBe(0);
            });
            it("should make a person available after the vacation ends", function() {
                var person_a = models.persons.get('A');
                var ward_a = models.wards.get('A');
                expect(yesterday.get_available(ward_a).length).toBe(3);
                expect(today.get_available(ward_a).length).toBe(3);
                expect(tomorrow.get_available(ward_a).length).toBe(3);
                // on leave since yesterday
                yesterday.ward_staffings.L.add(person_a, {continued: true});
                expect(yesterday.get_available(ward_a).length).toBe(2);
                expect(today.get_available(ward_a).length).toBe(2);
                expect(tomorrow.get_available(ward_a).length).toBe(2);
                // back today
                today.ward_staffings.L.remove(person_a, {continued: true});
                expect(yesterday.get_available(ward_a).length).toBe(2);
                expect(today.get_available(ward_a).length).toBe(3);
                expect(tomorrow.get_available(ward_a).length).toBe(3);
            });
            it("should continue a persons duties after the vacation ends", function() {
                var person_a = models.persons.get('A');
                var person_b = models.persons.get('B');
                // A is on ward A
                yesterday.ward_staffings.A.add(person_a, {continued: true});
                yesterday.ward_staffings.A.add(person_b, {continued: true});
                expect(yesterday.persons_duties.A.length).toBe(1);
                // on leave since today
                today.ward_staffings.L.add(person_a, {continued: true});
                expect(today.ward_staffings.A.length).toBe(2);
                expect(today.ward_staffings.A.displayed.length).toBe(1);
                expect(today.persons_duties.A.pluck('shortname')).toEqual(['A', 'L']);
                // back tomorrow
                tomorrow.ward_staffings.L.remove(person_a, {continued: true});
                expect(tomorrow.ward_staffings.A.length).toBe(2);
                expect(tomorrow.ward_staffings.A.displayed.length).toBe(2);
                expect(tomorrow.persons_duties.A.pluck('shortname')).toEqual(['A']);
                expect(tomorrow.persons_duties.A.length).toBe(1);
            });
            it("should continue the staffings if a day is added", function() {
                var tdat;
                today.ward_staffings.A.add(models.persons.get('A'),
                    {continued: true});
                // same thing for non-continued ward
                today.ward_staffings.O.add(models.persons.get('A'),
                    {continued: true});
                tdat = new models.Day({
                    date: new Date(2015, 7, 6),
                    yesterday: tomorrow,
                });
                expect(tdat.ward_staffings.A.length).toBe(1);
                expect(tdat.ward_staffings.A.models[0].id).toBe('A');
                expect(tdat.ward_staffings.O.length).toBe(1);
                expect(tdat.ward_staffings.B.length).toBe(0);
            });
            it("should calculate a persons duties if a day is added", function() {
                var tdat;
                today.ward_staffings.A.add(models.persons.get('A'),
                    {continued: true});
                tdat = new models.Day({
                    date: new Date(2015, 7, 6),
                    yesterday: tomorrow,
                });
                expect(tdat.persons_duties.A.length).toBe(1);
                expect(tdat.persons_duties.A.models[0].id).toBe('A');
                expect(tdat.persons_duties.B.length).toBe(0);
            });
        });
        describe("get_day and Day.make_next_day", function() {
            it("should start the day chain", function() {
                expect(models.days.length).toBe(0);
                var day = models.days.get_day(2016, 2, 24);
                expect(day).toBeDefined();
                expect(models.days.get('20160324')).toEqual(day);
                var next_day = day.make_next_day();
                expect(models.days.get('20160325')).toEqual(next_day);
                var future_day = models.days.get_day(2016, 2, 27);
                models.days.get('20160326').get('yesterday').marker = 'testmarker';
                expect(next_day.marker).toEqual('testmarker');
                // Why does this fail?
                expect(models.days.get('20160326').get('yesterday')).toBe(next_day);
            });
        });
        describe("apply plannings", function() {
            it("should apply plannings for the day", function() {
                var day = new models.Day({
                    date: new Date(2016, 2, 10),
                });
                day.apply_planning({ person: 'A', ward: 'A',
                    start: '20160310',
                    end: '20160310',
                });
                day.apply_planning({ person: 'A', ward: 'B',
                    start: '20160301',
                    end: '20160320',
                });
                day.apply_planning({ person: 'B', ward: 'A',
                    start: '20160301',
                    end: '20160310',
                });
                day.apply_planning({ person: 'B', ward: 'B',
                    start: '20160310',
                    end: '20160320',
                });
                expect(day.ward_staffings.A.pluck('id')).toEqual(['A', 'B']);
                expect(day.ward_staffings.B.pluck('id')).toEqual(['A', 'B']);
            });
            it("should not apply plannings for other days", function() {
                var day = new models.Day({
                    date: new Date(2016, 2, 10),
                });
                day.apply_planning({ person: 'A', ward: 'A',
                    start: '20160210',
                    end: '20160210',
                });
                day.apply_planning({ person: 'B', ward: 'A',
                    start: '20160311',
                    end: '20160320',
                });
                expect(day.ward_staffings.A.length).toBe(0);
            });
        });
        describe("get_month_id", function() {
            it("should return the right month_id", function() {
                var day = new models.Day({
                    date: new Date(2016, 2, 10),
                });
                expect(day.get_month_id()).toBe('201603');
            });
        });
    });
    describe("get_month_days", function() {
        beforeEach(function() {
            models.days.reset();
        });
        afterEach(function() {
            models.days.reset();
        });
        it("should return the right days", function() {
            expect(models.days.length).toBe(0);
            month_days = models.get_month_days(2016, 3);
            expect(month_days.length).toBe(30);
            expect(models.days.length).toBe(31);
            expect(month_days[0].id).toEqual('20160401');
            expect(month_days[29].id).toEqual('20160430');
            expect(models.days.get('20160501')).toBeDefined();
        });
    });
    describe("Changes", function() {
        beforeEach(function() {
            // initialize August 3 through 5
            models.days.reset();
            models.days.get_day(2015, 7, 3);
            models.days.get_day(2015, 7, 5);
        });
        afterEach(function() {
            models.days.reset();
        });
        it("should apply changes", function() {
            var yesterday = models.days.get('20150803');
            var today = models.days.get('20150804');
            var tomorrow = models.days.get('20150805');
            models.apply_change({
                person: 'A', ward: 'A',
                day: '20150804', action: 'add',
                continued: true,
            });
            expect(yesterday.ward_staffings.A.length).toBe(0);
            expect(yesterday.persons_duties.A.length).toBe(0);
            expect(today.ward_staffings.A.length).toBe(1);
            expect(today.ward_staffings.A.pluck('id')).toEqual(['A']);
            expect(today.persons_duties.A.pluck('shortname')).toEqual(['A']);
            expect(tomorrow.ward_staffings.A.pluck('id')).toEqual(['A']);
            expect(tomorrow.persons_duties.A.pluck('shortname')).toEqual(['A']);
        });
        it("should preserve a later planning, " +
            "if a previous duty is started", function() {
            var tomorrow = models.days.get('20150805');
            models.apply_change({  // add from today
                person: 'A', ward: 'A',
                day: '20150804', action: 'add', continued: true,
            });
            models.apply_change({  // remove tomorrow
                person: 'A', ward: 'A',
                day: '20150805', action: 'remove', continued: true,
            });
            models.apply_change({  // add from yesterday
                person: 'A', ward: 'A',
                day: '20150803', action: 'add', continued: true,
            });
            expect(tomorrow.ward_staffings.A.length).toEqual(0);
            expect(tomorrow.persons_duties.A.length).toEqual(0);
        });
        it("should preserve a later planning, " +
            "if a previous duty ends", function() {
            var tomorrow = models.days.get('20150805');
            models.apply_change({  // add from tomorrow
                person: 'A', ward: 'A',
                day: '20150805', action: 'add', continued: true,
            });
            models.apply_change({  // add from yesterday
                person: 'A', ward: 'A',
                day: '20150803', action: 'add', continued: true,
            });
            models.apply_change({  // remove today
                person: 'A', ward: 'A',
                day: '20150804', action: 'remove', continued: true,
            });
            expect(tomorrow.ward_staffings.A.pluck('id')).toEqual(['A']);
            expect(tomorrow.persons_duties.A.pluck('shortname')).toEqual(['A']);
        });
    });
});
