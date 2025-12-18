import Link from "next/link";

export function PublicHeader() {
    return (
        <header className="px-6 py-4 flex items-center justify-between border-b border-white/10 bg-black/50 backdrop-blur-md sticky top-0 z-50" role="banner">
            <div className="flex items-center gap-2 font-display font-bold text-xl">
                <img src="/images/sentinel-logo.png" alt="Sentinel Email Marketing Platform Logo" className="h-8 w-auto" />
                <Link href="/" className="bg-clip-text text-transparent bg-gradient-to-r from-[#6B11F4] to-violet-400">Sentinel</Link>
            </div>
            <nav className="flex items-center gap-4" role="navigation" aria-label="Main navigation">
                <Link href="/login" className="text-sm font-medium text-gray-300 hover:text-white transition-colors">
                    Sign In
                </Link>
                <Link
                    href="/register"
                    className="inline-flex items-center justify-center rounded-full text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-white text-black hover:bg-gray-200 h-9 px-6"
                >
                    Get Started
                </Link>
            </nav>
        </header>
    );
}
