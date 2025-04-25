import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  transpilePackages: ['@chakra-ui/react', '@chakra-ui/next-js'],
};

export default nextConfig;
