import os
import psycopg2
from psycopg2 import pool
from fastapi import FastAPI, Response, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Steam Profile DevOps API")

# --- КОНФИГУРАЦИЯ ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ (для Лабы 2 Docker Compose) ---
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "steam_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASSWORD", "postgres")

# Идентификатор инстанса (нужен для доказательства балансировки в Лабе 1)
INSTANCE_ID = os.getenv("INSTANCE_ID", os.getenv("HOSTNAME", "backend-1"))

# --- ПУЛ ПОДКЛЮЧЕНИЙ К БД (устойчив к падению БД в Лабе 2 со звездочкой) ---
try:
    db_pool = psycopg2.pool.SimpleConnectionPool(
        minconn=1, maxconn=10,
        host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASS
    )
except Exception as e:
    print(f"⚠️ Ошибка начального подключения к БД: {e}")
    db_pool = None

def get_db():
    global db_pool
    if db_pool is None:
        db_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1, maxconn=10,
            host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASS
        )
    conn = db_pool.getconn()
    return conn

def release_db(conn):
    if db_pool:
        db_pool.putconn(conn)

# Автоматически создаем таблицу comments при старте сервера
@app.on_event("startup")
def init_db():
    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS comments (
                    id SERIAL PRIMARY KEY,
                    author VARCHAR(100) NOT NULL,
                    text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
        release_db(conn)
        print("✅ Таблица comments успешно проверена/создана в PostgreSQL")
    except Exception as e:
        print(f"⚠️ Не удалось создать таблицу: {e}")

# Добавляем в заголовок ответа ID инстанса (требование Лабы 1)
@app.middleware("http")
async def add_instance_header(request, call_next):
    response = await call_next(request)
    response.headers["X-Backend-Server"] = INSTANCE_ID
    return response

# --- МОДЕЛЬ ДАННЫХ ---
class CommentCreate(BaseModel):
    author: str
    text: str

# --- API ЭНДПОИНТЫ ---

# 1. Healthcheck (проверка готовности для Docker и CI/CD)
@app.get("/api/health")
def health():
    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
        release_db(conn)
        return {"status": "ok", "backend": INSTANCE_ID, "db": "connected"}
    except Exception:
        return Response(content='{"status": "unhealthy"}', status_code=503)

# 2. Получение списка комментариев (READ)
@app.get("/api/comments")
def get_comments():
    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, author, text, to_char(created_at, 'DD.MM.YYYY HH24:MI') 
                FROM comments 
                ORDER BY id DESC;
            """)
            rows = cur.fetchall()
        release_db(conn)
        return [{"id": r[0], "author": r[1], "text": r[2], "date": r[3]} for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 3. Добавление комментария (WRITE)
@app.post("/api/comments")
def add_comment(comment: CommentCreate):
    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO comments (author, text) VALUES (%s, %s);",
                (comment.author, comment.text)
            )
            conn.commit()
        release_db(conn)
        return {"status": "created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- РАЗДАЧА СТАТИКИ ФРОНТЕНДА ---
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

# Прямой маршрут на главную страницу (железобетонно отдает index.html)
@app.get("/")
def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

# Раздача остальных файлов (стилей, картинок из index_files)
app.mount("/", StaticFiles(directory=FRONTEND_DIR), name="frontend")