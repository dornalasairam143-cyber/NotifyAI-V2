# NotifyAI V2 🚀

A production-grade, asynchronous website monitoring pipeline that leverages AI to detect, classify, and notify users of critical updates on government and educational portals.

## 🏗 Architecture
- **State Management:** SQLite ensures complete deduplication so you are only notified of *new* announcements.
- **Processing:** Asynchronous `ThreadPoolExecutor` targeting 100 sites/min.
- **AI Engine:** Google Gemini intelligently reads complex HTML/PDFs and categorizes them (Results, Admisssions, Counseling) with high accuracy.
- **Delivery:** Formatted Markdown alerts delivered directly to Telegram.

## 📦 Setup & Installation

1. **Clone & Install**
   ```bash
   git clone <repo-url> NotifyAI-V2
   cd NotifyAI-V2
   pip install -r requirements.txt