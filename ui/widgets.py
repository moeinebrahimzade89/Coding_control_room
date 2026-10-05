"""
لایه‌ی نمایش (Presentation Layer) - معماری لایه‌بندی شده (مسیر: ui/widgets.py)

شامل رنگ‌بندی تم پویا، ویجت‌های سفارشی سایدبار (آیتم چت + نماینده‌ی رنگ)،
توابع کمکی برای تولید آیکون‌های پویا و راست‌چین‌سازی متن، 
و شیت استایل (QSS) کل برنامه.
هیچ منطق کسب‌وکاری (business logic) اینجا نیست — فقط ظاهر.
"""

import os
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QTextOption, QPainter, QColor, QPainterPath, QPixmap, QIcon
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QMenu,
    QStyledItemDelegate, QSizePolicy
)

# ===================================================================
# تنظیمات مسیردهی برای دسترسی به آیکون‌ها
# ===================================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

RIGHT = Qt.AlignRight | Qt.AlignAbsolute

# ===================================================================
# ۱. پالت‌های رنگی پویا (تم‌ها و رنگ‌های مکمل)
# ===================================================================

THEMES = {
    "dark": {
        "bg": "#17171c",
        "panel": "#212128",
        "border": "#33333d",
        "text": "#f1f1f1",
        "muted": "#9a9aa5",
        "hover": "#2a2a35",
        "input_bg": "transparent"
    },
    "light": {
        "bg": "#f3f4f6",       
        "panel": "#ffffff",    
        "border": "#e5e7eb",   
        "text": "#1f2937",     
        "muted": "#6b7280",    
        "hover": "#e5e7eb",    
        "input_bg": "transparent"
    }
}

# رنگ‌های مکمل (جدید و قدیم)
ACCENTS = {
    "red":    {"base": "#e5383b", "hover": "#ff4d4f", "pressed": "#b3252a"},
    "blue":   {"base": "#3b82f6", "hover": "#60a5fa", "pressed": "#2563eb"},
    "green":  {"base": "#10b981", "hover": "#34d399", "pressed": "#059669"},
    "orange": {"base": "#f97316", "hover": "#fb923c", "pressed": "#ea580c"},
    "yellow": {"base": "#eab308", "hover": "#facc15", "pressed": "#ca8a04"},
    "purple": {"base": "#a855f7", "hover": "#c084fc", "pressed": "#9333ea"},
    "pink":   {"base": "#ec4899", "hover": "#f472b6", "pressed": "#db2777"},
    "black":  {"base": "#3f3f46", "hover": "#52525b", "pressed": "#27272a"},
    "brown":  {"base": "#92400e", "hover": "#b45309", "pressed": "#78350f"},
    "navy":   {"base": "#1e3a8a", "hover": "#2563eb", "pressed": "#1e40af"}
}

# ---------- دسته‌بندی‌های رنگی موضوعات پروژه‌ها ----------
PROJECT_COLORS = {
    "بازی‌سازی": "#e5383b",
    "طراحی سایت": "#ffc300",
    "اپلیکیشن موبایل": "#fd8c04",
    "هوش مصنوعی و یادگیری ماشین": "#023e8a",
    "برنامه‌نویسی و نرم‌افزار": "#00b4d8",
    "طراحی گرافیک و UI/UX": "#9d4edd",
    "تولید محتوا و ویدئو": "#ffb5a7",
    "داده و علم داده": "#a7c957",
    "امنیت سایبری و شبکه": "#386641",
    "سخت‌افزار و IoT": "#8b4513",
    "نامشخص / عمومی": "#808080"
}


# ===================================================================
# ۲. توابع تولید آیکون و ابزارهای کمکی
# ===================================================================

def add_custom_accent(color_name: str, base_hex: str):
    """
    یک رنگ سفارشی را به پالت رنگ‌های مکمل (ACCENTS) اضافه می‌کند.
    حالت‌های Hover و Pressed به صورت خودکار و از طریق QColor محاسبه می‌شوند.
    """
    color = QColor(base_hex)
    if color.isValid():
        # تولید خودکار رنگ‌های روشن‌تر و تیره‌تر (115 یعنی ۱۵ درصد تغییر)
        hover_color = color.lighter(115).name()
        pressed_color = color.darker(115).name()
        
        ACCENTS[color_name] = {
            "base": base_hex,
            "hover": hover_color,
            "pressed": pressed_color
        }


