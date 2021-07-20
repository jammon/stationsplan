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
from django.views.generic import TemplateView
from sp_app import views as sp_views
from sp_app import ajax as sp_ajax
from sp_app.admin import config_site

urlpatterns = [
    path('', sp_views.home, name='home'),
    # SPA
    re_path('plan/(?P<month>[0-9]+)?/?$', sp_views.plan, name='plan'),
    re_path(r'^dienste(/(?P<month>[0-9]+))?/?$', sp_views.plan, name='dienste'),
    re_path(r'^tag(/(?P<day>[0-9]+))?/?$', sp_views.plan, name='tag'),
    path('zuordnung', sp_views.plan, name='functions'),
    # Ajax
    path('change_function', sp_ajax.change_function,
         name='change_function'),
    path('changes', sp_ajax.changes, name='changes'),
    re_path(r'^changehistory/(?P<date>[0-9]+)/(?P<ward_id>[0-9]+)$',
            sp_ajax.change_history, name='changehistory'),
    path('set_approved', sp_ajax.change_approved, name='set_approved'),
    re_path(r'^updates/([0-9]+)/?$', sp_ajax.updates, name='updates'),
    # Administrators
    path('personen', sp_views.personen_funktionen, name='persons'),
    path('person/add/', sp_views.PersonCreateView.as_view(), name='person-add'),
    path('person/<int:pk>/', sp_views.PersonUpdateView.as_view(), name='person-update'),
    path('funktionen', sp_views.FunktionenView.as_view(), name='wards'),
    path('funktion/add/', sp_views.WardCreateView.as_view(), name='ward-add'),
    path('funktion/<int:pk>/', sp_views.WardUpdateView.as_view(), name='ward-update'),
    path('different_day/<str:action>/<int:ward>/<str:day_id>',
         sp_ajax.differentday, name='different-day'),
    # Other
    path('tests', TemplateView.as_view(template_name="sp_app/tests.html"),
         name='tests'),
    path('password_change',
         auth_views.PasswordChangeView.as_view(
             template_name='registration/password_change.html',
             success_url='/plan'),
         name='password_change'),
    path('admin/', admin.site.urls),
    path('config/', config_site.urls),
    path('login', auth_views.LoginView.as_view(), name='login'),
    path('logout', auth_views.LogoutView.as_view(next_page='/'),
         name='logout'),
    path('robots.txt',
         TemplateView.as_view(
             template_name="robots.txt", content_type="text/plain")),
    path('/', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
