# Purchase AI Chief

A modern, chat-based procurement assistant powered by DeepSeek, built for industrial purchase leadership workflows.

## What This App Includes

- DeepSeek-powered purchase advisor with a senior procurement persona.
- Multi-chat memory with SQLite (start new chat, continue old chat).
- Attachment knowledge upload per chat (TXT, PDF, DOCX, CSV, JSON, YAML, XML).
- Knowledge-aware answers using retrieved snippets from uploaded files.
- Modern responsive UI with sidebar conversations, live chat, and knowledge panel.

## Tech Stack

- Backend: FastAPI
- Model API: DeepSeek Chat Completions
- Memory: SQLite
- Frontend: Vanilla HTML/CSS/JS

## Setup

1. Create and activate a virtual environment.
2. Install dependencies.
3. Configure environment variables.
4. Run the app.

### 1) Create virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Install dependencies

```powershell
pip install -r requirements.txt
```

### 3) Configure environment

Copy `.env.example` to `.env` and set your API key:

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
APP_HOST=127.0.0.1
APP_PORT=8000
MAX_HISTORY_MESSAGES=24
MAX_KNOWLEDGE_CHUNKS=6
```

### 4) Run

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open http://127.0.0.1:8000 in your browser.

## Deploy To Vercel (GitHub)

1. Push this project to a GitHub repository.
2. In Vercel, click `Add New -> Project` and import your GitHub repo.
3. Keep defaults (Vercel auto-detects `vercel.json` and Python serverless function in `api/index.py`).
4. Add these environment variables in Vercel Project Settings:

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
MAX_HISTORY_MESSAGES=24
MAX_KNOWLEDGE_CHUNKS=6
```

5. Deploy. Your app URL will be served by:
- UI at `/`
- API at `/api/*`

## Vercel Runtime Notes

- On Vercel serverless, SQLite and uploaded files are stored in `/tmp`.
- This storage is writable but ephemeral, so long-term persistence is not guaranteed across cold starts and redeployments.
- For durable production chat memory, migrate storage to a managed database/object store (for example Vercel Postgres + Blob or Supabase).

## Notes

- Chat and document indexes are stored in `data/purchase_chief.db`.
- Uploaded files are stored under `data/uploads/<chat_id>/`.
- Each chat has isolated attachment context.
- If the model/API fails, the user message is still saved so the conversation remains traceable.
