"use strict";

// A person has a
//   - name
//   - id  = short form of the name
var Person = Backbone.Model;
var persons = new Backbone.Collection([], {
  model: Person
});

function initialize_persons (persons_init) {
  persons.reset(persons_init);
}

// A ward can be a usual ward, a task or a shift.
// It has a 
//   - name
//   - id  = short form of the name
//   - max = maximum staffing
//   - min = minimum staffing
//   - nightshift = if truthy, staffing can not be planned on the next day.
//   - everyday = if truthy, is to be planned also on free days.
//   - continued = if truthy, then todays staffing will be planned for tomorrow
//   - on_leave = if truthy, then persons planned for this are on leave
var Ward = Backbone.Model;
var wards = new Backbone.Collection([], {
  model: Ward
});
var nightshifts = new Backbone.Collection();
var on_leave = new Backbone.Collection();

function initialize_wards (wards_init) {
  wards.reset(wards_init);
  nightshifts.reset(wards.where({'nightshift': true}));
  on_leave.reset(wards.where({'on_leave': true}));
}
// A staffing are the persons working on a ward on one day.
// It has
//   - ward
//   - day
var Staffing = Backbone.Collection.extend({
  model: Person,
});

// Duties are the duties of one person on one day
var Duties = Backbone.Collection.extend({
  model: Ward,
});


var free_dates = [
  '2015.10.3',
  '2015.11.1',
  '2015.12.24',
  '2015.12.25',
  '2015.12.26',
  '2015.12.31',
  '2016.1.1.',
];
function is_free(date) {
  var weekday = date.getDay();
  if (weekday===6 || weekday===0) {
    return true;
  }
  var date_string = date.getFullYear()+'.'+(date.getMonth()+1)+'.'+date.getDate();
  return (free_dates.indexOf(date_string) > -1);
}

// A "Day" controls all the staffings of that day.
// It has a date and a reference to the previous day.
var Day = Backbone.Model.extend({

  initialize: function() {
    var that = this;
    var yesterday = this.get('yesterday');

    this.persons_duties = {};  // duties for each person
    persons.each(function(person) {
      var duties = new Duties();
      that.persons_duties[person.id] = duties;
    });

    this.ward_staffings = {};  // a staffing for each ward    
    wards.each(function(ward) {
      var staffing = new_staffing(ward, that);
      that.ward_staffings[ward.id] = staffing;
      staffing.on('add', that.person_added, that);
      staffing.on('remove', that.person_removed, that);
    });

    this.check_availability(yesterday);
  },

  new_staffing: function (ward) {
    var staffing, yesterdays_staffing;
    if (ward.get('continued')) {
      yesterdays_staffing = this.yesterdays_staffing(ward);
      staffing = new Staffing(yesterdays_staffing);
      yesterdays_staffing.on('add', staffing.add, staffing);
      yesterdays_staffing.on('remove', staffing.remove, staffing);
    } else {
      staffing = new Staffing();
    }
    staffing.ward = ward;
    staffing.day = this;
    return staffing;
  },

  get_available: function(ward) {
    var unavailable = [];
    var yesterday = this.get('yesterday');

    // yesterdays nightshift
    if (yesterday) {
      nightshifts.each(function(ward) {
        unavailable = unavailable.concat(
          yesterday.ward_staffings[ward.id].models);
      });
    }
    // persons on leave
    unavailable = unavailable.concat(this.on_leave.models);
    this.unavailable = unavailable;

    this.available = persons.difference(unavailable);
  },

  check_availability: function(yesterday) {
    // update this.available and this.unavailable
    var unavailable = [];

    // yesterdays nightshift
    if (yesterday) {
      nightshifts.each(function(ward) {
        unavailable = unavailable.concat(
          yesterday.ward_staffings[ward.id].models);
      });
    }
    // persons on leave
    on_leave.each(function(ward) {
      unavailable = unavailable.concat(
        this.ward_staffings[ward.id].models);
    });

    return persons.difference(unavailable);
  },

  yesterdays_staffing: function(ward) {
    var yesterday = this.get('yesterday');
    if (!ward.get('everyday')) {
      while (yesterday && is_free(yesterday.get('date'))) {
        yesterday = yesterday.get('yesterday');
      }
    }
    return yesterday ? yesterday.ward_staffings[ward] : undefined;
  },

  person_added: function(person, staffing) {
    this.persons_duties[person.id].add(staffing.ward);
    if (staffing.ward.get('nightshift')) {
      this.trigger('nightshift:added', person, staffing.ward);
    }
  },
  person_removed: function(person, staffing) {
    this.persons_duties[person.id].remove(staffing.ward);
    if (staffing.ward.get('nightshift')) {
      this.trigger('nightshift:removed', person, staffing.ward);
    }
  },
});

