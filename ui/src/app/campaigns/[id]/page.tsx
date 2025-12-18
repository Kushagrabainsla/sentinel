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

    // Calculate recipient count from stats if not available in campaign
    const recipientCount = campaign.recipient_count || stats?.event_counts?.sent || 0;
    const isABTest = campaign.type === 'AB';

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
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 px-2">
                <div className="flex items-start gap-6">
                    <Link
                        href="/campaigns"
                        className="flex h-12 w-12 items-center justify-center rounded-2xl bg-card border border-border shadow-sm hover:bg-primary/10 hover:text-primary transition-all group"
                    >
                        <ArrowLeft className="h-6 w-6 transition-transform group-hover:-translate-x-1" />
                    </Link>
                    <div className="space-y-1">
                        <div className="flex items-center gap-3">
                            <h1 className="text-4xl font-display font-bold tracking-tight text-foreground">
                                {campaign.name}
                            </h1>
                            <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-[10px] font-bold uppercase tracking-widest border ${getStatusColor(campaign.status)}`}>
                                <div className="w-1.5 h-1.5 rounded-full bg-current" />
                                {getStatusLabel(campaign.status)}
                            </span>
                        </div>
                        <div className="flex items-center gap-4 text-muted-foreground">
                            <span className="text-sm font-medium flex items-center gap-1.5">
                                <Clock className="h-4 w-4" />
                                ID: <span className="font-mono">{campaign.id.slice(0, 12)}</span>
                            </span>
                            {isABTest && (
                                <>
                                    <span className="text-muted-foreground/30">•</span>
                                    <span className="text-sm font-bold text-purple-500 bg-purple-500/10 px-2 py-0.5 rounded-lg flex items-center gap-1.5">
                                        <Activity className="h-3.5 w-3.5" />
                                        A/B Performance Test
                                    </span>
                                </>
                            )}
                        </div>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <Link
                        href={`/analytics?campaignId=${campaign.id}`}
                        className="inline-flex items-center justify-center rounded-xl text-sm font-bold transition-all hover:bg-muted bg-card border border-border h-11 px-6 shadow-sm"
                    >
                        Detailed Analytics
                    </Link>
                </div>
            </div>

            {/* Top Metrics Grid */}
            <div className="grid gap-6 md:grid-cols-3">
                {[
                    { label: 'Target Audience', value: recipientCount.toLocaleString(), icon: Users, sub: 'Total synchronized nodes', color: 'primary' },
                    { label: 'Primary Subject', value: campaign.email_subject, icon: Mail, sub: 'Neural message hook', color: 'purple' },
                    { label: campaign.type === 'S' ? 'Execution Queue' : 'Dispatch Profile', value: campaign.schedule_at ? new Date(campaign.schedule_at * 1000).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' }) : 'Immediate Launch', icon: campaign.type === 'S' ? Calendar : Send, sub: 'Temporal state', color: 'amber' }
                ].map((m, i) => (
                    <div key={i} className="group rounded-[2.5rem] border border-border bg-card/60 backdrop-blur-sm p-10 shadow-xl transition-all hover:border-primary/20 hover:-translate-y-1 overflow-hidden relative">
                        <div className="absolute top-0 right-0 p-8 opacity-5 pointer-events-none group-hover:scale-110 transition-transform">
                            <m.icon className="h-20 w-20" />
                        </div>
                        <div className="flex items-center justify-between mb-8">
                            <div className={`p-4 rounded-2xl bg-${m.color}-500/10 text-${m.color}-500`}>
                                <m.icon className="h-6 w-6" />
                            </div>
                        </div>
                        <div className="space-y-1">
                            <p className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em]">{m.label}</p>
                            <div className="text-3xl font-black tracking-tighter truncate" title={m.value}>{m.value}</div>
                            <p className="text-[10px] font-bold text-muted-foreground/60 uppercase tracking-widest">{m.sub}</p>
                        </div>
                    </div>
                ))}
            </div>

            {/* Engagement Funnel */}
            <div className="space-y-8">
                <div className="flex items-center gap-3 px-2">
                    <div className="w-1 h-6 bg-primary rounded-full" />
                    <h2 className="text-2xl font-black tracking-tight text-foreground uppercase">Transmission Telemetry</h2>
                </div>
                <div className="grid gap-6 grid-cols-2 lg:grid-cols-4">
                    {[
                        { label: 'Total Events', value: stats?.total_events || 0, icon: Activity, color: '#94a3b8' },
                        { label: 'Delivered', value: stats?.event_counts?.sent || 0, icon: Send, color: '#3b82f6' },
                        { label: 'Opened', value: stats?.event_counts?.open || 0, icon: MailOpen, color: '#10b981' },
                        { label: 'Clicked', value: stats?.event_counts?.click || 0, icon: MousePointerClick, color: '#8b5cf6' },
                    ].map((m, i) => (
                        <div key={i} className="rounded-[2rem] border border-border bg-card/60 backdrop-blur-sm p-8 flex flex-col items-center text-center group hover:bg-card hover:border-primary/20 transition-all hover:-translate-y-1 shadow-lg">
                            <div className="p-4 rounded-2xl bg-muted/40 text-foreground/80 mb-6 group-hover:scale-110 transition-transform border border-border/50" style={{ color: m.color }}>
                                <m.icon className="h-6 w-6" />
                            </div>
                            <div className="text-3xl font-black tracking-tighter mb-1 tabular-nums">{m.value.toLocaleString()}</div>
                            <div className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground opacity-60">{m.label}</div>

                            {/* Visual Progress Line */}
                            <div className="w-full h-1 bg-muted/20 rounded-full mt-6 overflow-hidden">
                                <div
                                    className="h-full bg-current opacity-40 rounded-full"
                                    style={{
                                        color: m.color,
                                        width: stats && stats.total_events > 0 ? `${(m.value / stats.total_events * 100)}%` : '0%'
                                    }}
                                />
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Content Preview Section */}
            <div className="space-y-6">
                <div className="flex items-center gap-3 px-2">
                    <div className="w-2 h-8 bg-primary rounded-full" />
                    <h2 className="text-2xl font-bold tracking-tight text-foreground">Creative Preview</h2>
                </div>
                <div className="rounded-[2.5rem] border border-border bg-card/60 backdrop-blur-sm shadow-xl overflow-hidden">
                    <div className="border-b border-border bg-muted/40 px-8 py-5 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <div className="flex gap-1.5 mr-4">
                                <div className="w-3 h-3 rounded-full bg-red-500/20" />
                                <div className="w-3 h-3 rounded-full bg-amber-500/20" />
                                <div className="w-3 h-3 rounded-full bg-emerald-500/20" />
                            </div>
                            <h3 className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Internal Content Display</h3>
                        </div>
                        <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                            <Mail className="h-3.5 w-3.5" />
                            Rendered Preview Mode
                        </div>
                    </div>
                    <div className="p-10 md:p-16 bg-white text-slate-900">
                        {isABTest && campaign.variations && campaign.variations.length > 0 ? (
                            <div className="space-y-12">
                                {campaign.variations.map((variation, index) => (
                                    <div key={`variation-${index}`} className="relative group/var">
                                        <div className="flex items-center gap-3 mb-6">
                                            <span className="inline-flex items-center rounded-xl px-4 py-1.5 text-xs font-black bg-purple-600 text-white shadow-lg shadow-purple-200">
                                                VARIATION {String.fromCharCode(65 + index)}
                                            </span>
                                            <span className="text-sm font-bold text-slate-400 uppercase tracking-widest">{variation.tone} tone</span>
                                        </div>
                                        <div className="bg-slate-50 rounded-3xl p-8 border border-slate-100 transition-all group-hover/var:border-primary/20">
                                            <div className="mb-6 flex items-start gap-3">
                                                <span className="text-xs font-black text-slate-300 uppercase mt-1">Subject</span>
                                                <p className="text-lg font-bold text-slate-700 tracking-tight">
                                                    {variation.subject}
                                                </p>
                                            </div>
                                            <div className="h-px bg-slate-200/60 mb-8" />
                                            <div className="prose prose-slate max-w-none prose-p:leading-relaxed prose-headings:font-display" dangerouslySetInnerHTML={{ __html: variation.content }} />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="max-w-3xl mx-auto space-y-8">
                                <div className="space-y-2">
                                    <span className="text-[10px] font-black text-slate-300 uppercase tracking-[0.2em]">Subject Focus</span>
                                    <h3 className="text-2xl font-display font-black text-slate-800 tracking-tight">
                                        {campaign.email_subject}
                                    </h3>
                                </div>
                                <div className="h-px bg-slate-200/60" />
                                <div className="prose prose-slate max-w-none prose-p:leading-relaxed prose-headings:font-display text-lg" dangerouslySetInnerHTML={{ __html: campaign.email_body }} />
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
