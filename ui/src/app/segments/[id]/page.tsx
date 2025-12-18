'use client';

import { useEffect, useState, use } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api, Segment } from '@/lib/api';
import { ArrowLeft, Plus, Trash2, Loader2, Mail } from 'lucide-react';
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
        <div className="space-y-8">
            <div className="flex items-center gap-4">
                <Link
                    href="/segments"
                    className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground"
                >
                    <ArrowLeft className="h-4 w-4" />
                </Link>
                <div>
                    <h1 className="text-3xl font-display font-bold tracking-tight">
                        {segment.name}
                    </h1>
                    <div className="flex items-center gap-2 mt-1">
                        <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${getStatusColor(segment.status)}`}>
                            {getStatusLabel(segment.status)}
                        </span>
                        <span className="text-muted-foreground">•</span>
                        <p className="text-muted-foreground">
                            {segment.description || 'No description'}
                        </p>
                    </div>
                </div>
            </div>

            <div className="grid gap-8 md:grid-cols-[2fr,1fr]">
                <div className="space-y-6">
                    <div className="rounded-xl border border-border bg-card shadow-sm">
                        <div className="p-6 border-b border-border">
                            <h3 className="font-semibold">Subscribers ({emails.length})</h3>
                        </div>
                        <div className="divide-y divide-border">
                            {emails.length === 0 ? (
                                <div className="p-6 text-center text-muted-foreground">
                                    No emails in this segment yet.
                                </div>
                            ) : (
                                emails.map((email) => (
                                    <div key={email} className="flex items-center justify-between p-4 hover:bg-muted/50 transition-colors">
                                        <div className="flex items-center gap-3">
                                            <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                                                <Mail className="h-4 w-4" />
                                            </div>
                                            <span className="text-sm font-medium">{email}</span>
                                        </div>
                                        <button
                                            onClick={() => handleRemoveEmail(email)}
                                            className="p-2 text-muted-foreground hover:text-destructive transition-colors"
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </button>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>

                <div className="space-y-6">
                    <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
                        <h3 className="font-semibold mb-4">Add Subscribers</h3>
                        <form onSubmit={handleAddEmails} className="space-y-4">
                            <div className="space-y-2">
                                <label className="text-sm text-muted-foreground">
                                    Enter emails (comma separated)
                                </label>
                                <textarea
                                    value={newEmails}
                                    onChange={(e) => setNewEmails(e.target.value)}
                                    placeholder="john@example.com, jane@example.com"
                                    className="flex min-h-[120px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 font-mono"
                                />
                            </div>
                            <button
                                type="submit"
                                disabled={isAdding || !newEmails.trim()}
                                className="w-full inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow hover:bg-primary/90 h-9 px-4 py-2"
                            >
                                {isAdding ? (
                                    <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        Adding...
                                    </>
                                ) : (
                                    'Add Emails'
                                )}
                            </button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    );
}
