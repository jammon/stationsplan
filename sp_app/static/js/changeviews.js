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
        models.save_change(this.staffing.day,
                           this.staffing.ward, 
                           continued,
                           this.collect_changes());
        this.$el.modal('hide');
    },
    collect_changes: function() {
        return _.reduce(
            this.change_person_views,
            function(memo, cpv) { 
                if (cpv.is_changed) {
                    memo.push({
                       id: cpv.person.get('id'),
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
    // - Shows current date and 2(?) days before and after
    // - Click on a Person 
    //   - deletes the previous planning
    //   - plans the Person
    //   - advances the current date
    events: {
        "click .next_day": "next_day",
        "click .prev_day": "prev_day",
        "plan_person": "plan_person",
    },
    render: function() {
        var ward = this.ward;
        this.$(".ward_name").text(ward.get('name'));

        this.day_views = new QuickDateViews({
            ward: this.ward,
            start_date: this.start_date,
        });
        this.day_views.render();

        var persons_div = this.$("#quickpersons");
        var day = models.days.get_day(this.start_date);
        if (!this.person_views) {
            this.person_views = [];
            _.each(
                models.persons.filter(function(person) {
                    return person.can_work_on(ward);
                }),
                function(person) {
                    var pv = new QuickPersonView({ 
                        model: person,
                        day: day,
                        ward: ward,
                    });
                    persons_div.append(
                        pv.render().$el);
                    this.person_views.push(pv);
                    this.listenTo(pv, 'plan_person', this.plan_person);
                }, this);
        } else {
            _.each(this.person_views, function(pv) {
                pv.new_day(day);
            });
        }

        return this;
    },
    show: function(ward, start_date) {
        // `ward` is the ward
        // `start_date` is the first day edited
        this.ward = ward;
        delete this.person_views;
        this.start_date = start_date;
        this.render().$el.modal('show');
    },
    new_date: function(date) {
        var day = models.days.get_day(date);
        this.start_date = date;
        _.each(this.person_views, function(pv) {
            pv.new_day(day);
        });
    },
    next_day: function() { 
        this.change_day(true);
        this.day_views.next_day();
    },
    prev_day: function() { 
        this.change_day(false);
        this.day_views.prev_day();
    },
    change_day: function(forward) {
        var ONEDAY = 24 * 60 * 60 * 1000;
        this.new_date(new Date(
            this.start_date.getTime() + (forward ? ONEDAY : -ONEDAY)));
    },
    plan_person: function(person, staffing) {
        var persons = [{ id: person.get('id'), action: 'add' }];
        if (staffing.length>0)
            persons.push({ id: staffing.at(0).id, action: 'remove' });
        models.save_change(staffing.day,
                           staffing.ward,
                           false,
                           persons);
        this.next_day();
    },
});
var quickinputview = new QuickInputView({
    el: $("#quickinput"),
});
var QuickPersonView = Backbone.View.extend({
    tagName: 'button',
    className: 'quickperson btn btn-default btn-block',
    events: {click: 'plan_person'},
    initialize: function(options) {
        this.ward = options.ward;
        this.new_day(options.day);
    },
    new_day: function(day) {
        this.staffing = day.ward_staffings[this.ward.id];
        return this;
    },
    is_unavailable: function() {
        return !this.staffing.can_be_planned(this.model);
    },
    render: function() {
        this.$el.empty().text(this.model.get("name"))
            .val(this.model.get("id"));
        if (this.is_unavailable())
            this.$el.attr("disabled", "disabled");
        return this;
    },
    plan_person: function() {
        this.trigger('plan_person', this.model, this.staffing);
    },
});
var QuickDateView = Backbone.View.extend({
    tagName: 'tr',
    template: _.template(
        "<td><%= day_name %>, <%= day %>.<%= month %>.</td><td><%= name %></td>"),
    initialize: function() {
        this.listenTo(this.collection.displayed, "update", this.render);
    },
    set_active: function(active) {
        this.active = active;
    },
    render: function() {
        var date = this.collection.day.get('date');
        var name = '';
        if (this.collection.length>0)
            name = this.collection.first().get('name');
        this.$el.html(this.template({
            day_name: utils.day_names[date.getDay()],
            day: date.getDate(),
            month: date.getMonth()+1,
            name: name,
        }));
        if (this.active)
            this.$el.addClass('active');
        else
            this.$el.removeClass('active');
        return this;
    },
});
var QuickDateViews = Backbone.View.extend({
    el: "#quickdays",
    NR_DAYS_BEFORE: 2,
    NR_DAYS_AFTER: 2,
    initialize: function(options) {
        this.start_date = options.start_date;
        this.ward = options.ward;
        this.views = {};
        this.offset = 0;
    },
    get_view: function(offset) {
        if (this.views[offset])
            return this.views[offset];
        var day = models.days.get_day(this.start_date, offset);
        var staffing = day.ward_staffings[this.ward.id];
        var view = new QuickDateView({collection: staffing});
        view.render();
        this.views[offset] = view;
        return view;
    },
    render: function() {
        this.$el.empty();
        var day, dv, i, staffing;
        for (i = this.offset - this.NR_DAYS_BEFORE; 
             i <= this.offset + this.NR_DAYS_AFTER; i++) {
            dv = this.get_view(i);
            dv.set_active(i === this.offset);
            this.$el.append(dv.render().el);
        }
        return this;
    },
    next_day: function() {
        this.offset += 1;
        this.render();
    },
    prev_day: function() {
        this.offset -= 1;
        this.render();
    },
});

return {
    staff: changestaffview,
    approve: approvestaffingview,
    quickinput: quickinputview,
    test: {
        QuickInputView: QuickInputView,
    },
};
})($, _, Backbone);
