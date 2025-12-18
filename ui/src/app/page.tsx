'use client';

import Link from "next/link";
import { ArrowRight, Zap, Shield, Mail, CheckCircle2 } from "lucide-react";
import { useEffect, useRef } from "react";
import { Globe } from "@/components/ui/Globe";
import { PublicHeader } from "@/components/layout/PublicHeader";
import { PublicFooter } from "@/components/layout/PublicFooter";

export default function LandingPage() {
  // Structured Data for SEO
  const structuredData = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "Sentinel",
    "applicationCategory": "BusinessApplication",
    "operatingSystem": "Web",
    "offers": {
      "@type": "Offer",
      "price": "0",
      "priceCurrency": "USD"
    },
    "description": "AI-powered email marketing platform with advanced analytics, audience segmentation, and campaign management.",
    "aggregateRating": {
      "@type": "AggregateRating",
      "ratingValue": "4.8",
      "ratingCount": "127"
    },
    "featureList": [
      "Email Campaign Management",
      "AI-Powered Content Generation",
      "Advanced Analytics",
      "Audience Segmentation",
      "A/B Testing",
      "Real-time Tracking"
    ]
  };
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let width = canvas.width = window.innerWidth;
    let height = canvas.height = window.innerHeight;

    const characters = '0101010101010101✉️@';
    const fontSize = 14;
    const columns = width / fontSize;
    const drops: number[] = [];

    for (let i = 0; i < columns; i++) {
      drops[i] = 1;
    }
    const draw = () => {
      ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
      ctx.fillRect(0, 0, width, height);

      ctx.font = `${fontSize}px monospace`;

      for (let i = 0; i < drops.length; i++) {
        const text = characters.charAt(Math.floor(Math.random() * characters.length));

        // Randomly make some characters brighter/different color for "email" feel
        if (text === '✉️' || text === '@') {
          ctx.fillStyle = '#D8B4FE'; // Light purple for special chars
        } else {
          ctx.fillStyle = '#6B11F4'; // Logo purple for main text
        }

        ctx.fillText(text, i * fontSize, drops[i] * fontSize);

        if (drops[i] * fontSize > height && Math.random() > 0.975) {
          drops[i] = 0;
        }
        drops[i]++;
      }
    };

    const interval = setInterval(draw, 33);

    const handleResize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    window.addEventListener('resize', handleResize);

    return () => {
      clearInterval(interval);
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return (
    <div className="relative min-h-screen flex flex-col overflow-hidden bg-black text-white">
      {/* Structured Data for SEO */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
      />

      {/* Background Canvas */}
      <canvas
        ref={canvasRef}
        className="absolute top-0 left-0 w-full h-full opacity-20 pointer-events-none"
      />

      {/* Header */}
      <PublicHeader />

      <main className="flex-1 relative z-10">
        {/* Hero Section */}
        <section className="py-32 px-6 text-center space-y-8 max-w-5xl mx-auto">
          <div className="inline-flex items-center rounded-full border border-[#6B11F4]/30 bg-[#6B11F4]/10 px-4 py-1.5 text-sm text-[#A78BFA] backdrop-blur-md animate-fade-in">
            <span className="flex h-2 w-2 rounded-full bg-[#6B11F4] mr-2 animate-pulse"></span>
            We are public
          </div>

          <h1 className="text-6xl md:text-8xl font-display font-bold tracking-tighter">
            Email marketing <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#6B11F4] via-violet-500 to-fuchsia-500 animate-gradient">
              for the digital age
            </span>
          </h1>

          <p className="text-xl md:text-2xl text-gray-400 max-w-3xl mx-auto leading-relaxed">
            Sentinel provides a powerful API and beautiful dashboard to manage your email campaigns, segments, and subscribers with ease.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-6 pt-8">
            <Link
              href="/register"
              className="group inline-flex items-center justify-center rounded-full text-lg font-bold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#6B11F4] disabled:pointer-events-none disabled:opacity-50 bg-[#6B11F4] text-white hover:bg-[#5b0ecf] hover:scale-105 h-14 px-10 shadow-[0_0_20px_rgba(107,17,244,0.5)]"
            >
              Start for free
              <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              href="https://github.com/Kushagrabainsla/sentinel/tree/main"
              className="inline-flex items-center justify-center rounded-full text-lg font-medium transition-all focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-white disabled:pointer-events-none disabled:opacity-50 border border-white/20 bg-white/5 backdrop-blur-sm hover:bg-white/10 hover:border-white/40 h-14 px-10"
            >
              View Documentation
            </Link>
          </div>
        </section>

        {/* Global Scale Section */}
        <section className="py-32 px-6 relative overflow-hidden">
          <div className="container mx-auto max-w-7xl relative z-10">
            <div className="grid md:grid-cols-2 gap-12 items-center">
              <div className="space-y-8">
                <div className="inline-flex items-center rounded-full border border-[#6B11F4]/30 bg-[#6B11F4]/10 px-4 py-1.5 text-sm text-[#A78BFA] backdrop-blur-md">
                  <span className="flex h-2 w-2 rounded-full bg-[#6B11F4] mr-2 animate-pulse"></span>
                  Global Infrastructure
                </div>
                <h2 className="text-4xl md:text-6xl font-display font-bold tracking-tight">
                  Reach your audience <br />
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#6B11F4] to-violet-400">
                    everywhere
                  </span>
                </h2>
                <p className="text-xl text-gray-400 leading-relaxed max-w-lg">
                  Sentinel's intelligent delivery engine optimizes routing for every region, ensuring your emails land in inboxes across the globe, not spam folders.
                </p>
                <div className="grid grid-cols-2 gap-6 pt-4">
                  <div className="space-y-2">
                    <div className="text-3xl font-bold text-white">190+</div>
                    <div className="text-sm text-gray-500">Countries Reachable</div>
                  </div>
                  <div className="space-y-2">
                    <div className="text-3xl font-bold text-white">99.9%</div>
                    <div className="text-sm text-gray-500">Global Delivery Rate</div>
                  </div>
                </div>
              </div>
              <div className="relative h-[600px] w-full flex items-center justify-center">
                <div className="absolute inset-0 bg-gradient-to-r from-[#6B11F4]/20 to-violet-500/20 blur-3xl rounded-full opacity-20"></div>
                <Globe />
              </div>
            </div>
          </div>
        </section>

        {/* Features Grid */}
        <section className="py-32 border-t border-white/10 bg-black/50 backdrop-blur-sm" aria-labelledby="features-heading">
          <div className="container px-6 mx-auto max-w-7xl">
            <h2 id="features-heading" className="sr-only">Key Features</h2>
            <div className="grid md:grid-cols-3 gap-8">
              {[
                {
                  icon: Zap,
                  title: "AI-Powered Content",
                  desc: "Generate engaging email subjects and content instantly with GenAI. Say goodbye to writer's block.",
                  color: "text-[#6B11F4]",
                  bg: "bg-[#6B11F4]/10"
                },
                {
                  icon: Shield,
                  title: "Deep Analytics",
                  desc: "Gain actionable insights with real-time charts for engagement, geographic distribution, and optimal send times.",
                  color: "text-fuchsia-500",
                  bg: "bg-fuchsia-500/10"
                },
                {
                  icon: Mail,
                  title: "Smart Segmentation",
                  desc: "Target the right audience by organizing subscribers into dynamic segments based on their behavior and attributes.",
                  color: "text-violet-400",
                  bg: "bg-violet-400/10"
                }
              ].map((feature, i) => (
                <article key={i} className="group relative bg-white/5 border border-white/10 p-8 rounded-3xl hover:bg-white/10 transition-all duration-300 hover:-translate-y-1">
                  <div className={`h-14 w-14 rounded-2xl ${feature.bg} ${feature.color} flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300`}>
                    <feature.icon className="h-7 w-7" aria-hidden="true" />
                  </div>
                  <h3 className="text-2xl font-bold mb-4 text-white">{feature.title}</h3>
                  <p className="text-gray-400 leading-relaxed text-lg">
                    {feature.desc}
                  </p>
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-32 px-6 border-t border-white/10">
          <div className="container mx-auto max-w-5xl relative">
            <div className="absolute inset-0 bg-gradient-to-r from-[#6B11F4]/20 to-fuchsia-500/20 blur-3xl rounded-full opacity-30"></div>
            <div className="relative bg-white/5 border border-white/10 rounded-[2.5rem] p-16 text-center space-y-8 backdrop-blur-xl overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-[#6B11F4] to-transparent opacity-50"></div>

              <h2 className="text-4xl md:text-5xl font-bold text-white">Ready to get started?</h2>
              <p className="text-xl text-gray-400 max-w-2xl mx-auto">
                Join thousands of developers who trust Sentinel for their email marketing needs.
              </p>
              <div className="pt-6">
                <Link
                  href="/register"
                  className="inline-flex items-center justify-center rounded-full text-lg font-bold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#6B11F4] disabled:pointer-events-none disabled:opacity-50 bg-white text-black hover:bg-gray-200 h-14 px-12 shadow-lg"
                >
                  Create free account
                </Link>
              </div>
              <p className="text-sm text-gray-500 pt-4">
                No credit card required • Free tier available
              </p>
            </div>
          </div>
        </section>
      </main>

      <PublicFooter />
    </div>
  );
}
