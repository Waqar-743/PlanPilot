from backend.services.gemini_service import gemini_service


class LocalExpertAgent:
    """
    Builds day-by-day itineraries using Gemini AI with context from Weather and Hotel agents.
    Trigger: Called ONLY AFTER receiving data from Weather, Flight, and Hotel agents.
    Required Input: {
        "destination": "City", "duration_days": int,
        "weather_context": "string", "hotel_location": "string"
    }
    """

    def __init__(self):
        self.gemini = gemini_service

    async def build_itinerary(
        self, destination: str, duration_days: int,
        weather_context: str, hotel_location: str,
        budget_level: str = "med"
    ) -> dict:
        prompt = f"""You are a local travel expert for {destination}. 
Create a detailed day-by-day itinerary for {duration_days} days.

CONTEXT:
- Weather forecast: {weather_context}
- Hotel location: {hotel_location}
- Budget level: {budget_level}

RULES:
1. NEVER schedule outdoor walking tours or activities during rain or storms.
2. Suggest indoor alternatives for bad weather days.
3. Include realistic time slots (morning, afternoon, evening).
4. Recommend REAL restaurants, cafes, and attractions (no invented places).
5. Consider the hotel location for proximity-based planning.
6. Include estimated costs in USD for each activity.
7. Mix popular landmarks with local hidden gems.
8. Account for budget level: {"budget-friendly options, street food, free attractions" if budget_level == "low" else "balanced mix of free and paid activities" if budget_level == "med" else "premium experiences, fine dining, VIP access"}.

Return the itinerary as a JSON object with this structure:
{{
  "destination": "{destination}",
  "duration_days": {duration_days},
  "daily_itinerary": [
    {{
      "day": 1,
      "theme": "Arrival & City Highlights",
      "weather_note": "Clear skies, 25°C",
      "activities": [
        {{
          "time": "09:00 AM",
          "activity": "Activity name",
          "location": "Specific location name",
          "description": "Brief description",
          "estimated_cost": "$X",
          "indoor_outdoor": "outdoor",
          "duration": "2 hours"
        }}
      ],
      "meals": [
        {{
          "type": "lunch",
          "restaurant": "Real restaurant name",
          "cuisine": "Type of cuisine",
          "estimated_cost": "$X"
        }}
      ],
      "tips": ["Useful local tip"]
    }}
  ],
  "general_tips": ["Overall trip tips"],
  "estimated_total_cost": "$X"
}}

Return ONLY the JSON object, no extra text.
"""

        response = await self.gemini.generate_simple(prompt)
        text = response.strip()

        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        import json
        try:
            itinerary = json.loads(text.strip())
            itinerary["summary"] = self._build_summary(itinerary, destination, duration_days)
            return itinerary
        except json.JSONDecodeError:
            return {
                "destination": destination,
                "duration_days": duration_days,
                "raw_itinerary": text,
                "summary": f"Generated a {duration_days}-day itinerary for {destination}.",
                "parse_error": True
            }

    def _build_summary(self, itinerary: dict, destination: str, days: int) -> str:
        daily = itinerary.get("daily_itinerary", [])
        total_activities = sum(len(d.get("activities", [])) for d in daily)
        total_cost = itinerary.get("estimated_total_cost", "N/A")

        themes = [d.get("theme", "") for d in daily if d.get("theme")]
        theme_str = ", ".join(themes[:3])
        if len(themes) > 3:
            theme_str += f", and {len(themes) - 3} more"

        return (
            f"Your {days}-day {destination} itinerary includes {total_activities} activities. "
            f"Highlights: {theme_str}. "
            f"Estimated total cost: {total_cost}."
        )


local_expert_agent = LocalExpertAgent()
