var changeviews = (function($, _, Backbone) {
"use strict";


var ChangeStaffView = Backbone.View.extend({
    events: {
        "click #one-day": "one_day",
        "click #continued": "continued",
    },
    one_day: function() { this.save(false); },
    continued: function() { this.save(true); },
    save: function(continued) {
        models.save_change({
            day: this.staffing.day.id,
            ward: this.staffing.ward,
            continued: continued,
            persons: this.collect_changes(),
        });
        this.$el.modal('hide');
    },
    collect_changes: function() {
        return _.reduce(
            this.change_person_views,
            function(memo, cpv) { 
                if (cpv.is_changed) {
                    memo.push({
                       id: cpv.person.id,
                       action: cpv.is_planned ? 'add' : 'remove',
                    });
                }
                return memo;
            },
            []);
    },
    render: function() {
        var staffing = this.staffing;
        var day = this.staffing.day;
        var cur_date = day.get('date');
        var datestr = utils.datestr(cur_date);
        var changestafftable = this.$("#changestafftable").empty();
        this.$(".changedate").text(datestr);
        this.$(".changeward").text(staffing.ward.get('name'));
        this.change_person_views = _.map(
            day.get_available(staffing.ward),
            function(person) {
                var view = new ChangePersonView({
                    person: person,
                    staffing: staffing,
                    day: day,
                });
                view.render();
                view.$el.appendTo(changestafftable);
                return view;
            });
        this.$("#date-picker input").val(datestr);
        var date_widget = this.$("#date-picker");
        date_widget.datepicker({
            format: "dd.mm.yyyy",
            weekStart: 1,
            language: "de",
        });
        date_widget.datepicker("setDate", cur_date);
        date_widget.datepicker("setStartDate", cur_date);
        // date_widget.datepicker("setEndDate", ?);
        // setDatesDisabled, setDaysOfWeekDisabled
        return this;
    },
    show: function(staffing) {
        this.staffing = staffing;
        this.render().$el.modal('show');
    },
});
var changestaffview = new ChangeStaffView({
    el: $("#changestaff"),
});

var ChangePersonView = Backbone.View.extend({
    tagName: 'tr',
    events: {
        "click .changestaff": "toggle_planned",
    },
    template: _.template($('#change_person_template').html()),
    initialize: function(options) {
        this.person = options.person;
        this.staffing = options.staffing;
        this.duties = options.day.persons_duties[this.person.id];
        this.is_planned = this.staffing.contains(this.person);
        this.is_changed = false;
    },
    render: function() {
        this.$el.empty().append(this.template({
            name: this.person.get('name'),
            duties: this.duties.pluck('shortname').join(', '),
        }));
        this.toggleClasses();
    },
    toggleClasses: function() {
        this.$('.changestaff')
            .toggleClass('btn-info', !this.is_planned)
            .toggleClass('btn-primary', this.is_planned)
            .toggleClass('changed', this.is_changed);
    },
    toggle_planned: function() {
        this.is_planned = !this.is_planned;
        this.is_changed = !this.is_changed;
        this.toggleClasses();
    }
});


return {
    staff: changestaffview,
};
})($, _, Backbone);
