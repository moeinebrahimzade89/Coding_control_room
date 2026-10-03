"""
برنامه پیشنهاددهنده پروژه برنامه‌نویسی (نسخه نهایی پیشرفته)
- دارای سایدبار منعطف (QSplitter) و منطقه امن
- مدیریت خطای کامل (UI + Thread)
- بارگذاری اختصاصی فونت (Estedad) از پوشه داخلی پروژه
- قابلیت انتخاب پویای مدل هوش مصنوعی برای هر مکالمه
- تشخیص هوشمند موضوع و اختصاص نوار رنگی در لبه‌ی راست هر چت
- سیستم فیلتر و مرتب‌سازی سه‌گانه
- دارای منوی سه‌نقطه (Hover) برای تغییر نام و حذف گفتگو در سایدبار
- استفاده از دیتابیس SQLite برای سرعت بالا در ثبت و ذخیره پیام‌ها
- به‌روزرسانی نقطه‌ای (In-Place Update) سایدبار برای جلوگیری از لگ
- سیستم بک‌آپ‌گیری از تاریخچه برای جلوگیری از حذف پیام در خطای پردازش مجدد
- قابلیت استخراج پاسخ‌ها به صورت فایل PDF راست‌چین (تزریق HTML)
- نام‌گذاری هوشمند فایل‌های PDF
- قابلیت ایجاد شاخه جدید (Branching) از هر نقطه‌ی گفتگو
- ★ حذف گزینه‌های پیش‌فرض انگلیسی از منوی راست‌کلیک و ایجاد منوی کاملاً سفارشی ★

نصب پیش‌نیاز:
    pip install PySide6 openai groq

اجرا:
    python main.py
"""

import sys
import os
import time

from PySide6.QtCore import Qt, QThread, QSize, QEvent, QUrl, QTimer
from PySide6.QtGui import (
    QFont, QFontDatabase, QDesktopServices, QPdfWriter, 
    QTextDocument, QTextOption, QTextCursor, QTextBlockFormat
)
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QTextEdit, QTextBrowser, QPushButton, QFrame, QMessageBox,
    QListWidget, QListWidgetItem, QMenu, QSplitter,
    QInputDialog, QLineEdit, QFileDialog
)

from prompts import SYSTEM_PROMPTS
import storage
import config
from workers import SuggestionWorker, TitleWorker, ColorWorker
from widgets import RIGHT, force_rtl, ChatItemDelegate, ChatItemWidget, build_stylesheet


