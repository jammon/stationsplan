from django.test import TestCase, Client
from django.core.urlresolvers import reverse


class TestViewsAnonymously(TestCase):

    def test_view_redirects_to_login(self):
        c = Client()
        for url in ('change', 'month', 'plan'):
            response = c.get(reverse(url))
            self.assertEqual(response.status_code, 302, msg=url)
            response = c.get(reverse(url), follow=True)
            self.assertRedirects(response, '/login/?next=%2F'+url,
                                 msg_prefix=url)
            response = c.post(reverse(url), follow=True)
            self.assertRedirects(response, '/login/?next=%2F'+url,
                                 msg_prefix=url)

    def test_status_post(self):
        c = Client()
        self.assertEqual(c.post('/change/', {}).status_code, 404)
