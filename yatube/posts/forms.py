from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {'text': 'Введите текст',
                  'group': 'Выберите группу',
                  'image': 'Картинка'}
        help_texts = {'text': 'Что тебя беспокоит?',
                      'group': 'К какой группе отнесем пост?',
                      }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text', )
        labels = {'text': 'Введите комментарий', }
