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
                         can_change, ward_selection) {
    setupCsrfProtection();
    models.initialize_wards(wards);
    models.persons.reset(persons);
    models.set_plannings(plannings);
    var month_view = new views.MonthView({
            year: year,
            month: month,
        });
    $(".plans").append(month_view.render().move_to('present').$el);
}

return {
    initialize_site: initialize_site,
};
})($, _, Backbone);
