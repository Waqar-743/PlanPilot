"use client";

import {
  Mountain,
  Plus,
  MessageSquare,
  MapPinned,
  Zap,
} from "lucide-react";

interface SidebarProps {
  onNewChat: () => void;
  conversations: Array<{ id: string; preview: string; date: string }>;
  activeConversation: string | null;
  onSelectConversation: (id: string) => void;
}

export default function Sidebar({
  onNewChat,
  conversations,
  activeConversation,
  onSelectConversation,
}: SidebarProps) {
  return (
    <aside className="w-[280px] h-screen flex flex-col bg-ink">
      {/* Brand */}
      <div className="p-5 pb-4">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-10 h-10 rounded-xl bg-accent flex items-center justify-center">
            <Mountain className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-display font-bold text-[15px] text-white uppercase tracking-wide">
              PlanPilot
            </h1>
            <p className="text-[10px] text-white/40 font-medium tracking-widest uppercase">
              Travel Concierge
            </p>
          </div>
        </div>

        {/* New Chat */}
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-white text-[13px] font-bold uppercase tracking-wider bg-accent hover:bg-accent-light transition-all duration-200"
        >
          <Plus className="w-4 h-4" />
          New Trip Plan
        </button>
      </div>

      {/* Divider */}
      <div className="mx-5 h-px bg-white/[0.08]" />

      {/* Conversations */}
      <div className="flex-1 overflow-y-auto px-3 pt-3">
        <p className="text-[10px] uppercase tracking-[0.2em] text-white/30 font-bold px-2 mb-2">
          Recent Plans
        </p>
        {conversations.length === 0 ? (
          <div className="px-3 py-8 text-center">
            <MapPinned className="w-8 h-8 text-white/15 mx-auto mb-2" />
            <p className="text-[11px] text-white/30">
              No trips planned yet
            </p>
            <p className="text-[10px] text-white/20 mt-1">
              Explore Pakistan -- from Hunza to Gwadar
            </p>
          </div>
        ) : (
          <div className="space-y-0.5">
            {conversations.map((conv, index) => (
              <button
                key={conv.id || `conversation-${index}`}
                onClick={() => onSelectConversation(conv.id)}
                className={`w-full text-left px-3 py-2.5 rounded-lg flex items-start gap-2.5 transition-all duration-150 group ${
                  activeConversation === conv.id
                    ? "bg-white/[0.08] text-white"
                    : "text-white/50 hover:bg-white/[0.04] hover:text-white/70"
                }`}
              >
                <MessageSquare
                  className={`w-3.5 h-3.5 mt-0.5 flex-shrink-0 transition-colors ${
                    activeConversation === conv.id
                      ? "text-accent"
                      : "text-white/25 group-hover:text-white/40"
                  }`}
                />
                <div className="overflow-hidden flex-1 min-w-0">
                  <p className="text-[12px] truncate leading-tight">
                    {conv.preview}
                  </p>
                  <p className="text-[10px] text-white/25 mt-0.5">
                    {conv.date}
                  </p>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-white/[0.06]">
        <div className="flex items-center gap-2 text-white/30">
          <Zap className="w-3 h-3 text-accent" />
          <span className="text-[10px] font-semibold uppercase tracking-wider">
            Powered by Gemini 2.0
          </span>
        </div>
      </div>
    </aside>
  );
}
