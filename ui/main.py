"""
برنامه پیشنهاددهنده پروژه برنامه‌نویسی (معماری لایه‌بندی شده)
نقطه ورود برنامه (مسیر: ui/main.py)
------------------------------------------------------------------
وظایف:
۱. حفظ هویت پنجره بومی برای پشتیبانی کامل از Snap Assist و Task View.
۲. ایجاد هدر سفارشی با طراحی مدرن و استفاده از آیکون‌های SVG پویا.
۳. ارتباط مستقیم با API ویندوز با پشتیبانی از High DPI Scaling.
۴. پشتیبانی کامل از تغییر رنگ پویا (تم تاریک و روشن) با معماری تمیز و یکپارچه.
۵. پشتیبانی از تم‌های هوشمند (تطبیقی و سیستمی) با استفاده از استراتژی ترجمه در لحظه.
"""

import sys
import os
import datetime

# ===================================================================
# تنظیمات مسیردهی پروژه (تعریف Root Directory)
# ===================================================================
# چون این فایل در پوشه ui قرار دارد، یک سطح به عقب برمی‌گردیم تا به پوشه اصلی برسیم
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
sys.path.insert(0, PROJECT_ROOT)

from PySide6.QtCore import Qt, QPoint, QSize, QTimer
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

# اضافه شدن کلاس‌های کاربردی (میانبرها، پیام شناور، نوتفیکیشن دسکتاپ و صفحات راه‌اندازی)
from utils.shortcut_manager import ShortcutManager
from ui.toast import ToastNotification
from utils.notification_manager import NotificationManager
from ui.onboarding import OnboardingWindow
from ui.splash_screen import SplashScreen

# اضافه شدن THEMES, ACCENTS و get_theme_icon برای پشتیبانی از تم و آیکون پویا
from ui.widgets import build_stylesheet, THEMES, ACCENTS, get_theme_icon

