"""
لایه هسته و منطق برنامه (Core Layer) - معماری لایه‌بندی شده (مسیر: core/api_client.py)

ارتباط با سرویس‌های هوش مصنوعی.
شامل کلاینت‌های مجزا برای پردازش اصلی، پردازش سبک و یک کلاینت پشتیبان (Groq) برای مواقع قطعی.
در این نسخه، مسیریابی هوشمند (Smart Routing) برای ارسال برخی مدل‌ها (مثل GPT OSS 120) به سرور مجزا وجود دارد،
و کلاینت‌ها به صورت پویا (Dynamic) بر اساس کلیدهای ثبت شده توسط کاربر در دیتابیس راه‌اندازی می‌شوند.
"""

import os
import re
from typing import Tuple

# ایمپورت تنظیمات و دیتابیس بر اساس معماری جدید
from core import config
from data import storage

# ---------------------------------------------------------
# ۱. ایمپورت ایمن کتابخانه‌ها (جلوگیری از کرش در صورت عدم نصب)
# ---------------------------------------------------------
try:
    from openai import OpenAI
    _has_openai = True
except ImportError:
    _has_openai = False

try:
    from groq import Groq
    _has_groq = True
except ImportError:
    _has_groq = False


# ---------------------------------------------------------
# ۲. ساخت کلاینت‌ها با زره محافظتی و قابلیت بازنشانی (Reload)
# ---------------------------------------------------------
_main_client = None
_cheap_client = None
_groq_client = None

def init_clients():
    """
    راه‌اندازی یا بروزرسانی کلاینت‌های اتصال به هوش مصنوعی.
    این تابع ابتدا کلیدهای ذخیره شده توسط کاربر را بررسی می‌کند و در صورت عدم وجود،
    از مقادیر پیش‌فرض فایل config استفاده می‌کند.
    با هر بار تغییر کلیدها در تنظیمات، این تابع می‌تواند مجدداً فراخوانی شود.
    """
    global _main_client, _cheap_client, _groq_client

    # خواندن کلیدهای شخصی کاربر از دیتابیس
    user_main_key = storage.get_setting("user_main_api_key", "").strip()
    user_groq_key = storage.get_setting("user_groq_api_key", "").strip()

    # تعیین کلید نهایی (اولویت با کاربر، سپس پیش‌فرض کانفیگ)
    final_main_key = user_main_key if user_main_key else getattr(config, "API_KEY", "")
    final_groq_key = user_groq_key if user_groq_key else getattr(config, "GROQ_API_KEY", "")

    if _has_openai:
        try:
            _main_client = OpenAI(
                api_key=final_main_key,
                base_url=getattr(config, "BASE_URL", "https://api.gapgpt.app/v1"),
                timeout=30.0,
            )
            
            # برای کلاینت ارزان، اگر کلید اختصاصی در کانفیگ نبود، از کلید اصلی استفاده می‌کنیم
            cheap_key = getattr(config, "CHEAP_API_KEY", "")
            if not cheap_key:
                cheap_key = final_main_key
                
            _cheap_client = OpenAI(
                api_key=cheap_key,
                base_url=getattr(config, "CHEAP_BASE_URL", "https://api.gapgpt.app/v1"),
                timeout=10.0, # زمان انتظار کوتاه برای انتقال سریع به Groq در زمان قطعی
            )
        except Exception as e:
            print(f"OpenAI Init Error: {e}")

    if _has_groq:
        try:
            if final_groq_key and final_groq_key != "YOUR_GROQ_API_KEY_HERE":
                _groq_client = Groq(api_key=final_groq_key, timeout=15.0)
            elif os.environ.get("GROQ_API_KEY"):
                _groq_client = Groq(timeout=15.0)
        except Exception as e:
            print(f"Groq Init Error: {e}")

# مقداردهی اولیه کلاینت‌ها در زمان لود شدن ماژول
init_clients()


# ---------------------------------------------------------
# ۳. توابع پردازشی (همراه با مسیریابی هوشمند)
# ---------------------------------------------------------

def get_chat_response(messages: list, model_id: str) -> Tuple[bool, str]:
    """دریافت پاسخ چت با استفاده از مسیریابی هوشمند سرورها."""
    
    # شناسایی مدل هدف برای سرور Groq
    groq_target_model = getattr(config, "GROQ_MODEL_NAME", "openai/gpt-oss-120b")
    
    # ---------------- مسیریابی به سمت سرور Groq ----------------
    if model_id == groq_target_model:
        if not _groq_client:
            return False, "کلاینت Groq نصب نشده یا کلید API آن تنظیم نشده است. لطفاً از بخش تنظیمات کلید را وارد کنید."
            
        try:
            response = _groq_client.chat.completions.create(
                model=model_id,
                messages=messages,
                max_tokens=4096,
            )
            return True, response.choices[0].message.content
        except Exception as e:
            return False, f"خطا در دریافت پاسخ از سرویس Groq:\n{e}"

    # ---------------- مسیریابی به سمت سرور اصلی (Main API) ----------------
    else:
        if not _main_client:
            return False, "کتابخانه OpenAI نصب نشده یا کلید API آن تنظیم نشده است. لطفاً از بخش تنظیمات کلید را وارد کنید."
            
        try:
            response = _main_client.chat.completions.create(
                model=model_id,
                messages=messages,
                max_tokens=4096,
            )
            return True, response.choices[0].message.content

        except Exception as e:
            return False, f"خطا در دریافت پاسخ از سرویس اصلی:\n{e}"


