/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic':
          'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
      },
      keyframes: {
        'slide-up': {
          '0%': {
            transform: 'translateY(20px)',
            opacity: '0'
          },
          '100%': {
            transform: 'translateY(0)',
            opacity: '1'
          }
        },
        'pulse-scale': {
          '0%, 100%': {
            transform: 'scale(1)',
            opacity: '0.7'
          },
          '50%': {
            transform: 'scale(1.5)',
            opacity: '1'
          }
        }
      },
      animation: {
        'slide-up': 'slide-up 0.3s ease-out',
        'pulse-scale': 'pulse-scale 1s ease-in-out infinite'
      }
    },
  },
  plugins: [],
}