# ایمپورت تابع راه‌اندازی مجدد کلاینت‌ها از هسته شبکه
from core.api_client import init_clients


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
        self.btn_maximize = QPushButton()
        self.btn_close = QPushButton()
        self.btn_close.setObjectName("closeBtn")
        
        # مقداردهی اولیه آیکون‌ها. (مقدار واقعی بلافاصله در کلاس MainWindow تنظیم می‌شود)
        self.update_icons("dark")
        
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

    def update_icons(self, theme_mode):
        """دریافت آیکون‌های پویا (سفید/مشکی) از کارخانه تولید آیکون در ui.widgets"""
        self.icon_close = get_theme_icon("Close.svg", theme_mode)
        self.icon_maximize = get_theme_icon("Fullscreen.svg", theme_mode)
        self.icon_restore = get_theme_icon("Exit-Fullscreen.svg", theme_mode)
        self.icon_minimize = get_theme_icon("Minimize.svg", theme_mode)

        self.btn_close.setIcon(self.icon_close)
        self.btn_minimize.setIcon(self.icon_minimize)
        
        if self.parent_window.isMaximized():
            self.btn_maximize.setIcon(self.icon_restore)
        else:
            self.btn_maximize.setIcon(self.icon_maximize)

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

        # متغیری برای ذخیره آخرین عرض سایدبار جهت بازیابیِ بی‌نقص
        self._last_sidebar_size = 250

        self._build_ui()
        self._connect_signals()
        
        self._update_global_font()

        # تایمر هوشمند: هر ۱ دقیقه چک می‌کند که آیا ساعت یا تم سیستم تغییر کرده است یا خیر
        self.theme_timer = QTimer(self)
        self.theme_timer.timeout.connect(self._check_dynamic_theme)
        self.theme_timer.start(60000)

        # ===================================================================
        # راه‌اندازی پیام شناور و سیستم نوتیفیکیشن
        # ===================================================================
        self.toast = ToastNotification(self)
        self.notification_manager = NotificationManager(self)

        # ===================================================================
        # اتصال کلاس مدیریت میانبرها به برنامه
        # ===================================================================
        self.shortcut_manager = ShortcutManager(self)

    def _check_dynamic_theme(self):
        """فراخوانی مجدد آپدیت استایل در صورتی که تم روی سیستم یا تطبیقی باشد"""
        raw_mode, _ = storage.get_theme_settings()
        if raw_mode in ("system", "adaptive"):
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
        # تغییر هوشمندانه: استفاده از HBox برای قرارگیری دکمه بازگشت در کنار اسپیلیتر
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # ======================================================================
        # دکمه بازگشت هوشمند (فقط وقتی سایدبار بسته است نمایش داده می‌شود)
        # ======================================================================
        self.sidebar_toggle_btn = QPushButton()
        self.sidebar_toggle_btn.setObjectName("sidebarToggleBtn")
        self.sidebar_toggle_btn.setFixedWidth(6)
        self.sidebar_toggle_btn.setCursor(Qt.PointingHandCursor)
        self.sidebar_toggle_btn.hide()
        self.sidebar_toggle_btn.clicked.connect(self._restore_sidebar)
        
        # در حالت راست‌چین، آیتمی که اول اضافه می‌شود در سمتِ راست‌ترین قسمت قرار می‌گیرد
        content_layout.addWidget(self.sidebar_toggle_btn)
        
        # تنظیمات سایدبار
        self.sidebar = SidebarWidget()
        sidebar_wrapper = QWidget()
        sidebar_wrapper.setMinimumWidth(0) 
        
        sidebar_layout = QVBoxLayout(sidebar_wrapper)
        # حفظ فاصله‌ی ۲۰ پیکسلی در داخل سایدبار تا طراحی کاملاً دست‌نخورده بماند
        sidebar_layout.setContentsMargins(0, 10, 20, 15)
        sidebar_layout.addWidget(self.sidebar)

        # تنظیمات پنل چت
        self.chat_panel = ChatWidget()
        chat_wrapper = QWidget()
        chat_layout = QVBoxLayout(chat_wrapper)
        # حفظ فاصله‌های پنل چت دقیقاً مطابق نسخه‌های قبلی (چپ:20، بالا:10، راست:20، پایین:15)
        chat_layout.setContentsMargins(20, 10, 20, 15)
        chat_layout.addWidget(self.chat_panel)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setObjectName("mainSplitter")
        
        # عرض ۶ پیکسلی ثابت برای دستگیره تا براحتی با موس گرفته شود
        self.splitter.setHandleWidth(6)
        
        self.splitter.setCollapsible(0, True)   
        self.splitter.setCollapsible(1, False)  
        
        self.splitter.addWidget(sidebar_wrapper)         
        self.splitter.addWidget(chat_wrapper)      
        self.splitter.setSizes([self._last_sidebar_size, 730])
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)

        content_layout.addWidget(self.splitter, stretch=1)
        
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
        self.settings_drawer.theme_mode_changed.connect(lambda _: self._update_global_font())
        self.settings_drawer.accent_color_changed.connect(lambda _: self._update_global_font())
        self.settings_drawer.chat_font_changed.connect(lambda _: self._update_global_font())
        self.settings_drawer.chat_font_size_changed.connect(lambda _: self._update_global_font())
        
        # ======================================================================
        # اتصال سیگنال آپدیت کلیدهای API به هسته شبکه جهت ریست کلاینت‌ها در لحظه
        # ======================================================================
        self.settings_drawer.api_keys_updated.connect(init_clients)
        
        # تشخیص حرکت جداکننده
        self.splitter.splitterMoved.connect(self._on_splitter_moved)

    def _on_splitter_moved(self, pos, index):
        """
        مدیریت هوشمند بسته شدن: 
        وقتی عرض به صفر می‌رسد، دستگیره معمولی مخفی و دکمه بازگشت جذاب نمایش داده می‌شود.
        """
        sizes = self.splitter.sizes()
        is_collapsed = (sizes[0] == 0)
        
        if is_collapsed:
            if self.sidebar_toggle_btn.isHidden():
                self.sidebar_toggle_btn.show()
                # نامرئی کردن و غیرفعال کردن دستگیره باگ‌دار Qt
                self.splitter.setHandleWidth(0) 
        else:
            if not self.sidebar_toggle_btn.isHidden():
                self.sidebar_toggle_btn.hide()
                # بازگرداندن دستگیره برای جابجایی
                self.splitter.setHandleWidth(6)
            # ذخیره عرض برای بازگشت بی‌نقص
            self._last_sidebar_size = sizes[0]

    def _restore_sidebar(self):
        """
        این متد با کلیک روی نوار رنگی اجرا می‌شود و سایدبار را دوباره باز می‌کند.
        """
        self.sidebar_toggle_btn.hide()
        self.splitter.setHandleWidth(6)
        
        restore_size = getattr(self, '_last_sidebar_size', 250)
        if restore_size < 100:
            restore_size = 250
            
        current_sizes = self.splitter.sizes()
        total_width = sum(current_sizes)
        
        # جلوگیری از باگ‌های محاسباتی عرض
        if total_width < restore_size:
            restore_size = total_width // 3
            
        self.splitter.setSizes([restore_size, total_width - restore_size])

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

    def _resolve_theme(self, mode: str) -> str:
        if mode == "adaptive":
            hour = datetime.datetime.now().hour
            if 6 <= hour < 18:
                return "light"
            else:
                return "dark"
        elif mode == "system":
            scheme = QApplication.styleHints().colorScheme()
            if scheme == Qt.ColorScheme.Dark:
                return "dark"
            else:
                return "light"
        return mode

    def _update_global_font(self):
        actual_font_name, px_size = self._get_current_font_settings()
        pt_size = max(8, px_size - 3)
        
        custom_font = QFont(actual_font_name, pt_size)
        custom_font.setStyleStrategy(QFont.PreferAntialias)
        QApplication.instance().setFont(custom_font)
        
        self._apply_styles(actual_font_name, px_size)

    def _apply_styles(self, font_family: str, px_size: int):
        raw_mode, accent_color = storage.get_theme_settings()
        actual_theme = self._resolve_theme(raw_mode)
        
        self.title_bar.update_icons(actual_theme)
        if hasattr(self, 'sidebar'):
            self.sidebar.update_icons(actual_theme)
        if hasattr(self, 'settings_drawer'):
            self.settings_drawer.update_icons(actual_theme)
        
        base_stylesheet = build_stylesheet(font_family, px_size, actual_theme, accent_color)
        
        th = THEMES.get(actual_theme, THEMES["dark"])
        ac = ACCENTS.get(accent_color, ACCENTS["red"])
        
        extra_stylesheet = f"""
            QFrame#mainContainer {{
                background-color: {th['bg']}; 
                border: 1px solid {th['border']};
                border-radius: 8px;
            }}
            
            QFrame#customTitleBar {{
                background-color: {th['panel']};
                border-bottom: 1px solid {th['border']};
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }}
            
            QPushButton#windowControlBtn {{
                background-color: transparent;
                color: {th['muted']};
                border: none;
                border-radius: 0px;
            }}
            QPushButton#windowControlBtn:hover {{
                background-color: {th['hover']};
            }}
            
            QPushButton#closeBtn {{
                background-color: transparent;
                border: none;
                border-top-left-radius: 8px; 
                border-bottom-left-radius: 0px;
                border-top-right-radius: 0px;
                border-bottom-right-radius: 0px;
            }}
            QPushButton#closeBtn:hover {{
                background-color: #e81123;
                border-top-left-radius: 8px;
            }}

            QFrame#settingsPanel {{
                background-color: {th['bg']}; 
                border: none;
                border-right: 1px solid {th['border']}; 
                border-radius: 0px; 
                border-bottom-left-radius: 8px; 
            }}
            
            QFrame#settingsPanel > QWidget {{
                background-color: transparent;
            }}

            QPushButton#settingsToggleBtn {{
                background-color: transparent;
                color: {th['muted']};
                font-size: 22px;
                border: none;
                border-radius: 0px;
            }}
            QPushButton#settingsToggleBtn:hover {{
                background-color: {th['hover']};
            }}
            
            /* ========================================================
               استایل نوار رنگیِ دکمه بازگشت (در زمان بسته بودن سایدبار)
               ======================================================== */
            QPushButton#sidebarToggleBtn {{
                background-color: {ac['base']};
                border: none;
                border-radius: 0px;
            }}
            QPushButton#sidebarToggleBtn:hover {{
                background-color: {ac['hover']};
            }}

            /* ========================================================
               استایل خط جداکننده و دستگیره موس (در زمان باز بودن)
               ======================================================== */
            QSplitter#mainSplitter::handle {{
                background-color: transparent;
                /* ایجاد یک خط ظریف ۲ پیکسلی در دل فضای ۶ پیکسلی */
                border-right: 2px solid {th['border']};
                margin: 0px; 
            }}
            QSplitter#mainSplitter::handle:hover {{
                background-color: {th['hover']};
                border-right: 2px solid {ac['base']};
            }}
        """
        self.setStyleSheet(base_stylesheet + extra_stylesheet)

        if hasattr(self, 'chat_panel'):
            original_get = storage.get_theme_settings
            storage.get_theme_settings = lambda: (actual_theme, accent_color)
            try:
                self.chat_panel.reload_chat_settings()
            finally:
                storage.get_theme_settings = original_get


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)

    # ===================================================================
    # نمایش فوری اسپلش اسکرین در میلی‌ثانیه‌های اولیه اجرای برنامه
    # ===================================================================
    splash = SplashScreen()
    splash.show()
    app.processEvents() # دستور اجباری به سیستم برای رندر کردن آنی صفحه

    # ===================================================================
    # بررسی اولین اجرای برنامه و نمایش ویزارد راه‌اندازی (Onboarding)
    # ===================================================================
    if storage.get_setting("is_first_run", "True") == "True":
        splash.hide() # مخفی کردن موقت اسپلش تا روی پنجره راه‌اندازی نیفتد
        
        wizard = OnboardingWindow()
        wizard.exec()
        init_clients()
        
        splash.show() # نمایش مجدد اسپلش برای پر کردن زمان لود شدن بقیه اجزا
        app.processEvents()

    # پردازش‌های سنگین برنامه از اینجا آغاز می‌شود
    loaded_fonts = _load_app_fonts()
    
    saved_font_key = storage.get_setting("ui_font_family", "سیستم (پیش‌فرض)")
    actual_font_name = loaded_fonts.get(saved_font_key, "Segoe UI")
    slider_val = int(storage.get_setting("ui_font_size", "3"))
    initial_pt_size = max(8, (8 + (slider_val * 2)) - 3)
    
    custom_font = QFont(actual_font_name, initial_pt_size)
    custom_font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(custom_font)

    # ساخت پنجره مرکزی با تمام تنظیمات
    window = MainWindow(available_fonts=loaded_fonts)
    
    # اتمام کار اسپلش اسکرین و نمایش پنجره نهایی
    splash.close()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()