def _clean_generated_title(raw_text: str) -> str:
    """خروجی خام مدل را پردازش و از تگ‌های تفکر پاکسازی می‌کند."""
    if not raw_text:
        return ""

    # پاک کردن بلوک‌های <think>...</think> در مدل‌های استدلالی
    raw_text = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL | re.IGNORECASE)

    lines = [ln.strip() for ln in raw_text.strip().splitlines() if ln.strip()]
    if not lines:
        return ""

    title = lines[-1]
    title = re.sub(r'^(thought|reasoning|analysis|فکر|تفکر|عنوان)\s*[:،\-]?\s*', '', title, flags=re.IGNORECASE)
    title = title.replace('"', '').replace("'", '').replace('*', '').strip()

    if len(title) > 60:
        title = title[:60].strip()

    return title


def generate_chat_title(user_message: str) -> str:
    """تولید عنوان چت با استفاده از API اول، و در صورت شکست، سوئیچ به API دوم (Groq)."""
    system_prompt = (
        "تو یک دستیار خلاصه‌نویس هستی. پیام کاربر را بخوان و فقط یک عنوان کوتاه، "
        "جذاب و مرتبط (حداکثر 4 کلمه) برای آن بنویس. "
        "هیچ کلمه اضافه‌ای (مثل 'عنوان:' یا نقطه در انتهای جمله) ننویس. "
        "فقط و فقط خود عنوان را در یک خط بنویس، بدون هیچ خط یا توضیح اضافه‌ی دیگر."
    )
    
    # -------- تلاش اول: API ارزان --------
    if _cheap_client:
        try:
            response = _cheap_client.chat.completions.create(
                model=getattr(config, "CHEAP_MODEL_NAME", "gemma-3-27b-it"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=20, 
            )
            title = _clean_generated_title(response.choices[0].message.content)
            if title:
                return title
        except Exception as e:
            print(f"[Fallback Triggered] Primary API failed on Title: {e}")
            
    # -------- تلاش دوم: Fallback به Groq --------
    if _groq_client:
        try:
            response = _groq_client.chat.completions.create(
                model=getattr(config, "GROQ_MODEL_NAME", "openai/gpt-oss-120b"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=1024, # افزایش توکن برای مدل‌های استدلالی تا تفکرشان قطع نشود
            )
            title = _clean_generated_title(response.choices[0].message.content)
            if title:
                return title
        except Exception as e:
            print(f"[Fallback Failed] Groq API error on Title: {e}")
            
    return "بدون عنوان"


def detect_project_color(project_text: str) -> str:
    """تشخیص رنگ موضوعی با استفاده از API اول، و در صورت شکست، سوئیچ به API دوم (Groq)."""
    system_prompt = (
        "تو یک تحلیل‌گر موضوع پروژه هستی. متن پروژه را بخوان و بر اساس موضوع اصلی آن، "
        "فقط و فقط یک کد رنگ HEX از لیست زیر برگردان:\n"
        "- بازی‌سازی: #e5383b\n"
        "- طراحی سایت: #ffc300\n"
        "- اپلیکیشن موبایل: #fd8c04\n"
        "- هوش مصنوعی و یادگیری ماشین: #023e8a\n"
        "- برنامه‌نویسی و نرم‌افزار: #00b4d8\n"
        "- طراحی گرافیک و UI/UX: #9d4edd\n"
        "- تولید محتوا و ویرایش ویدئو: #ffb5a7\n"
        "- داده، تحلیل و علم داده: #a7c957\n"
        "- امنیت سایبری و شبکه: #386641\n"
        "- سخت‌افزار، رباتیک و IoT: #8b4513\n"
        "اگر موضوع نامشخص بود یا به هیچ‌کدام نخورد، مقدار #808080 را برگردان.\n"
        "توجه: خروجی تو باید دقیقاً یک کد 7 کاراکتری (مثل #e5383b) باشد و هیچ متن اضافه‌ای نداشته باشد."
    )
    
    user_content = f"متن پروژه:\n{project_text[:1000]}"
    
    # -------- تلاش اول: API ارزان --------
    if _cheap_client:
        try:
            response = _cheap_client.chat.completions.create(
                model=getattr(config, "CHEAP_MODEL_NAME", "gemma-3-27b-it"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content} 
                ],
                max_tokens=10, 
            )
            color_code = response.choices[0].message.content.strip()
            match = re.search(r'#(?:[0-9a-fA-F]{3}){1,2}', color_code)
            if match:
                return match.group(0)
        except Exception as e:
            print(f"[Fallback Triggered] Primary API failed on Color: {e}")
            
    # -------- تلاش دوم: Fallback به Groq --------
    if _groq_client:
        try:
            response = _groq_client.chat.completions.create(
                model=getattr(config, "GROQ_MODEL_NAME", "openai/gpt-oss-120b"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content} 
                ],
                max_tokens=1024, # افزایش توکن برای عبور از مرحله تفکر
            )
            color_code = response.choices[0].message.content.strip()
            
            # حذف بلوک‌های تفکر قبل از استخراج کد رنگ
            color_code = re.sub(r'<think>.*?</think>', '', color_code, flags=re.DOTALL | re.IGNORECASE)
            
            match = re.search(r'#(?:[0-9a-fA-F]{3}){1,2}', color_code)
            if match:
                return match.group(0)
        except Exception as e:
            print(f"[Fallback Failed] Groq API error on Color: {e}")

    return "#808080" # خروجی امن