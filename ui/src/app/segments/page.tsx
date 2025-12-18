'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api, Segment } from '@/lib/api';
import { Plus, Users, Trash2, Loader2 } from 'lucide-react';
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
        <div className="space-y-8">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-display font-bold tracking-tight">
                        Segments
                    </h1>
                    <p className="text-muted-foreground">
                        Manage your email lists and subscriber groups
                    </p>
                </div>
                <Link
                    href="/segments/new"
                    className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow hover:bg-primary/90 h-9 px-4 py-2"
                >
                    <Plus className="mr-2 h-4 w-4" />
                    Create Segment
                </Link>
            </div>

            <div className="flex items-center border-b border-border">
                <button
                    onClick={() => setActiveTab('active')}
                    className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === 'active'
                        ? 'border-primary text-primary'
                        : 'border-transparent text-muted-foreground hover:text-foreground'
                        }`}
                >
                    Active
                </button>
                <button
                    onClick={() => setActiveTab('trash')}
                    className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === 'trash'
                        ? 'border-primary text-primary'
                        : 'border-transparent text-muted-foreground hover:text-foreground'
                        }`}
                >
                    Trash
                </button>
            </div>

            {isLoading ? (
                <div className="flex justify-center p-8">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
            ) : filteredSegments.length === 0 ? (
                <div className="rounded-xl border border-border bg-card p-12 text-center">
                    <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-muted">
                        <Users className="h-6 w-6 text-muted-foreground" />
                    </div>
                    <h3 className="mt-4 text-lg font-semibold">No {activeTab} segments</h3>
                    <p className="mt-2 text-sm text-muted-foreground">
                        {activeTab === 'active'
                            ? "Create a segment to start organizing your contacts."
                            : "Your trash is empty."}
                    </p>
                    {activeTab === 'active' && (
                        <Link
                            href="/segments/new"
                            className="mt-6 inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow hover:bg-primary/90 h-9 px-4 py-2"
                        >
                            Create Segment
                        </Link>
                    )}
                </div>
            ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {filteredSegments.map((segment) => (
                        <Link
                            key={segment.id}
                            href={`/segments/${segment.id}`}
                            className="group relative rounded-xl border border-border bg-card p-6 shadow-sm transition-all hover:shadow-md"
                        >
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <div className={`flex h-10 w-10 items-center justify-center rounded-full ${getStatusColor(segment.status)}`}>
                                        <Users className="h-5 w-5" />
                                    </div>
                                    <div>
                                        <h3 className="font-semibold leading-none tracking-tight">{segment.name}</h3>
                                        <p className="text-sm text-muted-foreground mt-1">
                                            {segment.contact_count} contacts • <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getStatusColor(segment.status)}`}>{getStatusLabel(segment.status)}</span>
                                        </p>
                                    </div>
                                </div>
                                <button
                                    onClick={(e) => handleDelete(e, segment)}
                                    className="opacity-0 group-hover:opacity-100 transition-opacity p-2 text-muted-foreground hover:text-destructive"
                                >
                                    <Trash2 className="h-4 w-4" />
                                </button>
                            </div>
                            {segment.description && (
                                <p className="mt-4 text-sm text-muted-foreground line-clamp-2">
                                    {segment.description}
                                </p>
                            )}
                        </Link>
                    ))}
                </div>
            )}
        </div>
    );
}
