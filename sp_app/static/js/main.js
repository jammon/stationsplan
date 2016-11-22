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


function initialize_site(persons, wards, plannings, year, month,
                         start_of_data, can_change, ward_selection) {
    setupCsrfProtection();
    models.initialize_wards(wards);
    models.persons.reset(persons);
    models.set_plannings(plannings); 
    models.start_day_chain(start_of_data.getFullYear(),
        start_of_data.getMonth());
    models.user_can_change = can_change;
    if (models.user_can_change) {
        // .plan should work as background for staff to throw out
        $(".plans").droppable({
            drop: function(event, ui) {
                views.remove_person_from_helper(ui.helper);
            }
        });
    }
    Backbone.history.start({ pushState: true });
}


return {
    initialize_site: initialize_site,
};
})($, _, Backbone);
