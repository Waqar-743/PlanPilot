import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        cream: {
          50: "#faf8f5",
          100: "#f5f0ea",
          200: "#ebe6e0",
          300: "#e0dbd5",
          400: "#d5d0ca",
        },
        ink: {
          DEFAULT: "#1a1a1a",
          light: "#2a2a2a",
          muted: "#5a5550",
          faint: "#8a8580",
        },
        accent: {
          DEFAULT: "#c44b1a",
          light: "#d4622f",
          dark: "#a33d14",
          bg: "rgba(196, 75, 26, 0.08)",
        },
      },
      fontFamily: {
        display: ["var(--font-display)", "var(--font-body)", "sans-serif"],
        body: ["var(--font-body)", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
