/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'glacier-white': '#F8FAFC',
        'justice-blue': '#1E3A8A',
        'geek-green': '#10B981',
      }
    },
  },
  plugins: [],
}
