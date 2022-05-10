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


function initialize_site(data) {
    setupCsrfProtection();
    _.extend(
        models.user, 
        _.pick(data, "is_editor", "is_dep_lead", "is_company_admin", "departments"));
    // just choose one department
    models.user.current_department = parseInt(_.keys(data.departments)[0]);
    models.initialize_wards(data.wards, data.different_days);
    models.persons.reset(data.persons);
    models.set_plannings(data.plannings); 
    utils.set_holidays(data.holidays);
    models.start_day_chain(data.data_year, data.data_month);
    models.schedule_next_update({
        pk: data.last_change_pk, 
        time: data.last_change_time
    });
    Backbone.history.start({ pushState: true });
}


return {
    initialize_site: initialize_site,
};
})($, _, Backbone);
