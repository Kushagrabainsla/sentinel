import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone', // Required for Amplify deployment
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
