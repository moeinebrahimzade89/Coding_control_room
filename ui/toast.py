"""
کامپوننت پیام شناور (Toast Notification)
مسیر: ui/toast.py
---------------------------------------------------
این کلاس یک ویجت شناور (Overlay Widget) است که برای نمایش پیام‌های کوتاه
(مانند "کپی شد") استفاده می‌شود.
این ویجت از هیچ Layoutای استفاده نمی‌کند، بنابراین می‌تواند آزادانه در
هر کجای پنجره مادر (MainWindow) قرار بگیرد و با افکت‌های نرم ظاهر و محو شود.
"""

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtWidgets import QLabel, QGraphicsOpacityEffect

class ToastNotification(QLabel):
    def __init__(self, parent):
        # والد این ویجت مستقیماً پنجره اصلی (MainWindow) خواهد بود
        super().__init__(parent)
        self.setObjectName("ToastMessage")
        self.setAlignment(Qt.AlignCenter)
        
        # ---------------------------------------------------------
        # ۱. استایل‌دهی پیام شناور (طراحی مدرن، تاریک و شیشه‌ای)
        # ---------------------------------------------------------
        self.setStyleSheet("""
            QLabel#ToastMessage {
                background-color: rgba(40, 40, 40, 230);
                color: #FFFFFF;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 10px 25px;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        
        # ---------------------------------------------------------
        # ۲. راه‌اندازی افکت شفافیت برای انیمیشن
        # ---------------------------------------------------------
        # چون این یک ویجت فرزند است، برای محو شدن به GraphicsEffect نیاز داریم
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0) # در ابتدا کاملاً نامرئی است
        
        self.hide()
        
        # ---------------------------------------------------------
        # ۳. تنظیمات انیمیشن و تایمر
        # ---------------------------------------------------------
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.anim.finished.connect(self._on_animation_finished)
        
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._fade_out)
        
        self._is_fading_out = False

    def show_message(self, text: str, duration: int = 2000):
        """
        نمایش پیام در مرکز صفحه.
        duration: مدت زمانی که پیام روی صفحه می‌ماند (بر حسب میلی‌ثانیه)
        """
        self.setText(text)
        self.adjustSize() # تنظیم خودکار ابعاد بر اساس طول متن
        
        # محاسبه مختصات برای قرارگیری دقیقاً در مرکز پنجره اصلی
        if self.parent():
            parent_rect = self.parent().rect()
            x = (parent_rect.width() - self.width()) // 2
            
            # قرار دادن در وسط (کمی متمایل به پایین برای زیبایی بیشتر)
            y = (parent_rect.height() - self.height()) // 2 + 60
            self.move(x, y)
            
        # آوردن ویجت به بالاترین لایه (روی بقیه ویجت‌ها)
        self.raise_()
        self.show()
        
        # متوقف کردن هر انیمیشن قبلی و شروع انیمیشن ظاهر شدن (Fade In)
        self._is_fading_out = False
        self.anim.stop()
        self.anim.setDuration(250) # سرعت ظاهر شدن
        self.anim.setStartValue(self.opacity_effect.opacity())
        self.anim.setEndValue(1.0)
        self.anim.start()
        
        # شروع تایمر برای محو شدن
        self._timer.start(duration)

    def _fade_out(self):
        """آغاز انیمیشن محو شدن (Fade Out)"""
        self._is_fading_out = True
        self.anim.stop()
        self.anim.setDuration(400) # سرعت محو شدن (کمی کندتر از ظاهر شدن)
        self.anim.setStartValue(self.opacity_effect.opacity())
        self.anim.setEndValue(0.0)
        self.anim.start()

    def _on_animation_finished(self):
        """وقتی انیمیشن تمام شد، اگر در حال محو شدن بودیم، ویجت را کاملاً مخفی کن"""
        if self._is_fading_out:
            self.hide()