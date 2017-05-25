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
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from sp_app import views as sp_views
from sp_app import ajax as sp_ajax
from sp_app.admin import config_site

urlpatterns = [
    url(r'^$', sp_views.home, name='home'),
    url(r'^plan(/(?P<month>[0-9]+))?/?$', sp_views.plan, name='plan'),
    url(r'^dienste(/(?P<month>[0-9]+))?/?$', sp_views.plan, name='dienste'),
    url(r'^tag(/(?P<day>[0-9]+))?/?$', sp_views.plan, name='tag'),
    url(r'^changes$', sp_ajax.changes, name='changes'),
    url(r'^set_approved$', sp_ajax.change_approved, name='set_approved'),
    url(r'^tests$', TemplateView.as_view(template_name="sp_app/tests.html"),
        name='tests'),
    url(r'^password_change', sp_views.password_change, name='password_change'),
    url(r'^admin/', admin.site.urls),
    url(r'^config/', config_site.urls),
    url(r'^login$', auth_views.login, name='login'),
    url('^logout/', auth_views.logout, {'next_page': '/'}, name='logout'),
    url('^', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
