module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      fontFamily: {
        'cinzel': ['Cinzel', 'serif'],
        'inter': ['Inter', 'sans-serif'],
      },
      colors: {
        'gold': '#d4af37',
        'dark-gold': '#b8860b',
        'navy': '#2c3e50',
        'light-navy': '#4a6491',
      },
      borderWidth: {
        '3': '3px',
      },
      animation: {
        'fadeIn': 'fadeIn 0.3s ease forwards',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        }
      }
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}