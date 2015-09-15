"use strict";
var sp = sp || {};

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
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
    var content = $("#main-content");

    var month_names = ['Januar', 'Februar', 'März', 'April', 'Mai',
        'Juni', 'Juli', 'August', 'September', 'Oktober',
        'November', 'Dezember'];
    content.append($('<h2/>', { text: month_names[month]+' '+year }));

    var table = $('<table/>', {border: 1});

    // Construct title row
    var titlerow = $('<tr/>', {'class': 'titlerow'}).append($('<th/>'));
    var d_i_m = days_in_month(month, year);
    var month_string = '.'+(month+1)+'.';
    var i;
    var day_names = ['So.<br>', 'Mo.<br>', 'Di.<br>', 'Mi.<br>',
                     'Do.<br>', 'Fr.<br>', 'Sa.<br>'];
    _.each(month_days, function(day) {
        var date = day.get('date');
        var title = day_names[date.getDay()] + date.getDate() + '.';
        titlerow.append($('<th/>', { html: title }));
    });
    table.append(titlerow);

    // Construct rows for wards and persons
    // first the wards
    var View = sp.StaffingView;
    var collection_array = 'ward_staffings';
    var row_class = 'wardrow';
    function construct_row(model) {
        var row, collection, cell;
        row = $('<tr/>', {'class': row_class});
        row.append($('<th/>', { text: model.get('name')}));
        _.each(month_days, function(day) {
            collection = day[collection_array][model.id];
            cell = collection ?
                (new View({collection: collection})).render().$el :
                '<td></td>';
            row.append(cell);
        });
        table.append(row);
    }
    sp.wards.each(function(ward) {
        construct_row(ward);
    });

    // then the persons
    View = sp.DutiesView;
    collection_array = 'persons_duties';
    row_class = 'personrow';
    var first_of_month = year*10000 + (month+1)*100 + 1;
    sp.persons.each(function(person) {
        var start = person.get('start_date');
        if (start && parseInt(start, 10)>first_of_month+31)
            return;
        var end = person.get('end_date');
        if (end && parseInt(end, 10)<first_of_month)
            return;
        construct_row(person);
    });

    content.append(table);
}
