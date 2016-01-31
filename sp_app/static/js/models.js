"use strict";

var $ = require('jquery');
var _ = require('underscore');
var Backbone = require('backbone');

var free_dates = [
    '2015.10.3',
    '2015.11.1',
    '2015.12.24',
    '2015.12.25',
    '2015.12.26',
    '2015.12.31',
    '2016.1.1',
];
var is_free = function (date) {
    var weekday = date.getDay();
    if (weekday===6 || weekday===0) {
        return true;
    }
    var date_string = date.getFullYear()+'.'+(date.getMonth()+1)+'.'+date.getDate();
    return (free_dates.indexOf(date_string) > -1);
};


// A person has a
//     - name
//     - id    = short form of the name
//     - start_date = begin of job
//     - end_date = end of job
var Person = Backbone.Model.extend({
    initialize: function() {
        var start = this.get('start_date') || [2015, 0, 1];
        this.set('start_date', new Date(start[0], start[1], start[2]));
        var end = this.get('end_date') || [2099, 11, 31];
        this.set('end_date', new Date(end[0], end[1], end[2]));
    },
    collection_array: 'persons_duties',
    row_class: function() { return 'personrow'; },
    is_available: function(date) {
        var begin = this.get('start_date');
        var end = this.get('end_date');
        return ((!begin || begin<=date) && (!end || end>=date));
    },
    can_work_on: function(ward) {
        var functions = this.get('functions');
        return _.indexOf(functions, ward.id)>-1;
    }
});

var Persons = Backbone.Collection.extend({
    model: Person,
    comparator: function(person) {
        return person.get('position') + person.get('name');
    },
});
var persons = new Persons();

// A ward can be a usual ward, a task or a shift.
// It has a 
//     - name
//     - shortname = short form of the name
//     - max = maximum staffing
//     - min = minimum staffing
//     - nightshift = if truthy, staffing can not be planned on the next day.
//     - everyday = if truthy, is to be planned also on free days.
//     - freedays = if truthy, is to be planned only on free days.
//     - continued = if truthy, then todays staffing will usually be continued tomorrow
//     - on_leave = if truthy, then persons planned for this are on leave
//     - approved = The date until which the plan is approved
//     - after_this = an Array of wards, that can be planned after this one
var Ward = Backbone.Model.extend({
    initialize: function() {
        var start = this.get('approved') || [2015, 0, 1];
        var after_this = this.get('after_this');
        this.set('approved', new Date(start[0], start[1], start[2]));
        if (after_this) {
            this.set('after_this', after_this.split(','));
        }
    },
    idAttribute: "shortname",
    collection_array: 'ward_staffings',
    row_class: function() {
        if (this.get('nightshift')) return 'nightshiftrow';
        if (!this.get('continued')) return 'non-continued-row';
        if (this.get('on_leave')) return 'leaverow';
        return 'wardrow';
    },
});


var Wards = Backbone.Collection.extend({
    model: Ward,
    comparator: function(ward) {
        var res = (ward.get('on_leave') ? '1' : '0') +  // on_leave last
            (ward.get('continued') ? '0' : '1') +  // normal wards first
            ward.get('position') +
            ward.get('name');
        return res;
    },
});
var wards = new Wards();
var nightshifts = new Backbone.Collection();
var on_leave = new Backbone.Collection();
var special_duties = new Backbone.Collection();

var initialize_wards = function (wards_init) {
    wards.reset(wards_init);
    nightshifts.reset(wards.where({'nightshift': true}));
    on_leave.reset(wards.where({'on_leave': true}));
    special_duties.reset(wards.filter(function(ward) {
        return ward.get('after_this')!==undefined;
    }));
};


