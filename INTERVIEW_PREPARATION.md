# AI Travel Planner - Interview Preparation Guide
## System Architecture, Logic & Workflow Deep-Dive

---

## 1. HIGH-LEVEL ARCHITECTURE

```
User (Browser)
     |
     v
[Next.js Frontend] --- port 3000
     |
     | REST API (POST /api/chat)
     v
[FastAPI Backend] --- port 8000
     |
     +---> Root Agent (Orchestrator)
              |
              +---> Gemini 2.0 Flash (LLM)
              |
              +---> [Phase 1] Gather Requirements
              |
              +---> [Phase 2] Delegate to Sub-Agents (async parallel)
              |       |
              |       +---> Weather_Agent  --> OpenWeatherMap API
              |       +---> Flight_Agent   --> Amadeus API
              |       +---> Hotel_Agent    --> Amadeus API
              |       +---> Local_Expert   --> Gemini AI
              |
              +---> [Phase 3] Output Formatter (Guardrails)
              |
              +---> Supabase (PostgreSQL) for persistence
```

---

## 2. PHASE-BY-PHASE WORKFLOW

### Phase 1: Persona & Core Behavior (Gathering)

**What happens when a user sends their first message:**

1. Frontend sends `POST /api/chat` with `{message, conversation_id: null, modality: "text"}`
2. Root Agent creates a new conversation in Supabase
3. Root Agent uses a **system prompt** (GATHERING_PROMPT) that instructs Gemini to:
   - Act as a premium travel concierge
   - Identify what requirements are missing (destination, dates, origin, budget)
   - Ask a maximum of TWO follow-up questions
   - If user ignores questions, make logical assumptions and proceed
4. User's message is saved to the `messages` table
5. Gemini generates a response following the persona rules
6. When Gemini determines all requirements are collected, it appends `[REQUIREMENTS_COMPLETE]` to its response
7. Root Agent detects this marker, calls `extract_requirements()` which uses Gemini to parse the conversation into structured JSON:
   ```json
   {
     "destination": "Paris",
     "origin": "Mumbai",
     "start_date": "2026-04-15",
     "end_date": "2026-04-18",
     "budget_level": "med",
     "duration_days": 3,
     "has_all_requirements": true
   }
   ```
8. Requirements are saved to the `conversations.travel_requirements` JSONB column

**Key Design Decision - Why a marker-based approach?**
- Gemini decides when requirements are complete, not hardcoded logic
- This handles ambiguous inputs (e.g., "next weekend" needs no date clarification)
- The fallback rule prevents infinite question loops

**Modality Awareness:**
- The `CURRENT_MODALITY` variable in the system prompt tells Gemini whether to format for text (markdown) or voice (plain conversational)
- This is set from the frontend's modality toggle

---

### Phase 2: Routing Logic (Delegation)

**What happens when requirements are complete and user sends next message:**

1. Root Agent detects `has_all_requirements: true` in the conversation
2. Sends a **transition message** ("I have everything I need, working on your plan...")
3. Executes the **Async Delegation** pattern:

```python
# Three API calls dispatched SIMULTANEOUSLY
weather_task = asyncio.create_task(weather_agent.get_forecast(...))
flight_task  = asyncio.create_task(flight_agent.search_flights(...))
hotel_task   = asyncio.create_task(hotel_agent.search_hotels(...))

# Wait for ALL three to complete
weather_data, flight_data, hotel_data = await asyncio.gather(
    weather_task, flight_task, hotel_task,
    return_exceptions=True  # Don't crash if one fails
)
```

4. **A2A Handoff**: Weather + Hotel results are passed to the Local Expert Agent:
   - Weather context tells it not to schedule outdoor activities during rain
   - Hotel location helps plan proximity-based itineraries

5. Results are saved to the `trip_plans` table with JSONB columns for each agent's data

**Sub-Agent Details:**

#### Weather_Agent (OpenWeatherMap API)
- **Input**: `{"destination": "Paris", "dates": "2026-04-15 to 2026-04-18"}`
- **Flow**:
  1. Geocodes city name to lat/lon using OpenWeatherMap Geocoding API
  2. If travel is within 5 days: uses 5-day/3-hour forecast endpoint
  3. If travel is further out: uses current weather as climate estimate
  4. Aggregates 3-hour data into daily summaries (high/low temp, dominant condition, humidity, wind)
