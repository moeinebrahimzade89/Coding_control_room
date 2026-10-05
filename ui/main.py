"""
برنامه پیشنهاددهنده پروژه برنامه‌نویسی (معماری لایه‌بندی شده)
نقطه ورود برنامه (مسیر: ui/main.py)
------------------------------------------------------------------
وظایف:
۱. حفظ هویت پنجره بومی برای پشتیبانی کامل از Snap Assist و Task View.
۲. ایجاد هدر سفارشی با طراحی مدرن و استفاده از آیکون‌های SVG از پوشه resources.
۳. ارتباط مستقیم با API ویندوز با پشتیبانی از High DPI Scaling.
"""

import sys
import os

# ===================================================================
# تنظیمات مسیردهی پروژه (تعریف Root Directory)
# ===================================================================
# چون این فایل در پوشه ui قرار دارد، یک سطح به عقب برمی‌گردیم تا به پوشه اصلی برسیم
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
sys.path.insert(0, PROJECT_ROOT)

from PySide6.QtCore import Qt, QPoint, QSize
from PySide6.QtGui import QFont, QFontDatabase, QMouseEvent, QIcon, QCursor
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QSplitter, QPushButton
)

# کتابخانه‌های لازم برای ارتباط با هسته ویندوز
try:
    import ctypes
    from ctypes.wintypes import MSG
except ImportError:
    pass

# ایمپورت ماژول‌ها بر اساس معماری جدید
from data import storage
from ui.sidebar_panel import SidebarWidget
from ui.chat_panel import ChatWidget
from ui.settings_panel import SettingsDrawer
from ui.widgets import build_stylesheet


def _load_app_fonts() -> dict:
    """بارگذاری فونت‌ها از پوشه resources/fonts"""
    font_dir = os.path.join(PROJECT_ROOT, "resources", "fonts")
    loaded_fonts = {"سیستم (پیش‌فرض)": "Segoe UI"}
    
    if os.path.exists(font_dir):
        for folder_name in os.listdir(font_dir):
            folder_path = os.path.join(font_dir, folder_name)
            if os.path.isdir(folder_path):
                for filename in os.listdir(folder_path):
                    if filename.lower().endswith(".ttf"):
                        font_path = os.path.join(folder_path, filename)
                        font_id = QFontDatabase.addApplicationFont(font_path)
                        if font_id != -1:
                            families = QFontDatabase.applicationFontFamilies(font_id)
                            if families:
                                loaded_fonts[folder_name] = families[0]
                            break 
    return loaded_fonts


# ===================================================================
# کلاس نوار عنوان سفارشی (Custom Title Bar)
# ===================================================================
class CustomTitleBar(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_window = parent
        self.setObjectName("customTitleBar")
        self.setFixedHeight(45)
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        # آدرس‌دهی جدید پوشه آیکون‌ها
        icons_dir = os.path.join(PROJECT_ROOT, "resources", "icons")
        
        self.icon_close = QIcon(os.path.join(icons_dir, "Close.svg"))
        self.icon_maximize = QIcon(os.path.join(icons_dir, "Fullscreen.svg"))
        self.icon_restore = QIcon(os.path.join(icons_dir, "Exit-Fullscreen.svg"))
        self.icon_minimize = QIcon(os.path.join(icons_dir, "Minimize.svg"))
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0) 
        layout.setSpacing(0)
        
        right_spacer = QLabel()
        right_spacer.setFixedWidth(135) 
        right_spacer.setStyleSheet("background: transparent;")
        
        self.title_label = QLabel("اتاق فرمان برنامه نویسی")
        self.title_label.setObjectName("title")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("background: transparent;")
        
        self.btn_minimize = QPushButton()
        self.btn_minimize.setIcon(self.icon_minimize)
        
        self.btn_maximize = QPushButton()
        self.btn_maximize.setIcon(self.icon_maximize)
        
        self.btn_close = QPushButton()
        self.btn_close.setIcon(self.icon_close)
        self.btn_close.setObjectName("closeBtn")
        
        layout.addWidget(right_spacer)
        layout.addWidget(self.title_label, stretch=1)
        
        for btn in [self.btn_minimize, self.btn_maximize, self.btn_close]:
            if btn != self.btn_close:
                btn.setObjectName("windowControlBtn")
            btn.setFixedSize(46, 45)
            btn.setIconSize(QSize(16, 16))
            btn.setCursor(Qt.ArrowCursor) 
            layout.addWidget(btn)
            
        self.btn_close.clicked.connect(self.parent_window.close)
        self.btn_maximize.clicked.connect(self.toggle_maximize)
        self.btn_minimize.clicked.connect(self.parent_window.showMinimized)

    def toggle_maximize(self):
        if self.parent_window.isMaximized():
            self.parent_window.showNormal()
            self.btn_maximize.setIcon(self.icon_maximize)
        else:
            self.parent_window.showMaximized()
            self.btn_maximize.setIcon(self.icon_restore) 

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and sys.platform != "win32":
            self._start_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent):
        if sys.platform != "win32" and hasattr(self, '_start_pos') and self._start_pos is not None:
            delta = event.globalPosition().toPoint() - self._start_pos
            self.parent_window.move(self.parent_window.pos() + delta)
            self._start_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if sys.platform != "win32":
            self._start_pos = None

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.toggle_maximize()


