var changeviews = (function($, _, Backbone) {
"use strict";

var MS_PER_DAY = 24 * 60 * 60 * 1000;
var current_date;

var ChangeStaffView = Backbone.View.extend({
    events: {
        "click #one-day": "one_day",
        "click #continued": "continued",
        "click #time_period": "time_period",
    },
    one_day: function() { this.save(false); },
    continued: function() { this.save(true); },
    time_period: function(e) { 
        this.save(this.$("#date-picker").datepicker('getDate'));
    },
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
        current_date = day.get('date');
        var datestr = utils.datestr(current_date);
        var changestafftable = this.$("#changestafftable").empty();
        var date_widget = this.$("#date-picker");
        var that = this;
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
                view.on("person_toggled", that.calc_changes, that);
                return view;
            });
        this.$("#date-picker input").val(datestr);
        date_widget.datepicker({
            format: "dd.mm.yyyy",
            weekStart: 1,
            language: "de",
            defaultViewDate: current_date,
        });
        if (!this._changeDate_connected) {
            date_widget.on("changeDate", this.date_changed);
            this._changeDate_connected = true;
        }
        date_widget.datepicker('setStartDate', current_date);
        date_widget.datepicker('setDate', current_date);
        date_widget.datepicker('update', current_date);
        return this;
    },
    date_changed: function(event) {
        var date_widget = $("#date-picker");
        var days = Math.round((event.date - current_date) / MS_PER_DAY) + 1;
        $('#time_period').text(
            "bis " +
            date_widget.datepicker('getFormattedDate') +
            " = " +
            days +
            (days>1 ? " Tage" : " Tag")
        );
    },
    show: function(staffing) {
        this.staffing = staffing;
        this.render().calc_changes().$el.modal('show');
    },
    calc_changes: function() {
        this.changes = this.collect_changes();
        this.$(".submitbuttons button").toggleClass("disabled", this.changes.length===0);
        return this;
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
        this.trigger("person_toggled");
    }
});


return {
    staff: changestaffview,
};
})($, _, Backbone);
