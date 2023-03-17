from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')

        widgets = {
            "text": forms.Textarea(attrs={
                'class': 'form-control',
                'cols': '40',
                'rows': '10'
            }),
            "group": forms.Select(attrs={
                'class': 'form-control'
            })
        }

        labels = {
            'text': ('Текст поста'),
            'group': ('Группа поста')
        }

        help_texts = {
            'text': ('Введите текст поста'),
            'group': ('Выберите группу поста (опционально)')
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            "text": forms.Textarea(attrs={
                'class': 'form-control',
                'rows': "3"
            })
        }
        help_texts = {
            'text': ('Введите текст поста'),
        }
