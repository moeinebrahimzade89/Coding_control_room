"""
لایه ابزارهای کمکی (Utils Layer) - معماری لایه‌بندی شده (مسیر: utils/template.py)

مسئولیت: نگهداری قالب‌های پایه HTML، CSS و جاوا اسکریپت برای رندر کردن محیط گفتگو و خروجی فایل‌های PDF.
با این کار، فایل‌های منطقی پایتون از کدهای طولانی سمت وب پاکسازی می‌شوند.
توجه: مسیرهای نسبی استفاده شده در این فایل (مثل assets و icons) توسط QUrl در chat_panel.py مدیریت شده
و مستقیماً از پوشه resources خوانده می‌شوند.
"""

# ===================================================================
# قالب HTML/CSS/JS برای موتور کرومیوم (محیط اصلی چت)
# ===================================================================
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <link rel="stylesheet" href="assets/atom-one-dark.min.css">
    <script src="assets/highlight.min.js"></script>
    <style id="dynamic-font">
        /*DYNAMIC_FONT*/
    </style>
    <style>
        body {
            background-color: transparent; 
            margin: 0;
            padding: 0;
            overflow: hidden; 
            font-family: var(--chat-font), Tahoma, sans-serif !important;
            font-size: var(--chat-size) !important;
        }
        
        #chat-content, table, th, td, p, div, span, li, ul, ol, h1, h2, h3, h4, h5, h6 {
            font-family: var(--chat-font), Tahoma, sans-serif;
        }

        #scroll-container {
            height: 100vh;
            overflow-y: auto;
            overflow-x: hidden;
            direction: rtl; 
            padding: 20px 25px; 
            box-sizing: border-box;
        }

        #loading-indicator {
            text-align: center;
            color: #9a9aa5;
            font-size: 13px;
            padding: 10px 0;
            display: none;
        }

        #chat-content {
            color: #f1f1f1;
            line-height: 1.7;
        }
        
        table {
            border-collapse: separate;
            border-spacing: 0;
            width: 100%;
            border: 1px solid #33333d;
            border-radius: 8px;
            overflow: hidden;
            margin: 20px 0;
        }
        th, td {
            padding: 12px 16px;
            border-bottom: 1px solid #33333d;
            border-left: 1px solid #33333d;
        }
        th:last-child, td:last-child {
            border-left: none;
        }
        tr:last-child td {
            border-bottom: none;
        }
        th {
            background-color: #2a2a35;
            font-weight: bold;
            text-align: right;
        }

        pre, code, pre *, code * {
            font-family: Consolas, "Courier New", monospace !important;
        }
        
        pre {
            background-color: #17171c;
            border: 1px solid #33333d;
            border-radius: 8px;
            padding: 15px;
            direction: ltr; 
            text-align: left;
            overflow-x: auto;
        }
        code {
            background-color: rgba(255, 255, 255, 0.05);
            padding: 2px 5px;
            border-radius: 4px;
        }
        pre code {
            background-color: transparent;
            padding: 0;
        }

        ul, ol {
            padding-right: 25px;
        }
        
        ::-webkit-scrollbar {
            width: 6px;
            background-color: transparent;
        }
        ::-webkit-scrollbar-track {
            background-color: transparent;
        }
        ::-webkit-scrollbar-thumb {
            background-color: #e5383b;
            border-radius: 3px;
            min-height: 30px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background-color: #ff4d4f;
        }

        /* --- استایل حبابی پیام کاربر --- */
        .user-msg-container {
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            margin-bottom: 30px;
        }
        
        .user-msg-bubble {
            background-color: #e5383b;
            color: #ffffff;
            padding: 12px 20px;
            border-radius: 16px;
            border-top-right-radius: 4px;
            max-width: 85%;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
        }
        
        .user-msg-bubble p:first-child { margin-top: 0; }
        .user-msg-bubble p:last-child { margin-bottom: 0; }

        /* --- استایل پیام هوش مصنوعی --- */
        .ai-msg-container {
            margin-bottom: 40px;
        }

        /* --- استایل دکمه‌های آیکون‌دار --- */
        .actions {
            margin-top: 15px;
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
            font-size: 13px;
            font-family: Tahoma, sans-serif; 
        }
        
        .actions a {
            display: flex;
            align-items: center;
            gap: 6px;
            color: #9a9aa5;
            text-decoration: none;
            font-weight: bold;
            padding: 6px 12px;
            border-radius: 6px;
            background-color: transparent;
            transition: all 0.2s ease;
        }
        
        .actions a:hover {
            color: #f1f1f1;
            background-color: rgba(255, 255, 255, 0.08);
        }
        
        .action-icon {
            width: 16px;
            height: 16px;
            background-color: #9a9aa5;
            -webkit-mask-size: contain;
            -webkit-mask-repeat: no-repeat;
            -webkit-mask-position: center;
            mask-size: contain;
            mask-repeat: no-repeat;
            mask-position: center;
            transition: background-color 0.2s ease;
        }
        
        .actions a:hover .action-icon {
            background-color: #f1f1f1;
        }
        
        .icon-copy   { -webkit-mask-image: url('icons/Copy.svg'); mask-image: url('icons/Copy.svg'); }
        .icon-regen  { -webkit-mask-image: url('icons/Reprocessing.svg'); mask-image: url('icons/Reprocessing.svg'); }
        .icon-pdf    { -webkit-mask-image: url('icons/File-down.svg'); mask-image: url('icons/File-down.svg'); }
        .icon-branch { -webkit-mask-image: url('icons/branch.svg'); mask-image: url('icons/branch.svg'); }

    </style>
