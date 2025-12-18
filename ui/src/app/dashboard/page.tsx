'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api, Campaign, Segment } from '@/lib/api';
import { Users, Mail, Plus, ArrowRight, Send } from 'lucide-react';

export default function DashboardPage() {
    const [userName, setUserName] = useState('');
    const [stats, setStats] = useState({
        campaigns: 0,
        segments: 0,
        emailsSent: 0
    });
    const [recentCampaigns, setRecentCampaigns] = useState<Campaign[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const name = localStorage.getItem('sentinel_user_name');
        if (name) setUserName(name);

        const fetchData = async () => {
            try {
                const [campaignsRes, segmentsRes] = await Promise.all([
                    api.get('/campaigns'),
                    api.get('/segments')
                ]);

                const campaigns = campaignsRes.data.campaigns || [];
                const activeCampaigns = campaigns.filter((c: Campaign) => {
                    const s = (c.status || "").toLowerCase().trim();
                    return s !== 'i' && s !== 'inactive' && s !== 'trash' && s !== 'd' && s !== 'deleted';
                });

                const segments = segmentsRes.data.segments || [];
                const activeSegments = segments.filter((s: Segment) => {
                    const st = (s.status || "").toLowerCase().trim();
                    return st !== 'i' && st !== 'inactive' && st !== 'trash' && st !== 'd' && st !== 'deleted';
                });

                setStats({
                    campaigns: activeCampaigns.length,
                    segments: activeSegments.length,
                    // Sum recipient_count for all campaigns (excluding deleted/inactive/trash)
                    emailsSent: campaigns.reduce((acc: number, curr: Campaign) => {
                        const status = (curr.status || '').toLowerCase().trim();
                        // Exclude deleted, inactive, and trash campaigns (same logic as activeCampaigns filter)
                        if (status === 'i' || status === 'inactive' || status === 'trash' || status === 'd' || status === 'deleted') {
                            return acc;
                        }
                        return acc + (curr.recipient_count || 0);
                    }, 0)
                });

                setRecentCampaigns(campaigns.slice(0, 5));
            } catch (error) {
                console.error('Failed to fetch dashboard data:', error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchData();
    }, []);

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
            {/* Hero Welcome Section */}
            <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-primary/10 via-background to-background border border-border p-8 md:p-12 shadow-xl">
                <div className="absolute top-0 right-0 -mt-20 -mr-20 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />
                <div className="flex flex-col md:flex-row items-center justify-between gap-8 relative z-10">
                    <div className="space-y-4 text-center md:text-left">
                        <h1 className="text-4xl md:text-5xl font-display font-bold tracking-tight">
                            Welcome back, <span className="text-primary">{userName || 'Member'}</span>
                        </h1>
                        <p className="text-xl text-muted-foreground max-w-lg">
                            Your campaigns are performing well. You've reached <span className="text-foreground font-semibold">{stats.emailsSent.toLocaleString()}</span> recipients this month.
                        </p>
                        <div className="pt-4 flex flex-wrap items-center justify-center md:justify-start gap-4">
                            <Link
                                href="/campaigns/new"
                                className="inline-flex items-center justify-center rounded-xl text-sm font-bold transition-all hover:scale-[1.02] active:scale-[0.98] bg-primary text-primary-foreground shadow-lg h-12 px-8"
                            >
                                <Plus className="mr-2 h-5 w-5" />
                                Create New Campaign
                            </Link>
                            <Link
                                href="/analytics"
                                className="inline-flex items-center justify-center rounded-xl text-sm font-bold transition-all hover:bg-muted bg-background border border-input h-12 px-8 shadow-sm"
                            >
                                View Detailed Insights
                            </Link>
                        </div>
                    </div>
                    <div className="hidden lg:flex items-center justify-center w-48 h-48 rounded-full bg-gradient-to-tr from-primary/20 to-primary/5 border border-primary/20 animate-pulse">
                        <Mail className="w-20 h-20 text-primary opacity-60" />
                    </div>
                </div>
            </div>

            {/* Quick Stats Grid */}
            <div className="grid gap-6 md:grid-cols-3">
                <div className="group rounded-3xl border border-border bg-card/60 backdrop-blur-sm p-8 shadow-sm transition-all hover:shadow-md hover:border-primary/20">
                    <div className="flex items-center justify-between mb-4">
                        <div className="p-3 rounded-2xl bg-blue-500/10 text-blue-500 transition-colors group-hover:bg-blue-500/20">
                            <Mail className="h-6 w-6" />
                        </div>
                    </div>
                    <div className="space-y-1">
                        <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Active Campaigns</h3>
                        <div className="text-4xl font-display font-bold">{stats.campaigns}</div>
                    </div>
                </div>

                <div className="group rounded-3xl border border-border bg-card/60 backdrop-blur-sm p-8 shadow-sm transition-all hover:shadow-md hover:border-primary/20">
                    <div className="flex items-center justify-between mb-4">
                        <div className="p-3 rounded-2xl bg-purple-500/10 text-purple-500 transition-colors group-hover:bg-purple-500/20">
                            <Users className="h-6 w-6" />
                        </div>
                    </div>
                    <div className="space-y-1">
                        <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Audience Segments</h3>
                        <div className="text-4xl font-display font-bold">{stats.segments}</div>
                    </div>
                </div>

                <div className="group rounded-3xl border border-border bg-card/60 backdrop-blur-sm p-8 shadow-sm transition-all hover:shadow-md hover:border-primary/20">
                    <div className="flex items-center justify-between mb-4">
                        <div className="p-3 rounded-2xl bg-amber-500/10 text-amber-500 transition-colors group-hover:bg-amber-500/20">
                            <Send className="h-6 w-6" />
                        </div>
                    </div>
                    <div className="space-y-1">
                        <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Total Emails Sent</h3>
                        <div className="text-4xl font-display font-bold">{stats.emailsSent.toLocaleString()}</div>
                    </div>
                </div>
            </div>

            {/* Recent Campaigns Section */}
            <div className="space-y-6">
                <div className="flex items-center justify-between px-2">
                    <div className="flex items-center gap-3">
                        <div className="w-2 h-8 bg-primary rounded-full" />
                        <h2 className="text-2xl font-bold tracking-tight text-foreground">Recent Campaigns</h2>
                    </div>
                    <Link href="/campaigns" className="text-sm font-bold text-primary hover:underline flex items-center gap-2 group">
                        Manage All <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                    </Link>
                </div>

                {recentCampaigns.length === 0 ? (
                    <div className="rounded-3xl border border-dashed border-border bg-muted/30 p-12 text-center">
                        <div className="mx-auto w-16 h-16 bg-muted rounded-full flex items-center justify-center mb-4">
                            <Plus className="h-8 w-8 text-muted-foreground" />
                        </div>
                        <h3 className="text-lg font-semibold mb-2">No campaigns found</h3>
                        <p className="text-muted-foreground mb-6">Create your first campaign to start engaging with your audience.</p>
                        <Link
                            href="/campaigns/new"
                            className="inline-flex items-center justify-center rounded-xl text-sm font-bold transition-all bg-primary text-primary-foreground h-10 px-6"
                        >
                            Get Started
                        </Link>
                    </div>
                ) : (
                    <div className="rounded-3xl border border-border bg-card/40 backdrop-blur-sm shadow-sm overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="w-full text-left border-collapse">
                                <thead>
                                    <tr className="border-b border-border/50 bg-muted/20">
                                        <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-muted-foreground">Campaign Name</th>
                                        <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-muted-foreground">Status</th>
                                        <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-muted-foreground">Audience</th>
                                        <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-muted-foreground">Schedule</th>
                                        <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-muted-foreground"></th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-border/50">
                                    {recentCampaigns.map((campaign) => (
                                        <tr key={campaign.id} className="group transition-colors hover:bg-muted/30">
                                            <td className="px-6 py-5">
                                                <div className="font-bold text-foreground group-hover:text-primary transition-colors">{campaign.name}</div>
                                                <div className="text-xs text-muted-foreground">ID: {campaign.id.slice(0, 8)}...</div>
                                            </td>
                                            <td className="px-6 py-5">
                                                <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold uppercase tracking-widest border ${getStatusColor(campaign.status)}`}>
                                                    <span className="w-1.5 h-1.5 rounded-full bg-current" />
                                                    {getStatusLabel(campaign.status)}
                                                </span>
                                            </td>
                                            <td className="px-6 py-5 font-medium text-muted-foreground">
                                                <div className="flex items-center gap-2">
                                                    <Users className="w-4 h-4" />
                                                    {campaign.recipient_count || 0}
                                                </div>
                                            </td>
                                            <td className="px-6 py-5 text-sm text-muted-foreground">
                                                {campaign.type === 'S' && campaign.schedule_at
                                                    ? new Date(campaign.schedule_at * 1000).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })
                                                    : 'Immediate'}
                                            </td>
                                            <td className="px-6 py-5 text-right">
                                                <Link
                                                    href={`/campaigns/${campaign.id}`}
                                                    className="p-2 text-muted-foreground hover:text-primary hover:bg-primary/10 rounded-xl transition-all inline-block"
                                                >
                                                    <ArrowRight className="h-5 w-5" />
                                                </Link>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                        <div className="p-4 bg-muted/10 border-t border-border/50 text-center">
                            <p className="text-xs text-muted-foreground">Showing the 5 most recent campaigns. <Link href="/campaigns" className="text-primary font-bold hover:underline">View all</Link></p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
