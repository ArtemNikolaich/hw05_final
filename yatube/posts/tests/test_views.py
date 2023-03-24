from http import HTTPStatus

from django import forms
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Follow, Group, Post, User


class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст',
            group=cls.group,
            image=cls.uploaded,
        )
        cls.comment_data = {
            'text': 'Тестовый комментарий'
        }
        cls.user_follower = User.objects.create(username='user')
        cls.user_following = User.objects.create(username='user_1')

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = User.objects.create_user(username='StasBasov')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_of_post = User.objects.create_user(
            username='author_of_post'
        )
        self.authorized_client_of_post = Client()
        self.authorized_client_of_post.force_login(self.author_of_post)
        self.following_client = Client()
        self.follower_client = Client()
        self.following_client.force_login(self.user_following)
        self.follower_client.force_login(self.user_follower)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test'}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': 'StasBasov'}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
            'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
            'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html'
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                if reverse_name == reverse('posts:post_edit',
                                           kwargs={'post_id': self.post.id}):
                    response = self.authorized_client_of_post.get(reverse_name)
                else:
                    response = self.authorized_client.get(reverse_name)
                    self.assertEqual(response.status_code, HTTPStatus.OK)
                    self.assertTemplateUsed(response, template)

    def test_index_view_context_with_image(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'Это главная страница проекта Yatube')
        self.assertContains(response, 'Тестовый текст')
        self.assertIn('page_obj', response.context)
        self.assertIn('posts', response.context)
        self.assertEqual(
            response.context['posts'][0].image,
            self.post.image.name
        )

    def test_group_posts_view_context_with_image(self):
        response = self.client.get(reverse('posts:group_list',
                                           kwargs={'slug': 'test'}))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'Тестовая группа')
        self.assertContains(response, 'Тестовый текст')
        self.assertIn('page_obj', response.context)
        self.assertIn('group', response.context)
        self.assertIn('posts', response.context)
        self.assertEqual(
            response.context['posts'][0].image,
            self.post.image.name
        )

    def test_profile_view_context_with_image(self):
        response = self.client.get(reverse('posts:profile',
                                           kwargs={'username': 'auth'}))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'Профайл пользователя auth')
        self.assertContains(response, 'Тестовый текст')
        self.assertIn('page_obj', response.context)
        self.assertIn('author', response.context)
        self.assertIn('total_posts', response.context)
        self.assertEqual(
            response.context['author'].posts.first().image,
            self.post.image.name
        )

    def test_post_detail_view_context_with_image(self):
        response = self.client.get(reverse('posts:post_detail',
                                           kwargs={'post_id': self.post.id}))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'Тестовый текст')
        self.assertIn('post', response.context)
        self.assertEqual(
            response.context['post'].image,
            self.post.image.name
        )

    def test_create_post_form(self):
        url = reverse('posts:post_create')
        response = self.authorized_client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'posts/create_post.html')
        self.assertIsInstance(response.context['form'], forms.ModelForm)
        self.assertFalse('post' in response.context)

    def test_edit_post_form(self):
        url = reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        response = self.authorized_client.get(url)
        self.assertRedirects(response, reverse('posts:post_detail',
                                               kwargs={'post_id': self.post.id}
                                               ))

    def test_create_post_in_group(self):
        """Если при создании поста указать группу, то этот пост появляется
        на главной странице сайта, на странице выбранной группы и в профайле
        пользователя."""
        new_group = Group.objects.create(
            title='Новая группа',
            slug='new_group',
            description='Новое описание',
        )
        post_data = {
            'text': 'Текст нового поста',
            'group': new_group.pk,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=post_data,
            follow=True
        )
        pages_to_check = {
            reverse('posts:index'): post_data['text'],
            reverse('posts:group_list', kwargs={'slug': new_group.slug}):
            post_data['text'],
            reverse('posts:profile', kwargs={'username': self.user.username}):
            post_data['text']
        }
        for page, text in pages_to_check.items():
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertContains(response, text)

    def test_create_post_in_wrong_group(self):
        """Пост не должен попадать в группу,
        для которой не был предназначен."""
        new_group = Group.objects.create(
            title='Новая группа',
            slug='new_group',
            description='Новое описание',
        )
        post_data = {
            'text': 'Текст нового поста',
            'group': new_group.pk,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=post_data,
            follow=True
        )
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertNotContains(response, post_data)

    def test_comment_post_authorization(self):
        """Комментирование поста возможно только для
        авторизованных пользователей."""
        url = reverse('posts:add_comment', kwargs={'post_id': self.post.pk})
        response = self.guest_client.post(url, data=self.comment_data)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, f'/auth/login/?next={url}')

    def test_comment_post(self):
        """После успешной отправки комментарий появляется на странице поста."""
        url = reverse('posts:add_comment', kwargs={'post_id': self.post.pk})
        response = self.authorized_client.post(url, data=self.comment_data,
                                               follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, self.comment_data['text'])
        self.assertTrue(response.context['comments'].filter(
            text=self.comment_data['text']).exists())

    def test_cache_index(self):
        """Кеширование главной страницы"""
        url = reverse('posts:index')
        response = self.client.get(url).content
        Post.objects.all().delete()
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK, response.content)
        cache.clear()
        response = self.client.get(url)
        self.assertNotEqual(response, response.content)

    def test_custom_404_page(self):
        """страница 404 отдаёт кастомный шаблон"""
        response = self.client.get('/page_not_found/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_follow(self):
        """Зарегистрированный пользователь может подписываться."""
        follower_count = Follow.objects.count()
        self.follower_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user_following}))
        self.assertEqual(Follow.objects.count(), follower_count + 1)

    def test_unfollow(self):
        """Зарегистрированный пользователь может отписаться."""
        Follow.objects.create(
            user=self.user_follower,
            author=self.user_following
        )
        follower_count = Follow.objects.count()
        self.follower_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.user_following}))
        self.assertEqual(Follow.objects.count(), follower_count - 1)

    def test_new_post_see_follower(self):
        """Пост появляется в ленте подписавшихся."""
        posts = Post.objects.create(
            text=self.post.text,
            author=self.user_following,
        )
        follow = Follow.objects.create(
            user=self.user_follower,
            author=self.user_following
        )
        response = self.follower_client.get(reverse('posts:follow_index'))
        post = response.context['page_obj'][0]
        self.assertEqual(post, posts)
        follow.delete()
        response = self.follower_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 0)
