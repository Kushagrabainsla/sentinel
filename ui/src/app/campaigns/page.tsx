'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api, Campaign } from '@/lib/api';
import { Plus, Mail, Trash2, Loader2, Calendar, Send, Users, ArrowRight } from 'lucide-react';
import { toast } from 'sonner';

export default function CampaignsPage() {
    const [campaigns, setCampaigns] = useState<Campaign[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    const fetchCampaigns = async () => {
        try {
            const response = await api.get('/campaigns');
            setCampaigns(response.data.campaigns || []);
        } catch (error) {
            console.error('Failed to fetch campaigns:', error);
            toast.error('Failed to load campaigns');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchCampaigns();
    }, []);

    const handleDelete = async (e: React.MouseEvent, campaign: Campaign) => {
        e.preventDefault();
        const isTrash = campaign.status === 'I';
        const message = isTrash
            ? 'Are you sure you want to delete this campaign from trash? It will be permanently removed from your dashboard.'
            : 'Are you sure you want to move this campaign to trash?';

        if (!confirm(message)) return;

        try {
            await api.delete(`/campaigns/${campaign.id}`);
            toast.success(isTrash ? 'Campaign deleted permanently' : 'Campaign moved to trash');
            fetchCampaigns();
        } catch (error) {
            console.error('Failed to delete campaign:', error);
            toast.error('Failed to delete campaign');
        }
    };

    const [activeTab, setActiveTab] = useState<'active' | 'trash'>('active');

    const filteredCampaigns = campaigns.filter(campaign => {
        const status = (campaign.status || "").toLowerCase().trim();
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
            case 'COMPLETED': return 'Completed';
            case 'SENDING': return 'Sending';
            case 'SENT': return 'Sent';
            case 'SCHEDULED':
            case 'SC':
            case 'S': return 'Scheduled';
            default: return status;
        }
    };

    const getStatusColor = (status: string) => {
        const s = (status || "").trim().toUpperCase();
        if (['A', 'ACTIVE', 'COMPLETED', 'SENT'].includes(s)) return 'bg-green-500/10 text-green-500';
        if (['SENDING', 'SCHEDULED', 'SC', 'S'].includes(s)) return 'bg-blue-500/10 text-blue-500';
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
                        Campaigns
                    </h1>
                    <p className="text-muted-foreground mt-1">
                        Manage and track your email marketing performance
                    </p>
                </div>
                <Link
                    href="/campaigns/new"
                    className="inline-flex items-center justify-center rounded-xl text-sm font-bold transition-all hover:scale-[1.02] active:scale-[0.98] bg-primary text-primary-foreground shadow-lg h-12 px-8"
                >
                    <Plus className="mr-2 h-5 w-5" />
                    Create New Campaign
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
                    Active Campaigns
                </button>
                <button
                    onClick={() => setActiveTab('trash')}
                    className={`px-6 py-2.5 text-sm font-bold rounded-xl transition-all ${activeTab === 'trash'
                        ? 'bg-background text-primary shadow-sm'
                        : 'text-muted-foreground hover:text-foreground'
                        }`}
                >
                    Archive / Trash
                </button>
            </div>

            {isLoading ? (
                <div className="flex flex-col items-center justify-center py-20 animate-pulse">
                    <Loader2 className="h-12 w-12 animate-spin text-primary/40 mb-4" />
                    <p className="text-muted-foreground font-medium">Fetching campaigns...</p>
                </div>
            ) : filteredCampaigns.length === 0 ? (
                <div className="rounded-3xl border border-dashed border-border bg-card/40 backdrop-blur-sm p-20 text-center">
                    <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-2xl bg-muted/50 text-muted-foreground mb-6">
                        <Mail className="h-10 w-10" />
                    </div>
                    <h3 className="text-2xl font-bold text-foreground">No {activeTab} campaigns</h3>
                    <p className="mt-2 text-muted-foreground max-w-xs mx-auto">
                        {activeTab === 'active'
                            ? "You haven't created any campaigns yet. Let's get started!"
                            : "Your archive is currently empty."}
                    </p>
                    {activeTab === 'active' && (
                        <Link
                            href="/campaigns/new"
                            className="mt-8 inline-flex items-center justify-center rounded-xl text-sm font-bold transition-all bg-primary text-primary-foreground shadow-lg h-12 px-8"
                        >
                            <Plus className="mr-2 h-5 w-5" />
                            Launch First Campaign
                        </Link>
                    )}
                </div>
            ) : (
                <div className="grid gap-6">
                    {filteredCampaigns.map((campaign) => (
                        <Link
                            key={campaign.id}
                            href={`/campaigns/${campaign.id}`}
                            className="group relative rounded-3xl border border-border bg-card/60 backdrop-blur-sm p-6 shadow-sm transition-all hover:shadow-xl hover:border-primary/30 hover:-translate-y-1 block"
                        >
                            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                                <div className="flex items-start gap-5">
                                    <div className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl transition-transform group-hover:scale-110 ${getStatusColor(campaign.status)}`}>
                                        {campaign.type === 'S' ? (
                                            <Calendar className="h-7 w-7" />
                                        ) : (
                                            <Send className="h-7 w-7" />
                                        )}
                                    </div>
                                    <div className="space-y-1 min-w-0">
                                        <div className="flex items-center gap-3">
                                            <h3 className="font-bold text-xl text-foreground truncate">{campaign.name}</h3>
                                            <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-widest border ${getStatusColor(campaign.status)}`}>
                                                {getStatusLabel(campaign.status)}
                                            </span>
                                        </div>
                                        <p className="text-sm text-muted-foreground font-medium flex items-center gap-2">
                                            <Mail className="h-4 w-4 text-primary/60" />
                                            {campaign.email_subject}
                                        </p>
                                        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 pt-2">
                                            <div className="flex items-center gap-1.5 text-xs text-muted-foreground bg-muted/30 px-3 py-1.5 rounded-lg border border-border/50">
                                                <Users className="h-3.5 w-3.5" />
                                                <span className="font-bold text-foreground">{campaign.recipient_count || 0}</span> recipients
                                            </div>
                                            {campaign.schedule_at && (
                                                <div className="flex items-center gap-1.5 text-xs text-muted-foreground bg-muted/30 px-3 py-1.5 rounded-lg border border-border/50">
                                                    <Calendar className="h-3.5 w-3.5" />
                                                    <span className="text-foreground">
                                                        {new Date(campaign.schedule_at * 1000).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })}
                                                    </span>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                <div className="flex items-center justify-end gap-3 shrink-0">
                                    <button
                                        onClick={(e) => handleDelete(e, campaign)}
                                        className="p-3 text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-all rounded-xl border border-transparent hover:border-destructive/20"
                                        title={campaign.status === 'I' ? "Delete Permanently" : "Move to Trash"}
                                    >
                                        <Trash2 className="h-5 w-5" />
                                    </button>
                                    <div className="p-3 rounded-xl bg-muted/30 text-muted-foreground group-hover:bg-primary/10 group-hover:text-primary transition-all border border-transparent group-hover:border-primary/10">
                                        <ArrowRight className="h-6 w-6" />
                                    </div>
                                </div>
                            </div>
                        </Link>
                    ))}
                </div>
            )}
        </div>
    );
}
