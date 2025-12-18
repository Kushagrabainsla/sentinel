'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api, Campaign, Segment } from '@/lib/api';
import { Users, Mail, Plus, ArrowRight } from 'lucide-react';

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
                    emailsSent: campaigns.reduce((acc: number, curr: Campaign) =>
                        curr.status === 'completed' || curr.status === 'sent' || curr.status === 'D' ? acc + (curr.recipient_count || 0) : acc, 0)
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
        <div className="space-y-8">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-display font-bold tracking-tight">
                        Dashboard
                    </h1>
                    <p className="text-muted-foreground">
                        Welcome back, {userName}
                    </p>
                </div>
                <div className="flex gap-3">
                    <Link
                        href="/campaigns/new"
                        className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow hover:bg-primary/90 h-9 px-4 py-2"
                    >
                        <Plus className="mr-2 h-4 w-4" />
                        New Campaign
                    </Link>
                </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
                <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
                    <div className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <h3 className="tracking-tight text-sm font-medium text-muted-foreground">Active Campaigns</h3>
                        <Mail className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div className="text-2xl font-bold">{stats.campaigns}</div>
                </div>
                <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
                    <div className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <h3 className="tracking-tight text-sm font-medium text-muted-foreground">Active Segments</h3>
                        <Users className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div className="text-2xl font-bold">{stats.segments}</div>
                </div>
                <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
                    <div className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <h3 className="tracking-tight text-sm font-medium text-muted-foreground">Emails Sent</h3>
                        <Mail className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div className="text-2xl font-bold">{stats.emailsSent}</div>
                </div>
            </div>

            <div className="space-y-4">
                <div className="flex items-center justify-between">
                    <h2 className="text-xl font-semibold tracking-tight">Recent Campaigns</h2>
                    <Link href="/campaigns" className="text-sm text-primary hover:underline flex items-center">
                        View all <ArrowRight className="ml-1 h-4 w-4" />
                    </Link>
                </div>

                {recentCampaigns.length === 0 ? (
                    <div className="rounded-xl border border-border bg-card p-8 text-center text-muted-foreground">
                        No campaigns found. Create your first campaign to get started.
                    </div>
                ) : (
                    <div className="rounded-xl border border-border bg-card shadow-sm overflow-hidden">
                        <div className="relative w-full overflow-auto">
                            <table className="w-full caption-bottom text-sm">
                                <thead className="[&_tr]:border-b">
                                    <tr className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                                        <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Name</th>
                                        <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Status</th>
                                        <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Recipients</th>
                                        <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Schedule</th>
                                    </tr>
                                </thead>
                                <tbody className="[&_tr:last-child]:border-0">
                                    {recentCampaigns.map((campaign) => (
                                        <tr key={campaign.id} className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                                            <td className="p-4 align-middle font-medium">{campaign.name}</td>
                                            <td className="p-4 align-middle">
                                                <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 ${getStatusColor(campaign.status)}`}>
                                                    {getStatusLabel(campaign.status)}
                                                </span>
                                            </td>
                                            <td className="p-4 align-middle">{campaign.recipient_count || 0}</td>
                                            <td className="p-4 align-middle">
                                                {campaign.type === 'S' && campaign.schedule_at
                                                    ? new Date(campaign.schedule_at * 1000).toLocaleDateString()
                                                    : 'Immediate'}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
