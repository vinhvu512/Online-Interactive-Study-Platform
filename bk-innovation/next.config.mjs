/** @type {import('next').NextConfig} */
const nextConfig = {
    images: {
        remotePatterns: [
            {
                hostname: "utfs.io",
            },
        ],
        loader: 'custom',
        loaderFile: './utils/imageLoader.ts',
    }
};

export default nextConfig;
