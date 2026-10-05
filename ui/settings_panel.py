"""
کامپوننت پنل تنظیمات کشویی (Sliding Drawer) - معماری لایه‌بندی شده (مسیر: ui/settings_panel.py)
مسئولیت‌ها:
۱. مدیریت انیمیشن باز و بسته شدن پنل.
۲. نمایش فیلدهای تنظیمات مجزا (رابط کاربری و محیط گفتگو).
۳. خواندن و ذخیره مستقیم تنظیمات در دیتابیس از طریق ماژول data.storage.
۴. ارسال سیگنال‌های تفکیک‌شده به main.py هنگام اعمال تغییرات.
"""

import os

# تنظیم مسیر ریشه پروژه برای دسترسی به سایر پوشه‌ها
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

from PySide6.QtCore import (
    Qt, Signal, QPropertyAnimation, QParallelAnimationGroup, QEasingCurve, QSize
)
from PySide6.QtGui import QPainter, QColor, QIcon
from PySide6.QtWidgets import (
    QFrame, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QSlider
)

# ایمپورت‌ها بر اساس معماری جدید
from data import storage
from ui.widgets import RIGHT


class DiscreteSlider(QSlider):
    """نوار لغزان سفارشی با 5 نقطه خاکستری و یک دستگیره قرمز برای انتخاب سایز"""
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
        
        # ۱. رسم نوار پس‌زمینه اصلی
        track_height = 6
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#33333d")) 
        painter.drawRoundedRect(margin, y_center - track_height // 2, usable_width, track_height, 3, 3)
        
        # ۲. رسم ۵ نقطه خاکستری
        steps = self.maximum() - self.minimum()
        dot_radius = 4
        for i in range(steps + 1):
            x = margin + int(i * usable_width / steps)
            painter.setBrush(QColor("#9a9aa5")) 
            painter.drawEllipse(x - dot_radius, y_center - dot_radius, dot_radius * 2, dot_radius * 2)
            
        # ۳. رسم دستگیره قرمز روی مقدار فعلی
        current_step = self.value() - self.minimum()
        handle_x = margin + int(current_step * usable_width / steps)
        handle_radius = 8
        painter.setBrush(QColor("#e5383b"))
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
    # سیگنال‌های تفکیک‌شده برای رابط کاربری و چت
    ui_font_changed = Signal(str)
    ui_font_size_changed = Signal(int)
    chat_font_changed = Signal(str)
    chat_font_size_changed = Signal(int)

    def __init__(self, available_fonts: dict, parent=None):
        super().__init__(parent)
        self.available_fonts = available_fonts
        
        self.setObjectName("settingsPanel")
        self.setFixedWidth(50) 
        
        self.setLayoutDirection(Qt.RightToLeft)
        
        self._build_ui()
        self._load_saved_settings()

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
        
        # مسیردهی جدید به آیکون تنظیمات در پوشه resources
        icon_path = os.path.join(PROJECT_ROOT, "resources", "icons", "Settings.svg")
        self.btn_open.setIcon(QIcon(icon_path))
        self.btn_open.setIconSize(QSize(24, 24))
        
        self.btn_open.clicked.connect(self.toggle_drawer)
        
        col_layout.addStretch(1)
        col_layout.addWidget(self.btn_open, alignment=Qt.AlignBottom | Qt.AlignHCenter)
        
        # ==========================================
        # ۲. ویجت حالت باز
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
        
        # --- بخش تنظیمات رابط کاربری (UI) ---
        ui_title = QLabel("ظاهر برنامه:")
        ui_title.setStyleSheet("color: #e5383b; font-weight: bold;")
        exp_layout.addWidget(ui_title)
        
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
        exp_layout.addLayout(ui_font_layout)
        
        ui_size_layout = QVBoxLayout()
        ui_size_layout.setSpacing(8)
        ui_size_label = QLabel("اندازه متون منوها:")
        ui_size_label.setObjectName("fieldLabel")
        
        self.ui_size_slider = DiscreteSlider()
        self.ui_size_slider.valueChanged.connect(self._on_ui_size_selected)
        self.ui_size_slider.setFixedHeight(30)
        
        ui_size_layout.addWidget(ui_size_label)
        ui_size_layout.addWidget(self.ui_size_slider)
        exp_layout.addLayout(ui_size_layout)
        
        # خط جداکننده
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("background-color: #33333d; margin: 10px 0;")
        exp_layout.addWidget(divider)
        
        # --- بخش تنظیمات محیط گفتگو (Chat) ---
        chat_title = QLabel("محیط گفتگو:")
        chat_title.setStyleSheet("color: #58a6ff; font-weight: bold;")
        exp_layout.addWidget(chat_title)

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
        exp_layout.addLayout(chat_font_layout)

        chat_size_layout = QVBoxLayout()
        chat_size_layout.setSpacing(8)
        chat_size_label = QLabel("اندازه متون پیام‌ها:")
        chat_size_label.setObjectName("fieldLabel")
        
        self.chat_size_slider = DiscreteSlider()
        self.chat_size_slider.valueChanged.connect(self._on_chat_size_selected)
        self.chat_size_slider.setFixedHeight(30)
        
        chat_size_layout.addWidget(chat_size_label)
        chat_size_layout.addWidget(self.chat_size_slider)
        exp_layout.addLayout(chat_size_layout)
        
        exp_layout.addStretch(1)
        
        layout.addWidget(self.collapsed_widget)
        layout.addWidget(self.expanded_widget)

    def _load_saved_settings(self):
        # بارگذاری تنظیمات رابط کاربری از دیتابیس
        saved_ui_font = storage.get_setting("ui_font_family", "سیستم (پیش‌فرض)")
        if saved_ui_font in self.available_fonts:
            self.ui_font_combo.blockSignals(True)
            self.ui_font_combo.setCurrentText(saved_ui_font)
            self.ui_font_combo.blockSignals(False)
            
        saved_ui_size = int(storage.get_setting("ui_font_size", "3"))
        self.ui_size_slider.blockSignals(True)
        self.ui_size_slider.setValue(saved_ui_size)
        self.ui_size_slider.blockSignals(False)

        # بارگذاری تنظیمات محیط چت از دیتابیس
        saved_chat_font = storage.get_setting("chat_font_family", "سیستم (پیش‌فرض)")
        if saved_chat_font in self.available_fonts:
            self.chat_font_combo.blockSignals(True)
            self.chat_font_combo.setCurrentText(saved_chat_font)
            self.chat_font_combo.blockSignals(False)
            
        saved_chat_size = int(storage.get_setting("chat_font_size", "3"))
        self.chat_size_slider.blockSignals(True)
        self.chat_size_slider.setValue(saved_chat_size)
        self.chat_size_slider.blockSignals(False)

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
            self.anim_min.setEndValue(260)
            self.anim_max.setStartValue(50)
            self.anim_max.setEndValue(260)
        else:
            self.expanded_widget.hide()
            self.collapsed_widget.show()
            self.anim_min.setStartValue(260)
            self.anim_min.setEndValue(50)
            self.anim_max.setStartValue(260)
            self.anim_max.setEndValue(50)
            
        self.anim_group = QParallelAnimationGroup()
        self.anim_group.addAnimation(self.anim_min)
        self.anim_group.addAnimation(self.anim_max)
        self.anim_group.start()

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