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

    function heading() {
        var month_names = ['Januar', 'Februar', 'März', 'April', 'Mai',
            'Juni', 'Juli', 'August', 'September', 'Oktober',
            'November', 'Dezember'];
        return $('<h2/>', { text: month_names[month]+' '+year })
    }

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

    var content = $("#main-content");
    var table = $('<table/>', {border: 1, 'class': 'plan'});
    var inner = $('<div/>', {'class': 'inner'});

    content.append(heading());
    table.append(titlerow());

    // first the wards
    sp.wards.each(function(ward) {
        table.append(construct_row(ward));
    });

    // then the persons
    var first_of_month = new Date(year, month, 1);
    var last_of_month = new Date(year, month, days_in_month(month, year));
    sp.persons.each(function(person) {
        if (person.is_available(first_of_month) ||
            person.is_available(last_of_month)) {
            table.append(construct_row(person));
        }
    });

    inner.append(table);
    content.append(inner);
}

sp.initialize_site = function (persons_init, wards_init, past_changes, changes,
                    curr_year, curr_month, can_change) {
    var next_month_btn = $('#next_month');
    var next_year, next_month;

    sp.initialize_wards(wards_init);
    sp.persons.reset(persons_init);
    add_month(curr_year, curr_month-1);
    _.each(past_changes, sp.apply_change);
    _.each(changes, sp.apply_change);

    if (curr_month==12) {
      next_year = curr_year+1;
      next_month = 0;
    } else {
      next_year = curr_year;
      next_month = curr_month;
    }
    next_month_btn.on('click', function () {
      add_month(next_year, next_month);
      // TODO: read changes!!
      $.ajax('/month', {
          data: {
              month: next_month+1,
              year: next_year,
          },
          method: 'GET',
          error: function(jqXHR, textStatus, errorThrown) {
              sp.store_error(textStatus, 'error');
              // sp.display_error(jqXHR.responseText);
          },
          success: function(data, textStatus, jqXHR) {
              if (data.warning) {
                  sp.store_error(data.warning, 'warning');
              } else {
                _.each(data, sp.apply_change);
              }
          },
      });
      next_month += 1;
      if (next_month==12) {
        next_year += 1;
        next_month = 0;
      }
    });
};

})($, _, Backbone);

