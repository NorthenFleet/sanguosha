/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        sanguo: {
          red: '#c53030',
          gold: '#d97706',
          blue: '#1e40af',
          green: '#065f46'
        }
      },
      fontFamily: {
        'chinese': ['SimSun', 'STKaiti', 'KaiTi', 'serif']
      }
    },
  },
  plugins: [],
}