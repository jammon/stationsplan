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
];
function is_free(date) {
    var weekday = date.getDay();
    if (weekday===6 || weekday===0) {
        return true;
    }
    var date_string = date.getFullYear()+'.'+(date.getMonth()+1)+'.'+date.getDate();
    return (free_dates.indexOf(date_string) > -1);
}

function get_next_month (year, month) {
    return (month < 11) ?
        { month: month+1, year: year } : 
        { month: 0,       year: year+1 };
}

function get_day_id (date_or_year, month, day) {
    var date = (month === void 0) ? date_or_year :
                                     new Date(date_or_year, month, day);
    return "" + (date.getFullYear()*10000 +
                 (date.getMonth()+1)*100 +
                 date.getDate());
}

function get_month_id (year, month) {
    return "" + (year*100 + (month+1));
}
function get_previous_month_id(month_id) {
    var m = get_year_month(month_id);
    if (m.month===0) {
        return get_month_id(m.year-1, 11);
    } else {
        return get_month_id(m.year, m.month-1);
    }
}
function get_next_month_id(month_id) {
    var m = get_year_month(month_id);
    if (m.month===11) {
        return get_month_id(m.year+1, 0);
    } else {
        return get_month_id(m.year, m.month+1);
    }
}

function get_year_month (month_id) {
    return {
        year: parseInt(month_id.slice(0, 4), 10),
        month: parseInt(month_id.slice(4, 6), 10) - 1,
    };
}

function datestr(date) {
    return date.getDate()+'.'+(date.getMonth()+1)+'.'+date.getFullYear();
}

return {
    is_free: is_free,
    get_next_month: get_next_month,
    get_day_id: get_day_id,
    get_month_id: get_month_id,
    get_previous_month_id: get_previous_month_id,
    get_next_month_id: get_next_month_id,
    get_year_month: get_year_month,
    datestr: datestr,
};
})($, _, Backbone);