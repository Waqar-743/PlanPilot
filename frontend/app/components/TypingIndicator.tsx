"use client";

import { Sparkles } from "lucide-react";

export default function TypingIndicator() {
  return (
    <div className="flex gap-3 animate-fade-in-up">
      <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-1 bg-accent">
        <Sparkles className="w-3.5 h-3.5 text-white" />
      </div>
      <div className="pt-2.5">
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-accent/60 typing-dot" />
          <div className="w-2 h-2 rounded-full bg-accent/70 typing-dot" />
          <div className="w-2 h-2 rounded-full bg-accent/80 typing-dot" />
        </div>
      </div>
    </div>
  );
}
