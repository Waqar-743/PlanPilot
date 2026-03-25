from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from backend.models.schemas import ChatRequest, ChatResponse, ConversationCreate
from backend.agents.root_agent import root_agent
from backend.services.supabase_service import supabase_service
from backend.config.settings import settings
import json

app = FastAPI(
    title="AI Travel Planner",
    description="Premium AI-powered travel planning with multi-agent orchestration",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def health_check():
    return {"status": "healthy", "service": "AI Travel Planner API"}


@app.get("/api/status")
async def api_status():
    return {
        "agents": {
            "root_agent": "active",
            "weather_agent": "active" if settings.OPENWEATHER_API_KEY else "no_api_key",
            "flight_agent": "active" if settings.AMADEUS_API_KEY else "no_api_key",
            "hotel_agent": "active" if settings.AMADEUS_API_KEY else "no_api_key",
            "local_expert_agent": "active" if settings.GEMINI_API_KEY else "no_api_key",
        },
        "database": "supabase_connected" if settings.SUPABASE_URL else "not_configured",
        "llm": "gemini-2.0-flash",
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        response = await root_agent.chat(request)
        return response
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "rate limit" in error_msg.lower():
            return ChatResponse(
                reply="I'm getting a lot of requests right now. Please wait a few seconds and try again.",
                conversation_id=request.conversation_id or "",
                phase="gathering"
            )
        raise HTTPException(status_code=500, detail=error_msg)


@app.post("/api/conversations")
async def create_conversation(request: ConversationCreate):
    try:
        conversation = supabase_service.create_conversation(
            modality=request.modality.value,
            user_id=request.user_id or "anonymous"
        )
        return conversation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    conversation = supabase_service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@app.get("/api/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: str):
    messages = supabase_service.get_messages(conversation_id)
    return {"messages": messages}


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            request_data = json.loads(data)
            request = ChatRequest(**request_data)
            response = await root_agent.chat(request)
            await websocket.send_text(response.model_dump_json())
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_text(json.dumps({"error": str(e)}))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
