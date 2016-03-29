var views = (function($, _, Backbone) {
"use strict";

var StaffingView = Backbone.View.extend({
    tagName: 'td',
    events: {
        "click": "addstaff",
    },
    initialize: function(options) {
        this.listenTo(this.collection.displayed, "update", this.render);
        if (options)
            this.display_long_name = options.display_long_name;
        if (!this.collection.ward.get('continued') && !this.collection.no_staffing)
            this.$el.addClass('on-call');
    },
    render: function() {
        var el = this.$el;
        var that = this;
        el.empty();
        if (!this.collection.no_staffing) {
            this.collection.displayed.each(function(person) {
                el.append($('<div/>', {
                    text: that.display_long_name ? person.get('name') : person.id,
                    'class': 'staff',
                }));
            });
            el.toggleClass('lacking', this.collection.lacking());
        }
        return this;
    },
    addstaff: function() {
        if (!can_change || this.collection.no_staffing) return;
        changestaffview.show(this.collection);
    },
});
models.Ward.prototype.row_view = StaffingView;

var DutiesView = Backbone.View.extend({
    tagName: 'td',
    initialize: function() {
        this.listenTo(this.collection, "update", this.render);
    },
    render: function() {
        this.$el.html(this.collection.pluck('shortname').join(', '));
        return this;
    },
});
models.Person.prototype.row_view = DutiesView;

var month_names = ["Januar", "Februar", "März", "April", "Mai", "Juni", 
    "Juli", "August", "September", "Oktober", "November", "Dezember"];
var day_names = ['So.', 'Mo.', 'Di.', 'Mi.', 'Do.', 'Fr.', 'Sa.'];

var MonthView = Backbone.View.extend({
    events: {
        "click .prev-month": "prev_month",
        "click .next-month": "next_month",
    },
    className: 'month_plan',
    template: _.template($('#big-table').html()),
    initialize: function(options) {
        this.year = options.year;
        this.month = options.month;
        this.month_days = models.get_month_days(this.year, this.month);
        this.prev_month_view = options.prev_month_view;
        if (this.prev_month_view) {
            this.prev_month_view.next_month_view = this;
        }
    },
    render: function() {
        this.$el.html(this.template({
            month_name: month_names[this.month],
            year: this.year,
        }));
        var table = this.$(".plan");
        var titlerow = $('<tr/>', {'class': 'titlerow'}).append($('<th/>'));
        _.each(this.month_days, function(day) {
            var date = day.get('date');
            titlerow.append($('<th/>', {'html': 
                day_names[date.getDay()] + '<br>' + date.getDate() + '.'}));
        });
        table.append(titlerow);

        var that = this;
        // Construct rows for wards and persons
        function construct_row(model) {
            var row = $('<tr/>', {'class': model.row_class()});
            row.append($('<th/>', { text: model.get('name')}));
            _.each(that.month_days, function(day) {
                var collection = day[model.collection_array][model.id];
                var view;
                if (collection) {
                    view = new model.row_view({
                        collection: collection,
                    });
                    row.append(view.render().$el);
                } else {
                    row.append('<td></td>');
                }
            });
            return row;
        }
        // first the wards
        models.wards.each(function(ward) {
            table.append(construct_row(ward));
        });
        // then the persons
        models.persons.each(function(person) {
            table.append(construct_row(person));
        });
        if (!this.prev_month_view) this.$('.prev-month').hide();
        this.$('.loading-message').hide();
        $(".plans").append(this.$el);
        return this;
    },
    move_to: function(direction) {
    // direction should be 'past', 'present' or 'future'
        if (this.time)
            this.$el.removeClass(this.time);
        this.time = direction;
        this.$el.addClass(direction);
        return this;
    },
    next_month: function() {
        var month, year;
        if (!this.next_month_view) {
            month = this.month + 1;
            year = this.year;
            if (month == 11) {
                year++;
                month = 0;
            }
            this.next_month_view = new MonthView({
                year: year,
                month: month,
                prev_month_view: this,
            });
            this.next_month_view.render().move_to('future')
            $(".plans").append(this.next_month_view.$el);
        }
        this.move_to('past').next_month_view.move_to('present');
    },
    prev_month: function() {
        if (this.prev_month_view)
            this.move_to('future').prev_month_view.move_to('present');
    },
});

function datestr(date) {
    return date.getDate()+'.'+(date.getMonth()+1)+'.'+date.getFullYear();
}
var ONE_DAY = 24*60*60*1000; // in msec
var ChangeStaffView = Backbone.View.extend({
    events: {
        "click #one-day": "one_day",
        "click #continued": "continued",
    },
    template: _.template($('#change_person_template').html()),
    one_day: function() { this.save(false); },
    continued: function() { this.save(true); },
    save: function(continued) {
        var data = {
            day: this.staffing.day.id,
            ward: this.staffing.ward.get('shortname'),
            continued: continued,
            persons: this.collect_changes(),
        };
        $.ajax({
            type: "POST",
            url: '/changes', 
            data: JSON.stringify(data),
            error: function(jqXHR, textStatus, errorThrown) {
                models.store_error(textStatus, 'error');
            },
            success: function(data, textStatus, jqXHR) {
                _.each(data, models.apply_change);
            },
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
        var changestafftable = this.$("#changestafftable").empty();
        this.$(".changedate").text(datestr(day.get('date')));
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
    StaffingView: StaffingView,
    DutiesView: DutiesView,
    MonthView: MonthView,
    ChangeStaffView: ChangeStaffView,
    ChangePersonView: ChangePersonView,
};
})($, _, Backbone);