// A staffing are the persons working on a ward on one day.
// It has
//     - ward
//     - day
var Staffing = Backbone.Collection.extend({
    model: Person,
    initialize: function(models, options) {
        this.day = options.day;
        this.ward = options.ward;
        this.displayed = new Backbone.Collection(null, { model: Person });
        this.on({
            'add': this.day.person_added,
            'remove': this.day.person_removed }, this.day);
        this.on({
            'add': this.person_added,
            'remove': this.person_removed }, this);
        this.comparator = 'name';
        this.no_staffing = !this.needs_staffing();
        this.add_issued = false;  // will be set to true
        // when an "add" change is issued for this day
        // so that a continued "remove" change on a *previous* day
        // won't delete this planning.
    },
    can_be_planned: function(person) {
        if (this.ward.get('on_leave')) return true;
        // is she/he on leave?
        if (this.day.persons_duties[person.id].any(function(ward) {
            return ward.get('on_leave');
        })) return false;
        // does yesterdays planning allow this?
        var yesterday = this.day.get('yesterday');
        var current_ward_id = this.ward.id;
        if (yesterday) {
            return yesterday.persons_duties[person.id].every(function(ward) {
                if (ward.get('nightshift')) return false;
                var after_this = ward.get('after_this');
                if (after_this && !_.contains(after_this, current_ward_id)) {
                    return false;
                }
                return true;
            });
        }
        return true;
    },
    calc_displayed: function(person) {
        if (this.no_staffing) {
            this.displayed.reset(null);
            return;
        }
        if (person) {
            this.displayed[this.can_be_planned(person) ? 'add' : 'remove'](person);
        } else {
            this.displayed.reset(this.filter(this.can_be_planned, this));
        }
    },
    person_added: function(person) {
        if (this.can_be_planned(person)) {
            this.displayed.add(person);
        }
    },
    person_removed: function(person) {
        this.displayed.remove(person);
    },
    added_yesterday: function(person, staffing, options) {
        this.continue_yesterday('add', person, options);
    },
    removed_yesterday: function(person, staffing, options) {
        if (!this.add_issued)
            this.continue_yesterday('remove', person, options);
    },
    continue_yesterday: function(action, person, options) {
        // continue yesterdays planning
        if (!options.continued) return;
        if (person.get('end_date')<this.day.get('date')) return;
        this[action](person, options);
    },
    lacking: function() {
        return this.displayed.length<this.ward.get('min');
    },
    room_for_more: function() {
        return this.displayed.length<this.ward.get('max');
    },
    needs_staffing: function() {
        var ward = this.ward;
        if (ward.get('everyday') || ward.get('on_leave')) {
            return true;
        }
        var day_is_free = is_free(this.day.get('date'));
        var for_free_days = (ward.get('freedays') || false);
        return day_is_free == for_free_days;
    },
    apply_change: function(change) {
        var person = persons.get(change.person);
        if (person) {
            this[change.action](person, { continued: change.continued });
            this.add_issued = change.action==="add";
        }
    },
});

// Duties are the duties of one person on one day
var Duties = Backbone.Collection.extend({
    model: Ward,
});


// A "Day" controls all the staffings of that day.
// It has a 'date' and a reference to the previous day ('yesterday').

