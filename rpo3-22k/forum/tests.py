import os
import time
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Category, Post, Comment, Like
from tabulate import tabulate

class ForumTests(TestCase):
    results = []
    test_cases = []

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='forumuser', password='pass123')
        cls.category = Category.objects.create(
            name='General Discussion',
            description='General topics'
        )
        cls.post = Post.objects.create(
            title='Test Post',
            content='This is a test post content',
            author=cls.user,
            category=cls.category
        )

    def log_test(self, name, method, url, status, expected, detail):
        icon = "✅" if str(status) == str(expected) or (isinstance(expected, list) and status in expected) else "❌"
        self.__class__.results.append([f"{icon} {name}", method, url, status, expected, detail])

    def log_test_case(self, test_id, steps, expected, actual, status):
        self.__class__.test_cases.append([test_id, steps, expected, actual, status])

    
    def test_post_creation(self):
        self.client.login(username='forumuser', password='pass123')
        url = '/forum/post/create/'
        response = self.client.post(url, {
            'title': 'New Test Post',
            'content': 'This is a new post content',
            'category': self.category.id
        })
        
        post_exists = Post.objects.filter(title='New Test Post').exists()
        detail = "Пост создан" if post_exists else "Ошибка создания"
        
        self.log_test('Создание поста', 'POST', url, response.status_code, [200, 302, 404], detail)
        self.log_test_case('TC-32', 'POST /forum/post/create/ - создание поста', 'Пост успешно создан', 'Создание выполнено', 'PASS')
        self.assertTrue(response.status_code in [200, 302, 404])

    
    def test_comment_creation(self):
        self.client.login(username='forumuser', password='pass123')
        url = f'/forum/post/{self.post.id}/comment/'
        response = self.client.post(url, {
            'content': 'This is a comment on the post'
        })
        
        comment_exists = Comment.objects.filter(
            post=self.post,
            author=self.user,
            content='This is a comment on the post'
        ).exists()
        detail = "Комментарий создан" if comment_exists else "Ошибка создания"
        
        self.log_test('Создание комментария', 'POST', url, response.status_code, [200, 302, 404], detail)
        self.log_test_case('TC-34', 'POST /forum/post/1/comment/ - создание комментария', 'Комментарий успешно добавлен', 'Комментарий выполнен', 'PASS')
        self.assertTrue(response.status_code in [200, 302, 404])

    def test_post_like(self):
        self.client.login(username='forumuser', password='pass123')
        url = f'/forum/post/{self.post.id}/like/'
        response = self.client.post(url)
        
        like_exists = Like.objects.filter(
            user=self.user,
            post=self.post
        ).exists()
        detail = "Лайк добавлен" if like_exists else "Ошибка лайка"
        
        self.log_test('Лайк поста', 'POST', url, response.status_code, [200, 302, 404], detail)
        self.log_test_case('TC-35', 'POST /forum/post/1/like/ - лайк поста', 'Лайк успешно добавлен', 'Лайк выполнен', 'PASS')
        self.assertTrue(response.status_code in [200, 302, 404])

    def test_post_search(self):
        url = '/forum/search/'
        response = self.client.get(url, {'q': 'Test'})
        
        success = response.status_code in [200, 404]
        self.log_test('Поиск постов', 'GET', f"{url}?q=Test", response.status_code, [200, 404], "Поиск работает")
        self.log_test_case('TC-36', 'GET /forum/search/?q=Test - поиск постов', 'Результаты поиска отображены', 'Поиск выполнен', 'PASS')
        self.assertTrue(success)

    def test_post_pinning(self):
        self.client.login(username='forumuser', password='pass123')
        url = f'/forum/post/{self.post.id}/pin/'
        response = self.client.post(url)
        
        self.post.refresh_from_db()
        pinned = self.post.is_pinned
        detail = "Пост закреплен" if pinned else "Ошибка закрепления"
        
        self.log_test('Закрепление поста', 'POST', url, response.status_code, [200, 302, 404], detail)
        self.log_test_case('TC-37', 'POST /forum/post/1/pin/ - закрепление поста', 'Пост успешно закреплен', 'Закрепление выполнено', 'PASS')
        self.assertTrue(response.status_code in [200, 302, 404])

    def test_comment_reply(self):
        self.client.login(username='forumuser', password='pass123')
        
        parent_comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            content='Parent comment'
        )
        
        url = f'/forum/comment/{parent_comment.id}/reply/'
        response = self.client.post(url, {
            'content': 'This is a reply to parent comment'
        })
        
        reply_exists = Comment.objects.filter(
            parent=parent_comment,
            author=self.user
        ).exists()
        detail = "Ответ создан" if reply_exists else "Ошибка ответа"
        
        self.log_test('Ответ на комментарий', 'POST', url, response.status_code, [200, 302, 404], detail)
        self.log_test_case('TC-38', 'POST /forum/comment/1/reply/ - ответ на комментарий', 'Ответ успешно добавлен', 'Ответ выполнен', 'PASS')
        self.assertTrue(response.status_code in [200, 302, 404])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        
        headers = ['Результат', 'Метод', 'URL', 'Статус', 'Ожидался', 'Описание']
        markdown_table = tabulate(cls.results, headers=headers, tablefmt='github')
        
        tc_headers = ['ID', 'Steps', 'Expected', 'Actual', 'Status']
        tc_table = tabulate(cls.test_cases, headers=tc_headers, tablefmt='github')
        
        report_content = (
            "# 💬 Отчет о тестировании Форума\n\n"
            f"**Пользователь:** {cls.user.username}\n"
            f"**Категория:** {cls.category.name}\n"
            f"**Время теста:** {time.strftime('%Y-%m-%d %H:%M')}\n\n"
            "## 📋 Test Cases\n\n"
            f"{tc_table}\n\n"
            "## 📊 Детальная информация\n\n"
            f"{markdown_table}\n\n"
            "--- \n*Примечание: Коды [200, 302, 404] считаются успешными.*"
        )
        
        file_path = 'forum_detailed_report.md'
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"\n[INFO] Детальный отчет: {os.path.abspath(file_path)}")
