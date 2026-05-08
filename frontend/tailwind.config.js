/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        soc: {
          bg: '#0a0e1a',
          panel: '#11172a',
          panel2: '#161d33',
          border: '#1f2940',
          accent: '#22d3ee',
          accent2: '#a855f7',
          danger: '#ef4444',
          warn: '#f59e0b',
          ok: '#10b981',
          text: '#e6ecff',
          mute: '#7d8aaa',
        },
      },
      fontFamily: {
        display: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
        sans: ['"Inter"', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        glow: '0 0 0 1px rgba(34,211,238,0.25), 0 8px 24px -8px rgba(34,211,238,0.35)',
      },
    },
  },
  plugins: [],
}
