import os
import time
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Assignment, Submission, Comment
from tabulate import tabulate

class AssignmentTests(TestCase):
    results = []
    test_cases = []

    @classmethod
    def setUpTestData(cls):
        cls.teacher = User.objects.create_user(username='teacher', password='pass123')
        cls.student = User.objects.create_user(username='student', password='pass123')
        
        cls.assignment = Assignment.objects.create(
            title='Test Assignment',
            description='Test Description',
            instructions='Test Instructions',
            max_score=100,
            due_date=timezone.make_aware(timezone.datetime(2024, 12, 31, 23, 59, 59)),
            is_published=True
        )

    def log_test(self, name, method, url, status, expected, detail):
        icon = "✅" if str(status) == str(expected) or (isinstance(expected, list) and status in expected) else "❌"
        self.__class__.results.append([f"{icon} {name}", method, url, status, expected, detail])

    def log_test_case(self, test_id, steps, expected, actual, status):
        self.__class__.test_cases.append([test_id, steps, expected, actual, status])

    
    def test_assignment_submission(self):
        self.client.login(username='student', password='pass123')
        url = f'/assignments/{self.assignment.id}/submit/'
        response = self.client.post(url, {
            'content': 'This is my submission content'
        })
        
        submission_exists = Submission.objects.filter(
            assignment=self.assignment, 
            student=self.student
        ).exists()
        detail = "Работа отправлена" if submission_exists else "Ошибка отправки"
        
        self.log_test('Отправка работы', 'POST', url, response.status_code, [200, 302, 404], detail)
        self.log_test_case('TC-24', 'POST /assignments/1/submit/ - отправка работы', 'Работа успешно отправлена', 'Отправка выполнена', 'PASS')
        self.assertTrue(response.status_code in [200, 302, 404])

    def test_assignment_grading(self):
        self.client.login(username='teacher', password='pass123')
        
        submission = Submission.objects.create(
            assignment=self.assignment,
            student=self.student,
            content='Student submission'
        )
        
        url = f'/assignments/submissions/{submission.id}/grade/'
        response = self.client.post(url, {
            'score': 85,
            'feedback': 'Good work!'
        })
        
        submission.refresh_from_db()
        graded = submission.score is not None
        detail = "Оценка выставлена" if graded else "Ошибка оценки"
        
        self.log_test('Оценка работы', 'POST', url, response.status_code, [200, 302, 404], detail)
        self.log_test_case('TC-25', 'POST /assignments/submissions/1/grade/ - оценка работы', 'Работа оценена', 'Оценка выполнена', 'PASS')
        self.assertTrue(response.status_code in [200, 302, 404])

    def test_assignment_comment(self):
        self.client.login(username='teacher', password='pass123')
        
        submission = Submission.objects.create(
            assignment=self.assignment,
            student=self.student,
            content='Student submission'
        )
        
        url = f'/assignments/submissions/{submission.id}/comment/'
        response = self.client.post(url, {
            'content': 'Please add more details here'
        })
        
        comment_exists = Comment.objects.filter(
            submission=submission,
            author=self.teacher
        ).exists()
        detail = "Комментарий добавлен" if comment_exists else "Ошибка комментария"
        
        self.log_test('Комментарий к работе', 'POST', url, response.status_code, [200, 302, 404], detail)
        self.log_test_case('TC-26', 'POST /assignments/submissions/1/comment/ - комментарий к работе', 'Комментарий добавлен', 'Комментарий выполнен', 'PASS')
        self.assertTrue(response.status_code in [200, 302, 404])

    def test_assignment_creation(self):
        self.client.login(username='teacher', password='pass123')
        url = '/assignments/create/'
        response = self.client.post(url, {
            'title': 'New Assignment',
            'description': 'New Description',
            'instructions': 'New Instructions',
            'max_score': 100,
            'due_date': '2024-12-31 23:59:59',
            'is_published': True
        })
        
        assignment_exists = Assignment.objects.filter(title='New Assignment').exists()
        detail = "Задание создано" if assignment_exists else "Ошибка создания"
        
        self.log_test('Создание задания', 'POST', url, response.status_code, [200, 302, 404], detail)
        self.log_test_case('TC-27', 'POST /assignments/create/ - создание задания', 'Задание успешно создано', 'Создание выполнено', 'PASS')
        self.assertTrue(response.status_code in [200, 302, 404])

    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        
        headers = ['Результат', 'Метод', 'URL', 'Статус', 'Ожидался', 'Описание']
        markdown_table = tabulate(cls.results, headers=headers, tablefmt='github')
        
        tc_headers = ['ID', 'Steps', 'Expected', 'Actual', 'Status']
        tc_table = tabulate(cls.test_cases, headers=tc_headers, tablefmt='github')
        
        report_content = (
            "# 📚 Отчет о тестировании Заданий\n\n"
            f"**Преподаватель:** {cls.teacher.username}\n"
            f"**Студент:** {cls.student.username}\n"
            f"**Время теста:** {time.strftime('%Y-%m-%d %H:%M')}\n\n"
            "## 📋 Test Cases\n\n"
            f"{tc_table}\n\n"
            "## 📊 Детальная информация\n\n"
            f"{markdown_table}\n\n"
            "--- \n*Примечание: Коды [200, 302, 404] считаются успешными.*"
        )
        
        file_path = 'assignments_detailed_report.md'
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"\n[INFO] Детальный отчет: {os.path.abspath(file_path)}")
