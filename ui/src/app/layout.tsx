import type { Metadata } from "next";
import { Inter, Outfit } from "next/font/google";
import { Toaster } from "sonner";
import "./globals.css";
import { ClientLayout } from "@/components/layout/ClientLayout";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const outfit = Outfit({
  variable: "--font-outfit",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL('https://dashboard.thesentinel.site'),
  title: {
    default: "Sentinel - AI-Powered Email Marketing Platform",
    template: "%s | Sentinel"
  },
  description: "Transform your email marketing with Sentinel's AI-powered platform. Create intelligent campaigns, segment audiences, track performance, and boost engagement with advanced analytics.",
  keywords: ["email marketing", "marketing automation", "AI email campaigns", "email analytics", "audience segmentation", "marketing platform", "email tracking", "A/B testing"],
  authors: [{ name: "Sentinel" }],
  creator: "Sentinel",
  publisher: "Sentinel",
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://dashboard.thesentinel.site",
    siteName: "Sentinel",
    title: "Sentinel - AI-Powered Email Marketing Platform",
    description: "Transform your email marketing with Sentinel's AI-powered platform. Create intelligent campaigns, segment audiences, and boost engagement.",
    images: [
      {
        url: "/images/og-image.png",
        width: 1200,
        height: 630,
        alt: "Sentinel Email Marketing Platform"
      }
    ]
  },
  twitter: {
    card: "summary_large_image",
    title: "Sentinel - AI-Powered Email Marketing Platform",
    description: "Transform your email marketing with AI-powered campaigns, segmentation, and analytics.",
    images: ["/images/twitter-image.png"],
    creator: "@sentinel"
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  // Note: Using DNS verification in Google Search Console instead of HTML tag
  // This is more reliable and doesn't require code changes
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="canonical" href="https://dashboard.thesentinel.site" />
      </head>
      <body
        className={`${inter.variable} ${outfit.variable} antialiased bg-background text-foreground`}
      >
        <ClientLayout>
          {children}
        </ClientLayout>
        <Toaster position="top-right" theme="dark" />
      </body>
    </html>
  );
}
