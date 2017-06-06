var utils = (function($, _, Backbone) {
"use strict";

var _holidays = {};
var _free_dates = [];

function is_free(date) {
    var weekday = date.getDay();
    if (weekday===6 || weekday===0) {
        return true;
    }
    return (_free_dates.indexOf(get_day_id(date)) > -1);
}

function set_holidays(holidays) {
    // holidays should be in the form of
    // {'YYYYMMDD': 'Name of the holiday', ...}
    _holidays = holidays;
    _free_dates = _.keys(holidays);
}
var month_names = ["Januar", "Februar", "März", "April", "Mai", "Juni", 
    "Juli", "August", "September", "Oktober", "November", "Dezember"];
var day_names = ['So.', 'Mo.', 'Di.', 'Mi.', 'Do.', 'Fr.', 'Sa.'];
var day_long_names = ['Sonntag', 'Montag', 'Dienstag', 'Mittwoch',
    'Donnerstag', 'Freitag', 'Samstag'];


function get_day_id (date_or_year, month, day) {
    var date = (month === void 0) ? 
               date_or_year : 
               new Date(date_or_year, month, day);
    return "" + (date.getFullYear()*10000 +
                 (date.getMonth()+1)*100 +
                 date.getDate());
}
function get_date(day_id) {
    return new Date(
        parseInt(day_id.slice(0, 4)),
        parseInt(day_id.slice(4, 6)) - 1,
        parseInt(day_id.slice(6, 8)));
}
function get_previous_day_id(day_id) {
    var date = new Date(
        parseInt(day_id.slice(0, 4)),
        parseInt(day_id.slice(4, 6)) - 1,
        parseInt(day_id.slice(6, 8)) - 1);
    return get_day_id(date);
}
function get_next_day_id(day_id) {
    var date = new Date(
        parseInt(day_id.slice(0, 4)),
        parseInt(day_id.slice(4, 6)) - 1,
        parseInt(day_id.slice(6, 8)) + 1);
    return get_day_id(date);
}

function get_month_id (year, month) {
    return "" + (year*100 + (month+1));
}

function get_previous_month (year, month) {
    return (month > 0) ?
        { month: month-1, year: year } : 
        { month: 11,      year: year-1 };
}
function get_previous_month_id(month_id) {
    var m = get_year_month(month_id);
    m = get_previous_month(m.year, m.month);
    return get_month_id(m.year, m.month);
}

function get_next_month (year, month) {
    return (month < 11) ?
        { month: month+1, year: year } : 
        { month: 0,       year: year+1 };
}
function get_next_month_id(month_id) {
    var m = get_year_month(month_id);
    m = get_next_month(m.year, m.month);
    return get_month_id(m.year, m.month);
}

function get_year_month (month_id) {
    return {
        year: parseInt(month_id.slice(0, 4), 10),
        month: parseInt(month_id.slice(4, 6), 10) - 1,
    };
}

function get_year_month_day (day_id) {
    return {
        year: parseInt(day_id.slice(0, 4), 10),
        month: parseInt(day_id.slice(4, 6), 10) - 1,
        day: parseInt(day_id.slice(6, 8), 10),
    };
}

function get_month_length(year, month) {
    var lengths = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    var result = lengths[month % 12];
    var real_year = year + Math.floor(month / 12);
    if (result == 28 && real_year % 4 === 0) return 29;
    else return result;
}

function datestr(date) {
    return date.getDate()+'.'+(date.getMonth()+1)+'.'+date.getFullYear();
}

return {
    is_free: is_free,
    set_holidays: set_holidays,
    month_names: month_names,
    day_names: day_names,
    day_long_names: day_long_names,    
    get_day_id: get_day_id,
    get_date: get_date,
    get_previous_day_id: get_previous_day_id,
    get_next_day_id: get_next_day_id,
    get_month_id: get_month_id,
    get_next_month: get_next_month,
    get_previous_month_id: get_previous_month_id,
    get_next_month_id: get_next_month_id,
    get_year_month: get_year_month,
    get_year_month_day: get_year_month_day,
    get_month_length: get_month_length,
    datestr: datestr,
};
})($, _, Backbone);
