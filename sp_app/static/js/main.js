(function($, _, Backbone) {
"use strict";

// Implement the js part of csrf protection
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
var csrftoken = getCookie('csrftoken');
function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

sp.days = {};
sp.months = {};

function days_in_month (month, year) {
    var days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    return (month == 1) ? (year % 4 ? 28 : 29) : days[month];
}

function add_month_days(year, month) {
    var month_days = [], i;
    var d_i_m = days_in_month(month, year);
    for (i = 0; i < d_i_m; i++) {
        var new_day = new sp.Day({
            date: new Date(year, month, i+1),
            yesterday: sp.last_day,
        });
        month_days[i] = sp.days[new_day.id] = sp.last_day = new_day;
    }

    sp.months[sp.get_month_id(year, month)] = month_days;
    return month_days;
}

function add_month(year, month) {
    var month_days = add_month_days(year, month);

    function titlerow() {
        var tr = $('<tr/>', {'class': 'titlerow'}).append($('<th/>'));
        var month_string = '.'+(month+1)+'.';
        var i;
        var day_names = ['So.<br>', 'Mo.<br>', 'Di.<br>', 'Mi.<br>',
                         'Do.<br>', 'Fr.<br>', 'Sa.<br>'];
        _.each(month_days, function(day) {
            var date = day.get('date');
            var title = day_names[date.getDay()] + date.getDate() + '.';
            tr.append($('<th/>', { html: title }));
        });
        return tr;
    }
    // Construct rows for wards and persons
    function construct_row(model) {
        var row, collection, cell;
        row = $('<tr/>', {'class': model.row_class()});
        row.append($('<th/>', { text: model.get('name')}));
        _.each(month_days, function(day) {
            collection = day[model.collection_array][model.id];
            cell = collection ?
                (new model.row_view({collection: collection})).render().$el :
                '<td></td>';
            row.append(cell);
        });
        return row;
    }

    var table = $('table.plan');
    table.append(titlerow());
    // first the wards
    sp.wards.each(function(ward) {
        table.append(construct_row(ward));
    });
    // then the persons
    sp.persons.each(function(person) {
        table.append(construct_row(person));
    });
    $('#loading-message').toggle(false);
}

sp.initialize_site = function (persons_init, wards_init, past_changes, changes,
                    curr_year, curr_month, can_change) {

    sp.initialize_wards(wards_init);
    sp.persons.reset(persons_init);
    add_month(curr_year, curr_month-1);
    _.each(past_changes, sp.apply_change);
    _.each(changes, sp.apply_change);

};

})($, _, Backbone);

