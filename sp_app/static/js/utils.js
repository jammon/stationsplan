// jshint esversion: 6
var utils = (function ($, _, Backbone) {
    "use strict";

    var _holidays = [];
    var _free_dates = {};
    var _calculated_years = {};
    var _easters = {
        2014: new Date(2014, 3, 20),
        2015: new Date(2015, 3, 5),
        2016: new Date(2016, 2, 27),
        2017: new Date(2017, 3, 16),
        2018: new Date(2018, 3, 1),
        2019: new Date(2019, 3, 21),
        2020: new Date(2020, 3, 12),
        2021: new Date(2021, 3, 4),
        2022: new Date(2022, 3, 17),
        2023: new Date(2023, 3, 9),
        2024: new Date(2024, 2, 31),
        2025: new Date(2025, 3, 20),
        2026: new Date(2026, 3, 5),
        2027: new Date(2027, 2, 28),
        2028: new Date(2028, 3, 16),
        2029: new Date(2029, 3, 1),
    };

    function is_free(date) {
        // date is a Javascript Date
        // returns a boolean or the name of the holiday
        var weekday = date.getDay();
        if (weekday === 6 || weekday === 0) {
            return true;
        }
        if (!_calculated_years[date.getFullYear()])
            calc_holidays(date.getFullYear());
        return _free_dates[get_day_id(date)] || false;
    }

    function calc_holidays(year) {
        _holidays.forEach(function (holiday) {
            let day_id;
            if (holiday.mode == 'abs') {
                if (holiday.year && holiday.year != year)
                    return;
                day_id = get_day_id(year, holiday.month - 1, holiday.day);
            } else {
                let easter = _easters[year];
                day_id = get_day_id(new Date(
                    year, easter.getMonth(), easter.getDate() + holiday.day));
            }
            _free_dates[day_id] = holiday.name;
        });
        _calculated_years[year] = true;
    }

    function set_holidays(holidays) {
        // holidays is a list of models.CalculatedHoliday.toJson
        _holidays = holidays;
        _free_dates = {};
        _calculated_years = {};
    }
    var month_names = ["Januar", "Februar", "März", "April", "Mai", "Juni",
        "Juli", "August", "September", "Oktober", "November", "Dezember"];
    var day_names = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'];
    var day_long_names = ['Sonntag', 'Montag', 'Dienstag', 'Mittwoch',
        'Donnerstag', 'Freitag', 'Samstag'];


    function get_day_id(date_or_year, month, day) {
        var date = (month === void 0) ?
            date_or_year :
            new Date(date_or_year, month, day);
        return "" + (date.getFullYear() * 10000 +
            (date.getMonth() + 1) * 100 +
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
    function get_last_monday(day) {
        return new Date(
            day.getFullYear(),
            day.getMonth(),
            day.getDate() - (day.getDay() + 6) % 7);
    }
    function get_last_monday_id(day_id) {
        return get_day_id(get_last_monday(get_date(day_id)));
    }

    function get_month_id(year, month) {
        return "" + (year * 100 + (month + 1));
    }

    function get_previous_month(year, month) {
        return (month > 0) ?
            { month: month - 1, year: year } :
            { month: 11, year: year - 1 };
    }
    function get_previous_month_id(month_id) {
        var m = get_year_month(month_id);
        m = get_previous_month(m.year, m.month);
        return get_month_id(m.year, m.month);
    }

    function get_next_month(year, month) {
        return (month < 11) ?
            { month: month + 1, year: year } :
            { month: 0, year: year + 1 };
    }
    function get_next_month_id(month_id) {
        var m = get_year_month(month_id);
        m = get_next_month(m.year, m.month);
        return get_month_id(m.year, m.month);
    }

    function get_year_month(month_id) {
        return {
            year: parseInt(month_id.slice(0, 4), 10),
            month: parseInt(month_id.slice(4, 6), 10) - 1,
        };
    }

    function get_year_month_day(day_id) {
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
        return date.getDate() + '.' + (date.getMonth() + 1) + '.' + date.getFullYear();
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
        get_last_monday: get_last_monday,
        get_last_monday_id: get_last_monday_id,
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
