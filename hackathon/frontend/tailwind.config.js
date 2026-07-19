/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./src/**/*.{js,ts,jsx,tsx,mdx}",
        "./app/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            colors: {
                darkBg: "#0a0f1d",
                darkCard: "rgba(20, 26, 45, 0.6)",
                cardBorder: "rgba(255, 255, 255, 0.08)",
                accentCyan: "#06b6d4",
                accentIndigo: "#6366f1",
                accentRose: "#f43f5e",
                accentAmber: "#f59e0b",
                accentEmerald: "#10b981",
                mutedGray: "#64748b",
            },
            fontFamily: {
                mono: ["Courier New", "Courier", "monospace"],
            },
            backdropBlur: {
                xs: "2px",
            }
        },
    },
    plugins: [],
}
