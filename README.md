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

### Option A: Docker (empfohlen)

Voraussetzung: [Docker Desktop](https://www.docker.com/products/docker-desktop/) installiert.

```bash
git clone https://github.com/Alex8791-cyber/WABot.git
cd WABot
cp .env.example .env
```

`.env` öffnen und mindestens `OPENAI_API_KEY` eintragen, dann:

```bash
docker compose up -d
```

- Web-Chat: http://localhost:8080
- API-Docs: http://localhost:8000/docs
- Datenbank wird automatisch erstellt und im Docker Volume gespeichert

Stoppen: `docker compose down`

### Option B: Lokal ohne Docker

Voraussetzungen: Python 3.10+, Flutter 3.x+, ein OpenAI API Key.

```bash
git clone https://github.com/Alex8791-cyber/WABot.git
cd WABot

# Linux/macOS
chmod +x start_bot.sh && OPENAI_API_KEY=sk-... ./start_bot.sh

# Windows — erst Umgebungsvariable setzen, dann:
set OPENAI_API_KEY=sk-...
start_bot.bat
```

### Option C: Nur Backend (z.B. für WhatsApp)

Wenn du nur den WhatsApp-Bot brauchst, ohne Flutter-Frontend:

```bash
cd WABot/service_bot_backend
pip install -r requirements.txt
OPENAI_API_KEY=sk-... uvicorn main:app --host 0.0.0.0 --port 8000
```

API-Docs: http://localhost:8000/docs

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
| `/webhook` | GET | WhatsApp webhook verification | — |
| `/webhook` | POST | WhatsApp incoming messages | — |
| `/payments/webhook` | POST | Paystack payment confirmation | — |
| `/payments/status/{ref}` | GET | Check payment status | — |
| `/payments/list` | GET | List all payments | — |
| `/calendar/events` | GET | List calendar events | — |
| `/calendar/events` | POST | Create calendar event | Admin |
| `/calendar/events/{id}` | PATCH | Update calendar event | Admin |
| `/calendar/events/{id}` | DELETE | Delete calendar event | Admin |
| `/calendar/slots` | GET | Get available time slots | — |

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
| `WHATSAPP_VERIFY_TOKEN` | — | Webhook verification token |
| `WHATSAPP_API_TOKEN` | — | WhatsApp Cloud API bearer token |
| `WHATSAPP_PHONE_NUMBER_ID` | — | WhatsApp Business phone number ID |
| `DATABASE_FILE` | `service_bot.db` | SQLite database path |
| `PAYSTACK_SECRET_KEY` | — | Paystack secret key for payments |
| `GOOGLE_CREDENTIALS_FILE` | — | Path to Google service account JSON |
| `GOOGLE_CALENDAR_ID` | `primary` | Google Calendar ID |
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

## WhatsApp Integration

Connect the bot to WhatsApp Business via the Meta Cloud API:

1. Create a [Meta Business App](https://developers.facebook.com/) with WhatsApp product
2. Get your **Phone Number ID**, **API Token**, and set a **Verify Token**
3. Set environment variables:
   ```bash
   WHATSAPP_VERIFY_TOKEN=your-verify-secret
   WHATSAPP_API_TOKEN=your-meta-api-token
   WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id
   ```
4. Expose `/webhook` publicly (e.g. via ngrok or a reverse proxy)
5. In Meta Developer Console, set the webhook URL to `https://your-domain/webhook`
6. Subscribe to `messages` webhook field

The bot uses the phone number as session ID (`wa-{phone}`), so each WhatsApp user gets persistent conversation history. Default language is German.

## Payments (Paystack)

The bot creates payment links via [Paystack](https://paystack.com) when customers want to pay for services directly.

1. Create a [Paystack account](https://dashboard.paystack.com/#/signup) (supports ZAR)
2. Get your **Secret Key** from Settings → API Keys
3. Set `PAYSTACK_SECRET_KEY=sk_live_...` (or `sk_test_...` for testing)
4. Set webhook URL in Paystack Dashboard to `https://your-domain/payments/webhook`

The LLM will automatically create payment links when a customer confirms a service. Payment status is tracked in the database and updated via webhook.

## Google Calendar Integration

The bot can read, create, update, and delete calendar events autonomously during conversations using OpenAI function calling.

1. Create a [Google Cloud Service Account](https://console.cloud.google.com/iam-admin/serviceaccounts) with Calendar API enabled
2. Download the JSON key file
3. Share your Google Calendar with the service account email
4. Set environment variables:
   ```bash
   GOOGLE_CREDENTIALS_FILE=path/to/service-account.json
   GOOGLE_CALENDAR_ID=your-calendar-id@group.calendar.google.com
   ```

The LLM will automatically use calendar tools when users ask about scheduling, availability, or appointments.

## License

MIT
