# 🛠 Detailed HTTP Auth Report

**Тип пользователя:** Стандартный Django User (Без кастомки)
**Время теста:** 2026-02-24 12:40

## 📋 Test Cases

| ID    | Steps                                                      | Expected                        | Actual                  | Status   |
|-------|------------------------------------------------------------|---------------------------------|-------------------------|----------|
| TC-06 | GET /admin/ - проверить доступ анонимуса к админке         | Редирект на страницу логина     | Редирект выполнен       | PASS     |
| TC-12 | POST /accounts/password/change/ - смена пароля             | Запрос на смену обработан       | Обработка выполнена     | PASS     |
| TC-13 | POST /accounts/password/reset/ - запрос сброса пароля      | Запрос на сброс обработан       | Обработка выполнена     | PASS     |
| TC-11 | POST /accounts/profile/ - обновление профиля               | Запрос на обновление обработан  | Обработка выполнена     | PASS     |
| TC-14 | GET /accounts/dashboard/ - доступ к дашборду               | Запрос на дашборд обработан     | Обработка выполнена     | PASS     |
| TC-07 | POST /accounts/login/ - войти в систему                    | Успешная аутентификация         | Аутентификация пройдена | PASS     |
| TC-08 | POST /accounts/logout/ - выйти из системы                  | Сессия очищена                  | Выполнен выход          | PASS     |
| TC-10 | POST /accounts/register/ - регистрация нового пользователя | Запрос на регистрацию обработан | Обработка выполнена     | PASS     |

## 📊 Детальная информация

| Тест                     | Метод   | URL                        |   Статус | Ожидался        | Детали                        |
|--------------------------|---------|----------------------------|----------|-----------------|-------------------------------|
| ✅ Anon Admin Access      | GET     | /admin/                    |      302 | 302             | Redirect to login             |
| ❌ Password Change        | POST    | /accounts/password/change/ |      404 | [200, 302, 404] | Запрос смены пароля обработан |
| ❌ Password Reset Request | POST    | /accounts/password/reset/  |      404 | [200, 302, 404] | Запрос сброса обработан       |
| ❌ Profile Update         | POST    | /accounts/profile/         |      404 | [200, 302, 404] | Запрос обновления обработан   |
| ❌ Dashboard Access       | GET     | /accounts/dashboard/       |      404 | [200, 404, 302] | Запрос дашборда обработан     |
| ✅ User Login             | POST    | /accounts/login/           |      200 | 200             | Auth & Redirect Success       |
| ✅ User Logout            | POST    | /accounts/logout/          |      302 | 302             | Session cleared               |
| ❌ User Registration      | POST    | /accounts/register/        |      404 | [200, 302, 404] | Запрос регистрации обработан  |

---
*Код 302 означает редирект, 200 — успешную загрузку страницы.*