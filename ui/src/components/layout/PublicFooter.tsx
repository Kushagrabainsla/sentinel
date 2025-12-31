import Image from "next/image";
import Link from "next/link";

export function PublicFooter() {
    return (
        <footer className="py-20 px-6 border-t border-border/40">
            <div className="container mx-auto max-w-7xl">
                <div className="flex flex-col md:flex-row justify-between items-start gap-12">
                    <div className="space-y-4">
                        <div className="flex items-center gap-3">
                            <Image src="/images/sentinel-logo.png" alt="Sentinel Logo" width={24} height={24} className="h-6 w-auto opacity-80" />
                            <span className="font-display font-black text-xl tracking-tighter uppercase">Sentinel</span>
                        </div>
                        <p className="text-sm text-muted-foreground font-medium max-w-xs">
                            The future of intelligent email infrastructure.
                            Built for developers, by developers.
                        </p>
                    </div>
                    <div className="grid grid-cols-2 gap-12 sm:gap-24">
                        <div className="space-y-4">
                            <h4 className="text-sm font-bold uppercase tracking-widest text-foreground">Resources</h4>
                            <ul className="space-y-2 text-sm font-medium text-muted-foreground">
                                <li><Link href="/blog" className="hover:text-primary transition-colors">Blog & Guides</Link></li>
                                <li><Link href="https://github.com/Kushagrabainsla/sentinel/blob/main/assets/docs/API_USAGE_GUIDE.md" className="hover:text-primary transition-colors">Documentation</Link></li>
                                <li><Link href="https://github.com/Kushagrabainsla/sentinel" className="hover:text-primary transition-colors">GitHub</Link></li>
                            </ul>
                        </div>
                        <div className="space-y-4">
                            <h4 className="text-sm font-bold uppercase tracking-widest text-foreground">Legal</h4>
                            <ul className="space-y-2 text-sm font-medium text-muted-foreground">
                                <li><Link href="/privacy" className="hover:text-primary transition-colors">Privacy Policy</Link></li>
                                <li><Link href="/terms" className="hover:text-primary transition-colors">Terms of Service</Link></li>
                            </ul>
                        </div>
                    </div>
                </div>
                <div className="mt-20 pt-8 border-t border-border/20 flex flex-col sm:flex-row justify-between items-center gap-4 text-xs font-bold text-muted-foreground uppercase tracking-widest">
                    <span>© 2025 Sentinel Inc.</span>
                    <span>Designed for the digital age</span>
                </div>
            </div>
        </footer>
    );
}
