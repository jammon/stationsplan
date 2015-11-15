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
//     - name
//     - id    = short form of the name
//     - start_date = begin of job
//     - end_date = end of job
sp.Person = Backbone.Model.extend({
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

sp.Persons = Backbone.Collection.extend({
    model: sp.Person,
    comparator: function(person) {
        return person.get('position') + person.get('name');
    },
});
sp.persons = new sp.Persons();

// A ward can be a usual ward, a task or a shift.
// It has a 
//     - name
//     - shortname = short form of the name
//     - max = maximum staffing
//     - min = minimum staffing
//     - nightshift = if truthy, staffing can not be planned on the next day.
//     - everyday = if truthy, is to be planned also on free days.
//     - freedays = if truthy, is to be planned only on free days.
//     - continued = if truthy, then todays staffing will be planned for tomorrow
//     - on_leave = if truthy, then persons planned for this are on leave
//     - approved = The date until which the plan is approved
sp.Ward = Backbone.Model.extend({
    initialize: function() {
        var start = this.get('approved') || [2015, 0, 1];
        this.set('approved', new Date(start[0], start[1], start[2]));
    },
    idAttribute: "shortname",
    collection_array: 'ward_staffings',
    row_class: function() {
        if (this.get('nightshift')) return 'nightshiftrow';
        if (this.get('freedays')) return 'freedaysrow';
        if (this.get('on_leave')) return 'leaverow';
        return 'wardrow';
    },
});


sp.Wards = Backbone.Collection.extend({
    model: sp.Ward,
    comparator: function(ward) {
        var res = (ward.get('on_leave') ? '1' : '0') +  // on_leave last
            (ward.get('continued') ? '0' : '1') +  // normal wards first
            ward.get('position') +
            ward.get('name');
        return res;
    },
});
sp.wards = new sp.Wards();
sp.nightshifts = new Backbone.Collection();
sp.on_leave = new Backbone.Collection();

sp.initialize_wards = function (wards_init) {
    sp.wards.reset(wards_init);
    sp.nightshifts.reset(sp.wards.where({'nightshift': true}));
    sp.on_leave.reset(sp.wards.where({'on_leave': true}));
};


// A staffing are the persons working on a ward on one day.
// It has
//     - ward
//     - day
sp.Staffing = Backbone.Collection.extend({
    model: sp.Person,
    initialize: function(models, options) {
        var day = this.day = options.day;
        this.ward = options.ward;
        this.on('add', day.person_added, day);
        this.on('remove', day.person_removed, day);
        this.comparator = 'name';
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
        if (person.get('end_date')<this.day.get('date')) return;
        if (person.get('start_date')>this.day.get('date')) return;
        if (!staffing.ward.get('on_leave') && this.day.is_on_leave(person))
            return;
        if (this.day.yesterdays_nightshift(person)) {
            // don't add/remove, but continue the chain
            this.trigger(action, person, staffing, options);
        } else {
            this[action](person);
        }
    },
    lacking: function() {
        return this.length<this.ward.get('min');
    },
    room_for_more: function() {
        return this.length<this.ward.get('max');
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

        this.ward_staffings = {};  // a staffing for each ward
                                   // can be undefined if this day is free
        sp.wards.each(this.get_staffing, this);

        this.persons_duties = {};    // duties for each person
        sp.persons.each(function(person) {
            var duties = new sp.Duties();
            sp.wards.each(function(ward) {
                var staffing = that.ward_staffings[ward.id];
                if (staffing && staffing.get(person)) {
                    duties.add(ward);
                }
            });
            that.persons_duties[person.id] = duties;
        });

        if (yesterday) {
            yesterday.on('nightshift:added', this.last_nightshift_added, this);
            yesterday.on('nightshift:removed', this.last_nightshift_removed, this);
        }
    },
    get_staffing: function(ward) {
        var staffing, yesterdays_staffing;
        var date = this.get('date');
        var options = { ward: ward, day: this };
        if (this.needs_staffing(ward)) {
            staffing = new sp.Staffing([], options);
            if (ward.get('continued')) {
                yesterdays_staffing = this.yesterdays_staffing(ward);
                if (yesterdays_staffing) {
                    staffing.reset(yesterdays_staffing.filter(function(person) {
                        var leaving = person.get('end_date');
                        return leaving >= date;
                    }));
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

    get_available: function(ward) {
        var unavailable = {};
        var available;
        var yesterday = this.get('yesterday');
        var that = this;

        function get_unavailables (staffing) {
            staffing.each(function(person) { unavailable[person.id] = true; });
        }
        // yesterdays nightshift
        if (yesterday) {
            sp.nightshifts.each(function(ward) {
                get_unavailables(yesterday.ward_staffings[ward.id]);
            });
        }
        // persons on leave
        sp.on_leave.each(function(ward) {
            get_unavailables(this.ward_staffings[ward.id]);
        }, this);
        // persons planned for this ward
        get_unavailables(this.ward_staffings[ward.id]);

        available = sp.persons.filter(function(person) {
            return !unavailable[person.id] &&
                person.is_available(that.get('date')) &&
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
        while (yesterday && !yesterday.needs_staffing(ward)) {
            yesterday = yesterday.get('yesterday');
        }
        return yesterday ? yesterday.ward_staffings[ward.id] : undefined;
    },
    needs_staffing: function(ward) {
        if (ward.get('everyday') || ward.get('on_leave')) {
            return true;
        }
        return is_free(this.get('date')) == (ward.get('freedays') || false);
    },

    person_added: function(person, staffing, options) {
        this.persons_duties[person.id].add(staffing.ward);
        if (staffing.ward.get('nightshift')) {
            this.trigger('nightshift:added', person, staffing.ward);
        }
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
sp.padStr = function (i) {
    return (i < 10) ? "0" + i : i;
}
sp.Day.get_id = function(date) {
    return "" + date.getFullYear() +
                sp.padStr(1 + date.getMonth()) +
                sp.padStr(date.getDate());
};
sp.get_month_id = function(year, month) {
    return "" + year + sp.padStr(1 + month);
};

sp.change_and_store = function(person_id, staffing, action) {
    var person = sp.persons.get(person_id);
    staffing[action](person);
    $.ajax('/change', {
        data: {
            person: person_id,
            ward: staffing.ward.get('shortname'),
            day: staffing.day.id,
            action: action,
        },
        method: 'POST',
        error: function(jqXHR, textStatus, errorThrown) {
            sp.store_error(textStatus, 'error');
        },
        success: function(data, textStatus, jqXHR) {
            if (data.warning) {
                sp.store_error(data.warning, 'warning');
            }
        },
    });
};

sp.apply_change = function(change) {
    var person = sp.persons.get(change.person);
    var day = sp.days[change.day];
    var staffing;
    if (day && person) {
        staffing = day.ward_staffings[change.ward];
        if (staffing) {
            staffing[change.action](person);
            return;
        }
    }
    // Something went wrong
    // TODO: This can happen when the first of month is a weekend day
    console.log(change);
};

sp.store_error = function(error, type) {
    $('#log').append($('<p/>', { text: error, 'class': type }));
};

sp.display_error = function(msg) {
    $('#errors').append($('<div/>', { html: msg }));
};
