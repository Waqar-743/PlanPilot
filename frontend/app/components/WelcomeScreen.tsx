"use client";

import {
  PlaneTakeoff,
  CloudSun,
  Hotel,
  MapPinned,
  ArrowRight,
  Shield,
} from "lucide-react";

interface WelcomeScreenProps {
  onSuggestionClick: (suggestion: string) => void;
}

const suggestions = [
  {
    icon: <PlaneTakeoff className="w-6 h-6" />,
    title: "Weekend in Paris",
    text: "Plan a 3-day trip to Paris on a medium budget",
    gradient: "from-blue-500/20 to-indigo-500/20",
    iconColor: "text-blue-400",
    border: "hover:border-blue-500/30",
  },
  {
    icon: <MapPinned className="w-6 h-6" />,
    title: "Explore Tokyo",
    text: "I want to explore Tokyo for a week in April",
    gradient: "from-rose-500/20 to-pink-500/20",
    iconColor: "text-rose-400",
    border: "hover:border-rose-500/30",
  },
  {
    icon: <Hotel className="w-6 h-6" />,
    title: "Budget Bali",
    text: "Find me a cheap 5-day trip to Bali from Mumbai",
    gradient: "from-emerald-500/20 to-teal-500/20",
    iconColor: "text-emerald-400",
    border: "hover:border-emerald-500/30",
  },
  {
    icon: <CloudSun className="w-6 h-6" />,
    title: "Dubai Luxury",
    text: "Plan a family trip to Dubai for 4 days, high budget",
    gradient: "from-amber-500/20 to-orange-500/20",
    iconColor: "text-amber-400",
    border: "hover:border-amber-500/30",
  },
];

const features = [
  { icon: <CloudSun className="w-4 h-4" />, text: "Real-time Weather" },
  { icon: <PlaneTakeoff className="w-4 h-4" />, text: "Live Flights" },
  { icon: <Hotel className="w-4 h-4" />, text: "Hotel Search" },
  { icon: <Shield className="w-4 h-4" />, text: "Smart Guardrails" },
];

export default function WelcomeScreen({
  onSuggestionClick,
}: WelcomeScreenProps) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center px-6 py-12">
      {/* Hero Text */}
      <div className="text-center mb-14 animate-fade-in-up">
        <h1 className="text-5xl font-extrabold text-white mb-4 tracking-tight leading-tight">
          Where do you want to{" "}
          <span className="gradient-text">explore</span>?
        </h1>
        <p className="text-slate-400 text-lg max-w-xl mx-auto leading-relaxed">
          I plan your entire trip with real-time flights, hotels, weather
          forecasts, and personalized daily itineraries -- all in seconds.
        </p>
      </div>

      {/* Suggestion Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-3xl w-full mb-12">
        {suggestions.map((s, i) => (
          <button
            key={i}
            onClick={() => onSuggestionClick(s.text)}
            className={`text-left p-5 rounded-2xl bg-gradient-to-br ${s.gradient} border border-white/[0.06] ${s.border} transition-all duration-200 group hover:-translate-y-[2px] hover:shadow-lg animate-fade-in-up`}
            style={{ animationDelay: `${i * 80}ms` }}
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <span
                  className={`${s.iconColor} transition-transform duration-200 group-hover:scale-110`}
                >
                  {s.icon}
                </span>
                <span className="text-[15px] font-bold text-slate-200 tracking-tight">
                  {s.title}
                </span>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-600 group-hover:text-slate-400 transition-all group-hover:translate-x-0.5" />
            </div>
            <p className="text-[14px] text-slate-400 group-hover:text-slate-300 transition-colors leading-relaxed">
              {s.text}
            </p>
          </button>
        ))}
      </div>

      {/* Feature Pills */}
      <div className="flex flex-wrap items-center justify-center gap-3 animate-fade-in">
        {features.map((f, i) => (
          <div
            key={i}
            className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/[0.03] border border-white/[0.06] text-slate-500"
          >
            <span className="text-indigo-400">{f.icon}</span>
            <span className="text-[13px] font-medium">{f.text}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
