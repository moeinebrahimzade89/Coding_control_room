"""
لایه‌ی نمایش (Presentation Layer) - معماری لایه‌بندی شده (مسیر: ui/widgets.py)

شامل رنگ‌بندی تم، ویجت‌های سفارشی سایدبار (آیتم چت + نماینده‌ی رنگ)،
تابع کمکی راست‌چین‌سازی متن، و شیت استایل (QSS) کل برنامه.
هیچ منطق کسب‌وکاری (business logic) اینجا نیست — فقط ظاهر.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QTextOption, QPainter, QColor
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QMenu,
    QStyledItemDelegate, QSizePolicy
)

# ---------- رنگ‌بندی تم ----------
COLOR_BG = "#17171c"
COLOR_PANEL = "#212128"
COLOR_PANEL_BORDER = "#33333d"
COLOR_RED = "#e5383b"
COLOR_RED_HOVER = "#ff4d4f"
COLOR_RED_PRESSED = "#b3252a"
COLOR_TEXT = "#f1f1f1"
COLOR_MUTED = "#9a9aa5"

RIGHT = Qt.AlignRight | Qt.AlignAbsolute


def force_rtl(text_widget):
    """جهت و چینش متن یک ویجت متنی (QTextEdit/QTextBrowser) را کاملاً راست‌به‌چپ می‌کند."""
    option = text_widget.document().defaultTextOption()
    option.setAlignment(RIGHT)
    option.setTextDirection(Qt.RightToLeft)
    option.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
    text_widget.document().setDefaultTextOption(option)
    text_widget.setLayoutDirection(Qt.RightToLeft)
    text_widget.setAlignment(RIGHT)


class ChatItemDelegate(QStyledItemDelegate):
    """یک نوار رنگی کوچک در لبه‌ی راست هر آیتم سایدبار می‌کشد (رنگ موضوع پروژه)."""

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        color_hex = index.data(Qt.UserRole + 1)
        if color_hex:
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(color_hex))

            rect = option.rect
            bar_width = 4
            margin_right = 4
            margin_y = 2

            x = rect.right() - margin_right - bar_width + 1
            y = rect.top() + margin_y + 3
            h = rect.height() - (margin_y * 2) - 6

            painter.drawRoundedRect(x, y, bar_width, h, 2, 2)
            painter.restore()


class ChatItemWidget(QWidget):
    """ویجت نمایش‌دهنده‌ی هر گفتگو در سایدبار."""

    rename_requested = Signal(str)
    delete_requested = Signal(str)

    def __init__(self, chat, parent=None):
        super().__init__(parent)
        self.chat_id = chat["id"]

        self.setFixedHeight(75)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 20, 5)
        layout.setAlignment(Qt.AlignVCenter)

        self.label = QLabel(f'{chat["language"]}\n{chat["title"]}')
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.label.setAlignment(Qt.AlignRight | Qt.AlignVCenter | Qt.AlignAbsolute)
        self.label.setStyleSheet("background: transparent; border: none; color: #f1f1f1;")
        self.label.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.btn = QPushButton("⋮")
        self.btn.setFixedSize(24, 24)
        self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #9a9aa5;
                font-size: 18px;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.15);
                color: #ffffff;
            }
        """)
        self.btn.hide()

        self.menu = QMenu(self)
        self.menu.setLayoutDirection(Qt.RightToLeft)

        rename_action = self.menu.addAction("تغییر عنوان")
        delete_action = self.menu.addAction("حذف گفتگو")

        rename_action.triggered.connect(lambda: self.rename_requested.emit(self.chat_id))
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.chat_id))

        self.btn.clicked.connect(self.show_menu)

        layout.addWidget(self.label, stretch=1)
        layout.addWidget(self.btn, alignment=Qt.AlignVCenter)

    def update_text(self, language: str, title: str):
        """به‌روزرسانی درجا (In-Place Update) لیبل."""
        self.label.setText(f'{language}\n{title}')

    def show_menu(self):
        pos = self.btn.mapToGlobal(self.btn.rect().bottomLeft())
        self.menu.exec(pos)

    def enterEvent(self, event):
        self.btn.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.btn.hide()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        event.ignore()
        super().mousePressEvent(event)


