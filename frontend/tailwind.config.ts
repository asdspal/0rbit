import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0A0F2C",
        surface: "#111827",
        surfaceElevated: "#1E293B",
        "surface-elevated": "#1E293B",
        primary: "#7C3AED",
        "primary-hover": "#6D28D9",
        secondary: "#06B6D4",
        success: "#10B981",
        warning: "#F59E0B",
        error: "#EF4444",
        muted: "#94A3B8",
        body: "#E2E8F0",
        border: "#334155",
      },
      borderColor: {
        DEFAULT: "#334155",
      },
      boxShadow: {
        card: "0 4px 12px rgba(0, 0, 0, 0.25)",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "sans-serif"],
        mono: ["var(--font-jetbrains)", "monospace"],
      },
    },
  },
  plugins: [],
};
export default config;
