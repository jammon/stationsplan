"use strict";
var sp = sp || {};

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

function days_in_month (month, year) {
  var days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  return (month == 1) ? (year % 4 ? 28 : 29) : days[month];
}

// A person has a
//   - name
//   - id  = short form of the name
//   - start_date = begin of job
//   - end_date = end of job
sp.Person = Backbone.Model.extend({
  is_available: function(date) {
    var begin = this.get('start_date');
    var end = this.get('end_date');
    return ((!begin || begin<=date) && (!end || end>=date));
  },
});
sp.persons = new Backbone.Collection([], {
  model: sp.Person
});

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
sp.Ward = Backbone.Model;
sp.wards = new Backbone.Collection([], {
  model: sp.Ward
});
sp.nightshifts = new Backbone.Collection();
sp.on_leave = new Backbone.Collection();

sp.initialize_wards = function (wards_init) {
  sp.wards.reset(wards_init);
  sp.nightshifts.reset(sp.wards.where({'nightshift': true}));
  sp.on_leave.reset(sp.wards.where({'on_leave': true}));
};


// A staffing are the persons working on a ward on one day.
// It has
//   - ward
//   - day
sp.Staffing = Backbone.Collection.extend({
  model: sp.Person,
  initialize: function(models, options) {
    var day = this.day = options.day;
    this.ward = options.ward;
    this.on('add', day.person_added, day);
    this.on('remove', day.person_removed, day);
  },
  added_yesterday: function(person, staffing, options) {
    this.add_remove_person('add', person, staffing, options);
  },
  removed_yesterday: function(person, staffing, options) {
    this.add_remove_person('remove', person, staffing, options);
  },
  add_remove_person: function(action, person, staffing, options) {
    // continue yesterdays planning
    if (options.no_continue) return;
    if (!staffing.ward.get('on_leave') && this.day.is_on_leave(person)) 
      return;
    if (this.day.yesterdays_nightshift(person)) {
      // don't add/remove, but continue the chain
      this.trigger(action, person, staffing, options);
    } else {
      this[action](person);
    }
  },
});

// Duties are the duties of one person on one day
sp.Duties = Backbone.Collection.extend({
  model: sp.Ward,
});


