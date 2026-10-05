"""
کامپوننت پنل گفتگوی مرکزی (Chat Panel) - معماری لایه‌بندی شده (مسیر: ui/chat_panel.py)
مسئولیت‌ها:
۱. مدیریت رابط کاربری چت و اتصال به موتور وب.
۲. انیمیشن نرم برای فوکوس و تغییر حالت چت.
۳. مدیریت هوشمند منوی راست‌کلیک با آیکون‌های SVG (از پوشه resources).
۴. ارتباط با لایه‌های core، utils و data به جای وارد کردن مستقیم.
"""

import os
import sys
import json
import ctypes
import markdown

# تنظیم مسیر ریشه پروژه برای دسترسی به سایر پوشه‌ها
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

from PySide6.QtCore import Qt, Signal, QThread, QEvent, QUrl, QTimer, Property, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QResizeEvent, QAction, QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QTextEdit, QPushButton, QFrame, QMessageBox, QFileDialog, QApplication
)

from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView

# ===================================================================
# ایمپورت‌ها بر اساس معماری ۵ پوشه‌ای جدید
# ===================================================================
from core.prompts import SYSTEM_PROMPTS
from core import config
from core.workers import SuggestionWorker, TitleWorker, ColorWorker
from data import storage
from ui.widgets import RIGHT, force_rtl
from ui.web_engine import CustomWebPage
from utils.template import HTML_TEMPLATE
from utils.font_manager import ensure_local_assets, get_uninstalled_fonts
from utils.pdf_exporter import PdfExporter


class ChatWebView(QWebEngineView):
    """مرورگر شخصی‌سازی شده برای مدیریت منوی راست‌کلیک و افزودن گزینه‌های هوشمند"""
    
    custom_action_requested = Signal(str, str, int)

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        if not menu:
            return
            
        menu.setStyleSheet("""
            QMenu {
                background-color: #212128;
                color: #f1f1f1;
                border: 1px solid #33333d;
                border-radius: 8px;
                padding: 6px 0px;
            }
            QMenu::item {
                padding: 8px 35px 8px 35px;
                border-radius: 4px;
                margin: 2px 8px;
            }
            QMenu::item:selected {
                background-color: rgba(255, 255, 255, 0.08);
            }
            QMenu::icon {
                padding: 0px 10px;
            }
            QMenu::separator {
                height: 1px;
                background-color: #33333d;
                margin: 4px 15px;
            }
        """)
            
        unwanted_actions = [
            QWebEnginePage.WebAction.Back,
            QWebEnginePage.WebAction.Forward,
            QWebEnginePage.WebAction.SavePage,
            QWebEnginePage.WebAction.ViewSource
        ]
        
        for action_type in unwanted_actions:
            action = self.page().action(action_type)
            if action:
                menu.removeAction(action)
                
        title = self.page().title()
        ctx_type = "none"
        ctx_idx = -1
        
        if title.startswith("CTX:"):
            parts = title.split(":")
            if len(parts) >= 3:
                ctx_type = parts[1]
                try:
                    ctx_idx = int(parts[2])
                except ValueError:
                    pass
                    
        if ctx_type in ["ai", "user"]:
            menu.addSeparator()
            
            # آدرس‌دهی جدید به پوشه resources
            icons_dir = os.path.join(PROJECT_ROOT, "resources", "icons")
            
            if ctx_type == "ai":
                copy_act = QAction(QIcon(os.path.join(icons_dir, "Copy.svg")), "کپی متن", self)
                copy_act.triggered.connect(lambda checked=False, x=ctx_idx: self.custom_action_requested.emit("copy", "ai", x))
                menu.addAction(copy_act)
                
                regen_act = QAction(QIcon(os.path.join(icons_dir, "Reprocessing.svg")), "پردازش مجدد", self)
                regen_act.triggered.connect(lambda checked=False, x=ctx_idx: self.custom_action_requested.emit("regen", "ai", x))
                menu.addAction(regen_act)
                
                pdf_act = QAction(QIcon(os.path.join(icons_dir, "File-down.svg")), "دانلود PDF", self)
                pdf_act.triggered.connect(lambda checked=False, x=ctx_idx: self.custom_action_requested.emit("pdf", "ai", x))
                menu.addAction(pdf_act)
                
                branch_act = QAction(QIcon(os.path.join(icons_dir, "branch.svg")), "شاخه جدید", self)
                branch_act.triggered.connect(lambda checked=False, x=ctx_idx: self.custom_action_requested.emit("branch", "ai", x))
                menu.addAction(branch_act)
                
            elif ctx_type == "user":
                copy_act = QAction(QIcon(os.path.join(icons_dir, "Copy.svg")), "کپی متن", self)
                copy_act.triggered.connect(lambda checked=False, x=ctx_idx: self.custom_action_requested.emit("copy", "user", x))
                menu.addAction(copy_act)
                
                resend_act = QAction(QIcon(os.path.join(icons_dir, "Reprocessing.svg")), "ارسال مجدد", self)
                resend_act.triggered.connect(lambda checked=False, x=ctx_idx: self.custom_action_requested.emit("resend", "user", x))
                menu.addAction(resend_act)
                
        menu.exec(event.globalPos())
        menu.deleteLater()


