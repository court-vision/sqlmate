/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    // Get the API URL from environment variable, with a fallback for local development
    const API_URL = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_API_URL;

    return [
      {
        source: "/auth/:path*",
        destination: `${API_URL}/auth/:path*`,
      },
      {
        source: "/query",
        destination: `${API_URL}/query`,
      },
      {
        source: "/users/:path*",
        destination: `${API_URL}/users/:path*`,
      },
      {
        source: "/schema",
        destination: `${API_URL}/schema`,
      },
    ];
  },
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "Content-Security-Policy",
            value: "frame-ancestors 'self' https://courtvision.dev",
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
