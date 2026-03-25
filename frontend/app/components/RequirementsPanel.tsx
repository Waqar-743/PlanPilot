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
      color: "text-rose-400",
    },
    {
      icon: <Navigation className="w-3.5 h-3.5" />,
      label: "Origin",
      value: requirements.origin,
      color: "text-blue-400",
    },
    {
      icon: <Calendar className="w-3.5 h-3.5" />,
      label: "Dates",
      value:
        requirements.start_date && requirements.end_date
          ? `${requirements.start_date} to ${requirements.end_date}`
          : null,
      color: "text-amber-400",
    },
    {
      icon: <Wallet className="w-3.5 h-3.5" />,
      label: "Budget",
      value: requirements.budget_level
        ? requirements.budget_level.charAt(0).toUpperCase() +
          requirements.budget_level.slice(1)
        : null,
      color: "text-emerald-400",
    },
  ];

  const allComplete = requirements.has_all_requirements;

  return (
    <div className="glass rounded-xl p-4 mb-4 animate-fade-in-up">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-[11px] font-bold text-slate-400 uppercase tracking-[0.15em]">
          Trip Requirements
        </h3>
        {allComplete ? (
          <span className="flex items-center gap-1 text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
            <CheckCircle2 className="w-3 h-3" />
            Ready
          </span>
        ) : (
          <span className="flex items-center gap-1 text-[10px] font-semibold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/20">
            <Loader2 className="w-3 h-3 animate-spin" />
            Gathering
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 gap-2.5">
        {items.map((item, i) => (
          <div
            key={i}
            className={`flex items-center gap-2.5 px-3 py-2 rounded-lg transition-colors ${
              item.value
                ? "bg-white/[0.03] border border-white/[0.06]"
                : "bg-transparent border border-dashed border-white/[0.06]"
            }`}
          >
            <span className={item.value ? item.color : "text-slate-700"}>
              {item.value ? (
                <CheckCircle2 className="w-3.5 h-3.5" />
              ) : (
                <Circle className="w-3.5 h-3.5" />
              )}
            </span>
            <span className={`${item.color} opacity-60`}>{item.icon}</span>
            <div className="min-w-0 flex-1">
              <p className="text-[9px] text-slate-600 font-semibold uppercase tracking-wider">
                {item.label}
              </p>
              <p
                className={`text-[12px] truncate ${
                  item.value ? "text-slate-200 font-medium" : "text-slate-700"
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
