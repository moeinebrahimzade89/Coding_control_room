"""
لایه ابزارهای کمکی (Utils Layer) - معماری لایه‌بندی شده (مسیر: utils/font_manager.py)

مسئولیت: بررسی و مدیریت دارایی‌های محلی (Assets) و فونت‌های مورد نیاز برنامه.
این ماژول وابستگی‌های خارجی محیط چت (مانند فایل‌های highlight.js و بررسی نصب فونت) را مدیریت می‌کند.
در معماری جدید، تمام دارایی‌ها در پوشه resources قرار دارند.
"""

import os
import urllib.request

# تنظیم مسیر ریشه پروژه برای دسترسی به پوشه resources
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)


def ensure_local_assets() -> str:
    """
    بررسی می‌کند که آیا فایل‌های مورد نیاز برای Syntax Highlighting دانلود شده‌اند یا خیر.
    در صورت عدم وجود، آن‌ها را از اینترنت دانلود و در پوشه resources/assets ذخیره می‌کند.
    خروجی: مسیر پوشه assets
    """
    assets_dir = os.path.join(PROJECT_ROOT, "resources", "assets")
    os.makedirs(assets_dir, exist_ok=True)
    
    files_to_download = {
        "highlight.min.js": "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js",
        "atom-one-dark.min.css": "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css"
    }
    
    for filename, url in files_to_download.items():
        filepath = os.path.join(assets_dir, filename)
        if not os.path.exists(filepath):
            try:
                urllib.request.urlretrieve(url, filepath)
            except Exception as e:
                print(f"خطا در دانلود فایل {filename}: {e}")
                
    return assets_dir


def get_uninstalled_fonts() -> list:
    """
    لیست فونت‌های نصب‌نشده‌ی داخل پوشه resources/web-fonts را با بررسی پوشه Fonts ویندوز پیدا می‌کند.
    خروجی: لیستی از نام فایل فونت‌هایی که روی سیستم نصب نیستند.
    """
    web_fonts_dir = os.path.join(PROJECT_ROOT, "resources", "web-fonts")
    
    if not os.path.exists(web_fonts_dir):
        return []

    windows_fonts_dir = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
    uninstalled = []

    for root, dirs, files in os.walk(web_fonts_dir):
        for filename in files:
            if filename.lower().endswith(('.ttf', '.otf')):
                dest_path = os.path.join(windows_fonts_dir, filename)
                if not os.path.exists(dest_path):
                    uninstalled.append(filename)
                    
    return uninstalled