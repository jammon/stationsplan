var utils = (function($, _, Backbone) {
"use strict";

var free_dates = [
    '2015.10.3',
    '2015.11.1',
    '2015.12.24',
    '2015.12.25',
    '2015.12.26',
    '2015.12.31',
    '2016.1.1',
    '2016.3.25',
    '2016.3.28',
    '2016.5.5',
    '2016.5.16',
    '2016.5.26',
    '2016.10.3',
    '2016.11.1',
    '2016.12.26',
    '2017.4.14',
    '2017.4.17',
    '2017.5.25',
    '2017.6.5',
    '2017.6.15',
    '2017.10.3',
    '2017.11.1',
];
function is_free(date) {
    var weekday = date.getDay();
    if (weekday===6 || weekday===0) {
        return true;
    }
    var date_string = date.getFullYear()+'.'+(date.getMonth()+1)+'.'+date.getDate();
    return (free_dates.indexOf(date_string) > -1);
}

function get_day_id (date_or_year, month, day) {
    var date = (month === void 0) ? 
               date_or_year : 
               new Date(date_or_year, month, day);
    return "" + (date.getFullYear()*10000 +
                 (date.getMonth()+1)*100 +
                 date.getDate());
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

function datestr(date) {
    return date.getDate()+'.'+(date.getMonth()+1)+'.'+date.getFullYear();
}

return {
    is_free: is_free,
    get_day_id: get_day_id,
    get_previous_day_id: get_previous_day_id,
    get_next_day_id: get_next_day_id,
    get_month_id: get_month_id,
    get_next_month: get_next_month,
    get_previous_month_id: get_previous_month_id,
    get_next_month_id: get_next_month_id,
    get_year_month: get_year_month,
    get_year_month_day: get_year_month_day,
    datestr: datestr,
};
})($, _, Backbone);
