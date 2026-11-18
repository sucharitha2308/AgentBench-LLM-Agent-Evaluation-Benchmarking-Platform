/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "#0B0F17",
        surface: "#111827",
        surfaceHover: "#1E293B",
        border: "#1F2937",
        primary: {
          DEFAULT: "#6366F1",
          hover: "#4F46E5",
          foreground: "#FFFFFF",
        },
        cyanAccent: "#06B6D4",
        violetAccent: "#8B5CF6",
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "Consolas", "monospace"],
      }
    },
  },
  plugins: [],
}
