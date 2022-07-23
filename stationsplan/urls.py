"""stationsplan URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf import settings
from django.urls import include, re_path, path
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import user_passes_test
from django.views.generic import TemplateView
from sp_app import views as sp_views
from sp_app import ajax as sp_ajax
from sp_app import ical_views
from sp_app.admin import config_site


def path2template(url, t_path, name, **kwargs):
    return path(
        url, TemplateView.as_view(template_name=t_path, **kwargs), name=name
    )


urlpatterns = [
    path("", sp_views.home, name="home"),
    path("setup/", sp_views.setup, name="setup"),
    #
    #
    # SPA  -------------------------------------------------------------
    #
    re_path("plan/(?P<month>[0-9]+)?/?$", sp_views.plan, name="plan"),
    re_path(
        r"^dienste(/(?P<month>[0-9]+))?/?$", sp_views.plan, name="dienste"
    ),
    re_path(r"^tag(/(?P<day>[0-9]+))?/?$", sp_views.plan, name="tag"),
    path("zuordnung", sp_views.plan, name="functions"),
    #
    #
    # Ajax -------------------------------------------------------------
    #
    path("change_function", sp_ajax.change_function, name="change_function"),
    path("changes", sp_ajax.changes, name="changes"),
    re_path(
        r"^changehistory/(?P<date>[0-9]+)/(?P<ward_id>[0-9]+)$",
        sp_ajax.change_history,
        name="changehistory",
    ),
    path("set_approved", sp_ajax.change_approved, name="set_approved"),
    re_path(r"^updates/([0-9]+)/?$", sp_ajax.updates, name="updates"),
    path(
        "different_day/<str:action>/<int:ward>/<str:day_id>",
        sp_ajax.differentday,
        name="different-day",
    ),
    path("edit/department", sp_ajax.edit_department, name="department-add"),
    path(
        "edit/department/<int:department_id>",
        sp_ajax.edit_department,
        name="department-update",
    ),
    path("edit/employee", sp_ajax.edit_employee, name="employee-add"),
    path(
        "edit/employee/<int:employee_id>",
        sp_ajax.edit_employee,
        name="employee-update",
    ),
    #
    #
    # iCal -------------------------------------------------------------
    #
    path("feed/<str:feed_id>", ical_views.DienstFeed(), name="icalfeed"),
    #
    #
    # Administrators -----------------------------------------------------
    #
    path("person/add/", sp_ajax.edit_person, name="person-add"),
    path("person/<int:pk>/", sp_ajax.edit_person, name="person-update"),
    path("funktion/add/", sp_ajax.edit_ward, name="ward-add"),
    path("funktion/<int:pk>/", sp_ajax.edit_ward, name="ward-update"),
    path("ical_feeds", sp_views.ical_feeds, name="ical_feeds"),
    path(
        "send_ical_feed/<int:pk>",
        sp_ajax.send_ical_feed,
        name="send_ical_feed",
    ),
    #
    #
    # Auth -------------------------------------------------------------
    #
    path(
        "password_change",
        auth_views.PasswordChangeView.as_view(
            template_name="registration/password_change.html",
            success_url="/plan",
        ),
        name="password_change",
    ),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path(
        "logout", auth_views.LogoutView.as_view(next_page="/"), name="logout"
    ),
    path("/", include("django.contrib.auth.urls")),
    #
    path2template("offer", "sp_app/signup/offer.jinja", "offer"),
    path("signup", sp_views.signup, name="signup"),
    path(
        "signup/success",
        TemplateView.as_view(
            template_name="sp_app/signup/activation_mail_sent.html"
        ),
        name="signup-success",
    ),
    path(
        "send_activation_mail/<int:user>",
        sp_views.send_activation_mail,
        name="send_activation_mail",
    ),
    path("activate/<int:uid>/<token>", sp_views.activate, name="activate"),
    path(
        "activate/success",
        TemplateView.as_view(
            template_name="sp_app/signup/activation_success.html"
        ),
        name="activation_success",
    ),
    #
    # Other -------------------------------------------------------------
    #
    path(
        "tests",
        user_passes_test(lambda user: user.is_superuser)(
            TemplateView.as_view(template_name="sp_app/tests.html")
        ),
        name="tests",
    ),
    path("delete_playwright_tests", sp_views.delete_playwright_tests),
    path2template("datenschutz", "datenschutz.html", "datenschutz"),
    path2template("impressum", "impressum.html", "impressum"),
    path2template(
        "robots.txt",
        "robots.txt",
        name="robots.txt",
        content_type="text/plain",
    ),
    path("admin/", admin.site.urls),
    path("config/", config_site.urls),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
        path(
            "test/activation_mail_sent/<int:user>",
            sp_views.send_activation_mail,
            {"send": False},
        ),
    ]
