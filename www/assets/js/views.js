"use strict";

var DayView, RowView, WardView, PersonView, StaffingView, DutiesView, NoStaffingView;

RowView = Backbone.View.extend({
  tagName: 'tr',
  render: function() {
    this.$el.html($('<th/>', {text: this.model.get('name')}));
  }
});
WardView = PersonView = RowView;


StaffingView = Backbone.View.extend({
  tagName: 'td',
  events: {
    "click .addstaff": "addstaff"
  },
  render: function() {
    var el = this.$el;
    this.collection.each(function(person) {
      el.append($('<div/>', {
        text: person.id,
        'class': 'staff',
      }));
    });
    el.append($('<div/>', {
      text: '+',
      'class': 'addstaff',
    }));
    return this;
  },
  addstaff: function() {
    alert('addstaff');
  },
});
NoStaffingView = Backbone.View.extend({
  tagName: 'td',
});

DutiesView = Backbone.View.extend({
  tagName: 'td',
  render: function() {
    this.$el.html(this.collection.pluck('id').join(', '));
    return this;
  },
});

