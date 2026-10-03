# 🚀 AI Project Mentor (Programming Project Suggester)

An open-source desktop assistant that turns your coding skills and interests into targeted, challenge-driven project ideas—designed to help you build practical software engineering experience.

---

## 📖 Short Description

**AI Project Mentor** is a desktop application built with Python and PySide6 that connects to OpenAI-compatible language models to generate practical, hands-on programming projects. Guided by the "10% beyond your comfort zone" learning philosophy, it acts like a true mentor: providing clear objectives, technical boundaries, and helpful hints without handing over ready-made code or copy-paste solutions. That way, you develop real problem-solving skills and genuinely understand what you build.

---

## ❓ Project Overview (Q&A)

### 1. What problem does this application solve?
It is easy to get stuck in "tutorial hell"—understanding concepts from videos or documentation, but struggling to come up with realistic, well-scoped projects on your own. This tool bridges that gap by turning passive learning into active building through practical challenges tailored to your current skill level.

### 2. What is the educational philosophy behind the prompts?
The system focuses on steady, incremental growth ("10% harder than your current capabilities"). The prompts guide the AI into an advisory role rather than a solution generator. Instead of serving full code or boilerplate implementations, it outlines requirements, milestones, expected results, and nudges—leaving the actual thinking and architectural choices to you.

### 3. Which programming languages are supported out of the box?
The application includes dedicated, detailed system prompts for **Python**, **C**, and **C++**, alongside starter prompts for **JavaScript** and **Java**. Adding support for another language is straightforward: simply add a new key to the `SYSTEM_PROMPTS` dictionary in `prompts.py`.

### 4. How was this project engineered and developed?
Initial project scaffolding was drafted with AI coding assistants, followed by hands-on architectural refactoring, multithreading optimizations, custom UI styling, and iterative prompt design to keep the experience stable, practical, and responsive.

### 5. Does the interface support multilingual or RTL layouts?
Yes. The PySide6 interface natively supports Right-to-Left (RTL) text flow, custom typography (optimized for fonts like Vazirmatn), and clean Markdown rendering for structured outputs.

---

## ✨ Features

- **Clean Dark Desktop Theme:** A custom dark interface with red and charcoal accents, designed to stay easy on the eyes during long sessions.
- **Non-blocking Asynchronous Operations:** Network requests run on a dedicated `QThread` (`SuggestionWorker`), keeping the UI smooth and responsive while waiting for API responses.
- **Session History Sidebar:** Automatically keeps track of generated projects during your session, so you can switch between them without repeating API calls.
- **Full Markdown Rendering:** Clearly displays formatted project briefs, including headers, checklists, and code snippets.
- **Responsive Splitter Layout:** An adjustable split-view that keeps proportions balanced and prevents the sidebar from expanding awkwardly when maximized.
- **Guiding Prompt Architecture:** Instructions crafted to keep the LLM focused on guidance, hints, and requirements rather than leaking direct answers.
- **OpenAI-Compatible Flexibility:** Works smoothly with any OpenAI-compatible provider (such as GapGPT, OpenRouter, DeepSeek, or official OpenAI endpoints).

---

## 🛠 Tech Stack

| Technology / Tool | Role & Description |
| :--- | :--- |
| **Python 3.10+** | Core programming language and business logic |
| **PySide6 (Qt for Python)** | Native desktop graphical user interface, event handling, and QSS styling |
| **OpenAI Python SDK** | Official client library used for LLM API integration |
| **DeepSeek (`deepseek-v4-flash`)** | High-performance language model powering project generation |
| **GapGPT Gateway** | OpenAI-compatible API gateway infrastructure |

---

## 📋 Prerequisites

Before setting up the project, make sure you have:

1. **Python 3.10** or higher installed.
2. Python package manager (`pip`).
3. An active API key from an OpenAI-compatible provider (such as GapGPT, OpenRouter, or OpenAI).
4. *(Optional but recommended)* **Vazirmatn** font installed on your system for the best typographic experience.

---

## ⚙️ Installation & Setup

Follow these steps to set up and run the project locally:

### 1. Clone the repository
```bash
git clone https://github.com/your-username/ai-project-suggester.git
cd ai-project-suggester
```

### 2. Create and activate a virtual environment
```bash
# On Windows:
python -m venv venv
venv\Scripts\activate

# On Linux / macOS:
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install PySide6 openai
```

### 4. Configure your API credentials
Open `config.py` and replace the placeholder values with your endpoint details and private API key:

```python
# config.py
BASE_URL = "https://api.gapgpt.app/v1"
API_KEY = "YOUR_ACTUAL_API_KEY"
MODEL_NAME = "deepseek-v4-flash"
```

> ⚠️ **Security Notice:** Never commit your actual secret API keys to public version control repositories. Consider using environment variables for production deployments.

---

## 🎮 How to Use

Launch the application using:

```bash
python main.py
```

### Workflow:
1. **Choose a Language:** Select your target programming language (e.g., Python, C++, etc.) from the dropdown menu.
2. **Describe Your Goals:** Enter your current experience level, concepts you already know, and any areas you want to explore (e.g., *"I understand basic Python loops and functions, and I want to build a small automation script or CLI utility"*).
3. **Generate:** Click **"دریافت پیشنهاد پروژه"** (Get Project Suggestion).
4. **Review & Build:** Read through the project brief in the main panel—covering target skills, step-by-step milestones, and guiding hints.
5. **Access History:** Jump back to any previously generated project during your session by clicking its title in the sidebar.

---

## 👨‍💻 Author

Created and maintained by:  
**Moein Ebrahimzadeh**

---

## 🌟 Support & Contributing

If this project helped you learn or build something interesting, here is how you can support it:

- ⭐ **Star the Repository:** Star the project on GitHub to help others find it.
- 📢 **Share:** Share the project with developer communities, peers, or friends.
- 💡 **Contribute:** Open issues, suggest prompt improvements, or submit Pull Requests to add new language templates.