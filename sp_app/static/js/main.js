var main = (function($, _, Backbone) {
"use strict";

function setupCsrfProtection() {
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
}


function initialize_site(persons, wards, different_days, plannings,
                         year, month, start_of_data, is_editor, holidays, 
                         department_ids, last_change_pk, last_change_time) {
    setupCsrfProtection();
    models.user.is_editor = is_editor;
    models.initialize_wards(wards, different_days);
    models.persons.reset(persons);
    models.persons.each(function(person) {
        person.set(
            'own_department',
            _.intersection(
                person.get('departments'),
                department_ids
            ).length>0
        ); 
    });
    models.set_plannings(plannings); 
    utils.set_holidays(holidays);
    models.start_day_chain(start_of_data.getFullYear(),
        start_of_data.getMonth());
    models.schedule_next_update({
        pk: last_change_pk, 
        time: last_change_time
    });
    Backbone.history.start({ pushState: true });
}


return {
    initialize_site: initialize_site,
};
})($, _, Backbone);
