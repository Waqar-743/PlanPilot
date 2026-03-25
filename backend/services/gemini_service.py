from google import genai
from google.genai import types
from backend.config.settings import settings
import json
import asyncio


class GeminiService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = "gemini-2.0-flash"
        self.max_retries = 3

    async def _call_with_retry(self, func, *args, **kwargs):
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    wait = (attempt + 1) * 8
                    await asyncio.sleep(wait)
                    continue
                raise
        raise Exception("Gemini API rate limit exceeded. Please try again in a moment.")

    async def generate(self, system_prompt: str, conversation_history: list[dict], user_message: str) -> str:
        contents = []

        contents.append(types.Content(
            role="user",
            parts=[types.Part(text=system_prompt + "\n\n---\nConversation begins now.")]
        ))
        contents.append(types.Content(
            role="model",
            parts=[types.Part(text="Understood. I am ready to assist as the AI Travel Planner.")]
        ))

        for msg in conversation_history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(types.Content(
                role=role,
                parts=[types.Part(text=msg["content"])]
            ))

        contents.append(types.Content(
            role="user",
            parts=[types.Part(text=user_message)]
        ))

        response = await self._call_with_retry(
            self.client.models.generate_content,
            model=self.model,
            contents=contents
        )
        return response.text

    async def generate_simple(self, prompt: str) -> str:
        response = await self._call_with_retry(
            self.client.models.generate_content,
            model=self.model,
            contents=prompt
        )
        return response.text

    async def extract_requirements(self, conversation_history: list[dict]) -> dict:
        extraction_prompt = """Analyze the conversation below and extract travel requirements.
Return ONLY a valid JSON object with these fields (use null for missing values):
{
  "destination": "city name or null",
  "origin": "city name or null",
  "start_date": "YYYY-MM-DD or null",
  "end_date": "YYYY-MM-DD or null",
  "budget_level": "low/med/high or null",
  "duration_days": number or null,
  "has_all_requirements": true/false
}

"has_all_requirements" should be true ONLY if destination, dates (start+end OR duration), and budget are all present.

Conversation:
"""
        for msg in conversation_history:
            extraction_prompt += f"\n{msg['role'].upper()}: {msg['content']}"

        response = await self._call_with_retry(
            self.client.models.generate_content,
            model=self.model,
            contents=extraction_prompt
        )
        text = response.text.strip()

        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            return {"has_all_requirements": False}


gemini_service = GeminiService()