- **Output**: Daily forecast + text summary (e.g., "Average 18°C, mostly cloudy. Rain on 1 day.")

#### Flight_Agent (Amadeus API)
- **Input**: `{"origin": "Mumbai", "destination": "Paris", "departure_date": "2026-04-15", "return_date": "2026-04-18", "budget_level": "med"}`
- **Flow**:
  1. Authenticates with Amadeus OAuth2 (client_credentials grant)
  2. Resolves city names to IATA codes (Mumbai -> BOM, Paris -> PAR)
  3. Searches flight offers with cabin class based on budget (low/med = ECONOMY, high = BUSINESS)
  4. Parses itinerary segments (departure, arrival, stops, duration, airline)
  5. Sorts by price, assesses budget fit
- **Output**: List of flights with prices, stops, times + budget assessment string

#### Hotel_Agent (Amadeus API)
- **Input**: `{"destination": "Paris", "check_in": "2026-04-15", "check_out": "2026-04-18", "budget_level": "med"}`
- **Flow**:
  1. Resolves city to IATA code
  2. Fetches hotel list filtered by star rating (low=1-3, med=3-4, high=4-5)
  3. For top 10 hotels, fetches pricing from Hotel Offers endpoint (batched in groups of 5)
  4. Calculates price-per-night, sorts by total price
- **Output**: List of hotels with name, rating, price, location + budget assessment

#### Local_Expert_Agent (Gemini AI)
- **Input**: `{"destination": "Paris", "duration_days": 3, "weather_context": "...", "hotel_location": "..."}`
- **Flow**:
  1. Constructs a detailed prompt with weather context, hotel location, budget level
  2. Instructs Gemini to generate a structured JSON itinerary
  3. Rules enforced: no outdoor activities during rain, real restaurant names, estimated costs, mix of landmarks and hidden gems
  4. Parses JSON response into structured day-by-day itinerary
- **Output**: Full itinerary with activities, meals, tips, estimated costs per day

**Error Handling:**
- `return_exceptions=True` in asyncio.gather prevents one failed agent from crashing the whole pipeline
- Each agent wraps exceptions into `{"error": "..."}` format
- The output formatter detects errors and generates natural user-facing messages

---

### Phase 3: Output Formatting & Guardrails

**What happens after all sub-agent data is collected:**

1. **Error Notice Generation**: The OutputFormatter checks each agent's response for errors:
   - Weather error -> "I wasn't able to get the weather forecast..."
   - Flight error -> "I'm having trouble finding flights for those exact dates..."
   - Hotel error -> "I couldn't find hotel availability..."

2. **Delivery Prompt Construction**: All sub-agent data (weather, flights, hotels, itinerary) is serialized as JSON and embedded in the DELIVERY_PROMPT system prompt, along with:
   - Modality-specific formatting rules (text vs voice)
   - Error notices to inform user naturally
   - Strict guardrail instructions

3. **Gemini generates the final travel plan** following the delivery prompt rules

4. **Post-processing Guardrails** (OutputFormatter):

   a. **Budget Adherence Check**:
   ```python
   if budget_level == "low" and cheapest_flight > 500:
       warning = "Note: cheapest flight is $X, higher than budget..."
   ```
   Appended to the response so the user is explicitly informed.

   b. **One Voice Principle** (regex-based):
   - `"The Flight_Agent found"` -> `"I found"`
   - `"The Weather_Agent said"` -> `"I checked"`
   - `"sub-agent"` -> `"system"`
   - `"A2A handoff"` -> `"coordination"`

   c. **Modality Formatting**:
   - **Text mode**: Prices kept as `$350`, markdown preserved
   - **Voice mode**:
     - `$350` -> `"three hundred and fifty dollars"` (number-to-words conversion)
     - All `*`, `#`, `_`, backticks stripped
     - URLs removed
     - Bullet points converted to prose

5. **Final plan saved** to `trip_plans.final_plan` column and `status` set to `"delivered"`

---

## 3. DATABASE SCHEMA (Supabase PostgreSQL)

