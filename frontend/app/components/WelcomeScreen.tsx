"use client";

import {
  Bus,
  CloudSun,
  Hotel,
  MapPinned,
  ArrowRight,
  Shield,
  Mountain,
} from "lucide-react";

interface WelcomeScreenProps {
  onSuggestionClick: (suggestion: string) => void;
}

const suggestions = [
  {
    icon: <Mountain className="w-5 h-5" />,
    num: "01",
    title: "Northern Adventure",
    text: "Plan a 5-day trip to Hunza Valley from Islamabad on a medium budget",
  },
  {
    icon: <MapPinned className="w-5 h-5" />,
    num: "02",
    title: "Historic Lahore",
    text: "I want to explore Lahore for a weekend with street food and Mughal heritage",
  },
  {
    icon: <Hotel className="w-5 h-5" />,
    num: "03",
    title: "Budget Swat Trip",
    text: "Find me a cheap 3-day trip to Swat Valley from Peshawar",
  },
  {
    icon: <CloudSun className="w-5 h-5" />,
    num: "04",
    title: "Coastal Gwadar",
    text: "Plan a 4-day trip to Gwadar and the Makran Coast, high budget",
  },
];

const features = [
  { icon: <CloudSun className="w-4 h-4" />, text: "Real-time Weather" },
  { icon: <Bus className="w-4 h-4" />, text: "Road Transport" },
  { icon: <Hotel className="w-4 h-4" />, text: "Hotel Search" },
  { icon: <Shield className="w-4 h-4" />, text: "Smart Guardrails" },
];

export default function WelcomeScreen({
  onSuggestionClick,
}: WelcomeScreenProps) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center px-6 py-16">
      {/* Hero */}
      <div className="text-center mb-16 animate-fade-in-up">
        <h1 className="font-display text-6xl md:text-7xl font-bold uppercase leading-[0.95] tracking-tight text-ink mb-6">
          Travel Planning
          <br />
          <span className="text-accent">Made Simple</span>
        </h1>
        <p className="text-ink-muted text-base max-w-lg mx-auto leading-relaxed">
          Your AI-powered Pakistan travel concierge. Plan trips with real-time
          weather, motorway routes, bus services, hotels, and personalized
          itineraries.
        </p>
      </div>

      {/* Numbered Suggestion Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-0 max-w-4xl w-full mb-14 border border-black/[0.06] rounded-xl overflow-hidden">
        {suggestions.map((s, i) => (
          <button
            key={i}
            onClick={() => onSuggestionClick(s.text)}
            className={`text-left p-6 bg-cream-200/60 hover:bg-ink transition-all duration-200 group animate-fade-in-up ${
              i < suggestions.length - 1
                ? "border-r border-black/[0.06]"
                : ""
            }`}
            style={{ animationDelay: `${i * 80}ms` }}
          >
            <span className="font-display text-3xl font-bold text-ink/15 group-hover:text-accent block mb-4 transition-colors">
              {s.num}
            </span>
            <h3 className="font-display text-sm font-bold uppercase tracking-wide text-ink mb-2 group-hover:text-white transition-colors">
              {s.title}
            </h3>
            <p className="text-xs text-ink-muted leading-relaxed group-hover:text-white/80 transition-colors">
              {s.text}
            </p>
            <ArrowRight className="w-4 h-4 text-ink/20 group-hover:text-accent mt-4 transition-all group-hover:translate-x-1" />
          </button>
        ))}
      </div>

      {/* Feature Pills */}
      <div className="flex flex-wrap items-center justify-center gap-3 animate-fade-in">
        {features.map((f, i) => (
          <div
            key={i}
            className="flex items-center gap-2 px-4 py-2 rounded-full border border-black/[0.08] text-ink-muted bg-cream-50"
          >
            <span className="text-accent">{f.icon}</span>
            <span className="text-xs font-semibold uppercase tracking-wider">
              {f.text}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
