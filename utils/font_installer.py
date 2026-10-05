"""
لایه ابزارهای کمکی (Utils Layer) - معماری لایه‌بندی شده (مسیر: utils/font_installer.py)

اسکریپت مستقل نصب فونت در ویندوز (Font Installer Worker)
این اسکریپت نیازی به PyQt/PySide ندارد و به صورت مجزا با دسترسی Administrator اجرا می‌شود.
وظایف:
۱. اسکن پوشه resources/web-fonts
۲. کپی فایل‌های ttf و otf در C:\\Windows\\Fonts
۳. ثبت کلیدها در رجیستری ویندوز
۴. اطلاع به سیستم‌عامل برای رفرش کردن کش فونت‌ها
"""

import os
import sys
import shutil
import winreg
import ctypes

def install_fonts():
    # بررسی اینکه آیا اسکریپت واقعاً با دسترسی ادمین اجرا شده است یا خیر
    if not ctypes.windll.shell32.IsUserAnAdmin():
        print("خطا: این اسکریپت برای نصب فونت نیازمند دسترسی Administrator است.")
        sys.exit(1)

    # پیدا کردن مسیر ریشه پروژه با توجه به نحوه اجرای برنامه
    if getattr(sys, 'frozen', False):
        # اگر فایل با PyInstaller کامپایل شده باشد (exe)، ریشه پروژه کنار فایل اجرایی است
        project_root = os.path.dirname(sys.executable)
    else:
        # اگر برنامه به صورت اسکریپت اجرا شده باشد، یک سطح از پوشه utils به عقب برمی‌گردیم
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
    # مسیر جدید پوشه فونت‌ها در معماری لایه‌بندی شده
    web_fonts_dir = os.path.join(project_root, "resources", "web-fonts")
    
    if not os.path.exists(web_fonts_dir):
        print(f"پوشه فونت‌ها در مسیر جدید یافت نشد: {web_fonts_dir}")
        sys.exit(0)

    windows_fonts_dir = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
    fonts_installed = False

    # جستجو در فایل‌های پوشه web-fonts
    for root, dirs, files in os.walk(web_fonts_dir):
        for filename in files:
            if filename.lower().endswith(('.ttf', '.otf')):
                font_path = os.path.join(root, filename)
                dest_path = os.path.join(windows_fonts_dir, filename)
                
                # اگر فونت از قبل در ویندوز موجود نباشد
                if not os.path.exists(dest_path):
                    try:
                        # ۱. کپی فایل در مسیر فونت‌های ویندوز
                        shutil.copy2(font_path, dest_path)
                        
                        # ۲. استخراج نام و پسوند برای ثبت دقیق در رجیستری
                        font_name, ext = os.path.splitext(filename)
                        font_type = "(OpenType)" if ext.lower() == '.otf' else "(TrueType)"
                        reg_key_name = f"{font_name} {font_type}"
                        
                        # ۳. ثبت کلید فونت در رجیستری ویندوز
                        reg_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
                        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path, 0, winreg.KEY_SET_VALUE) as key:
                            winreg.SetValueEx(key, reg_key_name, 0, winreg.REG_SZ, filename)
                            
                        # ۴. معرفی مستقیم فایل به هسته گرافیکی ویندوز (GDI)
                        ctypes.windll.gdi32.AddFontResourceW(dest_path)
                        fonts_installed = True
                        print(f"فونت '{filename}' با موفقیت نصب شد.")
                        
                    except Exception as e:
                        print(f"خطا در نصب فونت '{filename}': {e}")

    # ۵. در صورتی که حتی یک فونت نصب شده باشد، به کل سیستم پیام آپدیت فونت می‌فرستیم
    if fonts_installed:
        HWND_BROADCAST = 0xFFFF
        WM_FONTCHANGE = 0x001D
        SMTO_ABORTIFHUNG = 0x0002
        # ارسال سیگنال رفرش با تایم‌اوت ۱ ثانیه تا برنامه هنگ نکند
        ctypes.windll.user32.SendMessageTimeoutW(
            HWND_BROADCAST, 
            WM_FONTCHANGE, 
            0, 
            0, 
            SMTO_ABORTIFHUNG, 
            1000, 
            None
        )
        print("اطلاعات کش فونت سیستم‌عامل با موفقیت بروزرسانی شد.")
    else:
        print("هیچ فونت جدیدی برای نصب یافت نشد (فونت‌ها قبلاً نصب شده‌اند).")

if __name__ == "__main__":
    try:
        install_fonts()
    except Exception as e:
        print(f"خطای پیش‌بینی نشده: {e}")