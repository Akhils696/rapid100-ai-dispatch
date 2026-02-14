/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Emergency/dispatch colors
        'emergency-red': '#DC2626',
        'emergency-orange': '#EA580C',
        'emergency-yellow': '#CA8A04',
        'emergency-green': '#16A34A',
        'dispatch-dark': '#1F2937',
        'dispatch-darker': '#111827',
        'dispatch-gray': '#374151',
      },
      fontFamily: {
        'sans': ['Inter', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}