import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // ── 1421 Foundation palette ──────────────────────────────────
        // "gold" references in components → now foundation red
        gold: {
          DEFAULT: "#c0272d",   // 1421 Foundation red
          light:   "#e03038",   // lighter red for hovers
          dark:    "#8f1c21",   // darker red for pressed states
        },
        // "navy" references in components → now white/off-white tones
        navy: {
          DEFAULT: "#f5f5f5",   // near-white card background
          light:   "#ffffff",   // pure white
          dark:    "#ebebeb",   // slightly darker white for page bg
        },
        // Extra semantic colours
        foundation: {
          red:        "#c0272d",
          "red-light": "#e03038",
          "red-dark":  "#8f1c21",
          white:      "#ffffff",
          offwhite:   "#f5f5f5",
          muted:      "#f0f0f0",
        },
      },
      fontFamily: {
        display: ["Playfair Display", "serif"],
        sans:    ["Inter", "sans-serif"],
      },
    },
  },
  plugins: [],
} satisfies Config;