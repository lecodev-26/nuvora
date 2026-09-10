/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        navy: '#0A0A14',
        'deep-blue': '#0D1B2A',
        cyan: {
          400: '#00C6FF',
          500: '#00B4E6',
        },
        violet: {
          400: '#7B5CFF',
          500: '#6A4EE6',
        },
        magenta: {
          400: '#FF4ECD',
          500: '#E63DB8',
        },
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
      backgroundImage: {
        'gradient-primary': 'linear-gradient(135deg, #00C6FF, #7B5CFF, #FF4ECD)',
        'gradient-hero': 'linear-gradient(135deg, rgba(0,198,255,0.15), rgba(123,92,255,0.15), rgba(255,78,205,0.15))',
      },
      boxShadow: {
        glow: '0 0 40px rgba(123, 92, 255, 0.3)',
        'glow-lg': '0 0 60px rgba(123, 92, 255, 0.5)',
        card: '0 8px 32px rgba(0,0,0,0.12)',
        'card-hover': '0 12px 48px rgba(123, 92, 255, 0.2)',
      },
      borderRadius: {
        card: '16px',
        button: '12px',
      },
      animation: {
        'fade-in-up': 'fadeInUp 0.6s ease forwards',
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
      },
      keyframes: {
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseGlow: {
          '0%, 100%': { boxShadow: '0 0 20px rgba(123,92,255,0.3)' },
          '50%': { boxShadow: '0 0 40px rgba(123,92,255,0.6)' },
        },
      },
    },
  },
  plugins: [],
};
