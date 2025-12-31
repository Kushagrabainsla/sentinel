"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

export function PublicHeader() {
    const [isLoggedIn, setIsLoggedIn] = useState(false);

    useEffect(() => {
        const apiKey = localStorage.getItem('sentinel_api_key');
        setIsLoggedIn(!!apiKey);
    }, []);

    return (
        <header className="px-6 py-4 flex items-center justify-between border-b border-border/40 bg-background/60 backdrop-blur-xl sticky top-0 z-[100]" role="banner">
            <div className="flex items-center gap-2 group cursor-pointer">
                <img src="/images/sentinel-logo.png" alt="Sentinel Logo" className="h-7 w-auto transition-transform group-hover:scale-110" />
                <Link href="/" className="font-display font-black text-xl tracking-tighter">Sentinel</Link>
            </div>

            <nav className="hidden md:flex items-center gap-12 absolute left-1/2 -translate-x-1/2" role="navigation">
                <Link href="#features" className="text-sm font-bold text-muted-foreground hover:text-foreground transition-colors">Features</Link>
                <Link href="#pricing" className="text-sm font-bold text-muted-foreground hover:text-foreground transition-colors">Pricing</Link>
            </nav>

            <div className="flex items-center gap-3">
                {isLoggedIn ? (
                    <Link
                        href="/dashboard"
                        className="inline-flex items-center justify-center rounded-xl text-sm font-bold transition-all hover:scale-[1.02] active:scale-[0.98] bg-primary text-primary-foreground h-10 px-6 shadow-xl shadow-primary/10"
                    >
                        Dashboard
                    </Link>
                ) : (
                    <>
                        <Link href="/login" className="hidden sm:block text-sm font-bold text-muted-foreground hover:text-foreground transition-colors px-4">
                            Log In
                        </Link>
                        <Link
                            href="/register"
                            className="inline-flex items-center justify-center rounded-xl text-sm font-bold transition-all hover:scale-[1.02] active:scale-[0.98] bg-primary text-primary-foreground h-10 px-6 shadow-xl shadow-primary/10"
                        >
                            Get Started
                        </Link>
                    </>
                )}
            </div>
        </header>
    );
}
