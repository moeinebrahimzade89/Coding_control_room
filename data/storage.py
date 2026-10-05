"""
لایه مدیریت داده‌ها (Data Layer) - معماری لایه‌بندی شده (مسیر: data/storage.py)

ذخیره‌سازی تاریخچه گفتگوها و تنظیمات برنامه در دیتابیس SQLite برای سرعت و کارایی بالا.
هر گفتگو (chat) به عنوان یک ردیف ذخیره شده و پیام‌ها به صورت JSON در یک ستون نگهداری می‌شوند.
جدول settings نیز تنظیمات دلخواه کاربر (مانند فونت‌های مجزا، تم روشن/تاریک و رنگ مکمل) را حفظ می‌کند.
"""

import sqlite3
import json
import os
import uuid
from datetime import datetime

# ===================================================================
# تنظیمات مسیردهی
# ===================================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

# فایل دیتابیس اکنون به صورت مرتب در پوشه data ساخته و نگهداری می‌شود
DB_FILE = os.path.join(CURRENT_DIR, "chat_history.db")

def _get_connection():
    """ایجاد و بازگرداندن اتصال به دیتابیس."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """ساخت جداول در صورت عدم وجود و انتقال خودکار اطلاعات از JSON قدیمی."""
    with _get_connection() as conn:
        # ۱. ایجاد جدول چت‌ها
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
        
        # ۲. ایجاد جدول تنظیمات برنامه
        conn.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # اسکریپت مهاجرت (Migration) از JSON قدیمی (جستجو در ریشه پروژه)
        cursor = conn.execute("SELECT COUNT(*) FROM chats")
        if cursor.fetchone()[0] == 0:
            old_json = os.path.join(PROJECT_ROOT, "chat_history.json")
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


# ===================================================================
# بخش اول: مدیریت تنظیمات برنامه (Settings)
# ===================================================================

def get_setting(key: str, default_value: str = "") -> str:
    """یک تنظیم خاص را از دیتابیس می‌خواند؛ اگر وجود نداشت مقدار پیش‌فرض را برمی‌گرداند."""
    try:
        with _get_connection() as conn:
            cursor = conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                return row["value"]
    except sqlite3.Error:
        pass
    return default_value

def set_setting(key: str, value: str) -> None:
    """یک تنظیم را در دیتابیس ذخیره یا به‌روزرسانی می‌کند."""
    try:
        with _get_connection() as conn:
            conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    except sqlite3.Error:
        pass

# --- توابع کمکی برای مدیریت فونت‌ها ---

def get_ui_font() -> tuple:
    """فونت رابط کاربری را برمی‌گرداند. خروجی: (نام فونت, اندازه)"""
    family = get_setting("ui_font_family", "Segoe UI")
    size = get_setting("ui_font_size", "10") 
    return family, int(size)

def set_ui_font(family: str, size: int) -> None:
    """فونت رابط کاربری را ذخیره می‌کند."""
    set_setting("ui_font_family", family)
    set_setting("ui_font_size", str(size))

def get_chat_font() -> tuple:
    """فونت محیط گفتگو (وب) را برمی‌گرداند. خروجی: (نام فونت, اندازه)"""
    default_family, _ = get_ui_font()
    family = get_setting("chat_font_family", default_family)
    size = get_setting("chat_font_size", "15") 
    return family, int(size)

def set_chat_font(family: str, size: int) -> None:
    """فونت محیط گفتگو را ذخیره می‌کند."""
    set_setting("chat_font_family", family)
    set_setting("chat_font_size", str(size))

# --- توابع کمکی جدید برای مدیریت تم و رنگ مکمل ---

def get_theme_settings() -> tuple:
    """تم و رنگ مکمل برنامه را برمی‌گرداند. خروجی: (حالت تم, رنگ مکمل)"""
    theme_mode = get_setting("theme_mode", "dark") # گزینه‌ها: dark یا light
    accent_color = get_setting("accent_color", "red") # گزینه‌ها: red, blue, green, orange, yellow
    return theme_mode, accent_color

def set_theme_settings(theme_mode: str, accent_color: str) -> None:
    """تم و رنگ مکمل برنامه را ذخیره می‌کند."""
    set_setting("theme_mode", theme_mode)
    set_setting("accent_color", accent_color)


# ===================================================================
# بخش دوم: مدیریت تاریخچه چت‌ها (Chats)
# ===================================================================

def load_chats() -> list:
    """تمام گفتگوهای ذخیره‌شده را برمی‌گرداند (لیست دیکشنری)."""
    chats = []
    try:
        with _get_connection() as conn:
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