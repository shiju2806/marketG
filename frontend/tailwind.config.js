/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#EAEEF6",
        "ink-soft": "#A6B0C2",
        "ink-faint": "#6B7688",
        surface: "#141922",
        "surface-2": "#1B222D",
        bg: "#0C0F14",
        line: "#232B38",
        accent: "#5B8CFF",
        good: "#34C77B",
        warn: "#E5A93A",
        crit: "#F0605F",
      },
      fontFamily: {
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
    },
  },
  plugins: [],
};