</head>
<body>
    <div id="scroll-container">
        <div id="loading-indicator">⏳ در حال بارگذاری پیام‌های قدیمی...</div>
        <div id="chat-content"></div>
    </div>

    <script>
        let allMessages = [];
        let renderIndex = 0;
        const BATCH_SIZE = 10;
        let scrollContainer = document.getElementById('scroll-container');
        let chatContent = document.getElementById('chat-content');
        let isLoading = false;

        function highlightAll() {
            if (typeof hljs !== 'undefined') {
                document.querySelectorAll('pre code').forEach((block) => {
                    hljs.highlightElement(block);
                });
            }
        }

        function initChat(messagesHtmlArray) {
            allMessages = messagesHtmlArray;
            renderIndex = Math.max(0, allMessages.length - BATCH_SIZE);
            
            chatContent.innerHTML = allMessages.slice(renderIndex).join('');
            highlightAll();
            
            setTimeout(() => {
                scrollContainer.scrollTop = scrollContainer.scrollHeight;
            }, 50);
        }

        function loadOlderMessages() {
            if (renderIndex <= 0 || isLoading) return; 
            
            isLoading = true;
            let indicator = document.getElementById('loading-indicator');
            indicator.style.display = 'block';
            
            setTimeout(() => {
                let oldScrollHeight = scrollContainer.scrollHeight;
                let newRenderIndex = Math.max(0, renderIndex - BATCH_SIZE);
                let htmlToPrepend = allMessages.slice(newRenderIndex, renderIndex).join('');
                renderIndex = newRenderIndex;
                
                chatContent.insertAdjacentHTML('afterbegin', htmlToPrepend);
                highlightAll();
                
                let newScrollHeight = scrollContainer.scrollHeight;
                scrollContainer.scrollTop = newScrollHeight - oldScrollHeight;
                
                indicator.style.display = 'none';
                isLoading = false;
            }, 300);
        }

        scrollContainer.addEventListener('scroll', function() {
            if (this.scrollTop === 0) {
                loadOlderMessages();
            }
        });
    </script>
</body>
</html>"""


# ===================================================================
# قالب HTML/CSS اختصاصی برای تولید فایل PDF
# ===================================================================
PDF_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <style>
        @page { 
            size: A4 portrait;
            margin: 15mm !important; 
        }
        :root {
            --pdf-font: "/*PDF_FONT*/", Tahoma, sans-serif;
            --pdf-size: /*PDF_SIZE*/px;
        }
        body {
            font-family: var(--pdf-font) !important;
            font-size: var(--pdf-size) !important;
            line-height: 1.8;
            color: #000;
            background: #fff;
            direction: rtl;
            text-align: right;
            max-width: 100%;
            overflow-x: hidden;
        }
        table, th, td, p, div, span, li, ul, ol, h1, h2, h3, h4, h5, h6 {
            font-family: var(--pdf-font);
        }
        table {
            border-collapse: collapse;
            width: 100%;
            max-width: 100%;
            margin: 20px 0;
            page-break-inside: auto;
        }
        tr {
            page-break-inside: avoid;
            page-break-after: auto;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: right;
            word-break: normal; 
            overflow-wrap: break-word; 
        }
        th {
            background-color: #f5f5f5;
            font-weight: bold;
        }
        pre, code, pre *, code * {
            font-family: Consolas, "Courier New", monospace !important;
        }
        pre {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 15px;
            direction: ltr;
            text-align: left;
            white-space: pre-wrap;
            word-wrap: break-word;
            page-break-inside: avoid;
        }
        code {
            background-color: #f8f9fa;
            padding: 2px 4px;
            border-radius: 4px;
            direction: ltr;
        }
        pre code {
            background-color: transparent;
            padding: 0;
        }
        ul, ol {
            padding-right: 25px;
        }
    </style>
</head>
<body>
    /*PARSED_HTML*/
</body>
</html>"""