"""
ذخیره‌سازی تاریخچه گفتگوها در دیتابیس SQLite برای سرعت و کارایی بالا.
هر گفتگو (chat) به عنوان یک ردیف ذخیره شده و پیام‌ها به صورت JSON در یک ستون نگهداری می‌شوند.
"""

import sqlite3
import json
import os
import uuid
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat_history.db")

def _get_connection():
    """ایجاد و بازگرداندن اتصال به دیتابیس."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """ساخت جداول در صورت عدم وجود و انتقال خودکار اطلاعات از JSON قدیمی."""
    with _get_connection() as conn:
        # ایجاد جدول
        conn.execute('''
            CREATE TABLE IF NOT EXISTS chats (
                id TEXT PRIMARY KEY,
                language TEXT,
                model TEXT,
                title TEXT,
                color TEXT,
                created_at TEXT,
                messages TEXT
            )
        ''')
        
        # اسکریپت مهاجرت (Migration) از JSON به دیتابیس
        cursor = conn.execute("SELECT COUNT(*) FROM chats")
        if cursor.fetchone()[0] == 0:
            old_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat_history.json")
            if os.path.exists(old_json):
                try:
                    with open(old_json, "r", encoding="utf-8") as f:
                        old_chats = json.load(f)
                    
                    for c in old_chats:
                        conn.execute(
                            "INSERT INTO chats (id, language, model, title, color, created_at, messages) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (
                                c.get("id", str(uuid.uuid4())), 
                                c.get("language", "Unknown"), 
                                c.get("model", "Deepseek"), 
                                c.get("title", "بدون عنوان"), 
                                c.get("color", "#808080"), 
                                c.get("created_at", datetime.now().isoformat(timespec="seconds")), 
                                json.dumps(c.get("messages", []), ensure_ascii=False)
                            )
                        )
                    # تغییر نام فایل قدیمی برای جلوگیری از اجرای مجدد مهاجرت
                    os.rename(old_json, old_json + ".backup")
                except Exception:
                    pass

# اجرای ساختار دیتابیس در زمان ایمپورت شدن
init_db()


def load_chats() -> list:
    """تمام گفتگوهای ذخیره‌شده را برمی‌گرداند (لیست دیکشنری)."""
    chats = []
    try:
        with _get_connection() as conn:
            # واکشی به ترتیب زمان
            rows = conn.execute("SELECT * FROM chats ORDER BY created_at ASC").fetchall()
            for row in rows:
                chat = dict(row)
                chat["messages"] = json.loads(chat["messages"]) if chat["messages"] else []
                chats.append(chat)
    except sqlite3.Error:
        pass
    return chats


def create_chat(language: str, model: str, title: str = "در حال تولید نام...") -> dict:
    """یک گفتگوی جدید ساخته و در دیتابیس درج می‌کند."""
    chat_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat(timespec="seconds")
    color = "#808080"
    
    chat_dict = {
        "id": chat_id,
        "language": language,
        "model": model,
        "title": title,
        "color": color,
        "created_at": created_at,
        "messages": []
    }
    
    try:
        with _get_connection() as conn:
            conn.execute(
                "INSERT INTO chats (id, language, model, title, color, created_at, messages) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (chat_id, language, model, title, color, created_at, "[]")
            )
    except sqlite3.Error:
        pass
        
    return chat_dict


def update_chat(chat: dict) -> None:
    """فقط یک گفتگوی خاص را (بدون دست زدن به بقیه تاریخچه) در دیتابیس آپدیت می‌کند."""
    try:
        with _get_connection() as conn:
            conn.execute(
                "UPDATE chats SET title = ?, color = ?, messages = ? WHERE id = ?",
                (chat["title"], chat["color"], json.dumps(chat["messages"], ensure_ascii=False), chat["id"])
            )
    except sqlite3.Error:
        pass


def delete_chat(chat_id: str) -> None:
    """یک گفتگو را بر اساس ID از دیتابیس حذف می‌کند."""
    try:
        with _get_connection() as conn:
            conn.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
    except sqlite3.Error:
        pass