// A "Day" controls all the staffings of that day.
// It has a 'date' and a reference to the previous day ('yesterday').
sp.Day = Backbone.Model.extend({

  initialize: function() {
    var that = this;
    var yesterday = this.get('yesterday');
    this.id = sp.Day.get_id(this.get('date'));

    this.persons_duties = {};  // duties for each person
    sp.persons.each(function(person) {
      that.persons_duties[person.id] = new sp.Duties();
    });

    this.ward_staffings = {};  // a staffing for each ward
    // can be undefined if this day is free
    sp.wards.each(this.get_staffing, this);
    if (yesterday) {
      yesterday.on('nightshift:added', this.last_nightshift_added, this);
      yesterday.on('nightshift:removed', this.last_nightshift_removed, this);
    }
  },
  get_staffing: function(ward) {
    var staffing, yesterdays_staffing;
    var options = { ward: ward, day: this };
    if (!is_free(this.get('date')) ||
        ward.get('everyday') ||
        ward.get('on_leave')) {
      staffing = new sp.Staffing([], options);
      if (ward.get('continued')) {
        yesterdays_staffing = this.yesterdays_staffing(ward);
        if (yesterdays_staffing) {
          staffing.reset(yesterdays_staffing.models);
          yesterdays_staffing.on('add', staffing.added_yesterday, staffing);
          yesterdays_staffing.on('remove', staffing.removed_yesterday, staffing);
        }
      }
      if (ward.get('on_leave')) {
        staffing.on('add', this.on_leave_added, this);
      }
    }
    this.ward_staffings[ward.id] = staffing;
  },

  store: function() {
    // stores an Array with the person.ids or undefined for every ward
    // returns a Promise
    var properties = _.mapObject(this.ward_staffings, function(val, key) {
      return val && val.pluck('id');
    });
    properties.id = sp.Day.get_id(this.get('date'));
    return hoodie.store.add('day', properties).fail(sp.store_error);
  },
  store_update: function(staffing) {
    var ward_id = staffing.ward.id;
    hoodie.store.update('day', this.id, {
      ward_id: staffing.pluck('id')
    }).fail(sp.store_error);
  },

  get_available: function(ward) {
    var unavailable = {};
    var available;
    var yesterday = this.get('yesterday');

    function get_ids (staffing) {
      staffing.each(function(person) { unavailable[person.id] = true; });
    }
    // yesterdays nightshift
    if (yesterday) {
      sp.nightshifts.each(function(ward) {
        get_ids(yesterday.ward_staffings[ward.id]);
      });
    }
    // persons on leave
    sp.on_leave.each(function(ward) {
      get_ids(this.ward_staffings[ward.id]);
    }, this);
    // persons planned for this ward
    get_ids(this.ward_staffings[ward.id]);

    available = sp.persons.filter(function(person) {
      return !unavailable[person.id];
    });
    return available;
  },
  is_on_leave: function(person) {
    return this.persons_duties[person.id].any(function(ward) {
      return ward.get('on_leave');
    });
  },
  yesterdays_nightshift: function(person) {
    var yesterday = this.get('yesterday');
    if (!yesterday) return false;
    return yesterday.persons_duties[person.id].any(function(ward) {
      return ward.get('nightshift');
    });
  },

  yesterdays_staffing: function(ward) {
    var yesterday = this.get('yesterday');
    if (!ward.get('everyday')) {
      while (yesterday && is_free(yesterday.get('date'))) {
        yesterday = yesterday.get('yesterday');
      }
    }
    return yesterday ? yesterday.ward_staffings[ward.id] : undefined;
  },

  person_added: function(person, staffing, options) {
    this.persons_duties[person.id].add(staffing.ward);
    if (staffing.ward.get('nightshift')) {
      this.trigger('nightshift:added', person, staffing.ward);
    }
    this.store_update(staffing);
  },
  person_removed: function(person, staffing, options) {
    this.persons_duties[person.id].remove(staffing.ward);
    if (staffing.ward.get('nightshift')) {
      this.trigger('nightshift:removed', person, staffing.ward);
    }
  },
  on_leave_added: function(person, staffing, options) {
    var ward_staffings = this.ward_staffings;
    _.each(this.persons_duties[person.id].filter(function(ward) {
      return !ward.get('on_leave');
    }), function(ward) {
      ward_staffings[ward.id].remove(person);
    });
  },
  last_nightshift_added: function(person, staffing, options) {
    var that = this;
    _.each(this.persons_duties[person.id].filter(function(ward) {
      return !ward.get('nightshift');
    }), function(ward) {
      that.ward_staffings[ward.id].remove(person, {no_continue: true});
    });
  },
  last_nightshift_removed: function(person, staffing, options) {
    var that = this;
    this.get('yesterday').persons_duties[person.id].each(function(ward) {
      that.ward_staffings[ward.id].add(person, {no_continue: true});
    });
  },
});
sp.Day.retrieve = function(date, yesterday) {
  var day = new sp.Day({ date: date, yesterday: yesterday });
  hoodie.store.find('day', sp.Day.get_id(date))
    .done(function(properties) {
      var prop = properties;
      prop.foo = 'bar';
      _.mapObject(properties, function(val, key) {
        var staffing, person;
        if (key!='id') {
          if (val) {
            staffing = new sp.Staffing([], {
              ward: sp.wards.get(key),
              day: day,
            });
            for (var i = 0; i < val.length; i++) {
              person = sp.persons.get(val[i]);
              staffing.add(person);
            }
            val = staffing;
          }
          day.ward_staffings[key] = val;
        }
      });
    })
    .fail(function(error) {
      throw error;
    });
  return day;
};
sp.Day.get_id = function(date) {
  function padStr(i) {
    return (i < 10) ? "0" + i : i;
  }
  return "" + date.getFullYear() +
         padStr(1 + date.getMonth()) +
         padStr(date.getDate());
};

sp.store_error = function(error) {
  $('#errors').append($('<li/>', { text: error }));
};

// // A WardMonth contains the staffings of a ward for a whole month
// // It has a 'ward' and a reference to the 'month'
// sp.WardMonth = Backbone.Model.extend({
//   staffings: [],
//   initialize: function() {},
// });

// // A Month contains all the plannings for every ward and person.
// // It has a 'month' and a 'year' and a reference to the 'last_month'.
// sp.Month = Backbone.Collection.extend({

// });
