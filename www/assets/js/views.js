"use strict";
var sp = sp || {};

var DayView, RowView, WardView, PersonView, StaffingView, DutiesView, NoStaffingView;

sp.RowView = Backbone.View.extend({
  tagName: 'tr',
  render: function() {
    this.$el.html($('<th/>', {text: this.model.get('name')}));
  }
});
sp.WardView = sp.PersonView = sp.RowView;


sp.StaffingView = Backbone.View.extend({
  tagName: 'td',
  events: {
    "click .addstaff": "addstaff",
    "click option": "person_selected",
    "dblclick .staff": "remove_person",
  },
  initialize: function() {
    this.listenTo(this.collection, "update", this.render);
  },
  render: function() {
    var el = this.$el;
    el.empty();
    this.collection.each(function(person) {
      el.append($('<div/>', {
        text: person.id,
        'class': 'staff',
      }));
    });
    if (this.collection.length<this.collection.ward.get('max')) {
      el.append($('<div/>', {
          text: '+',
          'class': 'addstaff',
        }));
    }
    el.toggleClass('lacking', this.collection.length<this.collection.ward.get('min'));
    return this;
  },
  addstaff: function() {
    var coll = this.collection;
    var available = coll.day.get_available(coll.ward);
    var select = $('<select/>');
    select.append($('<option/>', {
      text: '---',
      name: '---',
    }));
    _.each(available, function(person) {
      select.append($('<option/>', {
        text: person.get('name'),
        value: person.id,
      }));
    });
    this.$(".addstaff").hide();
    this.$el.append(select);
    select.focus();
  },
  person_selected: function(event, options) {
    var id = event.target.value;
    if (id == '---') {
      this.selection_aborted();
    }
    this.$('select').remove();
    var person = sp.persons.get(id);
    this.collection.add(person);
    // this.render();
  },
  selection_aborted: function() {
    this.$('select').remove();
    this.$(".addstaff").show();
  },
  remove_person: function(event) {
    var id = event.target.textContent;
    var person = sp.persons.get(id);
    this.collection.remove(person);
  },
});

sp.DutiesView = Backbone.View.extend({
  tagName: 'td',
  initialize: function() {
    this.listenTo(this.collection, "update", this.render);
  },
  render: function() {
    this.$el.html(this.collection.pluck('id').join(', '));
    return this;
  },
});