# ===================================================================
# پنجره اصلی برنامه
# ===================================================================
class MainWindow(QWidget):
    def __init__(self, available_fonts: dict):
        super().__init__()
        self.available_fonts = available_fonts
        
        self.setWindowFlags(Qt.Window)
        
        self.setWindowTitle("پیشنهاددهنده پروژه برنامه‌نویسی")
        self.resize(980, 720)
        self.setLayoutDirection(Qt.RightToLeft)

        self._build_ui()
        self._connect_signals()
        
        self._update_global_font()

    def nativeEvent(self, eventType, message):
        if sys.platform == "win32" and eventType == b"windows_generic_MSG":
            try:
                msg = MSG.from_address(int(message))
                
                if msg.message == 0x0083 and msg.wParam:
                    return True, 0

                # بخش مدیریت تغییر سایز و کلیک در پنجره‌های Frameless
                if msg.message == 0x0084: 
                    # رفع باگ High DPI در مقیاس‌های ۱۵۰٪ ویندوز
                    pos = self.mapFromGlobal(QCursor.pos())
                    
                    w, h = self.width(), self.height()
                    border = 8 

                    if pos.x() < border and pos.y() < border: return True, 13
                    if pos.x() > w - border and pos.y() < border: return True, 14
                    if pos.x() < border and pos.y() > h - border: return True, 16
                    if pos.x() > w - border and pos.y() > h - border: return True, 17
                    if pos.x() < border: return True, 10
                    if pos.x() > w - border: return True, 11
                    if pos.y() < border: return True, 12
                    if pos.y() > h - border: return True, 15

                    if hasattr(self, 'title_bar') and pos.y() < self.title_bar.height():
                        child = self.childAt(pos)
                        if isinstance(child, QPushButton):
                            return False, 0
                        return True, 2 
            except Exception:
                pass
                
        return super().nativeEvent(eventType, message)

    def _build_ui(self):
        self.main_container = QFrame(self)
        self.main_container.setObjectName("mainContainer")
        self.main_container.setAttribute(Qt.WA_StyledBackground, True)
        
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(self.main_container)
        
        container_layout = QVBoxLayout(self.main_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        self.title_bar = CustomTitleBar(self)
        container_layout.addWidget(self.title_bar)
        
        body_widget = QWidget()
        body_layout = QHBoxLayout(body_widget)
        body_layout.setContentsMargins(0, 0, 0, 0) 
        body_layout.setSpacing(0)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 0, 20, 0)
        content_layout.setSpacing(0)
        
        self.sidebar = SidebarWidget()
        sidebar_wrapper = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_wrapper)
        sidebar_layout.setContentsMargins(0, 10, 0, 15)
        sidebar_layout.addWidget(self.sidebar)

        self.chat_panel = ChatWidget()
        chat_wrapper = QWidget()
        chat_layout = QVBoxLayout(chat_wrapper)
        chat_layout.setContentsMargins(0, 10, 20, 15)
        chat_layout.addWidget(self.chat_panel)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(sidebar_wrapper)         
        splitter.addWidget(chat_wrapper)      
        splitter.setSizes([250, 730])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        content_layout.addWidget(splitter, stretch=1)
        
        self.settings_drawer = SettingsDrawer(self.available_fonts)

        body_layout.addWidget(content_widget, stretch=1)
        body_layout.addWidget(self.settings_drawer)

        container_layout.addWidget(body_widget, stretch=1)

    def _connect_signals(self):
        self.sidebar.chat_selected.connect(self.chat_panel.set_chat)
        self.sidebar.new_chat_requested.connect(self._on_new_chat_requested)
        self.sidebar.chat_deleted.connect(self._on_chat_deleted)

        self.chat_panel.chat_created.connect(self.sidebar.add_new_chat)
        self.chat_panel.title_generated.connect(
            lambda chat_id, title: self.sidebar.update_chat_metadata(chat_id, title=title)
        )
        self.chat_panel.color_generated.connect(
            lambda chat_id, color: self.sidebar.update_chat_metadata(chat_id, color_hex=color)
        )

        self.settings_drawer.ui_font_changed.connect(lambda _: self._update_global_font())
        self.settings_drawer.ui_font_size_changed.connect(lambda _: self._update_global_font())
        self.settings_drawer.chat_font_changed.connect(lambda _: self.chat_panel.reload_chat_font())
        self.settings_drawer.chat_font_size_changed.connect(lambda _: self.chat_panel.reload_chat_font())

    def _on_new_chat_requested(self):
        self.sidebar.deselect_all()
        self.chat_panel.clear_for_new_chat()

    def _on_chat_deleted(self, deleted_chat_id: str):
        if self.chat_panel.current_chat and self.chat_panel.current_chat["id"] == deleted_chat_id:
            self._on_new_chat_requested()

    def _get_current_font_settings(self):
        font_key = storage.get_setting("ui_font_family", "سیستم (پیش‌فرض)")
        actual_font_name = self.available_fonts.get(font_key, "Segoe UI")
        slider_val = int(storage.get_setting("ui_font_size", "3"))
        px_size = 8 + (slider_val * 2) 
        return actual_font_name, px_size

    def _update_global_font(self):
        actual_font_name, px_size = self._get_current_font_settings()
        pt_size = max(8, px_size - 3)
        
        custom_font = QFont(actual_font_name, pt_size)
        custom_font.setStyleStrategy(QFont.PreferAntialias)
        QApplication.instance().setFont(custom_font)
        
        self._apply_styles(actual_font_name, px_size)

    def _apply_styles(self, font_family: str, px_size: int):
        base_stylesheet = build_stylesheet(font_family, px_size)
        
        extra_stylesheet = """
            QFrame#mainContainer {
                background-color: #17171c; 
                border: 1px solid #33333d;
                border-radius: 8px;
            }
            
            QFrame#customTitleBar {
                background-color: #212128;
                border-bottom: 1px solid #33333d;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QPushButton#windowControlBtn {
                background-color: transparent;
                border: none;
                border-radius: 0px;
            }
            QPushButton#windowControlBtn:hover {
                background-color: rgba(255, 255, 255, 0.08);
            }
            
            QPushButton#closeBtn {
                background-color: transparent;
                border: none;
                border-top-left-radius: 8px; 
                border-bottom-left-radius: 0px;
                border-top-right-radius: 0px;
                border-bottom-right-radius: 0px;
            }
            QPushButton#closeBtn:hover {
                background-color: #e81123;
                border-top-left-radius: 8px;
            }

            QFrame#settingsPanel {
                background-color: #17171c; 
                border: none;
                border-right: 1px solid #33333d; 
                border-radius: 0px; 
                border-bottom-left-radius: 8px; 
            }
            
            QFrame#settingsPanel > QWidget {
                background-color: transparent;
            }

            QPushButton#settingsToggleBtn {
                background-color: transparent;
                color: #9a9aa5;
                font-size: 22px;
                border: none;
                border-radius: 0px;
            }
            QPushButton#settingsToggleBtn:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }

            QSplitter::handle {
                background-color: #33333d;
                width: 1px;
                margin: 0px; 
            }
        """
        self.setStyleSheet(base_stylesheet + extra_stylesheet)


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)

    loaded_fonts = _load_app_fonts()
    
    saved_font_key = storage.get_setting("ui_font_family", "سیستم (پیش‌فرض)")
    actual_font_name = loaded_fonts.get(saved_font_key, "Segoe UI")
    slider_val = int(storage.get_setting("ui_font_size", "3"))
    initial_pt_size = max(8, (8 + (slider_val * 2)) - 3)
    
    custom_font = QFont(actual_font_name, initial_pt_size)
    custom_font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(custom_font)

    window = MainWindow(available_fonts=loaded_fonts)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()