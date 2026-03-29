# AI Service Bot

A configurable AI chatbot with a **FastAPI backend** and **Flutter web frontend** — designed for IT service companies to automate customer interactions, qualify leads, and hand off to humans when needed.

## Features

- **LLM-powered chat** via OpenAI-compatible API (GPT-4o-mini default)
- **Configurable personality** — edit `AGENTS.md` (behavior) and `SOUL.md` (tone) at runtime
- **Sentiment-based human handoff** — automatically escalates after repeated negative messages
- **Multimodal support** (optional) — audio transcription (Whisper), image analysis (GPT-4o Vision)
- **Service catalog + lead capture** — structured intake forms for IT services
- **Bilingual** — German and English, switchable at runtime
- **Admin-protected config** — change prompts, API keys, and features via the UI or API

## Architecture

```
┌─────────────────────┐       ┌──────────────────────┐
│  Flutter Web App     │──────▶│  FastAPI Backend      │
│  (Port 8080)         │◀──────│  (Port 8000)          │
│                      │       │                       │
│  • Chat interface    │       │  • OpenAI LLM         │
│  • Settings page     │       │  • Sentiment analysis  │
│  • Language toggle    │       │  • Audio/Image proc.  │
│  • Feature toggles   │       │  • Session persistence │
└─────────────────────┘       └──────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.10+
- Flutter 3.x+
- An OpenAI API key

### One-command launch

```bash
# Linux/macOS
chmod +x start_bot.sh && ./start_bot.sh

# Windows
start_bot.bat
```

This installs dependencies, starts the backend on port 8000, and opens the Flutter app on port 8080.

### Manual setup

**Backend:**

```bash
cd service_bot_backend
pip install -r requirements.txt
OPENAI_API_KEY=sk-... ADMIN_TOKEN=your-secret uvicorn main:app --reload --port 8000
```

**Frontend:**

```bash
cd service_bot_flutter
flutter pub get
flutter run -d chrome --web-hostname localhost --web-port 8080
```

API docs available at `http://localhost:8000/docs`

## API Endpoints

| Endpoint | Method | Description | Auth |
|---|---|---|---|
| `/agent/message` | POST | Send a chat message (text/audio/image) | Rate-limited |
| `/agent/config` | GET | Read agent configuration | — |
| `/agent/config` | POST | Update agent configuration | Admin |
| `/features/config` | GET | Read multimedia feature config | — |
| `/features/config` | POST | Update multimedia features | Admin |
| `/services` | GET | List service catalog | — |
| `/lead` | POST | Submit a lead form | — |
| `/health` | GET | Health check | — |

## Configuration

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | — | OpenAI API key (required) |
| `MODEL_NAME` | `gpt-4o-mini` | LLM model name |
| `ADMIN_TOKEN` | — | Token for protected endpoints |
| `ALLOWED_ORIGINS` | `http://localhost:8080` | CORS origins (comma-separated) |
| `HANDOFF_THRESHOLD` | `2` | Negative messages before human handoff |
| `MAX_HISTORY_MESSAGES` | `40` | Max messages in LLM context |
| `MAX_MESSAGE_LENGTH` | `10000` | Max characters per message |
| `RATE_LIMIT_REQUESTS` | `20` | Max requests per window per IP |
| `RATE_LIMIT_WINDOW` | `60` | Rate limit window in seconds |
| `DATABASE_FILE` | `service_bot.db` | SQLite database path |
| `ENABLE_AUDIO` | `false` | Enable audio transcription |
| `ENABLE_IMAGES` | `false` | Enable image analysis |
| `VISION_MODEL` | `gpt-4o` | Model for image analysis |

### Agent Personality

The bot's behavior is controlled by two Markdown files, editable at runtime via the Flutter settings page or the API:

- **`agents.md`** — Behavioral rules, task handling, response style
- **`soul.md`** — Personality, tone, values, communication style

Both are injected as the LLM system prompt.

## Service Catalog

Pre-configured IT services with lead qualification forms:

- Executive IT Support (Retainer)
- Cybersecurity Penetration Testing
- DSGVO/GDPR Compliance Audit
- Disaster Recovery Planning
- Data Center Hardware Refresh

Edit `services.json` to customize.

## License

MIT
