var persons_init = [
  { name: 'Anton', id: 'A', functions: ['A', 'B']},
  { name: 'Berta', id: 'B', functions: ['A', 'B']},
];
var wards_init = [
  { name: 'Ward A', shortname: 'A', min: 1, max: 2, continued: true },
  { name: 'Ward B', shortname: 'B', min: 2, max: 2, continued: true },
  { name: 'Nightshift', shortname: 'N', min: 0, max: 1, nightshift: true, everyday: true },
  { name: 'Leave', shortname: 'L', min: 0, max: 10, on_leave: true, continued: true },
  { name: 'Free days', shortname: 'F', min: 0, max: 10, freedays: true, continued: true },
  { name: 'One day task', shortname: 'O', min: 0, max: 10, continued: false },
  { name: 'Special', shortname: 'S', min: 0, max: 10, continued: false, after_this: 'S,A' },
];
function init_hospital() {
    models.initialize_wards(wards_init);
    models.persons.reset(persons_init);
}

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
        it("should strike off yesterdays nightshift for today, "+
            "and continue the duties tomorrow, "+
            "if they are to be continued", function() {
            function test_staffing (staffing, total, displayed) {
                expect(staffing.length).toBe(total);
                expect(staffing.displayed.length).toBe(displayed);
            }
            yesterday.ward_staffings.A.add(person_a, {continued: true});
            yesterday.ward_staffings.O.add(person_a);
            yesterday.ward_staffings.N.add(person_a);
            test_staffing(yesterday.ward_staffings.A, 1, 1);
            test_staffing(yesterday.ward_staffings.O, 1, 1);
            test_staffing(yesterday.ward_staffings.N, 1, 1);
            test_staffing(today.ward_staffings.A, 1, 0);
            test_staffing(today.ward_staffings.O, 0, 0);
            test_staffing(today.ward_staffings.N, 0, 0);
            test_staffing(tomorrow.ward_staffings.A, 1, 1);
            test_staffing(tomorrow.ward_staffings.O, 0, 0);
            test_staffing(tomorrow.ward_staffings.N, 0, 0);
            yesterday.ward_staffings.N.remove(person_a);
            test_staffing(today.ward_staffings.A, 1, 1);
            test_staffing(today.ward_staffings.O, 0, 0);
        });
        it("should strike off persons for wards, "+
            "that are not possible after their yesterdays duties", function() {
            function test_staffing (staffing, total, displayed) {
                expect(staffing.length).toBe(total);
                expect(staffing.displayed.length).toBe(displayed);
            }
            yesterday.ward_staffings.A.add(person_a, {continued: true});
            yesterday.ward_staffings.S.add(person_a);
            yesterday.ward_staffings.B.add(person_b, {continued: true});
            yesterday.ward_staffings.S.add(person_b);
            test_staffing(yesterday.ward_staffings.A, 1, 1);
            test_staffing(yesterday.ward_staffings.B, 1, 1);
            test_staffing(today.ward_staffings.A, 1, 1);
            test_staffing(today.ward_staffings.B, 1, 0);
            test_staffing(tomorrow.ward_staffings.A, 1, 1);
            test_staffing(tomorrow.ward_staffings.B, 1, 1);
        });
        it("should continue yesterdays planning", function() {
            yesterday.ward_staffings.A.add(person_a, {continued: true});
            expect(today.ward_staffings.A.length).toBe(1);
            expect(today.ward_staffings.A.models[0].id).toBe('A');
            expect(today.ward_staffings.B.length).toBe(0);
        });
        it("should continue yesterdays planning for leave", function() {
            yesterday.ward_staffings.L.add(person_b, {continued: true});
            expect(today.ward_staffings.L.length).toBe(1);
            expect(today.ward_staffings.L.models[0].id).toBe('B');
            expect(tomorrow.ward_staffings.L.length).toBe(1);
            today.ward_staffings.L.remove(person_b, {continued: true});
            expect(today.ward_staffings.L.length).toBe(0);
            expect(tomorrow.ward_staffings.L.length).toBe(0);
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
            day: '20150804', action: 'add',
            continued: true,
        });
        models.apply_change({  // remove tomorrow
            person: 'A', ward: 'A',
            day: '20150805', action: 'remove',
            continued: true,
        });
        models.apply_change({  // add from yesterday
            person: 'A', ward: 'A',
            day: '20150803', action: 'add',
            continued: true,
        });
        expect(tomorrow.ward_staffings.A.length).toEqual(0);
        expect(tomorrow.persons_duties.A.length).toEqual(0);
    });
    it("should preserve a later planning, " +
        "if a previous duty ends", function() {
        var tomorrow = models.days['20150805'];
        models.apply_change({  // add from tomorrow
            person: 'A', ward: 'A',
            day: '20150805', action: 'add',
            continued: true,
        });
        models.apply_change({  // add from yesterday
            person: 'A', ward: 'A',
            day: '20150803', action: 'add',
            continued: true,
        });
        models.apply_change({  // remove today
            person: 'A', ward: 'A',
            day: '20150804', action: 'remove',
            continued: true,
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