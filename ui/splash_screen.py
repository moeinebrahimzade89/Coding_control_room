"""
کامپوننت صفحه بارگذاری (Splash Screen)
مسیر: ui/splash_screen.py
---------------------------------------------------
این فایل یک پنجره‌ی بسیار سبک و سریع می‌سازد که بلافاصله پس از اجرای برنامه
نمایش داده می‌شود تا زمان لود شدن کامل رابط کاربری را پوشش دهد.
این صفحه کاملاً مستقل است تا هیچ تاخیری در پردازش نداشته باشد.
"""

import os
import datetime
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication, QGraphicsDropShadowEffect

from data import storage

# یافتن مسیر ریشه پروژه و فایل لوگو به صورت داینامیک
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
LOGO_PATH = os.path.join(PROJECT_ROOT, "resources", "logo", "logo.png")


class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        
        # تنظیمات پنجره: بدون حاشیه، همیشه روی صفحه، و با رفتار اختصاصی اسپلش اسکرین
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.SplashScreen
        )
        
        # پس‌زمینه شفاف کل پنجره (برای ایجاد گوشه‌های گرد و سایه لایه داخلی)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # اندازه ثابت پنجره بارگذاری
        self.setFixedSize(300, 300)
        
        self._build_ui()

    def _build_ui(self):
        # ۱. محاسبه سریع تم برای انتخاب رنگ پس‌زمینه
        bg_color = self._get_fast_theme_color()
        
        # لایه اصلی
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # ۲. فریم نگهدارنده مرکزی (برای اعمال استایل، رنگ و گوشه‌های گرد)
        self.container = QWidget(self)
        self.container.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border-radius: 20px;
            }}
        """)
        
        # ۳. افزودن سایه نرم (Drop Shadow) برای مدرن شدن ظاهر صفحه
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 8)
        self.container.setGraphicsEffect(shadow)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        
        # ۴. برچسب (Label) مربوط به لوگو
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setStyleSheet("background: transparent;")
        
        # ۵. بارگذاری و تنظیم سایز لوگو با بالاترین کیفیت
        if os.path.exists(LOGO_PATH):
            pixmap = QPixmap(LOGO_PATH)
            if not pixmap.isNull():
                # تغییر سایز نرم و باکیفیت لوگو (Anti-aliasing)
                scaled_pixmap = pixmap.scaled(
                    160, 160, 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.logo_label.setPixmap(scaled_pixmap)
        else:
            # اگر به هر دلیلی فایل لوگو پاک شده بود، برنامه کرش نمی‌کند
            self.logo_label.setText("LOGO")
            text_color = "white" if bg_color == "#1e1e1e" else "#111111"
            self.logo_label.setStyleSheet(f"color: {text_color}; font-size: 28px; font-weight: bold; background: transparent;")
            
        container_layout.addWidget(self.logo_label)
        main_layout.addWidget(self.container)

    def _get_fast_theme_color(self) -> str:
        """
        محاسبه فوق‌سریع رنگ پس‌زمینه بر اساس تنظیمات ذخیره شده.
        این کار بدون درگیر کردن و لود کردن ماژول‌های سنگین و CSSها انجام می‌شود
        تا اسپلش اسکرین در میلی‌ثانیه اول باز شود.
        """
        try:
            raw_mode, _ = storage.get_theme_settings()
        except Exception:
            raw_mode = "dark"
        
        if raw_mode == "light":
            return "#f5f5f5"
        elif raw_mode == "adaptive":
            hour = datetime.datetime.now().hour
            return "#f5f5f5" if 6 <= hour < 18 else "#1e1e1e"
        elif raw_mode == "system":
            # برای حالت سیستم، به سرعت از استایل سیستمی کیوت می‌خوانیم
            try:
                app = QApplication.instance()
                if app:
                    scheme = app.styleHints().colorScheme()
                    return "#1e1e1e" if scheme == Qt.ColorScheme.Dark else "#f5f5f5"
            except Exception:
                pass
        
        # پیش‌فرض همیشه تم تاریک است
        return "#1e1e1e"