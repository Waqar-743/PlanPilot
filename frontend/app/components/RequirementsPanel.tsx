"use client";

import {
  MapPin,
  Calendar,
  Wallet,
  Navigation,
  CheckCircle2,
  Circle,
  Loader2,
} from "lucide-react";

interface Requirements {
  destination?: string | null;
  origin?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  budget_level?: string | null;
  has_all_requirements?: boolean;
}

export default function RequirementsPanel({
  requirements,
}: {
  requirements: Requirements | null;
}) {
  if (!requirements) return null;

  const items = [
    {
      icon: <MapPin className="w-3.5 h-3.5" />,
      label: "Destination",
      value: requirements.destination,
      color: "text-accent",
    },
    {
      icon: <Navigation className="w-3.5 h-3.5" />,
      label: "Origin",
      value: requirements.origin,
      color: "text-ink",
    },
    {
      icon: <Calendar className="w-3.5 h-3.5" />,
      label: "Dates",
      value:
        requirements.start_date && requirements.end_date
          ? `${requirements.start_date} to ${requirements.end_date}`
          : null,
      color: "text-ink-muted",
    },
    {
      icon: <Wallet className="w-3.5 h-3.5" />,
      label: "Budget",
      value: requirements.budget_level
        ? requirements.budget_level.charAt(0).toUpperCase() +
          requirements.budget_level.slice(1)
        : null,
      color: "text-ink-muted",
    },
  ];

  const allComplete = requirements.has_all_requirements;

  return (
    <div className="bg-white border border-black/[0.06] rounded-xl p-4 mb-4 animate-fade-in-up">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-display text-[11px] font-bold text-ink-muted uppercase tracking-[0.2em]">
          Trip Requirements
        </h3>
        {allComplete ? (
          <span className="flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-accent bg-accent/10 px-2.5 py-1 rounded-full">
            <CheckCircle2 className="w-3 h-3" />
            Ready
          </span>
        ) : (
          <span className="flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-ink-muted bg-black/[0.04] px-2.5 py-1 rounded-full">
            <Loader2 className="w-3 h-3 animate-spin" />
            Gathering
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 gap-2.5">
        {items.map((item, i) => (
          <div
            key={i}
            className={`flex items-center gap-2.5 px-3 py-2.5 rounded-lg transition-colors ${
              item.value
                ? "bg-cream-100 border border-black/[0.04]"
                : "bg-transparent border border-dashed border-black/[0.08]"
            }`}
          >
            <span className={item.value ? "text-accent" : "text-ink-faint/40"}>
              {item.value ? (
                <CheckCircle2 className="w-3.5 h-3.5" />
              ) : (
                <Circle className="w-3.5 h-3.5" />
              )}
            </span>
            <span className={`${item.color} opacity-50`}>{item.icon}</span>
            <div className="min-w-0 flex-1">
              <p className="text-[9px] text-ink-faint font-bold uppercase tracking-widest">
                {item.label}
              </p>
              <p
                className={`text-[12px] truncate ${
                  item.value ? "text-ink font-medium" : "text-ink-faint/40"
                }`}
              >
                {item.value || "Pending..."}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
