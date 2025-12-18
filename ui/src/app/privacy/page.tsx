'use client';

import { PublicHeader } from "@/components/layout/PublicHeader";
import { PublicFooter } from "@/components/layout/PublicFooter";

export default function PrivacyPolicy() {
    return (
        <div className="relative min-h-screen flex flex-col bg-black text-white">
            <PublicHeader />

            <main className="flex-1 container mx-auto px-6 py-12 max-w-4xl">
                <h1 className="text-4xl md:text-5xl font-display font-bold mb-8 text-transparent bg-clip-text bg-gradient-to-r from-[#6B11F4] to-violet-400">
                    Privacy Policy
                </h1>

                <div className="space-y-8 text-gray-300 leading-relaxed">
                    <p className="text-sm text-gray-500">Last updated: December 18, 2025</p>

                    <section className="space-y-4">
                        <h2 className="text-2xl font-bold text-white">1. Introduction</h2>
                        <p>
                            Welcome to Sentinel ("we", "our", or "us"). We are committed to protecting your personal information and your right to privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you visit our website <span className="text-white">dashboard.thesentinel.site</span> (the "Site") and use our services.
                        </p>
                    </section>

                    <section className="space-y-4">
                        <h2 className="text-2xl font-bold text-white">2. Information We Collect</h2>
                        <p>We collect personal information that you voluntarily provide to us when you register on the Site, express an interest in obtaining information about us or our products and services, when you participate in activities on the Site, or otherwise when you contact us.</p>
                        <ul className="list-disc pl-5 space-y-2">
                            <li><strong>Personal Data:</strong> Personally identifiable information, such as your name, shipping address, email address, and telephone number, that you voluntarily give to us when you register with the Site.</li>
                            <li><strong>Derivative Data:</strong> Information our servers automatically collect when you access the Site, such as your IP address, your browser type, your operating system, your access times, and the pages you have viewed directly before and after accessing the Site.</li>
                        </ul>
                    </section>

                    <section className="space-y-4">
                        <h2 className="text-2xl font-bold text-white">3. How We Use Your Information</h2>
                        <p>We use the information we collect or receive:</p>
                        <ul className="list-disc pl-5 space-y-2">
                            <li>To facilitate account creation and logon process.</li>
                            <li>To send you marketing and promotional communications.</li>
                            <li>To send administrative information to you.</li>
                            <li>To fulfill and manage your orders.</li>
                            <li>To protect our Services.</li>
                        </ul>
                    </section>

                    <section className="space-y-4">
                        <h2 className="text-2xl font-bold text-white">4. Google User Data</h2>
                        <p>
                            Sentinel limits use of data to providing or improving user-facing features that are prominent in the requesting application's user interface.
                        </p>
                        <p>
                            If you choose to connect your Google account, we may access certain information as permitted by your settings. We do not sell your Google user data to third parties.
                        </p>
                    </section>

                    <section className="space-y-4">
                        <h2 className="text-2xl font-bold text-white">5. Contact Us</h2>
                        <p>
                            If you have questions or comments about this policy, you may email us at support@thesentinel.site.
                        </p>
                    </section>
                </div>
            </main>

            <PublicFooter />
        </div>
    );
}
