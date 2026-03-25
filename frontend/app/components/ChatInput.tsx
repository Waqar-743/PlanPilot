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

  // Sync transcript into the input field while listening
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
      // Auto-send if we have transcript
      if (message.trim()) {
        setTimeout(() => handleSend(), 200);
      }
    } else {
      setMessage("");
      onStartListening?.();
    }
  };

  return (
    <div className="px-4 pb-4 pt-2">
      <div className="max-w-3xl mx-auto">
        {/* Listening indicator */}
        {isListening && (
          <div className="flex items-center justify-center gap-2 mb-2 animate-fade-in">
            <div className="flex gap-1">
              <div className="w-1.5 h-1.5 rounded-full bg-rose-400 animate-pulse" />
              <div className="w-1.5 h-1.5 rounded-full bg-rose-400 animate-pulse" style={{ animationDelay: "0.15s" }} />
              <div className="w-1.5 h-1.5 rounded-full bg-rose-400 animate-pulse" style={{ animationDelay: "0.3s" }} />
            </div>
            <span className="text-[12px] text-rose-400 font-medium">
              Listening... {transcript ? `"${transcript}"` : "speak now"}
            </span>
          </div>
        )}

        {/* STT Error */}
        {sttError && (
          <p className="text-center text-[11px] text-rose-400 mb-2">{sttError}</p>
        )}

        {/* Input Container */}
        <div
          className={`relative rounded-3xl border shadow-lg shadow-black/20 transition-all duration-200 ${
            isListening
              ? "bg-[#1a1d2e] border-rose-500/30 shadow-rose-500/5"
              : "bg-[#1a1d2e] border-white/[0.06] focus-within:border-indigo-500/30 focus-within:shadow-indigo-500/5"
          }`}
        >
          <div className="flex items-end gap-1 p-1.5 pl-4">
            {/* Modality Toggle */}
            <button
              onClick={onToggleModality}
              className={`p-2 rounded-full transition-all duration-200 flex-shrink-0 mb-0.5 ${
                modality === "voice"
                  ? "bg-rose-500/15 text-rose-400"
                  : "text-slate-600 hover:text-slate-400 hover:bg-white/[0.05]"
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
                isListening ? "Listening..." : "Ask me to plan your trip..."
              }
              disabled={disabled || isListening}
              rows={1}
              className="flex-1 bg-transparent py-2.5 px-2 text-[15px] text-white placeholder-slate-600 resize-none focus:outline-none disabled:opacity-40 leading-relaxed"
            />

            {/* Mic Button (Speech-to-Text) */}
            {onStartListening && (
              <button
                onClick={handleMicClick}
                disabled={disabled}
                className={`p-2.5 rounded-full transition-all duration-200 flex-shrink-0 mb-0.5 ${
                  isListening
                    ? "bg-rose-500 text-white animate-pulse shadow-lg shadow-rose-500/30"
                    : "text-slate-600 hover:text-slate-400 hover:bg-white/[0.05]"
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
              className={`p-2.5 rounded-full transition-all duration-200 flex-shrink-0 mb-0.5 ${
                message.trim() && !disabled
                  ? "bg-indigo-500 text-white hover:bg-indigo-400 shadow-lg shadow-indigo-500/25"
                  : "bg-white/[0.05] text-slate-700 cursor-not-allowed"
              }`}
            >
              <ArrowUp className="w-[18px] h-[18px]" strokeWidth={2.5} />
            </button>
          </div>
        </div>

        <p className="text-center text-[11px] text-slate-700 mt-2.5">
          AI Travel Planner may produce inaccurate information. Verify details
          before booking.
        </p>
      </div>
    </div>
  );
}