def create_color_icon(color_hex: str) -> QIcon:
    """یک دایره رنگی کوچک به عنوان آیکون برای منو می‌سازد"""
    pixmap = QPixmap(18, 18)
    pixmap.fill(Qt.transparent)  # پس‌زمینه شفاف برای گرد شدن لبه‌ها
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)  # فعال‌سازی Anti-Aliasing برای کیفیت بالا
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(color_hex))
    
    # رسم دایره در مرکز (مختصات 2 و 2، با عرض و ارتفاع 14)
    painter.drawEllipse(2, 2, 14, 14)
    painter.end()
    
    return QIcon(pixmap)


def get_theme_icon(icon_filename: str, theme_mode: str) -> QIcon:
    """
    آیکون SVG را لود کرده و بر اساس تم (تاریک/روشن) آن را رنگ‌آمیزی می‌کند.
    در تم تاریک، رنگ آیکون روشن و در تم روشن، رنگ آیکون تیره می‌شود.
    """
    icons_dir = os.path.join(PROJECT_ROOT, "resources", "icons")
    path = os.path.join(icons_dir, icon_filename)
    
    # تعیین رنگ متناسب با تم
    icon_color = "#f1f1f1" if theme_mode == "dark" else "#1f2937"
    
    # ایجاد یک Pixmap با سایز پایه و کیفیت بالا
    pixmap = QIcon(path).pixmap(24, 24)
    
    # رنگ‌آمیزی پیکسل‌های غیرشفافِ آیکون
    painter = QPainter(pixmap)
    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), QColor(icon_color))
    painter.end()
    
    return QIcon(pixmap)


def force_rtl(text_widget):
    """جهت و چینش متن یک ویجت متنی را کاملاً راست‌به‌چپ می‌کند."""
    option = text_widget.document().defaultTextOption()
    option.setAlignment(RIGHT)
    option.setTextDirection(Qt.RightToLeft)
    option.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
    text_widget.document().setDefaultTextOption(option)
    text_widget.setLayoutDirection(Qt.RightToLeft)
    text_widget.setAlignment(RIGHT)


# ===================================================================
# ۳. ویجت‌های سفارشی رابط کاربری
# ===================================================================

class ChatItemDelegate(QStyledItemDelegate):
    """یک نوار رنگی ضخیم در لبه‌ی راست هر آیتم سایدبار می‌کشد (رنگ موضوع پروژه)."""

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        color_hex = index.data(Qt.UserRole + 1)
        if color_hex:
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(color_hex))

            rect = option.rect
            bar_width = 6  
            radius = 6     

            margin_top = 3
            margin_bottom = 3
            margin_right = 2

            x = rect.right() - bar_width - margin_right + 1
            y = float(rect.top() + margin_top)
            w = float(bar_width)
            h = float(rect.height() - margin_top - margin_bottom)

            path = QPainterPath()
            path.moveTo(x, y) 
            path.lineTo(x + w - radius, y)
            path.arcTo(x + w - (radius * 2), y, radius * 2, radius * 2, 90, -90)
            path.lineTo(x + w, y + h - radius)
            path.arcTo(x + w - (radius * 2), y + h - (radius * 2), radius * 2, radius * 2, 0, -90)
            path.lineTo(x, y + h)
            path.closeSubpath()

            painter.drawPath(path)
            painter.restore()


class ChatItemWidget(QWidget):
    """ویجت نمایش‌دهنده‌ی هر گفتگو در سایدبار."""

    rename_requested = Signal(str)
    change_color_requested = Signal(str, str) 
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
        self.label.setObjectName("chatItemLabel") 
        self.label.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.btn = QPushButton("⋮")
        self.btn.setObjectName("chatItemBtn") 
        self.btn.setFixedSize(24, 24)
        self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.hide()

        self.menu = QMenu(self)
        self.menu.setLayoutDirection(Qt.RightToLeft)

        rename_action = self.menu.addAction("تغییر عنوان")
        
        color_menu = self.menu.addMenu("تغییر موضوع و رنگ")
        color_menu.setLayoutDirection(Qt.RightToLeft)
        for name, hex_code in PROJECT_COLORS.items():
            act = color_menu.addAction(create_color_icon(hex_code), name)
            act.triggered.connect(lambda checked=False, h=hex_code: self.change_color_requested.emit(self.chat_id, h))
            
        delete_action = self.menu.addAction("حذف گفتگو")

        rename_action.triggered.connect(lambda: self.rename_requested.emit(self.chat_id))
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.chat_id))

        self.btn.clicked.connect(self.show_menu)

        layout.addWidget(self.label, stretch=1)
        layout.addWidget(self.btn, alignment=Qt.AlignVCenter)

    def update_text(self, language: str, title: str):
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


