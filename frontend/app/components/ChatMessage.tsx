"use client";

import ReactMarkdown from "react-markdown";
import { Sparkles, Volume2, VolumeX } from "lucide-react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

interface ChatMessageProps {
  message: Message;
  isSpeaking?: boolean;
  isSpeakingThis?: boolean;
  onToggleSpeech?: (text: string, id: string) => void;
}

export default function ChatMessage({
  message,
  isSpeaking,
  isSpeakingThis,
  onToggleSpeech,
}: ChatMessageProps) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end animate-fade-in">
        <div className="max-w-[75%]">
          <div className="bg-ink text-white rounded-2xl rounded-br-sm px-5 py-3.5">
            <p className="text-[15px] leading-[1.7]">
              {message.content}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-3 animate-fade-in-up group">
      {/* AI Icon */}
      <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-1 bg-accent">
        <Sparkles className="w-3.5 h-3.5 text-white" />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 pt-0.5">
        <div className="markdown-body text-[15px] leading-[1.8]">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>

        {/* Actions Row */}
        <div className="flex items-center gap-3 mt-2">
          <p className="text-[11px] text-ink-faint">
            {new Date(message.timestamp).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </p>

          {onToggleSpeech && (
            <button
              onClick={() => onToggleSpeech(message.content, message.id)}
              className={`flex items-center gap-1 px-2 py-1 rounded-full text-[10px] font-semibold uppercase tracking-wider transition-all duration-200 ${
                isSpeakingThis
                  ? "bg-accent/10 text-accent border border-accent/20"
                  : "text-ink-faint hover:text-ink-muted hover:bg-black/[0.04] opacity-0 group-hover:opacity-100 border border-transparent"
              }`}
              title={isSpeakingThis ? "Stop reading" : "Read aloud"}
            >
              {isSpeakingThis ? (
                <>
                  <VolumeX className="w-3 h-3" />
                  <span>Stop</span>
                </>
              ) : (
                <>
                  <Volume2 className="w-3 h-3" />
                  <span>Listen</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
