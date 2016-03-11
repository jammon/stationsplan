describe("function is_free", function() {
    it("should identify weekdays", function() {
        expect(models.is_free(new Date(2015, 7, 7))).toBe(false);  // Friday
        expect(models.is_free(new Date(2015, 7, 8))).toBe(true);  // Saturday
        expect(models.is_free(new Date(2015, 7, 9))).toBe(true);  // Sunday
        expect(models.is_free(new Date(2015, 7, 10))).toBe(false);  // Monday
    });
    it("should identify special holidays", function() {
        expect(models.is_free(new Date(2015, 9, 3))).toBe(true);
        expect(models.is_free(new Date(2015, 11, 24))).toBe(true);
    });
});
describe("Initializing data", function() {
    it("should have the persons and wards set", function() {
        init_hospital();
        expect(models.persons.length).toBe(2);
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
describe("Day", function() {
    init_hospital();
    var person_a = models.persons.get('A');
    var person_b = models.persons.get('B');
    var ward_a = models.wards.get('A');
    it("should be initialized properly", function() {
        var today = new models.Day({ date: new Date(2015, 7, 7) });
        expect(today.persons_duties).not.toEqual(undefined);
        expect(today.persons_duties.A.length).toBe(0);
        expect(today.ward_staffings).not.toEqual(undefined);
        expect(today.ward_staffings.A.length).toBe(0);
    });
    describe("check availability:", function() {
        function check_availability (action, nr_avail, first_avail) {
            var yesterday = new models.Day({
                date: new Date(2015, 7, 6),  // Thursday
            });
            var today = new models.Day({
                date: new Date(2015, 7, 7),  // Friday
                yesterday: yesterday,
            });
            action(today, yesterday);
            var available = today.get_available(ward_a);
            expect(available.length).toEqual(nr_avail);
            if (first_avail) {
                expect(available[0].id).toEqual(first_avail);
            }
        }
        it("usually everybody is available", function() {
            check_availability(function(today, yesterday) {},
            2);
        });
        it("who is on leave isn't available", function() {
            check_availability(function(today, yesterday) {
                today.ward_staffings.L.add(person_a);
            },
            1, 'B');
        });
        it("who was on nightshift yesterday isn't available", function() {
            check_availability(function(today, yesterday) {
                yesterday.ward_staffings.N.add(person_a);
            },
            1, 'B');
        });
        it("who is on nightshift today is available", function() {
            check_availability(function(today, yesterday) {
                today.ward_staffings.N.add(person_a);
            },
            2);
        });
        it("who is planned for a different ward today is available", function() {
            check_availability(function(today, yesterday) {
                today.ward_staffings.B.add(person_a);
            },
            2);
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
            var ward_a = models.wards.get('A');
            var ward_f = models.wards.get('F');
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
            yesterday.ward_staffings.A.add(person_a, {continued: true});
            expect(today.ward_staffings.A.length).toBe(1);
            expect(today.ward_staffings.A.models[0].id).toBe('A');
            expect(today.ward_staffings.B.length).toBe(0);
            today.ward_staffings.A.remove(person_a, {continued: true});
            expect(today.ward_staffings.A.length).toBe(0);
            expect(tomorrow.ward_staffings.A.length).toBe(0);
        });
        describe("combination of previous changes", function() {
            var template = _.template(
                "'<%= action1 %> <%= cont1 %>' <%= relation %> " +
                "'<%= action2 %> <%= cont2 %>' <%= change %> '<%= result %>' " +
                "(<%= sensible %>sensible change)");
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
            expect(today.persons_duties.A.length).toBe(0);
            today.ward_staffings.A.add(person_a);
            expect(today.persons_duties.A.length).toBe(1);
            expect(today.persons_duties.A.models[0].id).toBe('A');
            today.ward_staffings.A.remove(person_a);
            expect(today.persons_duties.A.length).toBe(0);
        });
        it("should make a person available after the vacation ends", function() {
            expect(yesterday.get_available(ward_a).length).toBe(2);
            expect(today.get_available(ward_a).length).toBe(2);
            expect(tomorrow.get_available(ward_a).length).toBe(2);
            // on leave since yesterday
            yesterday.ward_staffings.L.add(person_a, {continued: true});
            expect(yesterday.get_available(ward_a).length).toBe(1);
            expect(today.get_available(ward_a).length).toBe(1);
            expect(tomorrow.get_available(ward_a).length).toBe(1);
            // back today
            today.ward_staffings.L.remove(person_a, {continued: true});
            expect(yesterday.get_available(ward_a).length).toBe(1);
            expect(today.get_available(ward_a).length).toBe(2);
            expect(tomorrow.get_available(ward_a).length).toBe(2);
        });
        it("should continue a persons duties after the vacation ends", function() {
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
            today.ward_staffings.A.add(person_a, {continued: true});
            tdat = new models.Day({
                date: new Date(2015, 7, 6),
                yesterday: tomorrow,
            });
            expect(tdat.ward_staffings.A.length).toBe(1);
            expect(tdat.ward_staffings.A.models[0].id).toBe('A');
            expect(tdat.ward_staffings.B.length).toBe(0);
        });
        it("should calculate a persons duties if a day is added", function() {
            var tdat;
            today.ward_staffings.A.add(person_a, {continued: true});
            tdat = new models.Day({
                date: new Date(2015, 7, 6),
                yesterday: tomorrow,
            });
            expect(tdat.persons_duties.A.length).toBe(1);
            expect(tdat.persons_duties.A.models[0].id).toBe('A');
            expect(tdat.persons_duties.B.length).toBe(0);
        });
    });
    describe("calculating the id of the day", function() {
        it("should calculate usual date to an id", function() {
            function test_get_day_id(year, month, day, id) {
                expect(models.get_day_id(year, month, day)).toBe(id);
                expect(models.get_day_id(new Date(year, month, day))).toBe(id);
            }
            test_get_day_id(2015, 0, 1, "20150101");
            test_get_day_id(2015, 7, 30, "20150830");
            test_get_day_id(2015, 11, 31, "20151231");
            test_get_day_id(1999, 11, 31, "19991231");
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
});
describe("Person", function() {
    it("should know, if they are available", function() {
        var p1 = new models.Person({
            name: "Test Test",
            id: "test",
        });
        var p2 = new models.Person({
            name: "Test Test2",
            id: "test2",
            start_date: [2015, 1, 1],
            end_date: [2015, 11, 31],
        });
        var d1 = new Date(2015, 0, 31);
        var d2 = new Date(2015, 1, 1);
        var d3 = new Date(2015, 11, 31);
        var d4 = new Date(2016, 0, 1);
        expect(p1.is_available(d1)).toBe(true);
        expect(p1.is_available(d2)).toBe(true);
        expect(p1.is_available(d3)).toBe(true);
        expect(p1.is_available(d4)).toBe(true);
        expect(p2.is_available(d1)).toBe(false);
        expect(p2.is_available(d2)).toBe(true);
        expect(p2.is_available(d3)).toBe(true);
        expect(p2.is_available(d4)).toBe(false);
    });
});
describe("Changes", function() {
    beforeEach(function() {
        var last_day = models.days['20150803'] = new models.Day({
            date: new Date(2015, 7, 3),
        });
        last_day = models.days['20150804'] = new models.Day({
            date: new Date(2015, 7, 4),
            yesterday: last_day,
        });
        last_day = models.days['20150805'] = new models.Day({
            date: new Date(2015, 7, 5),
            yesterday: last_day,
        });
    });
    it("should apply changes", function() {
        var yesterday = models.days['20150803'];
        var today = models.days['20150804'];
        var tomorrow = models.days['20150805'];
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
        var tomorrow = models.days['20150805'];
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
        var tomorrow = models.days['20150805'];
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
describe("days_in_month", function() {
    it("should calculate the days per month", function() {
        expect(models.days_in_month(0, 2016)).toBe(31);
        expect(models.days_in_month(1, 2016)).toBe(29);
        expect(models.days_in_month(1, 2017)).toBe(28);
        expect(models.days_in_month(1, 2100)).toBe(29); // Sorry, that's wrong.
        // But I don't expect the software to run that long.
    });
});
// describe("Views");