class ChatWidget(QWidget):
    chat_created = Signal(dict)            
    title_generated = Signal(str, str)     
    color_generated = Signal(str, str)     

    def get_focus_progress(self):
        return self._focus_progress

    def set_focus_progress(self, val):
        self._focus_progress = val
        self._update_input_margins()

    focusProgress = Property(float, get_focus_progress, set_focus_progress)

    def get_chat_state_progress(self):
        return self._chat_state_progress

    def set_chat_state_progress(self, val):
        self._chat_state_progress = val
        self._update_input_margins()

    chatStateProgress = Property(float, get_chat_state_progress, set_chat_state_progress)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("chatPanel")
        
        self.current_chat = None
        self._backup_messages = None 
        self.pdf_export_dir = None
        
        self._page_loaded = False
        self._pending_render = False

        self.thread = None
        self.worker = None
        self.title_thread = None
        self.title_worker = None
        self.color_thread = None
        self.color_worker = None
        
        self._focus_progress = 0.0
        self.focus_anim = QPropertyAnimation(self, b"focusProgress")
        self.focus_anim.setDuration(250)
        self.focus_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        self._chat_state_progress = 1.0 
        self.state_anim = QPropertyAnimation(self, b"chatStateProgress")
        self.state_anim.setDuration(600)  
        self.state_anim.setEasingCurve(QEasingCurve.InOutCubic)

        self.assets_dir = ensure_local_assets()
        self._build_ui()
        QTimer.singleShot(1000, self._check_and_request_admin_for_fonts)

    def _update_input_margins(self):
        if not hasattr(self, 'input_wrapper_layout'):
            return
            
        base_bottom = 10 + int(15 * self._focus_progress)
        
        if self.window() and self.window().isMaximized():
            base_side = int(self.width() * 0.075)
        else:
            base_side = 0
            
        input_h = self.input_container.height() if hasattr(self, 'input_container') else 135
        center_bottom_offset = max(0, (self.height() - input_h) // 2)
        center_side_offset = int(self.width() * 0.15) 
        
        final_bottom = base_bottom + int(center_bottom_offset * self._chat_state_progress)
        final_side = base_side + int(center_side_offset * self._chat_state_progress)
        
        self.input_wrapper_layout.setContentsMargins(final_side, 5, final_side, final_bottom)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self._update_input_margins()

    def _check_and_request_admin_for_fonts(self):
        uninstalled = get_uninstalled_fonts()
        if not uninstalled:
            return  

        msg = QMessageBox(self)
        msg.setWindowTitle("نصب فونت‌های برنامه")
        msg.setText("برای نمایش زیبای محیط گفتگو و خروجی فایل‌های PDF، فونت‌های برنامه روی سیستم شما نصب خواهند شد.\n\nاین عملیات در پس‌زمینه انجام می‌شود و نیازمند دسترسی ادمین (Administrator) است.\nآیا مایلید فونت‌ها اکنون نصب شوند؟")
        msg.setIcon(QMessageBox.Information)
        
        yes_btn = msg.addButton("بله، نصب فونت‌ها", QMessageBox.YesRole)
        msg.addButton("خیر", QMessageBox.NoRole)
        msg.setLayoutDirection(Qt.RightToLeft)
        
        msg.exec()
        
        if msg.clickedButton() == yes_btn:
            # آدرس‌دهی جدید اسکریپت نصب فونت در پوشه utils
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
                installer_path = os.path.join(base_dir, "utils", "font_installer.py")
            else:
                installer_path = os.path.join(PROJECT_ROOT, "utils", "font_installer.py")
            
            if os.path.exists(installer_path):
                executable = "python" if not getattr(sys, 'frozen', False) else sys.executable
                params = f'"{installer_path}"'
                
                ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, params, None, 1)
                QTimer.singleShot(4000, self._update_web_font)
            else:
                QMessageBox.warning(self, "خطا", f"فایل font_installer.py در مسیر یافت نشد:\n{installer_path}")

    def reload_chat_font(self):
        self._update_web_font()

    def _update_web_font(self):
        ff, slider_val = storage.get_chat_font()
        size_map = {1: 13, 2: 15, 3: 17, 4: 20, 5: 24}
        fs = size_map.get(slider_val, slider_val)
        
        css = f"""
            :root {{
                --chat-font: "{ff}";
                --chat-size: {fs}px;
            }}
        """
        if self._page_loaded:
            js_code = f"document.getElementById('dynamic-font').innerHTML = `{css}`;"
            self.web_view.page().runJavaScript(js_code)
        return css

    def changeEvent(self, event):
        if event.type() in [QEvent.FontChange, QEvent.ApplicationFontChange]:
            self._update_web_font()
        super().changeEvent(event)

    def _make_label(self, text: str, object_name: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName(object_name)
        label.setAlignment(RIGHT)
        return label

    def _adjust_input_height(self, _=None):
        if not hasattr(self, 'desc_text') or not hasattr(self, 'input_container'):
            return
            
        font_metrics = self.desc_text.fontMetrics()
        line_height = font_metrics.lineSpacing()
        doc_margin = int(self.desc_text.document().documentMargin())
        
        safe_margin = 5
        internal_padding = (doc_margin * 2) + safe_margin
        
        min_height = (line_height * 2) + internal_padding
        max_height = (line_height * 7) + internal_padding
        
        actual_text_height = int(self.desc_text.document().size().height()) + safe_margin
        target_text_height = max(min_height, min(actual_text_height, max_height))
        container_margins = 18
        
        self.input_container.setFixedHeight(target_text_height + container_margins)
        self._update_input_margins()

    def _build_ui(self):
        layout = QVBoxLayout(self)
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

        self.web_view = ChatWebView()
        self.web_page = CustomWebPage()
        
        self.web_page.action_requested.connect(self.on_transcript_action)
        self.web_view.custom_action_requested.connect(self._on_custom_context_action)
        
        self.web_page.setBackgroundColor(Qt.transparent)
        self.web_view.setPage(self.web_page)
        
        self.web_view.loadFinished.connect(self._on_load_finished)
        
        # در معماری جدید، Base URL کرومیوم باید روی پوشه resources تنظیم شود
        # تا بتواند فولدرهای assets و icons را به درستی پیدا کند.
        resources_dir = os.path.join(PROJECT_ROOT, "resources")
        
        modified_template = HTML_TEMPLATE.replace("</style>", """
        .actions a {
            outline: none !important;
            -webkit-user-drag: none;
            user-select: none;
        }
        .actions a:focus {
            outline: none !important;
        }
        </style>
        """)
        
        initial_font_css = self._update_web_font()
        final_html = modified_template.replace("/*DYNAMIC_FONT*/", initial_font_css)
        
        base_url = QUrl.fromLocalFile(resources_dir + "/")
        self.web_view.setHtml(final_html, base_url)
        
        layout.addWidget(self.web_view, stretch=1)

        self.input_container = QFrame()
        self.input_container.setObjectName("inputContainer")

        container_layout = QHBoxLayout(self.input_container)
        container_layout.setContentsMargins(15, 8, 15, 8)
        container_layout.setSpacing(12)

        self.desc_text = QTextEdit()
        self.desc_text.setObjectName("descText")
        self.desc_text.setPlaceholderText("مثلاً: مبتدی هستم و به پردازش تصویر علاقه دارم...")
        self.desc_text.setLineWrapMode(QTextEdit.WidgetWidth)
        force_rtl(self.desc_text)
        self.desc_text.installEventFilter(self)
        container_layout.addWidget(self.desc_text, stretch=1)
        
        self.desc_text.document().documentLayout().documentSizeChanged.connect(self._adjust_input_height)

        btn_column = QVBoxLayout()
        btn_column.setContentsMargins(0, 0, 0, 0)
        btn_column.addStretch(1)

        self.submit_btn = QPushButton("ارسال")
        self.submit_btn.setObjectName("submitBtn")
        self.submit_btn.setFixedSize(90, 36)
        self.submit_btn.setCursor(Qt.PointingHandCursor)
        self.submit_btn.clicked.connect(self.on_submit)
        btn_column.addWidget(self.submit_btn)

        container_layout.addLayout(btn_column)
        
        self.input_wrapper = QWidget()
        self.input_wrapper_layout = QHBoxLayout(self.input_wrapper)
        self.input_wrapper_layout.addWidget(self.input_container)
        self._update_input_margins()
        
        layout.addWidget(self.input_wrapper)
        self._adjust_input_height()

    def eventFilter(self, obj, event):
        if obj == self.desc_text:
            if event.type() == QEvent.FocusIn:
                self.focus_anim.stop()
                self.focus_anim.setEndValue(1.0)
                self.focus_anim.start()
            elif event.type() == QEvent.FocusOut:
                self.focus_anim.stop()
                self.focus_anim.setEndValue(0.0)
                self.focus_anim.start()
        return super().eventFilter(obj, event)

    def _on_load_finished(self, ok):
        self._page_loaded = True
        self._update_web_font()
        
        tracker_script = """
            document.addEventListener('contextmenu', function(e) {
                let u = e.target.closest('.user-msg-container');
                let a = e.target.closest('.ai-msg-container');
                if (u) {
                    document.title = "CTX:user:" + u.getAttribute('data-idx');
                } else if (a) {
                    document.title = "CTX:ai:" + a.getAttribute('data-idx');
                } else {
                    document.title = "CTX:none:-1";
                }
            }, true);
        """
        self.web_view.page().runJavaScript(tracker_script)
        
        if self._pending_render:
            self._render_transcript()
            self._pending_render = False

    def set_chat(self, chat_dict: dict):
        self.current_chat = chat_dict
        model_name = chat_dict.get("model", "Deepseek")
        self.active_chat_label.setText(f'ادامه گفتگو — {chat_dict["language"]} ({model_name})')

        lang_idx = self.lang_combo.findText(chat_dict["language"])
        if lang_idx >= 0:
            self.lang_combo.setCurrentIndex(lang_idx)
        self.lang_combo.setEnabled(False)

        model_idx = self.model_combo.findText(model_name)
        if model_idx >= 0:
            self.model_combo.setCurrentIndex(model_idx)
        self.model_combo.setEnabled(False)

        self._render_transcript()
        
        if self._chat_state_progress > 0:
            self.state_anim.stop()
            self.state_anim.setEndValue(0.0)
            self.state_anim.start()

    def clear_for_new_chat(self):
        self.current_chat = None
        self.active_chat_label.setText("گفتگوی جدید")
        self.lang_combo.setEnabled(True)
        self.model_combo.setEnabled(True)
        self.desc_text.clear()
        
        self._adjust_input_height()
        
        if self._page_loaded:
            self.web_view.page().runJavaScript("initChat([]);")
            
        self.state_anim.stop()
        self.state_anim.setEndValue(1.0)
        self.state_anim.start()

    def _render_transcript(self):
        if not self._page_loaded:
            self._pending_render = True
            return

        if not self.current_chat or not self.current_chat["messages"]:
            self.web_view.page().runJavaScript("initChat([]);")
            return

        html_parts = []
        for idx, msg in enumerate(self.current_chat["messages"]):
            parsed_html = markdown.markdown(
                msg["content"], 
                extensions=['fenced_code', 'tables', 'nl2br', 'sane_lists']
            )
            
            if msg["role"] == "user":
                html_parts.append(
                    f'<div class="user-msg-container" data-idx="{idx}">'
                    f'<div class="user-msg-bubble">{parsed_html}</div>'
                    f'</div>'
                )
            else:
                html_parts.append(
                    f'<div class="ai-msg-container" data-idx="{idx}">'
                    f'<div class="ai-msg-content">{parsed_html}</div>'
                    f'<div class="actions">'
                    f'<a href="http://app.action/copy/{idx}"><div class="action-icon icon-copy"></div> کپی متن</a>'
                    f'<a href="http://app.action/regen/{idx}"><div class="action-icon icon-regen"></div> پردازش مجدد</a>'
                    f'<a href="http://app.action/pdf/{idx}"><div class="action-icon icon-pdf"></div> دانلود PDF</a>'
                    f'<a href="http://app.action/branch/{idx}"><div class="action-icon icon-branch"></div> شاخه جدید</a>'
                    f'</div></div>'
                )

        js_code = f"initChat({json.dumps(html_parts)});"
        self.web_view.page().runJavaScript(js_code)

    def _on_custom_context_action(self, action: str, role: str, idx: int):
        if not self.submit_btn.isEnabled():
            return
            
        if role == "ai":
            self.on_transcript_action(action, idx)
        elif role == "user":
            if action == "copy":
                self._copy_action(idx)
            elif action == "resend":
                self._resend_user_message(idx)

    def on_transcript_action(self, action: str, idx: int):
        if not self.submit_btn.isEnabled():
            return
            
        if action == "copy":
            self._copy_action(idx)
        elif action == "regen":
            self._regenerate_response(idx)
        elif action == "pdf":
            self._export_pdf_chromium(idx)
        elif action == "branch":
            self._branch_chat(idx)

    def _copy_action(self, idx: int):
        msg = self.current_chat["messages"][idx]["content"]
        QApplication.clipboard().setText(msg)
        original_text = self.submit_btn.text()
        self.submit_btn.setText("✅ کپی شد")
        QTimer.singleShot(1500, lambda: self.submit_btn.setText(original_text) if self.submit_btn.text() == "✅ کپی شد" else None)

    def _branch_chat(self, idx: int):
        if not self.current_chat: return
        messages = self.current_chat["messages"]
        if idx < 0 or idx >= len(messages): return

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
        
        self.chat_created.emit(new_chat)
        self.set_chat(new_chat)

    def _export_pdf_chromium(self, idx: int):
        msg = self.current_chat["messages"][idx]["content"]
        
        if not self.pdf_export_dir:
            dir_path = QFileDialog.getExistingDirectory(self, "انتخاب پوشه پیش‌فرض برای ذخیره PDF")
            if not dir_path: return  
            self.pdf_export_dir = dir_path

        safe_title = "".join([c for c in self.current_chat["title"] if c.isalpha() or c.isdigit() or c == ' ']).strip().replace(' ', '_')
        if not safe_title: safe_title = "Chat_Export"
            
        msg_number = sum(1 for m in self.current_chat["messages"][:idx+1] if m.get("role") == "assistant")
        file_name = f"{safe_title}_{msg_number}.pdf"
        file_path = os.path.join(self.pdf_export_dir, file_name)

        self._original_btn_text = self.submit_btn.text()
        self.submit_btn.setText("⏳ در حال ساخت...")
        self.submit_btn.setEnabled(False)

        self.pdf_exporter = PdfExporter(self)
        self.pdf_exporter.export_finished.connect(self._finish_pdf_export)
        self.pdf_exporter.export_message(msg, file_path)

    def _finish_pdf_export(self, success: bool, filepath_or_error: str):
        self.submit_btn.setEnabled(True)
        if success:
            self.submit_btn.setText("✅ PDF ذخیره شد")
        else:
            self.submit_btn.setText("❌ خطا در PDF")
            QMessageBox.critical(self, "خطا", f"مشکلی در تولید فایل پیش آمد:\n{filepath_or_error}")

        QTimer.singleShot(2000, lambda: self.submit_btn.setText(self._original_btn_text) if "PDF" in self.submit_btn.text() else None)
        
        if hasattr(self, 'pdf_exporter'):
            self.pdf_exporter.deleteLater()
            del self.pdf_exporter

    def _resend_user_message(self, idx: int):
        if not self.current_chat: return
        messages = self.current_chat["messages"]
        if idx < 0 or idx >= len(messages) or messages[idx]["role"] != "user": return

        self._backup_messages = messages.copy()
        self.current_chat["messages"] = messages[:idx+1]
        self._render_transcript()

        self._dispatch_api_request()

    def _regenerate_response(self, idx: int):
        if not self.current_chat: return
        messages = self.current_chat["messages"]
        if idx <= 0 or idx >= len(messages) or messages[idx]["role"] != "assistant": return

        self._backup_messages = messages.copy()
        self.current_chat["messages"] = messages[:idx]
        self._render_transcript()

        self._dispatch_api_request()

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
            is_new_chat = True

        self.current_chat["messages"].append({"role": "user", "content": desc})
        
        trigger_title_worker = False
        if is_new_chat:
            trigger_title_worker = True
        elif self.current_chat.get("needs_new_title"):
            trigger_title_worker = True
            self.current_chat["needs_new_title"] = False
            
        storage.update_chat(self.current_chat)
        
        if is_new_chat:
            self.chat_created.emit(self.current_chat)
            self.set_chat(self.current_chat)
        else:
            self._render_transcript()
            
        self.desc_text.clear()
        self._adjust_input_height()
        
        if self._chat_state_progress > 0:
            self.state_anim.stop()
            self.state_anim.setEndValue(0.0)
            self.state_anim.start()

        if trigger_title_worker:
            self.title_worker = TitleWorker(desc, self.current_chat["id"])
            self.title_thread = self._run_worker(self.title_worker, self.on_title_ready)

        self._dispatch_api_request()

    def _dispatch_api_request(self):
        self.submit_btn.setEnabled(False)
        self.submit_btn.setText("⏳ صبر کنید")

        system_prompt = SYSTEM_PROMPTS[self.current_chat["language"]]
        api_messages = [{"role": "system", "content": system_prompt}]
        api_messages.extend(self.current_chat["messages"])

        current_model_name = self.current_chat.get("model", "Deepseek")
        actual_model_id = config.AVAILABLE_MODELS.get(current_model_name, config.AVAILABLE_MODELS["Deepseek"])

        self.worker = SuggestionWorker(api_messages, actual_model_id)
        self.thread = self._run_worker(self.worker, self.on_result_ready)

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

    def on_title_ready(self, title: str, chat_id: str):
        chats = storage.load_chats()
        for chat in chats:
            if chat["id"] == chat_id:
                chat["title"] = title
                storage.update_chat(chat) 
                
                if self.current_chat and self.current_chat["id"] == chat_id:
                    self.current_chat["title"] = title
                    
                self.title_generated.emit(chat_id, title)
                break

    def on_color_ready(self, color_hex: str, chat_id: str):
        chats = storage.load_chats()
        for chat in chats:
            if chat["id"] == chat_id:
                chat["color"] = color_hex
                storage.update_chat(chat)
                
                if self.current_chat and self.current_chat["id"] == chat_id:
                    self.current_chat["color"] = color_hex
                    
                self.color_generated.emit(chat_id, color_hex)
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
            if self._backup_messages is not None:
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