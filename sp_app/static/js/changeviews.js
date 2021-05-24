// jshint esversion: 6
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
        this.show_changehistory();
    },
    calc_changes: function() {
        this.changes = this.collect_changes();
        this.$(".submitbuttons button").toggleClass("disabled", this.changes.length===0);
        return this;
    },
    show_changehistory: function() {
        let div = this.$("#changehistory");
        div.empty();
        $.ajax({
            type: "GET",
            url: '/changehistory/'+this.staffing.day.id+'/'+this.staffing.ward.get('id'), 
            contentType: "application/json; charset=utf-8",
            success: write_data,
        });
        function write_data(data) {
            _.each(data, function(cl) {
                let person = models.persons.get(cl.person);
                if (!person) return;  // only show current persons
                // Don't show changes older than 3 months
                if (new Date() - new Date(cl.change_time) > 90*24*60*60*1000)
                    return;
                let day = date2str(cl.day);
                let time;
                if (!cl.continued || (cl.until && (cl.until==cl.day))) 
                    time = 'am ' + day;
                else if (cl.until)
                    time = 'von ' + day + ' bis ' + date2str(cl.until);
                else
                    time = 'ab ' + day;
                let text = cl.user + ': ' + person.get('name') +
                    ' ist ' + time + (cl.added ? '' : ' nicht mehr') + ' für ' +
                    models.wards.get(cl.ward).get('name') + ' eingeteilt. (' +
                    datetime2str(cl.change_time) + ')';
                $("<div>").text(text).appendTo(div);
            });
        }
        function date2str(date) {
            return date.slice(8, 10) + '.' +
                date.slice(5, 7) + '.' +
                date.slice(0, 4);
        }
        function datetime2str(date) {
            return date.slice(8, 10) + '.' +
                date.slice(5, 7) + '.' +
                date.slice(0, 4) + ', ' +
                date.slice(11, 13) + ':' +
                date.slice(14, 16) + ' Uhr';
        }
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


// ----------------------------------------------------------------
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
        let staffing = this.day.get_staffing(this.ward);
        this.$(".ward_name").text(this.ward.get('name'));

        if (this.day_views) {
            this.trigger('new_ward_and_date', {
                parent_view: this,
                staffing: staffing,
            });
        } else {
            this.day_views = new QuickDateViews({
                parent_view: this
            });
            this.$("#quickdays").empty().append(this.day_views.render().el);
            let persons_div = this.$("#quickpersons").empty();
            this.person_views = models.persons.map(
                function(person) {
                    var pv = new QuickPersonView({
                        model: person,
                        staffing: staffing,
                    });
                    persons_div.append(pv.render().$el);
                    this.listenTo(pv, 'plan_person', this.plan_person);
                    pv.listenTo(this, 'new_ward_and_date', pv.new_staffing);
                    pv.listenTo(this, 'new_date', pv.new_staffing);
                    return pv;
                },
                this);
        }

        return this;
    },
    show: function(ward, date) {
        // `ward` is the ward
        // `date` is the day edited
        this.ward = ward;
        this.day = models.days.get_day(date);
        this.render().$el.modal('show');
    },
    next_day: function() { this.change_day(true); },
    prev_day: function() { this.change_day(false); },
    change_day: function(forward) {
        this.day = models.days.get_day(this.day.get('date'), forward ? 1 : -1);
        this.trigger("new_date", {
            date: this.day.get('date'),
            staffing: this.day.get_staffing(this.ward),
            forward: forward,
        });
        this.day_views.change_day(forward);
    },
    plan_person: function(person, staffing) {
        if (!staffing.contains(person)) {
            let changes = [{
                id: person.get('id'), 
                action: 'add' }];
            if (staffing.length>0)
                changes.push({ 
                    id: staffing.at(0).get('id'), 
                    action: 'remove' });
            models.save_change(staffing.day,
                               staffing.ward,
                               false,
                               changes);
        }
        this.next_day();
    },
});
var quickinputview = new QuickInputView({
    el: $("#quickinput"),
});
var QuickPersonView = Backbone.View.extend({
    tagName: 'button',
    className: 'quickperson btn btn-default btn-block',
    events: {
        'click': 'plan_person',
    },
    initialize: function(options) {
        this.staffing = options.staffing;
    },
    new_staffing: function(data) {
        this.staffing = data.staffing;
        this.check_available();
        return this;
    },
    check_available: function() {
        this.$el.toggleClass("hidden", !this.staffing.can_be_planned(this.model));
    },
    render: function() {
        this.$el.empty().text(this.model.get("name"))
            .val(this.model.get("id"));
        this.check_available();
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
    set_current: function(is_current) {
        this.is_current = is_current;
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
        this.$el.toggleClass('active', this.is_current);
        return this;
    },
});
var QuickDateViews = Backbone.View.extend({
    el: "#quickdays",
    events: {
    },
    NR_DAYS_BEFORE: 2,
    NR_DAYS_AFTER: 2,
    initialize: function(options) {
        this.parent_view = options.parent_view;
        this.listenTo(this.parent_view, 'new_date', this.new_date);
        this.listenTo(this.parent_view, 'new_ward_and_date', this.new_ward_and_date);
        this.init_data();
    },
    init_data: function() {
        this.date = this.parent_view.day.get('date');
        this.ward = this.parent_view.ward;
        this.views = {};
    },
    get_view: function(offset) {
        // offset is from this.date
        var day = models.days.get_day(this.date, offset);
        if (this.views[day.id])
            return this.views[day.id];
        this.views[day.id] = new QuickDateView({
            collection: day.get_staffing(this.ward)
        });
        return this.views[day.id];
    },
    render: function() {
        this.$el.empty();
        var dv, i;
        for (i = -this.NR_DAYS_BEFORE; 
             i <= this.NR_DAYS_AFTER; i++) {
            dv = this.get_view(i);
            dv.set_current(i === 0);
            this.$el.append(dv.render().el);
        }
        return this;
    },
    new_ward_and_date: function(data) {
        this.init_data();
        this.render();
    },
    new_date: function(data) {
        this.date = data.date;
        this.render();
    },
});

// ---------------------------------------------------------------------
var DifferentDayView = Backbone.View.extend({
    // Do the planning of one Ward on one Day different to the normal schedule
    events: {
        "click #differentdaybutton": "save",
    },
    save: function(continued) {
        let that = this;
        $.ajax({
            type: "POST",
            url: ['/different_day', this.action,
                  this.staffing.ward.get('id'),
                  this.staffing.day.id].join('/'),
            dataType: "json",
            contentType: "application/json; charset=utf-8",
            statusCode: { 403: models.redirect_to_login },
            success: function(data) {
                if (data.status=='ok')
                    window.location.reload();
                else 
                    that.$el(".errors").text(data.message);
            },
        });
    },
    render: function() {
        let day = this.staffing.day;
        this.current_date = day.get('date');
        let datestr = utils.day_long_names[this.current_date.getDay()] +
            ', ' + utils.datestr(this.current_date);
        let ward = this.staffing.ward;
        let action_string = "zusätzlich planen";
        let dd = ward.different_days[day.id];
        if (dd) {
            if (dd=='+') {
                this.action = "remove_additional";
                action_string = "nicht planen";
            }
            else
                this.action = "remove_cancelation";
        } else {
            if (this.staffing.no_staffing)
                this.action = "add_additional";
            else {
                this.action = "add_cancelation";
                action_string = "nicht planen";
            }
        }
        this.$(".changedate").text(datestr);
        this.$(".changeward").text(ward.get('name'));
        this.$(".differentaction").text(action_string);
        return this;
    },
    show: function(staffing) {
        this.staffing = staffing;
        this.render().$el.modal('show');
    },
});
var differentdayview = new DifferentDayView({
    el: $("#differentday"),
});

return {
    staff: changestaffview,
    approve: approvestaffingview,
    quickinput: quickinputview,
    differentday: differentdayview,
    test: {
        QuickInputView: QuickInputView,
    },
};
})($, _, Backbone);
