from django.test import TestCase

from posts.constants import MAX_POST_TEXT_LENGTH

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        expected_results = {
            str(self.post): self.post.text[:MAX_POST_TEXT_LENGTH],
            str(self.group): self.group.title,
        }
        for obj, expected_text in expected_results.items():
            with self.subTest(obj=obj):
                self.assertEqual(expected_text, obj)

    def test_post_model_verbose_name(self):
        """Тестирование verbose_name атрибутов модели Post"""
        field_verboses = {
            'text': 'Текст',
            'created': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    Post._meta.get_field(value).verbose_name, expected)

    def test_post_model_help_text(self):
        """Тестирование help_text атрибутов модели Post"""
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу для поста',
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    Post._meta.get_field(value).help_text, expected)
