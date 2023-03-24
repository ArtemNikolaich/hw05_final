from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class AboutURLTest(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_author_tech_pages(self):
        """Тестирование страниц об авторе и технологиях"""
        context = [
            reverse('about:author'),
            reverse('about:tech'),
        ]
        for address in context:
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html'
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)
