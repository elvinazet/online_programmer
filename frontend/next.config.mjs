/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Линтинг гоняем отдельно (npm run lint), чтобы стиль-правила не роняли сборку.
  eslint: { ignoreDuringBuilds: true },
};

export default nextConfig;
