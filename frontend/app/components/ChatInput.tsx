"use client";

import { useState, useRef, useEffect } from "react";
import { ArrowUp, Mic, MicOff, Type } from "lucide-react";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled: boolean;
  modality: "text" | "voice";
  onToggleModality: () => void;
  isListening?: boolean;
  transcript?: string;
  onStartListening?: () => void;
  onStopListening?: () => void;
  sttError?: string | null;
}

export default function ChatInput({
  onSend,
  disabled,
  modality,
  onToggleModality,
  isListening,
  transcript,
  onStartListening,
  onStopListening,
  sttError,
}: ChatInputProps) {
  const [message, setMessage] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (isListening && transcript) {
      setMessage(transcript);
    }
  }, [transcript, isListening]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height =
        Math.min(textareaRef.current.scrollHeight, 150) + "px";
    }
  }, [message]);

  const handleSend = () => {
    if (!message.trim() || disabled) return;
    if (isListening && onStopListening) onStopListening();
    onSend(message.trim());
    setMessage("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleMicClick = () => {
    if (isListening) {
      onStopListening?.();
      if (message.trim()) {
        setTimeout(() => handleSend(), 200);
      }
    } else {
      setMessage("");
      onStartListening?.();
    }
  };

  return (
    <div className="px-4 pb-4 pt-2 bg-cream-100">
      <div className="max-w-3xl mx-auto">
        {/* Listening indicator */}
        {isListening && (
          <div className="flex items-center justify-center gap-2 mb-2 animate-fade-in">
            <div className="flex gap-1">
              <div className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
              <div className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" style={{ animationDelay: "0.15s" }} />
              <div className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" style={{ animationDelay: "0.3s" }} />
            </div>
            <span className="text-[12px] text-accent font-semibold">
              Listening... {transcript ? `"${transcript}"` : "speak now"}
            </span>
          </div>
        )}

        {sttError && (
          <p className="text-center text-[11px] text-accent mb-2">{sttError}</p>
        )}

        {/* Input Container */}
        <div
          className={`relative rounded-2xl border transition-all duration-200 ${
            isListening
              ? "bg-white border-accent/30 shadow-sm"
              : "bg-white border-black/[0.08] focus-within:border-accent/30 shadow-sm"
          }`}
        >
          <div className="flex items-end gap-1 p-1.5 pl-4">
            {/* Modality Toggle */}
            <button
              onClick={onToggleModality}
              className={`p-2 rounded-lg transition-all duration-200 flex-shrink-0 mb-0.5 ${
                modality === "voice"
                  ? "bg-accent/10 text-accent"
                  : "text-ink-faint hover:text-ink-muted hover:bg-black/[0.04]"
              }`}
              title={
                modality === "voice"
                  ? "Switch to text mode"
                  : "Switch to voice mode"
              }
            >
              {modality === "voice" ? (
                <Mic className="w-[18px] h-[18px]" />
              ) : (
                <Type className="w-[18px] h-[18px]" />
              )}
            </button>

            {/* Textarea */}
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                isListening ? "Listening..." : "Plan your trip across Pakistan..."
              }
              disabled={disabled || isListening}
              rows={1}
              className="flex-1 bg-transparent py-2.5 px-2 text-[15px] text-ink placeholder-ink-faint/60 resize-none focus:outline-none disabled:opacity-40 leading-relaxed"
            />

            {/* Mic Button */}
            {onStartListening && (
              <button
                onClick={handleMicClick}
                disabled={disabled}
                className={`p-2.5 rounded-lg transition-all duration-200 flex-shrink-0 mb-0.5 ${
                  isListening
                    ? "bg-accent text-white animate-pulse"
                    : "text-ink-faint hover:text-ink-muted hover:bg-black/[0.04]"
                }`}
                title={isListening ? "Stop listening" : "Voice input"}
              >
                {isListening ? (
                  <MicOff className="w-[18px] h-[18px]" />
                ) : (
                  <Mic className="w-[18px] h-[18px]" />
                )}
              </button>
            )}

            {/* Send Button */}
            <button
              onClick={handleSend}
              disabled={!message.trim() || disabled}
              className={`p-2.5 rounded-lg transition-all duration-200 flex-shrink-0 mb-0.5 ${
                message.trim() && !disabled
                  ? "bg-ink text-white hover:bg-ink-light"
                  : "bg-black/[0.04] text-ink-faint/40 cursor-not-allowed"
              }`}
            >
              <ArrowUp className="w-[18px] h-[18px]" strokeWidth={2.5} />
            </button>
          </div>
        </div>

        <p className="text-center text-[11px] text-ink-faint mt-2.5">
          PlanPilot AI may produce inaccurate information. Verify details
          before booking.
        </p>
      </div>
    </div>
  );
}