def build_stylesheet(font_family: str, base_font_size: int = 14) -> str:
    """شیت استایل (QSS) کامل برنامه را با فونت و سایز محاسبه‌شده می‌سازد."""
    
    title_size = base_font_size + 8
    subtitle_size = max(10, base_font_size - 2)
    active_chat_size = base_font_size + 1
    
    return f"""
        QWidget {{
            background-color: {COLOR_BG};
            color: {COLOR_TEXT};
            font-family: "{font_family}", "Segoe UI", "Tahoma", sans-serif;
            font-size: {base_font_size}px;
        }}

        QLabel#title {{
            color: {COLOR_RED};
            font-size: {title_size}px;
            font-weight: bold;
        }}

        QLabel#subtitle {{
            color: {COLOR_MUTED};
            font-size: {subtitle_size}px;
        }}

        QLabel#fieldLabel {{
            color: {COLOR_TEXT};
            font-weight: bold;
            margin-top: 4px;
        }}

        QLabel#activeChatLabel {{
            color: {COLOR_RED};
            font-weight: bold;
            font-size: {active_chat_size}px;
        }}

        QFrame#divider {{
            background-color: {COLOR_PANEL_BORDER};
            max-height: 1px;
            border: none;
        }}

        QWidget#sidebar {{
            background-color: transparent;
        }}

        QMenu {{
            background-color: {COLOR_PANEL};
            color: {COLOR_TEXT};
            border: 1px solid {COLOR_PANEL_BORDER};
            border-radius: 6px;
        }}
        QMenu::item {{
            padding: 8px 24px 8px 12px;
        }}
        QMenu::item:selected {{
            background-color: {COLOR_RED};
            color: white;
        }}

        QPushButton#sortBtn {{
            background-color: transparent;
            border: none;
            border-radius: 6px;
            font-size: {base_font_size}px;
            color: {COLOR_MUTED};
        }}
        QPushButton#sortBtn:hover {{
            background-color: rgba(255, 255, 255, 0.08);
        }}
        QPushButton#sortBtn[active="true"] {{
            background-color: {COLOR_RED};
            color: white;
        }}

        QTextBrowser {{
            background-color: {COLOR_PANEL};
            border: 1px solid {COLOR_PANEL_BORDER};
            border-radius: 8px;
            padding: 8px;
            padding-left: 18px;
            selection-background-color: {COLOR_RED};
        }}
        
        QTextBrowser a {{
            color: {COLOR_MUTED};
            text-decoration: none;
            font-weight: bold;
        }}
        QTextBrowser a:hover {{
            color: {COLOR_TEXT};
            text-decoration: underline;
        }}

        QComboBox {{
            background-color: {COLOR_PANEL};
            border: 1px solid {COLOR_PANEL_BORDER};
            border-radius: 8px;
            padding: 8px;
            padding-left: 18px;
            selection-background-color: {COLOR_RED};
        }}

        QFrame#inputContainer {{
            background-color: {COLOR_PANEL};
            border: 1px solid {COLOR_PANEL_BORDER};
            border-radius: 8px;
        }}

        QFrame#inputContainer[focused="true"] {{
            border: 1px solid {COLOR_RED};
        }}

        QTextEdit#descText {{
            background-color: transparent;
            border: none;
            padding: 8px;
            padding-left: 4px;
            selection-background-color: {COLOR_RED};
        }}
        QTextEdit#descText:focus {{
            border: none;
        }}

        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top left;
            width: 35px;
            border: none;
            background-color: transparent;
        }}

        QComboBox QAbstractItemView {{
            padding: 4px;
            background-color: {COLOR_PANEL};
            border: 1px solid {COLOR_PANEL_BORDER};
            border-radius: 8px;
            outline: none;
        }}

        QComboBox QAbstractItemView::item {{
            padding: 6px 10px;
            text-align: right;
            border-radius: 4px;
        }}

        QComboBox QAbstractItemView::item:selected {{
            background-color: {COLOR_RED};
            color: white;
        }}

        QComboBox:disabled, QTextEdit:disabled {{
            color: {COLOR_MUTED};
        }}

        QComboBox:focus {{
            border: 1px solid {COLOR_RED};
        }}

        QPushButton#submitBtn {{
            background-color: {COLOR_RED};
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: bold;
            font-size: {base_font_size}px;
        }}

        QPushButton#submitBtn:hover {{ background-color: {COLOR_RED_HOVER}; }}
        QPushButton#submitBtn:pressed {{ background-color: {COLOR_RED_PRESSED}; }}
        QPushButton#submitBtn:disabled {{ background-color: #5a5a63; color: #cfcfcf; }}

        QPushButton#newChatBtn {{
            background-color: transparent;
            color: {COLOR_RED};
            border: 1px solid {COLOR_RED};
            border-radius: 8px;
            padding: 8px;
            font-weight: bold;
        }}
        QPushButton#newChatBtn:hover {{ background-color: rgba(229, 56, 59, 0.15); }}

        QListWidget {{
            background-color: transparent;
            border: none;
            outline: none;
            padding: 4px;
            padding-left: 0px; 
        }}

        QListWidget::item {{
            background-color: transparent;
            border-radius: 4px; 
            padding: 0px;
            margin-top: 2px;
            margin-bottom: 2px;
            margin-left: 2px;
            margin-right: 2px;
        }}

        QListWidget::item:hover {{
            background-color: #2a2a35;
        }}

        QListWidget::item:selected {{
            background-color: {COLOR_RED};
            color: white;
        }}

        QSplitter::handle {{
            background-color: transparent;
            width: 2px;
            margin: 0px 15px;
        }}

        QSplitter::handle:hover {{
            background-color: transparent;
        }}

        /* =======================================================
           استایل نوار پیشرفت با ضخامت اصلی ۶ پیکسل
           ======================================================= */
        QScrollBar:vertical {{
            background-color: transparent;
            width: 6px; 
            border-radius: 3px; 
            margin: 0px;
            margin-left: 2px; 
        }}

        QScrollBar::handle:vertical {{
            background-color: {COLOR_RED};
            min-height: 10px; 
            border-radius: 3px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {COLOR_RED_HOVER};
        }}

        QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {{
            height: 0px;
            background: none;
            border: none;
        }}

        QScrollBar::sub-page:vertical {{
            background-color: {COLOR_RED};
            border-top-left-radius: 3px;
            border-top-right-radius: 3px;
        }}

        QScrollBar::add-page:vertical {{
            background-color: transparent;
        }}
    """