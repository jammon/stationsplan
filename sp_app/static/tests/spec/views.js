describe("views", function() {
    beforeEach(init_hospital);
    describe("StaffingView", function() {
        describe("with usual Staffing", function() {
            var monday, staffingview;
            beforeEach(function() {
                monday = new models.Day({ date: new Date(2016, 10, 28) });
                staffingview = new views.StaffingView({
                    collection: monday.ward_staffings.A,
                });
                spyOn(changeviews.staff, 'show');
            });
            it("should show changeviews.staff if the user can change plannings", function() {
                models.user.is_editor = true;
                staffingview.addstaff();
                expect(changeviews.staff.show).toHaveBeenCalled();
                models.user.is_editor = false;
            });
            it("should not show changeviews.staff if the user cannot change plannings", function() {
                staffingview.addstaff();
                expect(changeviews.staff.show).not.toHaveBeenCalled();
            });
        });
        describe("with 'no_staffing'", function() {
            var sunday, staffingview;
            beforeEach(function() {
                sunday = new models.Day({ date: new Date(2016, 10, 27) });
                staffingview = new views.StaffingView({
                    collection: sunday.ward_staffings.A,
                });
                spyOn(changeviews.staff, 'show');
            });
            it("should not show changeviews.staff if the user can change plannings", function() {
                models.user.is_editor = true;
                staffingview.addstaff();
                expect(changeviews.staff.show).not.toHaveBeenCalled();
                models.user.is_editor = false;
            });
            it("should not show changeviews.staff if the user cannot change plannings", function() {
                staffingview.addstaff();
                expect(changeviews.staff.show).not.toHaveBeenCalled();
            });
        });
    });
});