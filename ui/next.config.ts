import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/proxy/:path*',
        destination: 'https://api.thesentinel.site/v1/:path*',
      },
    ];
  },
};

export default nextConfig;
