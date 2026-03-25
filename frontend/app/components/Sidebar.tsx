"use client";

import {
  PlaneTakeoff,
  Plus,
  MessageSquare,
  Globe2,
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
    <aside className="w-[280px] h-screen flex flex-col glass-strong">
      {/* Brand */}
      <div className="p-5 pb-4">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-500 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <PlaneTakeoff className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-[15px] text-white tracking-tight">
              TravelAI
            </h1>
            <p className="text-[10px] text-slate-500 font-medium tracking-wide uppercase">
              Intelligent Planning
            </p>
          </div>
        </div>

        {/* New Chat */}
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-[13px] font-semibold transition-all duration-200 shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/30 hover:-translate-y-[1px] active:translate-y-0"
        >
          <Plus className="w-4 h-4" />
          New Trip Plan
        </button>
      </div>

      {/* Divider */}
      <div className="mx-5 h-px bg-gradient-to-r from-transparent via-slate-700/50 to-transparent" />

      {/* Conversations */}
      <div className="flex-1 overflow-y-auto px-3 pt-3">
        <p className="text-[10px] uppercase tracking-[0.15em] text-slate-600 font-semibold px-2 mb-2">
          Recent Plans
        </p>
        {conversations.length === 0 ? (
          <div className="px-3 py-8 text-center">
            <Globe2 className="w-8 h-8 text-slate-700 mx-auto mb-2" />
            <p className="text-[11px] text-slate-600">
              No trips planned yet
            </p>
            <p className="text-[10px] text-slate-700 mt-1">
              Start by telling me where you want to go
            </p>
          </div>
        ) : (
          <div className="space-y-0.5">
            {conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => onSelectConversation(conv.id)}
                className={`w-full text-left px-3 py-2.5 rounded-lg flex items-start gap-2.5 transition-all duration-150 group ${
                  activeConversation === conv.id
                    ? "bg-indigo-500/10 border border-indigo-500/20 text-white"
                    : "text-slate-400 hover:bg-white/[0.03] hover:text-slate-300 border border-transparent"
                }`}
              >
                <MessageSquare
                  className={`w-3.5 h-3.5 mt-0.5 flex-shrink-0 transition-colors ${
                    activeConversation === conv.id
                      ? "text-indigo-400"
                      : "text-slate-600 group-hover:text-slate-500"
                  }`}
                />
                <div className="overflow-hidden flex-1 min-w-0">
                  <p className="text-[12px] truncate leading-tight">
                    {conv.preview}
                  </p>
                  <p className="text-[10px] text-slate-600 mt-0.5">
                    {conv.date}
                  </p>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-white/[0.04]">
        <div className="flex items-center gap-2 text-slate-600">
          <Zap className="w-3 h-3 text-indigo-500" />
          <span className="text-[10px] font-medium">Powered by Gemini 2.0</span>
        </div>
      </div>
    </aside>
  );
}
