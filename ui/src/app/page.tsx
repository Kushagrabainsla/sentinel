'use client';

import Link from "next/link";
import { ArrowRight, Zap, Shield, Mail, CheckCircle2, Users, BarChart3, ChevronDown, Activity, Server, Key, DollarSign, Sparkles, Layers, Search, MessageSquare, Smartphone, Monitor, Globe2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Globe } from "@/components/ui/Globe";
import { PublicHeader } from "@/components/layout/PublicHeader";
import { PublicFooter } from "@/components/layout/PublicFooter";

export default function LandingPage() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const apiKey = localStorage.getItem('sentinel_api_key');
    setIsLoggedIn(!!apiKey);
  }, []);

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

  return (
    <div className="relative min-h-screen flex flex-col overflow-hidden bg-background text-foreground selection:bg-primary/30">
      {/* Structured Data for SEO */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
      />

      {/* Cinematic Background */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-[#6B11F4]/10 rounded-full blur-[160px] animate-pulse" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-blue-500/5 rounded-full blur-[160px]" />
        <div className="absolute top-[20%] right-[10%] w-[30%] h-[30%] bg-purple-500/5 rounded-full blur-[120px]" />
      </div>

      <PublicHeader />

      <main className="flex-1 relative z-10 w-full">
        {/* Massive Apple-style Hero */}
        <section className="relative min-h-[90vh] flex flex-col items-center justify-center px-6 text-center pt-40 md:pt-48 pb-40 overflow-hidden">
          {/* Cinematic Background Elements */}
          <div className="absolute inset-0 z-0">
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-primary/20 rounded-full blur-[120px] opacity-20" />
          </div>

          <div className="container max-w-7xl mx-auto space-y-12 relative z-10">
            <div className="space-y-6 animate-fade-in-up opacity-0">
              <div className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-gradient-to-r from-primary/10 via-primary/5 to-purple-500/10 px-4 py-2 text-sm font-bold tracking-tight text-primary backdrop-blur-md shadow-[0_0_20px_-5px_rgba(107,17,244,0.3)]">
                <Zap className="w-4 h-4 fill-primary animate-pulse" />
                <span className="bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-400">Introducing Sentinel v2.0</span>
              </div>

              <h1 className="text-7xl md:text-[140px] font-display font-black tracking-[-0.06em] leading-[0.9] text-balance">
                Email marketing, <br />
                <span className="bg-clip-text text-transparent bg-gradient-to-b from-primary via-primary to-primary/20">reimagined.</span>
              </h1>

              <p className="text-xl md:text-2xl text-muted-foreground max-w-2xl mx-auto leading-relaxed font-medium">
                The intelligence of AI meets the simplicity of modern design.
                Built for teams who care about every pixel and every person.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-6 animate-fade-in-up opacity-0 [animation-delay:200ms]">
              <Link
                href={isLoggedIn ? "/dashboard" : "/register"}
                className="group relative inline-flex items-center justify-center rounded-2xl text-lg font-bold transition-all hover:scale-[1.02] active:scale-[0.98] bg-primary text-primary-foreground shadow-2xl shadow-primary/20 h-16 px-12"
              >
                {isLoggedIn ? "Go to Dashboard" : "Get Started for Free"}
                <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
              </Link>
              <Link
                href="https://github.com/Kushagrabainsla/sentinel"
                className="inline-flex items-center justify-center rounded-2xl text-lg font-bold transition-all hover:bg-muted bg-background border border-border h-16 px-10 shadow-sm"
              >
                View on GitHub
              </Link>
            </div>

            {/* Refined Balanced Logo Container */}
            <div className="relative pt-20 animate-fade-in-up opacity-0 [animation-delay:400ms]">
              <div className="relative mx-auto max-w-[450px] group">
                <div className="relative rounded-[4rem] overflow-hidden border border-white/10 bg-black/30 backdrop-blur-2xl shadow-[0_0_60px_-10px_rgba(107,17,244,0.4)] transition-all duration-1000 aspect-square flex items-center justify-center mx-auto">
                  <div className="relative z-10 p-0 flex items-center justify-center w-full h-full">
                    <div className="absolute inset-0 bg-primary/30 rounded-full blur-[80px] animate-pulse [animation-duration:3s]" />
                    <img
                      src="/images/sentinel-logo.png"
                      alt="Sentinel"
                      className="w-full h-full object-contain relative z-20 drop-shadow-[0_0_40px_rgba(107,17,244,0.5)] transition-all duration-1000 group-hover:scale-105 invert dark:invert-0"
                    />
                  </div>

                  {/* Elegant ambient gradient */}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-black/10 pointer-events-none" />
                </div>
              </div>

              {/* Enhanced Secondary Floating Elements */}
              <div className="absolute -left-16 top-1/2 -translate-y-1/2 animate-float hidden xl:block z-20">
                <div className="p-8 rounded-[2.5rem] bg-card/80 border border-white/10 shadow-3xl backdrop-blur-3xl space-y-6 w-80 text-left">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-2xl bg-primary/20 flex items-center justify-center text-primary">
                      <Zap className="w-6 h-6 fill-primary" />
                    </div>
                    <div>
                      <div className="text-[11px] font-black uppercase tracking-widest opacity-50">AI Content Engine</div>
                      <div className="text-base font-bold">Generating Draft...</div>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div className="h-2 w-full bg-primary/10 rounded-full overflow-hidden">
                      <div className="h-full w-[70%] bg-primary animate-pulse" />
                    </div>
                    <div className="flex justify-between items-center text-[10px] font-black text-muted-foreground uppercase tracking-tighter">
                      <span>70% Confidence</span>
                      <span className="text-primary">Live</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="absolute -right-24 bottom-20 animate-float [animation-delay:1.5s] hidden xl:block z-20">
                <div className="p-8 rounded-[2.5rem] bg-card/80 border border-white/10 shadow-3xl backdrop-blur-3xl space-y-6 w-80 text-left">
                  <div className="flex items-center gap-4">
                    <div className="flex -space-x-4">
                      {[1, 2, 3, 4].map((i) => (
                        <div key={i} className="w-10 h-10 rounded-full border-4 border-card bg-muted flex items-center justify-center overflow-hidden">
                          <img src={`https://i.pravatar.cc/100?img=${i + 15}`} alt="user" className="w-full h-full object-cover" />
                        </div>
                      ))}
                    </div>
                    <div className="h-6 w-px bg-white/10" />
                    <div className="text-base font-bold">+1,248</div>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-green-500/10 border border-green-500/20 text-[11px] font-black text-green-500 uppercase">
                      <Activity className="w-3.5 h-3.5" />
                      Live Conversion
                    </div>
                    <span className="text-[10px] font-bold opacity-40">2s ago</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Features Journey Container */}
        <div className="relative">
          {/* Vertical Stitching Line (The Spine) */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-px h-full bg-gradient-to-b from-primary via-border to-primary opacity-20 pointer-events-none z-20" />

          {/* AI Generation Section */}
          <section id="features" className="py-24 px-6 relative">
            {/* Intersection Node */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 z-30">
              <div className="w-5 h-5 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center animate-pulse">
                <div className="w-2 h-2 rounded-full bg-primary shadow-[0_0_15px_var(--primary)]" />
              </div>
            </div>
            <div className="container mx-auto max-w-7xl">
              <div className="relative rounded-[4rem] bg-card border border-border/40 p-8 md:p-20 overflow-hidden group">
                <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-transparent pointer-events-none" />

                <div className="grid lg:grid-cols-2 gap-20 items-center relative z-10">
                  <div className="space-y-8 animate-fade-in-up opacity-0">
                    <div className="inline-flex items-center gap-2 rounded-full border border-purple-500/20 bg-purple-500/5 px-4 py-2 text-sm font-bold tracking-tight text-purple-500">
                      <Sparkles className="w-4 h-4 fill-purple-500" />
                      <span>Artificial Intelligence</span>
                    </div>
                    <h2 className="text-5xl md:text-6xl font-display font-black tracking-tight leading-tight">
                      Writer's block, <br />
                      <span className="text-muted-foreground">extinguished.</span>
                    </h2>
                    <p className="text-xl text-muted-foreground leading-relaxed max-w-lg font-medium">
                      Leverage the power of advanced AI to draft high-converting emails in seconds. From subject lines to full campaigns, Sentinel knows what resonates.
                    </p>
                    <div className="space-y-4 pt-4">
                      <div className="flex items-start gap-4 p-4 rounded-2xl bg-secondary/50 border border-border/40 max-w-sm">
                        <MessageSquare className="w-6 h-6 text-purple-500 mt-1" />
                        <div className="space-y-1">
                          <div className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Drafting Suggestion</div>
                          <p className="text-sm font-medium">"Boost your summer sales with 20% off..."</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="relative animate-fade-in-up opacity-0 [animation-delay:200ms]">
                    <div className="bg-background rounded-3xl border border-border/50 shadow-2xl p-8 space-y-6 relative overflow-hidden group/draft">
                      <div className="flex items-center gap-3 border-b border-border/40 pb-4">
                        <div className="w-3 h-3 rounded-full bg-red-500/20" />
                        <div className="w-3 h-3 rounded-full bg-amber-500/20" />
                        <div className="w-3 h-3 rounded-full bg-green-500/20" />
                      </div>
                      <div className="space-y-4">
                        <div className="h-4 w-1/3 bg-muted/50 rounded-full" />
                        <div className="h-4 w-full bg-muted/20 rounded-full" />
                        <div className="h-4 w-5/6 bg-muted/20 rounded-full" />
                        <div className="h-4 w-4/5 bg-primary/10 rounded-full relative overflow-hidden">
                          <div className="absolute inset-0 bg-primary/20 animate-reveal" />
                        </div>
                      </div>
                      <div className="pt-6">
                        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-primary text-primary-foreground text-xs font-bold">
                          Apply Draft
                        </div>
                      </div>
                    </div>
                    {/* Ambient Glow */}
                    <div className="absolute -bottom-10 -left-10 w-40 h-40 bg-purple-500/20 rounded-full blur-3xl" />
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Email Authorization Section */}
          <section id="authorization" className="py-24 px-6 relative">
            {/* Intersection Node */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 z-30">
              <div className="w-5 h-5 rounded-full bg-green-500/20 border border-green-500/30 flex items-center justify-center animate-pulse">
                <div className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_15px_#22c55e]" />
              </div>
            </div>
            <div className="container mx-auto max-w-7xl">
              <div className="relative rounded-[4rem] bg-card border border-border/40 p-8 md:p-20 overflow-hidden group">
                <div className="absolute inset-0 bg-gradient-to-br from-green-500/5 to-transparent pointer-events-none" />

                <div className="grid lg:grid-cols-2 gap-20 items-center relative z-10">
                  <div className="relative order-2 lg:order-1 transition-all duration-1000">
                    {/* Visual Representation of Email Auth */}
                    <div className="relative rounded-[3rem] bg-secondary/50 border border-border/40 p-8 md:p-12 aspect-[4/3] flex flex-col justify-center items-center gap-8 group/icon overflow-hidden">
                      <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-transparent transition-opacity duration-700" />

                      <div className="relative z-10 flex items-center justify-center gap-6">
                        <div className="w-20 h-20 rounded-3xl bg-card border border-border shadow-xl flex items-center justify-center text-primary">
                          <Mail className="w-10 h-10" />
                        </div>
                        <div className="flex flex-col gap-1 items-center">
                          <div className="w-12 h-0.5 border-t-2 border-dashed border-primary/20" />
                          <div className="p-2 rounded-full bg-primary/10">
                            <Shield className="w-4 h-4 text-primary" />
                          </div>
                          <div className="w-12 h-0.5 border-t-2 border-dashed border-primary/20" />
                        </div>
                        <div className="w-20 h-20 rounded-3xl bg-primary text-primary-foreground shadow-2xl flex items-center justify-center transition-all duration-700 hover:scale-105">
                          <img src="/images/sentinel-logo.png" alt="Sentinel" width={32} height={32} className="h-8 w-8 invert dark:invert-0" />
                        </div>
                      </div>

                      <div className="space-y-4 text-center">
                        <div className="inline-flex items-center gap-2 rounded-full bg-green-500/10 px-4 py-1.5 text-[10px] font-black uppercase tracking-widest text-green-500 border border-green-500/20">
                          Authenticated via OAuth
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-10 order-1 lg:order-2">
                    <div className="space-y-6">
                      <div className="inline-flex items-center gap-2 rounded-full border border-green-500/20 bg-green-500/5 px-4 py-2 text-sm font-bold tracking-tight text-green-500">
                        <Shield className="w-4 h-4" />
                        <span>Identity & Trust</span>
                      </div>
                      <h2 className="text-5xl md:text-6xl font-display font-black tracking-tight leading-[0.95]">
                        Your email, <br />
                        <span className="text-muted-foreground">your identity.</span>
                      </h2>
                      <p className="text-xl text-muted-foreground font-medium leading-relaxed max-w-lg">
                        Instead of sending from generic system domains, authorize your own professional email address. Sentinel sends directly from your inbox, ensuring maximum deliverability and trust.
                      </p>
                    </div>

                    <div className="grid sm:grid-cols-2 gap-8">
                      <div className="space-y-4">
                        <div className="w-12 h-12 rounded-2xl bg-amber-500/10 flex items-center justify-center text-amber-500">
                          <Zap className="w-6 h-6" />
                        </div>
                        <h4 className="text-lg font-bold">Instant Setup</h4>
                        <p className="text-sm text-muted-foreground font-medium">No complex DNS records or technical configuration required. Authorize with your email provider in just two clicks.</p>
                      </div>
                      <div className="space-y-4">
                        <div className="w-12 h-12 rounded-2xl bg-blue-500/10 flex items-center justify-center text-blue-500">
                          <CheckCircle2 className="w-6 h-6" />
                        </div>
                        <h4 className="text-lg font-bold">Primary Inbox Delivery</h4>
                        <p className="text-sm text-muted-foreground font-medium">By using your authorized personal email, your messages are more likely to land in the primary inbox, not the promotions tab.</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Global Scale & Security Section */}
          <section id="global-scale" className="py-24 px-6 relative">
            {/* Intersection Node */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 z-30">
              <div className="w-5 h-5 rounded-full bg-purple-500/20 border border-purple-500/30 flex items-center justify-center animate-pulse">
                <div className="w-2 h-2 rounded-full bg-[#6B11F4] shadow-[0_0_15px_#6B11F4]" />
              </div>
            </div>
            <div className="container mx-auto max-w-7xl">
              <div className="relative rounded-[4rem] bg-[#6B11F4] border border-white/10 p-8 md:p-20 overflow-hidden group text-white hover:border-white/20 transition-all duration-700">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,255,255,0.15),transparent)] pointer-events-none" />

                <div className="grid lg:grid-cols-2 gap-20 items-center relative z-10">
                  <div className="space-y-8 animate-fade-in-up opacity-0">
                    <div className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-bold tracking-tight text-white">
                      <Globe2 className="w-4 h-4" />
                      <span>Global Infrastructure</span>
                    </div>
                    <h2 className="text-5xl md:text-7xl font-display font-black tracking-tight leading-tight">
                      Scale without <br />
                      <span className="opacity-50">boundaries.</span>
                    </h2>
                    <p className="text-xl text-white/70 leading-relaxed max-w-lg font-medium">
                      Reach 190+ countries with a 99.9% delivery rate. Our infrastructure is designed for high-volume sending without compromising on privacy or latency.
                    </p>
                    <div className="grid grid-cols-2 gap-8 pt-4">
                      <div className="space-y-1">
                        <div className="text-4xl font-display font-black tracking-tighter">99.9%</div>
                        <div className="text-[10px] font-black uppercase tracking-[0.2em] opacity-50">Deliverability</div>
                      </div>
                      <div className="space-y-1">
                        <div className="text-4xl font-display font-black tracking-tighter">190+</div>
                        <div className="text-[10px] font-black uppercase tracking-[0.2em] opacity-50">Countries</div>
                      </div>
                    </div>
                  </div>

                  <div className="relative animate-fade-in-up opacity-0 [animation-delay:200ms] flex items-center justify-center min-h-[500px]">
                    <div className="absolute inset-0 bg-white/5 rounded-full blur-3xl animate-pulse" />
                    <div className="relative z-10 w-full flex items-center justify-center">
                      <Globe className="!max-w-none !mx-0 w-[500px] h-[500px]" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Interactive Analytics Preview */}
          <section id="analytics" className="py-24 px-6 relative">
            {/* Intersection Node */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 z-30">
              <div className="w-5 h-5 rounded-full bg-blue-500/20 border border-blue-500/30 flex items-center justify-center animate-pulse">
                <div className="w-2 h-2 rounded-full bg-blue-500 shadow-[0_0_15px_#3b82f6]" />
              </div>
            </div>
            <div className="container mx-auto max-w-7xl">
              <div className="relative rounded-[4rem] bg-card border border-border/40 p-8 md:p-20 overflow-hidden group">
                <div className="absolute top-0 right-0 w-full h-full opacity-5 pointer-events-none">
                  <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,var(--primary),transparent)]" />
                </div>

                <div className="grid lg:grid-cols-2 gap-20 items-center relative z-10">
                  <div className="space-y-8 animate-fade-in-up opacity-0">
                    <div className="inline-flex items-center gap-2 rounded-full border border-blue-500/20 bg-blue-500/5 px-4 py-2 text-sm font-bold tracking-tight text-blue-500">
                      <Activity className="w-4 h-4" />
                      <span>Real-time Intelligence</span>
                    </div>
                    <h2 className="text-5xl md:text-6xl font-display font-black tracking-tight leading-tight">
                      Analytics that <br />
                      <span className="text-muted-foreground">move the needle.</span>
                    </h2>
                    <p className="text-xl text-muted-foreground leading-relaxed max-w-lg font-medium">
                      Gain deep insights into your audience behavior. Track every open, click, and conversion with precision timing and geographic mapping.
                    </p>
                    <ul className="space-y-4 pt-4">
                      {[
                        "Optimal send time recommendations",
                        "Geographic engagement mapping",
                        "A/B test performance breakdown"
                      ].map((text, i) => (
                        <li key={i} className="flex items-center gap-3 text-sm font-bold text-foreground">
                          <div className="w-5 h-5 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                            <CheckCircle2 className="w-3 h-3" />
                          </div>
                          {text}
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="relative animate-fade-in-up opacity-0 [animation-delay:200ms]">
                    {/* Mock Analytics UI */}
                    <div className="relative bg-background rounded-3xl border border-border/50 shadow-2xl p-8 space-y-8 overflow-hidden">
                      <div className="flex justify-between items-center pb-2 border-b border-border/40">
                        <span className="text-sm font-bold flex items-center gap-2">
                          <Globe2 className="w-4 h-4 text-primary" />
                          Live Global Reach
                        </span>
                        <div className="flex items-center gap-1">
                          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                          <span className="text-[10px] font-black uppercase tracking-widest text-green-500">Active Now</span>
                        </div>
                      </div>

                      <div className="flex justify-between items-end h-40 gap-3 px-4">
                        {[40, 70, 45, 90, 65, 80, 55].map((h, i) => (
                          <div
                            key={i}
                            className="flex-1 relative group/bar"
                            style={{ height: '100%' }}
                          >
                            <div
                              className="w-full bg-primary/10 rounded-t-lg absolute bottom-0 transition-all duration-700 group-hover:bg-primary/30"
                              style={{
                                height: `${h}%`,
                                transitionDelay: `${i * 100}ms`
                              }}
                            />
                            <div
                              className="w-full bg-primary/60 rounded-t-lg absolute bottom-0 transition-all duration-1000 group-hover:bg-primary"
                              style={{
                                height: `${h * 0.6}%`,
                                transitionDelay: `${i * 150}ms`
                              }}
                            />
                          </div>
                        ))}
                      </div>

                      <div className="grid grid-cols-2 gap-6 py-4">
                        <div className="flex items-center gap-3 p-3 rounded-2xl bg-secondary/30">
                          <Smartphone className="w-5 h-5 text-muted-foreground" />
                          <div className="space-y-0.5">
                            <div className="text-[10px] font-bold text-muted-foreground uppercase leading-none">Mobile</div>
                            <div className="text-lg font-black leading-none">64%</div>
                          </div>
                        </div>
                        <div className="flex items-center gap-3 p-3 rounded-2xl bg-secondary/30">
                          <Monitor className="w-5 h-5 text-muted-foreground" />
                          <div className="space-y-0.5">
                            <div className="text-[10px] font-bold text-muted-foreground uppercase leading-none">Desktop</div>
                            <div className="text-lg font-black leading-none">36%</div>
                          </div>
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-4 pt-4 border-t border-border/40">
                        <div className="space-y-1">
                          <div className="text-xs font-bold text-muted-foreground uppercase tracking-widest">Avg. Open Rate</div>
                          <div className="text-2xl font-display font-black tracking-tight">24.8%</div>
                        </div>
                        <div className="space-y-1">
                          <div className="text-xs font-bold text-muted-foreground uppercase tracking-widest">Click-through</div>
                          <div className="text-2xl font-display font-black tracking-tight">3.2%</div>
                        </div>
                        <div className="space-y-1">
                          <div className="text-xs font-bold text-muted-foreground uppercase tracking-widest">Conversion</div>
                          <div className="text-2xl font-display font-black tracking-tight">1.8%</div>
                        </div>
                      </div>
                    </div>

                    {/* Live Feed Floating Card */}
                    <div className="absolute -bottom-8 -right-6 w-64 bg-card border border-border/50 rounded-2xl shadow-3xl p-4 space-y-3 animate-float hidden md:block backdrop-blur-xl z-20">
                      <div className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Recent Activity</div>
                      <div className="space-y-2">
                        <div className="flex items-center gap-2 text-[11px] font-medium animate-fade-in-up">
                          <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                          <span>User in <span className="font-bold">Berlin</span> opened email</span>
                          <span className="ml-auto text-muted-foreground text-[9px]">2s ago</span>
                        </div>
                        <div className="flex items-center gap-2 text-[11px] font-medium animate-fade-in-up [animation-delay:1s]">
                          <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
                          <span>New click from <span className="font-bold">Tokyo</span></span>
                          <span className="ml-auto text-muted-foreground text-[9px]">5s ago</span>
                        </div>
                      </div>
                    </div>

                    {/* Floating Decoration */}
                    <div className="absolute -top-6 -right-6 w-32 h-32 bg-primary/10 rounded-full blur-3xl opacity-50" />
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Segmentation Section */}
          <section id="segmentation" className="py-24 px-6 relative">
            {/* Intersection Node */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 z-30">
              <div className="w-5 h-5 rounded-full bg-blue-500/20 border border-blue-500/30 flex items-center justify-center animate-pulse">
                <div className="w-2 h-2 rounded-full bg-blue-500 shadow-[0_0_15px_#3b82f6]" />
              </div>
            </div>
            <div className="container mx-auto max-w-7xl">
              <div className="relative rounded-[4rem] bg-card border border-border/40 p-8 md:p-20 overflow-hidden group">
                <div className="absolute inset-0 bg-gradient-to-tr from-blue-500/5 to-transparent pointer-events-none" />

                <div className="grid lg:grid-cols-2 gap-20 items-center relative z-10">
                  <div className="relative order-2 lg:order-1 animate-fade-in-up opacity-0">
                    {/* Segmentation UI Mockup */}
                    <div className="grid grid-cols-2 gap-4">
                      {[
                        { label: "High Value", color: "bg-green-500", count: "2.4k" },
                        { label: "Inactive", color: "bg-red-500", count: "1.1k" },
                        { label: "New Users", color: "bg-blue-500", count: "890" },
                        { label: "Engineers", color: "bg-amber-500", count: "540" }
                      ].map((s, i) => (
                        <div key={i} className="bg-background rounded-3xl border border-border/50 p-6 space-y-3 shadow-xl transition-transform hover:-translate-y-1">
                          <div className="flex items-center gap-2">
                            <div className={`w-2 h-2 rounded-full ${s.color}`} />
                            <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">{s.label}</span>
                          </div>
                          <div className="text-2xl font-display font-black tracking-tight">{s.count}</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-8 order-1 lg:order-2 animate-fade-in-up opacity-0 [animation-delay:200ms]">
                    <div className="inline-flex items-center gap-2 rounded-full border border-blue-500/20 bg-blue-500/5 px-4 py-2 text-sm font-bold tracking-tight text-blue-500">
                      <Layers className="w-4 h-4" />
                      <span>Precision Targeting</span>
                    </div>
                    <h2 className="text-5xl md:text-6xl font-display font-black tracking-tight leading-tight">
                      Right person, <br />
                      <span className="text-muted-foreground">right time.</span>
                    </h2>
                    <p className="text-xl text-muted-foreground leading-relaxed max-w-lg font-medium">
                      Create dynamic segments based on behavior, attributes, and purchase history. Deliver personalized messages that feel hand-crafted for every subscriber.
                    </p>
                    <div className="pt-4">
                      <div className="flex items-center gap-4 text-sm font-bold">
                        <Search className="w-5 h-5 text-primary" />
                        <span className="pb-1 border-b-2 border-primary/20">filter by "last_active {"<"} 30 days"</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            {/* Terminal Node */}
            <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 z-30">
              <div className="w-5 h-5 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center animate-pulse">
                <div className="w-2 h-2 rounded-full bg-primary shadow-[0_0_15px_var(--primary)]" />
              </div>
            </div>
          </section>
        </div>

        {/* FAQ Section */}
        <section id="faq" className="py-40 px-6">
          <div className="container mx-auto max-w-3xl">
            <div className="text-center space-y-4 mb-20 animate-fade-in-up opacity-0">
              <h2 className="text-4xl md:text-5xl font-display font-black tracking-tight">Questions? Answers.</h2>
              <p className="text-xl text-muted-foreground font-medium">Everything you need to know about Sentinel.</p>
            </div>

            <div className="space-y-4">
              {[
                {
                  q: "What is Sentinel exactly?",
                  a: "Sentinel is a high-performance email marketing infrastructure built for teams who need more control, better deliverability, and AI-powered automation without the complexity of traditional platforms."
                },
                {
                  q: "Do I need my own email provider?",
                  a: "Sentinel currently integrates seamlessly with AWS SES to provide the most reliable and cost-effective sending infrastructure, though we handle all the complexity of management for you."
                },
                {
                  q: "How does the AI generation work?",
                  a: "We leverage advanced AI to analyze your audience's historical engagement and generate high-converting subject lines and email copy tailored to your brand voice."
                },
                {
                  q: "Is my data secure?",
                  a: "Security is built into our core. We use enterprise-grade encryption for all data at rest and in transit, and we never use your proprietary email data to train public AI models."
                }
              ].map((item, i) => (
                <div key={i} className="group animate-fade-in-up opacity-0" style={{ animationDelay: `${i * 100}ms` }}>
                  <details className="p-8 rounded-[2rem] bg-card border border-border/40 hover:border-primary/20 transition-all cursor-pointer [&_summary::-webkit-details-marker]:hidden">
                    <summary className="flex items-center justify-between gap-4 font-display font-bold text-xl tracking-tight list-none">
                      {item.q}
                      <ChevronDown className="w-5 h-5 text-muted-foreground transition-transform group-open:rotate-180" />
                    </summary>
                    <div className="pt-6 text-muted-foreground leading-relaxed font-medium">
                      {item.a}
                    </div>
                  </details>
                </div>
              ))}
            </div>
          </div>
        </section>
        <section id="pricing" className="py-40 px-6">
          <div className="container mx-auto max-w-6xl">
            <div className="relative rounded-[3.5rem] bg-primary p-12 md:p-24 text-center space-y-12 overflow-hidden shadow-2xl shadow-primary/20 animate-fade-in-up opacity-0">
              {/* Decorative elements for CTA */}
              <div className="absolute top-0 left-0 w-full h-full pointer-events-none">
                <div className="absolute top-[-20%] right-[-10%] w-[60%] h-[60%] bg-white/10 rounded-full blur-[100px]" />
                <div className="absolute bottom-[-10%] left-[-10%] w-[40%] h-[40%] bg-white/5 rounded-full blur-[80px]" />
              </div>

              <div className="relative z-10 space-y-8">
                <h2 className="text-5xl md:text-[80px] lg:text-[100px] font-display font-black tracking-tight leading-[0.9] text-primary-foreground">
                  Be the first to know. <br />
                  <span className="opacity-30">Start sending now.</span>
                </h2>

                <p className="text-xl text-primary-foreground/80 max-w-xl mx-auto font-medium">
                  Experience the next generation of email infrastructure.
                  Join Sentinel today and transform your customer engagement.
                </p>

                <div className="pt-6">
                  <Link
                    href={isLoggedIn ? "/dashboard" : "/register"}
                    className="group relative inline-flex items-center justify-center rounded-2xl text-xl font-bold transition-all hover:scale-[1.05] active:scale-[0.95] bg-primary-foreground text-primary h-20 px-16 shadow-[0_20px_50px_rgba(0,0,0,0.2)]"
                  >
                    {isLoggedIn ? "Go to Dashboard" : "Get Started Now"}
                    <ArrowRight className="ml-3 h-6 w-6 group-hover:translate-x-1 transition-transform" />
                  </Link>
                </div>

                <div className="flex items-center justify-center gap-6 pt-4 text-xs font-bold text-primary-foreground/60 uppercase tracking-widest">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4" />
                    No credit card
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4" />
                    Free tier included
                  </div>
                </div>
              </div>

              {/* Background Text Overlay */}
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 -z-0 select-none pointer-events-none opacity-[0.05]">
                <span className="text-[250px] font-black tracking-tighter uppercase leading-none text-white">SENTINEL</span>
              </div>
            </div>
          </div>
        </section>
      </main>

      <PublicFooter />
    </div>
  );
}
