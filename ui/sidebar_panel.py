"""
کامپوننت سایدبار تاریخچه (Sidebar Panel) - معماری لایه‌بندی شده (مسیر: ui/sidebar_panel.py)
مسئولیت‌ها:
۱. مدیریت لیست گفتگوهای قبلی (خواندن از دیتابیس در پوشه data).
۲. مرتب‌سازی سه‌گانه (زمان، رنگ، زبان) با استفاده از آیکون‌های پویا.
۳. مدیریت منوی راست‌کلیک و کلیک روی سه‌نقطه (تغییر نام، تغییر رنگ از پیش‌فرض‌ها و حذف چت).
۴. ارسال سیگنال به main.py برای انتخاب چت یا درخواست چت جدید.
"""

import os
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QMenu, QInputDialog, QLineEdit
)

# تنظیم مسیر ریشه پروژه برای دسترسی به سایر پوشه‌ها
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

# ایمپورت‌ها بر اساس معماری جدید
from data import storage
from ui.widgets import RIGHT, ChatItemDelegate, ChatItemWidget, PROJECT_COLORS, create_color_icon, get_theme_icon


class SidebarWidget(QWidget):
    # سیگنال‌های خروجی برای ارتباط با رهبر ارکستر (main.py)
    chat_selected = Signal(dict)      # وقتی چتی از لیست انتخاب می‌شود
    new_chat_requested = Signal()     # وقتی دکمه چت جدید فشرده می‌شود
    chat_deleted = Signal(str)        # وقتی چتی حذف می‌شود (تا اگر باز بود، پنل چت پاک شود)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setMaximumWidth(450)

        # حافظه داخلی برای نگهداری چت‌ها جهت مرتب‌سازی سریع بدون درگیر کردن دیتابیس
        self.chats = storage.load_chats()
        self.current_sort_mode = 'time'
        self.time_descending = True

        self._build_ui()
        self.refresh_list()
        
        # بارگذاری اولیه رنگ آیکون‌ها بر اساس تم ذخیره شده
        current_theme, _ = storage.get_theme_settings()
        self.update_icons(current_theme)

    def update_icons(self, theme_mode: str):
        """رنگ آیکون‌های مرتب‌سازی سایدبار را بر اساس تم پویا به‌روز می‌کند."""
        self.btn_sort_lang.setIcon(get_theme_icon("Code.svg", theme_mode))
        self.btn_sort_color.setIcon(get_theme_icon("Color.svg", theme_mode))
        self.btn_sort_time.setIcon(get_theme_icon("Clock.svg", theme_mode))

    def _make_label(self, text: str, object_name: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName(object_name)
        label.setAlignment(RIGHT)
        return label

    def _make_sort_button(self, tooltip: str, slot) -> QPushButton:
        """ساخت دکمه پایه برای مرتب‌سازی (آیکون در متد update_icons اعمال می‌شود)"""
        btn = QPushButton()
        btn.setObjectName("sortBtn")
        btn.setToolTip(tooltip)
        btn.setFixedSize(28, 28)
        btn.setIconSize(QSize(18, 18))
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(slot)
        return btn

    def _build_ui(self):
        # ساختار کلی سایدبار
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        top_layout = QVBoxLayout()
        top_layout.setContentsMargins(10, 0, 10, 0) 
        top_layout.setSpacing(10)

        self.new_chat_btn = QPushButton("+ گفتگوی جدید")
        self.new_chat_btn.setObjectName("newChatBtn")
        self.new_chat_btn.setCursor(Qt.PointingHandCursor)
        self.new_chat_btn.clicked.connect(self.new_chat_requested.emit)
        top_layout.addWidget(self.new_chat_btn)

        history_header_layout = QHBoxLayout()
        history_header_layout.addWidget(self._make_label("گفتگوهای قبلی:", "fieldLabel"))
        history_header_layout.addStretch(1)

        # ساخت دکمه‌های مرتب‌سازی
        self.btn_sort_lang = self._make_sort_button("مرتب‌سازی بر اساس زبان برنامه‌نویسی", self.sort_by_language)
        self.btn_sort_color = self._make_sort_button("مرتب‌سازی بر اساس موضوع پروژه", self.sort_by_color)
        self.btn_sort_time = self._make_sort_button("مرتب‌سازی بر اساس زمان", self.sort_by_time)

        history_header_layout.addWidget(self.btn_sort_lang)
        history_header_layout.addWidget(self.btn_sort_color)
        history_header_layout.addWidget(self.btn_sort_time)
        top_layout.addLayout(history_header_layout)

        layout.addLayout(top_layout)

        list_layout = QVBoxLayout()
        list_layout.setContentsMargins(0, 0, 0, 0) 
        
        self.history_list = QListWidget()
        self.history_list.setLayoutDirection(Qt.RightToLeft)
        self.history_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.history_list.setItemDelegate(ChatItemDelegate(self.history_list))
        self.history_list.itemClicked.connect(self._on_item_clicked)

        self.history_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.history_list.customContextMenuRequested.connect(self._on_context_menu)

        list_layout.addWidget(self.history_list)
        
        layout.addLayout(list_layout, stretch=1)

    def _update_sort_buttons_ui(self):
        for btn, mode in [(self.btn_sort_time, 'time'),
                          (self.btn_sort_color, 'color'),
                          (self.btn_sort_lang, 'language')]:
            btn.setProperty("active", str(self.current_sort_mode == mode).lower())
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def sort_by_time(self):
        if self.current_sort_mode == 'time':
            self.time_descending = not self.time_descending
        else:
            self.current_sort_mode = 'time'
            self.time_descending = True
        self.refresh_list()

    def sort_by_color(self):
        self.current_sort_mode = 'color'
        self.refresh_list()

    def sort_by_language(self):
        self.current_sort_mode = 'language'
        self.refresh_list()

    def refresh_list(self, select_chat_id: str = None):
        self.history_list.clear()

        sorted_chats = sorted(self.chats, key=lambda c: c["created_at"], reverse=True)

        if self.current_sort_mode == 'time':
            sorted_chats = sorted(self.chats, key=lambda c: c["created_at"], reverse=self.time_descending)
        elif self.current_sort_mode == 'color':
            sorted_chats = sorted(sorted_chats, key=lambda c: c.get("color", "#808080"))
        elif self.current_sort_mode == 'language':
            sorted_chats = sorted(sorted_chats, key=lambda c: c["language"])

        self._update_sort_buttons_ui()

        for chat in sorted_chats:
            self._create_list_item(chat)

        if select_chat_id:
            self.select_chat(select_chat_id)

    def _create_list_item(self, chat: dict, insert_at_top: bool = False):
        item = QListWidgetItem()
        item.setData(Qt.UserRole, chat["id"])
        item.setData(Qt.UserRole + 1, chat.get("color", "#808080"))

        widget = ChatItemWidget(chat)
        widget.rename_requested.connect(self.rename_chat)
        widget.change_color_requested.connect(self.change_chat_color) 
        widget.delete_requested.connect(self.delete_chat)

        item.setSizeHint(QSize(0, 75))

        if insert_at_top:
            self.history_list.insertItem(0, item)
        else:
            self.history_list.addItem(item)
            
        self.history_list.setItemWidget(item, widget)
        return item

    def _on_item_clicked(self, item: QListWidgetItem):
        chat_id = item.data(Qt.UserRole)
        chat = next((c for c in self.chats if c["id"] == chat_id), None)
        if chat:
            self.chat_selected.emit(chat)

    def _on_context_menu(self, pos):
        item = self.history_list.itemAt(pos)
        if item is None:
            return

        chat_id = item.data(Qt.UserRole)

        menu = QMenu(self)
        menu.setLayoutDirection(Qt.RightToLeft)

        rename_action = menu.addAction("تغییر عنوان")
        
        # ساخت زیرمنو برای رنگ‌ها در راست‌کلیک
        color_menu = menu.addMenu("تغییر موضوع و رنگ")
        color_menu.setLayoutDirection(Qt.RightToLeft)
        for name, hex_code in PROJECT_COLORS.items():
            act = color_menu.addAction(create_color_icon(hex_code), name)
            act.triggered.connect(lambda checked=False, c_id=chat_id, h=hex_code: self.change_chat_color(c_id, h))

        delete_action = menu.addAction("حذف گفتگو")

        action = menu.exec(self.history_list.mapToGlobal(pos))

        if action == rename_action:
            self.rename_chat(chat_id)
        elif action == delete_action:
            self.delete_chat(chat_id)

    def rename_chat(self, chat_id: str):
        chat = next((c for c in self.chats if c["id"] == chat_id), None)
        if not chat:
            return

        dialog = QInputDialog(self)
        dialog.setWindowTitle("تغییر عنوان")
        dialog.setLabelText("عنوان جدید گفتگو را وارد کنید (حداکثر ۳۰ کاراکتر):")
        dialog.setTextValue(chat["title"])
        dialog.setLayoutDirection(Qt.RightToLeft)

        line_edit = dialog.findChild(QLineEdit)
        if line_edit:
            line_edit.setMaxLength(30)

        if dialog.exec() == QInputDialog.Accepted:
            new_title = dialog.textValue().strip()
            if new_title:
                chat["title"] = new_title
                storage.update_chat(chat) 
                
                item = self._find_list_item(chat_id)
                if item:
                    widget = self.history_list.itemWidget(item)
                    if widget:
                        widget.update_text(chat["language"], new_title)

    def change_chat_color(self, chat_id: str, new_color_hex: str):
        """ذخیره و اعمال رنگ انتخاب‌شده از زیرمنو"""
        chat = next((c for c in self.chats if c["id"] == chat_id), None)
        if not chat:
            return

        chat["color"] = new_color_hex
        storage.update_chat(chat)
        
        item = self._find_list_item(chat_id)
        if item:
            item.setData(Qt.UserRole + 1, new_color_hex)

    def delete_chat(self, chat_id: str):
        storage.delete_chat(chat_id)
        self.chats = [c for c in self.chats if c["id"] != chat_id]
        
        item = self._find_list_item(chat_id)
        if item:
            row = self.history_list.row(item)
            self.history_list.takeItem(row)
            
        self.chat_deleted.emit(chat_id)

    def _find_list_item(self, chat_id: str):
        for i in range(self.history_list.count()):
            item = self.history_list.item(i)
            if item.data(Qt.UserRole) == chat_id:
                return item
        return None

    def add_new_chat(self, chat_dict: dict):
        self.chats.append(chat_dict)
        item = self._create_list_item(chat_dict, insert_at_top=True)
        self.history_list.setCurrentItem(item)

    def update_chat_metadata(self, chat_id: str, title: str = None, color_hex: str = None):
        for chat in self.chats:
            if chat["id"] == chat_id:
                if title: chat["title"] = title
                if color_hex: chat["color"] = color_hex
                break

        item = self._find_list_item(chat_id)
        if item:
            if color_hex:
                item.setData(Qt.UserRole + 1, color_hex)
            if title:
                widget = self.history_list.itemWidget(item)
                if widget:
                    lang = next((c["language"] for c in self.chats if c["id"] == chat_id), "")
                    widget.update_text(lang, title)

    def select_chat(self, chat_id: str):
        item = self._find_list_item(chat_id)
        if item:
            self.history_list.setCurrentItem(item)

    def deselect_all(self):
        self.history_list.clearSelection()