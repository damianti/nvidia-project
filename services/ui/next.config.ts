import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  eslint: {
    // Ignore test directories during build
    dirs: ['app', 'pages', 'components', 'lib', 'src'],
  },
};

export default nextConfig;
