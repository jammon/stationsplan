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

var month_names = ["Januar", "Februar", "März", "April", "Mai", "Juni", 
    "Juli", "August", "September", "Oktober", "November", "Dezember"];
var day_names = ['So.', 'Mo.', 'Di.', 'Mi.', 'Do.', 'Fr.', 'Sa.'];

var MonthView = Backbone.View.extend({
    events: {
        "click .prev-month": "prev_month",
        "click .next-month": "next_month",
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
    build_table: function(table) {
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
        models.persons.each(function(person) {
            table.append(construct_row(person));
        });
    },
    render: function() {
        this.$el.html(this.template({
            month_name: month_names[this.month],
            year: this.year,
        }));
        this.build_table(this.$(".plan"));

        // display only the currently loaded days
        if (models.days.first().get_month_id()===this.month_id) {
            this.$(".prev-month").hide();
        }
        $(".plans").append(this.$el);
        return this;
    },
    prev_month: function() {
        router.navigate(this.slug+'/'+utils.get_previous_month_id(this.month_id),
            {trigger: true});
    },
    next_month: function() {
        router.navigate(this.slug+'/'+utils.get_next_month_id(this.month_id),
            {trigger: true});
    },
});

var OnCallView = MonthView.extend({
    base_class: 'on_call_plan',
    slug: 'dienste',
    template: _.template($('#on-call-table').html()),
    build_table: function(table) {
        var tasks = models.wards.filter(function(ward) {
            return !ward.get('continued');
        });
        var titlerow = $('<tr/>', {'class': 'titlerow'}).append($('<th/>'));
        _.each(tasks, function(task) {
            titlerow.append($('<th/>', {text: task.get('name')}));
        });
        table.append(titlerow);

        var that = this;
        // Construct rows for every day
        var day_label = _.template(
            "<%= name %> <%= date %>.<%= month %>.");
        function get_day_label(date) {
            return day_label({
                name: day_names[date.getDay()],
                date: date.getDate(),
                month: date.getMonth()+1
            });
        }
        _.each(that.month_days, function(day) {
            var date = day.get('date');
            var row = $('<tr/>');
            if (day.get('is_free')) row.addClass('free-day');
            row.append($('<th/>', { text: get_day_label(date) }));

            _.each(tasks, function(task) {
                var collection = day.ward_staffings[task.id];
                var view = collection ?
                    (new StaffingView({ 
                        collection: collection,
                        display_long_name: true,
                    })).render().$el :
                    '<td></td>';
                row.append(view);
            });
            table.append(row);
        });
    },
});

var current_month_id = "";

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
var month_views = new MonthViews(MonthView);
var on_call_views = new MonthViews(OnCallView);

var Router = Backbone.Router.extend({
    routes: {
        "plan(/:month_id)": "plan",    // #plan
        "dienste(/:month_id)": "dienste",    // #dienste
    },
    plan: function(month_id) {
        this.call_view(month_views, month_id);
    },
    dienste: function(month_id) {
        this.call_view(on_call_views, month_id);
    },
    call_view: function(klass, month_id) {
        var options, view;
        if (month_id) {
            options = { month_id: month_id };
        } else {
            var today = new Date();
            options = {
                year: today.getFullYear(), 
                month: today.getMonth(),
            };
        }
        view = klass.get_view(options);
        // find current view and hide it
        $('.monthview.current').removeClass('current');
        // show new view
        view.$el.addClass('current');
    },
});
var router = new Router();

var NavView = Backbone.View.extend({
    events: {
        "click #nav-stationen": "stationen",
        "click #nav-dienste": "dienste",
    },
    stationen: function(event) {
        router.navigate("plan/" + current_month_id, {trigger: true});
    },
    dienste: function(event) {
        router.navigate("dienste/" + current_month_id, {trigger: true});
    },
});

var nav_view = new NavView({el: $(".nav")});

var ErrorView = Backbone.View.extend({
    initialize: function() {
        this.listenTo(models.errors, "add", this.addError);
    },
    addError: function(error) {
        var tr = $("<tr/>");
        tr.append("<td/>", { text: error.get('textStatus') });
        tr.append("<td/>", { text: error.get('errorThrown').toString() });
        this.$el.append(tr);
    },
});
var error_view = new ErrorView({ el: $("#errors")});

return {
    // StaffingView: StaffingView,
    // DutiesView: DutiesView,
    // MonthView: MonthView,
    // router: router,
};
})($, _, Backbone);
