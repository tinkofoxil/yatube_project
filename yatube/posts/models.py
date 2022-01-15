from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Group(models.Model):
    def __str__(self) -> str:
        return self.title
    title = models.CharField('Название сообщества', max_length=200)
    slug = models.SlugField(max_length = 50, unique=True, verbose_name='URL')
    description = models.TextField()

class Post(models.Model):
    text = models.TextField()
    pub_date = models.DateTimeField(auto_now_add=True)
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts'
    )


    
