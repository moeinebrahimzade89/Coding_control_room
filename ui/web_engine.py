"""
لایه رابط کاربری (Presentation Layer) - معماری لایه‌بندی شده (مسیر: ui/web_engine.py)

مسئولیت: مدیریت رفتار موتور کرومیوم تعبیه‌شده در برنامه (QWebEnginePage).
این کلاس مسئول رهگیری کلیک‌ها روی لینک‌ها و دکمه‌های عملیاتی داخل محیط وب و تبدیل آن‌ها به سیگنال‌های پایتونی است.
"""

from PySide6.QtCore import Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWebEngineCore import QWebEnginePage


class CustomWebPage(QWebEnginePage):
    # سیگنال برای ارسال دستورات اکشن (مثل کپی، تولید PDF، پردازش مجدد، شاخه جدید) به همراه شماره پیام
    action_requested = Signal(str, int)

    def acceptNavigationRequest(self, url, _type, isMainFrame):
        """
        این متد هر بار که در محیط وب روی یک لینک کلیک می‌شود فراخوانی می‌گردد.
        ما از این رفتار برای اجرای دستورات پایتون به جای باز کردن صفحات جدید استفاده می‌کنیم.
        """
        url_str = url.toString()
        
        # ۱. بررسی لینک‌های عملیاتی داخلی برنامه (مثل http://app.action/copy/2)
        if url_str.startswith("http://app.action/"):
            parts = url_str.split("/")
            if len(parts) >= 5:
                action = parts[3]    # نوع عملیات (مثلا copy، regen، pdf، branch)
                idx = int(parts[4])  # شماره (ایندکس) پیام در لیست گفتگو
                self.action_requested.emit(action, idx)
            return False  # با برگرداندن False جلوی رفتن مرورگر به این آدرس را می‌گیریم
            
        # ۲. باز کردن لینک‌های اینترنتی واقعی در مرورگر پیش‌فرض سیستم‌عامل کاربر (مثل کروم یا فایرفاکس)
        if url_str.startswith("http"):
            QDesktopServices.openUrl(url)
            return False
            
        # ۳. در سایر موارد (مثل لود شدن فایل‌های محلی CSS و JS) اجازه ناوبری را بده
        return super().acceptNavigationRequest(url, _type, isMainFrame)