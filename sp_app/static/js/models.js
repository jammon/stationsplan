var models = (function($, _, Backbone) {
"use strict";

var default_start_for_person = [2015, 0, 1];
var default_end_for_person = [2099, 11, 31];

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

function initialize_wards (wards_init) {
    wards.reset(wards_init);
    nightshifts.reset(wards.where({'nightshift': true}));
    on_leave.reset(wards.where({'on_leave': true}));
    special_duties.reset(wards.filter(function(ward) {
        return ward.get('after_this') !== void 0;
    }));
}


// A staffing are the persons working on a ward on one day.
// It has
//     - ward
//     - day
var Staffing = Backbone.Collection.extend({
    model: Person,
    comparator: 'name',
    initialize: function(models, options) {
        this.day = options.day;
        this.ward = options.ward;
        this.displayed = new Backbone.Collection(null, { 
            model: Person,
            comparator: 'name',
        });
        this.on({
            'add': this.person_added,
            'remove': this.person_removed }, this);
        this.on({
            'add': this.day.person_added,
            'remove': this.day.person_removed }, this.day);
        this.no_staffing = !this.needs_staffing();
        this.added_today = [];  // holds the ids of the persons added on this day
        // so that a continued "remove" change on a *previous* day
        // won't delete this planning.
    },
    can_be_planned: function(person) {
        // a vacation can always be planned
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
        if (this.added_today.indexOf(person.id)==-1)
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
        var day_is_free = utils.is_free(this.day.get('date'));
        var for_free_days = (ward.get('freedays') || false);
        return day_is_free == for_free_days;
    },
    apply_change: function(change) {
        var person = persons.get(change.person);
        if (person) {
            this[change.action](person, { continued: change.continued });
            if (change.action==="add") {
                this.added_today.push(person.id);
            } else {
                // remove person.id from this.added_today
                var i = this.added_today.indexOf(person.id);
                if (i!=-1) {
                    this.added_today.splice(i, 1);
                }
            }
        }
    },
});

// Duties are the duties of one person on one day
var Duties = Backbone.Collection.extend({
    model: Ward,
    initialize: function(models, options) {
        this.person = options.person;
        this.day = options.day;
        this.displayed = new Backbone.Collection(null, {model: Ward});
    },
    calc_displayed: function() {
        var that = this;
        this.displayed.reset(
            this.filter(function(ward) {
                return that.day.ward_staffings[ward.id].displayed.get(that.person);
            }));
    },
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
        var yesterday = this.get('yesterday');
        this.id = utils.get_day_id(this.get('date'));
        this.set({'id': this.id});

        var ward_staffings = this.ward_staffings = {};
        this.persons_duties = {};

        wards.each(function(ward) {
            this.ward_staffings[ward.id] = new Staffing([], 
                { ward: ward, day: this });
        }, this);
        persons.each(function(person) {
            this.persons_duties[person.id] = new Duties([], 
                { person: person, day: this });
        }, this);

        this.persons_available = {};
        this.on('on_leave-changed', this.calc_persons_display, this);
        if (yesterday) {
            yesterday.on('nightshift-changed', this.calc_persons_display, this);
            yesterday.on('special-duty-changed', this.calc_persons_display, this);
            this.continue_yesterdays_staffings();
        }
    },
    continue_yesterdays_staffings: function() {
        var date = this.get('date');
        wards.each(function(ward) {
            var staffing = this.ward_staffings[ward.id];
            var yesterdays_staffing = this.yesterdays_staffing(ward);
            if (yesterdays_staffing) {
                yesterdays_staffing.on({
                    'add': staffing.added_yesterday,
                    'remove': staffing.removed_yesterday,
                }, staffing);
                yesterdays_staffing.each(function(person) {
                    if (person.get('end_date') >= date) {
                        staffing.add(person);
                    }
                });
            }
        }, this);
        
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
        function get_unavailables (day, wards) {
            wards.each(function(ward) {
                var staffing = day.ward_staffings[ward.id];
                if (staffing) {
                    staffing.each(function(person) {
                        unavailable[person.id] = true;
                    });
                }
            });
        }
        // yesterdays nightshift
        if (yesterday) get_unavailables(yesterday, nightshifts);
        // persons on leave
        get_unavailables(this, on_leave);

        available = persons.filter(function(person) {
            return !unavailable[person.id] &&
                person.is_available(date) &&
                person.can_work_on(ward);
        });
        return available;
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
        if (ward.get('after_this') !== void 0) {
            this.trigger('special-duty-changed', person, ward, action);
        }
        this.persons_duties[person.id].calc_displayed();
    },
    calc_persons_display: function(person) {
        var ward_staffings = this.ward_staffings;
        this.persons_duties[person.id].each(function(ward) {
            ward_staffings[ward.id].calc_displayed(person);
        });
    },
    apply_planning: function(pl) {
        if (this.id>=pl.start && this.id<=pl.end) {
            this.ward_staffings[pl.ward].add(persons.get(pl.person), {
                continued: false
            });
            return true;
        }
        return false;
    },
    make_next_day: function() {
        var date = this.get('date');
        var next_day = days.add({
            date: new Date(date.getFullYear(), date.getMonth(),
                           date.getDate()+1),
            yesterday: this
        });
        // remove all plannings, that have ended
        current_plannings = _.filter(current_plannings, function(planning) {
            if (planning.end<next_day.id) {
                next_day.ward_staffings[planning.ward].remove(
                    persons.get(planning.person));
                return false;
            }
            return true;
        });
        // add all plannings, that start on this day
        _.each(plannings, function(planning) {
            if (planning.start==next_day.id) {
                next_day.apply_planning(planning);
                current_plannings.push(planning);
            }
        });
        return next_day;
    },
    get_month_id: function() {
        return  this.id.slice(0, 6);
    },
});

var plannings;  // Array of plannings to be applied
var current_plannings = [];

var Days = Backbone.Collection.extend({
    model: Day,
    get_day: function(year, month, day) {
        // month is 0..11 like in javascript
        var result, day_id;
        if (this.length===0) {
            // Start day chain
            result = this.add({ date: new Date(year, month, day) });
            // Start application of the plannings
            current_plannings = _.filter(plannings, result.apply_planning, result);
            return result;
        }
        // Retrieve result, if it exists already
        day_id = utils.get_day_id(year, month, day);
        result = this.get(day_id);
        if (result) 
            return result;
        // Build new days 
        result = this.last();
        if (day_id < result.id) {
            // requested day is before the start of the day chain
            // should not happen
            return void 0;
        }
        while (result.id < day_id) {
            result = result.make_next_day();
        }
        return result;
    },    
});

var days = new Days();

function start_day_chain(year, month) {
    days.get_day(year, month, 1);
}

// Returns Array with the Days of the current month
// This should only be called in sequence
function get_month_days(year, month) {
    // month is 0..11 like in javascript
    var month_days = [];
    var i = 1;
    var next_day = days.get_day(year, month, i);
    do {
        month_days.push(next_day);
        next_day = days.get_day(year, month, ++i);
    } while (next_day.get('date').getMonth()===month);
    return month_days;
}


function set_plannings(p) {
    plannings = p;
}


function apply_change(change) {
    var changed_day = days.get(change.day);
    var staffing;
    if (changed_day) {
        staffing = changed_day.ward_staffings[change.ward];
        if (staffing) {
            staffing.apply_change(change);
            return;
        }
    }
    // Something went wrong
    console.log(change);
}

function store_error(error, type) {
    $('#log').append($('<p/>', { text: error, 'class': type }));
}

function reset_data() {
    // for testing
    persons.reset(null);
    wards.reset(null);
    nightshifts.reset(null);
    on_leave.reset(null);
    special_duties.reset(null);
    days.reset();
}

return {
    Person: Person,
    Persons: Persons,
    persons: persons,
    Ward: Ward,
    Wards: Wards,
    wards: wards,
    nightshifts: nightshifts,
    on_leave: on_leave,
    special_duties: special_duties,
    initialize_wards: initialize_wards,
    Staffing: Staffing,
    Duties: Duties,
    Day: Day,
    days: days,
    start_day_chain: start_day_chain,
    get_month_days: get_month_days,
    // get_day: get_day,
    set_plannings: set_plannings,
    apply_change: apply_change,
    store_error: store_error,
    reset_data: reset_data,
};
})($, _, Backbone);
