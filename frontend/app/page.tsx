"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import Sidebar from "./components/Sidebar";
import ChatMessage from "./components/ChatMessage";
import ChatInput from "./components/ChatInput";
import TypingIndicator from "./components/TypingIndicator";
import WelcomeScreen from "./components/WelcomeScreen";
import RequirementsPanel from "./components/RequirementsPanel";
import { useTextToSpeech, useSpeechToText } from "./hooks/useSpeech";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

interface Conversation {
  id: string;
  preview: string;
  date: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [modality, setModality] = useState<"text" | "voice">("text");
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [phase, setPhase] = useState("gathering");
  const [travelRequirements, setTravelRequirements] = useState<any>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // TTS hook
  const { isSpeaking, speakingId, toggle: toggleSpeech, stop: stopSpeech } =
    useTextToSpeech();

  // STT hook -- onResult fires when speech is finalized
  const handleVoiceResult = useCallback((text: string) => {
    // We don't auto-send; user reviews transcript in input and hits send
  }, []);

  const {
    isListening,
    transcript,
    startListening,
    stopListening,
    error: sttError,
  } = useSpeechToText(handleVoiceResult);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Auto-read AI responses in voice mode
  const lastMessageRef = useRef<string | null>(null);
  useEffect(() => {
    if (modality === "voice" && messages.length > 0) {
      const last = messages[messages.length - 1];
      if (last.role === "assistant" && last.id !== lastMessageRef.current) {
        lastMessageRef.current = last.id;
        // Small delay so UI renders first
        setTimeout(() => toggleSpeech(last.content, last.id), 300);
      }
    }
  }, [messages, modality, toggleSpeech]);

  const sendMessage = async (content: string) => {
    // Stop any ongoing speech when user sends a message
    stopSpeech();

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: content,
          conversation_id: conversationId,
          modality,
        }),
      });

      if (!response.ok) throw new Error("Failed to send message");

      const data = await response.json();

      if (!conversationId) {
        setConversationId(data.conversation_id);
        setConversations((prev) => [
          {
            id: data.conversation_id,
            preview:
              content.slice(0, 45) + (content.length > 45 ? "..." : ""),
            date: new Date().toLocaleDateString(),
          },
          ...prev,
        ]);
      }

      setPhase(data.phase || "gathering");
      if (data.travel_requirements) {
        setTravelRequirements(data.travel_requirements);
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.reply,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content:
          "I apologize, but I encountered a connection issue. Please check that the backend server is running and try again.",
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = () => {
    stopSpeech();
    setMessages([]);
    setConversationId(null);
    setPhase("gathering");
    setTravelRequirements(null);
  };

  const handleSelectConversation = async (id: string) => {
    stopSpeech();
    try {
      const res = await fetch(`${API_BASE}/api/conversations/${id}/messages`);
      const data = await res.json();
      setConversationId(id);
      setMessages(
        data.messages.map((m: any) => ({
          id: m.id,
          role: m.role,
          content: m.content,
          timestamp: m.created_at,
        }))
      );
    } catch {
      console.error("Failed to load conversation");
    }
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar
        onNewChat={handleNewChat}
        conversations={conversations}
        activeConversation={conversationId}
        onSelectConversation={handleSelectConversation}
      />

      <main className="flex-1 flex flex-col h-screen min-w-0 bg-[#0a0c14]">
        {/* Minimal Header */}
        <header className="h-12 flex items-center justify-center px-5 border-b border-white/[0.03] flex-shrink-0">
          <span className="text-[15px] font-semibold text-slate-200 tracking-tight">
            TravelAI
          </span>
          {phase === "delivered" && (
            <span className="text-[12px] text-emerald-400/80 font-medium ml-2">
              -- Plan Ready
            </span>
          )}
        </header>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <WelcomeScreen onSuggestionClick={sendMessage} />
          ) : (
            <div className="max-w-3xl mx-auto py-6 px-5 space-y-6">
              {travelRequirements && (
                <RequirementsPanel requirements={travelRequirements} />
              )}
              {messages.map((msg) => (
                <ChatMessage
                  key={msg.id}
                  message={msg}
                  isSpeaking={isSpeaking}
                  isSpeakingThis={speakingId === msg.id}
                  onToggleSpeech={
                    msg.role === "assistant" ? toggleSpeech : undefined
                  }
                />
              ))}
              {isLoading && <TypingIndicator />}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input */}
        <ChatInput
          onSend={sendMessage}
          disabled={isLoading}
          modality={modality}
          onToggleModality={() => {
            stopSpeech();
            setModality((prev) => (prev === "text" ? "voice" : "text"));
          }}
          isListening={isListening}
          transcript={transcript}
          onStartListening={startListening}
          onStopListening={stopListening}
          sttError={sttError}
        />
      </main>
    </div>
  );
}
