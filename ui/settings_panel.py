"""
کامپوننت پنل تنظیمات کشویی (Sliding Drawer) - معماری لایه‌بندی شده (مسیر: ui/settings_panel.py)
مسئولیت‌ها:
۱. مدیریت انیمیشن باز و بسته شدن پنل.
۲. نمایش فیلدهای تنظیمات مجزا (رنگ، پوسته، رابط کاربری و محیط گفتگو).
۳. خواندن و ذخیره مستقیم تنظیمات در دیتابیس از طریق ماژول data.storage.
۴. ارسال سیگنال‌های تفکیک‌شده به main.py هنگام اعمال تغییرات.
۵. پشتیبانی از اضافه کردن رنگ سفارشی و تنظیم مسیر پیش‌فرض ذخیره فایل‌های PDF.
۶. مدیریت کلیدهای شخصی API کاربر و اطلاع‌رسانی به هسته شبکه.
"""

import os
import json

# تنظیم مسیر ریشه پروژه برای دسترسی به سایر پوشه‌ها
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

from PySide6.QtCore import (
    Qt, Signal, QPropertyAnimation, QParallelAnimationGroup, QEasingCurve, QSize, QTimer
)
from PySide6.QtGui import QPainter, QColor, QIcon
from PySide6.QtWidgets import (
    QFrame, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QSlider, QScrollArea, QColorDialog, QInputDialog, QLineEdit, QFileDialog
)

# ایمپورت‌ها بر اساس معماری جدید (اضافه شدن توابع تولید آیکون پویا و افزودن رنگ)
from data import storage
from ui.widgets import RIGHT, get_theme_icon, add_custom_accent

# مپ کردن نام‌های نمایشی به مقادیر داخلی
THEME_MAP = {
    "تاریک (Dark)": "dark",
    "روشن (Light)": "light",
    "سیستم (System)": "system",
    "تطبیقی (Adaptive)": "adaptive"
}
REV_THEME_MAP = {v: k for k, v in THEME_MAP.items()}

# لیست پایه‌ی رنگ‌ها
COLOR_MAP = {
    "قرمز (پیش‌فرض)": "red",
    "آبی": "blue",
    "سبز": "green",
    "نارنجی": "orange",
    "زرد": "yellow",
    "بنفش": "purple",
    "صورتی": "pink",
    "مشکی": "black",
    "قهوه‌ای": "brown",
    "سرمه‌ای": "navy"
}
REV_COLOR_MAP = {v: k for k, v in COLOR_MAP.items()}


