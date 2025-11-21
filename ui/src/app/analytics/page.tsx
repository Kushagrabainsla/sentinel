'use client';

import { useState, useEffect } from 'react';
import { api, Campaign } from '@/lib/api';
import { AnalyticsCharts } from '@/app/campaigns/[id]/AnalyticsCharts';
import { Loader2, BarChart3 } from 'lucide-react';

// Fallback UI components if shadcn/ui components are not available
const SimpleSelect = ({ value, onChange, options, placeholder }: any) => (
    <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
    >
        <option value="" disabled>{placeholder}</option>
        {options.map((opt: any) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
    </select>
);

export default function AnalyticsPage() {
    const [campaigns, setCampaigns] = useState<Campaign[]>([]);
    const [selectedCampaignId, setSelectedCampaignId] = useState<string>('');
    const [timeRange, setTimeRange] = useState<'24h' | '7d' | '30d' | 'all'>('all');
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchCampaigns = async () => {
            try {
                const response = await api.get('/campaigns');
                setCampaigns(response.data.campaigns);
                if (response.data.campaigns.length > 0) {
                    setSelectedCampaignId(response.data.campaigns[0].id);
                }
            } catch (error) {
                console.error('Failed to fetch campaigns:', error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchCampaigns();
    }, []);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    return (
        <div className="space-y-8">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                    <h1 className="text-3xl font-display font-bold tracking-tight">Analytics</h1>
                    <p className="text-muted-foreground">
                        View detailed performance metrics for your campaigns.
                    </p>
                </div>
            </div>

            <div className="flex flex-col gap-4 md:flex-row md:items-center bg-card p-4 rounded-lg border border-border shadow-sm">
                <div className="w-full md:w-[300px]">
                    <label className="text-sm font-medium mb-1 block text-muted-foreground">Select Campaign</label>
                    <SimpleSelect
                        value={selectedCampaignId}
                        onChange={setSelectedCampaignId}
                        options={campaigns.map(c => ({ value: c.id, label: c.name }))}
                        placeholder="Select a campaign"
                    />
                </div>
                <div className="w-full md:w-[200px]">
                    <label className="text-sm font-medium mb-1 block text-muted-foreground">Time Range</label>
                    <SimpleSelect
                        value={timeRange}
                        onChange={setTimeRange}
                        options={[
                            { value: '24h', label: 'Last 24 Hours' },
                            { value: '7d', label: 'Last 7 Days' },
                            { value: '30d', label: 'Last 30 Days' },
                            { value: 'all', label: 'All Time' },
                        ]}
                        placeholder="Select time range"
                    />
                </div>
            </div>

            {selectedCampaignId ? (
                <AnalyticsCharts campaignId={selectedCampaignId} timeRange={timeRange} />
            ) : (
                <div className="flex flex-col items-center justify-center h-[400px] border border-dashed border-border rounded-xl bg-muted/10">
                    <BarChart3 className="h-12 w-12 text-muted-foreground mb-4" />
                    <h3 className="text-lg font-semibold">No Campaign Selected</h3>
                    <p className="text-muted-foreground">Select a campaign to view analytics.</p>
                </div>
            )}
        </div>
    );
}
