// /home/user/advocatus-frontend/tailwind.config.js
// DEFINITIVE VERSION 4.0: KONTABILISTI AI REBRAND
// UPDATED: Color palette changed to teal/emerald with gold accents for accounting theme.
// FIX: Added 'pulse-slow' and 'float' to support the new MainLayout ambient background.

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  safelist: [
    'text-success-start',
  ],
  theme: {
    extend: {
      colors: {
        // New accounting-focused palette
        'primary-start': '#0d9488',   // teal-600
        'primary-end': '#10b981',     // emerald-500
        'secondary-start': '#f59e0b', // amber-500
        'secondary-end': '#d97706',   // amber-600
        'accent-start': '#f97316',    // orange-500
        'accent-end': '#fbbf24',      // amber-300
        'success-start': '#10b981',   // emerald-500
        'success-end': '#22c55e',     // green-500
        'text-primary': '#f9fafb',    // unchanged
        'text-secondary': '#d1d5db',  // unchanged
        'glass-edge': 'rgba(255, 255, 255, 0.1)', // unchanged
        'background-dark': '#030712', // unchanged
        'background-light': '#1f2937', // unchanged
      },
      // --- ANIMATION DEFINITIONS (unchanged) ---
      animation: {
        'gradient-shift': 'gradient-shift 15s ease infinite',
        'particle-float': 'particle-float 60s linear infinite',
        'pulse-slow': 'pulse 8s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        'gradient-shift': {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        'particle-float': {
          '0%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-20px)' },
          '100%': { transform: 'translateY(0px)' },
        }
      },
    },
  },
  plugins: [],
}