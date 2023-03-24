from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_open_page(self):
        """Тестирование общедоступных страниц"""
        context = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test'}),
            reverse('posts:profile', kwargs={'username': 'auth'}),
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
        ]
        for address in context:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_close_page(self):
        """Тестирование скрытых страниц"""
        context = [
            reverse('posts:post_create'),
        ]
        for address in context:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_author_page(self):
        """Тестирование страниц доступных только автору"""
        context = [
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
        ]
        for address in context:
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_not_found_page(self):
        """Тестирование запроса несуществующей страницы"""
        context = [
            '/not_found_page/',
            '/group/not_found_group/',
            '/profile/not_found_user/',
            '/posts/999/',
        ]
        for address in context:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_redirect_for_anonymous_user(self):
        """Тестирование редиректа неавторизованного пользователя"""
        context = [
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
        ]
        for address in context:
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(
                    response,
                    f'{reverse("login")}?next={address}',
                    status_code=HTTPStatus.FOUND,
                    target_status_code=HTTPStatus.OK,
                )
