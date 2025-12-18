'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api, Segment } from '@/lib/api';
import { Plus, Users, Trash2, Loader2, ArrowRight } from 'lucide-react';
import { toast } from 'sonner';

export default function SegmentsPage() {
    const [segments, setSegments] = useState<Segment[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'active' | 'trash'>('active');
    const router = useRouter();

    const fetchSegments = async () => {
        try {
            const response = await api.get('/segments');
            setSegments(response.data.segments || []);
        } catch (error) {
            console.error('Failed to fetch segments:', error);
            toast.error('Failed to load segments');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchSegments();
    }, []);

    const handleDelete = async (e: React.MouseEvent, segment: Segment) => {
        e.preventDefault(); // Prevent navigation to details
        const isTrash = segment.status === 'I';
        const message = isTrash
            ? 'Are you sure you want to delete this segment from trash? It will be permanently removed from your dashboard.'
            : 'Are you sure you want to move this segment to trash?';

        if (!confirm(message)) return;

        try {
            await api.delete(`/segments/${segment.id}`);
            toast.success(isTrash ? 'Segment deleted permanently' : 'Segment moved to trash');
            fetchSegments();
        } catch (error) {
            console.error('Failed to delete segment:', error);
            toast.error('Failed to delete segment');
        }
    };

    const filteredSegments = segments.filter(segment => {
        const status = (segment.status || "").toLowerCase().trim();
        if (activeTab === 'active') {
            // Show everything that isn't explicitly Trashed or Deleted
            return status !== 'i' && status !== 'inactive' && status !== 'trash' && status !== 'd' && status !== 'deleted';
        } else {
            // Show explicitly Trashed items
            return status === 'i' || status === 'inactive' || status === 'trash';
        }
    });

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

    return (
        <div className="max-w-6xl mx-auto space-y-10 pb-20">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div>
                    <h1 className="text-4xl font-display font-bold tracking-tight text-foreground">
                        Segments
                    </h1>
                    <p className="text-muted-foreground mt-1">
                        Manage your audience and subscriber groups
                    </p>
                </div>
                <Link
                    href="/segments/new"
                    className="inline-flex items-center justify-center rounded-xl text-sm font-bold transition-all hover:scale-[1.02] active:scale-[0.98] bg-primary text-primary-foreground shadow-lg h-12 px-8"
                >
                    <Plus className="mr-2 h-5 w-5" />
                    Create New Segment
                </Link>
            </div>

            {/* Tab Navigation */}
            <div className="flex items-center gap-1 p-1 bg-muted/40 rounded-2xl w-fit border border-border/50">
                <button
                    onClick={() => setActiveTab('active')}
                    className={`px-6 py-2.5 text-sm font-bold rounded-xl transition-all ${activeTab === 'active'
                        ? 'bg-background text-primary shadow-sm'
                        : 'text-muted-foreground hover:text-foreground'
                        }`}
                >
                    Active Groups
                </button>
                <button
                    onClick={() => setActiveTab('trash')}
                    className={`px-6 py-2.5 text-sm font-bold rounded-xl transition-all ${activeTab === 'trash'
                        ? 'bg-background text-primary shadow-sm'
                        : 'text-muted-foreground hover:text-foreground'
                        }`}
                >
                    Archive
                </button>
            </div>

            {isLoading ? (
                <div className="flex flex-col items-center justify-center py-20 animate-pulse">
                    <Loader2 className="h-12 w-12 animate-spin text-primary/40 mb-4" />
                    <p className="text-muted-foreground font-medium">Loading audience data...</p>
                </div>
            ) : filteredSegments.length === 0 ? (
                <div className="rounded-3xl border border-dashed border-border bg-card/40 backdrop-blur-sm p-20 text-center">
                    <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-2xl bg-muted/50 text-muted-foreground mb-6">
                        <Users className="h-10 w-10" />
                    </div>
                    <h3 className="text-2xl font-bold text-foreground">No segments found</h3>
                    <p className="mt-2 text-muted-foreground max-w-xs mx-auto">
                        {activeTab === 'active'
                            ? "Start organizing your contacts by creating your first audience segment."
                            : "Your archived segments will appear here."}
                    </p>
                    {activeTab === 'active' && (
                        <Link
                            href="/segments/new"
                            className="mt-8 inline-flex items-center justify-center rounded-xl text-sm font-bold transition-all bg-primary text-primary-foreground shadow-lg h-12 px-8"
                        >
                            <Plus className="mr-2 h-5 w-5" />
                            Launch First Segment
                        </Link>
                    )}
                </div>
            ) : (
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                    {filteredSegments.map((segment) => (
                        <Link
                            key={segment.id}
                            href={`/segments/${segment.id}`}
                            className="group relative rounded-3xl border border-border bg-card/60 backdrop-blur-sm p-6 shadow-sm transition-all hover:shadow-xl hover:border-primary/30 hover:-translate-y-1 flex flex-col h-full"
                        >
                            <div className="flex items-start justify-between mb-4">
                                <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl transition-transform group-hover:scale-110 ${getStatusColor(segment.status)}`}>
                                    <Users className="h-6 w-6" />
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-widest border ${getStatusColor(segment.status)}`}>
                                        {getStatusLabel(segment.status)}
                                    </span>
                                    <button
                                        onClick={(e) => handleDelete(e, segment)}
                                        className="p-2 text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-all rounded-lg opacity-0 group-hover:opacity-100"
                                        title="Delete Segment"
                                    >
                                        <Trash2 className="h-4 w-4" />
                                    </button>
                                </div>
                            </div>

                            <div className="space-y-1 mb-4 flex-1">
                                <h3 className="text-xl font-bold text-foreground group-hover:text-primary transition-colors">{segment.name}</h3>
                                {segment.description && (
                                    <p className="text-sm text-muted-foreground line-clamp-2">
                                        {segment.description}
                                    </p>
                                )}
                            </div>

                            <div className="pt-4 border-t border-border/50 flex items-center justify-between">
                                <div className="flex items-center gap-1.5 text-sm font-bold text-foreground">
                                    <Users className="h-4 w-4 text-primary/60" />
                                    {segment.contact_count.toLocaleString()}
                                    <span className="text-xs font-normal text-muted-foreground ml-1">Contacts</span>
                                </div>
                                <div className="p-2 rounded-lg bg-muted text-muted-foreground group-hover:bg-primary/10 group-hover:text-primary transition-all">
                                    <ArrowRight className="h-4 w-4" />
                                </div>
                            </div>
                        </Link>
                    ))}
                </div>
            )}
        </div>
    );
}
