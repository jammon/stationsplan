(function($, _, Backbone) {
"use strict";

sp.StaffingView = Backbone.View.extend({
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
        sp.changestaffview.show(this.collection);
    },
});
sp.Ward.prototype.row_view = sp.StaffingView;

function datestr(date) {
    return date.getDate()+'.'+(date.getMonth()+1)+'.'+date.getFullYear();
}
var ONE_DAY = 24*60*60*1000; // in msec
sp.ChangeStaffView = Backbone.View.extend({
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
            url: '/change_more', 
            data: JSON.stringify(data),
            error: function(jqXHR, textStatus, errorThrown) {
                sp.store_error(textStatus, 'error');
            },
            success: function(data, textStatus, jqXHR) {
                _.each(data, sp.apply_change);
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
    add_person_html: function(person, action, changestafftable, day) {
        changestafftable.append(this.template({
            shortname: person.id,
            name: person.get('name'),
            type: (action=='add' ? 'info' : 'primary'),
            action: action,
            duties: day.persons_duties[person.id].pluck('shortname').join(', '),
        }));
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
                var view = new sp.ChangePersonView({
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
        this.render();
        this.$el.modal('show');
    },
});
sp.changestaffview = new sp.ChangeStaffView({
    el: $("#changestaff"),
});

sp.ChangePersonView = Backbone.View.extend({
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

sp.DutiesView = Backbone.View.extend({
    tagName: 'td',
    initialize: function() {
        this.listenTo(this.collection, "update", this.render);
    },
    render: function() {
        this.$el.html(this.collection.pluck('shortname').join(', '));
        return this;
    },
});
sp.Person.prototype.row_view = sp.DutiesView;

})($, _, Backbone);
