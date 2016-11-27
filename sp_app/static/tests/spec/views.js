describe("views", function() {
    describe("StaffingView", function() {
        describe("with usual Staffing", function() {
            var monday = new models.Day({ date: new Date(2016, 10, 28) });
            var staffingview = new views.StaffingView({
                collection: monday.ward_staffings.A,
            });
            beforeEach(function() {
                spyOn(changeviews.staff, 'show');
            });
            it("should show changeviews.staff if the user can change plannings", function() {
                models.user_can_change = true;
                staffingview.addstaff();
                expect(changeviews.staff.show).toHaveBeenCalled();
            });
            it("should not show changeviews.staff if the user cannot change plannings", function() {
                models.user_can_change = false;
                staffingview.addstaff();
                expect(changeviews.staff.show).not.toHaveBeenCalled();
            });
        });
        describe("with 'no_staffing'", function() {
            var sunday = new models.Day({ date: new Date(2016, 10, 27) });
            var staffingview = new views.StaffingView({
                collection: sunday.ward_staffings.A,
            });
            beforeEach(function() {
                spyOn(changeviews.staff, 'show');
            });
            it("should not show changeviews.staff if the user can change plannings", function() {
                models.user_can_change = true;
                staffingview.addstaff();
                expect(changeviews.staff.show).not.toHaveBeenCalled();
            });
            it("should not show changeviews.staff if the user cannot change plannings", function() {
                models.user_can_change = false;
                staffingview.addstaff();
                expect(changeviews.staff.show).not.toHaveBeenCalled();
            });
        });
    });
});