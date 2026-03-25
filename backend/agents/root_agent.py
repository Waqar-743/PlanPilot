import json
import asyncio
from backend.services.gemini_service import gemini_service
from backend.services.supabase_service import supabase_service
from backend.services.output_formatter import output_formatter
from backend.agents.weather_agent import weather_agent
from backend.agents.flight_agent import flight_agent
from backend.agents.hotel_agent import hotel_agent
from backend.agents.local_expert_agent import local_expert_agent
from backend.models.schemas import ChatRequest, ChatResponse, Modality

# ============================================================
# SYSTEM PROMPT - PHASE 1: PERSONA & CORE BEHAVIOR
# ============================================================
GATHERING_PROMPT = """
PHASE 1: PERSONA & CORE BEHAVIOR (MULTIMODAL)

Role: You are the Root Agent for a premium AI Travel Planning system. You act as the lead
orchestrator and the sole point of contact for the user.

Core Directive: Your job is to understand the user's travel goals, gather necessary constraints,
and coordinate with your specialized sub-agents (Flight, Accommodation, Weather, Local Expert)
to build a comprehensive, realistic travel itinerary.

Interaction Rules:
1. Identify if you have the core requirements: Destination, Dates/Duration, Origin City, and rough Budget.
2. If missing, ask a maximum of TWO short, conversational follow-up questions.
3. Fallback: If the user ignores your questions, DO NOT ask again. Make logical assumptions based on their initial prompt and immediately begin planning.
4. Modality Awareness: Pay attention to how the user interacts.
   - If VOICE mode: keep sentences conversational, concise, no markdown.
   - If TEXT mode: use clean markdown, bullet points, bold text.
5. Never invent flight prices, hotel names, or weather data.

You are in the GATHERING phase. Collect: destination, travel dates (or duration), origin city, and budget (low/med/high).
When you have enough info, confirm the details and end your message with: [REQUIREMENTS_COMPLETE]

CURRENT_MODALITY: {modality}
"""

# ============================================================
# SYSTEM PROMPT - PHASE 2: SUB-AGENT ROUTING & A2A DELEGATION
# ============================================================
PLANNING_PROMPT = """
The user's travel requirements have been collected. You are now coordinating your sub-agents.
Tell the user you have everything you need and are now working on their plan.
Be warm, professional, and let them know you're checking weather, flights, hotels, and building their itinerary.
Keep it brief -- just a transition message.

CURRENT_MODALITY: {modality}
"""

# ============================================================
# SYSTEM PROMPT - PHASE 3: FINAL OUTPUT & STRICT GUARDRAILS
# ============================================================
DELIVERY_PROMPT = """
PHASE 3: FINAL OUTPUT & STRICT GUARDRAILS

You are the Root Agent. You have received ALL data from your sub-agents. Present the final travel plan.

STRICT RULES:
1. NO HALLUCINATIONS: Only use the data provided below. If a sub-agent returned an error, inform the user naturally (e.g., "I'm having trouble finding flights for those exact dates. Are you flexible by a day or two?")
2. BUDGET ADHERENCE: If the user requested a budget trip but results are expensive, point it out explicitly.
3. ONE VOICE: Never say "The Flight Agent said..." or "I am talking to the Weather Agent." Say "I found great flights..." or "I checked the weather..."

Output Formatting (Based on Modality):
{modality_rules}

=== SUB-AGENT DATA ===

WEATHER DATA:
{weather_data}

FLIGHT DATA:
{flight_data}

HOTEL DATA:
{hotel_data}

ITINERARY DATA:
{itinerary_data}

=== END SUB-AGENT DATA ===

Present the complete travel plan to the user now. Include all sections: Weather overview, Flights, Accommodation, and Day-by-Day Itinerary.
"""

TEXT_MODE_RULES = """
IF TEXT MODE:
- Provide a brief, enthusiastic introduction.
- Use clearly labeled sections with bold headers (e.g., Flights, Accommodation, Day 1: Arrival & Exploration).
- Display prices clearly with currency symbols (e.g., $350).
- Use bullet points for daily itineraries.
"""

VOICE_MODE_RULES = """
IF VOICE MODE:
- Start with a warm, natural greeting (e.g., "I've got your trip to Rome all planned out!").
- CRITICAL: Do NOT output any asterisks (*), hashtags (#), or long URLs.
- Group information naturally as you would in a conversation.
- Read out numbers and currencies naturally (write "three hundred and fifty dollars" instead of "$350").
- Keep the daily itinerary summary brief. Offer to read the full day-by-day plan.
"""


