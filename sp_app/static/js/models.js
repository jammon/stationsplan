// jshint esversion: 6
var models = (function($, _, Backbone) {
"use strict";

// This module contains
// - all the constructors for the data models (`Person`, `Ward` etc.),
// - the data models themselves (`persons`, `wards` etc.),
// - some data determining the working status 
//   (like `user`, `errors` etc.)

var default_start_for_person = [2015, 0, 1];
var default_end_for_person = [2099, 11, 31];
var user = {
    is_editor: false,
    is_dep_lead: false,
};

var Current_Date = Backbone.Model.extend({
    initialize: function() {
        this.set({ date_id: utils.get_day_id(new Date()) });
    },
    update: function() {
        var today_id = utils.get_day_id(new Date());
        this.set({ date_id: today_id });
    },
    is_today: function(date_id) {
        return date_id == this.get('date_id');
    },
});
var current_date = new Current_Date();

// A person has a
//     - name
//     - shortname = short form of the name
//     - id
//     - start_date = begin of job
//     - end_date = end of job
//     - functions = Array of Wards/Tasks that can be done
//     - departments = Array of Department-Ids the person belongs to
//     - position = position in the listing
//     - anonymous = true if it represents a different department
var Person = Backbone.Model.extend({
    idAttribute: "shortname",
    defaults: {
        'start_date': [2015, 0, 1],
        'end_date': [2099, 11, 31],
        'position': '01',
        'anonymous': false,
    },
    initialize: function() {
        var start = this.get('start_date');
        this.set('start_date', new Date(start[0], start[1], start[2]));
        var end = this.get('end_date');
        this.set('end_date', new Date(end[0], end[1], end[2]));
        this.set(
            'current_department',
            this.get('departments').indexOf(user.current_department) > -1
        );
    },
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
    // all persons available on this date
    available: function(date) {
        return this.filter(function(person) {
            return person.is_available(date);
        });
    },
});
var persons = new Persons();

// A ward can be a usual ward, a task or a shift.
// It has a 
//     - name
//     - shortname = short form of the name
//     - id
//     - max = maximum staffing
//     - min = minimum staffing
//     - everyday = if truthy, is to be planned also on free days.
//     - freedays = if truthy, is to be planned only on free days.
//     - weekdays = Days of the week when this is to be planned.
//     - callshift = if truthy, then this function is treated as call shift
//     - on_leave = if truthy, then persons planned for this are on leave
//     - approved = The date until which the plan is approved or false
//     - after_this = an Array of wards, that can be planned after this one
//     - ward_type = none or '' or type of ward (for handling of call shifts)
//     - active = Boolean; if false, this ward should not be shown
var Ward = Backbone.Model.extend({
    initialize: function() {
        var approved = this.get('approved');
        if (approved)
            this.set('approved', new Date(approved[0], approved[1], approved[2]));
        var after_this = this.get('after_this');
        if (after_this) {
            this.set('after_this', after_this.split(','));
        }
        this.set('weight', this.get('weight') || 0);
        this.different_days = {};
    },
    idAttribute: "shortname",
    get_ward_type: function() {
        return this.get('ward_type') || this.get('name');
    },
    is_approved: function(date) {
        var approved = this.get('approved');
        return !approved || (date <= approved);
    },
    set_different_day: function(date_id, key) {
        // key is '+' if added else '-'
        this.different_days[date_id] = key;
    },
});


var WARD_COLLECTION = {
    model: Ward,
    // Sorting of wards:
    // At first the normal wards, then the callshifts, then 'on leave'
    comparator: function(ward) {
        return (ward.get('on_leave') ? '1' : '0') +  // on_leave last
            (ward.get('callshift') ? '1' : '0') +  // normal wards first
            ward.get('position') +
            ward.get('name');
    },
};
var Wards = Backbone.Collection.extend(WARD_COLLECTION);
var wards = new Wards();
// nightshifts - wards with an limited list of "after_this"
var nightshifts = new Backbone.Collection(null, WARD_COLLECTION);
var on_leave = new Backbone.Collection(null, WARD_COLLECTION);
var on_call = new Backbone.Collection(null, WARD_COLLECTION);
var on_call_types = [];  // List of the ward_types of on-call shifts

function initialize_wards (wards_init, different_days) {
    wards.reset(wards_init);
    nightshifts.reset(wards.filter(function(ward) { 
        return ward.get('after_this'); 
    }));
    on_leave.reset(wards.where({'on_leave': true}));
    on_call.reset(wards.filter(function(ward) {
        return ward.get('callshift');
    }));
    on_call.each(function(ward) {
        var ward_type = ward.get_ward_type();
        if (!_.contains(on_call_types, ward_type))
            on_call_types.push(ward_type);
    });
    _.each(different_days, function(dd) {
        wards.get(dd[0]).set_different_day(dd[1], dd[2]);
    });
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
        this.displayed = new Backbone.Collection(null, { 
            model: Person,
            comparator: 'name',
        });
        this.ward = this.displayed.ward = options.ward;
        this.on({
            'add': this.person_added,
            'remove': this.person_removed }, this);
        this.on({
            'add': this.day.person_added,
            'remove': this.day.person_removed }, this.day);
        this.no_staffing = !needs_staffing(this.ward, this.day);
        this.added_today = [];  // holds the ids of the persons added on this day
        // so that a continued "remove" change on a *previous* day
        // won't delete this planning.
    },
    can_be_planned: function(person) {
        if (!person) return false;
        // a vacation can be planned for the members of the current department
        if (this.ward.get('on_leave')) 
            return person.get('current_department');
        // is she/he on leave?
        if (this.day.persons_duties[person.id].where({on_leave: true}).length>0)
            return false;
        // Is this ward in their portfolio?
        if (!person.can_work_on(this.ward)) return false;
        // does yesterdays planning allow this?
        if (!person.get('anonymous')) {
            var yesterday = this.day.get('yesterday');
            var current_ward_id = this.ward.id;
            if (yesterday) {
                // if they were on leave yesterday, they can be planned
                if (yesterday.persons_duties[person.id].where({on_leave: true}).length>0)
                    return true;
                // do yesterdays plannings allow this?
                return yesterday.persons_duties[person.id].every(function(ward) {
                    var after_this = ward.get('after_this');
                    if (after_this && !_.contains(after_this, current_ward_id)) {
                        return false;
                    }
                    return true;
                });
            }
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
        if (options.until && options.until>=this.day.id ||
            this.added_today.indexOf(person.id)==-1)
            this.continue_yesterday('remove', person, options);
    },
    continue_yesterday: function(action, person, options) {
        // continue yesterdays planning
        if (!options.continued) return;
        if (options.until && options.until<this.day.id) return;
        if (person.get('end_date')<this.day.get('date')) return;
        this[action](person, options);
        if (options.until && options.until>this.day.id) {
            if (action=='add' && this.contains(person) ||
                action=='remove' && !this.contains(person)) {
                this.trigger(action, person, this, options);
            }
        }
    },
    lacking: function() {
        return this.displayed.length<this.ward.get('min');
    },
    room_for_more: function() {
        return this.displayed.length<this.ward.get('max');
    },
    apply_change: function(change) {
        var person = persons.get(change.person);
        if (person) {
            this[change.action](person, _.pick(change, 'continued', 'until'));
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
function needs_staffing(ward, day) {
    // True if persons can be planned for this day
    if (ward.get('everyday') || ward.get('on_leave')) {
        return true;
    }
    var different_day = ward.different_days[day.id];
    if (different_day) return (different_day == '+');
    var weekdays = ward.get('weekdays');
    if (weekdays)
        return weekdays.indexOf(day.get('date').getDay()) > -1;
    var day_is_free = !!day.get('is_free'); // must be boolean
    var for_free_days = (ward.get('freedays') || false);
    return day_is_free == for_free_days;
}

// Duties are the duties of one person on one day
var Duties = Backbone.Collection.extend({
    model: Ward,
    initialize: function(models, options) {
        this.person = options.person;
        this.day = options.day;
        this.displayed = new Backbone.Collection(null, {model: Ward});
    },
    calc_displayed: function() {
        let day = this.day;
        let person = this.person;
        this.displayed.reset(
            this.filter(function(ward) {
                return day.get_staffing(ward).displayed.get(person);
            }));
    },
});


// A "Day" controls all the staffings of that day.
// It has a 'date' and a reference to the previous day ('yesterday').

// this.ward_staffings:  
//     an object with a staffing for each ward.
//     If this day is free, the staffing has no_staffing==true
//     All changes should be done on the staffings and are reflected in the duties.
// this.persons_duties:  
//     an object with duties for each person
var Day = Backbone.Model.extend({

    initialize: function() {
        var yesterday = this.get('yesterday');
        this.id = utils.get_day_id(this.get('date'));
        this.set({'id': this.id});
        let _is_free = utils.is_free(this.get('date'));
        this.set({'is_free': !!_is_free});
        if (_.isString(_is_free))
            this.set('holiday', _is_free);

        this.ward_staffings = {};
        this.persons_duties = {};
        this.update_not_planned();

        wards.each(function(ward) {
            this.ward_staffings[ward.id] = new Staffing(
                [], { ward: ward, day: this });
        }, this);
        persons.each(function(person) {
            let duties = this.persons_duties[person.id] = new Duties(
                [], { person: person, day: this });
        }, this);

        this.on('on_leave-changed', this.calc_persons_display, this);
        this.on('person-changed', this.update_not_planned, this);
        if (yesterday) {
            yesterday.on('special-duty-changed', this.calc_persons_display, this);
            yesterday.on('special-duty-changed', this.update_not_planned, this);
            this.continue_yesterdays_staffings();
        }
        this.update_is_today();
        current_date.on('change:date_id', this.update_is_today, this);
    },
    update_is_today: function() {
        this.set({ is_today: current_date.is_today(this.id) });
    },
    continue_yesterdays_staffings: function() {
        var date = this.get('date');
        wards.each(function(ward) {
            var staffing = this.get_staffing(ward);
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
        function ward_unavailable(day, unavailable_ward) {
            let staffing = day.get_staffing(unavailable_ward);
            if (staffing) {
                staffing.each(function(person) {
                    unavailable[person.id] = true;
                });
            }
        }
        function get_unavailables (day, wards) {
            // all persons working on this ward at this day are unavailable
            wards.each(function(ward) {
                ward_unavailable(day, ward);
            });
        }
        // yesterdays nightshift
        if (yesterday) {
            nightshifts.each(function(nightshift) {
                if (!_.contains(nightshift.get('after_this'), ward.id))
                    ward_unavailable(yesterday, nightshift);
            });
        }
        // persons on leave
        get_unavailables(this, on_leave);

        available = persons.filter(function(person) {
            return !unavailable[person.id] &&
                person.is_available(date) &&
                person.can_work_on(ward);
        });
        return available;
    },

    get_staffing: function(ward) {
        return this.ward_staffings[ward.id];
    },
    yesterdays_staffing: function(ward) {
        var yesterday = this.get('yesterday');
        return yesterday && yesterday.get_staffing(ward);
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
        this.trigger('person-changed', action, person, staffing);
        if (ward.get('on_leave')) {
            this.trigger('on_leave-changed', person, action);
        }
        if (ward.get('after_this') !== void 0) {
            this.trigger('special-duty-changed', person, ward, action);
        }
        this.persons_duties[person.id].calc_displayed();
    },
    calc_persons_display: function(person) {
        this.persons_duties[person.id].each(function(ward) {
            this.get_staffing(ward).calc_displayed(person);
        }, this);
    },
    apply_planning: function(pl) {
        if (this.id>=pl.start && this.id<=pl.end) {
            this.get_staffing(pl.ward).add(pl.person, {continued: false});
            return true;
        }
        return false;
    },
    apply_change: function(change) {
        let staffing = this.ward_staffings[change.ward];
        if (staffing) {
            staffing.apply_change(change);
        }
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
                next_day.get_staffing(planning.ward).remove(
                    planning.person);
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
        // FIXME: check new changes
        return next_day;
    },
    get_month_id: function() {
        return  this.id.slice(0, 6);
    },
    update_not_planned: function() {
        // not planned ist everybody who 
        // - is not anonymous
        // - belongs to the current department
        // - has no duties 
        // - is not yesterdays nightshift
        // - is not Chefarzt

        // not applicable on free days
        if (this.get('is_free')) return [];

        // not anonymous
        // belongs to the current department
        // not Chefarzt
        let available = persons.available(this.get('date'));
        this.not_planned = _.filter(
            available, 
            function(person) { 
                let not_anonymous = !person.get('anonymous');
                let current_department = person.get('current_department');
                let not_chefarzt = (person.get('position') < '80'); 
                return not_anonymous && current_department && not_chefarzt;
            }
        );
        // no duties
        if (!_.isEmpty(this.persons_duties)) {
            this.not_planned = _.filter(
                this.not_planned,
                function(person) {
                    let duties = this.persons_duties[person.id];
                    return !(duties && duties.length>0);
                }, 
                this);
        }
        // not yesterdays nightshift
        let yesterday = this.get('yesterday');
        if (yesterday) {
            let yesterdays_nightshifters = nightshifts.map(function(ward) {
                return yesterday.get_staffing(ward).models;
            });
            let yesterdays_nightshift = _.uniq(_.flatten(yesterdays_nightshifters));
            this.not_planned = _.difference(
                this.not_planned,
                yesterdays_nightshift
            );
        }
    },
});

var plannings;  // Array of plannings to be applied
var current_plannings = [];

var Days = Backbone.Collection.extend({
    model: Day,
    get_day: function(date, offset) {
        // Days.get_day(date) - get the day on this date
        // Days.get_day(date, offset) - get the day <offset> days after this date
        let result;
        let _date = new Date(date);
        if (offset)
            _date.setDate(_date.getDate() + parseInt(offset));
        if (_date.getFullYear()<2015)
            // should not happen
            // we don't deal with historical plans 
            return void 0;
        if (this.length===0) {
            // Start day chain
            result = this.add({ date: _date });
            // Start application of the plannings
            current_plannings = _.filter(plannings, result.apply_planning, result);
        } else {
            // Retrieve result, if it exists already
            let day_id = utils.get_day_id(_date);
            result = this.get(day_id);
            if (!result) {
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
            }
        }
        return result;
    },    
});

var days = new Days();

function start_day_chain(year, month) {
    days.get_day(new Date(year, month, 1));
}

// the 'Day's of one period.
var PeriodDays = Backbone.Collection.extend({
    initialize: function(models, options) {
        this.first_day = options.first_day;
        this.nr_days = options.nr_days;
        var year = this.first_day.getFullYear();
        var month = this.first_day.getMonth();
        var day = this.first_day.getDate();
        for (var i = 0; i < this.nr_days; i++) {
            this.add(days.get_day(new Date(year, month, day+i)));
        }
        if (user.is_editor && options.needs_calltallies)
            this.build_calltallies();
    },
    build_calltallies: function() {
        var calltallies = this.calltallies = new CallTallies();
        _.each(this.current_persons(), function(person) {
            calltallies.add({ id: person.id, name: person.get('name') });
        });
        this.each(function(day) {
            on_call.each(function(ward) {
                var displayed = day.get_staffing(ward).displayed;
                displayed.each(function(person) {
                    calltallies.on_call_added(person, displayed);
                });
                displayed.on({
                    'add': calltallies.on_call_added,
                    'remove': calltallies.on_call_removed
                }, calltallies);
            });
        });
    },
    current_persons: function() {
        if (!this._current_persons) {
            var last = this.last().get('date');
            var that = this;
            this._current_persons = persons.filter(function(person) {
                return (person.get('end_date') >= that.first_day &&
                        person.get('start_date') <= last);
            });
        }
        return this._current_persons;
    },
});

// the 'Day's of one month.
// is used as event dispatcher for the CallTallies
var MonthDays = PeriodDays.extend({
    initialize: function(models, options) {
        // month is 0..11 like in javascript
        var year = options.year, month = options.month;
        PeriodDays.prototype.initialize.call(this, [], {
            first_day: new Date(year, month, 1),
            nr_days: utils.get_month_length(year, month),
            needs_calltallies: true,
        });
    },
    current_persons: function() {
        if (!this._current_persons) {
            var first = this.first().get('date');
            var last = this.last().get('date');
            this._current_persons = persons.filter(function(person) {
                return (person.get('end_date') >= first &&
                        person.get('start_date') <= last);
            });
        }
        return this._current_persons;
    },
});

// Returns Collection with the Days of the requested period
function get_period_days(start, length) {
    start = _.isDate(start) ? start : utils.get_date(start);
    return new PeriodDays(null, { 
        first_day: start, 
        nr_days: length,
    });
}


// Returns Collection with the Days of the current month
// This should only be called in sequence
function get_month_days(year, month) {
    // month is 0..11 like in javascript
    return new MonthDays(null, { year: year, month: month, });
}


// CallTally counts the number of call-shifts for one person
// per month
var CallTally = Backbone.Model.extend({
    add_shift: function(ward) {
        var ward_type = '_' + ward.get_ward_type();
        this.set(ward_type, (this.get(ward_type) || 0) + 1);
        this.set('weights', (this.get('weights') || 0) + ward.get('weight'));        
    },
    subtract_shift: function(ward) {
        var ward_type = '_' + ward.get_ward_type();
        this.set(ward_type, this.get(ward_type) - 1);
        this.set('weights', this.get('weights') - ward.get('weight'));        
    },
    get_tally: function(on_call_type) {
        return this.get('_' + on_call_type) || 0;
    },
});

// One CallTally per person
var CallTallies = Backbone.Collection.extend({
    model: CallTally,
    on_call_added: function(person, staffing, options) {
        var ct = this.get(person.id);
        if (ct) ct.add_shift(staffing.ward);
    },
    on_call_removed: function(person, staffing, options) {
        var ct = this.get(person.id);
        if (ct) ct.subtract_shift(staffing.ward);
    },
});


function save_change(day, ward, continued, persons) {
    // Parameters: 
    //   day: a models.Day
    //   ward: a models.Ward
    //   continued: a Boolean or a Date
    //   persons: an Array of {
    //       id: a persons id,
    //       action: 'add' or 'remove'
    //   }
    var json_data = {
        day: day.id,
        ward_id: ward.get('id'),
        continued: _.isDate(continued) ?
            utils.get_day_id(continued) :
            continued,
        persons: persons,
        last_pk: _last_change_pk,
    };
    var url = '/changes';
    do_ajax_call(url, json_data, process_changes);
}
function process_changes(data, textStatus, jqXHR) {
    if (jqXHR && jqXHR.status == 304) {
        models.schedule_next_update();
    } else {
        _.each(data.cls, models.apply_change);
        models.schedule_next_update(data.last_change);
    }
}

function save_approval(ward_ids, date) {
    // data should have these attributes: 
    //   date: a Date or false
    //   ward_ids: an Array of <ward_ids>
    var json_data = {
        date: date ? utils.get_day_id(date) : false,
        wards: ward_ids,
    };
    var url = '/set_approved';
    function success (data, textStatus, jqXHR) {
        var approved = data.approved ? utils.get_date(data.approved) : false;
        _.each(data.wards, function(ward_id) {
            wards.get(ward_id).set('approved', approved);
        });
    }
    do_ajax_call(url, json_data, success);
}

function save_function(person, ward, added) {
    var json_data = {
        person: person.get('id'),
        ward: ward.get('id'),
        add: added,
    };
    var url = '/change_function';
    function success (data, textStatus, jqXHR) {
        if (data.status=='ok') {
            persons.get(data.person).set('functions', data.functions);
        } else {
            error(jqXHR, textStatus, data.reason);
        }
    }
    do_ajax_call(url, json_data, success);
}

function redirect_to_login() {
    window.location.reload();
}

function do_ajax_call(url, json_data, success) {
    function error (jqXHR, textStatus, errorThrown) {
        if (jqXHR.status == 403)
            window.location.reload();
        models.errors.add({
            textStatus: textStatus, 
            errorThrown: errorThrown,
            responseText: jqXHR.responseText,
            url: url,
            data: json_data,
        });
    }
    $.ajax({
        type: "POST",
        url: url,
        data: JSON.stringify(json_data),
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        statusCode: { 403: redirect_to_login },
        error: error,
        success: success,
    });
}

function set_plannings(p) {
    _.each(p, function(planning) {
        planning.person = persons.findWhere({id: planning.person});
        planning.ward = wards.findWhere({id: planning.ward});
    });
    plannings = p;
}


function apply_change(change) {
    // 'change' ist der Output von sp_app.models.ChangeLogging.to_Json
    var changed_day = days.get(change.day);
    // provide enough days, so that the change can be fully applied
    if (change.until) {
        if (change.until>=days.last().id)
            days.get_day(utils.get_date(change.until), 1);
    }
    else if (change.day==days.last().id && !change.continued)
        days.get_day(utils.get_date(change.day), 1);
    if (changed_day)
        changed_day.apply_change(change);
}

var _min_update_intervall = 10;  // 10 sec
var _max_update_intervall = 120;  // 2 min
var _next_check_id;
var _last_change_pk;
function schedule_next_update(last_change) {
    var next_update_check;
    if (last_change) {
        next_update_check = Math.min(
            Math.max(last_change.time, _min_update_intervall),
            _max_update_intervall);
        _last_change_pk = last_change.pk;
    } else next_update_check = _max_update_intervall;
    window.clearTimeout(_next_check_id);
    _next_check_id = window.setTimeout(get_updates, next_update_check*1000);
}

function updates_failed() {
    models.schedule_next_update();
}

function get_updates() {
    $.ajax({
        type: "GET",
        url: '/updates/' + _last_change_pk, 
        cache: false,
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        error: updates_failed,
        success: process_changes,
    });
    current_date.update();
}

var errors = new Backbone.Collection();

function reset_data() {
    // for testing
    persons.reset(null);
    wards.reset(null);
    nightshifts.reset(null);
    on_leave.reset(null);
    days.reset();
}

return {
    Current_Date: Current_Date,
    Person: Person,
    Persons: Persons,
    persons: persons,
    Ward: Ward,
    Wards: Wards,
    wards: wards,
    nightshifts: nightshifts,
    on_leave: on_leave,
    on_call: on_call,
    on_call_types: on_call_types,
    initialize_wards: initialize_wards,
    Staffing: Staffing,
    needs_staffing: needs_staffing,
    Duties: Duties,
    Day: Day,
    days: days,
    start_day_chain: start_day_chain,
    get_period_days: get_period_days,
    get_month_days: get_month_days,
    CallTally: CallTally,
    CallTallies: CallTallies,
    save_change: save_change,
    process_changes: process_changes,
    save_approval: save_approval,
    save_function: save_function,
    set_plannings: set_plannings,
    apply_change: apply_change,
    redirect_to_login: redirect_to_login,
    errors: errors,
    reset_data: reset_data,
    user: user,
    schedule_next_update: schedule_next_update,
};
})($, _, Backbone);
