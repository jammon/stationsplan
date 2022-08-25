// jshint esversion: 6
let views = (function ($, _, Backbone) {
    "use strict";

    // StaffingDisplayView is used in DayView
    let StaffingDisplayView = Backbone.View.extend({
        tagName: 'td',
        initialize: function (options) {
            this.listenTo(this.collection.displayed, "update", this.render);
            this.listenTo(this.collection.ward, "change:approved", this.render);
            if (options) {
                this.display_long_name = options.display_long_name;
                this.changeable = options.changeable;
            }
            if (this.collection.ward.get('callshift') && !this.collection.no_staffing)
                this.$el.addClass('on-call');
            this.listenTo(this.collection.day, "change:day_id", this.update_today);
        },
        render_staffing: function (el, staffing) {
            el.text(staffing.displayed.pluck('name').join(", "));
        },
        extra_rendering: function (el, staffing) { },
        render: function () {
            let el = this.$el;
            const staffing = this.collection;
            const approved = staffing.ward.is_approved(staffing.day.get('date'));
            el.empty();
            // do we have to render it
            if (staffing.no_staffing) return this;
            if (!models.user.is_editor && !approved) return this; // not approved
            // ok, we have to
            this.render_staffing(el, staffing);
            el.toggleClass('lacking', staffing.lacking());
            this.update_today();
            el.toggleClass('unapproved', !approved);
            this.extra_rendering(el, staffing);
            return this;
        },
        update_today: function () {
            this.$el.toggleClass('today', this.collection.day.get('is_today'));
        },
    });
    // PersonView is used in StaffingView
    let marked_person;
    let PersonView = Backbone.View.extend({

        events: {
            "click": "mark",
        },
        initialize: function (options) {
            this.person_id = options.person.get("id");
            this.text = options.person.get(
                options.display_long_name ? "name" : "shortname");
            this.title = options.title;
        },
        mark: function (e) {
            // for editor/dep_lead a simple click means "edit"
            if (!e.shiftKey &&
                (models.user.is_editor || models.user.is_dep_lead)) {
                return;
            }
            // Prevent unwanted selection of text
            if (e.shiftKey) {
                document.getSelection().setBaseAndExtent(
                    this.el, 0, this.el, 0);
            }
            let is_marked = this.$el.hasClass("marked");
            $(".staff.marked").removeClass("marked");
            if (!is_marked)
                $(".staff.person-" + this.person_id).addClass("marked");
            marked_person = this.person_id;
        },
        render: function () {
            this.$el.text(this.text);
            if (marked_person == this.person_id) {
                this.$el.addClass("marked");
            }
            return this;
        },
    });
    // StaffingView is used in PeriodView and OnCallView
    let StaffingView = StaffingDisplayView.extend({
        events: {
            "click": "addstaff",
            "contextmenu": "differentday",
        },
        render_staffing: function (el, staffing) {
            staffing.displayed.each(function (person) {
                let view = new PersonView({
                    person: person,
                    display_long_name: this.display_long_name,
                    title: staffing.day.persons_duties[person.id].displayed.pluck('name').join(', '),
                    className: "staff person-" + person.get("id"),
                }
                );
                el.append(view.render().el);
            }, this);
        },
        extra_rendering: function (el, staffing) {

        },
        addstaff: function (e) {
            // Shift-click means "mark person"
            if (e.shiftKey) return;
            if (models.user.is_editor && !this.collection.no_staffing)
                changeviews.staff.show(this.collection);
        },
        differentday: function (e) {
            if (models.user.is_editor && this.collection.ward.get("on_different_days")) {
                e.preventDefault();
                changeviews.differentday.show(this.collection);
            }
        },
    });
    let NotPlannedView = Backbone.View.extend({
        tagName: 'td',
        initialize: function (options) {
            this.day = options.day;
            this.listenTo(this.day, 'person-changed', this.render);
        },
        render: function () {
            this.$el.text(
                _.map(this.day.not_planned, function (person) {
                    return person.get('shortname');
                }).join(", "));
            return this;
        },
    });
    let DutiesView = Backbone.View.extend({
        tagName: 'td',
        initialize: function () {
            this.listenTo(this.collection.displayed, "update", this.render);
            this.listenTo(this.collection.displayed, "reset", this.render);
        },
        render: function () {
            this.$el.html(this.collection.displayed.pluck('shortname').join(', '));
            return this;
        },
    });

    const _table_template = _.template($('#table-template').html());
    function get_table_from_template(options) {
        return _table_template(options);
    }
    const _period_template = _.template($('#period-template').html());
    function get_period_from_template(options) {
        const start_year = options.start.getFullYear();
        const end_year = options.end.getFullYear();
        return _period_template({
            start: [options.start.getDate(), options.start.getMonth() + 1,
            start_year == end_year ? '' : start_year]
                .join('.'),
            end: [options.end.getDate(), options.end.getMonth() + 1, end_year]
                .join('.'),
        });
    }

    const title_template = _.template("<%= day_name %>.<br> <%= day %>.");
    const date_template = _.template("<%= day %>. <%= month %> <%= year %>");
    const holiday_template = _.template("<%= day %>. <%= month %> <%= year %>"
        + "<% if (holiday) print(' - '); %><%= holiday %>");
    let DayTitleView = Backbone.View.extend({
        tagName: "th",
        render: function () {
            const date = this.model.get('date');
            let el = this.$el;
            el.html(title_template({
                day_name: utils.day_names[date.getDay()],
                day: date.getDate(),
            }));
            let holiday = this.model.get('holiday') || '';
            el.attr({
                title: (holiday ? holiday_template : date_template)({
                    day: date.getDate(),
                    month: utils.month_names[date.getMonth()],
                    year: date.getFullYear(),
                    holiday: holiday,
                }),
                day_id: utils.get_day_id(date),
            });
            el.addClass('daycol');
            el.toggleClass('today', this.model.get('is_today'));
            return this;
        },
    });
    let PeriodView = Backbone.View.extend({
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
            // this is implemented only in OnCallView
            "click .quickinput": "quickinput",
        },
        base_class: 'period_plan',
        slug: 'plan',
        className: function () {
            return ['contentview', this.base_class, this.start_id].join(' ');
        },
        template: _.template($('#big-table').html()),
        initialize: function (options) {
            // options.start_id is 'YYYYMMDD' (or 'YYYYMM')
            // options.size can be 'xxs', 'xs', 'sm' or 'md'.
            //7, 14, 21, 28 or 'month'
            const lengths = { xxs: 7, xs: 14, sm: 21, md: 28 };
            _.extend(this, _.pick(options, 'start_id', 'size'));
            this.length = lengths[this.size];
            this.start = this.get_start_date(this.start_id);
            this.get_period_days();
        },
        get_start_date: function (start_id) {
            return utils.get_last_monday(utils.get_date(start_id));
        },
        get_period_days: function () {
            this.period_days = models.get_period_days(this.start, this.length);
            this.end = new Date(
                this.start.getFullYear(),
                this.start.getMonth(),
                this.start.getDate() + this.length - 1);
        },
        construct_row: function (model, row_class, collection_array, View) {
            let row = $('<tr/>', { 'class': row_class });
            row.append($('<th/>', { text: model.get('name') }));
            this.period_days.each(function (day) {
                const collection = day[collection_array][model.id];
                let view;
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
        construct_not_planned: function () {
            let row = $('<tr/>', { 'class': 'not_planned' });
            row.append($('<th/>', { text: 'unverplant' }));
            this.period_days.each(function (day) {
                let view = new NotPlannedView({ day: day });
                row.append(view.render().$el);
            });
            return row;
        },
        build_table: function () {
            this.table = this.$(".plan");
            let titlerow = $('<tr/>', { 'class': 'titlerow' }).append($('<th/>'));
            this.period_days.each(function (day) {
                const view = new DayTitleView({ model: day });
                titlerow.append(view.render().$el);
            });
            this.table.append(titlerow);

            // Construct rows for wards and persons
            // first the wards
            models.wards.each(function (ward) {
                let row_class = 'wardrow';
                if (ward.get('callshift'))
                    row_class = 'callshiftrow';
                else if (ward.get('on_leave'))
                    row_class = 'leaverow';
                this.table.append(this.construct_row(
                    ward,
                    row_class + ' approvable',
                    'ward_staffings', StaffingView));
            }, this);
            if (models.user.is_editor)
                this.table.append(this.construct_not_planned());
        },
        build_duties_table: function () {
            _.each(this.period_days.current_persons(), function (person) {
                if (!person.get('anonymous'))
                    this.table.append(this.construct_row(
                        person, 'personrow', 'persons_duties', DutiesView));
            }, this);
            this.$(".show-duties").hide();
        },
        get_template_options: function () {
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
        render: function () {
            this.$el.html(get_table_from_template(this.get_template_options()));
            this.build_table();
            $(".plans").append(this.$el);
            return this;
        },
        make_current: function () {
            this.$el.addClass('current');
            $(".current_dept").text(
                models.user.departments[models.user.current_department]);
            return this;
        },
        prev_period: function () {
            this.change_period(false);
        },
        next_period: function () {
            this.change_period(true);
        },
        change_period: function (forward) {
            update_current_day(this.next_day_id(forward));
            router.navigate(this.slug + '/' + current_day_id, { trigger: true });
        },
        next_day_id: function (forward) {
            const next_start = new Date(
                this.start.getFullYear(),
                this.start.getMonth(),
                this.start.getDate() + (forward ? this.length : - this.length));
            return utils.get_day_id(next_start);
        },
        approve: function (e) {
            if (!models.user.is_editor) return;
            const ward = models.wards.where({ name: e.currentTarget.textContent });
            if (ward.length)
                changeviews.approve.show(ward[0]);
            else
                changeviews.approve.show();
        },
        show_day: function (e) {
            const day_id = $(e.currentTarget).attr('day_id');
            router.navigate('tag/' + day_id, { trigger: true });
        },
    });
    PeriodView.get_period_id = function (options) {
        return utils.get_last_monday_id(options.start_id) + options.size;
    };


    let MonthView = PeriodView.extend({
        get_start_date: function (start_id) {
            return utils.get_date(start_id.length == 6 ? start_id + '01' : start_id);
        },
        get_period_days: function () {
            this.period_days = models.get_month_days(
                this.start.getFullYear(), this.start.getMonth());
        },
        get_template_options: function () {
            return {
                period: utils.month_names[this.start.getMonth()] + ' ' +
                    this.start.getFullYear(),
                label_prev: "Voriger Monat",
                label_next: "Nächster Monat",
                content: this.template(),
            };
        },
        next_day_id: function (forward) {
            const next_month_id = forward ? 'get_next_month_id' : 'get_previous_month_id';
            return utils[next_month_id](this.start_id.slice(0, 6)) + '01';
        },
    });
    MonthView.get_period_id = function (options) {
        return options.start_id.slice(0, 6);
    };

    let OnCallRowView = Backbone.View.extend({
        tagName: "tr",
        render: function () {
            const day = this.model;
            const date = day.get('date');
            const day_label = _.template(
                "<%= name %>. <%= date %>.<%= month %>.");
            let el = this.$el;
            el.empty();

            el.toggleClass('today', day.get('is_today'));
            if (day.get('is_free')) el.addClass('free-day');
            el.append($('<td/>', {
                text: day_label({
                    name: utils.day_names[date.getDay()],
                    date: date.getDate(),
                    month: date.getMonth() + 1,
                })
            }));

            models.on_call.each(function (task) {
                const collection = day.get_staffing(task);
                if (collection && !collection.no_staffing) {
                    el.append((new StaffingView({
                        collection: collection,
                        display_long_name: true,
                    })).render().$el);
                } else {
                    el.append('<td></td>');
                }
            });
            return this;
        }
    });
    let OnCallView = MonthView.extend({
        base_class: 'on_call_plan',
        slug: 'dienste',
        template: _.template($('#on-call-table').html()),
        build_table: function () {
            let table = this.$(".plan");
            let titlerow = $('<tr/>', { 'class': 'titlerow' })
                .append($('<th/>'));
            models.on_call.each(function (task) {
                let th = $(
                    '<th/>', { text: task.get('name') });
                if (task.get('min') < 2)
                    th.addClass('quickinput');
                titlerow.append(th);
            });
            table.append(titlerow);

            // Construct rows for every day
            this.period_days.each(function (day) {
                let row = new OnCallRowView({ model: day });
                table.append(row.render().$el);
            });

            // build CallTallies
            if (models.user.is_editor) {
                table = this.$(".calltallies");
                titlerow = $('<tr/>', { 'class': 'titlerow' }).append($('<th/>'));
                _.each(models.on_call_types, function (on_call_type) {
                    titlerow.append($('<th/>', { text: on_call_type }));
                });
                titlerow.append($('<th/>', { text: 'Last' }));
                table.append(titlerow);
                this.period_days.calltallies.each(function (calltally) {
                    let view = new CallTallyView({ model: calltally });
                    table.append(view.render().$el);
                });
            }
        },
        quickinput: function (event) {
            const ward = models.wards.where({ name: event.currentTarget.textContent })[0];
            changeviews.quickinput.show(ward, this.period_days.first_day);
        },
    });
    let CallTallyView = Backbone.View.extend({
        tagName: 'tr',
        initialize: function () {
            this.listenTo(this.model, "change", this.render);
        },
        render: function () {
            let el = this.$el;
            const tally = this.model;
            el.empty().append($("<th\>", { text: tally.get("name") }));
            _.each(models.on_call_types, function (on_call_type) {
                el.append($("<td\>", { text: tally.get_tally(on_call_type) }));
            });
            el.append($("<td\>", { text: tally.get('weights') }));
            return this;
        },

    });

    let DayView = PeriodView.extend({
        base_class: 'day_plan',
        slug: 'tag',
        template: _.template($('#day-table').html()),
        initialize: function (options) {
            // options can be like { start_id: '20160610' }
            this.start_id = options.start_id;
            _.extend(this, utils.get_year_month_day(this.start_id));
            this.day_obj = models.days.get_day(new Date(this.year, this.month, this.day));
        },
        get_template_options: function () {
            const date = this.day_obj.get('date');
            return {
                period: utils.day_long_names[date.getDay()] + ', ' + this.day + '. ' +
                    utils.month_names[this.month] + ' ' + this.year,
                label_prev: "Voriger Tag",
                label_next: "Nächster Tag",
                content: this.template(),
            };
        },
        build_table: function () {
            let table = this.$(".plan");
            const day = this.day_obj;
            models.wards.each(function (ward) {
                if (!day.get_staffing(ward).no_staffing) {
                    let row = $('<tr/>').append($('<th/>').text(ward.get("name")));
                    let view = new StaffingDisplayView({
                        collection: day.get_staffing(ward),
                        className: day.get('is_free') ? 'free-day' : '',
                    });
                    row.append(view.render().$el);
                    table.append(row);
                }
            });
        },
        next_day_id: function (forward) {
            if (forward) return utils.get_next_day_id(this.start_id);
            else return utils.get_previous_day_id(this.start_id);
        },
    });
    DayView.get_period_id = function (options) {
        return options.start_id;
    };

    // Former Persons and Inactive Wards
    ["#former_persons", "#inactive_wards"].forEach(function (id) {
        $(id).click(function () {
            $(id).hide();
            $(id + '_list').removeClass("hidden");
        });
    });

    let current_day_id;   // the currently displayed day
    function update_current_day(day_id) {
        current_day_id = day_id || utils.get_day_id(new Date());
    }
    update_current_day();

    let current_size;   // the currently displayed size
    function update_current_size() {
        const old_size = current_size;
        current_size = $('.device-check:visible').attr('data-device');
        if (current_size == 'xs' && window.screen.availWidth <= 550)
            current_size = 'xxs';
        if (old_size && old_size != current_size)
            router.size_changed();
    }
    update_current_size();
    $(window).resize(update_current_size);

    function PeriodViews(klass) {
        this.klass = klass;
        this.get_view = function (options) {
            let cur_klass = this.klass;
            if (cur_klass == PeriodView && options.size == 'lg')
                cur_klass = MonthView;
            const period_id = options.period_id = cur_klass.get_period_id(options);
            if (!_.has(this, period_id)) {
                this[period_id] = (new cur_klass(options)).render();
            }
            update_current_day(options.start_id);
            return this[period_id];
        };
    }
    let month_views = new PeriodViews(PeriodView);
    let on_call_views = new PeriodViews(OnCallView);
    let day_views = new PeriodViews(DayView);


    const is_top_level_nav = {
        "#nav-stationen": true,
        "#nav-dienste": true,
        "#nav-tag": true,
    };
    let Router = Backbone.Router.extend({
        routes: {
            "plan(/:period_id)(/)": "plan",    // #plan
            "dienste(/:period_id)(/)": "dienste",    // #dienste
            "tag(/:day_id)(/)": "tag",    // #Aufgaben an einem Tag
        },
        plan: function (period_id) {
            this.call_view(month_views, "#nav-stationen", period_id, 'plan');
        },
        dienste: function (period_id) {
            this.call_view(on_call_views, "#nav-dienste", period_id, 'dienste');
        },
        tag: function (period_id) {
            this.call_view(day_views, "#nav-tag", period_id, 'tag');
        },
        call_view: function (views_coll, nav_id, period_id, slug) {
            if (period_id && period_id < models.days.first().id) {
                document.location = "/" + slug + "/" + period_id;
                return;
            }
            let view = views_coll.get_view({
                start_id: period_id || utils.get_day_id(new Date()),
                size: current_size,
            });
            this.make_current(view, nav_id);
        },
        make_current: function (view, nav_id) {
            // find current view and hide it
            if (this.current_view)
                this.current_view.$el.removeClass('current');
            // show new view
            this.current_view = view.make_current();
            nav_view.$(".active").removeClass("active");
            if (is_top_level_nav[nav_id])
                nav_view.$(nav_id).addClass("active");
        },
        size_changed: function () {
            Backbone.history.loadUrl(Backbone.history.fragment);
        },
    });
    let router = new Router();

    let NavView = Backbone.View.extend({
        events: {
            "click #nav-stationen": "stationen",
            "click #nav-dienste": "dienste",
            "click #nav-tag": "tag",
            "click #nav-funktionen": "funktionen",
            "click #nav-personen": "personen",
            "click #nav-admin": "admin",
        },
        stationen: function (event) {
            this.navigate_to("plan/" + current_day_id, event);
        },
        dienste: function (event) {
            this.navigate_to("dienste/" + current_day_id, event);
        },
        tag: function (event) {
            this.navigate_to("tag/" + utils.get_day_id(new Date()), event);
        },
        personen: function (event) {
            window.location = "/personen";
        },
        admin: function (event) {
            window.location = "/admin/";
        },
        navigate_to: function (path, event) {
            event.preventDefault();
            update_current_day();
            router.navigate(path, { trigger: true });
        },
    });

    let nav_view = new NavView({ el: $(".nav") });

    let ErrorView = Backbone.View.extend({
        template: _.template(
            "<tr>" +
            "<td><%= status %></td>" +
            "<td><%= error %></td>" +
            "<td><%= response %></td>" +
            "<td><%= url %></td>" +
            "<td><%= data %></td>" +
            "</tr>"),
        initialize: function () {
            this.listenTo(models.errors, "add", this.addError);
            this.$el.append();
        },
        addError: function (error) {
            const msg = this.template({
                status: error.get('textStatus'),
                error: error.get('errorThrown'),
                response: error.get('responseText'),
                url: error.get('url'),
                data: error.get('data'),
            });
            this.$el.removeClass("hidden").append(msg);
        },
    });
    let error_view;
    if (models.user.is_editor)
        error_view = new ErrorView({ el: $("#errors") });

    return {
        StaffingView: StaffingView,  // exported for testing
        // DutiesView: DutiesView,
        // PeriodView: PeriodView,
        // router: router,
    };
})($, _, Backbone);
