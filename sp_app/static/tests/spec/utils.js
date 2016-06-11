describe("utils", function() {
    describe("function is_free", function() {
        it("should identify weekdays", function() {
            expect(utils.is_free(new Date(2015, 7, 7))).toBe(false);  // Friday
            expect(utils.is_free(new Date(2015, 7, 8))).toBe(true);  // Saturday
            expect(utils.is_free(new Date(2015, 7, 9))).toBe(true);  // Sunday
            expect(utils.is_free(new Date(2015, 7, 10))).toBe(false);  // Monday
        });
        it("should identify special holidays", function() {
            expect(utils.is_free(new Date(2015, 9, 3))).toBe(true);
            expect(utils.is_free(new Date(2015, 11, 24))).toBe(true);
        });
    });
    describe("function get_next_month", function() {
        it("should calculate the next month", function() {
            expect(utils.get_next_month(2016, 5)).toEqual({ year: 2016, month: 6 });
            expect(utils.get_next_month(2016, 0)).toEqual({ year: 2016, month: 1 });
            expect(utils.get_next_month(2016, 11)).toEqual({ year: 2017, month: 0 });
        });
    });
    describe("calculating the id of the day (get_day_id)", function() {
        it("should calculate usual date to an id", function() {
            function test_get_day_id(year, month, day, id) {
                expect(utils.get_day_id(year, month, day)).toBe(id);
                expect(utils.get_day_id(new Date(year, month, day))).toBe(id);
            }
            test_get_day_id(2015, 0, 1, "20150101");
            test_get_day_id(2015, 7, 30, "20150830");
            test_get_day_id(2015, 11, 31, "20151231");
            test_get_day_id(1999, 11, 31, "19991231");
        });
    });
});