class RootAgent:
    def __init__(self):
        self.gemini = gemini_service
        self.db = supabase_service

    async def chat(self, request: ChatRequest) -> ChatResponse:
        if request.conversation_id:
            conversation = self.db.get_conversation(request.conversation_id)
            if not conversation:
                conversation = self.db.create_conversation(modality=request.modality.value)
        else:
            conversation = self.db.create_conversation(modality=request.modality.value)

        conversation_id = conversation["id"]
        self.db.add_message(conversation_id, "user", request.message)

        messages = self.db.get_messages(conversation_id)
        history = [{"role": m["role"], "content": m["content"]} for m in messages[:-1]]

        travel_reqs = conversation.get("travel_requirements", {})

        # ---- Phase branching ----
        if travel_reqs and travel_reqs.get("has_all_requirements"):
            trip_plan = self.db.get_trip_plan(conversation_id)

            if trip_plan and trip_plan.get("status") == "delivered":
                # Already delivered -- handle follow-up questions
                reply = await self._handle_followup(request, history, trip_plan, travel_reqs)
            elif trip_plan and trip_plan.get("status") == "ready":
                # Plan is ready but not yet delivered -- deliver it
                reply = await self._deliver_plan(trip_plan, request.modality)
                self.db.update_trip_plan(trip_plan["id"], {"status": "delivered"})
            else:
                # Requirements complete but no plan yet -- orchestrate sub-agents
                reply = await self._orchestrate(conversation_id, request, travel_reqs, history)
        else:
            # Still gathering requirements
            reply = await self._gather_requirements(request, history, conversation_id, messages)

        self.db.add_message(conversation_id, "assistant", reply["text"])

        return ChatResponse(
            reply=reply["text"],
            conversation_id=conversation_id,
            travel_requirements=reply.get("requirements"),
            phase=reply.get("phase", "gathering")
        )

    # -----------------------------------------------------------------
    # PHASE 1: Gathering requirements
    # -----------------------------------------------------------------
    async def _gather_requirements(self, request, history, conversation_id, messages) -> dict:
        system_prompt = GATHERING_PROMPT.format(modality=request.modality.value)
        response = await self.gemini.generate(system_prompt, history, request.message)

        requirements_complete = "[REQUIREMENTS_COMPLETE]" in response
        reply_clean = response.replace("[REQUIREMENTS_COMPLETE]", "").strip()

        extracted_reqs = None
        phase = "gathering"

        if requirements_complete:
            all_msgs = [{"role": m["role"], "content": m["content"]} for m in messages]
            all_msgs.append({"role": "assistant", "content": reply_clean})
            extracted_reqs = await self.gemini.extract_requirements(all_msgs)
            self.db.update_conversation(conversation_id, {"travel_requirements": extracted_reqs})
            if extracted_reqs.get("has_all_requirements"):
                phase = "ready"

        reply_clean = output_formatter.format_response(reply_clean, request.modality.value)
        return {"text": reply_clean, "requirements": extracted_reqs, "phase": phase}

    # -----------------------------------------------------------------
    # PHASE 2: Orchestrate sub-agents (Async Delegation)
    # -----------------------------------------------------------------
    async def _orchestrate(self, conversation_id, request, reqs, history) -> dict:
        # First, send a transition message
        transition_prompt = PLANNING_PROMPT.format(modality=request.modality.value)
        transition_msg = await self.gemini.generate(transition_prompt, history, request.message)
        transition_clean = transition_msg.replace("[REQUIREMENTS_COMPLETE]", "").strip()

        # Prepare parameters
        destination = reqs.get("destination", "Unknown")
        origin = reqs.get("origin", "Unknown")
        start_date = reqs.get("start_date", "")
        end_date = reqs.get("end_date", "")
        budget = reqs.get("budget_level", "med")
        duration = reqs.get("duration_days", 3)

        if start_date and end_date:
            dates_str = f"{start_date} to {end_date}"
        else:
            dates_str = f"{start_date} to {start_date}" if start_date else ""

        # === ASYNC DELEGATION: Dispatch Weather, Flight, Hotel simultaneously ===
        weather_task = asyncio.create_task(
            weather_agent.get_forecast(destination, dates_str)
        )
        flight_task = asyncio.create_task(
            flight_agent.search_flights(origin, destination, start_date, end_date, budget)
        )
        hotel_task = asyncio.create_task(
            hotel_agent.search_hotels(destination, start_date, end_date, budget)
        )

        # Wait for all three
        weather_data, flight_data, hotel_data = await asyncio.gather(
            weather_task, flight_task, hotel_task,
            return_exceptions=True
        )

        # Handle exceptions
        if isinstance(weather_data, Exception):
            weather_data = {"error": str(weather_data)}
        if isinstance(flight_data, Exception):
            flight_data = {"error": str(flight_data)}
        if isinstance(hotel_data, Exception):
            hotel_data = {"error": str(hotel_data)}

        # === A2A HANDOFF: Pass Weather + Hotel context to Local Expert ===
        weather_context = weather_data.get("summary", "Weather data unavailable")
        hotel_location = "City center"
        if not hotel_data.get("error") and hotel_data.get("hotels"):
            top_hotel = hotel_data["hotels"][0]
            hotel_location = f"{top_hotel.get('name', 'Hotel')} in {destination}"

        itinerary_data = await local_expert_agent.build_itinerary(
            destination=destination,
            duration_days=duration,
            weather_context=weather_context,
            hotel_location=hotel_location,
            budget_level=budget
        )

        # Save trip plan to database
        plan_data = {
            "destination": destination,
            "origin": origin,
            "start_date": start_date,
            "end_date": end_date,
            "budget_level": budget,
            "weather_data": json.dumps(weather_data, default=str),
            "flight_data": json.dumps(flight_data, default=str),
            "hotel_data": json.dumps(hotel_data, default=str),
            "itinerary": json.dumps(itinerary_data, default=str),
            "status": "ready",
        }

        trip_plan = self.db.create_trip_plan(conversation_id, plan_data)

        # Deliver the plan with all guardrails
        delivery = await self._deliver_plan_from_data(
            weather_data, flight_data, hotel_data, itinerary_data, request.modality, budget
        )

        self.db.update_trip_plan(trip_plan["id"], {"status": "delivered", "final_plan": delivery})

        return {"text": f"{transition_clean}\n\n---\n\n{delivery}", "phase": "delivered"}

    # -----------------------------------------------------------------
    # PHASE 3: Deliver the final plan using Gemini with guardrails
    # -----------------------------------------------------------------
    async def _deliver_plan_from_data(self, weather_data, flight_data, hotel_data, itinerary_data, modality, budget_level: str = "med") -> str:
        modality_rules = TEXT_MODE_RULES if modality == Modality.TEXT else VOICE_MODE_RULES

        # Guardrail 1: Check for sub-agent errors before delivery
        error_notices = output_formatter.build_error_notices(weather_data, flight_data, hotel_data)

        prompt = DELIVERY_PROMPT.format(
            modality_rules=modality_rules,
            weather_data=json.dumps(weather_data, indent=2, default=str),
            flight_data=json.dumps(flight_data, indent=2, default=str),
            hotel_data=json.dumps(hotel_data, indent=2, default=str),
            itinerary_data=json.dumps(itinerary_data, indent=2, default=str),
        )

        if error_notices:
            prompt += "\n\nIMPORTANT - These data issues occurred. Inform the user naturally:\n"
            for notice in error_notices:
                prompt += f"- {notice}\n"

        response = await self.gemini.generate_simple(prompt)
        formatted = response.strip()

        # Guardrail 2: Budget adherence check
        budget_warning = output_formatter.check_budget_adherence(
            flight_data, hotel_data, budget_level
        )
        if budget_warning:
            formatted += f"\n\n---\n\n{budget_warning}"

        # Guardrail 3: Apply output formatting (strip agent refs, modality rules)
        formatted = output_formatter.format_response(formatted, modality.value if hasattr(modality, 'value') else modality)

        return formatted

    async def _deliver_plan(self, trip_plan, modality) -> str:
        if trip_plan.get("final_plan"):
            return output_formatter.format_response(
                trip_plan["final_plan"],
                modality.value if hasattr(modality, 'value') else modality
            )

        weather_data = json.loads(trip_plan.get("weather_data", "{}"))
        flight_data = json.loads(trip_plan.get("flight_data", "{}"))
        hotel_data = json.loads(trip_plan.get("hotel_data", "{}"))
        itinerary_data = json.loads(trip_plan.get("itinerary", "{}"))
        budget_level = trip_plan.get("budget_level", "med")

        return await self._deliver_plan_from_data(
            weather_data, flight_data, hotel_data, itinerary_data, modality, budget_level
        )

    # -----------------------------------------------------------------
    # Follow-up handler (post-delivery)
    # -----------------------------------------------------------------
    async def _handle_followup(self, request, history, trip_plan, reqs) -> dict:
        followup_prompt = f"""You are the AI Travel Planner. You already delivered a trip plan to the user.
Here are the trip details: destination={reqs.get('destination')}, dates={reqs.get('start_date')} to {reqs.get('end_date')}, budget={reqs.get('budget_level')}.

The user is asking a follow-up question. Answer helpfully based on the trip plan data.
Act as a unified concierge -- never mention sub-agents. Say "I found..." not "The agent said..."

CURRENT_MODALITY: {request.modality.value}
"""
        response = await self.gemini.generate(followup_prompt, history, request.message)
        formatted = output_formatter.format_response(response.strip(), request.modality.value)
        return {"text": formatted, "phase": "delivered"}


root_agent = RootAgent()
