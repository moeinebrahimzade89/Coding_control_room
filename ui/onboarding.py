"""
کامپوننت راه‌اندازی اولیه (Onboarding Wizard)
مسیر: ui/onboarding.py
---------------------------------------------------
این پنجره در اولین اجرای برنامه باز می‌شود تا تنظیمات پایه (تم، رنگ، کلیدهای API)
را از کاربر بگیرد و یک آموزش کوتاه تصویری ارائه دهد.
"""

import os
import datetime
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QWidget, QLineEdit, QGridLayout, QFrame, 
    QGraphicsDropShadowEffect, QApplication
)

from data import storage

class CustomWarningBox(QDialog):
    """یک دیالوگ خطای سفارشی و مدرن برای جایگزینی QMessageBox پیش‌فرض"""
    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(350)
        self.setLayoutDirection(Qt.RightToLeft)
        
        # حذف حاشیه‌های ویندوز و شفاف کردن پس‌زمینه دیالوگ
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        frame = QFrame(self)
        frame.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border: 2px solid #e5383b;
                border-radius: 10px;
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
                border: none;
            }
            QPushButton {
                background-color: #e5383b;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 25px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #ba1826;
            }
        """)
        
        # اضافه کردن سایه
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 4)
        frame.setGraphicsEffect(shadow)
        
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(20, 20, 20, 20)
        
        title_lbl = QLabel(f"⚠️ {title}")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffc300;")
        
        msg_lbl = QLabel(message)
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet("line-height: 1.5;")
        
        btn_ok = QPushButton("متوجه شدم")
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.clicked.connect(self.accept)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)
        btn_layout.addWidget(btn_ok)
        
        frame_layout.addWidget(title_lbl)
        frame_layout.addSpacing(10)
        frame_layout.addWidget(msg_lbl)
        frame_layout.addSpacing(15)
        frame_layout.addLayout(btn_layout)
        
        layout.addWidget(frame)


class OnboardingWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("خوش آمدید")
        self.resize(750, 500)
        self.setLayoutDirection(Qt.RightToLeft)
        
        # حذف حاشیه‌های پیش‌فرض ویندوز برای طراحی مدرن‌تر
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # متغیرهای موقت برای ذخیره انتخاب‌های کاربر
        self.selected_theme = "dark"
        self.selected_color = "red"

        self._build_ui()
        # اعمال تم اولیه (تاریک)
        self._apply_theme_style("dark")

    def _apply_theme_style(self, mode):
        """اعمال پویا و لحظه‌ای استایل بر اساس تم انتخابی کاربر"""
        if mode == "dark":
            bg_color = "#1e1e1e"
            panel_color = "#2a2a2a"
            text_color = "#ffffff"
            subtext_color = "#aaaaaa"
            border_color = "#444444"
        else:
            bg_color = "#f5f5f5"
            panel_color = "#ffffff"
            text_color = "#111111"
            subtext_color = "#555555"
            border_color = "#cccccc"

        self.setStyleSheet(f"""
            QDialog {{ background: transparent; }}
            QFrame#mainFrame {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 12px;
            }}
            QLabel {{
                color: {text_color};
                font-size: 14px;
            }}
            QLabel#titleLabel {{
                font-size: 22px;
                font-weight: bold;
                color: {text_color};
                margin-bottom: 10px;
            }}
            QLabel#subtitleLabel {{
                font-size: 14px;
                color: {subtext_color};
                margin-bottom: 20px;
            }}
            QPushButton {{
                background-color: {panel_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 6px;
                padding: 8px 15px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {border_color};
            }}
            QPushButton#primaryBtn {{
                background-color: #e5383b;
                color: white;
                border: none;
            }}
            QPushButton#primaryBtn:hover {{
                background-color: #ba1826;
            }}
            QLineEdit {{
                background-color: {panel_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 6px;
                padding: 10px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 1px solid #e5383b;
            }}
        """)

    def _build_ui(self):
        # فریم اصلی با گوشه‌های گرد و سایه
        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("mainFrame")
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 5)
        self.main_frame.setGraphicsEffect(shadow)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.addWidget(self.main_frame)

        frame_layout = QVBoxLayout(self.main_frame)
        frame_layout.setContentsMargins(30, 30, 30, 20)

        # استک برای اسلایدها
        self.stack = QStackedWidget()
        frame_layout.addWidget(self.stack)

        # ساخت اسلایدها
        self.stack.addWidget(self._build_theme_slide())
        self.stack.addWidget(self._build_color_slide())
        self.stack.addWidget(self._build_api_slide())
        self.stack.addWidget(self._build_tutorial_slide())

        # نوار پایین (دکمه‌های ناوبری)
        nav_layout = QHBoxLayout()
        
        self.btn_prev = QPushButton("مرحله قبل")
        self.btn_prev.clicked.connect(self._prev_slide)
        self.btn_prev.hide() # در اسلاید اول مخفی است
        
        self.btn_skip = QPushButton("رد کردن")
        self.btn_skip.clicked.connect(self._skip_slide)
        
        self.btn_next = QPushButton("مرحله بعد")
        self.btn_next.setObjectName("primaryBtn")
        self.btn_next.clicked.connect(self._next_slide)

        nav_layout.addWidget(self.btn_prev)
        nav_layout.addStretch(1)
        nav_layout.addWidget(self.btn_skip)
        nav_layout.addWidget(self.btn_next)

        frame_layout.addLayout(nav_layout)
        
        self.stack.currentChanged.connect(self._update_nav_buttons)

    # ==========================================
    # اسلاید ۱: انتخاب تم
    # ==========================================
    def _build_theme_slide(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title = QLabel("قدم اول: انتخاب پوسته")
        title.setObjectName("titleLabel")
        subtitle = QLabel("ترجیح می‌دهید در چه محیطی کار کنید؟ (بعداً قابل تغییر است)")
        subtitle.setObjectName("subtitleLabel")
        
        layout.addWidget(title, alignment=Qt.AlignCenter)
        layout.addWidget(subtitle, alignment=Qt.AlignCenter)
        layout.addStretch(1)

        grid = QGridLayout()
        grid.setSpacing(20)

        self.btn_dark = QPushButton("🌙 محیط تاریک")
        self.btn_dark.setFixedSize(180, 110)
        
        self.btn_light = QPushButton("☀️ محیط روشن")
        self.btn_light.setFixedSize(180, 110)

        self.btn_system = QPushButton("💻 سیستمی")
        self.btn_system.setFixedSize(180, 110)

        self.btn_adaptive = QPushButton("⏳ تطبیقی (ساعت)")
        self.btn_adaptive.setFixedSize(180, 110)

        self.btn_dark.clicked.connect(lambda: self._select_theme("dark"))
        self.btn_light.clicked.connect(lambda: self._select_theme("light"))
        self.btn_system.clicked.connect(lambda: self._select_theme("system"))
        self.btn_adaptive.clicked.connect(lambda: self._select_theme("adaptive"))

        grid.addWidget(self.btn_dark, 0, 0)
        grid.addWidget(self.btn_light, 0, 1)
        grid.addWidget(self.btn_system, 1, 0)
        grid.addWidget(self.btn_adaptive, 1, 1)

        grid_widget = QWidget()
        grid_widget.setLayout(grid)
        
        h_layout = QHBoxLayout()
        h_layout.addStretch(1)
        h_layout.addWidget(grid_widget)
        h_layout.addStretch(1)
        
        layout.addLayout(h_layout)
        layout.addStretch(1)
        
        # مقداردهی اولیه استایل دکمه‌ها
        self._select_theme("dark")
        return widget

    def _select_theme(self, mode):
        self.selected_theme = mode
        
        # محاسبه تم واقعی برای پیش‌نمایش در حالت سیستم یا تطبیقی
        preview_mode = mode
        if mode == "adaptive":
            hour = datetime.datetime.now().hour
            preview_mode = "light" if 6 <= hour < 18 else "dark"
        elif mode == "system":
            scheme = QApplication.styleHints().colorScheme()
            preview_mode = "dark" if scheme == Qt.ColorScheme.Dark else "light"
            
        self._apply_theme_style(preview_mode) # تغییر زنده استایل کل پنجره
        
        # استایل‌های پایه برای دکمه‌ها
        unselected_dark = "font-size: 16px; background-color: #2a2a2a; color: white; border: 2px solid transparent; border-radius: 10px;"
        unselected_light = "font-size: 16px; background-color: #f0f0f0; color: #111111; border: 2px solid transparent; border-radius: 10px;"
        selected_border = "border: 2px solid #e5383b;"
        
        # بروزرسانی ظاهر هر ۴ دکمه
        self.btn_dark.setStyleSheet(unselected_dark + (selected_border if mode == "dark" else ""))
        self.btn_light.setStyleSheet(unselected_light + (selected_border if mode == "light" else ""))
        self.btn_system.setStyleSheet(unselected_dark + (selected_border if mode == "system" else ""))
        self.btn_adaptive.setStyleSheet(unselected_dark + (selected_border if mode == "adaptive" else ""))

    # ==========================================
    # اسلاید ۲: انتخاب رنگ سیستم
    # ==========================================
    def _build_color_slide(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title = QLabel("قدم دوم: رنگ سیستم")
        title.setObjectName("titleLabel")
        subtitle = QLabel("رنگ اصلی دکمه‌ها و المان‌های برنامه را انتخاب کنید.")
        subtitle.setObjectName("subtitleLabel")
        
        layout.addWidget(title, alignment=Qt.AlignCenter)
        layout.addWidget(subtitle, alignment=Qt.AlignCenter)
        layout.addStretch(1)

        grid = QGridLayout()
        grid.setSpacing(10)
        
        # به‌روزرسانی رنگ‌ها با کدهای HEX مدرن و جدید
        colors = [
            ("قرمز", "red", "#e5383b"), ("آبی", "blue", "#3b82f6"),
            ("سبز", "green", "#10b981"), ("نارنجی", "orange", "#fb923c"),
            ("زرد", "yellow", "#eab308"), ("بنفش", "purple", "#a855f7"),
            ("صورتی", "pink", "#ec4899"), ("مشکی", "black", "#3f3f46"),
            ("قهوه‌ای", "brown", "#92400e"), ("سرمه‌ای", "navy", "#1e3a8a")
        ]
        
        self.color_btns = {}
        row, col = 0, 0
        for name, key, hex_code in colors:
            btn = QPushButton(name)
            btn.setFixedSize(110, 55)
            btn.setStyleSheet(f"background-color: {hex_code}; color: white; font-size: 16px; border: none; border-radius: 6px;")
            btn.clicked.connect(lambda checked=False, k=key, b=btn: self._select_color(k, b))
            grid.addWidget(btn, row, col)
            self.color_btns[key] = btn
            
            col += 1
            if col > 4: # تنظیم برای ۵ ستون و ۲ ردیف
                col = 0
                row += 1
                
        # انتخاب پیش‌فرض
        self._select_color("red", self.color_btns["red"])

        grid_widget = QWidget()
        grid_widget.setLayout(grid)
        
        h_layout = QHBoxLayout()
        h_layout.addStretch(1)
        h_layout.addWidget(grid_widget)
        h_layout.addStretch(1)
        
        layout.addLayout(h_layout)
        layout.addStretch(1)
        return widget

    def _select_color(self, key, active_btn):
        self.selected_color = key
        for k, btn in self.color_btns.items():
            if btn == active_btn:
                btn.setStyleSheet(btn.styleSheet() + "border: 3px solid white;")
            else:
                btn.setStyleSheet(btn.styleSheet().replace("border: 3px solid white;", "border: none;"))

    # ==========================================
    # اسلاید ۳: کلیدهای API
    # ==========================================
    def _build_api_slide(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title = QLabel("قدم سوم: اتصال به هوش مصنوعی")
        title.setObjectName("titleLabel")
        subtitle = QLabel("کلیدهای API خود را وارد کنید. (اگر کلید ندارید، دکمه «رد کردن» را بزنید)")
        subtitle.setObjectName("subtitleLabel")
        
        layout.addWidget(title, alignment=Qt.AlignCenter)
        layout.addWidget(subtitle, alignment=Qt.AlignCenter)
        layout.addStretch(1)
        
        form_layout = QVBoxLayout()
        form_layout.setSpacing(15)
        
        lbl_main = QLabel("کلید اصلی (OpenAI / Deepseek / ...):")
        self.api_main = QLineEdit()
        self.api_main.setEchoMode(QLineEdit.Password)
        self.api_main.setPlaceholderText("sk-...")
        self.api_main.setLayoutDirection(Qt.LeftToRight)
        
        lbl_groq = QLabel("کلید جایگزین (Groq API):")
        self.api_groq = QLineEdit()
        self.api_groq.setEchoMode(QLineEdit.Password)
        self.api_groq.setPlaceholderText("gsk_...")
        self.api_groq.setLayoutDirection(Qt.LeftToRight)

        form_layout.addWidget(lbl_main)
        form_layout.addWidget(self.api_main)
        form_layout.addWidget(lbl_groq)
        form_layout.addWidget(self.api_groq)

        h_form = QHBoxLayout()
        h_form.addStretch(1)
        form_container = QWidget()
        form_container.setLayout(form_layout)
        form_container.setFixedWidth(400)
        h_form.addWidget(form_container)
        h_form.addStretch(1)

        layout.addLayout(h_form)
        layout.addStretch(1)
        return widget

    # ==========================================
    # اسلاید ۴: آموزش سریع
    # ==========================================
    def _build_tutorial_slide(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title = QLabel("آموزش سریع و کاربردی 🚀")
        title.setObjectName("titleLabel")
        layout.addWidget(title, alignment=Qt.AlignCenter)
        layout.addSpacing(20)

        grid = QGridLayout()
        grid.setSpacing(20)

        tutorials = [
            ("🧠 انتخاب مدل", "از منوی کشویی بالای صفحه می‌توانید مدل‌های مختلف (مثل Claude یا Groq) را انتخاب کنید."),
            ("💻 زبان برنامه‌نویسی", "زبان پروژه خود را از منوی بالا انتخاب کنید تا هوش مصنوعی پاسخ را متناسب با آن تنظیم کند."),
            ("📚 پنل گفتگوها (سایدبار)", "با کلیک روی نوار سمت راست یا فشردن Ctrl+Alt+H تاریخچه چت‌های خود را ببینید."),
            ("⚙️ تنظیمات پیشرفته", "آیکون چرخ‌دنده در پایین صفحه (یا Ctrl+Alt+S) برای تغییر فونت، تم و مسیر ذخیره فایل‌ها است.")
        ]

        row = 0
        for header, desc in tutorials:
            h_lbl = QLabel(header)
            h_lbl.setStyleSheet("font-weight: bold; font-size: 16px; color: #e5383b;")
            
            d_lbl = QLabel(desc)
            d_lbl.setWordWrap(True)
            # رفع مشکل نصفه شدن متن با حذف تراز اجباری
            d_lbl.setStyleSheet("color: #888888; font-size: 14px;")
            
            grid.addWidget(h_lbl, row, 0, alignment=Qt.AlignTop | Qt.AlignRight)
            grid.addWidget(d_lbl, row, 1, alignment=Qt.AlignTop) # اجازه گسترش متن در عرض
            row += 1

        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)
        layout.addStretch(1)
        return widget

    # ==========================================
    # منطق ناوبری و ذخیره‌سازی
    # ==========================================
    def _update_nav_buttons(self, index):
        self.btn_prev.setVisible(index > 0)
        
        if index == self.stack.count() - 1:
            self.btn_next.setText("شروع کار با برنامه ✔️")
            self.btn_skip.hide()
        else:
            self.btn_next.setText("مرحله بعد")
            self.btn_skip.show()

    def _prev_slide(self):
        current = self.stack.currentIndex()
        if current > 0:
            self.stack.setCurrentIndex(current - 1)

    def _skip_slide(self):
        """بدون اعتبارسنجی مستقیماً به اسلاید بعد می‌رود"""
        current = self.stack.currentIndex()
        if current < self.stack.count() - 1:
            self.stack.setCurrentIndex(current + 1)
        else:
            self._save_all_and_finish()

    def _next_slide(self):
        current = self.stack.currentIndex()
        
        # استفاده از دیالوگ سفارشی به جای QMessageBox پیش‌فرض
        if current == 2:
            main_key = self.api_main.text().strip()
            if not main_key:
                warning_box = CustomWarningBox(
                    "اخطار اعتبارسنجی",
                    "لطفاً کلید API خود را وارد کنید.\n\nاگر در حال حاضر کلیدی ندارید، می‌توانید به جای «مرحله بعد» دکمه‌ی «رد کردن» را بزنید تا تنظیمات را بعداً انجام دهید.",
                    self
                )
                warning_box.exec()
                return

        # ذخیره اطلاعات در مرحله آخر
        if current == self.stack.count() - 1:
            self._save_all_and_finish()
        else:
            self.stack.setCurrentIndex(current + 1)

    def _save_all_and_finish(self):
        """ذخیره تمام اطلاعات در دیتابیس و بستن دیالوگ"""
        # ذخیره تم و رنگ
        storage.set_theme_settings(self.selected_theme, self.selected_color)
        
        # ذخیره کلیدهای API (اگر وارد شده باشند)
        main_key = self.api_main.text().strip()
        groq_key = self.api_groq.text().strip()
        
        if main_key: storage.set_setting("user_main_api_key", main_key)
        if groq_key: storage.set_setting("user_groq_api_key", groq_key)
        
        # ثبت اینکه Onboarding انجام شده است
        storage.set_setting("is_first_run", "False")
        
        self.accept() # بستن دیالوگ و ادامه اجرای برنامه