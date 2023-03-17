import shutil
import tempfile

from django.conf import settings
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Post, Group, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Название группы',
            description='Тестовое описание',
            slug='test-slug'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            group=cls.group,
            pub_date=timezone.now(),
            author=cls.user,
            image=cls.uploaded
        )
        cls.comment = Comment.objects.create(
            text='Комментарий',
            post=cls.post,
            author=cls.user,
            created=timezone.now()
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.pk,
            'image': self.uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        post_latest = Post.objects.latest('pub_date')
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(post_latest)
        self.assertEqual(post_latest.text, form_data['text'])
        self.assertEqual(post_latest.group.pk, form_data['group'])
        self.assertEqual(post_latest.author, self.user)
        self.assertTrue(Post.objects.filter(
            group=self.group.pk,
            text=self.post.text,
            image='posts/small.gif',
        ).exists())

    def test_text_valid_form_edit_post(self):
        """Валидная форма редактирует запись в Post."""
        form_data = {
            'text': 'Редактируемый текст',
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=(self.post.id,)),
            data=form_data,
            follow=True
        )
        post_latest = Post.objects.latest('pub_date')
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(post_latest)
        self.assertNotEqual(response, self.post.text)
        self.assertEqual(post_latest.author, self.user)
        self.assertEqual(post_latest.text, form_data['text'])
        self.assertEqual(post_latest.group.pk, self.group.pk)

    def test_create_post_guest(self):
        response = self.guest_client.post(
            reverse('posts:post_create'),
            follow=True,
        )
        self.assertRedirects(response, '/auth/login/?next=/create/')
        self.assertEqual(Post.objects.count(), Post.objects.count())

    def test_create_comment(self):
        """Валидная форма создает запись в Post."""
        form_data = {
            'text': 'Комментарий',
        }
        comments_latest = Comment.objects.latest('created')
        self.assertTrue(comments_latest)
        self.assertEqual(comments_latest.text, form_data['text'])
        self.assertEqual(comments_latest.author, self.user)
