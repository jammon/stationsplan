var persons_init = [
  { name: 'Anton', id: 'A'},
  { name: 'Berta', id: 'B',},
];
var wards_init = [
  { name: 'Ward A', id: 'A', min: 1, max: 2, continued: true },
  { name: 'Ward B', id: 'B', min: 2, max: 2, continued: true },
  { name: 'Nightshift', id: 'N', min: 0, max: 1, nightshift: true, everyday: true },
  { name: 'Leave', id: 'L', min: 0, max: 10, on_leave: true, continued: true }
];
function init_hospital() {
    sp.initialize_wards(wards_init);
    sp.persons.reset(persons_init);
}

describe("function is_free", function() {
    it("should identify weekdays", function() {
        expect(is_free(new Date(2015, 7, 7))).toBe(false);  // Friday
        expect(is_free(new Date(2015, 7, 8))).toBe(true);  // Saturday
        expect(is_free(new Date(2015, 7, 9))).toBe(true);  // Sunday
        expect(is_free(new Date(2015, 7, 10))).toBe(false);  // Monday
    });
    it("should identify special holidays", function() {
        expect(is_free(new Date(2015, 9, 3))).toBe(true);
        expect(is_free(new Date(2015, 11, 24))).toBe(true);
    });
});
describe("Initializing data", function() {
    it("should have the persons and wards set", function() {
        init_hospital();
        expect(sp.persons.length).toBe(2);
        expect(sp.wards.length).toBe(4);
        var person_a = sp.persons.get('A');
        expect(person_a.get('name')).toBe('Anton');
        var ward_a = sp.wards.get('A');
        expect(ward_a.get('name')).toBe('Ward A');
        expect(ward_a.get('min')).toBe(1);
        expect(ward_a.get('max')).toBe(2);
        expect(ward_a.get('continued')).toBe(true);
    });
});
describe("Day", function() {
    init_hospital();
    var person_a = sp.persons.get('A');
    var person_b = sp.persons.get('B');
    var ward_a = sp.wards.get('A');
    it("should be initialized properly", function() {
        var today = new sp.Day({ date: new Date(2015, 7, 7) });
        expect(today.persons_duties).not.toEqual(undefined);
        expect(today.persons_duties.A.length).toBe(0);
        expect(today.ward_staffings).not.toEqual(undefined);
        expect(today.ward_staffings.A.length).toBe(0);
    });
    describe("check availability:", function() {
        function check_availability (action, nr_avail, first_avail) {
            var yesterday = new sp.Day({
                date: new Date(2015, 7, 6),
            });
            var today = new sp.Day({
                date: new Date(2015, 7, 7),
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
        it("who is planned for a ward isn't available any more", function() {
            check_availability(function(today, yesterday) {
                today.ward_staffings.A.add(person_a);
            },
            1, 'B');
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
    describe("interaction with previous planning", function() {
        var yesterday, today, tomorrow;
        beforeEach(function() {
            yesterday = new sp.Day({
                date: new Date(2015, 7, 5),
            });
            today = new sp.Day({
                date: new Date(2015, 7, 6),
                yesterday: yesterday,
            });
            tomorrow = new sp.Day({
                date: new Date(2015, 7, 7),
                yesterday: today,
            });
        });
        it("should check if on leave", function() {
            expect(today.is_on_leave(person_a)).toBe(false);
            today.ward_staffings.L.add(person_a);
            expect(today.is_on_leave(person_a)).toBe(true);
        });
        it("should check if somebody is on yesterdays nightshift", function() {
            expect(today.yesterdays_nightshift(person_a)).toBe(false);
            yesterday.ward_staffings.N.add(person_a);
            expect(today.yesterdays_nightshift(person_a)).toBe(true);
            expect(today.yesterdays_nightshift(person_b)).toBe(false);
        });
        it("should strike off yesterdays nightshift for today", function() {
            yesterday.ward_staffings.A.add(person_a);
            yesterday.ward_staffings.N.add(person_a);
            expect(yesterday.ward_staffings.A.length).toBe(1);
            expect(today.ward_staffings.A.length).toBe(0);
            expect(tomorrow.ward_staffings.A.length).toBe(1);
            yesterday.ward_staffings.N.remove(person_a);
            expect(today.ward_staffings.A.length).toBe(1);
        });
        it("should continue yesterdays planning", function() {
            yesterday.ward_staffings.A.add(person_a);
            expect(today.ward_staffings.A.length).toBe(1);
            expect(today.ward_staffings.A.models[0].id).toBe('A');
            expect(today.ward_staffings.B.length).toBe(0);
        });
        it("should continue yesterdays planning for leave", function() {
            yesterday.ward_staffings.L.add(person_b);
            expect(today.ward_staffings.L.length).toBe(1);
            expect(today.ward_staffings.L.models[0].id).toBe('B');
            today.ward_staffings.L.remove(person_b);
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
            yesterday.ward_staffings.L.add(person_a);
            expect(yesterday.get_available(ward_a).length).toBe(1);
            expect(today.get_available(ward_a).length).toBe(1);
            expect(tomorrow.get_available(ward_a).length).toBe(1);
            // back today
            today.ward_staffings.L.remove(person_a);
            expect(yesterday.get_available(ward_a).length).toBe(1);
            expect(today.get_available(ward_a).length).toBe(2);
            expect(tomorrow.get_available(ward_a).length).toBe(2);
        });
    });
    describe("calculating the id of the day", function() {
        it("should calculate usual date to an id", function() {
            expect(sp.Day.get_id(new Date(2015, 0, 1)))
                .toBe("20150101");
            expect(sp.Day.get_id(new Date(2015, 7, 30)))
                .toBe("20150830");
            expect(sp.Day.get_id(new Date(2015, 11, 31)))
                .toBe("20151231");
            expect(sp.Day.get_id(new Date(1999, 11, 31)))
                .toBe("19991231");
        });
    });
    describe("storing and retrieving", function() {
        it("should retrieve an empty day if it hasn't been stored", function() {
            var day = sp.Day.retrieve(new Date(2015, 0, 1));
            expect(day.ward_staffings.A.length).toBe(0);
            expect(day.ward_staffings.B.length).toBe(0);
            expect(day.ward_staffings.L.length).toBe(0);
            expect(day.ward_staffings.N.length).toBe(0);
            expect(day.get('yesterday')).toBe(undefined);
        });
        it("should retrieve an empty day if it has been stored empty", function() {
            var some_date = new Date(2015, 0, 1);
            var day, day2;
            day = new sp.Day({ date: some_date });
            day.store()
                .then(function() { day2 = sp.Day.retrieve(some_date); })
                // avoid pollution of the db
                .then(function() { return hoodie.store.remove('day', day.id, {silent: true});})
                .then(function() {
                    expect(day2.ward_staffings.A.length).toBe(0);
                    expect(day2.ward_staffings.B.length).toBe(0);
                    expect(day2.ward_staffings.L.length).toBe(0);
                    expect(day2.ward_staffings.N.length).toBe(0);
                    expect(day2.get('yesterday')).toBe(undefined);
                });
        });
        it("should retrieve a day with plannings", function() {
            var some_date = new Date(2015, 0, 1);
            var day, day2;
            day = new sp.Day({ date: some_date });
            day.ward_staffings.A.add(sp.persons.get('A'));
            day.ward_staffings.B.add(sp.persons.get('B'));
            day.store()
                .then(function() { 
                    day2 = sp.Day.retrieve(some_date); 
                })
                // avoid pollution of the db
                .then(function() { 
                    return hoodie.store.remove('day', day.id, {silent: true});
                })
                .then(function() {
                    expect(day2.ward_staffings.A.length).toBe(1);
                    expect(day2.ward_staffings.A.at(0).id).toBe('A');
                    expect(day2.ward_staffings.B.length).toBe(1);
                    expect(day2.ward_staffings.B.at(0).id).toBe('B');
                    expect(day2.ward_staffings.L.length).toBe(0);
                    expect(day2.ward_staffings.N.length).toBe(0);
                    expect(day2.get('yesterday')).toBe(undefined);
                });
        });
        it("should update the plannings", function() {
            var some_date = new Date(2015, 0, 1);
            var day, day2;
            day = new sp.Day({ date: some_date });
            day.ward_staffings.A.add(sp.persons.get('A'));
            day.store()
                .then(function() { 
                    day.ward_staffings.B.add(sp.persons.get('B'));
                    return day.store_update(day.ward_staffings.B);
                })
                .then(function() { 
                    day2 = sp.Day.retrieve(some_date); 
                })
                // avoid pollution of the db
                .then(function() { 
                    return hoodie.store.remove('day', day.id, {silent: true});
                })
                .then(function() {
                    expect(day2.ward_staffings.A.length).toBe(1);
                    expect(day2.ward_staffings.A.at(0).id).toBe('A');
                    expect(day2.ward_staffings.B.length).toBe(1);
                    expect(day2.ward_staffings.B.at(0).id).toBe('B');
                    expect(day2.ward_staffings.L.length).toBe(0);
                    expect(day2.ward_staffings.N.length).toBe(0);
                    expect(day2.get('yesterday')).toBe(undefined);
                });
        });
    });
});
describe("Persons", function() {
    it("should retrieve zero persons if there aren't any", function() {
        var persons = new sp.Persons();
        persons.retrieve()
            .then(function() {
                expect(persons.length).toBe(0);
            });
    });
    it("should retrieve persons that have been stored", function() {
        var p1 = new sp.Person({
            name: "Test Test",
            id: "test",
        });
        var p2 = new sp.Person({
            name: "Test Test2",
            id: "test2",
            start_date: new Date(2015, 0, 1),
            end_date: new Date(2015, 11, 31),
        });
        var persons = new sp.Persons();
        p1.store()
            .then(function() {
                return p2.store();
            })
            .then(function() {
                return persons.retrieve();
            })
            .then(function() {
                var p1, p2;
                expect(persons.length).toBe(2);
                p1 = persons.get("test");
                p2 = persons.get("test2");
                expect(p1.get("id")).toBe("test");
                expect(p2.get("id")).toBe("test2");
                expect(p1.get("name")).toBe("Test Test");
                expect(p2.get("name")).toBe("Test Test2");
            });
    });
});
describe("Wards", function() {
    it("should retrieve zero wards if there aren't any", function() {
        var wards = new sp.Wards();
        wards.retrieve()
            .then(function() {
                expect(wards.length).toBe(0);
            });
    });
    it("should retrieve wards that have been stored", function() {
        var w1 = new sp.Ward({
            name: "Ward A",
            id: "a",
            max: 3,
            min: 2,
        });
        var w2 = new sp.Ward({
            name: "Ward B",
            id: "b",
            max: 2,
            min: 1,
        });
        var wards = new sp.Wards();
        w1.store()
            .then(function() {
                return w2.store();
            })
            .then(function() {
                return wards.retrieve();
            })
            .then(function() {
                var w1_, w2_;
                expect(wards.length).toBe(2);
                w1_ = wards.get("a");
                w2_ = wards.get("b");
                expect(w1_.get("id")).toBe("a");
                expect(w2_.get("id")).toBe("b");
                expect(w1_.get("name")).toBe("Ward A");
                expect(w2_.get("name")).toBe("Ward B");
                expect(w1_.get("max")).toBe(3);
                expect(w2_.get("max")).toBe(2);
                expect(w1_.get("min")).toBe(2);
                expect(w2_.get("min")).toBe(1);
            });
    });
});