# ---------- پنجره اصلی ----------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.thread = None
        self.worker = None
        self.title_thread = None
        self.title_worker = None
        self.color_thread = None
        self.color_worker = None
        
        self._backup_messages = None 
        self.pdf_export_dir = None
        self._msg_bounds = []

        self.chats = storage.load_chats()
        self.current_chat = None

        self.current_sort_mode = 'time'
        self.time_descending = True

        self.setWindowTitle("پیشنهاددهنده پروژه برنامه‌نویسی")
        self.resize(980, 720)
        self.setLayoutDirection(Qt.RightToLeft)

        self._build_ui()
        self._apply_styles()
        self._refresh_sidebar()

    # --- متد مدیریت افکت تغییر رنگ باکس ورودی هنگام کلیک ---
    def eventFilter(self, obj, event):
        if obj == self.desc_text:
            if event.type() == QEvent.FocusIn:
                self.input_container.setProperty("focused", "true")
                self.input_container.style().unpolish(self.input_container)
                self.input_container.style().polish(self.input_container)
            elif event.type() == QEvent.FocusOut:
                self.input_container.setProperty("focused", "false")
                self.input_container.style().unpolish(self.input_container)
                self.input_container.style().polish(self.input_container)
        return super().eventFilter(obj, event)

    # ===================================================================
    # ساخت رابط کاربری
    # ===================================================================
    def _build_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(20, 20, 20, 20)
        outer_layout.setSpacing(12)

        outer_layout.addWidget(self._make_label("پیشنهاددهنده پروژه برنامه‌نویسی", "title"))
        outer_layout.addWidget(self._make_label(
            "یک زبان انتخاب کن، هدفت را توضیح بده و یک ایده پروژه بگیر — گفتگوهای قبلی ذخیره می‌مانند.",
            "subtitle"
        ))

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setObjectName("divider")
        outer_layout.addWidget(divider)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        splitter.addWidget(self._build_sidebar())
        splitter.addWidget(self._build_main_panel())

        splitter.setSizes([250, 730])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        outer_layout.addWidget(splitter, stretch=1)

    def _make_label(self, text: str, object_name: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName(object_name)
        label.setAlignment(RIGHT)
        return label

    def _make_sort_button(self, icon_text: str, tooltip: str, slot) -> QPushButton:
        btn = QPushButton(icon_text)
        btn.setObjectName("sortBtn")
        btn.setToolTip(tooltip)
        btn.setFixedSize(28, 28)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(slot)
        return btn

    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setMaximumWidth(450)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(10)

        self.new_chat_btn = QPushButton("+ گفتگوی جدید")
        self.new_chat_btn.setObjectName("newChatBtn")
        self.new_chat_btn.setCursor(Qt.PointingHandCursor)
        self.new_chat_btn.clicked.connect(self.on_new_chat)
        layout.addWidget(self.new_chat_btn)

        history_header_layout = QHBoxLayout()
        history_header_layout.addWidget(self._make_label("گفتگوهای قبلی:", "fieldLabel"))
        history_header_layout.addStretch(1)

        self.btn_sort_lang = self._make_sort_button("💻", "مرتب‌سازی بر اساس زبان برنامه‌نویسی", self.sort_by_language)
        self.btn_sort_color = self._make_sort_button("🎨", "مرتب‌سازی بر اساس موضوع پروژه", self.sort_by_color)
        self.btn_sort_time = self._make_sort_button("🕒", "مرتب‌سازی بر اساس زمان", self.sort_by_time)

        history_header_layout.addWidget(self.btn_sort_lang)
        history_header_layout.addWidget(self.btn_sort_color)
        history_header_layout.addWidget(self.btn_sort_time)

        layout.addLayout(history_header_layout)

        self.history_list = QListWidget()
        self.history_list.setLayoutDirection(Qt.RightToLeft)
        self.history_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.history_list.setItemDelegate(ChatItemDelegate(self.history_list))
        self.history_list.itemClicked.connect(self.on_history_item_clicked)

        self.history_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.history_list.customContextMenuRequested.connect(self.on_history_context_menu)

        layout.addWidget(self.history_list, stretch=1)

        return sidebar

    def _build_main_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(10)

        self.active_chat_label = self._make_label("گفتگوی جدید", "activeChatLabel")
        layout.addWidget(self.active_chat_label)

        options_row = QHBoxLayout()
        options_row.setSpacing(15)

        options_row.addWidget(self._make_label("زبان برنامه‌نویسی:", "fieldLabel"))

        self.lang_combo = QComboBox()
        self.lang_combo.addItems(list(SYSTEM_PROMPTS.keys()))
        self.lang_combo.setLayoutDirection(Qt.RightToLeft)
        self.lang_combo.view().setLayoutDirection(Qt.RightToLeft)
        options_row.addWidget(self.lang_combo)

        options_row.addWidget(self._make_label("مدل هوش مصنوعی:", "fieldLabel"))

        self.model_combo = QComboBox()
        self.model_combo.addItems(list(config.AVAILABLE_MODELS.keys()))
        self.model_combo.setLayoutDirection(Qt.RightToLeft)
        self.model_combo.view().setLayoutDirection(Qt.RightToLeft)
        options_row.addWidget(self.model_combo)

        options_row.addStretch(1)
        layout.addLayout(options_row)

        self.transcript_browser = QTextBrowser()
        self.transcript_browser.setOpenExternalLinks(False) 
        self.transcript_browser.setOpenLinks(False) 
        
        self.transcript_browser.anchorClicked.connect(self.on_transcript_action)
        
        self.transcript_browser.setContextMenuPolicy(Qt.CustomContextMenu)
        self.transcript_browser.customContextMenuRequested.connect(self.on_transcript_context_menu)
        
        self.transcript_browser.setLineWrapMode(QTextBrowser.WidgetWidth)
        force_rtl(self.transcript_browser)
        layout.addWidget(self.transcript_browser, stretch=1)

        layout.addWidget(self._make_label("پیام شما:", "fieldLabel"))

        self.input_container = QFrame()
        self.input_container.setObjectName("inputContainer")
        self.input_container.setFixedHeight(135)

        container_layout = QHBoxLayout(self.input_container)
        container_layout.setContentsMargins(4, 4, 4, 4)
        container_layout.setSpacing(8)

        self.desc_text = QTextEdit()
        self.desc_text.setObjectName("descText")
        self.desc_text.setPlaceholderText("مثلاً: مبتدی هستم و به پردازش تصویر علاقه دارم...")
        self.desc_text.setLineWrapMode(QTextEdit.WidgetWidth)
        force_rtl(self.desc_text)
        self.desc_text.installEventFilter(self)

        container_layout.addWidget(self.desc_text, stretch=1)

        btn_column = QVBoxLayout()
        btn_column.setContentsMargins(12, 0, 12, 10)
        btn_column.addStretch(1)

        self.submit_btn = QPushButton("ارسال")
        self.submit_btn.setObjectName("submitBtn")
        self.submit_btn.setFixedSize(90, 36)
        self.submit_btn.setCursor(Qt.PointingHandCursor)
        self.submit_btn.clicked.connect(self.on_submit)

        btn_column.addWidget(self.submit_btn)
        container_layout.addLayout(btn_column)

        layout.addWidget(self.input_container)

        return panel

    def _apply_styles(self):
        app_font_family = QApplication.font().family()
        self.setStyleSheet(build_stylesheet(app_font_family))

    # ===================================================================
    # متدهای کمکی و مرتب‌سازی
    # ===================================================================
    def _find_list_item(self, chat_id: str):
        for i in range(self.history_list.count()):
            item = self.history_list.item(i)
            if item.data(Qt.UserRole) == chat_id:
                return item
        return None

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
        self._refresh_sidebar()

    def sort_by_color(self):
        self.current_sort_mode = 'color'
        self._refresh_sidebar()

    def sort_by_language(self):
        self.current_sort_mode = 'language'
        self._refresh_sidebar()

    # ===================================================================
    # مدیریت رویدادهای تغییر نام و حذف در سایدبار
    # ===================================================================
    def on_chat_rename(self, chat_id):
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

    def on_chat_delete(self, chat_id):
        storage.delete_chat(chat_id)
        self.chats = [c for c in self.chats if c["id"] != chat_id]
        
        item = self._find_list_item(chat_id)
        if item:
            row = self.history_list.row(item)
            self.history_list.takeItem(row)
            
        if self.current_chat and self.current_chat["id"] == chat_id:
            self.on_new_chat()

    def on_history_context_menu(self, pos):
        item = self.history_list.itemAt(pos)
        if item is None:
            return

        chat_id = item.data(Qt.UserRole)

        menu = QMenu(self)
        menu.setLayoutDirection(Qt.RightToLeft)

        rename_action = menu.addAction("تغییر عنوان")
        delete_action = menu.addAction("حذف گفتگو")

        action = menu.exec(self.history_list.mapToGlobal(pos))

        if action == rename_action:
            self.on_chat_rename(chat_id)
        elif action == delete_action:
            self.on_chat_delete(chat_id)

    # ===================================================================
    # پنل کناری: ساخت اولیه لیست گفتگوها
    # ===================================================================
    def _refresh_sidebar(self):
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
            item = QListWidgetItem()
            item.setData(Qt.UserRole, chat["id"])
            item.setData(Qt.UserRole + 1, chat.get("color", "#808080"))

            widget = ChatItemWidget(chat)
            widget.rename_requested.connect(self.on_chat_rename)
            widget.delete_requested.connect(self.on_chat_delete)

            item.setSizeHint(QSize(0, 75))

            self.history_list.addItem(item)
            self.history_list.setItemWidget(item, widget)

            if self.current_chat and chat["id"] == self.current_chat["id"]:
                item.setSelected(True)

    def on_history_item_clicked(self, item: QListWidgetItem):
        chat_id = item.data(Qt.UserRole)
        chat = next((c for c in self.chats if c["id"] == chat_id), None)
        if chat is None:
            return
        self.current_chat = chat

        model_name = chat.get("model", "Deepseek")
        self.active_chat_label.setText(f'ادامه گفتگو — {chat["language"]} ({model_name})')

        lang_index = self.lang_combo.findText(chat["language"])
        if lang_index >= 0:
            self.lang_combo.setCurrentIndex(lang_index)
        self.lang_combo.setEnabled(False)

        model_index = self.model_combo.findText(model_name)
        if model_index >= 0:
            self.model_combo.setCurrentIndex(model_index)
        self.model_combo.setEnabled(False)

        self._render_transcript()

    def on_new_chat(self):
        self.current_chat = None
        self.active_chat_label.setText("گفتگوی جدید")

        self.lang_combo.setEnabled(True)
        self.model_combo.setEnabled(True)

        self.desc_text.clear()
        self.transcript_browser.clear()
        self.history_list.clearSelection()

    # ===================================================================
    # رندر کردن متن چت‌ها و نقشه‌برداری برای راست‌کلیک
    # ===================================================================
    def _render_transcript(self):
        if not self.current_chat or not self.current_chat["messages"]:
            self.transcript_browser.clear()
            self._msg_bounds = []
            return

        parts = []
        for i, msg in enumerate(self.current_chat["messages"]):
            if msg["role"] == "user":
                parts.append(f'**🧑 شما:**\n\n{msg["content"]}\n\n---\n')
            else:
                parts.append(f'**🤖 پیشنهاد هوش مصنوعی:**\n\n{msg["content"]}\n\n')
                parts.append(f'[ 📋 کپی متن ](copy:{i}) &nbsp;&nbsp;&nbsp;&nbsp; [ 🔄 پردازش مجدد ](regen:{i}) &nbsp;&nbsp;&nbsp;&nbsp; [ 📄 دانلود PDF ](pdf:{i}) &nbsp;&nbsp;&nbsp;&nbsp; [ 🌿 شاخه جدید ](branch:{i})\n\n---\n')

        self.transcript_browser.setMarkdown("\n".join(parts))
        force_rtl(self.transcript_browser)
        
        full_text = self.transcript_browser.toPlainText()
        self._msg_bounds = []
        current_pos = 0
        for i, msg in enumerate(self.current_chat["messages"]):
            marker = "شما:" if msg["role"] == "user" else "پیشنهاد هوش مصنوعی:"
            idx = full_text.find(marker, current_pos)
            if idx != -1:
                self._msg_bounds.append((idx, i))
                current_pos = idx + len(marker)
                
        scrollbar = self.transcript_browser.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    # ===================================================================
    # مدیریت منوی راست‌کلیک روی مرورگر متن (Context Menu)
    # ===================================================================
    def on_transcript_context_menu(self, pos):
        if not self.current_chat or not self.current_chat["messages"]:
            return

        cursor = self.transcript_browser.cursorForPosition(pos)
        click_pos = cursor.position()

        target_idx = -1
        for start_pos, msg_i in reversed(self._msg_bounds):
            if click_pos >= start_pos:
                target_idx = msg_i
                break

        if target_idx == -1 and self._msg_bounds:
            target_idx = self._msg_bounds[0][1]

        if target_idx == -1:
            return

        if self.current_chat["messages"][target_idx]["role"] == "user":
            if target_idx + 1 < len(self.current_chat["messages"]):
                target_idx += 1
            else:
                return 

        if self.current_chat["messages"][target_idx]["role"] != "assistant":
            return

        # تغییر کلیدی: به جای استفاده از منوی استاندارد، یک منوی کاملاً خالی می‌سازیم
        menu = QMenu(self.transcript_browser)
        menu.setLayoutDirection(Qt.RightToLeft)

        copy_action = menu.addAction("📋 کپی کل این پیام")
        regen_action = menu.addAction("🔄 پردازش مجدد")
        pdf_action = menu.addAction("📄 دانلود PDF")
        branch_action = menu.addAction("🌿 شاخه جدید")

        action = menu.exec(self.transcript_browser.mapToGlobal(pos))

        if action == copy_action:
            msg = self.current_chat["messages"][target_idx]["content"]
            QApplication.clipboard().setText(msg)
            original_text = self.submit_btn.text()
            self.submit_btn.setText("✅ کپی شد")
            QTimer.singleShot(1500, lambda: self.submit_btn.setText(original_text) if self.submit_btn.text() == "✅ کپی شد" else None)
        elif action == regen_action:
            self._regenerate_response(target_idx)
        elif action == pdf_action:
            self._export_pdf(target_idx)
        elif action == branch_action:
            self._branch_chat(target_idx)

    # ===================================================================
    # مدیریت کلیک روی دکمه‌های لینک (کپی / رفرش / PDF / شاخه جدید)
    # ===================================================================
    def on_transcript_action(self, url: QUrl):
        url_str = url.toString()
        
        if url_str.startswith("http"):
            QDesktopServices.openUrl(url)
            return
            
        if not self.submit_btn.isEnabled():
            return
            
        if ":" not in url_str:
            return
            
        action, idx_str = url_str.split(":", 1)
        try:
            idx = int(idx_str)
        except ValueError:
            return
            
        if action == "copy":
            msg = self.current_chat["messages"][idx]["content"]
            QApplication.clipboard().setText(msg)
            
            original_text = self.submit_btn.text()
            self.submit_btn.setText("✅ کپی شد")
            QTimer.singleShot(1500, lambda: self.submit_btn.setText(original_text) if self.submit_btn.text() == "✅ کپی شد" else None)
            
        elif action == "regen":
            self._regenerate_response(idx)
            
        elif action == "pdf":
            self._export_pdf(idx)
            
        elif action == "branch":
            self._branch_chat(idx)

    def _branch_chat(self, idx: int):
        if not self.current_chat: 
            return
            
        messages = self.current_chat["messages"]
        if idx < 0 or idx >= len(messages):
            return

        branch_messages = messages[:idx+1].copy()
        language = self.current_chat["language"]
        model_name = self.current_chat.get("model", "Deepseek")
        parent_color = self.current_chat.get("color", "#808080")
        parent_title = self.current_chat["title"]

        temp_title = f"شاخه: {parent_title}"
        if len(temp_title) > 30:
            temp_title = temp_title[:27] + "..."
            
        new_chat = storage.create_chat(language, model_name, title=temp_title)
        new_chat["messages"] = branch_messages
        new_chat["color"] = parent_color
        new_chat["needs_new_title"] = True 
        
        storage.update_chat(new_chat)
        self.chats.append(new_chat)

        item = QListWidgetItem()
        item.setData(Qt.UserRole, new_chat["id"])
        item.setData(Qt.UserRole + 1, parent_color)

        widget = ChatItemWidget(new_chat)
        widget.rename_requested.connect(self.on_chat_rename)
        widget.delete_requested.connect(self.on_chat_delete)

        item.setSizeHint(QSize(0, 75))

        self.history_list.insertItem(0, item)
        self.history_list.setItemWidget(item, widget)
        
        self.history_list.setCurrentItem(item)
        self.current_chat = new_chat
        self.active_chat_label.setText(f'ادامه گفتگو — {language} ({model_name})')
        self._render_transcript()

    def _export_pdf(self, idx: int):
        msg = self.current_chat["messages"][idx]["content"]
        
        if not self.pdf_export_dir:
            dir_path = QFileDialog.getExistingDirectory(self, "انتخاب پوشه پیش‌فرض برای ذخیره PDF")
            if not dir_path:
                return  
            self.pdf_export_dir = dir_path

        safe_title = "".join([c for c in self.current_chat["title"] if c.isalpha() or c.isdigit() or c == ' ']).strip().replace(' ', '_')
        if not safe_title:
            safe_title = "Chat_Export"
            
        msg_number = sum(1 for m in self.current_chat["messages"][:idx+1] if m.get("role") == "assistant")
        
        file_name = f"{safe_title}_{msg_number}.pdf"
        file_path = os.path.join(self.pdf_export_dir, file_name)

        try:
            temp_doc = QTextDocument()
            temp_doc.setMarkdown(msg)
            html_content = temp_doc.toHtml()
            
            html_content = html_content.replace(
                "<body", 
                "<body dir='rtl' align='right' "
            )
            
            doc = QTextDocument()
            doc.setDefaultFont(QApplication.font())
            
            option = QTextOption()
            option.setTextDirection(Qt.RightToLeft)
            option.setAlignment(Qt.AlignRight)
            doc.setDefaultTextOption(option)
            
            doc.setHtml(html_content)
            
            writer = QPdfWriter(file_path)
            doc.print_(writer)

            original_text = self.submit_btn.text()
            self.submit_btn.setText("✅ PDF ذخیره شد")
            QTimer.singleShot(1500, lambda: self.submit_btn.setText(original_text) if self.submit_btn.text() == "✅ PDF ذخیره شد" else None)
            
        except Exception as e:
            QMessageBox.critical(self, "خطا در استخراج PDF", f"ذخیره فایل با خطا مواجه شد:\n{str(e)}")

    def _regenerate_response(self, idx: int):
        if not self.current_chat: 
            return
            
        messages = self.current_chat["messages"]
        if idx <= 0 or idx >= len(messages) or messages[idx]["role"] != "assistant":
            return

        self._backup_messages = messages.copy()

        self.current_chat["messages"] = messages[:idx]
        self._render_transcript()

        system_prompt = SYSTEM_PROMPTS[self.current_chat["language"]]
        api_messages = [{"role": "system", "content": system_prompt}]
        api_messages.extend(self.current_chat["messages"])

        self.submit_btn.setEnabled(False)
        self.submit_btn.setText("⏳ صبر کنید")

        current_model_name = self.current_chat.get("model", "Deepseek")
        actual_model_id = config.AVAILABLE_MODELS.get(current_model_name, config.AVAILABLE_MODELS["Deepseek"])

        self.worker = SuggestionWorker(api_messages, actual_model_id)
        self.thread = self._run_worker(self.worker, self.on_result_ready)

    # ===================================================================
    # اجرای کارگرهای پس‌زمینه
    # ===================================================================
    def _run_worker(self, worker, on_finished) -> QThread:
        thread = QThread()
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.finished.connect(on_finished)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        thread.start()
        return thread

    # ===================================================================
    # منطق ارسال درخواست اصلی
    # ===================================================================
    def on_submit(self):
        desc = self.desc_text.toPlainText().strip()
        if not desc:
            QMessageBox.warning(self, "هشدار", "لطفاً پیام خود را وارد کنید.")
            return

        is_new_chat = False
        if self.current_chat is None:
            language = self.lang_combo.currentText()
            model_name = self.model_combo.currentText()

            if not language:
                QMessageBox.warning(self, "هشدار", "لطفاً یک زبان برنامه‌نویسی انتخاب کنید.")
                return
            if not model_name:
                QMessageBox.warning(self, "هشدار", "لطفاً مدل هوش مصنوعی را انتخاب کنید.")
                return

            self.current_chat = storage.create_chat(language, model_name)
            self.chats.append(self.current_chat)

            self.lang_combo.setEnabled(False)
            self.model_combo.setEnabled(False)
            self.active_chat_label.setText(f"ادامه گفتگو — {language} ({model_name})")

            is_new_chat = True

        system_prompt = SYSTEM_PROMPTS[self.current_chat["language"]]
        api_messages = [{"role": "system", "content": system_prompt}]
        api_messages.extend(self.current_chat["messages"])
        api_messages.append({"role": "user", "content": desc})

        self.current_chat["messages"].append({"role": "user", "content": desc})
        
        trigger_title_worker = False
        if is_new_chat:
            trigger_title_worker = True
        elif self.current_chat.get("needs_new_title"):
            trigger_title_worker = True
            self.current_chat["needs_new_title"] = False
            
        storage.update_chat(self.current_chat)
        self._render_transcript()
        self.desc_text.clear()

        if is_new_chat:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, self.current_chat["id"])
            item.setData(Qt.UserRole + 1, self.current_chat.get("color", "#808080"))

            widget = ChatItemWidget(self.current_chat)
            widget.rename_requested.connect(self.on_chat_rename)
            widget.delete_requested.connect(self.on_chat_delete)

            item.setSizeHint(QSize(0, 75))

            self.history_list.insertItem(0, item)
            self.history_list.setItemWidget(item, widget)
            self.history_list.setCurrentItem(item)

        if trigger_title_worker:
            self.title_worker = TitleWorker(desc, self.current_chat["id"])
            self.title_thread = self._run_worker(self.title_worker, self.on_title_ready)

        self.submit_btn.setEnabled(False)
        self.submit_btn.setText("⏳ صبر کنید")

        current_model_name = self.current_chat.get("model", "Deepseek")
        actual_model_id = config.AVAILABLE_MODELS.get(current_model_name, config.AVAILABLE_MODELS["Deepseek"])

        self.worker = SuggestionWorker(api_messages, actual_model_id)
        self.thread = self._run_worker(self.worker, self.on_result_ready)

    def on_title_ready(self, title: str, chat_id: str):
        for chat in self.chats:
            if chat["id"] == chat_id:
                chat["title"] = title
                storage.update_chat(chat) 
                
                item = self._find_list_item(chat_id)
                if item:
                    widget = self.history_list.itemWidget(item)
                    if widget:
                        widget.update_text(chat["language"], title)
                break

    def on_color_ready(self, color_hex: str, chat_id: str):
        for chat in self.chats:
            if chat["id"] == chat_id:
                chat["color"] = color_hex
                storage.update_chat(chat) 
                
                item = self._find_list_item(chat_id)
                if item:
                    item.setData(Qt.UserRole + 1, color_hex)
                break

    def on_result_ready(self, success: bool, result: str):
        if success:
            self._backup_messages = None 
            self.current_chat["messages"].append({"role": "assistant", "content": result})
            storage.update_chat(self.current_chat) 
            self._render_transcript()

            if self.current_chat.get("color", "#808080") == "#808080":
                self.color_worker = ColorWorker(result, self.current_chat["id"])
                self.color_thread = self._run_worker(self.color_worker, self.on_color_ready)
        else:
            if getattr(self, '_backup_messages', None) is not None:
                self.current_chat["messages"] = self._backup_messages.copy()
                self._backup_messages = None
            else:
                if self.current_chat["messages"] and self.current_chat["messages"][-1]["role"] == "user":
                    failed_msg = self.current_chat["messages"].pop()["content"]
                    self.desc_text.setText(failed_msg)
                    storage.update_chat(self.current_chat)

            self._render_transcript()
            QMessageBox.critical(self, "خطای ارتباط", "ارتباط با سرور برقرار نشد.\n\n" + result)

        self.submit_btn.setEnabled(True)
        self.submit_btn.setText("ارسال")


# ===================================================================
# بارگذاری فونت اختصاصی
# ===================================================================
def _load_app_font(app: QApplication) -> None:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    font_dir = os.path.join(base_dir, "fonts", "Estedad")
    font_family = "Segoe UI"

    if os.path.exists(font_dir):
        for filename in os.listdir(font_dir):
            if filename.lower().endswith(".ttf"):
                font_path = os.path.join(font_dir, filename)
                font_id = QFontDatabase.addApplicationFont(font_path)
                if font_id != -1 and font_family == "Segoe UI":
                    families = QFontDatabase.applicationFontFamilies(font_id)
                    if families:
                        font_family = families[0]

    custom_font = QFont(font_family, 11)
    custom_font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(custom_font)


def main():
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)

    _load_app_font(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()