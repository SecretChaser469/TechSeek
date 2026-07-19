/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true,
    output: 'standalone',
    // Optional rewrites if we want to forward uploads
    async rewrites() {
        return [
            {
                source: '/uploads/:path*',
                destination: 'http://backend:8000/uploads/:path*', // Forward files to backend volume service
            },
        ]
    },
}

module.exports = nextConfig
