// jshint esversion: 6
beforeEach(init_hospital);
describe("models", function () {
    describe("Initializing data", function () {
        it("should have the persons and wards set", function () {
            expect(models.persons.length).toBe(persons_init.length);
            expect(models.wards.length).toBe(wards_init.length);
            const person_a = models.persons.get('A');
            expect(person_a.get('name')).toBe('Anton');
            expect(person_a.get('current_department')).toBeTruthy();
            const person_d = models.persons.get('DiffDept');
            expect(person_d.get('name')).toBe('Different Department');
            expect(person_d.get('current_department')).toBeFalsy();
            const ward_a = models.wards.get('A');
            expect(ward_a.get('name')).toBe('Ward A');
            expect(ward_a.get('min')).toBe(1);
            expect(ward_a.get('max')).toBe(2);
        });
    });
    describe("Current_Date", function () {
        it("should initialize to todays id", function () {
            const current_date = new models.Current_Date();
            expect(current_date.get('date_id'))
                .toBe(utils.get_day_id(new Date()));
        });
        it("should send change event only when the date has changed", function () {
            let current_date = new models.Current_Date();
            let changed = false;
            current_date.on('change:date_id', function () { changed = true; });
            current_date.update();
            expect(changed).toBeFalsy();

            current_date.set({ date_id: '20170101' });
            changed = false;
            current_date.update();
            expect(changed).toBeTruthy();
        });
        it("should tell, if a date_id refers to today", function () {
            const current_date = new models.Current_Date();
            expect(current_date.is_today(utils.get_day_id(new Date())))
                .toBeTruthy();
            expect(current_date.is_today('20170101')).toBeFalsy();
        });
    });
    describe("Person", function () {
        describe("calculating availability", function () {
            const before = new Date(2016, 1, 29);
            const firstday = new Date(2016, 2, 1);
            const lastday = new Date(2016, 2, 31);
            const after = new Date(2016, 3, 1);
            const start_date = [2016, 2, 1];
            const end_date = [2016, 2, 31];
            let person;
            it("should calculate availability for a person with start_date and end_date", function () {
                person = new models.Person(
                    {
                        start_date: start_date, end_date: end_date,
                        departments: [1]
                    });
                expect(person.is_available(before)).toBe(false);
                expect(person.is_available(firstday)).toBe(true);
                expect(person.is_available(lastday)).toBe(true);
                expect(person.is_available(after)).toBe(false);
            });
            it("should calculate availability for a person with start_date", function () {
                person = new models.Person(
                    {
                        start_date: start_date,
                        departments: [1]
                    });
                expect(person.is_available(before)).toBe(false);
                expect(person.is_available(firstday)).toBe(true);
                expect(person.is_available(lastday)).toBe(true);
                expect(person.is_available(after)).toBe(true);
            });
            it("should calculate availability for a person with end_date", function () {
                person = new models.Person(
                    { end_date: end_date, departments: [1] });
                expect(person.is_available(before)).toBe(true);
                expect(person.is_available(firstday)).toBe(true);
                expect(person.is_available(lastday)).toBe(true);
                expect(person.is_available(after)).toBe(false);
            });
            it("should calculate availability for a person without start_date or end_date", function () {
                person = new models.Person({ departments: [1] });
                expect(person.is_available(before)).toBe(true);
                expect(person.is_available(firstday)).toBe(true);
                expect(person.is_available(lastday)).toBe(true);
                expect(person.is_available(after)).toBe(true);
            });
        });
    });
    describe("Ward", function () {
        it("can be approved for a date", function () {
            // Approval date not set
            let ward = new models.Ward({ shortname: 'A' });
            expect(ward.is_approved(new Date(2017, 3, 1))).toBe(true);
            // Approval date set to false
            ward = new models.Ward({ shortname: 'A', approved: false });
            expect(ward.is_approved(new Date(2017, 3, 1))).toBe(true);
            // Approval date set
            ward = new models.Ward({ shortname: 'A', approved: [2017, 3, 1] });
            expect(ward.is_approved(new Date(2017, 3, 1))).toEqual(true);
            expect(ward.is_approved(new Date(2017, 3, 2))).toEqual(false);
        });
        it("has a ward_type", function () {
            expect(models.wards.get('V').get_ward_type()).toEqual('Visite');
            expect(models.wards.get('N').get_ward_type()).toEqual('Callshifts');
            expect(models.wards.get('O').get_ward_type()).toEqual('Callshifts');
        });
        describe("on_call", function () {
            it("should contain the call shifts", function () {
                expect(models.on_call.pluck('shortname')).toEqual(['N', 'O', 'V']);
            });
        });
        describe("on_call_types", function () {
            it("should contain the types of the call shifts", function () {
                expect(models.on_call_types).toEqual(['Callshifts', 'Visite']);
            });
        });
        describe("allows_after_this", function () {
            it("should exclude the correct wards", function () {
                // no exclusions
                let ward = new models.Ward();
                expect(ward.allows_after_this('A')).toBe(true);
                ward = new models.Ward({ after_this: 'A,B' });
                expect(ward.allows_after_this('A')).toBe(true);
                expect(ward.allows_after_this('B')).toBe(true);
                expect(ward.allows_after_this('C')).toBe(false);
            });
        });
        describe("allows_with_this", function () {
            it("should exclude the correct wards", function () {
                // no exclusions
                let ward = new models.Ward();
                expect(ward.allows_with_this('A')).toBe(true);
                ward = new models.Ward({ not_with_this: 'A,B' });
                expect(ward.allows_with_this('A')).toBe(false);
                expect(ward.allows_with_this('B')).toBe(false);
                expect(ward.allows_with_this('C')).toBe(true);
            });
        });
    });
    describe("Staffing", function () {
        describe("calculate who can be planned", function () {
            let today, yesterday, staffing_a, person_a;
            beforeEach(function () {
                yesterday = new models.Day({
                    date: new Date(2016, 8, 19)
                });
                today = new models.Day({
                    date: new Date(2016, 8, 20),
                    yesterday: yesterday,
                });
                staffing_a = today.ward_staffings.A;
                person_a = models.persons.get('A');
            });
            it("if no person is given, it cannot be planned", function () {
                expect(staffing_a.can_be_planned(void 0)).toBeFalsy();
            });
            it("usually persons can be planned", function () {
                expect(staffing_a.can_be_planned(person_a)).toBeTruthy();
            });
            it("who is on leave, cannot be planned", function () {
                today.ward_staffings.L.add(person_a);
                expect(staffing_a.can_be_planned(person_a)).toBeFalsy();
            });
            it("who was on call last night, cannot be planned", function () {
                yesterday.ward_staffings.N.add(person_a);
                expect(staffing_a.can_be_planned(person_a)).toBeFalsy();
            });
            it("who was on call last night, can be planned if they are anonymous", function () {
                other = models.persons.get('Other');
                yesterday.ward_staffings.N.add(other);
                expect(staffing_a.can_be_planned(other)).toBeTruthy();
            });
            it("who was planned on call last night but became ill, can be planned", function () {
                yesterday.ward_staffings.N.add(person_a);
                yesterday.ward_staffings.L.add(person_a);
                expect(staffing_a.can_be_planned(person_a)).toBeTruthy();
            });
            it("who cannot work on this ward, cannot be planned", function () {
                expect(today.ward_staffings.N.can_be_planned(
                    models.persons.get('C'))).toBeFalsy();
            });
            it("for 'on leave', the members of the current department can be planned", function () {
                const staffing_l = today.ward_staffings.L;
                expect(staffing_l.can_be_planned(person_a)).toBeTruthy();
                // nightshift yesterday
                yesterday.ward_staffings.N.add(person_a);
                expect(staffing_l.can_be_planned(person_a)).toBeTruthy();
                // on leave
                today.ward_staffings.L.add(person_a);
                expect(staffing_l.can_be_planned(person_a)).toBeTruthy();
                // Different department
                const person_d = models.persons.get('DiffDept');
                expect(staffing_l.can_be_planned(person_d)).toBeFalsy();
            });
            it("'anonymous' persons can be planned after a call shift", function () {
                const anon = models.persons.get('Other');
                expect(staffing_a.can_be_planned(anon)).toBeTruthy();
                yesterday.ward_staffings.N.add(anon);
                expect(staffing_a.can_be_planned(anon)).toBeTruthy();
            });
        });
    });
    describe("Day", function () {
        it("should be initialized properly", function () {
            const today = new models.Day({ date: new Date(2015, 7, 7) });
            expect(today.id).toEqual('20150807');
            expect(today.persons_duties).toBeDefined();
            expect(today.persons_duties.A.length).toBe(0);
            expect(today.ward_staffings).toBeDefined();
            expect(today.ward_staffings.A.length).toBe(0);
        });
        describe("check availability:", function () {
            function get_availables_after_planning(
                day_to_plan, ward_id, person_id,
                ward_to_check) {
                // add a person to a staffing on a day
                // return a list of ids of availables for a given ward
                const yesterday = new models.Day({
                    date: new Date(2015, 7, 6),  // Thursday
                });
                const today = new models.Day({
                    date: new Date(2015, 7, 7),  // Friday
                    yesterday: yesterday,
                });
                if (day_to_plan) {
                    let _day = day_to_plan == 'today' ? today : yesterday;
                    _day.ward_staffings[ward_id].add(models.persons.get(person_id));
                }
                let available = today.get_available(models.wards.get(ward_to_check));
                return _.map(available, function (p) {
                    return p.get('shortname');
                });
            }
            it("usually everybody is available", function () {
                let available = get_availables_after_planning(
                    '', '', '',
                    'A');
                expect(available).toContain('A');
                expect(available).toContain('B');
                expect(available).toContain('C');
                expect(available).toContain('Other');
                expect(available).toContain('DiffDept');
            });
            it("everybody is available for leave", function () {
                let available = get_availables_after_planning(
                    'today', 'A', 'A',
                    'L');
                expect(available).toContain('A');
                expect(available).toContain('B');
                expect(available).toContain('C');
                expect(available).toContain('Other');
                expect(available).toContain('DiffDept');
            });
            it("not available for leave who doesn't work here any more", function () {
                models.persons.add({
                    name: 'Soon to come', id: '10', shortname: 'Soon',
                    functions: ['A', 'B', 'N', 'O'], departments: [1],
                    'start_date': [2015, 8, 1]
                });
                models.persons.add({
                    name: 'No more', id: '11', shortname: 'Nomore',
                    functions: ['A', 'B', 'N', 'O'], departments: [1],
                    'end_date': [2015, 6, 31]
                });
                let available = get_availables_after_planning(
                    'today', 'A', 'A',
                    'L');
                expect(available).toContain('A');
                expect(available).toContain('B');
                expect(available).not.toContain('Soon');
                expect(available).not.toContain('Nomore');
            });
            it("who is on leave isn't available", function () {
                let available = get_availables_after_planning(
                    'today', 'L', 'A',
                    'A');
                expect(available).not.toContain('A');
                expect(available).toContain('B');
            });
            it("who was on nightshift yesterday isn't available", function () {
                let available = get_availables_after_planning(
                    'yesterday', 'N', 'A',
                    'A');
                expect(available).not.toContain('A');
                expect(available).toContain('B');
            });
            it("who was on nightshift yesterday is available if they are anonymous", function () {
                let yesterday = new models.Day({
                    date: new Date(2015, 7, 6),  // Thursday
                });
                let today = new models.Day({
                    date: new Date(2015, 7, 7),  // Friday
                    yesterday: yesterday,
                });
                let other = models.persons.get('Other');
                yesterday.ward_staffings.N.add(other);
                let available = today.get_available(models.wards.get('A'));
                expect(_.map(available, function (p) { return p.get('shortname'); })).toContain('Other');
            });
            it("who was on nightshift yesterday is available for todays nightshift", function () {
                let available = get_availables_after_planning(
                    'yesterday', 'N', 'A',
                    'N');
                expect(available).toContain('A');
            });
            it("who is on nightshift today is available", function () {
                let available = get_availables_after_planning(
                    'today', 'N', 'A',
                    'A');
                expect(available).toContain('A');
                expect(available).toContain('B');
            });
            it("who is planned for a different ward today is available", function () {
                let available = get_availables_after_planning(
                    'today', 'B', 'A',
                    'A');
                expect(available).toContain('A');
                expect(available).toContain('B');
            });
        });
        describe("need for staffing (implicitly test Staffing.needs_staffing)", function () {
            it("should respect free days", function () {
                const sunday = new models.Day({ date: new Date(2015, 7, 2) });
                const monday = new models.Day({ date: new Date(2015, 7, 3) });
                expect(sunday.ward_staffings.A.no_staffing).toBeTruthy();
                expect(sunday.ward_staffings.F.no_staffing).toBeFalsy();
                expect(monday.ward_staffings.A.no_staffing).toBeFalsy();
                expect(monday.ward_staffings.F.no_staffing).toBeTruthy();
            });
            it("should plan wards for certain weekdays", function () {
                const saturday = new models.Day({ date: new Date(2015, 7, 1) });
                const sunday = new models.Day({ date: new Date(2015, 7, 2) });
                const monday = new models.Day({ date: new Date(2015, 7, 3) });
                expect(saturday.ward_staffings.V.no_staffing).toBeFalsy();
                expect(sunday.ward_staffings.V.no_staffing).toBeTruthy();
                expect(monday.ward_staffings.V.no_staffing).toBeTruthy();
            });
            it("should account for different days", function () {
                const no = new models.Day({ date: new Date(2015, 7, 8) });
                const yes = new models.Day({ date: new Date(2015, 7, 9) });
                expect(no.ward_staffings.V.no_staffing).toBeTruthy();
                expect(yes.ward_staffings.V.no_staffing).toBeFalsy();
            });
        });
        describe("needs_staffing (explicitly test models.needs_staffing)", function () {
            it("should respect free days", function () {
                const sunday = new models.Day({ date: new Date(2015, 7, 2) });
                const monday = new models.Day({ date: new Date(2015, 7, 3) });
                const A = new models.Ward({
                    name: 'Ward A', shortname: 'A', min: 1, max: 2
                });
                const F = new models.Ward({
                    name: 'Free days', shortname: 'F', min: 0, max: 10,
                    freedays: true
                });
                expect(models.needs_staffing(A, sunday)).toBeFalsy();
                expect(models.needs_staffing(F, sunday)).toBeTruthy();
                expect(models.needs_staffing(A, monday)).toBeTruthy();
                expect(models.needs_staffing(F, monday)).toBeFalsy();
            });
            it("should plan wards for certain weekdays", function () {
                const V = new models.Ward({
                    name: 'Visite', shortname: 'V', min: 0, max: 10,
                    weekdays: '16'
                });
                const saturday = new models.Day({ date: new Date(2015, 7, 1) });
                const sunday = new models.Day({ date: new Date(2015, 7, 2) });
                const monday = new models.Day({ date: new Date(2015, 7, 3) });
                const tuesday = new models.Day({ date: new Date(2015, 7, 4) });
                expect(models.needs_staffing(V, saturday)).toBeTruthy();
                expect(models.needs_staffing(V, sunday)).toBeFalsy();
                expect(models.needs_staffing(V, monday)).toBeTruthy();
                expect(models.needs_staffing(V, tuesday)).toBeFalsy();
            });
            it("should account for different days", function () {
                let V = new models.Ward({
                    name: 'Visite', shortname: 'V', min: 0, max: 10,
                    weekdays: '1'
                });
                const saturday = new models.Day({ date: new Date(2015, 7, 1) });
                const sunday = new models.Day({ date: new Date(2015, 7, 2) });
                V.set_different_day('20150801', '-');
                V.set_different_day('20150802', '+');
                expect(models.needs_staffing(V, saturday)).toBeFalsy();
                expect(models.needs_staffing(V, sunday)).toBeTruthy();
            });
        });
        describe("interaction with previous planning", function () {
            let yesterday, today, tomorrow, person_a;
            beforeEach(function () {
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
                person_a = models.persons.get('A');
            });
            function test_staffing(day, staffing, total, displayed) {
                const st = day.ward_staffings[staffing];
                expect(st.length).toBe(total);
                expect(st.displayed.length).toBe(displayed);
            }
            it("should strike off yesterdays nightshift for today, " +
                "and continue the duties tomorrow, " +
                "if they are to be continued", function () {
                    yesterday.ward_staffings.A.add(person_a, { continued: true });
                    yesterday.ward_staffings.O.add(person_a, { continued: false });
                    yesterday.ward_staffings.N.add(person_a, { continued: false });
                    test_staffing(yesterday, 'A', 1, 1);
                    test_staffing(yesterday, 'O', 1, 1);
                    test_staffing(yesterday, 'N', 1, 1);
                    test_staffing(today, 'A', 1, 0);
                    test_staffing(today, 'O', 0, 0);
                    test_staffing(today, 'N', 0, 0);
                    test_staffing(tomorrow, 'A', 1, 1);
                    test_staffing(tomorrow, 'O', 0, 0);
                    test_staffing(tomorrow, 'N', 0, 0);
                    yesterday.ward_staffings.N.remove(person_a);
                    test_staffing(today, 'A', 1, 1);
                    test_staffing(today, 'O', 0, 0);
                });
            it("should strike off persons for wards, " +
                "that are not possible after their yesterdays duties", function () {
                    const person_b = models.persons.get('B');
                    yesterday.ward_staffings.A.add(person_a, { continued: true });
                    yesterday.ward_staffings.S.add(person_a);
                    yesterday.ward_staffings.B.add(person_b, { continued: true });
                    yesterday.ward_staffings.S.add(person_b);
                    test_staffing(yesterday, 'A', 1, 1);
                    test_staffing(yesterday, 'B', 1, 1);
                    test_staffing(today, 'A', 1, 1);
                    test_staffing(today, 'B', 1, 0);
                    test_staffing(tomorrow, 'A', 1, 1);
                    test_staffing(tomorrow, 'B', 1, 1);
                });
            it("should continue yesterdays planning", function () {
                yesterday.ward_staffings.A.add(person_a, { continued: true });
                expect(today.ward_staffings.A.length).toBe(1);
                expect(today.ward_staffings.A.models[0].id).toBe('A');
                expect(today.ward_staffings.B.length).toBe(0);
                today.ward_staffings.A.remove(person_a, { continued: true });
                expect(today.ward_staffings.A.length).toBe(0);
                expect(tomorrow.ward_staffings.A.length).toBe(0);
            });
            describe("combination of previous changes", function () {
                const template = _.template(
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
                                ward_staffings.A[action1 == 'add' ? 'add' : 'remove'](
                                    person_a, { continued: cont1 == 'cont' });
                            const previous = tomorrow.ward_staffings.A.length;
                            (relation == 'then' ? today : yesterday).
                                ward_staffings.A[action2 == 'add' ? 'add' : 'remove'](
                                    person_a, { continued: cont2 == 'cont' });
                            expect(tomorrow.ward_staffings.A.length).toBe(
                                result == 'planned' ? 1 : 0);
                            if (change == 'stays')
                                expect(tomorrow.ward_staffings.A.length)
                                    .toBe(previous);
                            else
                                expect(tomorrow.ward_staffings.A.length)
                                    .not.toBe(previous);
                        });
                }
                do_test('add', 'cont', 'then', 'add', 'cont', 'stays', 'planned', false);
                do_test('add', 'cont', 'then', 'add', 'once', 'stays', 'planned', false);
                do_test('add', 'cont', 'then', 'rem', 'cont', 'changes to', 'not planned', true);
                do_test('add', 'cont', 'then', 'rem', 'once', 'stays', 'planned', true);

                do_test('add', 'once', 'then', 'add', 'cont', 'changes to', 'planned', true);
                do_test('add', 'once', 'then', 'add', 'once', 'stays', 'not planned', true);
                do_test('add', 'once', 'then', 'rem', 'cont', 'stays', 'not planned', false);
                do_test('add', 'once', 'then', 'rem', 'once', 'stays', 'not planned', false);

                do_test('rem', 'cont', 'then', 'add', 'cont', 'changes to', 'planned', true);
                do_test('rem', 'cont', 'then', 'add', 'once', 'stays', 'not planned', true);
                do_test('rem', 'cont', 'then', 'rem', 'cont', 'stays', 'not planned', false);
                do_test('rem', 'cont', 'then', 'rem', 'once', 'stays', 'not planned', false);

                // To start with 'rem once' always seems unsensible
                do_test('rem', 'once', 'then', 'add', 'cont', 'changes to', 'planned', false);
                do_test('rem', 'once', 'then', 'add', 'once', 'stays', 'not planned', false);
                do_test('rem', 'once', 'then', 'rem', 'cont', 'stays', 'not planned', false);
                do_test('rem', 'once', 'then', 'rem', 'once', 'stays', 'not planned', false);

                do_test('add', 'cont', 'then earlier', 'add', 'cont', 'stays', 'planned', false);
                do_test('add', 'cont', 'then earlier', 'add', 'once', 'stays', 'planned', true);
                do_test('add', 'cont', 'then earlier', 'rem', 'cont', 'stays', 'planned', true);
                do_test('add', 'cont', 'then earlier', 'rem', 'once', 'stays', 'planned', true);

                do_test('add', 'once', 'then earlier', 'add', 'cont', 'stays', 'not planned', true);
                do_test('add', 'once', 'then earlier', 'add', 'once', 'stays', 'not planned', true);
                do_test('add', 'once', 'then earlier', 'rem', 'cont', 'stays', 'not planned', false);
                do_test('add', 'once', 'then earlier', 'rem', 'once', 'stays', 'not planned', false);

                do_test('rem', 'cont', 'then earlier', 'add', 'cont', 'changes to', 'planned', true);
                do_test('rem', 'cont', 'then earlier', 'add', 'once', 'stays', 'not planned', true);
                do_test('rem', 'cont', 'then earlier', 'rem', 'cont', 'stays', 'not planned', true);
                do_test('rem', 'cont', 'then earlier', 'rem', 'once', 'stays', 'not planned', true);

                // To start with 'rem once' always seems unsensible
                do_test('rem', 'once', 'then earlier', 'add', 'cont', 'changes to', 'planned', false);
                do_test('rem', 'once', 'then earlier', 'add', 'once', 'stays', 'not planned', false);
                do_test('rem', 'once', 'then earlier', 'rem', 'cont', 'stays', 'not planned', false);
                do_test('rem', 'once', 'then earlier', 'rem', 'once', 'stays', 'not planned', false);

            });
            it("should set a persons duties", function () {
                expect(today.persons_duties.A.length).toBe(0);
                today.ward_staffings.A.add(person_a);
                expect(today.persons_duties.A.length).toBe(1);
                expect(today.persons_duties.A.models[0].id).toBe('A');
                today.ward_staffings.A.remove(person_a);
                expect(today.persons_duties.A.length).toBe(0);
            });
            it("should make a person available after the vacation ends", function () {
                const ward_a = models.wards.get('A');
                expect(yesterday.get_available(ward_a).length).toBe(6);
                expect(today.get_available(ward_a).length).toBe(6);
                expect(tomorrow.get_available(ward_a).length).toBe(6);
                // on leave since yesterday
                yesterday.ward_staffings.L.add(person_a, { continued: true });
                expect(yesterday.get_available(ward_a).length).toBe(5);
                expect(today.get_available(ward_a).length).toBe(5);
                expect(tomorrow.get_available(ward_a).length).toBe(5);
                // back today
                today.ward_staffings.L.remove(person_a, { continued: true });
                expect(yesterday.get_available(ward_a).length).toBe(5);
                expect(today.get_available(ward_a).length).toBe(6);
                expect(tomorrow.get_available(ward_a).length).toBe(6);
            });
            it("should continue a persons duties after the vacation ends", function () {
                const person_b = models.persons.get('B');
                // A is on ward A
                yesterday.ward_staffings.A.add(person_a, { continued: true });
                yesterday.ward_staffings.A.add(person_b, { continued: true });
                expect(yesterday.persons_duties.A.length).toBe(1);
                // on leave since today
                today.ward_staffings.L.add(person_a, { continued: true });
                expect(today.ward_staffings.A.length).toBe(2);
                expect(today.ward_staffings.A.displayed.length).toBe(1);
                expect(today.persons_duties.A.pluck('shortname')).toEqual(['A', 'L']);
                // back tomorrow
                tomorrow.ward_staffings.L.remove(person_a, { continued: true });
                expect(tomorrow.ward_staffings.A.length).toBe(2);
                expect(tomorrow.ward_staffings.A.displayed.length).toBe(2);
                expect(tomorrow.persons_duties.A.pluck('shortname')).toEqual(['A']);
                expect(tomorrow.persons_duties.A.length).toBe(1);
            });
            it("should continue the staffings if a day is added", function () {
                today.ward_staffings.A.add(models.persons.get('A'),
                    { continued: true });
                const tdat = new models.Day({
                    date: new Date(2015, 7, 6),
                    yesterday: tomorrow,
                });
                expect(tdat.ward_staffings.A.length).toBe(1);
                expect(tdat.ward_staffings.A.models[0].id).toBe('A');
                expect(tdat.ward_staffings.B.length).toBe(0);
            });
            it("should calculate a persons duties if a day is added", function () {
                today.ward_staffings.A.add(models.persons.get('A'),
                    { continued: true });
                const tdat = new models.Day({
                    date: new Date(2015, 7, 6),
                    yesterday: tomorrow,
                });
                expect(tdat.persons_duties.A.length).toBe(1);
                expect(tdat.persons_duties.A.models[0].id).toBe('A');
                expect(tdat.persons_duties.B.length).toBe(0);
            });
        });
        describe("get_day and Day.make_next_day", function () {
            it("should start the day chain", function () {
                expect(models.days.length).toBe(0);
                const day = models.days.get_day(new Date(2016, 2, 24));
                expect(day).toBeDefined();
                expect(models.days.get('20160324')).toEqual(day);

                expect(models.days.get_day(new Date(2016, 2, 21), 3)).toEqual(day);

                const next_day = day.make_next_day();
                expect(models.days.get('20160325')).toEqual(next_day);
                const future_day = models.days.get_day(new Date(2016, 2, 27));
                models.days.get('20160326').get('yesterday').marker = 'testmarker';
                expect(next_day.marker).toEqual('testmarker');
                // Why does this fail?
                expect(models.days.get('20160326').get('yesterday')).toBe(next_day);
            });
        });
        describe("apply plannings", function () {
            it("should apply plannings for the day", function () {
                let day = new models.Day({
                    date: new Date(2016, 2, 10),
                });
                let person_a = models.persons.get('A');
                let person_b = models.persons.get('B');
                let ward_a = models.wards.get('A');
                let ward_b = models.wards.get('B');
                day.apply_planning({
                    person: person_a, ward: ward_a,
                    start: '20160310',
                    end: '20160310',
                });
                day.apply_planning({
                    person: person_a, ward: ward_b,
                    start: '20160301',
                    end: '20160320',
                });
                day.apply_planning({
                    person: person_b, ward: ward_a,
                    start: '20160301',
                    end: '20160310',
                });
                day.apply_planning({
                    person: person_b, ward: ward_b,
                    start: '20160310',
                    end: '20160320',
                });
                expect(day.ward_staffings.A.pluck('shortname')).toEqual(['A', 'B']);
                expect(day.ward_staffings.B.pluck('shortname')).toEqual(['A', 'B']);
            });
            it("should not apply plannings for other days", function () {
                let day = new models.Day({
                    date: new Date(2016, 2, 10),
                });
                let person_a = models.persons.get('A');
                let person_b = models.persons.get('B');
                let ward_a = models.wards.get('A');
                day.apply_planning({
                    person: person_a, ward: ward_a,
                    start: '20160210',
                    end: '20160210',
                });
                day.apply_planning({
                    person: person_b, ward: ward_a,
                    start: '20160311',
                    end: '20160320',
                });
                expect(day.ward_staffings.A.length).toBe(0);
            });
        });
        describe("get_month_id", function () {
            it("should return the right month_id", function () {
                const day = new models.Day({
                    date: new Date(2016, 2, 10),
                });
                expect(day.get_month_id()).toBe('201603');
            });
        });
        describe("not_planned", function () {
            it("should have all persons not planned initially except the anonymous ones", function () {
                const today = new models.Day({ date: new Date(2019, 8, 27) });
                ["A", "B", "C"].forEach(function (c) {
                    expect(today.not_planned).toContain(models.persons.get(c));
                });
            });
            it("should respect todays planning", function () {
                let today = new models.Day({ date: new Date(2019, 8, 27) });
                let person_a = models.persons.get('A');
                let person_b = models.persons.get('B');
                today.ward_staffings.A.add(person_a);
                expect(today.not_planned).not.toContain(person_a);
                expect(today.not_planned).toContain(person_b);
            });
            it("should respect yesterdays nightshift", function () {
                let yesterday = new models.Day({
                    date: new Date(2019, 8, 26)
                });
                let today = new models.Day({
                    date: new Date(2019, 8, 27),
                    yesterday: yesterday,
                });
                let person_a = models.persons.get('A');
                let person_b = models.persons.get('B');
                today.ward_staffings.A.add(person_a);
                yesterday.ward_staffings.N.add(person_b);

                expect(today.not_planned).not.toContain(person_a);
                expect(today.not_planned).not.toContain(person_b);
                expect(today.not_planned).toContain(models.persons.get('C'));
            });
            it("should not contain external persons", function () {
                const today = new models.Day({ date: new Date(2019, 8, 27) });
                let not_planned = _.pluck(today.not_planned, 'id');
                expect(not_planned).not.toContain('Ext');
            });
        });
    });
    describe("get_month_days and MonthDays", function () {
        let month_days;
        beforeEach(function () {
            models.days.reset();
            month_days = models.get_month_days(2016, 3);
        });
        afterEach(function () {
            models.days.reset();
        });
        it("should return the right days", function () {
            expect(month_days.length).toBe(30);
            expect(month_days.at(0).id).toEqual('20160401');
            expect(month_days.at(29).id).toEqual('20160430');
        });
    });
    describe("get_period_days", function () {
        it("should return the right days", function () {
            models.days.reset();
            const period_days = models.get_period_days(new Date(2017, 5, 5), 14);
            expect(period_days.length).toBe(14);
            expect(period_days.at(0).id).toEqual('20170605');
            expect(period_days.at(13).id).toEqual('20170618');
            models.days.reset();
        });
        describe("Bugfix", function () {
            [{
                msg: "should not continue the last planning if planned for the last day",
                day: '20200310',
                next: '20200311',
            }, {
                msg: "should not continue the last planning if planned until the last day",
                day: '20200308',
                until: '20200310',
                next: '20200311',
            }, {
                msg: "should not continue the last planning if planned after the last day",
                day: '20200308',
                until: '20200312',
                next: '20200313',
            }].forEach(function (test) {
                it(test.msg, function () {
                    models.days.reset();
                    let days = models.get_period_days(new Date(2020, 2, 1), 10);
                    let change = {
                        person: 'A',
                        ward: 'A',
                        day: test.day,
                        action: 'add',
                        continued: !!test.until,
                        pk: 1,
                    };
                    if (test.until)
                        change.until = test.until;
                    models.apply_change(change);
                    // get next period
                    let next_period = models.get_period_days(
                        new Date(2020, 2, 11), 10);
                    expect(next_period.get(test.next).ward_staffings.A.length).toBe(0);
                    models.days.reset();
                });

            });

        });
    });
    describe("get_month_days and CallTallies", function () {
        let month_days;
        beforeEach(function () {
            models.days.reset();
        });
        afterEach(function () {
            models.days.reset();
        });
        it("should initialize a CallTally for every person if the user can change",
            function () {
                models.user.is_editor = true;
                month_days = models.get_month_days(2016, 3);
                expect(month_days.calltallies).toBeDefined();
                expect(month_days.calltallies.length).toBe(persons_init.length);
                models.user.is_editor = false;
            });
        it("should not initialize a CallTally if the user cannot change",
            function () {
                month_days = models.get_month_days(2016, 3);
                expect(month_days.calltallies).not.toBeDefined();
            });
        it("should update the CallTallies", function () {
            models.user.is_editor = true;
            month_days = models.get_month_days(2016, 3);
            const person_a = models.persons.get('A');
            const person_b = models.persons.get('B');
            const day1 = month_days.get('20160401');
            const day2 = month_days.get('20160402');
            const day3 = month_days.get('20160403');
            day1.ward_staffings.O.add(person_a);
            day2.ward_staffings.O.add(person_b);
            day3.ward_staffings.O.add(person_a);
            const ward_o = models.wards.get('O').get_ward_type();
            const ward_v = models.wards.get('V').get_ward_type();
            let tally = month_days.calltallies.get('A');
            expect(tally.get_tally(ward_o)).toBe(2);
            expect(tally.get_tally(ward_v)).toBe(0);
            expect(tally.get('weights')).toBe(6);
            tally = month_days.calltallies.get('B');
            expect(tally.get_tally(ward_o)).toBe(1);
            expect(tally.get_tally(ward_v)).toBe(0);
            expect(tally.get('weights')).toBe(3);
            tally = month_days.calltallies.get('Other');
            expect(tally.get_tally(ward_o)).toBe(0);
            expect(tally.get_tally(ward_v)).toBe(0);
            expect(tally.get('weights')).toBeUndefined();
            models.user.is_editor = false;
        });
    });
    describe("MonthDays.current_persons", function () {
        it("should exclude persons according to their employment status", function () {
            models.days.reset();
            models.persons.add([
                {
                    name: 'No More', shortname: 'X', end_date: [2016, 2, 31],
                    departments: [1]
                },
                {
                    name: 'Not Yet', shortname: 'Y', start_date: [2016, 4, 1],
                    departments: [1]
                },
                {
                    name: 'Short Time', shortname: 'Z',
                    start_date: [2016, 2, 1], end_date: [2016, 4, 31],
                    departments: [1]
                },
            ]);
            const month_days = models.get_month_days(2016, 3);
            let current = _.pluck(month_days.current_persons(), 'id');
            'A B C DiffDept Ext Other Z'.split(' ').forEach(function (id) {
                expect(current).toContain(id);
            });
            ['X', 'Y'].forEach(function (id) {
                expect(current).not.toContain(id);
            });

            models.days.reset();
        });

    });
    describe("Changes", function () {
        beforeEach(function () {
            // initialize August 3 through 7
            models.days.reset();
            models.days.get_day(new Date(2015, 7, 3));
            models.days.get_day(new Date(2015, 7, 7));
        });
        afterEach(function () {
            models.days.reset();
        });
        function test_staffing(day_or_day_id, person_shortnames) {
            if (_.isString(day_or_day_id)) {
                expect(models.days.get(day_or_day_id)
                    .ward_staffings.A.pluck('shortname'))
                    .toEqual(person_shortnames);
            } else {
                expect(day_or_day_id
                    .ward_staffings.A.pluck('shortname'))
                    .toEqual(person_shortnames);
            }
        }
        function test_duties(day_or_day_id, staff_ids) {
            if (_.isString(day_or_day_id)) {
                expect(models.days.get(day_or_day_id)
                    .persons_duties.A.pluck('shortname'))
                    .toEqual(staff_ids);
            } else {
                expect(day_or_day_id
                    .persons_duties.A.pluck('shortname'))
                    .toEqual(staff_ids);
            }
        }
        function make_change(options) {
            models.apply_change({
                person: 'A', ward: 'A',
                day: options.day,
                action: options.action,
                continued: options.continued,
                until: options.until,
            });
        }
        it("should apply changes", function () {
            const yesterday = models.days.get('20150803');
            const today = models.days.get('20150804');
            const tomorrow = models.days.get('20150805');
            make_change({
                day: '20150804', action: 'add',
                continued: true,
            });
            test_staffing(yesterday, []);
            test_duties(yesterday, []);
            test_staffing(today, ['A']);
            test_duties(today, ['A']);
            test_staffing(tomorrow, ['A']);
            test_duties(tomorrow, ['A']);
        });
        it("should preserve a later planning, " +
            "if a previous duty is started", function () {
                const tomorrow = models.days.get('20150805');
                make_change({  // add from today
                    day: '20150804', action: 'add', continued: true,
                });
                make_change({  // remove tomorrow
                    day: '20150805', action: 'remove', continued: true,
                });
                make_change({  // add from yesterday
                    day: '20150803', action: 'add', continued: true,
                });
                test_staffing(tomorrow, []);
                test_duties(tomorrow, []);
            });
        it("should preserve a later planning, " +
            "if a previous duty ends", function () {
                const tomorrow = models.days.get('20150805');
                make_change({  // add from tomorrow
                    day: '20150805', action: 'add', continued: true,
                });
                make_change({  // add from yesterday
                    day: '20150803', action: 'add', continued: true,
                });
                make_change({  // remove today
                    day: '20150804', action: 'remove', continued: true,
                });
                test_staffing(tomorrow, ['A']);
                test_duties(tomorrow, ['A']);
            });
        it("should apply a change with an end", function () {
            make_change({
                day: '20150803', action: 'add', continued: true,
                until: '20150804',
            });
            test_staffing('20150803', ['A']);
            test_staffing('20150804', ['A']);
            test_staffing('20150805', []);
        });
        it("should apply a remove with an end", function () {
            test_staffing('20150803', []);
            make_change({
                day: '20150803', action: 'add', continued: false,
            });
            make_change({
                day: '20150805', action: 'add', continued: true,
            });
            make_change({
                day: '20150803', action: 'remove', continued: true,
                until: '20150805',
            });
            test_staffing('20150803', []);
            test_staffing('20150804', []);
            test_staffing('20150805', []);
            test_staffing('20150806', ['A']);
        });
        it("should apply changes over other plannings when there is an end", function () {
            make_change({
                day: '20150804', action: 'add', continued: false,
            });
            make_change({
                day: '20150806', action: 'add', continued: true,
            });
            make_change({
                day: '20150803', action: 'add', continued: true,
                until: '20150806',
            });
            test_staffing('20150803', ['A']);
            test_staffing('20150804', ['A']);
            test_staffing('20150805', ['A']);
            test_staffing('20150806', ['A']);
        });
        describe("process_changes", function () {
            const data = {
                cls: [
                    {
                        person: 'A', ward: 'A', action: 'add', pk: 14,
                        continued: false, day: "20150805"
                    },
                    {
                        person: 'B', ward: 'A', action: 'add', pk: 15,
                        continued: true, day: "20150804"
                    },
                ],
                last_change: {
                    pk: 15,
                    time: 240,
                }
            };
            beforeEach(function () {
                spyOn(models, 'schedule_next_update');
                models.process_changes(data);
            });
            it("should apply the transmitted changes", function () {
                test_staffing('20150803', []);
                test_staffing('20150804', ['B']);
                test_staffing('20150805', ['A', 'B']);
                test_staffing('20150806', ['B']);
            });
            it("should set last_change", function () {
                expect(models.schedule_next_update).toHaveBeenCalledWith(
                    data.last_change);
            });
        });
    });
});
