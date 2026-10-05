"""
لایه ابزارهای کمکی (Utils Layer) - معماری لایه‌بندی شده (مسیر: utils/pdf_exporter.py)

مسئولیت: دریافت محتوای مارک‌داون، تبدیل آن به HTML، تنظیم فونت‌های اختصاصی و خروجی گرفتن به صورت فایل PDF.
این کلاس از QWebEnginePage به صورت مخفی (Headless) برای رندر و چاپ PDF استفاده می‌کند.
"""

from PySide6.QtCore import QObject, Signal, QMarginsF
from PySide6.QtGui import QPageLayout, QPageSize
from PySide6.QtWebEngineCore import QWebEnginePage

import markdown

# ایمپورت‌ها بر اساس معماری جدید
from data import storage
from utils.template import PDF_HTML_TEMPLATE


class PdfExporter(QObject):
    # سیگنال برای اطلاع به رابط کاربری پس از اتمام کار (وضعیت موفقیت، مسیر فایل یا پیام خطا)
    export_finished = Signal(bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        # نگهداری نمونه صفحه وب برای جلوگیری از حذف شدن توسط زباله‌روب (Garbage Collector)
        self._pdf_page = None

    def export_message(self, message_content: str, file_path: str):
        """
        دریافت متن پیام و مسیر فایل، و شروع فرآیند تولید PDF.
        """
        try:
            # ۱. تبدیل مارک‌داون به HTML
            parsed_html = markdown.markdown(
                message_content, 
                extensions=['fenced_code', 'tables', 'nl2br', 'sane_lists']
            )
            
            # ۲. دریافت فونت و سایز از دیتابیس
            ff, slider_val = storage.get_chat_font()
            size_map = {1: 13, 2: 15, 3: 17, 4: 20, 5: 24}
            fs = size_map.get(slider_val, slider_val)
            
            # ۳. جایگذاری متغیرها در قالب HTML آماده
            pdf_html = PDF_HTML_TEMPLATE.replace(
                "/*PDF_FONT*/", ff
            ).replace(
                "/*PDF_SIZE*/", str(fs)
            ).replace(
                "/*PARSED_HTML*/", parsed_html
            )

            # ۴. ایجاد صفحه وب مخفی برای تولید PDF
            self._pdf_page = QWebEnginePage()

            # تابع داخلی: وقتی محتوای HTML کاملاً بارگذاری شد
            def on_load_finished(ok):
                if ok:
                    try:
                        # تنظیمات حاشیه و ابعاد کاغذ A4
                        layout = QPageLayout(
                            QPageSize(QPageSize.A4),
                            QPageLayout.Portrait,
                            QMarginsF(15, 15, 15, 15),
                            QPageLayout.Millimeter
                        )
                        self._pdf_page.printToPdf(file_path, layout)
                    except Exception:
                        # پشتیبان (Fallback) در صورت عدم پشتیبانی از تنظیمات Layout
                        self._pdf_page.printToPdf(file_path)
                else:
                    self.export_finished.emit(False, "خطا در بارگذاری موتور وب برای تولید PDF.")
                    self._pdf_page = None

            # تابع داخلی: وقتی چاپ PDF تمام شد
            def on_pdf_finished(filepath, success):
                self.export_finished.emit(success, filepath)
                self._pdf_page = None  # آزادسازی حافظه

            # ۵. اتصال سیگنال‌های صفحه وب به توابع داخلی
            self._pdf_page.loadFinished.connect(on_load_finished)
            self._pdf_page.pdfPrintingFinished.connect(on_pdf_finished)
            
            # ۶. تزریق HTML نهایی برای شروع رندر
            self._pdf_page.setHtml(pdf_html)

        except Exception as e:
            self.export_finished.emit(False, f"آماده‌سازی فایل با خطا مواجه شد:\n{str(e)}")
            self._pdf_page = None