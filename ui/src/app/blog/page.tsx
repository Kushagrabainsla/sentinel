import Link from "next/link";
import { blogPosts } from "@/lib/blog-data";
import { PublicHeader } from "@/components/layout/PublicHeader";
import { PublicFooter } from "@/components/layout/PublicFooter";
import { Calendar, User, ArrowRight, Sparkles } from "lucide-react";
import Image from "next/image";

export const metadata = {
    title: "Blog & Guides | Sentinel",
    description: "Learn how to master AI email marketing with Sentinel tutorials, guides, and industry insights.",
};

export default function BlogListingPage() {
    return (
        <div className="relative min-h-screen flex flex-col bg-black text-white">
            <PublicHeader />

            <main className="flex-1 container mx-auto px-6 py-12 max-w-4xl">
                <h1 className="text-4xl md:text-5xl font-display font-bold mb-8 text-transparent bg-clip-text bg-gradient-to-r from-[#6B11F4] to-violet-400">
                    Blog & Guides
                </h1>

                <div className="space-y-12 text-gray-300 leading-relaxed">
                    <p className="text-lg text-gray-400 mb-12">
                        Stay updated with the latest in AI email marketing, product updates, and comprehensive guides for Sentinel.
                    </p>

                    <div className="space-y-16">
                        {blogPosts.map((post) => (
                            <section key={post.slug} className="space-y-4">
                                <div className="flex items-center gap-4 text-xs font-bold text-gray-500 uppercase tracking-widest">
                                    <span>{new Date(post.date).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</span>
                                    <span className="w-1 h-1 rounded-full bg-gray-500" />
                                    <span className="text-[#6B11F4]">{post.category}</span>
                                </div>

                                <Link href={`/blog/${post.slug}`} className="group block space-y-3">
                                    <h2 className="text-3xl font-bold text-white group-hover:text-[#6B11F4] transition-colors leading-tight">
                                        {post.title}
                                    </h2>
                                    <p className="text-gray-400 text-lg line-clamp-2">
                                        {post.description}
                                    </p>
                                </Link>

                                <Link
                                    href={`/blog/${post.slug}`}
                                    className="inline-flex items-center gap-2 text-sm font-bold text-[#6B11F4] hover:text-violet-400 transition-colors uppercase tracking-widest pt-2"
                                >
                                    Read full guide <ArrowRight className="w-4 h-4" />
                                </Link>
                            </section>
                        ))}
                    </div>
                </div>
            </main>

            <PublicFooter />
        </div>
    );
}
