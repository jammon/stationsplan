var views = (function($, _, Backbone) {
"use strict";

// StaffingDisplayView is used in DayView
var StaffingDisplayView = Backbone.View.extend({
    tagName: 'td',
    initialize: function(options) {
        this.listenTo(this.collection.displayed, "update", this.render);
        this.listenTo(this.collection.ward, "change:approved", this.render);
        if (options) {
            this.display_long_name = options.display_long_name;
            this.changeable = options.changeable;
            this.drag_n_droppable = options.drag_n_droppable;
        }
        if (!this.collection.ward.get('continued') && !this.collection.no_staffing)
            this.$el.addClass('on-call');
        this.listenTo(this.collection.day, "change:day_id", this.update_today);
    },
    render: function() {
        var el = this.$el;
        var staffing = this.collection;
        var approved = staffing.ward.is_approved(staffing.day.get('date'));
        el.empty();
        if (staffing.no_staffing) return this;
        if (!models.user_can_change() && !approved) return this; // not approved
        el.text(staffing.displayed.pluck('name').join(", "));
        el.toggleClass('lacking', staffing.lacking());
        this.update_today();
        el.toggleClass('unapproved', !approved);
        return this;
    },
    update_today: function() {
        this.$el.toggleClass('today', this.collection.day.get('is_today'));
    },
});
// StaffingView is used in PeriodView and OnCallView
var StaffingView = StaffingDisplayView.extend({
    events: {
        "click": "addstaff",
    },
    render: function() {
        var el = this.$el;
        var that = this;
        var staffing = this.collection;
        var approved = staffing.ward.is_approved(staffing.day.get('date'));
        el.empty();
        // do we have to render it
        if (staffing.no_staffing) return this;
        if (!models.user_can_change() && !approved) return this; // not approved
        // ok, we have to
        staffing.displayed.each(function(person) {
            var name = $('<div/>', {
                text: that.display_long_name ? person.get('name') : person.id,
                'class': 'staff',
                title: staffing.day.persons_duties[person.id].displayed.pluck('name').join(', '),
            });
            if (models.user_can_change() && that.drag_n_droppable) {
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
        el.toggleClass('lacking', staffing.lacking())
            .toggleClass('unapproved', !approved);
        this.update_today();
        if (models.user_can_change() && that.drag_n_droppable) {
            el.droppable({
                accept: function(draggable) {
                    var person = models.persons.where({ name: draggable.text() });
                    return staffing.can_be_planned(person.length && person[0]);
                },
                drop: function(event, ui) {
                    // Is it dropped back on the same day and ward?
                    if (staffing.day.id == ui.helper.attr('day') &&
                        staffing.ward.id == ui.helper.attr('ward')) return;
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
        if (models.user_can_change() && !this.collection.no_staffing)
            changeviews.staff.show(this.collection);
    },
});

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

function remove_person_from_helper(helper) {
    // If a person has been drag-n-dropped to a StaffingView
    // it has to be removed from its origin 
    // if that is a StaffingView as well
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

var _table_template = _.template($('#table-template').html());
function get_table_from_template(options) {
    return _table_template(options);
}
var _period_template = _.template($('#period-template').html());
function get_period_from_template(options) {
    var start_year = options.start.getFullYear();
    var end_year = options.end.getFullYear();
    if (start_year==end_year)
        start_year = '';
    return _period_template({
        start: [options.start.getDate(), options.start.getMonth()+1, start_year]
             .join('.'),
        end: [options.end.getDate(), options.end.getMonth()+1, end_year]
             .join('.'),
    });
}

var title_template = _.template("<%= day_name %>.<br> <%= day %>.");
var date_template = _.template("<%= day %>. <%= month %> <%= year %>");
var DayTitleView = Backbone.View.extend({
    tagName: "th",
    render: function() {
        var date = this.model.get('date');
        var el = this.$el;
        el.html(title_template({
            day_name: utils.day_names[date.getDay()],
            day: date.getDate(),
        }));
        el.attr({
            title: date_template({
                day: date.getDate(),
                month: utils.month_names[date.getMonth()],
                year: date.getFullYear(),
            }),
            day_id: utils.get_day_id(date),
        });
        this.$el.toggleClass('today', this.model.get('is_today'));
        return this;
    },
});
var PeriodView = Backbone.View.extend({
    // This view displays some period of days, 
    // usually a month, but maybe less according to the available screenspace
    events: {
        "click .prev-view": "prev_period",
        "click .next-view": "next_period",
        // "swiperight": "prev_period",
        // "swipeleft": "next_period",
        "click .approvable th": "approve",
        "click .daycol": "show_day",
        "click .show-duties": "build_duties_table",
    },
    base_class: 'period_plan',
    slug: 'plan',
    className: function() {
        return ['contentview', this.base_class, this.start_id].join(' ');
    },
    template: _.template($('#big-table').html()),
    initialize: function(options) {
        // options.start_id is 'YYYYMMDD' (or 'YYYYMM')
        // options.size can be 'xxs', 'xs', 'sm' or 'md'.
        //7, 14, 21, 28 or 'month'
        var lengths = {xxs: 7, xs: 14, sm: 21, md: 28};
        _.extend(this, _.pick(options, 'start_id', 'size'));
        this.length = lengths[this.size];
        this.start = this.get_start_date(this.start_id);
        this.get_period_days();
    },
    get_start_date: function(start_id) {
        return utils.get_last_monday(utils.get_date(start_id));
    },
    get_period_days: function() {
        this.period_days = models.get_period_days(this.start, this.length);
        this.end = new Date(
            this.start.getFullYear(), 
            this.start.getMonth(),
            this.start.getDate() + this.length - 1);
    },
    construct_row: function(model, row_class, collection_array, View) {
        var row = $('<tr/>', {'class': row_class});
        row.append($('<th/>', { text: model.get('name')}));
        this.period_days.each(function(day) {
            var collection = day[collection_array][model.id];
            var view;
            if (collection) {
                view = new View({
                    collection: collection,
                    className: day.get('is_free') ? 'free-day' : '',
                });
                row.append(view.render().$el);
            } else {
                row.append('<td></td>');
            }
        });
        return row;
    },
    build_table: function() {
        this.table = this.$(".plan");
        var titlerow = $('<tr/>', {'class': 'titlerow'}).append($('<th/>'));
        this.period_days.each(function(day) {
            var view = new DayTitleView({ model: day });
            titlerow.append(view.render().$el);
        });
        this.table.append(titlerow);

        var that = this;
        // Construct rows for wards and persons
        // first the wards
        models.wards.each(function(ward) {
            var row_class = 'wardrow';
            if (ward.get('nightshift')) row_class = 'nightshiftrow';
            else if (!ward.get('continued')) row_class = 'non-continued-row';
            else if (ward.get('on_leave')) row_class = 'leaverow';
            that.table.append(that.construct_row(
                ward, 
                row_class + ' approvable',
                'ward_staffings', StaffingView));
        });
    },
    build_duties_table: function() {
        var that = this;
        _.each(this.period_days.current_persons(), function(person) {
            if (!person.get('anonymous'))
                that.table.append(that.construct_row(
                    person, 'personrow', 'persons_duties', DutiesView));
        });
        this.$(".show-duties").hide();
    },
    get_template_options: function() {
        return {
            period: get_period_from_template({
                start: this.start,
                end: this.end,
            }),
            label_prev: "Zurück",
            label_next: "Weiter",
            content: this.template(),
        };
    },
    is_first_loaded_view: function() {
        return models.days.first().id===this.start_id;
    },
    render: function() {
        this.$el.html(get_table_from_template(this.get_template_options()));
        this.build_table();

        // display only the currently loaded days
        if (this.is_first_loaded_view()) {
            this.$(".prev-view").hide();
        }
        $(".plans").append(this.$el);
        return this;
    },
    prev_period: function() {
        this.change_period(false);
    },
    next_period: function() {
        this.change_period(true);
    },
    change_period: function(forward) {
        update_current_day(this.next_day_id(forward));
        router.navigate(this.slug+'/'+current_day_id, {trigger: true});
    },
    next_day_id: function(forward) {
        var next_start = new Date(
            this.start.getFullYear(),
            this.start.getMonth(),
            this.start.getDate() + (forward ? this.length : - this.length));
        return utils.get_day_id(next_start);
    },
    approve: function(e) {
        if (!models.user_can_change()) return;
        var ward = models.wards.where({name: e.currentTarget.textContent});
        if (ward.length)
            changeviews.approve.show(ward[0]);
        else
            changeviews.approve.show();
    },
    show_day: function(e) {
        var day_id = $(e.currentTarget).attr('day_id');
        router.navigate('tag/' + day_id, {trigger: true});
    },
});
PeriodView.get_period_id = function(options) {
    return utils.get_last_monday_id(options.start_id) + options.size;
};


var MonthView = PeriodView.extend({
    get_start_date: function(start_id) {
        return utils.get_date(start_id.length==6 ? start_id+'01' : start_id);
    },
    get_period_days: function() {
        this.period_days = models.get_month_days(
            this.start.getFullYear(), this.start.getMonth());
    },
    get_template_options: function() {
        return {
            period: utils.month_names[this.start.getMonth()] + ' ' +
                this.start.getFullYear(),
            label_prev: "Voriger Monat",
            label_next: "Nächster Monat",
            content: this.template(),
        };
    },
    next_day_id: function(forward) {
        var next_month_id = forward ? 'get_next_month_id' : 'get_previous_month_id';
        return utils[next_month_id](this.start_id.slice(0, 6)) + '01';
    },
});
MonthView.get_period_id = function(options) {
    return options.start_id.slice(0, 6);
};

var OnCallRowView = Backbone.View.extend({
    tagName: "tr",
    render: function() {
        var day = this.model;
        var date = day.get('date');
        var day_label = _.template(
            "<%= name %>. <%= date %>.<%= month %>.");
        var el = this.$el;
        el.empty();

        el.toggleClass('today', day.get('is_today'));
        if (day.get('is_free')) el.addClass('free-day');
        el.append($('<th/>', { 
            text: day_label({
                name: utils.day_names[date.getDay()],
                date: date.getDate(),
                month: date.getMonth()+1,
            })
        }));

        models.on_call.each(function(task) {
            var collection = day.ward_staffings[task.id];
            var view = (collection && !collection.no_staffing) ?
                (new StaffingView({ 
                    collection: collection,
                    display_long_name: true,
                    drag_n_droppable: true,
                })).render().$el :
                '<td></td>';
            el.append(view);
        });
        return this;
    }
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
        this.period_days.each(function(day) {
            var row = new OnCallRowView({ model: day });
            table.append(row.render().$el);
        });

        // build CallTallies
        if (models.user_can_change()) {
            table = this.$(".calltallies");
            titlerow = $('<tr/>', {'class': 'titlerow'}).append($('<th/>'));
            _.each(models.on_call_types, function(on_call_type) {
                titlerow.append($('<th/>', {text: on_call_type}));
            });
            titlerow.append($('<th/>', {text: 'Last'}));
            table.append(titlerow);
            this.period_days.calltallies.each(function(calltally) {
                var view = new CallTallyView({ model: calltally });
                table.append(view.render().$el);
            });
        }
    },
});
var CallTallyView = Backbone.View.extend({
    tagName: 'tr',
    initialize: function() {
        this.listenTo(this.model, "change", this.render);
    },
    render: function() {
        var el = this.$el;
        var tally = this.model;
        var name = $("<th\>", { text: tally.get("name") });
        name.draggable({
            helper: 'clone',
        });
        el.empty().append(name);
        _.each(models.on_call_types, function(on_call_type) {
            el.append($("<td\>", { text: tally.get_tally(on_call_type) }));
        });
        el.append($("<td\>", { text: tally.get('weights') }));
        return this;
    },

});

var DayView = PeriodView.extend({
    base_class: 'day_plan',
    slug: 'tag',
    template: _.template($('#day-table').html()),
    initialize: function(options) {
        // options can be like { start_id: '20160610' }
        this.start_id = options.start_id;
        _.extend(this, utils.get_year_month_day(this.start_id));
        this.day_obj = models.days.get_day(this.year, this.month, this.day);
    },
    get_template_options: function() {
        var date = this.day_obj.get('date');
        return {
            period: utils.day_long_names[date.getDay()] + ', ' + this.day + '. ' + 
                utils.month_names[this.month] + ' ' + this.year,
            label_prev: "Voriger Tag",
            label_next: "Nächster Tag",
            content: this.template(),
        };
    },
    build_table: function() {
        var table = this.$(".plan");
        var day = this.day_obj;
        models.wards.each(function(ward) {
            if (!day.ward_staffings[ward.id].no_staffing) {
                var row = $('<tr/>').append($('<th/>').text(ward.get("name")));
                var view = new StaffingDisplayView({ 
                    collection: day.ward_staffings[ward.id],
                    className: day.get('is_free') ? 'free-day' : '',
                });
                row.append(view.render().$el);
                table.append(row);
            }
        });
    },
    next_day_id: function(forward) {
        if (forward) return utils.get_next_day_id(this.start_id);
        else return utils.get_previous_day_id(this.start_id);
    },
});
DayView.get_period_id = function(options) {
    return options.start_id;
};

var PersonFunctionView = Backbone.View.extend({
    events: {
        "click": "save_function",
    },
    tagName: 'td',
    initialize: function(options) {
        this.person = options.person;
        this.ward = options.ward;
        this.listenTo(this.person, "change:functions", this.render);
    },
    render: function() { 
        var attr = {type: 'checkbox'};
        if (this.person.can_work_on(this.ward))
            attr.checked = 'checked';
        var input = $('<input>').attr(attr);
        this.$el.empty().append(input);
        this.input = input[0];
        return this; 
    },
    save_function: function(event) {
        if (this.person.can_work_on(this.ward) === this.input.checked)
            return;
        models.save_function(this.person, this.ward, this.input.checked);
        this.$('input').attr('disabled', 'disabled');
    },
});
var FunctionsView = Backbone.View.extend({
    // Edit the functions of every person
    el: "#functions_view",
    render: function() {
        var table = this.$('table');
        var titleline = $('<tr />', {'class': 'titleline'});
        titleline.append($('<td />'));
        models.wards.each(function(ward) {
            titleline.append($('<th />', {
                text: ward.get('shortname'),
            }));
        });
        table.append(titleline);
        models.persons.each(function(person) {
            var p_line = $('<tr />');
            p_line.append($('<th />', {
                text: person.get('name'),
            }));
            models.wards.each(function(ward) {
                var view = new PersonFunctionView({
                    person: person,
                    ward: ward,
                });
                view.render();
                var el = view.$el;
                p_line.append(el);
            });
            table.append(p_line);
        });
        this.$el.addClass('contentview functions_view');
        return this;
    },
});
var functionsview;

var current_day_id;   // the currently displayed day
function update_current_day(day_id) {
    current_day_id = day_id || utils.get_day_id(new Date());
}
update_current_day();

var current_size;   // the currently displayed size
function update_current_size() {
    var old_size = current_size;
    current_size = $('.device-check:visible').attr('data-device');
    if (current_size=='xs' && window.screen.availWidth<=550)
        current_size='xxs';
    if (old_size && old_size!=current_size)
        router.size_changed();
}
update_current_size();
$(window).resize(update_current_size);

function PeriodViews(klass) {
    this.klass = klass;
    this.get_view = function(options) {
        var cur_klass = this.klass;
        if (cur_klass==PeriodView && options.size=='lg')
            cur_klass = MonthView;
        var period_id = options.period_id = cur_klass.get_period_id(options);
        if (!_.has(this, period_id)) {
            this[period_id] = (new cur_klass(options)).render();
        }
        update_current_day(options.start_id);
        return this[period_id];
    };
}
var month_views = new PeriodViews(PeriodView);
var on_call_views = new PeriodViews(OnCallView);
var day_views = new PeriodViews(DayView);


var Router = Backbone.Router.extend({
    routes: {
        "plan(/:period_id)(/)": "plan",    // #plan
        "dienste(/:period_id)(/)": "dienste",    // #dienste
        "tag(/:day_id)(/)": "tag",    // #Aufgaben an einem Tag
        "funktionen(/)": "funktionen"
    },
    plan: function(period_id) {
        this.call_view(month_views, "#nav-stationen", period_id);
    },
    dienste: function(period_id) {
        this.call_view(on_call_views, "#nav-dienste", period_id);
    },
    tag: function(period_id) {
        this.call_view(day_views, "#nav-tag", period_id);
    },
    funktionen: function() {
        if (!functionsview)
            functionsview = (new FunctionsView()).render();
        this.make_current(functionsview, "#nav-funktionen");
    },
    call_view: function(views_coll, nav_id, period_id) {
        var view = views_coll.get_view({
            start_id: period_id || utils.get_day_id(new Date()),
            size: current_size,
        });
        this.make_current(view, nav_id);
    },
    make_current: function(view, nav_id) {
        // find current view and hide it
        if (this.current_view)
            this.current_view.$el.removeClass('current');
        // show new view
        view.$el.addClass('current');
        this.current_view = view;
        nav_view.$(".active").removeClass("active");
        nav_view.$(nav_id).addClass("active");
    },
    size_changed: function() {
        Backbone.history.loadUrl(Backbone.history.fragment);
    },
});
var router = new Router();

var NavView = Backbone.View.extend({
    events: {
        "click #nav-stationen": "stationen",
        "click #nav-dienste": "dienste",
        "click #nav-tag": "tag",
        "click #nav-funktionen": "funktionen",
    },
    stationen: function(event) {
        this.navigate_to("plan/" + current_day_id);
    },
    dienste: function(event) {
        this.navigate_to("dienste/" + current_day_id);
    },
    tag: function(event) {
        this.navigate_to("tag/" + utils.get_day_id(new Date()));
    },
    funktionen: function(event) {
        router.navigate("funktionen/", {trigger: true});
    },
    navigate_to: function(path) {
        update_current_day();
        router.navigate(path, {trigger: true});
    },
});

var nav_view = new NavView({el: $(".nav")});

var ErrorView = Backbone.View.extend({
    template: _.template(
            "<tr>" +
              "<td><%= status %></td>" +
              "<td><%= error %></td>" +
              "<td><%= response %></td>" +
              "<td><%= url %></td>" +
              "<td><%= data %></td>" +
            "</tr>"),
    initialize: function() {
        this.listenTo(models.errors, "add", this.addError);
        this.$el.append();
    },
    addError: function(error) {
        var msg = this.template({
            status: error.get('textStatus'),
            error: error.get('errorThrown'),
            response: error.get('responseText'),
            url: error.get('url'),
            data: error.get('data'),
        });
        this.$el.removeClass("hidden").append(msg);
    },
});
var error_view;
if (models.user_can_change )
    error_view = new ErrorView({ el: $("#errors")});

return {
    StaffingView: StaffingView,
    // DutiesView: DutiesView,
    // PeriodView: PeriodView,
    // router: router,
    remove_person_from_helper: remove_person_from_helper,
};
})($, _, Backbone);
