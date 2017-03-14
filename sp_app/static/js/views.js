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
        var staffing = this.collection;
        el.empty();
        if (!this.collection.no_staffing) {
            this.collection.displayed.each(function(person) {
                var name = $('<div/>', {
                    text: that.display_long_name ? person.get('name') : person.id,
                    'class': 'staff',
                });
                if (models.user_can_change && that.display_long_name) {
                    name.draggable({
                        helper: function() {
                            return $('<div/>', {
                                text: person.get('name'),
                                ward: staffing.ward.id,
                                day: staffing.day.id,
                                person: person.id,
                            });
                        }
                    });
                }
                el.append(name);
            });
            el.toggleClass('lacking', this.collection.lacking());
            el.toggleClass('today', this.collection.day.id==models.today_id);
        }
        if (models.user_can_change) {
            el.droppable({
                accept: function(draggable) {
                    var person = models.persons.where({ name: draggable.text() });
                    if (staffing.can_be_planned(person.length && person[0])) {
                        return true;
                    } else {
                        return false;
                    }
                },
                drop: function(event, ui) {
                    var persons = models.persons.where({ name: ui.draggable.text() });
                    if (persons.length) {
                        models.save_change({
                            day: staffing.day.id,
                            ward: staffing.ward,
                            continued: false,
                            persons: [{
                                id: persons[0].id,
                                action: 'add',
                            }],
                        });
                    }
                    remove_person_from_helper(ui.helper);
                },
                activeClass: "ui-state-highlight",
                tolerance: "pointer",
                cursor: "pointer",
            });
        }
        return this;
    },
    addstaff: function() {
        if (models.user_can_change || !this.collection.no_staffing)
            changeviews.staff.show(this.collection);
    },
});
models.Ward.prototype.row_view = StaffingView;

var DutiesView = Backbone.View.extend({
    tagName: 'td',
    initialize: function() {
        this.listenTo(this.collection.displayed, "update", this.render);
        this.listenTo(this.collection.displayed, "reset", this.render);
    },
    render: function() {
        this.$el.html(this.collection.displayed.pluck('shortname').join(', '));
        return this;
    },
});
models.Person.prototype.row_view = DutiesView;

function remove_person_from_helper(helper) {
    if (helper.attr('day'))
        models.save_change({
            day: helper.attr('day'),
            ward: helper.attr('ward'),
            continued: false,
            persons: [{
                id: helper.attr('person'),
                action: 'remove',
            }],
        });
}

var month_names = ["Januar", "Februar", "März", "April", "Mai", "Juni", 
    "Juli", "August", "September", "Oktober", "November", "Dezember"];
var day_names = ['So.', 'Mo.', 'Di.', 'Mi.', 'Do.', 'Fr.', 'Sa.'];
var day_long_names = ['Sonntag', 'Montag', 'Dienstag', 'Mittwoch',
    'Donnerstag', 'Freitag', 'Samstag'];