class DiscreteSlider(QSlider):
    """نوار لغزان سفارشی با 5 نقطه و یک دستگیره برای انتخاب سایز"""
    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent)
        self.setMinimum(1)
        self.setMaximum(5)
        self.setCursor(Qt.PointingHandCursor)
        self.setLayoutDirection(Qt.LeftToRight)
        self.setStyleSheet("background: transparent;")
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        margin = 14
        usable_width = self.width() - 2 * margin
        y_center = self.height() // 2
        
        track_height = 6
        painter.setPen(Qt.NoPen)
        # رنگ پس‌زمینه مسیر لغزان
        painter.setBrush(QColor(150, 150, 150, 80)) 
        painter.drawRoundedRect(margin, y_center - track_height // 2, usable_width, track_height, 3, 3)
        
        steps = self.maximum() - self.minimum()
        dot_radius = 4
        for i in range(steps + 1):
            x = margin + int(i * usable_width / steps)
            painter.setBrush(QColor(150, 150, 150, 150)) 
            painter.drawEllipse(x - dot_radius, y_center - dot_radius, dot_radius * 2, dot_radius * 2)
            
        current_step = self.value() - self.minimum()
        handle_x = margin + int(current_step * usable_width / steps)
        handle_radius = 8
        
        # دستگیره با رنگی ثابت اما مشخص رسم می‌شود
        painter.setBrush(QColor(120, 120, 120))
        painter.drawEllipse(handle_x - handle_radius, y_center - handle_radius, handle_radius * 2, handle_radius * 2)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            margin = 14
            usable_width = self.width() - 2 * margin
            click_x = min(max(event.position().x() - margin, 0), usable_width)
            steps = self.maximum() - self.minimum()
            val = self.minimum() + round((click_x / usable_width) * steps)
            self.setValue(int(val))
            event.accept()
        else:
            super().mousePressEvent(event)
            
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            margin = 14
            usable_width = self.width() - 2 * margin
            click_x = min(max(event.position().x() - margin, 0), usable_width)
            steps = self.maximum() - self.minimum()
            val = self.minimum() + round((click_x / usable_width) * steps)
            self.setValue(int(val))
            event.accept()
        else:
            super().mouseMoveEvent(event)


class SettingsDrawer(QFrame):
    # سیگنال‌های تفکیک‌شده برای بخش‌های مختلف تنظیمات
    ui_font_changed = Signal(str)
    ui_font_size_changed = Signal(int)
    chat_font_changed = Signal(str)
    chat_font_size_changed = Signal(int)
    theme_mode_changed = Signal(str)      
    accent_color_changed = Signal(str)
    
    # سیگنال جدید برای اطلاع‌رسانی در مورد تغییر کلیدهای API
    api_keys_updated = Signal()

    def __init__(self, available_fonts: dict, parent=None):
        super().__init__(parent)
        self.available_fonts = available_fonts
        
        self.setObjectName("settingsPanel")
        self.setFixedWidth(50) 
        
        self.setLayoutDirection(Qt.RightToLeft)
        
        # نگهداری مقدار قبلی رنگ برای زمانی که کاربر دیالوگ را کنسل می‌کند
        self._prev_color_text = "قرمز (پیش‌فرض)"
        
        self._load_custom_colors_from_db()
        self._build_ui()
        self._load_saved_settings()

    def _load_custom_colors_from_db(self):
        """رنگ‌های سفارشی ذخیره شده در دیتابیس را خوانده و به پالت اضافه می‌کند"""
        customs_json = storage.get_setting("custom_accents", "{}")
        try:
            customs = json.loads(customs_json)
            for fa_name, hex_code in customs.items():
                internal_key = f"custom_{hex_code.replace('#', '')}"
                COLOR_MAP[fa_name] = internal_key
                REV_COLOR_MAP[internal_key] = fa_name
                add_custom_accent(internal_key, hex_code)
        except Exception:
            pass

    def update_icons(self, theme_mode: str):
        """تغییر پویا و لحظه‌ای رنگ آیکون چرخ‌دنده"""
        self.btn_open.setIcon(get_theme_icon("Settings.svg", theme_mode))

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # ==========================================
        # ۱. ویجت حالت بسته
        # ==========================================
        self.collapsed_widget = QWidget()
        self.collapsed_widget.setLayoutDirection(Qt.RightToLeft)
        
        col_layout = QVBoxLayout(self.collapsed_widget)
        col_layout.setContentsMargins(0, 0, 0, 20) 
        
        self.btn_open = QPushButton()
        self.btn_open.setObjectName("settingsToggleBtn")
        self.btn_open.setFixedSize(50, 50)
        self.btn_open.setCursor(Qt.PointingHandCursor)
        self.btn_open.setIconSize(QSize(24, 24))
        
        self.btn_open.clicked.connect(self.toggle_drawer)
        
        col_layout.addStretch(1)
        col_layout.addWidget(self.btn_open, alignment=Qt.AlignBottom | Qt.AlignHCenter)
        
        # ==========================================
        # ۲. ویجت حالت باز (همراه با ScrollArea)
        # ==========================================
        self.expanded_widget = QWidget()
        self.expanded_widget.setLayoutDirection(Qt.RightToLeft)
        self.expanded_widget.hide() 
        
        exp_layout = QVBoxLayout(self.expanded_widget)
        exp_layout.setContentsMargins(15, 15, 15, 15)
        exp_layout.setSpacing(15)
        
        header_layout = QHBoxLayout()
        title_label = QLabel("تنظیمات")
        title_label.setObjectName("activeChatLabel")
        title_label.setAlignment(RIGHT | Qt.AlignVCenter) 
        
        self.btn_close = QPushButton("✖")
        self.btn_close.setFixedSize(28, 28)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setObjectName("sortBtn")
        self.btn_close.clicked.connect(self.toggle_drawer)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(self.btn_close)
        exp_layout.addLayout(header_layout)

        # ایجاد اسکرول اریا برای محتوای تنظیمات
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("background: transparent;")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 5, 0)
        content_layout.setSpacing(15)
        
        # --- بخش تنظیمات پوسته و رنگ ---
        theme_title = QLabel("پوسته و رنگ:")
        theme_title.setObjectName("sectionTitle")
        content_layout.addWidget(theme_title)
        
        theme_mode_layout = QVBoxLayout()
        theme_mode_layout.setSpacing(8)
        theme_mode_label = QLabel("حالت نمایش:")
        theme_mode_label.setObjectName("fieldLabel")
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEME_MAP.keys()))
        self.theme_combo.setLayoutDirection(Qt.RightToLeft)
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        
        theme_mode_layout.addWidget(theme_mode_label)
        theme_mode_layout.addWidget(self.theme_combo)
        content_layout.addLayout(theme_mode_layout)

        accent_color_layout = QVBoxLayout()
        accent_color_layout.setSpacing(8)
        accent_color_label = QLabel("رنگ اصلی برنامه:")
        accent_color_label.setObjectName("fieldLabel")
        
        self.color_combo = QComboBox()
        self.color_combo.addItems(list(COLOR_MAP.keys()))
        self.color_combo.addItem("+ افزودن رنگ جدید...")
        self.color_combo.setLayoutDirection(Qt.RightToLeft)
        self.color_combo.currentTextChanged.connect(self._on_color_changed)
        
        accent_color_layout.addWidget(accent_color_label)
        accent_color_layout.addWidget(self.color_combo)
        content_layout.addLayout(accent_color_layout)

        # خط جداکننده
        divider1 = QFrame()
        divider1.setObjectName("divider")
        content_layout.addWidget(divider1)

        # --- بخش تنظیمات کلیدهای دسترسی (API Keys) ---
        api_title = QLabel("تنظیمات اتصال (API Keys):")
        api_title.setObjectName("sectionTitle")
        content_layout.addWidget(api_title)

        main_api_layout = QVBoxLayout()
        main_api_layout.setSpacing(8)
        main_api_label = QLabel("کلید اصلی (پیش‌فرض):")
        main_api_label.setObjectName("fieldLabel")
        
        self.main_api_input = QLineEdit()
        self.main_api_input.setEchoMode(QLineEdit.Password)
        self.main_api_input.setLayoutDirection(Qt.LeftToRight)
        self.main_api_input.setPlaceholderText("sk-...")
        self.main_api_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(128, 128, 128, 0.1);
                border: 1px solid rgba(128, 128, 128, 0.3);
                border-radius: 6px;
                padding: 6px;
                color: inherit;
            }
        """)
        main_api_layout.addWidget(main_api_label)
        main_api_layout.addWidget(self.main_api_input)
        content_layout.addLayout(main_api_layout)

        groq_api_layout = QVBoxLayout()
        groq_api_layout.setSpacing(8)
        groq_api_label = QLabel("کلید جایگزین (Groq):")
        groq_api_label.setObjectName("fieldLabel")
        
        self.groq_api_input = QLineEdit()
        self.groq_api_input.setEchoMode(QLineEdit.Password)
        self.groq_api_input.setLayoutDirection(Qt.LeftToRight)
        self.groq_api_input.setPlaceholderText("gsk_...")
        self.groq_api_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(128, 128, 128, 0.1);
                border: 1px solid rgba(128, 128, 128, 0.3);
                border-radius: 6px;
                padding: 6px;
                color: inherit;
            }
        """)
        groq_api_layout.addWidget(groq_api_label)
        groq_api_layout.addWidget(self.groq_api_input)
        content_layout.addLayout(groq_api_layout)

        # دکمه ذخیره کلیدها
        self.btn_save_keys = QPushButton("ذخیره کلیدها")
        self.btn_save_keys.setCursor(Qt.PointingHandCursor)
        self.btn_save_keys.setObjectName("sortBtn") 
        self.btn_save_keys.setStyleSheet("""
            QPushButton {
                background-color: rgba(128, 128, 128, 0.15);
                border: 1px solid rgba(128, 128, 128, 0.3);
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: rgba(128, 128, 128, 0.3);
            }
        """)
        self.btn_save_keys.clicked.connect(self._on_save_api_keys)
        content_layout.addWidget(self.btn_save_keys)

        # خط جداکننده
        divider_api = QFrame()
        divider_api.setObjectName("divider")
        content_layout.addWidget(divider_api)

        # --- بخش تنظیمات رابط کاربری (UI) ---
        ui_title = QLabel("قلم رابط کاربری:")
        ui_title.setObjectName("sectionTitle")
        content_layout.addWidget(ui_title)
        
        ui_font_layout = QVBoxLayout()
        ui_font_layout.setSpacing(8)
        ui_font_label = QLabel("فونت منوها:")
        ui_font_label.setObjectName("fieldLabel")
        
        self.ui_font_combo = QComboBox()
        self.ui_font_combo.addItems(list(self.available_fonts.keys()))
        self.ui_font_combo.setLayoutDirection(Qt.RightToLeft)
        self.ui_font_combo.currentTextChanged.connect(self._on_ui_font_selected)
        
        ui_font_layout.addWidget(ui_font_label)
        ui_font_layout.addWidget(self.ui_font_combo)
        content_layout.addLayout(ui_font_layout)
        
        ui_size_layout = QVBoxLayout()
        ui_size_layout.setSpacing(8)
        ui_size_label = QLabel("اندازه متون منوها:")
        ui_size_label.setObjectName("fieldLabel")
        
        self.ui_size_slider = DiscreteSlider()
        self.ui_size_slider.valueChanged.connect(self._on_ui_size_selected)
        self.ui_size_slider.setFixedHeight(30)
        
        ui_size_layout.addWidget(ui_size_label)
        ui_size_layout.addWidget(self.ui_size_slider)
        content_layout.addLayout(ui_size_layout)
        
        # خط جداکننده
        divider2 = QFrame()
        divider2.setObjectName("divider")
        content_layout.addWidget(divider2)
        
        # --- بخش تنظیمات محیط گفتگو (Chat) ---
        chat_title = QLabel("قلم محیط گفتگو:")
        chat_title.setObjectName("sectionTitle")
        content_layout.addWidget(chat_title)

        chat_font_layout = QVBoxLayout()
        chat_font_layout.setSpacing(8)
        chat_font_label = QLabel("فونت پیام‌ها:")
        chat_font_label.setObjectName("fieldLabel")
        
        self.chat_font_combo = QComboBox()
        self.chat_font_combo.addItems(list(self.available_fonts.keys()))
        self.chat_font_combo.setLayoutDirection(Qt.RightToLeft)
        self.chat_font_combo.currentTextChanged.connect(self._on_chat_font_selected)
        
        chat_font_layout.addWidget(chat_font_label)
        chat_font_layout.addWidget(self.chat_font_combo)
        content_layout.addLayout(chat_font_layout)

        chat_size_layout = QVBoxLayout()
        chat_size_layout.setSpacing(8)
        chat_size_label = QLabel("اندازه متون پیام‌ها:")
        chat_size_label.setObjectName("fieldLabel")
        
        self.chat_size_slider = DiscreteSlider()
        self.chat_size_slider.valueChanged.connect(self._on_chat_size_selected)
        self.chat_size_slider.setFixedHeight(30)
        
        chat_size_layout.addWidget(chat_size_label)
        chat_size_layout.addWidget(self.chat_size_slider)
        content_layout.addLayout(chat_size_layout)
        
        # خط جداکننده
        divider3 = QFrame()
        divider3.setObjectName("divider")
        content_layout.addWidget(divider3)

        # --- بخش تنظیمات خروجی PDF ---
        pdf_title = QLabel("محل ذخیره فایل‌ها:")
        pdf_title.setObjectName("sectionTitle")
        content_layout.addWidget(pdf_title)

        pdf_path_layout = QVBoxLayout()
        pdf_path_layout.setSpacing(8)
        pdf_path_label = QLabel("پوشه پیش‌فرض PDF:")
        pdf_path_label.setObjectName("fieldLabel")
        
        pdf_row = QHBoxLayout()
        pdf_row.setSpacing(8)
        
        self.pdf_path_input = QLineEdit()
        self.pdf_path_input.setReadOnly(True)
        self.pdf_path_input.setLayoutDirection(Qt.LeftToRight)
        self.pdf_path_input.setPlaceholderText("مسیری انتخاب نشده است...")
        # استایل‌دهی مستقیم برای نمایش واضح فیلد متنی در هر دو تم
        self.pdf_path_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(128, 128, 128, 0.1);
                border: 1px solid rgba(128, 128, 128, 0.3);
                border-radius: 6px;
                padding: 6px;
                color: inherit;
            }
        """)
        
        self.btn_select_pdf_dir = QPushButton("انتخاب پوشه")
        self.btn_select_pdf_dir.setCursor(Qt.PointingHandCursor)
        self.btn_select_pdf_dir.setObjectName("sortBtn") 
        # استایل‌دهی مستقیم دکمه
        self.btn_select_pdf_dir.setStyleSheet("""
            QPushButton {
                background-color: rgba(128, 128, 128, 0.15);
                border: 1px solid rgba(128, 128, 128, 0.3);
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: rgba(128, 128, 128, 0.3);
            }
        """)
        self.btn_select_pdf_dir.clicked.connect(self._on_select_pdf_dir)
        
        pdf_row.addWidget(self.pdf_path_input, stretch=1)
        pdf_row.addWidget(self.btn_select_pdf_dir)
        
        pdf_path_layout.addWidget(pdf_path_label)
        pdf_path_layout.addLayout(pdf_row)
        content_layout.addLayout(pdf_path_layout)
        
        content_layout.addStretch(1)
        scroll_area.setWidget(content_widget)
        exp_layout.addWidget(scroll_area)
        
        layout.addWidget(self.collapsed_widget)
        layout.addWidget(self.expanded_widget)

    def _load_saved_settings(self):
        # بارگذاری تم و رنگ و رنگ‌آمیزی آیکون چرخ‌دنده بر اساس آن
        saved_theme, saved_color = storage.get_theme_settings()
        self.update_icons(saved_theme)
        
        theme_text = REV_THEME_MAP.get(saved_theme, "تاریک (Dark)")
        self.theme_combo.blockSignals(True)
        self.theme_combo.setCurrentText(theme_text)
        self.theme_combo.blockSignals(False)
        
        color_text = REV_COLOR_MAP.get(saved_color, "قرمز (پیش‌فرض)")
        self._prev_color_text = color_text
        self.color_combo.blockSignals(True)
        self.color_combo.setCurrentText(color_text)
        self.color_combo.blockSignals(False)
        
        # بارگذاری کلیدهای شخصی ذخیره شده در سیستم (API Keys)
        saved_main_key = storage.get_setting("user_main_api_key", "")
        if saved_main_key:
            self.main_api_input.setText(saved_main_key)
            
        saved_groq_key = storage.get_setting("user_groq_api_key", "")
        if saved_groq_key:
            self.groq_api_input.setText(saved_groq_key)

        # بارگذاری تنظیمات رابط کاربری
        saved_ui_font = storage.get_setting("ui_font_family", "سیستم (پیش‌فرض)")
        if saved_ui_font in self.available_fonts:
            self.ui_font_combo.blockSignals(True)
            self.ui_font_combo.setCurrentText(saved_ui_font)
            self.ui_font_combo.blockSignals(False)
            
        saved_ui_size = int(storage.get_setting("ui_font_size", "3"))
        self.ui_size_slider.blockSignals(True)
        self.ui_size_slider.setValue(saved_ui_size)
        self.ui_size_slider.blockSignals(False)

        # بارگذاری تنظیمات محیط چت
        saved_chat_font = storage.get_setting("chat_font_family", "سیستم (پیش‌فرض)")
        if saved_chat_font in self.available_fonts:
            self.chat_font_combo.blockSignals(True)
            self.chat_font_combo.setCurrentText(saved_chat_font)
            self.chat_font_combo.blockSignals(False)
            
        saved_chat_size = int(storage.get_setting("chat_font_size", "3"))
        self.chat_size_slider.blockSignals(True)
        self.chat_size_slider.setValue(saved_chat_size)
        self.chat_size_slider.blockSignals(False)

        # بارگذاری مسیر ذخیره PDF
        saved_pdf_path = storage.get_setting("pdf_export_path", "")
        if saved_pdf_path:
            self.pdf_path_input.setText(saved_pdf_path)

    def _on_save_api_keys(self):
        """ذخیره کلیدهای کاربر در دیتابیس محلی و ارسال سیگنال بروزرسانی به هسته شبکه"""
        main_key = self.main_api_input.text().strip()
        groq_key = self.groq_api_input.text().strip()
        
        storage.set_setting("user_main_api_key", main_key)
        storage.set_setting("user_groq_api_key", groq_key)
        
        self.api_keys_updated.emit()
        
        # نمایش بازخورد بصری به کاربر روی خود دکمه
        original_text = self.btn_save_keys.text()
        self.btn_save_keys.setText("✅ ذخیره شد")
        QTimer.singleShot(2000, lambda: self.btn_save_keys.setText(original_text) if "✅" in self.btn_save_keys.text() else None)

    def _on_select_pdf_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "انتخاب پوشه پیش‌فرض برای ذخیره PDF")
        if dir_path:
            storage.set_setting("pdf_export_path", dir_path)
            self.pdf_path_input.setText(dir_path)

    def toggle_drawer(self):
        is_collapsed = self.width() == 50
        
        self.anim_min = QPropertyAnimation(self, b"minimumWidth")
        self.anim_max = QPropertyAnimation(self, b"maximumWidth")
        self.anim_min.setDuration(250)
        self.anim_max.setDuration(250)
        self.anim_min.setEasingCurve(QEasingCurve.OutCubic)
        self.anim_max.setEasingCurve(QEasingCurve.OutCubic)
        
        if is_collapsed:
            self.collapsed_widget.hide()
            self.expanded_widget.show()
            self.anim_min.setStartValue(50)
            self.anim_min.setEndValue(300) 
            self.anim_max.setStartValue(50)
            self.anim_max.setEndValue(300)
        else:
            self.expanded_widget.hide()
            self.collapsed_widget.show()
            self.anim_min.setStartValue(300)
            self.anim_min.setEndValue(50)
            self.anim_max.setStartValue(300)
            self.anim_max.setEndValue(50)
            
        self.anim_group = QParallelAnimationGroup()
        self.anim_group.addAnimation(self.anim_min)
        self.anim_group.addAnimation(self.anim_max)
        self.anim_group.start()

    def _on_theme_changed(self, text: str):
        mode = THEME_MAP.get(text, "dark")
        current_color = COLOR_MAP.get(self.color_combo.currentText(), "red")
        storage.set_theme_settings(mode, current_color)
        
        self.update_icons(mode)
        self.theme_mode_changed.emit(mode)

    def _on_color_changed(self, text: str):
        if text == "+ افزودن رنگ جدید...":
            self._handle_add_custom_color()
            return
            
        if text in COLOR_MAP:
            self._prev_color_text = text
            current_mode = THEME_MAP.get(self.theme_combo.currentText(), "dark")
            color = COLOR_MAP.get(text, "red")
            storage.set_theme_settings(current_mode, color)
            self.accent_color_changed.emit(color)

    def _handle_add_custom_color(self):
        """باز کردن دیالوگ رنگ، دریافت نام رنگ از کاربر و ذخیره‌ی آن در سیستم"""
        color = QColorDialog.getColor(Qt.white, self, "انتخاب رنگ سفارشی")
        
        if color.isValid():
            hex_code = color.name()
            
            # باز کردن دیالوگ ساده برای دریافت نام رنگ سفارشی از کاربر
            name, ok = QInputDialog.getText(
                self, "نام رنگ", "یک نام برای این رنگ وارد کنید:",
                QLineEdit.Normal, "رنگ سفارشی من"
            )
            
            if ok and name.strip():
                name = name.strip()
                if name in COLOR_MAP or name == "+ افزودن رنگ جدید...":
                    name = name + " (سفارشی)"
                
                internal_key = f"custom_{hex_code.replace('#', '')}"
                
                # افزودن رنگ به حافظه موقت برنامه (UI)
                COLOR_MAP[name] = internal_key
                REV_COLOR_MAP[internal_key] = name
                add_custom_accent(internal_key, hex_code)
                
                # ذخیره در دیتابیس (JSON)
                customs_json = storage.get_setting("custom_accents", "{}")
                try:
                    customs = json.loads(customs_json)
                except Exception:
                    customs = {}
                    
                customs[name] = hex_code
                storage.set_setting("custom_accents", json.dumps(customs))
                
                # بروزرسانی منوی کشویی رنگ‌ها
                self.color_combo.blockSignals(True)
                self.color_combo.clear()
                self.color_combo.addItems(list(COLOR_MAP.keys()))
                self.color_combo.addItem("+ افزودن رنگ جدید...")
                self.color_combo.setCurrentText(name)
                self.color_combo.blockSignals(False)
                
                self._prev_color_text = name
                
                # اعمال رنگ و سیگنال‌دهی به کل برنامه
                current_mode = THEME_MAP.get(self.theme_combo.currentText(), "dark")
                storage.set_theme_settings(current_mode, internal_key)
                self.accent_color_changed.emit(internal_key)
                return
                
        # در صورتی که کاربر دیالوگ را ببندد (کنسل کند)، رنگ قبلی را برمی‌گردانیم
        self.color_combo.blockSignals(True)
        self.color_combo.setCurrentText(self._prev_color_text)
        self.color_combo.blockSignals(False)

    def _on_ui_font_selected(self, font_name: str):
        storage.set_setting("ui_font_family", font_name)
        self.ui_font_changed.emit(font_name)

    def _on_ui_size_selected(self, size_val: int):
        storage.set_setting("ui_font_size", str(size_val))
        self.ui_font_size_changed.emit(size_val)
        
    def _on_chat_font_selected(self, font_name: str):
        storage.set_setting("chat_font_family", font_name)
        self.chat_font_changed.emit(font_name)

    def _on_chat_size_selected(self, size_val: int):
        storage.set_setting("chat_font_size", str(size_val))
        self.chat_font_size_changed.emit(size_val)

    # ========================================================================
    # توابع کمکی (Helper Methods) برای تعامل با ShortcutManager
    # این توابع ابزارهای روی پنل را تکان می‌دهند تا چرخه آپدیت کامل طی شود
    # ========================================================================
    
    def set_theme_from_shortcut(self, mode_name: str):
        """تغییر مستقیم تم از طریق کلیدهای میانبر"""
        text = REV_THEME_MAP.get(mode_name)
        if text:
            # تغییر دادن CurrentText به صورت خودکار سیگنال currentTextChanged را شلیک می‌کند
            # در نتیجه دیتابیس آپدیت شده و به کل برنامه اطلاع داده می‌شود
            self.theme_combo.setCurrentText(text)

    def toggle_theme_from_shortcut(self):
        """چرخش بین حالت‌های مختلف تم در منوی کشویی"""
        current = self.theme_combo.currentIndex()
        next_idx = (current + 1) % self.theme_combo.count()
        self.theme_combo.setCurrentIndex(next_idx)

    def step_ui_font(self, step: int):
        """حرکت دادنِ اسلایدر سایز فونت منوها"""
        current = self.ui_size_slider.value()
        new_val = max(self.ui_size_slider.minimum(), min(self.ui_size_slider.maximum(), current + step))
        # این کار باعث شلیک valueChanged می‌شود
        self.ui_size_slider.setValue(new_val)

    def step_chat_font(self, step: int):
        """حرکت دادنِ اسلایدر سایز فونت پیام‌های چت"""
        current = self.chat_size_slider.value()
        new_val = max(self.chat_size_slider.minimum(), min(self.chat_size_slider.maximum(), current + step))
        # این کار باعث شلیک valueChanged می‌شود
        self.chat_size_slider.setValue(new_val)