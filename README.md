# Mira Loop Bot
![Python 3.11](https://img.shields.io/badge/python-3.11-blue)
![python-telegram-bot](https://img.shields.io/badge/python--telegram--bot-20.7-blue)
![SQLite](https://img.shields.io/badge/SQLite-lightgrey)

A Telegram bot that gamifies Mira AI usage and drives viral growth through challenges and referrals.

Mira Loop gives users short, segment-tailored challenges that require opening Mira (https://mira.com), submitting proof, earning XP, and inviting friends.

## ⚙️ How it works

- User joins the bot and picks a segment (Student / Marketer / Founder).
- Bot serves a challenge that requires using Mira (https://mira.com).
- User submits proof (screenshot or text).
- User earns XP and climbs a live leaderboard.
- Users invite friends via referral links; both sides receive bonus XP.
- The loop repeats to encourage continued engagement.

## ✨ Features

- 3 user segments with tailored challenges (student, marketer, founder)
- XP system and live leaderboard (top 10)
- Referral system with deep links and XP bonuses
- Auto-approval flow for quick UX
- Lightweight: SQLite, no Docker; runs with one command

## 📁 Project structure

```
mira-loop-bot/
├── bot/
│   ├── main.py          # Entrypoint: starts the Telegram Application
│   ├── handlers.py      # Async handlers and ConversationHandler factory
	│   └── keyboards.py     # InlineKeyboard helper functions
├── backend/
│   ├── database.py      # sqlite3 helper + create_tables()
│   ├── models.py        # (placeholder) domain models
│   └── services.py      # Business logic (register, tasks, submissions)
├── data/
│   └── tasks.py         # Hardcoded TASKS and seeder function
├── .env                 # Environment variables (not committed)
├── requirements.txt     # Python dependencies
├── README.md            # This file
└── test_services.py     # Small local smoke-test script
```

## 🚀 Quick start

1. Clone the repo:

```bash
git clone <repo-url>
cd mira-loop-bot
```

2. Create and activate a virtual environment (Python 3.11):

```bash
python -m venv .venv
source .venv/bin/activate   # macOS / Linux
.venv\Scripts\activate     # Windows (PowerShell)
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create `.env` from the example and fill values:

```bash
cp .env.example .env
# edit .env and set TELEGRAM_BOT_TOKEN and BOT_USERNAME
```

5. Run the bot:

```bash
python -m bot.main
```

## 🔐 Environment variables

| Name | Description |
|---|---|
| TELEGRAM_BOT_TOKEN | Bot token from BotFather |
| BOT_USERNAME | Bot username (without @) — used to build referral links |

## ⌨️ Bot commands

- `/start` — Launch the bot and start onboarding

## 🛠 Tech stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Bot framework | python-telegram-bot 20.7 |
| Database | SQLite (builtin sqlite3) |
| Config | python-dotenv |

## 🧪 Development notes

- Database file `mira_loop.db` is created in the project root on startup.
- Use `test_services.py` to run a quick smoke test of core services.

---

