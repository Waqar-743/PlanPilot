# AI Travel Planner

A premium AI-powered travel planning system that orchestrates multiple specialized agents to build comprehensive, realistic trip itineraries using real-time data.

---

## Overview

AI Travel Planner uses a multi-agent architecture where a Root Agent coordinates four specialized sub-agents -- Weather, Flight, Hotel, and Local Expert -- to deliver end-to-end trip planning through a single conversational interface.

The system gathers user requirements through natural conversation, dispatches agents in parallel for real-time data, and synthesizes everything into a polished travel plan with strict quality guardrails.

---

## Architecture

```
                         +-------------------+
                         |    Next.js UI     |
                         |    (Port 3000)    |
                         +--------+----------+
                                  |
                            REST API / WS
                                  |
                         +--------v----------+
                         |   FastAPI Server  |
                         |    (Port 8000)    |
                         +--------+----------+
                                  |
                         +--------v----------+
                         |    Root Agent     |
                         |  (Orchestrator)   |
                         +---+----+----+----++
                             |    |    |    |
              +--------------+    |    |    +---------------+
              |                   |    |                    |
     +--------v-------+ +--------v--+ +--v--------+ +------v---------+
     | Weather Agent   | |Flight Agent| |Hotel Agent| |Local Expert   |
     | OpenWeatherMap  | |Amadeus API | |Amadeus API| |Gemini AI      |
     +----------------+ +-----------+ +-----------+ +----------------+
                                  |
                         +--------v----------+
                         |     Supabase      |
                         |   (PostgreSQL)    |
                         +-------------------+
```

---

## Features

**Conversational Planning** -- Natural language interaction with smart follow-up questions. The system identifies missing requirements and asks a maximum of two clarifying questions before making assumptions and proceeding.

**Real-Time Data** -- Live flight pricing and availability via Amadeus API, current weather forecasts via OpenWeatherMap, and hotel search with dynamic pricing.

**Parallel Agent Execution** -- Weather, Flight, and Hotel agents run simultaneously using Python asyncio, reducing total response time to the duration of the slowest single agent call.

**A2A Context Handoff** -- Weather conditions and hotel location are passed directly to the Local Expert agent, ensuring the itinerary accounts for rain (no outdoor tours during storms) and proximity to accommodation.

**Multimodal Output** -- Text mode delivers clean markdown with bold headers, price symbols, and bullet points. Voice mode converts prices to spoken words, strips markdown formatting, and removes URLs.

**Strict Guardrails** -- No hallucinated data (all facts come from APIs), budget adherence warnings when prices exceed expectations, and the "One Voice" principle that hides internal agent architecture from users.

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Next.js 14, React 18, Tailwind CSS | Chat interface with dark premium theme |
| Backend | Python, FastAPI, Uvicorn | Async API server with multi-agent orchestration |
| LLM | Google Gemini 2.0 Flash | Conversation handling, requirement extraction, itinerary generation |
| Database | Supabase (PostgreSQL) | Conversation persistence, trip plan storage (JSONB) |
| Weather | OpenWeatherMap API | 5-day forecasts, geocoding, climate estimates |
| Flights & Hotels | Amadeus API | Real-time flight offers, hotel search and pricing |

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- API keys for: Google Gemini, OpenWeatherMap, Amadeus

### 1. Clone and Configure

```bash
git clone <repository-url>
cd AI-Travel-Planner
cp .env.example .env
```

Edit `.env` with your API keys:

```env
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
OPENWEATHER_API_KEY=your_openweather_key
AMADEUS_API_KEY=your_amadeus_key
AMADEUS_API_SECRET=your_amadeus_secret
```

### 2. Install Dependencies

```bash
# Backend
pip install -r backend/requirements.txt

# Frontend
cd frontend
npm install
```

### 3. Run the Application

```bash
# Terminal 1 - Backend (port 8000)
python run_backend.py

# Terminal 2 - Frontend (port 3000)
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## API Reference

| Method | Endpoint | Description |
|--------|---------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/api/status` | Agent status and configuration |
| `POST` | `/api/chat` | Send message and receive AI response |
| `POST` | `/api/conversations` | Create a new conversation |
| `GET` | `/api/conversations/:id` | Retrieve conversation details |
| `GET` | `/api/conversations/:id/messages` | Retrieve message history |
| `WS` | `/ws/chat` | WebSocket endpoint for real-time chat |

### Chat Request

```json
{
  "message": "Plan a 3-day trip to Paris on a medium budget",
  "conversation_id": null,
  "modality": "text"
}
```

### Chat Response

```json
{
  "reply": "I'd love to help you plan your Paris trip! ...",
  "conversation_id": "uuid",
  "travel_requirements": { "destination": "Paris", ... },
  "phase": "gathering"
}
```

---

## Project Structure

```
AI-Travel-Planner/
├── backend/
│   ├── agents/               # AI agent implementations
│   │   ├── root_agent.py     # Orchestrator (phases 1-3)
│   │   ├── weather_agent.py  # OpenWeatherMap integration
│   │   ├── flight_agent.py   # Amadeus flight search
│   │   ├── hotel_agent.py    # Amadeus hotel search
│   │   └── local_expert_agent.py  # Itinerary builder
│   ├── services/             # Shared services
│   │   ├── gemini_service.py
│   │   ├── supabase_service.py
│   │   └── output_formatter.py
│   ├── models/schemas.py     # Pydantic models
│   ├── config/settings.py    # Environment configuration
│   └── main.py               # FastAPI application
├── frontend/
│   ├── app/
│   │   ├── components/       # React components
│   │   ├── globals.css       # Design system
│   │   ├── layout.tsx        # Root layout
│   │   └── page.tsx          # Main page
│   └── package.json
├── .env.example              # Environment template
├── INTERVIEW_PREPARATION.md  # System logic deep-dive
└── README.md
```

---

## How It Works

1. **User sends a message** describing their travel plans
2. **Root Agent (Phase 1)** engages in conversation to collect destination, dates, origin, and budget
3. **Root Agent (Phase 2)** dispatches Weather, Flight, and Hotel agents simultaneously
4. **A2A Handoff** passes weather and hotel data to the Local Expert for context-aware itinerary planning
5. **Root Agent (Phase 3)** applies output formatting guardrails and delivers the complete plan
6. **Follow-up questions** are handled by the Root Agent using the stored trip plan context

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google AI Studio API key |
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_ANON_KEY` | Yes | Supabase anonymous/public key |
| `OPENWEATHER_API_KEY` | Yes | OpenWeatherMap API key |
| `AMADEUS_API_KEY` | Yes | Amadeus for Developers API key |
| `AMADEUS_API_SECRET` | Yes | Amadeus API secret |

---

## License

This project is for educational and demonstration purposes.
