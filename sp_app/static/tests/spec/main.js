// jshint esversion: 6
describe("main", function () {
    describe("initialize_site", function () {
        beforeEach(function () {
            spyOn(models, "initialize_wards");
            spyOn(models.persons, "reset");
            spyOn(models, "set_plannings");
            spyOn(utils, "set_holidays");
            spyOn(models, "start_day_chain");
            spyOn(models, "schedule_next_update");
            spyOn(Backbone.history, "start");
        });
        it("should initialize correctly", function () {
            main.initialize_site({
                is_company_admin: false,
                is_dep_lead: true,
                is_editor: true,
                departments: { 1: "Dep1", 2: "Dep2" },
                wards: "wards",
                different_days: "different_days",
                persons: "persons",
                plannings: "plannings",
                holidays: "holidays",
                data_month: 3,
                data_year: 2022,
                last_change_pk: 15678,
                last_change_time: 576,
            });

            expect(models.user.is_editor).toBe(true);
            expect(models.user.is_dep_lead).toBe(true);
            expect(models.user.is_company_admin).toBe(false);
            expect(models.user.current_department).toEqual(1);
            expect(models.initialize_wards).toHaveBeenCalledWith(
                "wards", "different_days");
            expect(models.persons.reset).toHaveBeenCalledWith("persons");
            expect(models.set_plannings).toHaveBeenCalledWith("plannings");
            expect(utils.set_holidays).toHaveBeenCalledWith("holidays");
            expect(models.start_day_chain).toHaveBeenCalledWith(2022, 3);
            expect(models.schedule_next_update).toHaveBeenCalledWith({
                pk: 15678,
                time: 576
            });
            expect(Backbone.history.start).toHaveBeenCalled();
        });
    });
});
