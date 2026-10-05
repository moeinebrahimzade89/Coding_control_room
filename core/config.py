"""
لایه هسته و منطق برنامه (Core Layer) - معماری لایه‌بندی شده (مسیر: core/config.py)

تنظیمات اتصال به سرویس هوش مصنوعی.
این تنظیمات شامل بخش سرویس اصلی، سرویس نام‌گذاری (ارزان) و سرویس جایگزین (Groq) است.
نکته امنیتی: برای امنیت بیشتر، برنامه ابتدا متغیرهای محیطی (OS Environments) را چک می‌کند
و در صورت عدم وجود، از مقادیر پیش‌فرض استفاده می‌کند.
"""

import os

# ==========================================
# ۱. تنظیمات عمومی (کلید و آدرس سرور)
# ==========================================
BASE_URL = os.environ.get("API_BASE_URL", "https://api.gapgpt.app/v1")
API_KEY = os.environ.get("API_KEY", "YUOR_API")

# ==========================================
# ۲. مدل‌های در دسترس برای گفتگو (سرویس اصلی)
# ==========================================
AVAILABLE_MODELS = {
    "Deepseek": "deepseek-v4-flash",
    "GPT": "gpt-5.6-luna",
    "Gemma": "gemma-3-27b-it",
    "Gemini": "gemini-3.1-flash-lite",
    "Qwen": "qwen3-235b-a22b",
    "Grok": "grok-4.3"    
}

# ==========================================
# ۳. تنظیمات سرویس ارزان (فقط برای تولید نام و رنگ)
# ==========================================
CHEAP_BASE_URL = os.environ.get("CHEAP_BASE_URL", "https://api.gapgpt.app/v1")
CHEAP_API_KEY = os.environ.get("CHEAP_API_KEY", "YUOR_API")
CHEAP_MODEL_NAME = os.environ.get("CHEAP_MODEL_NAME", "gemma-3-27b-it")

# ==========================================
# ۴. تنظیمات سرویس جایگزین (Groq Fallback)
# ==========================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "YUOR_API")
GROQ_MODEL_NAME = os.environ.get("GROQ_MODEL_NAME", "openai/gpt-oss-120b")