import type { NextConfig } from "next";

const APP_ORIGIN = process.env.NEXT_PUBLIC_APP_URL || "https://codemaster-oj.vercel.app";

const securityHeaders = [
  // ─── Strict-Transport-Security (HSTS) ──────────────────────────────────────
  // Forces HTTPS for 1 year; applies to subdomains and preloads.
  {
    key: "Strict-Transport-Security",
    value: "max-age=31536000; includeSubDomains; preload",
  },
  // ─── Content-Security-Policy ───────────────────────────────────────────────
  // Restricts which sources can load JS, CSS, fonts, images, connections, etc.
  {
    key: "Content-Security-Policy",
    value: [
      "default-src 'self'",
      // Scripts: self + Next.js inline/eval (required for HMR & React hydration)
      "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://apis.google.com",
      // Styles: self + Bootstrap CDN + Font Awesome CDN + inline (Next.js injects these)
      "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com",
      // Fonts: Google Fonts, Font Awesome, self
      "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com",
      // Images: self + Google user-content (avatars) + GitHub avatars + data URIs
      "img-src 'self' data: https://lh3.googleusercontent.com https://avatars.githubusercontent.com",
      // Fetch / XHR: self + Piston API (code execution)
      "connect-src 'self' https://emkc.org",
      // Prevent embedding in iframes (anti-clickjacking)
      "frame-ancestors 'none'",
      // No plugins
      "object-src 'none'",
      // Upgrade any accidental http:// requests to https://
      "upgrade-insecure-requests",
    ].join("; "),
  },
  // ─── X-Frame-Options (legacy anti-clickjacking for older browsers) ──────────
  {
    key: "X-Frame-Options",
    value: "DENY",
  },
  // ─── X-Content-Type-Options ────────────────────────────────────────────────
  // Prevents browsers from MIME-sniffing a response away from the declared type.
  {
    key: "X-Content-Type-Options",
    value: "nosniff",
  },
  // ─── Referrer-Policy ───────────────────────────────────────────────────────
  {
    key: "Referrer-Policy",
    value: "strict-origin-when-cross-origin",
  },
  // ─── Permissions-Policy ────────────────────────────────────────────────────
  // Restricts access to powerful browser features.
  {
    key: "Permissions-Policy",
    value: "camera=(), microphone=(), geolocation=(), interest-cohort=()",
  },
];

const nextConfig: NextConfig = {
  output: "standalone",
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "lh3.googleusercontent.com" },
      { protocol: "https", hostname: "avatars.githubusercontent.com" },
    ],
  },
  serverExternalPackages: ["@prisma/client"],

  async headers() {
    return [
      // Apply security headers to all routes
      {
        source: "/(.*)",
        headers: securityHeaders,
      },
      // ─── X-Content-Type-Options for static assets ────────────────────────
      // Next.js's /(.*) glob does NOT match /_next/static/ paths because those
      // are served by Vercel's edge CDN and bypass the custom headers() config.
      // We explicitly target them here so font/JS/CSS files get nosniff.
      // (ZAP finding: X-Content-Type-Options Header Missing on woff2/static files)
      {
        source: "/_next/static/(.*)",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Cache-Control", value: "public, max-age=31536000, immutable" },
        ],
      },
      {
        source: "/_next/image/(.*)",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
        ],
      },
      // ─── CORS: restrict API routes to this app's origin only ─────────────
      // Removes the wildcard Access-Control-Allow-Origin that caused the ZAP
      // Cross-Domain Misconfiguration finding.
      {
        source: "/api/(.*)",
        headers: [
          {
            key: "Access-Control-Allow-Origin",
            value: APP_ORIGIN,
          },
          {
            key: "Access-Control-Allow-Methods",
            value: "GET, POST, PUT, DELETE, OPTIONS",
          },
          {
            key: "Access-Control-Allow-Headers",
            value: "Content-Type, Authorization",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
