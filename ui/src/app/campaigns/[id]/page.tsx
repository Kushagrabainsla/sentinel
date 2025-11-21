'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { api, Campaign, CampaignEventsResponse } from '@/lib/api';
import { ArrowLeft, Calendar, Mail, Send, Users, Clock, CheckCircle2, AlertCircle, Activity, MailOpen, MousePointerClick } from 'lucide-react';
import { toast } from 'sonner';

export default function CampaignDetailsPage() {
    const params = useParams();
    const [campaign, setCampaign] = useState<Campaign | null>(null);
    const [stats, setStats] = useState<CampaignEventsResponse['summary'] | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchCampaign = async () => {
            try {
                const [campaignRes, eventsRes] = await Promise.all([
                    api.get(`/campaigns/${params.id}`),
                    api.get(`/campaigns/${params.id}/events`)
                ]);
                setCampaign(campaignRes.data.campaign);
                setStats(eventsRes.data.summary);
            } catch (error) {
                console.error('Failed to fetch campaign data:', error);
                toast.error('Failed to load campaign details');
            } finally {
                setIsLoading(false);
            }
        };

        if (params.id) {
            fetchCampaign();
        }
    }, [params.id]);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
        );
    }

    if (!campaign) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
                <AlertCircle className="h-12 w-12 text-destructive" />
                <h2 className="text-xl font-semibold">Campaign not found</h2>
                <Link href="/campaigns" className="text-primary hover:underline">
                    Back to Campaigns
                </Link>
            </div>
        );
    }

    return (
        <div className="space-y-8 max-w-5xl mx-auto">
            <div className="flex items-center gap-4">
                <Link
                    href="/campaigns"
                    className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground"
                >
                    <ArrowLeft className="h-4 w-4" />
                </Link>
                <div>
                    <h1 className="text-3xl font-display font-bold tracking-tight">
                        {campaign.name}
                    </h1>
                    <div className="flex items-center gap-2 text-muted-foreground mt-1">
                        <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${campaign.status === 'completed' ? 'bg-green-500/10 text-green-500' :
                            campaign.status === 'scheduled' ? 'bg-blue-500/10 text-blue-500' :
                                'bg-yellow-500/10 text-yellow-500'
                            }`}>
                            {campaign.status}
                        </span>
                        <span>•</span>
                        <span className="text-sm">ID: {campaign.id}</span>
                    </div>
                </div>
            </div>

            <div className="grid gap-6 md:grid-cols-3">
                <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
                    <div className="flex items-center gap-4">
                        <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                            <Users className="h-5 w-5" />
                        </div>
                        <div>
                            <p className="text-sm font-medium text-muted-foreground">Recipients</p>
                            <h3 className="text-2xl font-bold">{campaign.recipient_count || 0}</h3>
                        </div>
                    </div>
                </div>
                <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
                    <div className="flex items-center gap-4">
                        <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                            <Mail className="h-5 w-5" />
                        </div>
                        <div>
                            <p className="text-sm font-medium text-muted-foreground">Subject</p>
                            <h3 className="text-lg font-semibold truncate max-w-[200px]" title={campaign.email_subject}>
                                {campaign.email_subject}
                            </h3>
                        </div>
                    </div>
                </div>
                <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
                    <div className="flex items-center gap-4">
                        <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                            {campaign.type === 'S' ? (
                                <Calendar className="h-5 w-5" />
                            ) : (
                                <Send className="h-5 w-5" />
                            )}
                        </div>
                        <div>
                            <p className="text-sm font-medium text-muted-foreground">
                                {campaign.type === 'S' ? 'Scheduled For' : 'Sent At'}
                            </p>
                            <h3 className="text-sm font-semibold">
                                {campaign.schedule_at
                                    ? new Date(campaign.schedule_at * 1000).toLocaleString()
                                    : 'Immediately'}
                            </h3>
                        </div>
                    </div>
                </div>
            </div>

            <div className="grid gap-6 md:grid-cols-4 mb-8">
                <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
                    <div className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <h3 className="tracking-tight text-sm font-medium text-muted-foreground">Total Events</h3>
                        <Activity className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div className="text-2xl font-bold">{stats?.total_events || 0}</div>
                </div>
                <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
                    <div className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <h3 className="tracking-tight text-sm font-medium text-muted-foreground">Sent</h3>
                        <Send className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div className="text-2xl font-bold">{stats?.event_counts?.sent || 0}</div>
                </div>
                <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
                    <div className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <h3 className="tracking-tight text-sm font-medium text-muted-foreground">Opened</h3>
                        <MailOpen className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div className="text-2xl font-bold">{stats?.event_counts?.opened || 0}</div>
                </div>
                <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
                    <div className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <h3 className="tracking-tight text-sm font-medium text-muted-foreground">Clicked</h3>
                        <MousePointerClick className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div className="text-2xl font-bold">{stats?.event_counts?.clicked || 0}</div>
                </div>
            </div>

            <div className="rounded-xl border border-border bg-card shadow-sm overflow-hidden">
                <div className="border-b border-border bg-muted/40 px-6 py-4">
                    <h3 className="font-semibold">Email Content Preview</h3>
                </div>
                <div className="p-6 bg-white text-black min-h-[300px]">
                    {/* Warning: This is a simplified preview. In a real app, use a proper HTML sanitizer/renderer */}
                    <div className="prose max-w-none">
                        <p className="text-gray-500 italic text-sm mb-4">
                            Subject: {campaign.email_subject}
                        </p>
                        <hr className="my-4" />
                        <div className="mt-4" dangerouslySetInnerHTML={{ __html: campaign.email_body }} />
                    </div>
                </div>
            </div>
        </div>
    );
}
