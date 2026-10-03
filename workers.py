"""
لایه‌ی پردازش پس‌زمینه (Workers).

هر کلاس اینجا یک QObject است که قرار است داخل یک QThread جدا اجرا شود
تا رابط کاربری هنگام صحبت با API فریز نشود. این فایل هیچ وابستگی‌ای
به رابط کاربری ندارد و فقط با api_client.py صحبت می‌کند.
"""

from PySide6.QtCore import QObject, Signal

from api_client import get_chat_response, generate_chat_title, detect_project_color


class SuggestionWorker(QObject):
    """پاسخ اصلی (پیشنهاد پروژه) را از مدل انتخاب‌شده می‌گیرد."""

    finished = Signal(bool, str)  # (success, content_or_error)

    def __init__(self, messages: list, model_id: str):
        super().__init__()
        self.messages = messages
        self.model_id = model_id

    def run(self):
        try:
            success, content = get_chat_response(self.messages, self.model_id)
        except Exception as e:
            success, content = False, f"خطا در دریافت پاسخ از سرویس:\nخطای داخلی برنامه: {str(e)}"
        self.finished.emit(success, content)


class TitleWorker(QObject):
    """یک عنوان کوتاه برای گفتگوی تازه‌ساخته‌شده تولید می‌کند."""

    finished = Signal(str, str)  # (title, chat_id)

    def __init__(self, user_message: str, chat_id: str):
        super().__init__()
        self.user_message = user_message
        self.chat_id = chat_id

    def run(self):
        title = generate_chat_title(self.user_message)
        self.finished.emit(title, self.chat_id)


class ColorWorker(QObject):
    """موضوع پروژه را تشخیص داده و یک کد رنگ HEX برمی‌گرداند."""

    finished = Signal(str, str)  # (color_hex, chat_id)

    def __init__(self, project_text: str, chat_id: str):
        super().__init__()
        self.project_text = project_text
        self.chat_id = chat_id

    def run(self):
        color_hex = detect_project_color(self.project_text)
        self.finished.emit(color_hex, self.chat_id)