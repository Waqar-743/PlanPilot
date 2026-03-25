from supabase import create_client, Client
from backend.config.settings import settings
from typing import Optional
import json


class SupabaseService:
    def __init__(self):
        self.client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY
        )

    def create_conversation(self, modality: str = "text", user_id: str = "anonymous") -> dict:
        result = self.client.table("conversations").insert({
            "modality": modality,
            "user_id": user_id,
            "status": "active",
            "travel_requirements": {}
        }).execute()
        return result.data[0]

    def get_conversation(self, conversation_id: str) -> Optional[dict]:
        result = self.client.table("conversations").select("*").eq(
            "id", conversation_id
        ).execute()
        return result.data[0] if result.data else None

    def update_conversation(self, conversation_id: str, updates: dict) -> dict:
        result = self.client.table("conversations").update(updates).eq(
            "id", conversation_id
        ).execute()
        return result.data[0]

    def add_message(self, conversation_id: str, role: str, content: str, metadata: dict = None) -> dict:
        result = self.client.table("messages").insert({
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "metadata": metadata or {}
        }).execute()
        return result.data[0]

    def get_messages(self, conversation_id: str, limit: int = 50) -> list:
        result = self.client.table("messages").select("*").eq(
            "conversation_id", conversation_id
        ).order("created_at").limit(limit).execute()
        return result.data

    def create_trip_plan(self, conversation_id: str, plan_data: dict) -> dict:
        result = self.client.table("trip_plans").insert({
            "conversation_id": conversation_id,
            **plan_data
        }).execute()
        return result.data[0]

    def update_trip_plan(self, plan_id: str, updates: dict) -> dict:
        result = self.client.table("trip_plans").update(updates).eq(
            "id", plan_id
        ).execute()
        return result.data[0]

    def get_trip_plan(self, conversation_id: str) -> Optional[dict]:
        result = self.client.table("trip_plans").select("*").eq(
            "conversation_id", conversation_id
        ).order("created_at", desc=True).limit(1).execute()
        return result.data[0] if result.data else None


supabase_service = SupabaseService()