```sql
-- conversations: Tracks each chat session
conversations (
  id UUID PRIMARY KEY,
  user_id TEXT,
  modality TEXT ('text' | 'voice'),
  status TEXT ('active' | 'completed' | 'archived'),
  travel_requirements JSONB,  -- Structured requirements extracted by Gemini
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ
)

-- messages: Full conversation history
messages (
  id UUID PRIMARY KEY,
  conversation_id UUID -> conversations(id),
  role TEXT ('user' | 'assistant' | 'system'),
  content TEXT,
  metadata JSONB,
  created_at TIMESTAMPTZ
)

-- trip_plans: Complete trip data from all agents
trip_plans (
  id UUID PRIMARY KEY,
  conversation_id UUID -> conversations(id),
  destination TEXT,
  origin TEXT,
  start_date DATE,
  end_date DATE,
  budget_level TEXT ('low' | 'med' | 'high'),
  weather_data JSONB,   -- Full weather agent response
  flight_data JSONB,    -- Full flight agent response
  hotel_data JSONB,     -- Full hotel agent response
  itinerary JSONB,      -- Full local expert response
  final_plan TEXT,      -- Formatted final output
  status TEXT ('planning' | 'ready' | 'delivered'),
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ
)
```

**Why JSONB columns?**
- Sub-agent responses have varying structures
- Enables querying inside JSON (e.g., find all trips to Paris)
- No need for complex normalized tables for agent data

---

## 4. KEY DESIGN PATTERNS

