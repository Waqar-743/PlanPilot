"use client";

import { Sparkles } from "lucide-react";

export default function TypingIndicator() {
  return (
    <div className="flex gap-3 animate-fade-in-up">
      <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mt-1 bg-gradient-to-br from-indigo-500 to-violet-500 shadow-md shadow-indigo-500/20">
        <Sparkles className="w-3.5 h-3.5 text-white" />
      </div>
      <div className="pt-2.5">
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-indigo-400/80 typing-dot" />
          <div className="w-2 h-2 rounded-full bg-violet-400/80 typing-dot" />
          <div className="w-2 h-2 rounded-full bg-purple-400/80 typing-dot" />
        </div>
      </div>
    </div>
  );
}
