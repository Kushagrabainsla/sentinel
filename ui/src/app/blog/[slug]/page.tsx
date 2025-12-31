import Link from "next/link";
import { blogPosts } from "@/lib/blog-data";
import { PublicHeader } from "@/components/layout/PublicHeader";
import { PublicFooter } from "@/components/layout/PublicFooter";
import { Calendar, User, ArrowLeft, Share2, Sparkles } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { notFound } from "next/navigation";

export async function generateStaticParams() {
    return blogPosts.map((post) => ({
        slug: post.slug,
    }));
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
    const { slug } = await params;
    const post = blogPosts.find((p) => p.slug === slug);
    if (!post) return;

    return {
        title: `${post.title} | Sentinel Blog`,
        description: post.description,
    };
}

export default async function BlogPostPage({ params }: { params: Promise<{ slug: string }> }) {
    const { slug } = await params;
    const post = blogPosts.find((p) => p.slug === slug);

    if (!post) {
        notFound();
    }

    return (
        <div className="relative min-h-screen flex flex-col bg-black text-white">
            <PublicHeader />

            <main className="flex-1 container mx-auto px-6 py-12 max-w-4xl">
                <Link
                    href="/blog"
                    className="inline-flex items-center gap-2 text-sm font-bold text-gray-500 hover:text-[#6B11F4] transition-colors mb-12 uppercase tracking-widest"
                >
                    <ArrowLeft className="w-4 h-4" />
                    Back to Blog
                </Link>

                <article className="space-y-12">
                    <div className="space-y-6">
                        <div className="flex items-center gap-4 text-xs font-bold text-gray-500 uppercase tracking-widest">
                            <span>{new Date(post.date).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</span>
                            <span className="w-1 h-1 rounded-full bg-gray-500" />
                            <span className="text-[#6B11F4]">{post.category}</span>
                        </div>

                        <h1 className="text-4xl md:text-5xl font-display font-bold text-white leading-tight">
                            {post.title}
                        </h1>

                        <div className="flex items-center gap-3 pt-2 text-sm text-gray-400 font-medium pb-8 border-b border-gray-800">
                            <span className="text-gray-500">By</span>
                            <span className="text-white">{post.author}</span>
                        </div>
                    </div>

                    <div className="prose prose-invert prose-violet max-w-none 
                        prose-headings:text-white prose-headings:font-bold prose-headings:font-display
                        prose-p:text-gray-300 prose-p:text-lg prose-p:leading-relaxed
                        prose-strong:text-white prose-strong:font-bold
                        prose-li:text-gray-300
                        prose-a:text-[#6B11F4] hover:prose-a:text-violet-400">
                        <ReactMarkdown>{post.content}</ReactMarkdown>
                    </div>

                    {/* Simple CTA */}
                    <div className="mt-24 pt-12 border-t border-gray-800 flex flex-col items-center text-center space-y-6">
                        <h2 className="text-2xl font-bold text-white">Ready to transform your email marketing?</h2>
                        <Link
                            href="/register"
                            className="inline-flex items-center justify-center rounded-xl bg-[#6B11F4] text-white h-14 px-10 text-sm font-bold transition-all hover:bg-violet-600 active:scale-95 shadow-xl shadow-[#6B11F4]/10"
                        >
                            Get Started with Sentinel
                        </Link>
                    </div>
                </article>
            </main>

            <PublicFooter />
        </div>
    );
}
