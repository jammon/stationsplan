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
    url(r'^zuordnung/?$', sp_views.plan, name='functions'),
    url(r'^change_function/?$', sp_ajax.change_function, name='change_function'),
    url(r'^changes$', sp_ajax.changes, name='changes'),
    url(r'^changehistory/(?P<date>[0-9]+)/(?P<ward_id>[0-9]+)$',
        sp_ajax.change_history, name='changehistory'),
    url(r'^set_approved$', sp_ajax.change_approved, name='set_approved'),
    url(r'^updates/([0-9]+)/?$', sp_ajax.updates, name='updates'),
    url(r'^tests$', TemplateView.as_view(template_name="sp_app/tests.html"),
        name='tests'),
    url(r'^password_change',
        auth_views.PasswordChangeView.as_view(
            template_name='registration/password_change.html',
            success_url='/plan'),
        name='password_change'),
    url(r'^admin/', admin.site.urls),
    url(r'^config/', config_site.urls),
    url(r'^login$', auth_views.LoginView.as_view(), name='login'),
    url('^logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    url('^', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url('__debug__/', include(debug_toolbar.urls)),
    ]
