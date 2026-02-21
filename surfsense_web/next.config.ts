import { createMDX } from "fumadocs-mdx/next";
import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

// Create the next-intl plugin
const withNextIntl = createNextIntlPlugin("./i18n/request.ts");

const nextConfig: NextConfig = {
	output: "standalone",
	// Disable StrictMode for BlockNote compatibility with React 19/Next 15
	reactStrictMode: false,
	typescript: {
		ignoreBuildErrors: true,
	},
	images: {
		remotePatterns: [
			{
				protocol: "https",
				hostname: "**",
			},
		],
	},
	// Mark BlockNote server packages as external
	serverExternalPackages: ["@blocknote/server-util"],

	// Configure webpack to handle blocknote packages
	webpack: (config, { isServer }) => {
		if (isServer) {
			// Don't bundle these packages on the server
			config.externals = [...(config.externals || []), "@blocknote/server-util"];
		}
		return config;
	},

	// PostHog reverse proxy configuration
	// This helps bypass ad blockers by routing requests through your domain
	async rewrites() {
		// When exposing the frontend via a tunnel/reverse proxy, remote browsers cannot
		// access backend/electric at their own localhost. Proxy those requests through
		// Next.js so everything stays same-origin.
		const backend = process.env.INTERNAL_FASTAPI_BACKEND_URL || "http://backend:8000";
		const electric = process.env.INTERNAL_ELECTRIC_URL || "http://electric:3000";

		return [
			// Backend (FastAPI)
			{ source: "/auth/:path*", destination: `${backend}/auth/:path*` },
			{ source: "/users/:path*", destination: `${backend}/users/:path*` },
			{ source: "/api/:path*", destination: `${backend}/api/:path*` },
			{ source: "/verify-token", destination: `${backend}/verify-token` },
			// Avoid clobbering the frontend docs route at /docs
			{ source: "/openapi.json", destination: `${backend}/openapi.json` },
			{ source: "/redoc", destination: `${backend}/redoc` },

			// ElectricSQL
			{ source: "/electric/:path*", destination: `${electric}/:path*` },

			// PostHog reverse proxy
			{
				source: "/ingest/static/:path*",
				destination: "https://us-assets.i.posthog.com/static/:path*",
			},
			{
				source: "/ingest/:path*",
				destination: "https://us.i.posthog.com/:path*",
			},
			{
				source: "/ingest/decide",
				destination: "https://us.i.posthog.com/decide",
			},
		];
	},
	// Required for PostHog reverse proxy to work correctly
	skipTrailingSlashRedirect: true,
};

// Wrap the config with MDX and next-intl plugins
const withMDX = createMDX({});

export default withNextIntl(withMDX(nextConfig));
