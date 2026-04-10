import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  experimental: {
    serverActions: {
      bodySizeLimit: '5mb', // o '10mb', '20mb', etc.
    },
  },
};

export default nextConfig;
