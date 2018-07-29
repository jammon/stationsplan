var changeviews = (function($, _, Backbone) {
"use strict";

var MS_PER_DAY = 24 * 60 * 60 * 1000;

var ChangeStaffView = Backbone.View.extend({
    // Change the Staffing of one Ward on one Day
    events: {
        "click #continued": "continued",
        "click #time_period": "time_period",
        "dblclick .changestaff": "one_click_plan",
        "changeDate": "date_changed",
    },
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
        this.current_date = day.get('date');
        var datestr = utils.day_long_names[this.current_date.getDay()] +
            ', ' + utils.datestr(this.current_date);
        var changestafftable = this.$("#changestafftable").empty();
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
        this.date_widget = this.$("#date-picker");
        this.date_widget.datepicker({
            format: "dd.mm.yyyy",
            weekStart: 1,
            language: "de",
            defaultViewDate: this.current_date,
        });
        this.date_widget.datepicker('setStartDate', this.current_date);
        this.date_widget.datepicker('setDate', this.current_date);
        this.date_widget.datepicker('update', this.current_date);
        return this;
    },
    date_changed: function(event) {
        var days = Math.round((event.date - this.current_date) / MS_PER_DAY) + 1;
        $('#time_period').text(
            "bis " +
            this.date_widget.datepicker('getFormattedDate') +
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
    // Subview for ChangeStaffView for changing the planning of one Person
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
    // Approve the plannings of one or more Wards until a given day
    events: {
        "click #approve-to-date": "approve",
        "click #approve-all": "approve_all",
        "changeDate": "approval_date_changed",
    },
    render: function() {
        this.$("#changeapprovaltable").append(
            models.wards.map(function(ward) {
                var view = new SelectStaffingView({ward: ward});
                return view.render().$el;
            }));
        var today = new Date();
        this.date_widget = this.$("#approval-date-picker");
        this.date_widget.datepicker({
            format: "dd.mm.yyyy",
            weekStart: 1,
            language: "de",
            defaultViewDate: today,
        });
        this.date_widget.datepicker('setDate', today);
        this.date_widget.datepicker('update', today);
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
        var date = this.date_widget.datepicker('getFormattedDate');
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
    // Subview for ApproveStaffingsView for selecting a Ward
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


var QuickInputView = Backbone.View.extend({
    // Quickly key in the the Staffing of On-Call-Shifts
    // - Shows possible Persons
    // - Greys out unavailable Persons
    // - Shows current date and 3(?) days before and after
    // - Click on a Person 
    //   - deletes the previous planning
    //   - plans the Person
    //   - advances the current date
    events: {
        "click .next_day": "next_day",
        "click .prev_day": "prev_day",
    },
    TOTAL_NR_DAYS: 5,
    NR_DAYS_BEFORE: 2,
    render: function() {
        this.days_table = this.$el.$("#quickdays");
        this.persons_div = this.$el.$("#quickpersons");
        var day, staffing,  dv, i;
        this.day_views = {};
        this.days = {};
        this.displayed_dayviews = [];
        for (i = -this.NR_DAYS_BEFORE; 
             i < this.TOTAL_NR_DAYS - this.NR_DAYS_BEFORE; i++) {
            day = this.get_day(i);
            dv = this.get_day_view(day);
            this.days_table.append(dv.render().$el);
            if (i === 0) dv.$el.addClass("current");
            this.displayed_dayviews.push(dv);
        }
        this.offset_current = 0;

        var ward = this.ward;
        this.person_views = _.map(
            models.persons.filter(function(person) {
                return person.can_work_on(ward);
            }),
            function(person) {
                var pv = new QuickPersonView({ model: person });
                this.persons_div.append(
                    pv.render().new_day(day, ward).$el);
                return pv;
            }, this);
        return this;
    },
    show: function(ward, start_date) {
        // `ward` is the ward
        // `start_date` is the first day edited
        this.new_staffings = {};
        this.ward = ward;
        this.start_date = start_date;
        this.render().$el.modal('show');
    },
    next_day: function() { this.change_day(true); },
    prev_day: function() { this.change_day(false); },
    change_day: function(forward) {
        var dvs = this.displayed_dayviews;
        var dv;
        dvs[this.NR_DAYS_BEFORE].blur();
        if (forward) {
            dvs.shift().remove();
            this.offset_current += 1;
            dv = this.get_day_view(this.offset_current - this.NR_DAYS_BEFORE +
                this.TOTAL_NR_DAYS);
            this.days_table.append(dv.render().$el);
            dvs.push(dv);
        } else {
            dvs.pop().remove();
            this.offset_current -= 1;
            dv = this.get_day_view(this.offset_current - this.NR_DAYS_BEFORE);
            this.days_table.prepend(dv.render().$el);
            dvs.unshift(dv);
        }
        dvs[this.NR_DAYS_BEFORE].focus();
        this.displayed_dayviews = dvs;
        var day = this.get_day(this.offset_current);
    },
    update_personviews: function(day, ward) {
        _.each(this.person_views, function(pv) {
            pv.new_day(day, ward);
        });
    },
    get_day: function(offset) {
        if (!this.days[offset])
            this.days[offset] = models.days.get_day(
                this.start_date.getYear(),
                this.start_date.getMonth(),
                this.start_date.getDate() + offset);
        return this.days[offset]
    },
    get_day_view: function(offset) {
        var day = this.get_day(offset);
        var dv = this.day_views[day.id];
        if (dv) return dv;
        var staffing = day.ward_staffings[this.ward.id];
        dv = new QuickInputDayView({ 
            date: day.get('date'),
            name: this.new_staffings[day.id] || 
                staffing.first().get('name') || '',
        });
        this.day_views[day.id] = dv;
        return dv;
    },
});
var quickinputview = new QuickInputView({
    el: $("#quickinput"),
});
var QuickInputDayView = Backbone.View.extend({
    tagName: 'tr',
    template: _.template(
        "<td><%= day %>.<%= month %>.</td><td><%= name %></td>"),
    initialize: function(options) {
        // options should contain { date: …, name: … }
        this.day = options.date.getDate();
        this.month = options.date.getMonth() + 1;
        this.name = options.name;
    },
    render: function() {
        this.$el.empty().append(this.template(this));
        return this;
    },
    set_name: function(name) {
        this.name = name;
        this.render();
    },
    focus: function() { this.$el.addClass("current"); },
    blur: function() { this.$el.removeClass("current"); },
});
var QuickPersonView = new Backbone.View.extend({
    tagName: 'button',
    className: 'quickperson',
    render: function() {
        this.$el.text(this.model.get("name"))
            .val(this.model.get("id"));
        return this;
    },
    new_day: function(day, ward) {
        if (day.ward_staffings[ward.id].can_be_planned(this.model))
            this.$el.removeClass("unavailable");
        else
            this.$el.addClass("unavailable");
        return this;
    },
});

return {
    staff: changestaffview,
    approve: approvestaffingview,
    quickinput: quickinputview,
};
})($, _, Backbone);
