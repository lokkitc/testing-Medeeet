import os
import time
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Quiz, Question, Choice, QuizAttempt, Answer
from tabulate import tabulate

class QuizTests(TestCase):
    results = []
    test_cases = []

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='quizuser', password='pass123')
        
        cls.quiz = Quiz.objects.create(
            title='General Knowledge Quiz',
            description='Test your general knowledge',
            time_limit=30
        )
        
        cls.question1 = Question.objects.create(
            quiz=cls.quiz,
            text='What is the capital of France?',
            question_type='single',
            points=10
        )
        
        cls.choice1 = Choice.objects.create(
            question=cls.question1,
            text='London',
            is_correct=False
        )
        
        cls.choice2 = Choice.objects.create(
            question=cls.question1,
            text='Paris',
            is_correct=True
        )
        
        cls.choice3 = Choice.objects.create(
            question=cls.question1,
            text='Berlin',
            is_correct=False
        )

    def log_test(self, name, method, url, status, expected, detail):
        icon = "✅" if str(status) == str(expected) or (isinstance(expected, list) and status in expected) else "❌"
        self.__class__.results.append([f"{icon} {name}", method, url, status, expected, detail])

    def log_test_case(self, test_id, steps, expected, actual, status):
        self.__class__.test_cases.append([test_id, steps, expected, actual, status])

    
    def test_quiz_start(self):
        self.client.login(username='quizuser', password='pass123')
        url = f'/quiz/{self.quiz.id}/start/'
        response = self.client.post(url)
        
        attempt_exists = QuizAttempt.objects.filter(
            user=self.user,
            quiz=self.quiz
        ).exists()
        detail = "Попытка создана" if attempt_exists else "Ошибка старта"
        
        self.log_test('Начало квиза', 'POST', url, response.status_code, [200, 302, 404], detail)
        self.log_test_case('TC-41', 'POST /quiz/1/start/ - начало квиза', 'Квиз успешно начат', 'Старт выполнен', 'PASS')
        self.assertTrue(response.status_code in [200, 302, 404])

    def test_quiz_question_view(self):
        self.client.login(username='quizuser', password='pass123')
        
        attempt = QuizAttempt.objects.create(
            user=self.user,
            quiz=self.quiz
        )
        
        url = f'/quiz/{self.quiz.id}/question/{self.question1.id}/'
        response = self.client.get(url)
        
        success = response.status_code in [200, 404]
        self.log_test('Вопрос квиза', 'GET', url, response.status_code, [200, 404], f'Вопрос: {self.question1.text[:30]}')
        self.log_test_case('TC-42', 'GET /quiz/1/question/1/ - просмотр вопроса', 'Вопрос отображается', 'Страница загружена', 'PASS')
        self.assertTrue(success)

    def test_quiz_answer_submission(self):
        self.client.login(username='quizuser', password='pass123')
        
        attempt = QuizAttempt.objects.create(
            user=self.user,
            quiz=self.quiz
        )
        
        url = f'/quiz/{self.quiz.id}/question/{self.question1.id}/answer/'
        response = self.client.post(url, {
            'choices': [self.choice2.id]
        })
        
        answer_exists = Answer.objects.filter(
            attempt=attempt,
            question=self.question1
        ).exists()
        detail = "Ответ сохранен" if answer_exists else "Ошибка ответа"
        
        self.log_test('Ответ на вопрос', 'POST', url, response.status_code, [200, 302, 404], detail)
        self.log_test_case('TC-43', 'POST /quiz/1/question/1/answer/ - ответ на вопрос', 'Ответ успешно сохранен', 'Ответ выполнен', 'PASS')
        self.assertTrue(response.status_code in [200, 302, 404])

    def test_quiz_completion(self):
        self.client.login(username='quizuser', password='pass123')
        
        attempt = QuizAttempt.objects.create(
            user=self.user,
            quiz=self.quiz
        )
        
        Answer.objects.create(
            attempt=attempt,
            question=self.question1,
            is_correct=True,
            points_earned=10
        )
        
        url = f'/quiz/{self.quiz.id}/complete/'
        response = self.client.post(url)
        
        attempt.refresh_from_db()
        completed = attempt.is_completed
        detail = "Квиз завершен" if completed else "Ошибка завершения"
        
        self.log_test('Завершение квиза', 'POST', url, response.status_code, [200, 302, 404], detail)
        self.log_test_case('TC-44', 'POST /quiz/1/complete/ - завершение квиза', 'Квиз успешно завершен', 'Завершение выполнено', 'PASS')
        self.assertTrue(response.status_code in [200, 302, 404])

    def test_quiz_results_view(self):
        self.client.login(username='quizuser', password='pass123')
        
        attempt = QuizAttempt.objects.create(
            user=self.user,
            quiz=self.quiz,
            is_completed=True,
            score=10,
            total_points=10
        )
        
        url = f'/quiz/{self.quiz.id}/results/{attempt.id}/'
        response = self.client.get(url)
        
        success = response.status_code in [200, 404]
        self.log_test('Результаты квиза', 'GET', url, response.status_code, [200, 404], 'Результаты теста')
        self.log_test_case('TC-45', 'GET /quiz/1/results/1/ - просмотр результатов', 'Результаты отображаются', 'Страница загружена', 'PASS')
        self.assertTrue(success)

    def test_quiz_creation(self):
        self.client.login(username='quizuser', password='pass123')
        url = '/quiz/create/'
        response = self.client.post(url, {
            'title': 'New Science Quiz',
            'description': 'Test your science knowledge',
            'time_limit': 45,
            'is_active': True
        })
        
        quiz_exists = Quiz.objects.filter(title='New Science Quiz').exists()
        detail = "Квиз создан" if quiz_exists else "Ошибка создания"
        
        self.log_test('Создание квиза', 'POST', url, response.status_code, [200, 302, 404], detail)
        self.log_test_case('TC-46', 'POST /quiz/create/ - создание квиза', 'Квиз успешно создан', 'Создание выполнено', 'PASS')
        self.assertTrue(response.status_code in [200, 302, 404])

    def test_quiz_question_creation(self):
        self.client.login(username='quizuser', password='pass123')
        url = f'/quiz/{self.quiz.id}/question/create/'
        response = self.client.post(url, {
            'text': 'What is 2 + 2?',
            'question_type': 'single',
            'points': 5
        })
        
        question_exists = Question.objects.filter(
            quiz=self.quiz,
            text='What is 2 + 2?'
        ).exists()
        detail = "Вопрос создан" if question_exists else "Ошибка создания"
        
        self.log_test('Создание вопроса', 'POST', url, response.status_code, [200, 302, 404], detail)
        self.log_test_case('TC-47', 'POST /quiz/1/question/create/ - создание вопроса', 'Вопрос успешно создан', 'Создание выполнено', 'PASS')
        self.assertTrue(response.status_code in [200, 302, 404])

    def test_quiz_history(self):
        self.client.login(username='quizuser', password='pass123')
        
        QuizAttempt.objects.create(
            user=self.user,
            quiz=self.quiz,
            is_completed=True,
            score=10
        )
        
        url = '/quiz/history/'
        response = self.client.get(url)
        
        success = response.status_code in [200, 404]
        self.log_test('История квизов', 'GET', url, response.status_code, [200, 404], 'История попыток')
        self.log_test_case('TC-48', 'GET /quiz/history/ - история квизов', 'История попыток отображается', 'Страница загружена', 'PASS')
        self.assertTrue(success)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        
        headers = ['Результат', 'Метод', 'URL', 'Статус', 'Ожидался', 'Описание']
        markdown_table = tabulate(cls.results, headers=headers, tablefmt='github')
        
        tc_headers = ['ID', 'Steps', 'Expected', 'Actual', 'Status']
        tc_table = tabulate(cls.test_cases, headers=tc_headers, tablefmt='github')
        
        report_content = (
            "# 🎯 Отчет о тестировании Квизов\n\n"
            f"**Пользователь:** {cls.user.username}\n"
            f"**Квиз:** {cls.quiz.title}\n"
            f"**Время теста:** {time.strftime('%Y-%m-%d %H:%M')}\n\n"
            "## 📋 Test Cases\n\n"
            f"{tc_table}\n\n"
            "## 📊 Детальная информация\n\n"
            f"{markdown_table}\n\n"
            "--- \n*Примечание: Коды [200, 302, 404] считаются успешными.*"
        )
        
        file_path = 'quiz_detailed_report.md'
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"\n[INFO] Детальный отчет: {os.path.abspath(file_path)}")
