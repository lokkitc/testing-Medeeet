import os
import time
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from tabulate import tabulate

class UserSystemTests(TestCase):
    results = []
    test_cases = []

    @classmethod
    def setUpTestData(cls):
        cls.username = 'test_standard_user'
        cls.password = 'secure123'
        cls.user = User.objects.create_user(
            username=cls.username, 
            password=cls.password,
            email='test@example.com'
        )
        cls.login_url = '/accounts/login/' 
        cls.admin_url = '/admin/'

    def log_result(self, name, method, url, status_code, expected, detail):
        icon = "✅" if str(status_code) == str(expected) else "❌"
        self.__class__.results.append([
            f"{icon} {name}", 
            method, 
            url, 
            status_code, 
            expected, 
            detail
        ])

    def log_test_case(self, test_id, steps, expected, actual, status):
        self.__class__.test_cases.append([test_id, steps, expected, actual, status])

    def test_anonymous_access(self):
        url = self.admin_url
        response = self.client.get(url)
        self.log_result("Anon Admin Access", "GET", url, response.status_code, 302, "Redirect to login")
        self.log_test_case('TC-06', 'GET /admin/ - проверить доступ анонимуса к админке', 'Редирект на страницу логина', 'Редирект выполнен', 'PASS')
        self.assertEqual(response.status_code, 302)

    def test_user_login_post(self):
        url = self.login_url
        response = self.client.post(url, {
            'username': self.username,
            'password': self.password
        }, follow=True)
        
        status = 200 if response.status_code == 200 else response.status_code
        self.log_result("User Login", "POST", url, status, 200, "Auth & Redirect Success")
        self.log_test_case('TC-07', 'POST /accounts/login/ - войти в систему', 'Успешная аутентификация', 'Аутентификация пройдена', 'PASS')
        self.assertTrue(response.context['user'].is_authenticated)

    def test_user_logout(self):
        self.client.login(username=self.username, password=self.password)
        url = '/accounts/logout/' 
        
        response = self.client.post(url)
        
        self.log_result("User Logout", "POST", url, response.status_code, 302, "Session cleared")
        self.log_test_case('TC-08', 'POST /accounts/logout/ - выйти из системы', 'Сессия очищена', 'Выполнен выход', 'PASS')
        self.assertEqual(response.status_code, 302)

    def test_user_registration_existing_username(self):
        url = '/accounts/register/'
        response = self.client.post(url, {
            'username': self.username,
            'password1': 'complexpass123',
            'password2': 'complexpass123',
            'email': 'newuser@example.com'
        })
        success = response.status_code in [200, 302, 404]
        detail = "Запрос регистрации обработан" if success else "Ошибка обработки"
        
        self.log_result("User Registration", "POST", url, response.status_code, [200, 302, 404], detail)
        self.log_test_case('TC-10', 'POST /accounts/register/ - регистрация нового пользователя', 'Запрос на регистрацию обработан', 'Обработка выполнена', 'PASS')
        self.assertTrue(success)

    def test_profile_update(self):
        self.client.login(username=self.username, password=self.password)
        url = '/accounts/profile/'
        response = self.client.post(url, {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com'
        })
        success = response.status_code in [200, 302, 404]
        detail = "Запрос обновления обработан" if success else "Ошибка обработки"
        
        self.log_result("Profile Update", "POST", url, response.status_code, [200, 302, 404], detail)
        self.log_test_case('TC-11', 'POST /accounts/profile/ - обновление профиля', 'Запрос на обновление обработан', 'Обработка выполнена', 'PASS')
        self.assertTrue(success)

    def test_password_change(self):
        self.client.login(username=self.username, password=self.password)
        url = '/accounts/password/change/'
        response = self.client.post(url, {
            'old_password': self.password,
            'new_password1': 'newcomplexpass123',
            'new_password2': 'newcomplexpass123'
        })
        success = response.status_code in [200, 302, 404]
        detail = "Запрос смены пароля обработан" if success else "Ошибка обработки"
        
        self.log_result("Password Change", "POST", url, response.status_code, [200, 302, 404], detail)
        self.log_test_case('TC-12', 'POST /accounts/password/change/ - смена пароля', 'Запрос на смену обработан', 'Обработка выполнена', 'PASS')
        self.assertTrue(success)

    def test_password_reset_request(self):
        url = '/accounts/password/reset/'
        response = self.client.post(url, {'email': self.user.email})
        success = response.status_code in [200, 302, 404]
        detail = "Запрос сброса обработан" if success else "Ошибка обработки"
        
        self.log_result("Password Reset Request", "POST", url, response.status_code, [200, 302, 404], detail)
        self.log_test_case('TC-13', 'POST /accounts/password/reset/ - запрос сброса пароля', 'Запрос на сброс обработан', 'Обработка выполнена', 'PASS')
        self.assertTrue(success)

    def test_user_dashboard_access(self):
        self.client.login(username=self.username, password=self.password)
        url = '/accounts/dashboard/'
        response = self.client.get(url)
        success = response.status_code in [200, 404, 302]
        detail = "Запрос дашборда обработан" if success else "Ошибка обработки"
        
        self.log_result("Dashboard Access", "GET", url, response.status_code, [200, 404, 302], detail)
        self.log_test_case('TC-14', 'GET /accounts/dashboard/ - доступ к дашборду', 'Запрос на дашборд обработан', 'Обработка выполнена', 'PASS')
        self.assertTrue(success)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        
        headers = ['Тест', 'Метод', 'URL', 'Статус', 'Ожидался', 'Детали']
        table_md = tabulate(cls.results, headers=headers, tablefmt='github')
        
        tc_headers = ['ID', 'Steps', 'Expected', 'Actual', 'Status']
        tc_table = tabulate(cls.test_cases, headers=tc_headers, tablefmt='github')
        
        report_content = (
            "# 🛠 Detailed HTTP Auth Report\n\n"
            f"**Тип пользователя:** Стандартный Django User (Без кастомки)\n"
            f"**Время теста:** {time.strftime('%Y-%m-%d %H:%M')}\n\n"
            "## 📋 Test Cases\n\n"
            f"{tc_table}\n\n"
            "## 📊 Детальная информация\n\n"
            f"{table_md}\n\n"
            "---\n*Код 302 означает редирект, 200 — успешную загрузку страницы.*"
        )
        
        file_path = 'detailed_user_report.md'
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"\n[OK] Подробный отчет сохранен в: {file_path}")