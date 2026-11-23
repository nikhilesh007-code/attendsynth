import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#030712",
        surface: "#090e17",
        "surface-elevated": "#0f172a",
        "surface-card": "#090e17",
        border: "#1e293b",
        "border-subtle": "#162032",
        primary: {
          DEFAULT: "#10b981",
          hover: "#059669",
          light: "#34d399",
        },
        accent: {
          blue: "#38bdf8",
          emerald: "#10b981",
          amber: "#f59e0b",
          rose: "#ef4444",
          violet: "#8b5cf6",
        },
      },
    },
  },
  plugins: [],
};
export default config;
