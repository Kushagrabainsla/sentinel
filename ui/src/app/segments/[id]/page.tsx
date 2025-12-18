'use client';

import { useEffect, useState, use } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api, Segment } from '@/lib/api';
import { ArrowLeft, Plus, Trash2, Loader2, Mail, Activity } from 'lucide-react';
import { toast } from 'sonner';

export default function SegmentDetailsPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const [segment, setSegment] = useState<Segment | null>(null);
    const [emails, setEmails] = useState<string[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [newEmails, setNewEmails] = useState('');
    const [isAdding, setIsAdding] = useState(false);

    const fetchData = async () => {
        try {
            const [segmentRes, emailsRes] = await Promise.all([
                api.get(`/segments/${id}`),
                api.get(`/segments/${id}/emails`)
            ]);
            setSegment(segmentRes.data.segment);
            setEmails(emailsRes.data.emails || []);
        } catch (error) {
            console.error('Failed to fetch segment details:', error);
            toast.error('Failed to load segment details');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [id]);

    const getStatusLabel = (status: string) => {
        const s = (status || "").trim().toUpperCase();
        switch (s) {
            case 'A':
            case 'ACTIVE': return 'Active';
            case 'I':
            case 'INACTIVE':
            case 'TRASH': return 'Trash';
            case 'D':
            case 'DELETED': return 'Deleted';
            default: return status;
        }
    };

    const getStatusColor = (status: string) => {
        const s = (status || "").trim().toUpperCase();
        if (['A', 'ACTIVE'].includes(s)) return 'bg-green-500/10 text-green-500';
        if (['I', 'INACTIVE', 'TRASH'].includes(s)) return 'bg-yellow-500/10 text-yellow-500';
        if (['D', 'DELETED'].includes(s)) return 'bg-red-500/10 text-red-500';
        return 'bg-gray-500/10 text-gray-500';
    };

    const handleAddEmails = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newEmails.trim()) return;

        setIsAdding(true);
        try {
            const emailList = newEmails.split(',').map(e => e.trim()).filter(e => e.length > 0);
            await api.post(`/segments/${id}/emails`, { emails: emailList });
            toast.success('Emails added successfully');
            setNewEmails('');
            fetchData();
        } catch (error) {
            console.error('Failed to add emails:', error);
            toast.error('Failed to add emails');
        } finally {
            setIsAdding(false);
        }
    };

    const handleRemoveEmail = async (email: string) => {
        if (!confirm(`Remove ${email} from this segment?`)) return;

        try {
            await api.delete(`/segments/${id}/emails`, {
                data: { emails: [email] }
            });
            toast.success('Email removed');
            fetchData();
        } catch (error) {
            console.error('Failed to remove email:', error);
            toast.error('Failed to remove email');
        }
    };

    if (isLoading) {
        return (
            <div className="flex justify-center p-8">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
        );
    }

    if (!segment) {
        return <div>Segment not found</div>;
    }

    return (
        <div className="max-w-6xl mx-auto space-y-12 pb-24">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 px-2">
                <div className="flex items-start gap-6">
                    <Link
                        href="/segments"
                        className="flex h-12 w-12 items-center justify-center rounded-2xl bg-card border border-border shadow-sm hover:bg-primary/10 hover:text-primary transition-all group"
                    >
                        <ArrowLeft className="h-6 w-6 transition-transform group-hover:-translate-x-1" />
                    </Link>
                    <div className="space-y-1">
                        <div className="flex items-center gap-2 mb-1">
                            <div className="w-1 h-4 bg-primary rounded-full" />
                            <h2 className="text-[10px] font-black uppercase tracking-[0.2em] text-primary/80">Segment Intelligence</h2>
                        </div>
                        <h1 className="text-4xl font-display font-black tracking-tight text-foreground">
                            {segment.name}
                        </h1>
                        <div className="flex flex-wrap items-center gap-3 mt-2">
                            <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-[10px] font-black uppercase tracking-widest border ${getStatusColor(segment.status)}`}>
                                <div className={`w-1.5 h-1.5 rounded-full animate-pulse ${segment.status === 'A' ? 'bg-green-500' : 'bg-yellow-500'}`} />
                                {getStatusLabel(segment.status)}
                            </span>
                            <span className="text-muted-foreground/30">•</span>
                            <p className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                                <Activity className="h-4 w-4" />
                                {segment.description || 'No strategic description provided'}
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            <div className="grid gap-10 lg:grid-cols-3">
                {/* Main Content: Subscriber Nodes */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="group rounded-[2.5rem] border border-border bg-card/60 backdrop-blur-sm shadow-xl overflow-hidden transition-all hover:border-primary/20">
                        <div className="p-8 border-b border-border/50 bg-muted/30 flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
                                    <Mail className="h-5 w-5" />
                                </div>
                                <div>
                                    <h3 className="text-xl font-bold">Synchronized Contacts</h3>
                                    <p className="text-xs font-medium text-muted-foreground uppercase tracking-widest">Active nodes in segment</p>
                                </div>
                            </div>
                            <div className="px-4 py-2 rounded-2xl bg-background border border-border shadow-sm">
                                <span className="text-2xl font-black tabular-nums">{emails.length}</span>
                                <span className="ml-2 text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Total</span>
                            </div>
                        </div>

                        <div className="divide-y divide-border/50 max-h-[600px] overflow-y-auto custom-scrollbar">
                            {emails.length === 0 ? (
                                <div className="p-20 text-center space-y-4">
                                    <div className="h-16 w-16 rounded-full bg-muted mx-auto flex items-center justify-center opacity-40">
                                        <Mail className="h-8 w-8 text-muted-foreground" />
                                    </div>
                                    <p className="font-bold text-muted-foreground uppercase tracking-widest text-xs">
                                        No active nodes detected in this grouping
                                    </p>
                                </div>
                            ) : (
                                emails.map((email) => (
                                    <div key={email} className="group/item flex items-center justify-between p-6 hover:bg-primary/5 transition-all">
                                        <div className="flex items-center gap-4">
                                            <div className="h-10 w-10 rounded-xl bg-background border border-border flex items-center justify-center text-muted-foreground group-hover/item:border-primary/30 group-hover/item:text-primary transition-all">
                                                <Mail className="h-4 w-4" />
                                            </div>
                                            <div>
                                                <span className="text-base font-bold text-foreground block">{email}</span>
                                                <span className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em] opacity-60">Verified Identity</span>
                                            </div>
                                        </div>
                                        <button
                                            onClick={() => handleRemoveEmail(email)}
                                            className="h-10 w-10 rounded-xl flex items-center justify-center text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-all opacity-0 group-hover/item:opacity-100"
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </button>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>

                {/* Sidebar: Coordination */}
                <div className="space-y-8">
                    <div className="group rounded-[2.5rem] border border-border bg-card p-10 shadow-xl transition-all hover:border-primary/20 relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-8 opacity-5 pointer-events-none group-hover:scale-110 transition-transform">
                            <Plus className="h-24 w-24" />
                        </div>

                        <div className="relative space-y-8">
                            <div className="space-y-2">
                                <h3 className="text-xl font-bold">Inbound Link</h3>
                                <p className="text-sm text-muted-foreground font-medium">Inject new identities into this segment logic</p>
                            </div>

                            <form onSubmit={handleAddEmails} className="space-y-6">
                                <div className="space-y-3">
                                    <label className="text-xs font-black text-muted-foreground uppercase tracking-widest ml-1">
                                        Email Addresses
                                    </label>
                                    <textarea
                                        value={newEmails}
                                        onChange={(e) => setNewEmails(e.target.value)}
                                        placeholder="user@domain.com, guest@domain.com..."
                                        className="flex min-h-[160px] w-full rounded-2xl border border-border bg-background/50 px-5 py-4 text-base font-medium shadow-sm transition-all focus:ring-4 focus:ring-primary/10 focus:border-primary outline-none font-mono resize-none"
                                    />
                                    <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest opacity-60 px-1">
                                        Use commas to separate multiple entries
                                    </p>
                                </div>
                                <button
                                    type="submit"
                                    disabled={isAdding || !newEmails.trim()}
                                    className="w-full inline-flex items-center justify-center rounded-2xl text-sm font-black uppercase tracking-[0.1em] transition-all focus:ring-4 focus:ring-primary/20 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow-xl shadow-primary/20 hover:shadow-primary/30 hover:-translate-y-1 active:translate-y-0 h-14 px-4 group"
                                >
                                    {isAdding ? (
                                        <>
                                            <Loader2 className="mr-3 h-4 w-4 animate-spin" />
                                            Synchronizing...
                                        </>
                                    ) : (
                                        <>
                                            Inject Identities
                                            <Plus className="ml-2 h-4 w-4 transition-transform group-hover:rotate-90" />
                                        </>
                                    )}
                                </button>
                            </form>
                        </div>
                    </div>

                    {/* Insights Mini Card */}
                    <div className="rounded-[2rem] border border-border bg-card/40 p-8 space-y-4">
                        <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">System Status</h4>
                        <div className="flex items-center justify-between">
                            <span className="text-sm font-bold">Deduplication</span>
                            <span className="text-xs font-black text-emerald-500 uppercase">Active</span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-sm font-bold">Auto-Validation</span>
                            <span className="text-xs font-black text-emerald-500 uppercase">Active</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
