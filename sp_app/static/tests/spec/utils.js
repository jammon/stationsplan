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
    describe("function get_month_id", function() {
        it("should calculate the id of the month", function() {
            expect(utils.get_month_id(2016, 5)).toEqual('201606');
            expect(utils.get_month_id(2016, 0)).toEqual('201601');
            expect(utils.get_month_id(2016, 11)).toEqual('201612');
        });
    });
    describe("function get_previous_month_id", function() {
        it("should calculate the id of the previous month", function() {
            expect(utils.get_previous_month_id('201606')).toEqual('201605');
            expect(utils.get_previous_month_id('201601')).toEqual('201512');
            expect(utils.get_previous_month_id('201612')).toEqual('201611');
        });
    });
    describe("function get_next_month_id", function() {
        it("should calculate the id of the next month", function() {
            expect(utils.get_next_month_id('201606')).toEqual('201607');
            expect(utils.get_next_month_id('201601')).toEqual('201602');
            expect(utils.get_next_month_id('201612')).toEqual('201701');
        });
    });
    describe("function get_year_month", function() {
        it("should calculate the year/month from a month_id", function() {
            expect(utils.get_year_month('201606')).toEqual({ year: 2016, month: 5 });
            expect(utils.get_year_month('201601')).toEqual({ year: 2016, month: 0 });
            expect(utils.get_year_month('201612')).toEqual({ year: 2016, month: 11 });
        });
    });
    describe("datestr", function() {
        it("should calculate the date strings", function() {
            expect(utils.datestr(new Date(2016, 0, 1)))
                .toEqual("1.1.2016");
            expect(utils.datestr(new Date(2016, 11, 31)))
                .toEqual("31.12.2016");
            expect(utils.datestr(new Date(2016, 1, 29)))
                .toEqual("29.2.2016");
        });
    });
});