'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api, Campaign } from '@/lib/api';
import { Plus, Mail, Trash2, Loader2, Calendar, Send } from 'lucide-react';
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

    const handleDelete = async (e: React.MouseEvent, id: string) => {
        e.preventDefault();
        if (!confirm('Are you sure you want to delete this campaign?')) return;

        try {
            await api.delete(`/campaigns/${id}`);
            toast.success('Campaign deleted');
            fetchCampaigns();
        } catch (error) {
            console.error('Failed to delete campaign:', error);
            toast.error('Failed to delete campaign');
        }
    };

    const [activeTab, setActiveTab] = useState<'active' | 'inactive'>('active');

    const filteredCampaigns = campaigns.filter(campaign => {
        if (activeTab === 'active') {
            return ['A'].includes(campaign.status);
        } else {
            return ['deleted'].includes(campaign.status);
        }
    });

    return (
        <div className="space-y-8">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-display font-bold tracking-tight">
                        Campaigns
                    </h1>
                    <p className="text-muted-foreground">
                        Manage and track your email campaigns
                    </p>
                </div>
                <Link
                    href="/campaigns/new"
                    className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow hover:bg-primary/90 h-9 px-4 py-2"
                >
                    <Plus className="mr-2 h-4 w-4" />
                    Create Campaign
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
                    onClick={() => setActiveTab('inactive')}
                    className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === 'inactive'
                        ? 'border-primary text-primary'
                        : 'border-transparent text-muted-foreground hover:text-foreground'
                        }`}
                >
                    Inactive
                </button>
            </div>

            {isLoading ? (
                <div className="flex justify-center p-8">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
            ) : filteredCampaigns.length === 0 ? (
                <div className="rounded-xl border border-border bg-card p-12 text-center">
                    <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-muted">
                        <Mail className="h-6 w-6 text-muted-foreground" />
                    </div>
                    <h3 className="mt-4 text-lg font-semibold">No {activeTab} campaigns</h3>
                    <p className="mt-2 text-sm text-muted-foreground">
                        {activeTab === 'active'
                            ? "Create a campaign to start reaching your audience."
                            : "No past campaigns found."}
                    </p>
                    {activeTab === 'active' && (
                        <Link
                            href="/campaigns/new"
                            className="mt-6 inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow hover:bg-primary/90 h-9 px-4 py-2"
                        >
                            Create Campaign
                        </Link>
                    )}
                </div>
            ) : (
                <div className="grid gap-4">
                    {filteredCampaigns.map((campaign) => (
                        <Link
                            key={campaign.id}
                            href={`/campaigns/${campaign.id}`}
                            className="group relative rounded-xl border border-border bg-card p-6 shadow-sm transition-all hover:shadow-md flex items-center justify-between block"
                        >
                            <div className="flex items-center gap-4">
                                <div className={`flex h-12 w-12 items-center justify-center rounded-full ${campaign.status === 'completed' ? 'bg-green-500/10 text-green-500' :
                                    campaign.type === 'S' ? 'bg-blue-500/10 text-blue-500' :
                                        'bg-yellow-500/10 text-yellow-500'
                                    }`}>
                                    {campaign.type === 'S' ? (
                                        <Calendar className="h-6 w-6" />
                                    ) : (
                                        <Send className="h-6 w-6" />
                                    )}
                                </div>
                                <div>
                                    <h3 className="font-semibold text-lg">{campaign.name}</h3>
                                    <div className="flex items-center gap-4 text-sm text-muted-foreground mt-1">
                                        <span className="flex items-center gap-1">
                                            <Mail className="h-3 w-3" />
                                            {campaign.email_subject}
                                        </span>
                                        <span>•</span>
                                        <span>{campaign.recipient_count || 0} recipients</span>
                                        <span>•</span>
                                        <span className="capitalize">{campaign.status}</span>
                                    </div>
                                </div>
                            </div>

                            <div className="flex items-center gap-2">
                                {campaign.schedule_at && (
                                    <div className="text-sm text-muted-foreground mr-4">
                                        Scheduled for: {new Date(campaign.schedule_at * 1000).toLocaleString()}
                                    </div>
                                )}
                                <button
                                    onClick={(e) => handleDelete(e, campaign.id)}
                                    className="opacity-0 group-hover:opacity-100 transition-opacity p-2 text-muted-foreground hover:text-destructive z-10 relative"
                                >
                                    <Trash2 className="h-4 w-4" />
                                </button>
                            </div>
                        </Link>
                    ))}
                </div>
            )}
        </div>
    );
}
