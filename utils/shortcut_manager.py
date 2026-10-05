"""
مدیر میانبرهای کیبورد (Shortcut Manager)
مسیر: utils/shortcut_manager.py
---------------------------------------------------
وظیفه این کلاس شنود و مدیریت تمامی میانبرهای کیبورد برنامه است.
این فایل با الگوی Dependency Injection طراحی شده و پنجره اصلی (MainWindow)
را به عنوان ورودی می‌گیرد تا بتواند دستورات را مستقیماً به بخش‌های مختلف ارسال کند.

در این نسخه، ارتباط با پیام شناور (ToastNotification) اضافه شده است تا پس از اجرای
دستورات مهم (مثل کپی کردن)، به کاربر بازخورد بصری مناسب داده شود.
"""

from PySide6.QtCore import QObject, Qt, QEvent
from PySide6.QtGui import QKeySequence, QShortcut

class ShortcutManager(QObject):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.mw = main_window
        
        # ۱. راه‌اندازی فیلترهای رویداد (برای محیط تایپ پیام)
        self._install_event_filters()
        
        # ۲. راه‌اندازی میانبرهای ترکیبی (Global Shortcuts)
        self._register_global_shortcuts()

    def _install_event_filters(self):
        """فیلتر کردن رویدادهای کیبورد اختصاصی برای کادر متنی پیام‌ها"""
        if hasattr(self.mw, 'chat_panel') and hasattr(self.mw.chat_panel, 'desc_text'):
            self.mw.chat_panel.desc_text.installEventFilter(self)

    def eventFilter(self, obj, event):
        """پردازش کلیدهای Enter و Shift+Enter در زمان تایپ"""
        if hasattr(self.mw, 'chat_panel') and obj == self.mw.chat_panel.desc_text:
            if event.type() == QEvent.KeyPress:
                # بررسی فشرده شدن کلید Enter
                if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                    # اگر Shift نگه داشته شده بود (Shift + Enter) -> ایجاد خط جدید
                    if event.modifiers() == Qt.ShiftModifier:
                        return False # اجازه می‌دهیم خود QTextEdit خط جدید را بسازد
                    
                    # اگر فقط Enter زده شد -> ارسال پیام
                    elif event.modifiers() == Qt.NoModifier:
                        if self.mw.chat_panel.submit_btn.isEnabled():
                            self.mw.chat_panel.on_submit()
                        return True # مصرف رویداد (جلوگیری از ایجاد خط جدید)
                        
        return super().eventFilter(obj, event)

    def _register_global_shortcuts(self):
        """ثبت تمام میانبرهای ترکیبی در یک دیکشنری برای توسعه‌پذیری بالا"""
        shortcuts = {
            "Ctrl+Alt+C": self.copy_last_ai_msg,
            "Ctrl+Alt+R": self.regen_last_ai_msg,
            "Ctrl+Alt+P": self.pdf_last_ai_msg,
            "Ctrl+Alt+B": self.branch_last_ai_msg,
            "Ctrl+Alt+S": self.toggle_settings,
            "Ctrl+Alt+T": self.toggle_theme_mode,
            "Ctrl+Alt+D": lambda: self.set_theme("dark"),
            "Ctrl+Alt+L": lambda: self.set_theme("light"),
            "Ctrl+Alt+=": lambda: self.adjust_ui_font(1),
            "Ctrl+Alt+-": lambda: self.adjust_ui_font(-1),
            "Ctrl+Alt+]": lambda: self.adjust_chat_font(1),
            "Ctrl+Alt+[": lambda: self.adjust_chat_font(-1),
            "Ctrl+Alt+H": self.toggle_sidebar,
            "PageUp": self.scroll_up,
            "PageDown": self.scroll_down,
        }

        for key_combo, func in shortcuts.items():
            shortcut = QShortcut(QKeySequence(key_combo), self.mw)
            shortcut.setContext(Qt.ApplicationShortcut)
            shortcut.activated.connect(func)

    # =========================================================
    # توابع کمکی و منطق اجرایی میانبرها
    # =========================================================

    def _get_last_ai_index(self):
        """یک تابع کمکی برای پیدا کردن ایندکسِ آخرین پیام هوش مصنوعی در چت فعلی"""
        if not hasattr(self.mw, 'chat_panel') or not self.mw.chat_panel.current_chat:
            return -1
        
        messages = self.mw.chat_panel.current_chat.get("messages", [])
        # جستجو از انتها به ابتدا برای پیدا کردن آخرین پاسخ سیستم
        for i in range(len(messages) - 1, -1, -1):
            if messages[i].get("role") == "assistant":
                return i
        return -1

    def copy_last_ai_msg(self):
        idx = self._get_last_ai_index()
        if idx != -1: 
            self.mw.chat_panel._copy_action(idx)
            # نمایش پیام شناور
            if hasattr(self.mw, 'toast'):
                self.mw.toast.show_message("آخرین پیام کپی شد!")

    def regen_last_ai_msg(self):
        idx = self._get_last_ai_index()
        if idx != -1: 
            self.mw.chat_panel._regenerate_response(idx)
            if hasattr(self.mw, 'toast'):
                self.mw.toast.show_message("در حال پردازش مجدد پیام...")

    def pdf_last_ai_msg(self):
        idx = self._get_last_ai_index()
        if idx != -1: 
            self.mw.chat_panel._export_pdf_chromium(idx)
            if hasattr(self.mw, 'toast'):
                self.mw.toast.show_message("در حال تهیه خروجی PDF...")

    def branch_last_ai_msg(self):
        idx = self._get_last_ai_index()
        if idx != -1: 
            self.mw.chat_panel._branch_chat(idx)
            if hasattr(self.mw, 'toast'):
                self.mw.toast.show_message("شاخه جدید با موفقیت ایجاد شد!")

    def toggle_settings(self):
        if hasattr(self.mw, 'settings_drawer'):
            self.mw.settings_drawer.toggle_drawer()

    # ---------------------------------------------------------
    # توابع هدایت درخواست‌های ظاهری به سمت پنل تنظیمات
    # ---------------------------------------------------------

    def set_theme(self, mode_name):
        """ارسال دستور تغییر مستقیم تم به پنل تنظیمات"""
        if hasattr(self.mw, 'settings_drawer'):
            self.mw.settings_drawer.set_theme_from_shortcut(mode_name)

    def toggle_theme_mode(self):
        """ارسال دستور چرخش تم به پنل تنظیمات"""
        if hasattr(self.mw, 'settings_drawer'):
            self.mw.settings_drawer.toggle_theme_from_shortcut()

    def adjust_ui_font(self, step):
        """ارسال دستور حرکت دادن اسلایدر فونت UI به پنل تنظیمات"""
        if hasattr(self.mw, 'settings_drawer'):
            self.mw.settings_drawer.step_ui_font(step)

    def adjust_chat_font(self, step):
        """ارسال دستور حرکت دادن اسلایدر فونت چت به پنل تنظیمات"""
        if hasattr(self.mw, 'settings_drawer'):
            self.mw.settings_drawer.step_chat_font(step)

    # ---------------------------------------------------------

    def toggle_sidebar(self):
        """باز و بسته کردن سایدبار (لیست گفتگوها)"""
        if not hasattr(self.mw, 'splitter'): return
        
        sizes = self.mw.splitter.sizes()
        if sizes[0] == 0:
            self.mw._restore_sidebar()
        else:
            total = sum(sizes)
            self.mw.splitter.setSizes([0, total])
            # فراخوانی دستی متد برای بروزرسانی استایلِ نوار رنگی
            self.mw._on_splitter_moved(0, 1)

    def scroll_up(self):
        """اسکرول سریع به بالا در صفحه چت"""
        if hasattr(self.mw, 'chat_panel') and self.mw.chat_panel._page_loaded:
            self.mw.chat_panel.web_view.page().runJavaScript("window.scrollBy(0, -500);")

    def scroll_down(self):
        """اسکرول سریع به پایین در صفحه چت"""
        if hasattr(self.mw, 'chat_panel') and self.mw.chat_panel._page_loaded:
            self.mw.chat_panel.web_view.page().runJavaScript("window.scrollBy(0, 500);")