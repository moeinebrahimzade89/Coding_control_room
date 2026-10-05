"""
مدیر اعلان‌های سیستم‌عامل (OS Notification Manager)
مسیر: utils/notification_manager.py
---------------------------------------------------
وظیفه این کلاس ارتباط با سیستم‌عامل برای ارسال نوتفیکیشن‌های بومی (Native) است.
این فایل از الگوی Dependency Injection پیروی می‌کند و پنجره اصلی را می‌گیرد
تا وضعیت آن (مینیمایز بودن) را بررسی کرده و در صورت نیاز آن را بازیابی کند.
"""

import os
from PySide6.QtCore import QObject
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication, QStyle

# پیدا کردن مسیر ریشه پروژه به صورت داینامیک
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
LOGO_PATH = os.path.join(PROJECT_ROOT, "resources", "logo", "logo.png")


class NotificationManager(QObject):
    def __init__(self, main_window):
        # QObject بودن باعث می‌شود بتوانیم از سیستم سیگنال‌های کیوت استفاده کنیم
        super().__init__(main_window)
        self.mw = main_window
        
        # ۱. ساخت شیء System Tray (آیکون کنار ساعت ویندوز)
        self.tray_icon = QSystemTrayIcon(self)
        
        # ۲. تنظیم آیکون اختصاصی برنامه برای System Tray و نوتفیکیشن
        self.app_icon = QIcon(LOGO_PATH)
        
        # اگر فایل لوگو پیدا نشد، از آیکون پیش‌فرض ویندوز استفاده می‌کنیم تا برنامه خطا ندهد
        if self.app_icon.isNull():
            fallback_icon = self.mw.windowIcon()
            if fallback_icon.isNull():
                fallback_icon = QApplication.style().standardIcon(QStyle.SP_ComputerIcon)
            self.app_icon = fallback_icon
            
        self.tray_icon.setIcon(self.app_icon)
        
        # ۳. ساخت منوی کلیک راست برای آیکون کنار ساعت (توسعه‌پذیری)
        self._build_context_menu()
        
        # ۴. اتصال رویداد کلیک روی خود نوتفیکیشن
        # وقتی کاربر روی پیغامِ گوشه تصویر کلیک کند، برنامه باز می‌شود
        self.tray_icon.messageClicked.connect(self._restore_window)
        
        # ۵. نمایش آیکون در کنار ساعت
        self.tray_icon.show()

    def _build_context_menu(self):
        """ساخت منوی کلیک راست برای آیکون System Tray"""
        self.tray_menu = QMenu()
        
        # دکمه بازگردانی برنامه
        restore_action = self.tray_menu.addAction("نمایش اتاق فرمان")
        restore_action.triggered.connect(self._restore_window)
        
        self.tray_menu.addSeparator() # خط جداکننده
        
        # دکمه خروج کامل از برنامه
        quit_action = self.tray_menu.addAction("خروج از برنامه")
        quit_action.triggered.connect(QApplication.instance().quit)
        
        # اختصاص منو به آیکون
        self.tray_icon.setContextMenu(self.tray_menu)

    def notify_if_minimized(self, title: str, message: str, duration_ms: int = 3000):
        """
        ارسال نوتفیکیشن فقط در صورتی که برنامه مینیمایز شده باشد.
        
        پارامترها:
        title: تیتر نوتفیکیشن
        message: متن اصلی نوتفیکیشن
        duration_ms: مدت زمان نمایش روی صفحه (پیش‌فرض ۳ ثانیه)
        """
        # بررسی وضعیت پنجره: آیا مینیمایز است یا کاملاً مخفی شده؟
        if self.mw.isMinimized() or self.mw.isHidden():
            self.tray_icon.showMessage(
                title,
                message,
                self.app_icon, # استفاده از لوگوی اختصاصی برنامه به جای آیکون ساده اطلاعات
                duration_ms
            )

    def _restore_window(self):
        """
        بازگرداندن برنامه به حالت عادی (از مینیمایز) و آوردن آن به روی سایر پنجره‌ها.
        این تابع هم با کلیک روی منو و هم با کلیک روی نوتفیکیشن کار می‌کند.
        """
        if self.mw.isMinimized() or self.mw.isHidden():
            self.mw.showNormal()
        
        # فوکوس دادن به برنامه و آوردن آن به بالاترین لایه تصویر
        self.mw.activateWindow()
        self.mw.raise_()