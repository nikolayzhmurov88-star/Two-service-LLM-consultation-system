# Двухсервисная система LLM-консультаций

## 📋 Оглавление
1. [Описание проекта](#описание-проекта)
2. [Архитектура системы](#архитектура-системы)
3. [Регистрация Telegram бота](#регистрация-telegram-бота)
4. [Регистрация OpenRouter API](#регистрация-openrouter-api)
5. [Установка и запуск](#установка-и-запуск)
6. [Проверка работы](#проверка-работы)
7. [Тестирование](#тестирование)
8. [Скриншоты](#скриншоты)

---

## Описание проекта

**Двухсервисная система LLM-консультаций** — это распределённое приложение, состоящее из двух независимых сервисов:

| Сервис | Назначение | Технологии |
|--------|-----------|-------------|
| **Auth Service** | Аутентификация пользователей, выпуск и проверка JWT-токенов | FastAPI, SQLite |
| **Bot Service** | LLM-консультации через Telegram-бота | aiogram 3, Celery, RabbitMQ, Redis, httpx |

### Ключевая идея

Telegram-бот не знает ничего о пользователях, паролях и механизмах регистрации. Он доверяет только корректно подписанному и не истёкшему JWT-токену, выданному сервисом авторизации.

---

## Архитектура системы

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                   ПОЛЬЗОВАТЕЛЬ                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘
         │                                                    │
         │ (1) Регистрация/Логин                             │ (4) Сообщение в бота
         │ (Swagger UI)                                      │ (Telegram)
         ▼                                                    ▼
┌─────────────────────┐                          ┌─────────────────────────────────────┐
│                     │                          │                                     │
│   AUTH SERVICE      │                          │           BOT SERVICE               │
│   (порт 8000)       │                          │           (порт 8001)               │
│                     │                          │                                     │
│ • Регистрация       │                          │ • Telegram polling                  │
│ • Логин             │                          │ • Проверка JWT                      │
│ • Выдача JWT        │                          │ • Генерация task_id                 │
│                     │                          │ • Отправка задачи в RabbitMQ        │
└─────────────────────┘                          └───────────────────┬─────────────────┘
                                                                    │
                                                                    │ (5) Задача
                                                                    │ llm_request.delay()
                                                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                     │
│                              RABBITMQ (порт 5672)                                   │
│                              ОЧЕРЕДЬ ЗАДАЧ                                          │
│                                                                                     │
│                        ┌─────────┐ ┌─────────┐ ┌─────────┐                         │
│                        │ Задача1 │ │ Задача2 │ │ Задача3 │  ...                     │
│                        └─────────┘ └─────────┘ └─────────┘                         │
│                                                                                     │
└─────────────────────────────────────┬───────────────────────────────────────────────┘
                                      │
                                      │ (6) Забор задачи
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                     │
│                              CELERY WORKER                                          │
│                             ВЫПОЛНЕНИЕ ЗАДАЧ                                        │
│                                                                                     │
│              ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                       │
│              │ Воркер 1    │ │ Воркер 2    │ │ Воркер 3    │  ...                   │
│              │ → OpenRouter│ │ → OpenRouter│ │ → OpenRouter│                       │
│              └──────┬──────┘ └──────┬──────┘ └──────┬──────┘                       │
│                     │               │               │                              │
│                     └───────────────┼───────────────┘                              │
│                                     ▼                                              │
│                          ┌─────────────────────────┐                              │
│                          │    OpenRouter API       │                              │
│                          │    (LLM провайдер)      │                              │
│                          └────────────┬────────────┘                              │
│                                       │                                            │
│                                       ▼                                            │
│                          ┌─────────────────────────┐                              │
│                          │    Сохранение результата│                              │
│                          │    r.setex(f"llm_result:{task_id}", 120, answer)      │
│                          └─────────────────────────┘                              │
└─────────────────────────────────────┬───────────────────────────────────────────────┘
                                      │
                                      │ (7) Результат в Redis
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                     │
│                              REDIS (порт 6379)                                      │
│                                                                                     │
│  ┌───────────────────────────────────────────────────────────────────────────────┐ │
│  │ token:1234567890 → "eyJhbGciOiJIUzI1NiIs..."  (JWT токен пользователя)        │ │
│  │ llm_result:uuid-1 → "Привет! Чем могу помочь?"  (ответ LLM)                   │ │
│  │ llm_result:uuid-2 → "Сегодня хорошая погода!"  (ответ LLM)                    │ │
│  └───────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                     │
└─────────────────────────────────────┬───────────────────────────────────────────────┘
                                      │
                                      │ (8) wait_for_result читает результат
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                     │
│                    BOT SERVICE забирает результат из Redis                          │
│                    и отправляет пользователю в Telegram                             │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Взаимодействие компонентов


1. **Пользователь регистрируется** в Auth Service через Swagger UI

2. **Auth Service выдаёт JWT-токен** (возвращает пользователю)

3. **Пользователь вводит токен** в Telegram-бота (команда `/token <JWT>`)

4. **Бот проверяет токен** (через `decode_and_validate`) и **сохраняет его в Redis** (ключ `token:{user_id}`)

5. **При отправке сообщения** бот генерирует `task_id` и отправляет задачу в Celery через RabbitMQ

6. **Celery воркер** забирает задачу из очереди, запрашивает LLM через OpenRouter API

7. **Результат сохраняется в Redis** (ключ `llm_result:{task_id}`) с TTL 120 секунд

8. **Бот** (функция `wait_for_result`) читает результат из Redis и отправляет пользователю в Telegram


---

## Регистрация Telegram бота

1. **Откройте Telegram** и найдите [@BotFather](https://t.me/botfather)

2. **Создайте нового бота** командой:
   ```
   /newbot
   ```

3. **Ответьте на вопросы BotFather:**
   - **Name:** Придумайте имя (например, `My LLM Bot`)
   - **Username:** Уникальное имя, заканчивающееся на `bot` (например, `my_llm_consultant_bot`)

4. **Сохраните токен**, который выдаст BotFather. Он выглядит так:
   ```
   1234567890:ABCdefGHIJKLMNOPQRSTUVWXYZ_abcdefgh
   ```

> **Внимание:** Токен — это секрет, не допустите его утечки

---

## Регистрация OpenRouter API

1. **Перейдите на сайт** [https://openrouter.ai](https://openrouter.ai)

2. **Зарегистрируйтесь** (через Google или GitHub)

3. **Получите API ключ:**
   - Перейдите в **Settings** → **API Keys**
   - Нажмите **Create Key**
   - Скопируйте ключ (начинается с `sk-or-v1-...`)

---

## Установка и запуск

### 1. Клонирование репозитория

```bash
git clone https://github.com/nikolayzhmurov88-star/Two-service-LLM-consultation-system.git
cd Two-service-LLM-consultation-system
```

### 2. Настройка переменных окружения

Скопируйте примеры файлов `.env` и заполните их:

```bash
cd auth_service
cp .env.example .env
nano .env
```

**`auth_service/.env`:**
```env
JWT_SECRET=your_super_secret_key_change_me #(! поменять на свой)
JWT_ALG=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=sqlite+aiosqlite:///./app.db
REDIS_URL=redis://redis:6379/0
RABBITMQ_URL=pyamqp://guest:guest@rabbitmq:5672//
```

```bash
cd ../bot_service
cp .env.example .env
nano .env
```

**`bot_service/.env`:**
```env

TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIJKLMNOPQRSTUVWXYZ_abcdefgh #(!Вставить свой токен)

JWT_SECRET=your_super_secret_key_change_me #(! поменять на свой) 
JWT_ALG=HS256

OPENROUTER_API_KEY=sk-or-v1-... #(! поменять на свой ключ)

OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

OPENROUTER_MODEL=openrouter/free (или liquid/lfm-2.5-1.2b-instruct:free для скорости) или другую на свое усмотрение

OPENROUTER_SITE_URL=http://localhost:8000
OPENROUTER_APP_NAME=ConsultationBot
REDIS_URL=redis://redis:6379/0
RABBITMQ_URL=pyamqp://guest:guest@rabbitmq:5672//
```

> **Важно:** `JWT_SECRET` должен быть одинаковым в обоих сервисах!
> Модель `liquid/lfm-2.5-1.2b-instruct:free` добавлена как быстрая альтернатива, однако на практике она стабильнее отвечает на запросы на английском языке.

### 3. Запуск Docker контейнеров

```bash
cd ~/Two-service-LLM-consultation-system
docker-compose up -d --build
```

### 4. Проверка запуска

```bash
docker-compose ps
```

Должны быть запущены 5 контейнеров: `rabbitmq`, `redis`, `auth_service`, `bot_service`, `celery_worker`.

---

## Проверка работы

### 1. Auth Service (Swagger UI)

Откройте в браузере: **http://localhost:8000/docs**

#### Регистрация пользователя

1. Нажмите `POST /auth/register` → `Try it out`
2. Введите данные в формате:
   ```json
   {
     "email": "ivanov@email.com",
     "password": "your_password"
   }
   ```
3. Нажмите `Execute`

#### Логин и получение JWT-токена

1. Нажмите `POST /auth/login` → `Try it out`
2. Введите те же email и пароль
3. Нажмите `Execute`
4. Скопируйте `access_token` из ответа

### 2. Telegram-бот

1. Найдите своего бота в Telegram
2. Отправьте команду с токеном:
   ```
   /token <скопированный_access_token>
   ```
3. Отправьте любое текстовое сообщение
4. Бот должен ответить через LLM

### 3. RabbitMQ Management

Откройте в браузере: **http://localhost:15672**

- **Login:** `guest`
- **Password:** `guest`

Здесь можно наблюдать очереди задач Celery.

### 4. Healthcheck

```bash
curl http://localhost:8000/health
# {"status":"ok"}

curl http://localhost:8001/health
# {"status":"ok"}
```

---

## Тестирование 

> Тесты проверяют только бизнес-логику и не требуют работающих контейнеров.  
> В `auth_service` используется **in‑memory SQLite** (`DATABASE_URL=sqlite+aiosqlite:///:memory:`), чтобы тесты не трогали реальную базу данных.  
> Виртуальные окружения создаются **отдельно для каждого сервиса**, так как их зависимости различаются.  

###  Auth Service

```bash
# Auth Service
cd auth_service
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
DATABASE_URL="sqlite+aiosqlite:///:memory:" pytest -v
```

###  Bot Service
```bash
cd ../bot_service
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
PYTHONPATH=. pytest -v
```

---

## Скриншоты

### 1. Swagger Auth Service (регистрация, логин, /auth/me)

### Регистрация пользователя
![Регистрация](screenshots/Swagger_register_1.png)
![Регистрация](screenshots/Swagger_register_2.png)

### Login
![Login](screenshots/Swagger_login_1.png)
![Login](screenshots/Swagger_login_2.png)

### /auth/me
![Me](screenshots/Swagger_me.png)


### 2. Telegram-бот

![Telegram](screenshots/Telegram_1.png)
![Telegram](screenshots/Telegram.png)


### 3. RabbitMQ интерфейс

![RabbitMQ](screenshots/RabbitMQ.png)


### 4. Тестирование

![Test_auth](screenshots/Test_auth.png)
![Test_bot](screenshots/Test_bot.png)


---

## Остановка проекта

```bash
docker-compose down
```

Для остановки с удалением всех данных (базы, очереди):

```bash
docker-compose down -v
```

---

## Используемые технологии

| Компонент | Технология | Версия |
|-----------|------------|--------|
| Auth Service | FastAPI | 0.136+ |
| Bot Service | aiogram | 3.28+ |
| Очередь | Celery + RabbitMQ | 5.6+ |
| Кэш | Redis | 7+ |
| База данных | SQLite | 3+ |
| HTTP клиент | httpx | 0.27+ |
| Контейнеризация | Docker | 24.0+ |
| Оркестрация | Docker Compose | 2.20+ |
