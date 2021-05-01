from unittest import TestCase
from django.urls import resolve
from django.views.generic import TemplateView

from sp_app import views as sp_views
from sp_app import ajax as sp_ajax


class TestUrls(TestCase):
    def test_resolution_for_views(self):
        for url, func, args, kwargs in (
                ('/', sp_views.home, (), {}),
                ('/plan/', sp_views.plan, (), {}),
                ('/plan/202104/', sp_views.plan, (), {'month': '202104'}),
                ('/dienste/', sp_views.plan, (), {}),
                ('/dienste/202104/', sp_views.plan, (), {'month': '202104'}),
                ('/tag/', sp_views.plan, (), {}),
                ('/tag/20210426/', sp_views.plan, (), {'day': '20210426'}),
                ('/zuordnung/', sp_views.plan, (), {}),
                ('/change_function', sp_ajax.change_function, (), {}),
                ('/changes', sp_ajax.changes, (), {}),
                ('/changehistory/20210426/17', sp_ajax.change_history, (),
                    {'date': '20210426', 'ward_id': '17'}),
                ('/set_approved', sp_ajax.change_approved, (), {}),
                ('/updates/32145/', sp_ajax.updates, ('32145',), {}),
        ):
            resolver = resolve(url)
            self.assertEqual(resolver.func, func, msg=f'{url} - func')
            self.assertEqual(resolver.args, args, msg=f'{url} - args')
            self.assertEqual(resolver.kwargs, kwargs, msg=f'{url} - kwargs')

    def test_resolution_for_views_classes(self):
        for url, func_cls, args, kwargs in (
                ('/personen', sp_views.PersonenView, (), {}),
                ('/funktionen', sp_views.FunktionenView, (), {}),
                ('/tests', TemplateView, (), {}),
                ('/robots.txt', TemplateView, (), {}),
        ):
            resolver = resolve(url)
            self.assertEqual(resolver.func.view_class, func_cls, msg=f'{url} - func_cls')
            self.assertEqual(resolver.args, args, msg=f'{url} - args')
            self.assertEqual(resolver.kwargs, kwargs, msg=f'{url} - kwargs')