### Multi-Agent Orchestration
- **Pattern**: Manager-Worker with async fan-out
- **Root Agent** = Manager: decides which workers to call and when
- **Sub-Agents** = Workers: each has a single responsibility
- **Fan-out**: Weather, Flight, Hotel called simultaneously (asyncio.gather)
- **Fan-in**: Results collected, then passed to Local Expert sequentially (because it needs the others' data)

### A2A (Agent-to-Agent) Communication
- Not direct agent-to-agent calls
- Root Agent acts as the message broker
- Weather + Hotel data is **passed as context** into the Local Expert's prompt
- This prevents the Local Expert from scheduling outdoor tours during thunderstorms

### System Prompt Engineering
- Three distinct prompt phases, each with specific behavioral constraints
- Marker-based phase transitions (`[REQUIREMENTS_COMPLETE]`)
- Modality variable injection (`CURRENT_MODALITY: text/voice`)
- Guardrail instructions embedded directly in prompts

### Error Resilience
- `return_exceptions=True` in asyncio.gather
- Each agent wraps failures into structured error objects
- OutputFormatter generates natural-language error messages
- The system never crashes; it degrades gracefully

---

## 5. TECH STACK RATIONALE

| Technology | Why |
|---|---|
| **FastAPI** | Async-native Python framework, perfect for concurrent API calls to sub-agents |
| **Next.js 14** | App Router, server components, built-in API rewrites for proxying to backend |
| **Gemini 2.0 Flash** | Fast inference, large context window for multi-agent prompts, free tier |
| **Supabase** | Managed PostgreSQL with JSONB support, instant REST API, RLS for security |
| **Amadeus API** | Industry-standard flight/hotel data, free test sandbox |
| **OpenWeatherMap** | Reliable weather data, free tier (1000 calls/day), geocoding included |
| **Tailwind CSS** | Utility-first CSS, rapid UI iteration, consistent design tokens |

---

## 6. COMMON INTERVIEW QUESTIONS & ANSWERS

### Q: "How do the agents communicate with each other?"
**A**: They don't communicate directly. The Root Agent acts as an orchestrator/broker. It collects data from Weather, Flight, and Hotel agents simultaneously using Python's asyncio, then passes relevant context (weather summary, hotel location) into the Local Expert agent's prompt. This is an A2A handoff pattern where the Root Agent controls all data flow.

### Q: "What happens if the flight API is down?"
**A**: The system uses `asyncio.gather(return_exceptions=True)`, so a failed agent returns an exception object instead of crashing the pipeline. The OutputFormatter detects the error and generates a natural response like "I'm having trouble finding flights for those exact dates. Are you flexible by a day or two?" The rest of the plan (weather, hotels, itinerary) is still delivered.

### Q: "How do you prevent the AI from hallucinating data?"
**A**: Three layers: (1) The system prompt explicitly says "Never invent flight prices, hotel names, or weather data." (2) All factual data comes from real APIs, not from the LLM. (3) The OutputFormatter strips any raw JSON leakage and checks for error states before delivery.

### Q: "Why async for sub-agents instead of sequential?"
**A**: Weather, Flight, and Hotel searches are independent operations. Running them sequentially would take 3x longer (each API call is ~2-5 seconds). Using `asyncio.gather()` runs all three simultaneously, reducing total wait time to the slowest single call. Only the Local Expert runs sequentially because it depends on the others' results.

### Q: "How does modality awareness work?"
**A**: The frontend sends a `modality` field ("text" or "voice") with every request. This is injected into the system prompt as `CURRENT_MODALITY`. The LLM adjusts its response style accordingly. Then the OutputFormatter applies post-processing: for voice mode, it converts "$350" to "three hundred and fifty dollars", strips markdown symbols, and removes URLs.

### Q: "How do you handle budget adherence?"
**A**: The budget level flows through the entire pipeline: Flight agent adjusts cabin class (economy vs business), Hotel agent filters by star rating, Local Expert adjusts activity suggestions (street food vs fine dining). After all data is collected, the OutputFormatter runs a budget adherence check -- if a "low" budget user gets $800 flights, a warning is appended to the response.

### Q: "What is the 'One Voice' principle?"
**A**: The user should never know that multiple AI agents are working behind the scenes. The OutputFormatter uses regex to replace any leaked agent references: "The Flight Agent said..." becomes "I found..." This creates the illusion of a single, unified travel concierge.

### Q: "How is conversation state managed?"
**A**: Every conversation has a `travel_requirements` JSONB column that stores extracted requirements. The Root Agent checks this on every request to determine which phase to enter: (1) if `has_all_requirements` is false -> gathering phase, (2) if true but no trip_plan exists -> orchestrate sub-agents, (3) if trip_plan status is "delivered" -> handle follow-up questions. Full message history is stored in the messages table for context.

### Q: "What would you improve if you had more time?"
**A**: (1) Add caching for API responses to avoid redundant calls. (2) Implement streaming responses via WebSocket for real-time typing effect. (3) Add user authentication with Supabase Auth. (4) Build a trip comparison feature. (5) Add email/PDF export of itineraries. (6) Implement rate limiting and request queuing.

---

## 7. API ENDPOINTS

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Health check |
| GET | `/api/status` | Agent status + config |
| POST | `/api/chat` | Main chat endpoint (handles all phases) |
| POST | `/api/conversations` | Create new conversation |
| GET | `/api/conversations/:id` | Get conversation details |
| GET | `/api/conversations/:id/messages` | Get message history |
| WS | `/ws/chat` | WebSocket for real-time chat |

---

## 8. FILE STRUCTURE

```
AI-Travel-Planner/
├── backend/
│   ├── agents/
│   │   ├── root_agent.py        # Orchestrator - phases 1, 2, 3
│   │   ├── weather_agent.py     # OpenWeatherMap integration
│   │   ├── flight_agent.py      # Amadeus flights
│   │   ├── hotel_agent.py       # Amadeus hotels
│   │   └── local_expert_agent.py # Gemini-powered itinerary builder
│   ├── services/
│   │   ├── gemini_service.py    # Google GenAI client
│   │   ├── supabase_service.py  # Database operations
│   │   └── output_formatter.py  # Phase 3 guardrails
│   ├── models/
│   │   └── schemas.py           # Pydantic request/response models
│   ├── config/
│   │   └── settings.py          # Environment config
│   ├── main.py                  # FastAPI app + routes
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── components/
│   │   │   ├── Sidebar.tsx
│   │   │   ├── WelcomeScreen.tsx
│   │   │   ├── ChatMessage.tsx
│   │   │   ├── ChatInput.tsx
│   │   │   ├── TypingIndicator.tsx
│   │   │   └── RequirementsPanel.tsx
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── package.json
│   ├── tailwind.config.ts
│   └── next.config.js
├── .env                         # API keys (gitignored)
├── .env.example                 # Template for required keys
├── .gitignore
└── run_backend.py               # Backend entry point
```