// this.ward_staffings:  
//     an Array with a staffing for each ward.
//     The staffing can be undefined if this day is free.
//     All changes should be done on the staffings and are reflected in the duties.
// this.persons_duties:  
//     an Array with duties for each person
var Day = Backbone.Model.extend({

    initialize: function() {
        var that = this;
        var yesterday = this.get('yesterday');
        this.id = Day.get_id(this.get('date'));

        var ward_staffings = this.ward_staffings = {};
        wards.each(this.make_staffing, this);

        this.persons_duties = {};
        persons.each(this.make_duties, this);

        wards.each(function(ward) {
            if (ward_staffings[ward.id])
                ward_staffings[ward.id].calc_displayed();
        });

        this.persons_available = {};

        this.on('on_leave-changed', this.calc_persons_display, this);
        if (yesterday) {
            yesterday.on('nightshift-changed', this.calc_persons_display, this);
            yesterday.on('special-duty-changed', this.calc_persons_display, this);
        }
    },
    make_staffing: function(ward) {
        var staffing = new Staffing([], { ward: ward, day: this });
        var yesterdays_staffing = this.yesterdays_staffing(ward);
        var date = this.get('date');
        if (yesterdays_staffing) {
            yesterdays_staffing.on({
                'add': staffing.added_yesterday,
                'remove': staffing.removed_yesterday,
            }, staffing);
            if (ward.get('continued')) {
                staffing.reset(yesterdays_staffing.filter(function(person) {
                    return person.get('end_date') >= date;
                }));
            }
        }
        this.ward_staffings[ward.id] = staffing;
    },
    make_duties: function(person) {
        var duties = new Duties();
        var ward_staffings = this.ward_staffings;
        wards.each(function(ward) {
            var staffing = ward_staffings[ward.id];
            if (staffing && staffing.get(person)) {
                duties.add(ward);
            }
        });
        this.persons_duties[person.id] = duties;
    },
    calc_availability: function(person) {
        var that = this;
        var yesterday = this.get('yesterday');
        if (this.persons_duties[person.id].any(function(ward) {
            return ward.get('on_leave');
        }) || yesterday.persons_duties[person.id].any(function(ward) {
            return ward.get('nightshift');
        })) {
            this.persons_available[person.id] = on_leave;
        }
    },
    get_available: function(ward) {
        // Get all the persons, that can be planned for this ward
        // and are not planned already
        var unavailable = {};
        var available;
        var yesterday = this.get('yesterday');
        var date = this.get('date');

        if (ward.get('on_leave')) {  // everybody can be on leave
            return persons.models;
        }
        function get_unavailables (staffing) {
            if (staffing)
                staffing.each(function(person) {
                    unavailable[person.id] = true;
                });
        }
        // yesterdays nightshift
        if (yesterday) {
            nightshifts.each(function(ward) {
                get_unavailables(yesterday.ward_staffings[ward.id]);
            });
        }
        // persons on leave
        on_leave.each(function(ward) {
            get_unavailables(this.ward_staffings[ward.id]);
        }, this);

        available = persons.filter(function(person) {
            return !unavailable[person.id] &&
                person.is_available(date) &&
                person.can_work_on(ward);
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
        return yesterday && yesterday.ward_staffings[ward.id];
    },

    // The next two functions are called when the staffing changes
    person_added: function(person, staffing, options) {
        this.person_changed('add', person, staffing, options);
    },
    person_removed: function(person, staffing, options) {
        this.person_changed('remove', person, staffing, options);
    },
    person_changed: function(action, person, staffing, options) {
        var ward = staffing.ward;
        this.persons_duties[person.id][action](ward);
        if (ward.get('on_leave')) {
            this.trigger('on_leave-changed', person, action);
        }
        if (ward.get('nightshift')) {
            this.trigger('nightshift-changed', person, action);
        }
        if (ward.get('after_this')!==undefined) {
            this.trigger('special-duty-changed', person, ward, action);
        }
    },
    calc_persons_display: function(person) {
        var ward_staffings = this.ward_staffings;
        this.persons_duties[person.id].each(function(ward) {
            ward_staffings[ward.id].calc_displayed(person);
        });
    },
});
function padStr(i) {
    return (i < 10) ? "0" + i : i;
};
Day.get_id = function(date) {
    return "" + date.getFullYear() +
                padStr(1 + date.getMonth()) +
                padStr(date.getDate());
};
var days = {};

var get_month_id = function(year, month) {
    return "" + year + padStr(1 + month);
};

var change_and_store = function(person_id, staffing, action) {
    var person = persons.get(person_id);
    staffing[action](person);
    $.post({
        url: '/change', 
        data: {
            person: person_id,
            ward: staffing.ward.get('shortname'),
            day: staffing.day.id,
            action: action,
        },
        error: function(jqXHR, textStatus, errorThrown) {
            store_error(textStatus, 'error');
        },
        success: function(data, textStatus, jqXHR) {
            if (data.warning) {
                store_error(data.warning, 'warning');
            }
        },
    });
};

var apply_change = function(change) {
    var day = days[change.day];
    var staffing;
    if (day) {
        staffing = day.ward_staffings[change.ward];
        if (staffing) {
            staffing.apply_change(change);
            return;
        }
    }
    // Something went wrong
    // TODO: This can happen when the first of month is a weekend day
    console.log(change);
};

var store_error = function(error, type) {
    $('#log').append($('<p/>', { text: error, 'class': type }));
};

module.exports = {
    is_free: is_free,
    Person: Person,
    Persons: Persons,
    Ward: Ward,
    Wards: Wards,
    persons: persons,
    wards: wards,
    nightshifts: nightshifts,
    on_leave: on_leave,
    special_duties: special_duties,
    initialize_wards: initialize_wards,
    Staffing: Staffing,
    Duties: Duties,
    Day: Day,
    days: days,
    get_month_id: get_month_id,
    apply_change: apply_change, //
    store_error: store_error, //
};