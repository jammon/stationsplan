var main = (function($, _, Backbone) {
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


function titlerow(collection, get_content) {
    var tr = $('<tr/>', {'class': 'titlerow'}).append($('<th/>'));
    function get_cell(model) {
        tr.append($('<th/>', {'html': get_content(model)}));
    }
    if (collection.each) {collection.each(get_cell); } 
    else {_.each(collection, get_cell); }
    return tr;
}



function get_staffing_view (ward, day) {
    var collection = day.ward_staffings[ward.id];
    return collection && (new views.StaffingView({
        collection: collection,
        display_long_name: true,
    }));
}

function display_month_vertical(year, month) {
    $('#loading-message').toggle(true);

    var month_string = '.'+(month+1)+'.';
    var day_names = ['So. ', 'Mo. ', 'Di. ', 'Mi. ',
                     'Do. ', 'Fr. ', 'Sa. '];

    var table = $('table.plan').empty();
    table.addClass('vertical');
    table.append(titlerow(models.wards, function(ward) {
        return ward.get('name');
    }));

    _.each(month_days, function(day) {
        var date = day.get('date');
        var title = day_names[date.getDay()] + date.getDate() + month_string;
        var row = $('<tr/>', {'class': models.is_free(date) ? 'free-day' : ''});
        row.append($('<th/>', { html: title }));
        models.wards.each(function(ward) {
            var view = get_staffing_view(ward, day);
            row.append(view ? view.render().$el : '<td></td>');
        });
        table.append(row);
    });
    $('#loading-message').toggle(false);
}


function initialize_site(persons_init, wards_init, past_changes, changes,
                    curr_year, curr_month, can_change, ward_selection) {

    models.initialize_wards(wards_init);
    models.persons.reset(persons_init);
    models.set_changes(past_changes.concat(changes));
    var month_view;
    for (var i = 0; i < 3; i++) {
        if (curr_month == 12) {
            curr_year++;
            curr_month = 0;
        }
        month_view = new views.MonthView({
            year: curr_year,
            month: curr_month,
            prev_month_view: month_view,
        });
        $(".plans").append(month_view.render().move_to(i ? 'future' : 'present').$el);
        curr_month += 1;
    }
    // if (ward_selection=='noncontinued') {
    //     display_month_vertical(curr_year, curr_month);
    // } else {
    //     display_month(curr_year, curr_month);
    // }
}

return {
    initialize_site: initialize_site,
};
})($, _, Backbone);
