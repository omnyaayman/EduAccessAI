/** @type {import('next').NextConfig} */
const isStaticDemo =
  process.env.NEXT_STATIC_EXPORT === "1";

const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ["tailwind-merge", "clsx", "lucide-react"],
  ...(isStaticDemo
    ? {
        output: "export",
        images: { unoptimized: true },
        basePath: process.env.NEXT_PUBLIC_BASE_PATH || undefined,
        assetPrefix:
          process.env.NEXT_PUBLIC_ASSET_PREFIX || process.env.NEXT_PUBLIC_BASE_PATH || undefined,
        trailingSlash: true,
      }
    : {
        output: "standalone",
      }),
};

export default nextConfig;