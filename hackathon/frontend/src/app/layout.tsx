import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
    title: 'TechSeek - Checked Achievement Graph',
    description: 'Verified academic accomplishment network and team collaborations',
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="en">
            <body className="antialiased text-white selection:bg-indigo-500 selection:text-white">
                {children}
            </body>
        </html>
    )
}