var _table_template = _.template($('#table-template').html());
function get_table_from_template(options) {
    return _table_template(options);
}
var MonthView = Backbone.View.extend({
    events: {
        "click .prev-view": "prev_period",
        "click .next-view": "next_period",
    },
    base_class: 'month_plan',
    slug: 'plan',
    className: function() {
        return ['monthview', this.base_class, this.month_id].join(' ');
    },
    template: _.template($('#big-table').html()),
    initialize: function(options) {
        // options can be { year: 2016, month: 5 } or { month_id: '201606' }
        // options.month is 0..11 like in javascript
        _.extend(this, _.pick(options, 'year', 'month', 'month_id'));
        if (this.month_id === void 0) {
            this.month_id = utils.get_month_id(this.year, this.month);
        } else if (this.year === void 0) {
            _.extend(this, utils.get_year_month(this.month_id));
        }
        this.month_days = models.get_month_days(this.year, this.month);
    },
    build_table: function() {
        var table = this.$(".plan");
        var titlerow = $('<tr/>', {'class': 'titlerow'}).append($('<th/>'));
        this.month_days.each(function(day) {
            var date = day.get('date');
            var th = $('<th/>', {'html': 
                day_names[date.getDay()] + '<br>' + date.getDate() + '.'});
            th.toggleClass('today', day.id==models.today_id);
            titlerow.append(th);
        });
        table.append(titlerow);

        var that = this;
        // Construct rows for wards and persons
        function construct_row(model) {
            var row = $('<tr/>', {'class': model.row_class()});
            row.append($('<th/>', { text: model.get('name')}));
            that.month_days.each(function(day) {
                var collection = day[model.collection_array][model.id];
                var view;
                if (collection) {
                    view = new model.row_view({ 
                        collection: collection,
                        className: day.get('is_free') ? 'free-day' : '',
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
        _.each(this.month_days.current_persons(), function(person) {
            table.append(construct_row(person));
        });
    },
    get_template_options: function() {
        return {
            period: month_names[this.month] + ' ' + this.year,
            label_prev: "Voriger Monat",
            label_next: "Nächster Monat",
            content: this.template(),
        };
    },
    is_first_loaded_view: function() {
        return models.days.first().get_month_id()===this.month_id;
    },
    render: function() {
        this.$el.html(get_table_from_template(this.get_template_options()));
        this.build_table(this.$(".plan"));

        // display only the currently loaded days
        if (this.is_first_loaded_view()) {
            this.$(".prev-view").hide();
        }
        $(".plans").append(this.$el);
        return this;
    },
    prev_period: function() {
        router.navigate(this.slug+'/'+utils.get_previous_month_id(this.month_id),
            {trigger: true});
    },
    next_period: function() {
        router.navigate(this.slug+'/'+utils.get_next_month_id(this.month_id),
            {trigger: true});
    },
});

var OnCallView = MonthView.extend({
    base_class: 'on_call_plan',
    slug: 'dienste',
    template: _.template($('#on-call-table').html()),
    build_table: function() {
        var table = this.$(".plan");
        var titlerow = $('<tr/>', {'class': 'titlerow'}).append($('<th/>'));
        models.on_call.each(function(task) {
            titlerow.append($('<th/>', {text: task.get('name')}));
        });
        table.append(titlerow);

        // Construct rows for every day
        var day_label = _.template(
            "<%= name %> <%= date %>.<%= month %>.");
        function get_day_label(date) {
            return day_label({
                name: day_names[date.getDay()],
                date: date.getDate(),
                month: date.getMonth()+1,
            });
        }
        this.month_days.each(function(day) {
            var date = day.get('date');
            var row = $('<tr/>');
            row.toggleClass('today', day.id==models.today_id);
            if (day.get('is_free')) row.addClass('free-day');
            row.append($('<th/>', { text: get_day_label(date) }));

            models.on_call.each(function(task) {
                var collection = day.ward_staffings[task.id];
                var view = (collection && !collection.no_staffing) ?
                    (new StaffingView({ 
                        collection: collection,
                        display_long_name: true,
                    })).render().$el :
                    '<td></td>';
                row.append(view);
            });
            table.append(row);
        });

        // build CallTallies
        if (models.user_can_change) {
            table = this.$(".calltallies");
            titlerow = $('<tr/>', {'class': 'titlerow'}).append($('<th/>'));
            _.each(models.on_call_types, function(on_call_type) {
                titlerow.append($('<th/>', {text: on_call_type}));
            });
            table.append(titlerow);
            this.month_days.calltallies.each(function(calltally) {
                var view = new CallTallyView({ model: calltally });
                table.append(view.render().$el);
            });
        }
    },
});

var DayView = MonthView.extend({
    base_class: 'day_plan',
    slug: 'tag',
    template: _.template($('#day-table').html()),
    row_template: _.template($('#day-row').html()),
    initialize: function(options) {
        // options can be { year: 2016, month: 5, day: 10 } or { day_id: '20160610' }
        // options.month is 0..11 like in javascript
        _.extend(this, _.pick(options, 'year', 'month', 'day', 'day_id'));
        if (this.day_id === void 0) {
            this.day_id = utils.get_day_id(this.year, this.month, this.day);
        } else if (this.year === void 0) {
            _.extend(this, utils.get_year_month_day(this.day_id));
        }
        this.day_obj = models.days.get_day(this.year, this.month, this.day);
    },
    get_template_options: function() {
        var date = this.day_obj.get('date');
        return {
            period: day_long_names[date.getDay()] + ', ' + this.day + '. ' + 
                month_names[this.month] + ' ' + this.year,
            label_prev: "Voriger Tag",
            label_next: "Nächster Tag",
            content: this.template(),
        };
    },
    build_table: function() {
        var table = this.$(".plan");
        var day = this.day_obj;
        var row_template = this.row_template;
        models.wards.each(function(ward) {
            var displayed = day.ward_staffings[ward.id].displayed;
            var tr = row_template({
                ward: ward.get("name"),
                persons: displayed.pluck("name").join(', '),
            });
            table.append(tr);
        });

    },
    prev_period: function() {
        router.navigate(this.slug+'/'+utils.get_previous_day_id(this.day_id),
            {trigger: true});
    },
    next_period: function() {
        router.navigate(this.slug+'/'+utils.get_next_day_id(this.day_id),
            {trigger: true});
    },
});

var current_day_id;
var current_month_id;
function update_current_day() {
    current_day_id = utils.get_day_id(new Date());
    current_month_id = current_day_id.slice(0, 6);
}

function MonthViews(klass) {
    this.klass = klass;
    this.get_view = function(options) {
        var month_id = options.year ?
            utils.get_month_id(options.year, options.month) :
            (options.month_id || current_month_id);
        if (!_.has(this, month_id)) {
            this[month_id] = (new klass(options)).render();
        }
        current_month_id = month_id;
        return this[month_id];
    };
}
function DayViews() {
    this.get_view = function(options) {
        var day_id = options.day ?
            utils.get_day_id(options.day) :
            (options.day_id || current_day_id);
        if (!_.has(this, day_id)) {
            this[day_id] = (new DayView({day_id: day_id})).render();
        }
        current_day_id = day_id;
        return this[day_id];
    };
}
var month_views = new MonthViews(MonthView);
var on_call_views = new MonthViews(OnCallView);
var day_views = new DayViews();

var CallTallyView = Backbone.View.extend({
    tagName: 'tr',
    initialize: function() {
        this.listenTo(this.model, "change", this.render);
    },
    render: function() {
        var el = this.$el;
        var model = this.model;
        var name = $("<th\>", { text: model.get("name") });
        name.draggable({
            helper: 'clone',
        });
        el.empty().append(name);
        _.each(models.on_call_types, function(on_call_type) {
            el.append($("<td\>", { text: model.get_tally(on_call_type) }));
        });
        return this;
    },

});

var Router = Backbone.Router.extend({
    routes: {
        "plan(/:month_id)": "plan",    // #plan
        "dienste(/:month_id)": "dienste",    // #dienste
        "tag(/:day_id)": "tag",    // #Augaben an einem Tag
    },
    plan: function(month_id) {
        this.call_view(month_views, month_id);
    },
    dienste: function(month_id) {
        this.call_view(on_call_views, month_id);
    },
    tag: function(day_id) {
        var view = day_views.get_view({day_id: day_id});
        // find current view and hide it
        $('.monthview.current').removeClass('current');
        // show new view
        view.$el.addClass('current');
    },
    call_view: function(klass, month_id, period) {
        var view;
        view = klass.get_view(this.get_options(month_id, period));
        // find current view and hide it
        $('.monthview.current').removeClass('current');
        // show new view
        view.$el.addClass('current');
    },
    get_options: function(id, period) {
        // id can be '' or undefined
        // period should be 'month' (default) or 'day'
        var result = {};
        if (id) {
            result[(period || 'month') + '_id'] = id;
            return result;
        }
        var today = new Date();
        if (period=='day')
            return { day: today };
        return {
            year: today.getFullYear(), 
            month: today.getMonth(),
        };
    },
});
var router = new Router();

var NavView = Backbone.View.extend({
    events: {
        "click #nav-stationen": "stationen",
        "click #nav-dienste": "dienste",
        "click #nav-tag": "tag",
    },
    stationen: function(event) {
        update_current_day();
        router.navigate("plan/" + current_month_id, {trigger: true});
    },
    dienste: function(event) {
        update_current_day();
        router.navigate("dienste/" + current_month_id, {trigger: true});
    },
    tag: function(event) {
        update_current_day();
        router.navigate("tag/" + current_day_id, {trigger: true});
    },
});

var nav_view = new NavView({el: $(".nav")});

var ErrorView = Backbone.View.extend({
    initialize: function() {
        this.listenTo(models.errors, "add", this.addError);
    },
    addError: function(error) {
        var tr = $("<tr/>");
        tr.append($("<td/>", { text: error.get('textStatus') }));
        tr.append($("<td/>", { text: error.get('errorThrown').toString() }));
        this.$el.append(tr);
    },
});
var error_view = new ErrorView({ el: $("#errors")});

return {
    // StaffingView: StaffingView,
    // DutiesView: DutiesView,
    // MonthView: MonthView,
    // router: router,
    remove_person_from_helper: remove_person_from_helper,
};
})($, _, Backbone);
