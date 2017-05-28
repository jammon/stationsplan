var changeviews = (function($, _, Backbone) {
"use strict";

var MS_PER_DAY = 24 * 60 * 60 * 1000;
var current_date;

var ChangeStaffView = Backbone.View.extend({
    events: {
        "click #one-day": "one_day",
        "click #continued": "continued",
        "click #time_period": "time_period",
        "dblclick .changestaff": "one_click_plan",
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
        var min_staffing = staffing.ward.get('min');
        this.no_dblclick = (min_staffing && min_staffing>1);
        current_date = day.get('date');
        var datestr = utils.day_long_names[current_date.getDay()] +
            ', ' + utils.datestr(current_date);
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
    one_click_plan: function() {
        if (this.no_dblclick) return;
        _.each(this.change_person_views, function(cpv) {
            if (cpv.is_dblclicked) {
                if (!cpv.is_planned) cpv.toggle_planned();
                cpv.is_dblclicked = false;
            } else {
                if (cpv.is_planned) cpv.toggle_planned();
            }
        });
        this.save(false);
    },
});
var changestaffview = new ChangeStaffView({
    el: $("#changestaff"),
});

var ChangePersonView = Backbone.View.extend({
    tagName: 'tr',
    events: {
        "click .changestaff": "toggle_planned",
        "dblclick .changestaff": "one_click_plan",
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
    },
    one_click_plan: function() {
        this.is_dblclicked = true;
    },
});

var ApproveStaffingsView = Backbone.View.extend({
    events: {
        "click #approve-to-date": "approve",
        "click #approve-all": "approve_all",
    },
    render: function() {
        this.$("#changeapprovaltable").append(
            models.wards.map(function(ward) {
                var view = new SelectStaffingView({ward: ward});
                return view.render().$el;
            }));
        var date_widget = this.$("#approval-date-picker");
        date_widget.datepicker({
            format: "dd.mm.yyyy",
            weekStart: 1,
            language: "de",
            defaultViewDate: current_date,
        });
        date_widget.datepicker('setDate', current_date);
        date_widget.datepicker('update', current_date);
        if (!this._changeDate_connected) {
            date_widget.on("changeDate", this.approval_date_changed);
            this._changeDate_connected = true;
        }
        this.rendered = true;
        return this;
    },
    show: function(ward) {
        if (!this.rendered) this.render();
        if (ward)
            this.$("input[value='" + ward.get('shortname') + "']")
                .attr('checked', true);
        this.$el.modal('show');
    },
    approval_date_changed: function() {
        var date = $("#approval-date-picker").datepicker('getFormattedDate');
        $('#approve-to-date').text("Bis " + date + " freigeben");
    },
    get_checked_wards: function() {
        return this.$("input:checked")
            .map(function() {
                return $( this ).val();
            })
            .get();
    },
    save: function(approval) {
        models.save_approval(this.get_checked_wards(), approval);
        this.$el.modal('hide');
    },
    approve: function() {
        this.save(this.$("#approval-date-picker").datepicker('getDate'));
    },
    approve_all: function() { this.save(false); },
});
var approvestaffingview = new ApproveStaffingsView({
    el: $("#approvestaffing"),
});

var SelectStaffingView = Backbone.View.extend({
    tagName: 'tr',
    initialize: function(options) {
        this.ward = options.ward;
        this.listenTo(this.ward, "change:approved", this.render);
    },
    template: _.template($('#approve_staffing_template').html()),
    render: function() {
        var approved = this.ward.get('approved');
        var currentapproval =
            approved ? utils.datestr(approved) : "offen";
        this.$el.empty().append(this.template({
            ward: this.ward.get('name'),
            ward_id: this.ward.get('shortname'),
            currentapproval: currentapproval,
        }));
        return this;
    },
});

return {
    staff: changestaffview,
    approve: approvestaffingview,
};
})($, _, Backbone);
