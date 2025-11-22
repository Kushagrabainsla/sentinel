'use client';

import { useState, useEffect } from 'react';
import { api, Campaign } from '@/lib/api';
import { AnalyticsCharts } from '@/app/campaigns/[id]/AnalyticsCharts';
import { Globe } from '@/components/ui/Globe';
import { Loader2, BarChart3, Globe2 } from 'lucide-react';

// Fallback UI components if shadcn/ui components are not available
const SimpleSelect = ({ value, onChange, options, placeholder, className }: any) => (
    <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${className}`}
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
    const [country, setCountry] = useState<string>('all');
    const [availableCountries, setAvailableCountries] = useState<string[]>([]);
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



    // ...

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

            <div className="grid gap-6">
                {/* Unified Control Panel */}
                <div className="bg-zinc-950 rounded-3xl border border-zinc-800 shadow-2xl overflow-hidden relative">
                    {/* Ambient Background Effect */}
                    <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-blue-500/10 rounded-full blur-3xl pointer-events-none -translate-y-1/2 translate-x-1/2" />

                    <div className="relative p-8 flex flex-col lg:flex-row gap-12 items-center">
                        {/* Filters Section */}
                        <div className="flex-1 space-y-8 w-full z-10">
                            <div>
                                <h2 className="text-2xl font-display font-bold text-white mb-2">Campaign Settings</h2>
                                <p className="text-zinc-400">Select a campaign and time period to analyze performance.</p>
                            </div>

                            <div className="grid gap-6 sm:grid-cols-2">
                                <div className="space-y-2">
                                    <label className="text-xs font-medium text-zinc-500 uppercase tracking-wider">Select Campaign</label>
                                    <div className="relative">
                                        <SimpleSelect
                                            value={selectedCampaignId}
                                            onChange={setSelectedCampaignId}
                                            options={campaigns.map(c => ({ value: c.id, label: c.name }))}
                                            placeholder="Select a campaign"
                                            className="bg-zinc-900/50 border-zinc-800 text-zinc-100 focus:ring-blue-500/50"
                                        />
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <label className="text-xs font-medium text-zinc-500 uppercase tracking-wider">Time Range</label>
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
                                        className="bg-zinc-900/50 border-zinc-800 text-zinc-100 focus:ring-blue-500/50"
                                    />
                                </div>
                            </div>

                            <div className="flex items-center gap-4 p-4 rounded-xl bg-zinc-900/30 border border-zinc-800/50 backdrop-blur-sm">
                                <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400">
                                    <Globe2 className="h-5 w-5" />
                                </div>
                                <div>
                                    <h3 className="text-sm font-medium text-zinc-200">Geographic Filter Active</h3>
                                    <p className="text-xs text-zinc-500 mt-0.5">
                                        Viewing data for: <span className="font-semibold text-white">{country === 'all' ? 'Global' : country}</span>
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Globe Section */}
                        <div className="w-full lg:w-[500px] shrink-0 relative">
                            <div className="aspect-square w-full relative flex items-center justify-center">
                                <div className="absolute inset-0 bg-gradient-to-t from-zinc-950 via-transparent to-transparent z-10 pointer-events-none" />
                                <Globe selectedCountry={country} onSelectCountry={setCountry} availableCountries={availableCountries} />
                            </div>
                            <div className="absolute bottom-0 left-0 right-0 text-center pb-4 z-20 pointer-events-none">
                                <p className="text-xs text-zinc-600 font-medium tracking-widest uppercase">Interactive Global View</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Charts Section */}
                {selectedCampaignId ? (
                    <AnalyticsCharts
                        campaignId={selectedCampaignId}
                        timeRange={timeRange}
                        country={country}
                        onAvailableCountriesChange={setAvailableCountries}
                    />
                ) : (
                    <div className="flex flex-col items-center justify-center h-[400px] border border-dashed border-border rounded-xl bg-muted/10">
                        <BarChart3 className="h-12 w-12 text-muted-foreground mb-4" />
                        <h3 className="text-lg font-semibold">No Campaign Selected</h3>
                        <p className="text-muted-foreground">Select a campaign to view analytics.</p>
                    </div>
                )}
            </div>
        </div >
    );
}
