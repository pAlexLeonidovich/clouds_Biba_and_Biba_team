# Лаба 0 — Инструкция по запуску

Сервис профиля Steam с кастомным бэкендом и базой данных для стены комментариев. Используется как базовый сервис для последующих лабораторных работ (Nginx, Docker, CI/CD).

## Требования

* Python 3.10+
* Docker Desktop (для запуска PostgreSQL) или локально установленный PostgreSQL 14+

---

## 1. Настройка базы данных

Запуск сетевого инстанса PostgreSQL в Docker:

```bash
docker run --name steam-postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=steam_db -p 5432:5432 -d postgres:15
```

Проверка статуса работы контейнера:

```bash
docker ps
```

Параметры подключения по умолчанию:
* **Host:** `localhost`
* **Port:** `5432`
* **Database:** `steam_db`
* **User:** `postgres`
* **Password:** `postgres`

При необходимости параметры можно переопределить через переменные окружения:

```bash
# Linux/macOS
export DB_HOST="localhost"
export DB_PORT="5432"
export DB_NAME="steam_db"
export DB_USER="postgres"
export DB_PASSWORD="postgres"

# Windows (PowerShell)
$env:DB_HOST="localhost"
$env:DB_PORT="5432"
$env:DB_NAME="steam_db"
$env:DB_USER="postgres"
$env:DB_PASSWORD="postgres"
```

---

## 2. Установка зависимостей

Переход в папку бэкенда:

```bash
cd backend
```

Создание и активация виртуального окружения:

```bash
# Создание venv
python -m venv venv

# Активация (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Активация (Linux/macOS)
source venv/bin/activate
```

Установка библиотек:

```bash
pip install -r requirements.txt
```

---

## 3. Запуск приложения

Таблица `comments` в базе данных создается автоматически при первом запуске приложения.

Запуск сервера Uvicorn:

```bash
uvicorn main:app --reload --port 8000
```

Сервер доступен по адресу: `http://localhost:8000`

---

## 4. Проверка работоспособности

### Проверка API через терминал

Проверка здоровья сервиса и подключения к БД:

```bash
curl http://localhost:8000/api/health
# {"status":"ok","backend":"backend-1","db":"connected"}
```

Получение списка комментариев:

```bash
curl http://localhost:8000/api/comments
# []
```

### Проверка через веб-интерфейс

1. Открыть браузер по адресу: `http://localhost:8000/`
2. Ввести имя автора и текст комментария в форме внизу страницы.
3. Нажать кнопку **«ОТПРАВИТЬ»**.
4. Убедиться, что комментарий отобразился в списке.
5. Перезагрузить страницу (`F5`) — комментарий должен остаться на месте, подтверждая успешное чтение данных из PostgreSQL.