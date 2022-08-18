let main = (function ($, _, Backbone) {
    "use strict";

    function setupCsrfProtection() {
        // Implement the js part of csrf protection
        function getCookie(name) {
            if (document.cookie && document.cookie !== '') {
                for (const raw_cookie of document.cookie.split(';')) {
                    const cookie = raw_cookie.trim();
                    // Does this cookie string begin with the name we want?
                    if (cookie.startsWith(name + '=')) {
                        return decodeURIComponent(cookie.substring(name.length + 1));
                    }
                }
            }
            return null;
        }
        const csrftoken = getCookie('csrftoken');
        function csrfSafeMethod(method) {
            // these HTTP methods do not require CSRF protection
            return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
        }
        $.ajaxSetup({
            beforeSend: function (xhr, settings) {
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
