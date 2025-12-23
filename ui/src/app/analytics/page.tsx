'use client';

import { useState, useEffect } from 'react';
import { api, Campaign } from '@/lib/api';
import { AnalyticsCharts } from '@/app/campaigns/[id]/AnalyticsCharts';
import { Globe } from '@/components/ui/Globe';
import { Loader2, BarChart3, Globe2, Sparkles, CheckCircle2, AlertTriangle, Lightbulb, ArrowRight, ChevronDown } from 'lucide-react';
import { Dialog } from '@/components/ui/Dialog';
import { CampaignEventsResponse } from '@/lib/api';

interface InsightsReport {
    executive_summary: string;
    key_strengths: string[];
    areas_for_improvement: string[];
    actionable_recommendations: Array<{
        recommendation: string;
        example: string;
    }>;
}

// Fallback UI components if shadcn/ui components are not available
const SimpleSelect = ({ value, onChange, options, placeholder, className }: any) => (
    <div className="relative group/select">
        <select
            value={value}
            onChange={(e) => onChange(e.target.value)}
            className={`flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 pr-10 appearance-none cursor-pointer ${className}`}
        >
            <option value="" disabled>{placeholder}</option>
            {options.map((opt: any) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
        </select>
        <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none group-focus-within/select:text-primary transition-colors" />
    </div>
);

export default function AnalyticsPage() {
    const [campaigns, setCampaigns] = useState<Campaign[]>([]);
    const [selectedCampaignId, setSelectedCampaignId] = useState<string>('');
    const [timeRange, setTimeRange] = useState<'24h' | '7d' | '30d' | 'all'>('all');
    const [country, setCountry] = useState<string>('all');
    const [availableCountries, setAvailableCountries] = useState<string[]>([]);
    const [selectedVariation, setSelectedVariation] = useState<string>('all');
    const [isLoading, setIsLoading] = useState(true);
    const [summary, setSummary] = useState<CampaignEventsResponse['summary'] | undefined>(undefined);
    const [isGeneratingInsights, setIsGeneratingInsights] = useState(false);
    const [aiReport, setAiReport] = useState<InsightsReport | null>(null);
    const [isDialogOpen, setIsDialogOpen] = useState(false);

    const generateInsights = async () => {
        const campaign = campaigns.find(c => c.id === selectedCampaignId);
        if (!campaign || !summary) return;

        setIsGeneratingInsights(true);
        try {
            const response = await api.post('/generate-insights', {
                campaign,
                stats: summary
            });

            if (response.data.report) {
                setAiReport(response.data.report);
                setIsDialogOpen(true);
            }
        } catch (error) {
            console.error('Failed to generate insights:', error);
        } finally {
            setIsGeneratingInsights(false);
        }
    };

    // Get selected campaign details
    const selectedCampaign = campaigns.find(c => c.id === selectedCampaignId);
    const isABTest = selectedCampaign?.type === 'AB';

    // Reset variation filter when campaign changes
    useEffect(() => {
        setSelectedVariation('all');
    }, [selectedCampaignId]);

    useEffect(() => {
        const fetchCampaigns = async () => {
            try {
                const response = await api.get('/campaigns');
                const allCampaigns = response.data.campaigns || [];

                // Filter out Trash (I) and Deleted (D)
                const activeAndLive = allCampaigns.filter((c: Campaign) => {
                    const s = (c.status || "").toUpperCase();
                    return s !== 'I' && s !== 'D' && s !== 'INACTIVE' && s !== 'DELETED' && s !== 'TRASH';
                });

                setCampaigns(activeAndLive);
                if (activeAndLive.length > 0) {
                    setSelectedCampaignId(activeAndLive[0].id);
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
        <div className="max-w-6xl mx-auto space-y-10 pb-20">
            {/* Header Section */}
            {/* Header Section */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div>
                    <h1 className="text-4xl font-display font-bold tracking-tight text-foreground">
                        Analytics
                    </h1>
                    <p className="text-muted-foreground mt-1">
                        View performance metrics and insights for your campaigns
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <div className="px-4 py-2 rounded-xl bg-card border border-border shadow-sm flex items-center gap-3">
                        <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                        <span className="text-sm font-bold">Real-time Updates</span>
                    </div>
                </div>
            </div>

            <div className="grid gap-8">
                {/* Unified Control Panel */}
                <div className="group rounded-[2.5rem] bg-card border border-border shadow-2xl overflow-hidden relative transition-all hover:border-primary/20">
                    {/* Ambient Background Effect */}
                    <div className="absolute top-0 right-0 w-full h-full bg-gradient-to-br from-primary/5 via-transparent to-transparent pointer-events-none" />
                    <div className="absolute -bottom-24 -left-24 w-64 h-64 bg-primary/5 rounded-full blur-3xl pointer-events-none" />

                    <div className="relative p-10 flex flex-col lg:flex-row gap-12 items-stretch">
                        {/* Filters Section */}
                        <div className="flex-1 space-y-10 w-full z-10 flex flex-col justify-center">
                            <div>
                                <h2 className="text-3xl font-display font-bold text-foreground mb-3 flex items-center gap-3">
                                    <BarChart3 className="h-8 w-8 text-primary" />
                                    Filter Settings
                                </h2>
                                <p className="text-muted-foreground text-lg">Filter and refine your performance view.</p>
                            </div>

                            <div className="grid gap-8 sm:grid-cols-2">
                                <div className="space-y-3">
                                    <label className="text-xs font-bold text-muted-foreground uppercase tracking-[0.2em] ml-1">Context</label>
                                    <SimpleSelect
                                        value={selectedCampaignId}
                                        onChange={setSelectedCampaignId}
                                        options={campaigns.map(c => ({ value: c.id, label: c.name }))}
                                        placeholder="Select a campaign"
                                        className="h-14 bg-background/50 border-border rounded-2xl text-foreground focus:ring-primary/20 text-base font-medium"
                                    />
                                </div>
                                <div className="space-y-3">
                                    <label className="text-xs font-bold text-muted-foreground uppercase tracking-[0.2em] ml-1">Timeframe</label>
                                    <SimpleSelect
                                        value={timeRange}
                                        onChange={setTimeRange}
                                        options={[
                                            { value: '24h', label: 'Last 24 Hours' },
                                            { value: '7d', label: 'Last 7 Days' },
                                            { value: '30d', label: 'Last 30 Days' },
                                            { value: 'all', label: 'Historical' },
                                        ]}
                                        placeholder="Select time range"
                                        className="h-14 bg-background/50 border-border rounded-2xl text-foreground focus:ring-primary/20 text-base font-medium"
                                    />
                                </div>
                                {isABTest && (
                                    <div className="space-y-3 sm:col-span-2">
                                        <label className="text-xs font-bold text-muted-foreground uppercase tracking-[0.2em] ml-1">Variation Alpha/Beta</label>
                                        <SimpleSelect
                                            value={selectedVariation}
                                            onChange={setSelectedVariation}
                                            options={[
                                                { value: 'all', label: 'Aggregated Performance' },
                                                { value: 'A', label: 'Variation A' },
                                                { value: 'B', label: 'Variation B' },
                                                { value: 'C', label: 'Variation C' },
                                            ]}
                                            placeholder="Select variation"
                                            className="h-14 bg-background/50 border-border rounded-2xl text-foreground focus:ring-primary/20 text-base font-medium"
                                        />
                                    </div>
                                )}
                            </div>

                            <div className="p-1 pr-1 pl-6 rounded-2xl bg-primary/5 border border-primary/10 backdrop-blur-md flex items-center justify-between group/ai transition-all hover:bg-primary/10">
                                <div className="flex items-center gap-4 py-3">
                                    <div className="p-2.5 rounded-xl bg-primary/10 text-primary group-hover/ai:scale-110 transition-transform">
                                        <Sparkles className="h-6 w-6" />
                                    </div>
                                    <div>
                                        <h3 className="text-sm font-bold text-foreground">AI Intelligence Report</h3>
                                        <p className="text-xs text-muted-foreground">Analysis of current metrics</p>
                                    </div>
                                </div>
                                <button
                                    onClick={generateInsights}
                                    disabled={isGeneratingInsights || !summary}
                                    className="inline-flex items-center gap-2 px-6 py-4 rounded-xl bg-primary text-primary-foreground hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm font-bold active:scale-[0.98]"
                                >
                                    {isGeneratingInsights ? (
                                        <Loader2 className="h-5 w-5 animate-spin" />
                                    ) : (
                                        <Sparkles className="h-5 w-5" />
                                    )}
                                    {isGeneratingInsights ? 'Parsing Data...' : 'Generate Insights'}
                                </button>
                            </div>
                        </div>

                        {/* Globe Section */}
                        <div className="w-full lg:w-[460px] shrink-0 relative flex flex-col">
                            <div className="aspect-square w-full relative flex items-center justify-center rounded-[2rem] overflow-hidden bg-background/30 backdrop-blur-sm border border-border/50 shadow-inner">
                                <div className="absolute inset-0 bg-gradient-to-t from-card via-transparent to-transparent z-10 pointer-events-none" />
                                <Globe selectedCountry={country} onSelectCountry={setCountry} availableCountries={availableCountries} />
                            </div>
                            <div className="mt-4 text-center">
                                <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-muted/50 border border-border/50 text-[10px] font-bold text-muted-foreground uppercase tracking-[0.3em]">
                                    <Globe2 className="h-3 w-3" /> Area of Engagement
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Charts Section */}
                {selectedCampaignId ? (
                    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
                        <AnalyticsCharts
                            campaignId={selectedCampaignId}
                            campaign={campaigns.find(c => c.id === selectedCampaignId)}
                            timeRange={timeRange}
                            country={country}
                            variationFilter={isABTest && selectedVariation !== 'all' ? selectedVariation : undefined}
                            onAvailableCountriesChange={setAvailableCountries}
                            onDataLoaded={setSummary}
                        />
                    </div>
                ) : (
                    <div className="rounded-[2.5rem] border-2 border-dashed border-border bg-card/40 backdrop-blur-sm p-24 text-center">
                        <div className="mx-auto flex h-24 w-24 items-center justify-center rounded-3xl bg-muted/50 text-muted-foreground mb-8">
                            <BarChart3 className="h-12 w-12" />
                        </div>
                        <h3 className="text-2xl font-bold text-foreground">Awaiting Selection</h3>
                        <p className="mt-2 text-muted-foreground max-w-sm mx-auto text-lg leading-relaxed">
                            Pick a campaign from the settings above to visualize its performance trajectory.
                        </p>
                    </div>
                )}
            </div>

            <Dialog
                isOpen={isDialogOpen}
                onClose={() => setIsDialogOpen(false)}
                title="Intelligence Genesis Report"
                className="max-w-4xl rounded-[2rem]"
            >
                {aiReport && (
                    <div className="space-y-10 py-4">
                        {/* Executive Summary */}
                        <div className="p-8 rounded-3xl bg-gradient-to-br from-primary/10 via-background to-background border border-primary/20 shadow-lg relative overflow-hidden">
                            <div className="absolute top-0 right-0 p-4 opacity-10">
                                <Sparkles className="h-16 w-16" />
                            </div>
                            <h3 className="text-xl font-bold mb-4 flex items-center gap-3">
                                <Sparkles className="h-6 w-6 text-primary" />
                                Strategic Overview
                            </h3>
                            <p className="text-muted-foreground text-lg leading-relaxed font-outfit">
                                {aiReport.executive_summary}
                            </p>
                        </div>

                        <div className="grid gap-8 md:grid-cols-2">
                            {/* Strengths */}
                            <div className="group space-y-6">
                                <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-[0.2em] flex items-center gap-2 px-2">
                                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                                    Competitive Strengths
                                </h3>
                                <div className="space-y-4">
                                    {aiReport.key_strengths.map((strength, i) => (
                                        <div key={i} className="p-5 rounded-2xl bg-emerald-500/5 border border-emerald-500/10 text-base font-medium transition-all hover:bg-emerald-500/10">
                                            {strength}
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Improvements */}
                            <div className="group space-y-6">
                                <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-[0.2em] flex items-center gap-2 px-2">
                                    <div className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                                    Optimisation Nodes
                                </h3>
                                <div className="space-y-4">
                                    {aiReport.areas_for_improvement.map((area, i) => (
                                        <div key={i} className="p-5 rounded-2xl bg-amber-500/5 border border-amber-500/10 text-base font-medium transition-all hover:bg-amber-500/10">
                                            {area}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Recommendations */}
                        <div className="space-y-6">
                            <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-[0.2em] flex items-center gap-2 px-2">
                                <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                                Dynamic Tactics
                            </h3>
                            <div className="grid gap-6">
                                {aiReport.actionable_recommendations.map((rec, i) => (
                                    <div key={i} className="group p-6 rounded-[2rem] border border-border bg-card/60 hover:bg-card hover:shadow-xl transition-all hover:-translate-y-1">
                                        <div className="flex items-start gap-6">
                                            <div className="h-12 w-12 rounded-2xl bg-blue-500/10 flex items-center justify-center shrink-0 text-blue-500 font-black text-lg group-hover:bg-blue-500 transition-all group-hover:text-white group-hover:rotate-12">
                                                {i + 1}
                                            </div>
                                            <div className="space-y-4 flex-1">
                                                <h4 className="font-bold text-xl">{rec.recommendation}</h4>
                                                <div className="flex items-start gap-3 text-sm text-muted-foreground bg-muted/30 p-4 rounded-2xl border border-border/50">
                                                    <div className="mt-1 h-5 w-5 shrink-0 flex items-center justify-center rounded-full bg-primary/10 text-primary">
                                                        <ArrowRight className="h-3 w-3" />
                                                    </div>
                                                    <p className="leading-relaxed"><span className="font-bold text-foreground">Actionable Blueprint:</span> {rec.example}</p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="pt-6 text-center">
                            <button
                                onClick={() => setIsDialogOpen(false)}
                                className="px-10 py-4 bg-muted text-foreground font-bold rounded-2xl hover:bg-muted/80 transition-all border border-border/50"
                            >
                                Dismiss Transmission
                            </button>
                        </div>
                    </div>
                )}
            </Dialog>
        </div >
    );
}