# ===================================================================
# ۴. تولیدکننده شیت استایل داینامیک
# ===================================================================

def build_stylesheet(font_family: str, base_font_size: int = 14, theme_mode: str = "dark", accent_color: str = "red") -> str:
    """شیت استایل (QSS) کامل برنامه را با توجه به تم و رنگ مکمل محاسبه‌شده می‌سازد."""
    
    th = THEMES.get(theme_mode, THEMES["dark"])
    
    # تلاش برای واکشی رنگ از ACCENTS (اگر رنگ سفارشی باشد، به درستی اعمال می‌شود)
    ac = ACCENTS.get(accent_color, ACCENTS["red"])
    
    title_size = base_font_size + 8
    subtitle_size = max(10, base_font_size - 2)
    active_chat_size = base_font_size + 1
    
    return f"""
        QWidget {{
            background-color: {th['bg']};
            color: {th['text']};
            font-family: "{font_family}", "Segoe UI", "Tahoma", sans-serif;
            font-size: {base_font_size}px;
        }}

        QLabel#title {{
            color: {ac['base']};
            font-size: {title_size}px;
            font-weight: bold;
        }}
        
        QLabel#sectionTitle {{
            color: {ac['base']};
            font-weight: bold;
            margin-top: 10px;
        }}

        QLabel#subtitle {{
            color: {th['muted']};
            font-size: {subtitle_size}px;
        }}

        QLabel#fieldLabel {{
            color: {th['text']};
            font-weight: bold;
            margin-top: 4px;
        }}

        QLabel#activeChatLabel {{
            color: {ac['base']};
            font-weight: bold;
            font-size: {active_chat_size}px;
        }}
        
        QLabel#chatItemLabel {{
            background: transparent;
            border: none;
            color: {th['text']};
        }}

        QFrame#divider {{
            background-color: {th['border']};
            max-height: 1px;
            border: none;
        }}

        QWidget#sidebar {{
            background-color: transparent;
        }}

        QMenu {{
            background-color: {th['panel']};
            color: {th['text']};
            border: 1px solid {th['border']};
            border-radius: 6px;
            padding: 4px 0px;
        }}
        QMenu::item {{
            padding: 8px 24px 8px 16px;
            background-color: transparent;
        }}
        QMenu::item:selected {{
            background-color: {ac['base']};
            color: white;
        }}
        QMenu::icon {{
            /* ایجاد فضای امن از سمت راست برای جدا شدن آیکون از لبه پنجره */
            padding-right: 14px; 
            padding-left: 10px;
        }}

        QPushButton#sortBtn {{
            background-color: transparent;
            border: none;
            border-radius: 6px;
            font-size: {base_font_size}px;
            color: {th['muted']};
        }}
        QPushButton#sortBtn:hover {{
            background-color: {th['hover']};
        }}
        QPushButton#sortBtn[active="true"] {{
            background-color: {ac['base']};
            color: white;
        }}
        
        QPushButton#chatItemBtn {{
            background: transparent;
            color: {th['muted']};
            font-size: 18px;
            font-weight: bold;
            border: none;
            border-radius: 4px;
        }}
        QPushButton#chatItemBtn:hover {{
            background-color: {th['hover']};
            color: {th['text']};
        }}

        QTextBrowser {{
            background-color: {th['panel']};
            border: 1px solid {th['border']};
            border-radius: 8px;
            padding: 8px;
            padding-left: 18px;
            selection-background-color: {ac['base']};
        }}
        
        QTextBrowser a {{
            color: {th['muted']};
            text-decoration: none;
            font-weight: bold;
        }}
        QTextBrowser a:hover {{
            color: {th['text']};
            text-decoration: underline;
        }}

        QFrame#inputContainer {{
            background-color: {th['panel']};
            border: 1px solid {th['border']};
            border-radius: 8px;
        }}

        QFrame#inputContainer[focused="true"] {{
            border: 1px solid {ac['base']};
        }}

        QTextEdit#descText {{
            background-color: {th['input_bg']};
            border: none;
            padding: 8px;
            padding-left: 4px;
            selection-background-color: {ac['base']};
        }}
        QTextEdit#descText:focus {{
            border: none;
        }}

        /* =======================================================
           تنظیمات دقیق QComboBox برای قطع وابستگی به سیستم‌عامل
           ======================================================= */
        QComboBox {{
            background-color: {th['panel']};
            color: {th['text']};
            border: 1px solid {th['border']};
            border-radius: 8px;
            padding: 8px;
            padding-left: 18px;
        }}

        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top left;
            width: 35px;
            border: none;
            background-color: transparent;
        }}
        
        /* ====== استایل اختصاصی منوهای انگلیسی (چپ‌چین) ====== */
        QComboBox#ltrCombo {{
            padding-left: 12px;
            padding-right: 35px;
        }}
        
        QComboBox#ltrCombo::drop-down {{
            subcontrol-position: top right;
        }}
        /* ==================================================== */

        QComboBox QAbstractItemView {{
            background-color: {th['panel']};
            color: {th['text']};
            border: 1px solid {th['border']};
            border-radius: 4px; 
            selection-background-color: {ac['base']};
            outline: none;
        }}

        QComboBox QAbstractItemView::item {{
            min-height: 24px;
            padding: 6px 10px;
            background-color: {th['panel']};
            color: {th['text']};
        }}

        QComboBox QAbstractItemView::item:selected {{
            background-color: {ac['base']};
            color: white;
        }}

        QComboBox QAbstractItemView::item:hover {{
            background-color: {th['hover']};
            color: {th['text']};
        }}

        QComboBox:disabled, QTextEdit:disabled {{
            color: {th['muted']};
        }}

        QComboBox:focus {{
            border: 1px solid {ac['base']};
        }}

        /* ======================================================= */

        QPushButton#submitBtn {{
            background-color: {ac['base']};
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: bold;
            font-size: {base_font_size}px;
        }}

        QPushButton#submitBtn:hover {{ background-color: {ac['hover']}; }}
        QPushButton#submitBtn:pressed {{ background-color: {ac['pressed']}; }}
        QPushButton#submitBtn:disabled {{ background-color: {th['border']}; color: {th['muted']}; }}

        QPushButton#newChatBtn {{
            background-color: transparent;
            color: {ac['base']};
            border: 1px solid {ac['base']};
            border-radius: 8px;
            padding: 8px;
            font-weight: bold;
        }}
        QPushButton#newChatBtn:hover {{ background-color: {th['hover']}; }}

        QListWidget {{
            background-color: transparent;
            border: none;
            outline: none;
            padding: 4px;
            padding-left: 15px; 
        }}

        QListWidget::item {{
            background-color: transparent;
            border-radius: 6px; 
            padding: 0px;
            margin-top: 3px;
            margin-bottom: 3px;
            margin-left: 2px;
            margin-right: 2px;
        }}

        QListWidget::item:hover {{
            background-color: {th['hover']};
        }}

        QListWidget::item:selected {{
            background-color: {ac['base']};
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
           استایل نوار پیشرفت (Scrollbar)
           ======================================================= */
        QScrollBar:vertical {{
            background-color: transparent;
            width: 14px; 
            margin: 0px;
        }}

        QScrollBar::handle:vertical {{
            background-color: {ac['base']};
            min-height: 20px; 
            border-radius: 3px;
            margin: 0px 4px 0px 4px; 
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {ac['hover']};
        }}

        QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {{
            height: 0px;
            background: none;
            border: none;
        }}

        QScrollBar::sub-page:vertical, QScrollBar::add-page:vertical {{
            background-color: transparent;
        }}
        
        QMenu#colorMenu {{
            background-color: {th['panel']};
        }}
    """