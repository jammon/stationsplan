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
            this.display_long_name = options.display_long_name
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
        "click button.changestaff": "person_selected",
    },
    initialize: function(options) {
        this.day = options.day;
        this.ward = options.ward;
    },
    person_selected: function(event) {
        sp.change_and_store(
            event.target.dataset.shortname,
            this.staffing,
            event.target.dataset.action);
        this.$el.modal('hide');
    },
    change_person_template: _.template($('#change_person_template').html()),
    add_person_html: function(person, action, changestafftable, day) {
        changestafftable.append(this.change_person_template({
            shortname: person.id,
            name: person.get('name'),
            type: (action=='add' ? 'info' : 'primary'),
            action: action,
            duties: day.persons_duties[person.id].pluck('shortname').join(', '),
        }));
    },
    render: function() {
        var ward = this.staffing.ward;
        var day = this.staffing.day;
        var available = day.get_available(ward);
        var changestafftable = this.$("#changestafftable").empty();
        var that = this;
        this.$(".changedate").text(datestr(day.get('date')));
        this.$(".changeward").text(ward.get('name'));
        this.staffing.each(function(person) {
            that.add_person_html(person, 'remove', changestafftable, day);
        });
        _.each(available, function(person) {
            that.add_person_html(person, 'add', changestafftable, day);
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
