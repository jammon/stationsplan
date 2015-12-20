(function($, _, Backbone) {
"use strict";

sp.StaffingView = Backbone.View.extend({
    tagName: 'td',
    events: {
        "click": "addstaff",
    },
    initialize: function() {
        this.listenTo(this.collection.displayed, "update", this.render);
    },
    render: function() {
        var el = this.$el;
        el.empty();
        if (!this.collection.no_staffing) {
            this.collection.displayed.each(function(person) {
                el.append($('<div/>', {
                    text: person.id,
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
    // get_dayspinner: function(day) {
    //     var date = day.get('date');
    //     var day_spinner = new sp.DaySpinnerView({
    //         previous: 
    //         current: datestr(date),
    //         next
    //     });
    //     this.listenTo(day_spinner, "click .spinner-previous", function() {});
    // },
    render: function() {
        var ward = this.staffing.ward;
        var day = this.staffing.day;
        var available = day.get_available(ward);
        var changestafftable = this.$("#changestafftable").empty();
        // var spinners = this.$("#spinners").empty();
        
        // var ward_spinner = new sp.WardSpinnerView({ward: ward});
        var that = this;
        this.$(".changedate").text(datestr(day.get('date')));
        this.$(".changeward").text(ward.get('name'));
        this.staffing.each(function(person) {
            that.add_person_html(person, 'remove', changestafftable, day);
        });
        _.each(available, function(person) {
            that.add_person_html(person, 'add', changestafftable, day);
        });
        // spinners.append(day_spinner.render().$el);
        // spinners.append(ward_spinner.render().$el);
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

// sp.SpinnerView = Backbone.View.extend({
//     events: {
//         "click .previous": "select_previous",
//         "click .next": "select_next",
//     },
//     template: _.template($('#spinner_template').html()),
//     initialize: function(options) {
//         // options should have:
//         // previous, next, current
//         this.options = options;
//     },
//     render: function() {
//         var html = this.template(this.options);
//         this.$el.html(html);
//         return this;
//     },
// });
// sp.DaySpinnerView = sp.SpinnerView.extend({
//     initialize: function(options) {
//         this.day = options.day;
//         this.date = this.day.get('date');
//     },
//     previous: function() {
//         var yesterday = new Date(this.date.getTime() - ONE_DAY);
//         return datestr(yesterday);
//     },
//     next: function() {
//         var tomorrow = new Date(this.date.getTime() + ONE_DAY);
//         return datestr(tomorrow);
//     },
//     current: function() {
//         return datestr(this.date);
//     },
// });

// sp.WardSpinnerView = sp.SpinnerView.extend({
//     initialize: function(options) {
//         this.ward = options.ward;
//         this.index = sp.wards.indexOf(this.ward);
//     },
//     previous: function() {
//         var previous = sp.wards.at(this.index-1);
//         return previous.get('name');
//     },
//     next: function() {
//         var next = sp.wards.at(this.index+1);
//         return next.get('name');
//     },
//     current: function() {
//         return this.ward.get('name');
//     },
// });

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
