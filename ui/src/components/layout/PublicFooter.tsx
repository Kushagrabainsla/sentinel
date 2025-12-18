import Link from "next/link";

export function PublicFooter() {
    return (
        <footer className="py-12 px-6 border-t border-white/10 bg-black/80 backdrop-blur-lg">
            <div className="container mx-auto max-w-7xl">
                <div className="flex flex-col md:flex-row justify-between items-center gap-6">
                    <div className="flex items-center gap-2 font-display font-bold text-xl text-gray-400">
                        <img src="/images/sentinel-logo.png" alt="Sentinel Logo" className="h-6 w-auto grayscale opacity-50" />
                        Sentinel
                    </div>
                    <div className="flex gap-8 text-sm text-gray-500">
                        <Link href="/privacy" className="hover:text-gray-300 transition-colors">Privacy Policy</Link>
                        <Link href="/terms" className="hover:text-gray-300 transition-colors">Terms of Service</Link>
                        <span>© 2025 Sentinel Inc. All rights reserved.</span>
                    </div>
                </div>
            </div>
        </footer>
    );
}
