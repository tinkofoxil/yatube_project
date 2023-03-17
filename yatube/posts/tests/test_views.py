import shutil
import tempfile

from django.conf import settings
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.core.cache import cache
from django.urls import reverse

from ..models import Post, Group, Comment, Follow, User
from ..forms import PostForm, CommentForm

from posts.views import NUMBERS_OF_POST

TEST_NUMBER_OF_POST = 13
FIRST_NUMBER_OF_POST = 1

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskPagesTests(TestCase):
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
        cls.follower = User.objects.create_user(username='follower')
        cls.follow = Follow.objects.create(
            author=cls.user,
            user=cls.follower
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template_anonymous(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/profile.html': reverse(
                'posts:profile', kwargs={'username': self.user}
            ),
            'posts/group_list.html': reverse(
                'posts:group_posts', kwargs={'slug': 'test-slug'}
            ),
            'posts/post_detail.html': (
                reverse('posts:post_detail', kwargs={'post_id': self.post.id})
            ),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_edit_pages_authorized_uses_correct_template(self):
        """URL-адреса используют шаблон posts/create.html."""
        response = self.authorized_client.\
            get(reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_post_edit_pages_authorized_uses_correct_template(self):
        """URL-адреса используют шаблон posts/create.html."""
        response = self.authorized_client.\
            get(reverse('posts:post_create'))
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_post_follow_page_authorized_uses_correct_template(self):
        """URL-адреса используют шаблон posts/create.html."""
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertTemplateUsed(response, 'posts/follow.html')

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        self.assertIn('page_obj', response.context)
        self.assertEqual(response.context['page_obj'][0], self.post)
        self.assertEqual(
            response.context['page_obj'][0].text, self.post.text
        )
        self.assertEqual(
            response.context['page_obj'][0].pub_date, self.post.pub_date
        )
        self.assertEqual(
            response.context['page_obj'][0].author.username, self.user.username
        )
        image = response.context["page_obj"][0].image
        self.assertEqual(image.read(), self.small_gif)

    def test_follow_page_show_correct_context(self):
        """Шаблон follow_index сформирован с правильным контекстом."""
        self.authorized_client.force_login(self.follower)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertIn('page_obj', response.context)
        self.assertEqual(response.context['page_obj'][0], self.post)
        self.assertEqual(
            response.context['page_obj'][0].text, self.post.text
        )
        self.assertEqual(
            response.context['page_obj'][0].pub_date, self.post.pub_date
        )
        self.assertEqual(
            response.context['page_obj'][0].author.username, self.user.username
        )
        image = response.context["page_obj"][0].image
        self.assertEqual(image.read(), self.small_gif)

    def test_follow(self):
        self.authorized_client.force_login(self.follower)
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': 'auth'}))
        self.assertTrue(Follow.objects.filter(
            author=self.user, user=self.follower
        ).exists())

    def test_unfollow(self):
        self.authorized_client.force_login(self.follower)
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': 'auth'}))
        self.assertTrue(Follow.objects.filter(
            author=self.user, user=self.follower
        ).exists())
        self.authorized_client.get(
            reverse('posts:profile_unfollow', kwargs={'username': 'auth'}))
        self.assertFalse(Follow.objects.filter(
            author=self.user, user=self.follower
        ).exists())

    def test_follow_myself(self):
        self.authorized_client.force_login(self.follower)
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': 'follower'}))
        self.assertFalse(Follow.objects.filter(
            author=self.follower, user=self.follower
        ).exists())

    def test_group_posts_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse(
            'posts:group_posts', kwargs={'slug': 'test-slug'})
        )
        self.assertIn('group', response.context)
        self.assertIn('page_obj', response.context)
        self.assertEqual(response.context['group'], self.group)
        self.assertEqual(response.context['page_obj'][0], self.post)
        self.assertEqual(
            response.context['page_obj'][0].text, 'Тестовый текст'
        )
        self.assertEqual(
            response.context['page_obj'][0].group.title, 'Название группы'
        )
        self.assertEqual(
            response.context['page_obj'][0].pub_date, self.post.pub_date
        )
        self.assertEqual(
            response.context['page_obj'][0].author.username, 'auth'
        )
        self.assertEqual(response.context['group'].slug, 'test-slug')
        image = response.context["page_obj"][0].image
        self.assertEqual(image.read(), self.small_gif)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse(
            'posts:profile', kwargs={'username': self.user})
        )
        self.assertEqual(response.context['page_obj'][0], self.post)
        self.assertEqual(
            response.context['page_obj'][0].author.username, 'auth'
        )
        image = response.context["page_obj"][0].image
        self.assertEqual(image.read(), self.small_gif)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.context['post'], self.post)
        self.assertEqual(
            response.context['post'].author.username, 'auth'
        )
        self.assertEqual(
            response.context['post'].pub_date, self.post.pub_date
        )
        self.assertEqual(response.context['post'].text, 'Тестовый текст')
        image = response.context["post"].image
        self.assertEqual(image.read(), self.small_gif)

    def test_add_comment(self):
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertIsInstance(response.context['form'], CommentForm)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit редактирует пост с правильным id"""
        response = (self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}
        )))
        form_field_text = response.context['form'].initial['text']
        self.assertEqual(form_field_text, self.post.text)

    def test_post_create_page_show_correct_context(self):
        """Шаблон create_post создает новый пост"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertIsNone(response.context.get('is_edit', None))

    def test_post_detail_with_comment(self):
        Comment.objects.create(
            author=self.user,
            text='Комментарий',
            post=self.post
        )
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(
            response.context['comments'][0].text, self.comment.text
        )

    def test_post_with_group(self):
        Post.objects.create(
            author=self.user,
            text='Тестовый пост с группой',
            group=self.group,
        )
        # Проверяем, что пост попал на главную страницу
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        text_0_index = first_object.text
        self.assertEqual(text_0_index, 'Тестовый пост с группой')
        # Проверяем, что пост попал в группу
        response = self.authorized_client.get(reverse(
            'posts:group_posts', kwargs={'slug': 'test-slug'}
        ))
        first_object = response.context['page_obj'][0]
        text_0_group = first_object.text
        self.assertEqual(text_0_group, 'Тестовый пост с группой')
        # Проверяем, что пост попал в профиль
        response = self.guest_client.get(reverse(
            'posts:profile', kwargs={'username': self.user})
        )
        first_object = response.context['page_obj'][0]
        text_0_profile = first_object.text
        self.assertEqual(text_0_profile, 'Тестовый пост с группой')

    def test_post_without_group(self):
        Post.objects.create(
            author=self.user,
            text='Тестовый пост без группы',
        )
        # Проверяем, что пост попал на главную страницу
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        text_0_index = first_object.text
        self.assertEqual(text_0_index, 'Тестовый пост без группы')
        # Проверяем, что пост не попал в группу
        response = self.authorized_client.get(reverse(
            'posts:group_posts', kwargs={'slug': 'test-slug'}
        ))
        first_object = response.context['page_obj'][0]
        text_0_group = first_object.text
        self.assertNotEqual(text_0_group, 'Тестовый пост без группы')
        # Проверяем, что пост попал в профиль
        response = self.guest_client.get(reverse(
            'posts:profile', kwargs={'username': self.user})
        )
        first_object = response.context['page_obj'][0]
        text_0_profile = first_object.text
        self.assertEqual(text_0_profile, 'Тестовый пост без группы')

    def test_cache_index_page(self):
        """Тестирование использование кеширования"""
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        cache_check = response.content
        post = Post.objects.get(pk=1)
        post.delete()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.content, cache_check)
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, cache_check)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        )
        for post_index in range(1, TEST_NUMBER_OF_POST):
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'Какой-то текст №{post_index}',
                group=cls.group,
            )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records_index(self):
        response = self.client.get(reverse('posts:index'))
        # Проверка: количество постов на первой странице равно 10.
        self.assertEqual(len(response.context['page_obj']), NUMBERS_OF_POST)

    def test_second_page_contains_three_records_index(self):
        # Проверка: на второй странице должно быть три поста.
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(
            len(response.context['page_obj']),
            TEST_NUMBER_OF_POST - NUMBERS_OF_POST
        )

    def test_first_page_contains_ten_records_group_list(self):
        response = self.guest_client.get(reverse(
            'posts:group_posts', kwargs={'slug': 'test-slug'})
        )
        # Проверка: количество постов на первой странице группы равно 10.
        self.assertEqual(len(response.context['page_obj']), NUMBERS_OF_POST)

    def test_second_page_contains_three_records_group_list(self):
        # Проверка: на второй странице группы должно быть три поста.
        response = self.guest_client.get(reverse(
            'posts:group_posts', kwargs={'slug': 'test-slug'}) + '?page=2')
        self.assertEqual(
            len(response.context['page_obj']),
            TEST_NUMBER_OF_POST - NUMBERS_OF_POST
        )

    def test_first_page_contains_ten_records_profile(self):
        response = self.guest_client.get(reverse(
            'posts:profile', kwargs={'username': self.user})
        )
        # Проверка: количество постов на первой странице профиля равно 10.
        self.assertEqual(len(response.context['page_obj']), NUMBERS_OF_POST)

    def test_second_page_contains_three_records_profile(self):
        # Проверка: на второй странице профиля должно быть три поста.
        response = self.guest_client.get(reverse(
            'posts:profile', kwargs={'username': self.user}) + '?page=2')
        self.assertEqual(
            len(response.context['page_obj']),
            TEST_NUMBER_OF_POST - NUMBERS_OF_POST
        )
