'use client';

import { useEffect, useState, useRef, useMemo } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, AreaChart, Area, CartesianGrid } from 'recharts';
import { api, TemporalAnalytics, EngagementMetrics, RecipientInsights, DistributionItem, CampaignEventsResponse, Campaign } from '@/lib/api';
import { Loader2, Clock, Users, MousePointerClick, Zap, Globe, Monitor, Link as LinkIcon, Activity, MousePointer2 } from 'lucide-react';

interface AnalyticsChartsProps {
    campaignId: string;
    campaign?: Campaign;
    timeRange?: '24h' | '7d' | '30d' | 'all';
    country?: string;
    variationFilter?: string;
    onAvailableCountriesChange?: (countries: string[]) => void;
    onDataLoaded?: (summary: CampaignEventsResponse['summary']) => void;
    refreshTrigger?: number;
    onRefreshingChange?: (refreshing: boolean) => void;
}

const COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#f97316', '#10b981', '#06b6d4'];

const formatTime = (timestamp: number, timezone?: string): string => {
    const date = new Date(timestamp * 1000);
    const formatter = new Intl.DateTimeFormat('en-US', {
        timeZone: timezone || Intl.DateTimeFormat().resolvedOptions().timeZone,
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    });
    return formatter.format(date);
};

const formatHour = (hour: number): string => {
    const h = hour % 12 || 12;
    const period = hour < 12 ? 'AM' : 'PM';
    return `${h} ${period}`;
};

const formatDuration = (seconds: number): string => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    return `${Math.round(seconds / 60)}m`;
};

// Extracted UI Components for performance
const InsightCard = ({ title, value, icon: Icon, subtext }: { title: string, value: string | number, icon: any, subtext?: string }) => (
    <div className="group rounded-[2rem] border border-border bg-card p-8 shadow-xl transition-all hover:border-primary/20 hover:-translate-y-1 relative overflow-hidden">
        <div className="absolute top-0 right-0 p-6 opacity-[0.03] pointer-events-none group-hover:scale-110 transition-transform">
            <Icon className="h-20 w-20" />
        </div>
        <div className="flex items-start justify-between relative z-10">
            <div className="space-y-4">
                <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
                    <Icon className="h-5 w-5" />
                </div>
                <div>
                    <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">{title}</p>
                    <h3 className="text-3xl font-black mt-1 tracking-tight">{value}</h3>
                    {subtext && <p className="text-[10px] font-bold text-muted-foreground/60 mt-1 uppercase tracking-widest">{subtext}</p>}
                </div>
            </div>
        </div>
    </div>
);

const ChartCard = ({ title, subtitle, children, className }: { title: string, subtitle?: string, children: React.ReactNode, className?: string }) => (
    <div className={`group rounded-[2.5rem] border border-border bg-card p-10 shadow-xl transition-all hover:border-primary/20 ${className}`}>
        <div className="mb-8 flex items-start justify-between">
            <div>
                <h3 className="text-xl font-bold tracking-tight">{title}</h3>
                {subtitle && <p className="text-xs font-medium text-muted-foreground mt-1 uppercase tracking-widest opacity-60">{subtitle}</p>}
            </div>
        </div>
        <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
                {children}
            </ResponsiveContainer>
        </div>
    </div>
);

const EmptyPieChart = ({ message }: { message: string }) => (
    <PieChart>
        <Pie
            data={[{ name: 'empty', value: 1 }]}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={80}
            dataKey="value"
            stroke="none"
            fill="currentColor"
            className="text-muted/10"
        />
        <text
            x="50%"
            y="50%"
            textAnchor="middle"
            dominantBaseline="middle"
            className="fill-muted-foreground font-black uppercase tracking-[0.2em] text-[10px]"
        >
            {message}
        </text>
    </PieChart>
);

export function AnalyticsCharts({ campaignId, campaign, timeRange = 'all', country = 'all', variationFilter, onAvailableCountriesChange, onDataLoaded, refreshTrigger, onRefreshingChange }: AnalyticsChartsProps) {
    const [data, setData] = useState<{
        openData: { country: DistributionItem[]; };
        clickData: {
            os: DistributionItem[];
            device: DistributionItem[];
            browser: DistributionItem[];
            country: DistributionItem[];
        };
        temporal: TemporalAnalytics;
        engagement: EngagementMetrics;
        insights: RecipientInsights;
        summary?: CampaignEventsResponse['summary'];
    } | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isInternalRefreshing, setIsInternalRefreshing] = useState(false);
    const [userTimezone, setUserTimezone] = useState<string>(Intl.DateTimeFormat().resolvedOptions().timeZone);
    const lastRequestKey = useRef<string>('');

    // Fetch user timezone only once
    useEffect(() => {
        let isMounted = true;
        const fetchTimezone = async () => {
            try {
                const response = await api.get('/auth/me');
                if (isMounted && response.data?.user?.timezone) {
                    setUserTimezone(response.data.user.timezone);
                }
            } catch (error) {
                console.log('Using default browser timezone');
            }
        };
        fetchTimezone();
        return () => { isMounted = false; };
    }, []);

    useEffect(() => {
        let isMounted = true;

        const fetchData = async () => {
            const currentRequestKey = `${campaignId}-${timeRange}-${country}-${variationFilter}-${refreshTrigger}`;

            // Prevent redundant loads if the effect is triggered but parameters haven't really changed
            if (lastRequestKey.current === currentRequestKey && data) return;
            lastRequestKey.current = currentRequestKey;

            // Check if context changed (ignoring refreshTrigger) to show loader
            const contextChanged = !lastRequestKey.current.startsWith(currentRequestKey.split('-').slice(0, 4).join('-')) || !data;

            if (contextChanged) {
                setData(null);
                setIsLoading(true);
            }

            setIsInternalRefreshing(true);
            onRefreshingChange?.(true);

            try {
                // Buffer first visual context change slightly
                if (contextChanged) {
                    await new Promise(resolve => setTimeout(resolve, 200));
                }

                const now = Math.floor(Date.now() / 1000);
                let from_epoch = 0;
                switch (timeRange) {
                    case '24h': from_epoch = now - 86400; break;
                    case '7d': from_epoch = now - 604800; break;
                    case '30d': from_epoch = now - 2592000; break;
                    default: from_epoch = 0; break;
                }

                const params: any = {
                    from_epoch,
                    to_epoch: now,
                    limit: 1000,
                    ...(country && country !== 'all' ? { country_code: country } : {}),
                    ...(variationFilter ? { variation_id: variationFilter } : {})
                };

                const response = await api.get(`/campaigns/${campaignId}/events`, { params });

                if (!isMounted) return;

                const { distributions, events } = response.data;
                let temporal_analytics = response.data.temporal_analytics;
                let engagement_metrics = response.data.engagement_metrics;
                let recipient_insights = response.data.recipient_insights;

                if (!temporal_analytics && events) {
                    const { calculateTemporalAnalytics, calculateEngagementMetrics, calculateRecipientInsights } = await import('@/lib/analytics_utils');
                    temporal_analytics = calculateTemporalAnalytics(events);
                    engagement_metrics = calculateEngagementMetrics(events);
                    recipient_insights = calculateRecipientInsights(events);
                }

                if (distributions) {
                    const newData = {
                        openData: { country: distributions.open_data?.country_distribution || [] },
                        clickData: {
                            os: distributions.click_data?.os_distribution || [],
                            device: distributions.click_data?.device_distribution || [],
                            browser: distributions.click_data?.browser_distribution || [],
                            country: distributions.click_data?.country_distribution || []
                        },
                        temporal: temporal_analytics,
                        engagement: engagement_metrics,
                        insights: recipient_insights,
                        summary: response.data.summary
                    };

                    setData(newData);

                    if (onAvailableCountriesChange) {
                        const clickCountries = distributions.click_data?.country_distribution?.map((d: any) => d.name) || [];
                        const openCountries = distributions.open_data?.country_distribution?.map((d: any) => d.name) || [];
                        const allCountries = [...new Set([...clickCountries, ...openCountries])].filter(c => c && c !== 'Unknown');
                        if (allCountries.length > 0) onAvailableCountriesChange(allCountries);
                    }

                    if (response.data.summary && onDataLoaded) onDataLoaded(response.data.summary);
                }
            } catch (error) {
                console.error('Failed to fetch analytics:', error);
            } finally {
                if (isMounted) {
                    setIsLoading(false);
                    setIsInternalRefreshing(false);
                    onRefreshingChange?.(false);
                }
            }
        };

        if (campaignId) {
            fetchData();
        }

        return () => { isMounted = false; };
    }, [campaignId, timeRange, country, variationFilter, refreshTrigger, onAvailableCountriesChange, onDataLoaded, onRefreshingChange]);

    // Tooltip and Legend renderers (Memoized)
    const CustomTooltip = useMemo(() => ({ active, payload, label }: any) => {
        if (active && payload && payload.length) {
            const formattedLabel = label > 100 ? formatTime(label, userTimezone) : formatHour(label);
            return (
                <div className="bg-popover/90 backdrop-blur-xl border border-border p-4 rounded-2xl shadow-2xl min-w-[200px]">
                    <p className="text-xs font-black uppercase tracking-widest text-muted-foreground mb-3">{formattedLabel}</p>
                    <div className="space-y-2">
                        {payload.map((entry: any, index: number) => (
                            <div key={index} className="flex items-center justify-between gap-4 text-sm">
                                <div className="flex items-center gap-2">
                                    <div className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
                                    <span className="font-bold text-foreground/80">{entry.name}</span>
                                </div>
                                <span className="font-black tabular-nums">{entry.value}</span>
                            </div>
                        ))}
                    </div>
                </div>
            );
        }
        return null;
    }, [userTimezone]);

    const renderCustomLegend = useMemo(() => (props: any) => {
        const { payload } = props;
        const total = payload.reduce((acc: number, entry: any) => acc + (entry.payload?.value || 0), 0);
        return (
            <div className="flex flex-wrap justify-center gap-x-6 gap-y-3 mt-8 pt-6 pb-2 border-t border-border/40">
                {payload.map((entry: any, index: number) => {
                    const percentage = total > 0 ? ((entry.payload.value / total) * 100).toFixed(1) : '0';
                    return (
                        <div key={`item-${index}`} className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
                            <span className="text-[10px] font-black uppercase tracking-wider text-muted-foreground">{entry.value}</span>
                            <span className="text-xs font-black tabular-nums">
                                {entry.payload.value} <span className="text-muted-foreground ml-0.5 opacity-60">({percentage}%)</span>
                            </span>
                        </div>
                    );
                })}
            </div>
        );
    }, []);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-[400px]">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    if (!data) {
        return (
            <div className="flex items-center justify-center h-[400px] text-muted-foreground">
                No data available for this period
            </div>
        );
    }

    const segmentsData = [
        { name: 'Elite Engagers', value: data?.insights?.engagement_segments?.highly_engaged?.count || 0 },
        { name: 'Active Participants', value: data?.insights?.engagement_segments?.moderately_engaged?.count || 0 },
        { name: 'Passive Observers', value: data?.insights?.engagement_segments?.low_engaged?.count || 0 },
    ].filter(item => item.value > 0);

    return (
        <div className={`space-y-12 transition-opacity duration-500 ${isInternalRefreshing && !isLoading ? 'opacity-80' : 'opacity-100'}`}>
            <div className="grid gap-6 grid-cols-2 lg:grid-cols-4">
                <InsightCard
                    title="Optimal Send Window"
                    value={data.temporal.hourly_engagement.peak_hours.length > 0
                        ? `${formatHour(data.temporal.hourly_engagement.peak_hours[0])} - ${formatHour(data.temporal.hourly_engagement.peak_hours[0] + 1)}`
                        : 'N/A'}
                    icon={Clock}
                    subtext="Peak engagement detected"
                />
                <InsightCard
                    title="Interaction Score"
                    value={
                        data?.summary?.unique_clicks != null && data?.summary?.unique_opens != null && data.summary.unique_opens > 0
                            ? Number(((data.summary.unique_clicks * 250) / data.summary.unique_opens).toFixed(0))
                            : 0
                    }
                    icon={Zap}
                    subtext="Neural quality index"
                />
                <InsightCard
                    title="C-T-O Efficiency"
                    value={
                        data?.summary?.unique_clicks != null && data?.summary?.unique_opens != null && data.summary.unique_opens > 0
                            ? (data.summary.unique_clicks * 100 / data.summary.unique_opens).toFixed(1) + '%'
                            : '0%'
                    }
                    icon={MousePointerClick}
                    subtext="Convergence performance"
                />
                <InsightCard
                    title="Network Reach"
                    value={data?.insights?.unique_recipients || 0}
                    icon={Users}
                    subtext="Unique active connections"
                />
            </div>

            <div className="grid gap-10 lg:grid-cols-3">
                <ChartCard
                    title="Temporal Engagement Matrix"
                    subtitle={`Timezone: ${userTimezone}`}
                    className="lg:col-span-2"
                >
                    <AreaChart data={data.temporal.hourly_engagement.engagement_by_hour}>
                        <defs>
                            <linearGradient id="colorSent" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2} />
                                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                            </linearGradient>
                            <linearGradient id="colorOpens" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.2} />
                                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                            </linearGradient>
                            <linearGradient id="colorProxyOpens" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#f97316" stopOpacity={0.2} />
                                <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
                            </linearGradient>
                            <linearGradient id="colorClicks" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#ec4899" stopOpacity={0.2} />
                                <stop offset="95%" stopColor="#ec4899" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#374151" opacity={0.1} />
                        <XAxis dataKey="hour" stroke="#9ca3af" tick={false} axisLine={false} />
                        <YAxis stroke="#9ca3af" axisLine={false} tickLine={false} tick={{ fontSize: 10, fontWeight: 'bold' }} allowDecimals={false} />
                        <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'rgba(255,255,255,0.05)', strokeWidth: 2 }} />
                        <Legend
                            verticalAlign="top"
                            align="right"
                            height={36}
                            content={(props) => (
                                <div className="flex justify-end gap-6 mb-4">
                                    {props.payload?.map((entry: any, index: number) => (
                                        <div key={index} className="flex items-center gap-2">
                                            <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: entry.color }} />
                                            <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">{entry.value}</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        />
                        <Area type="monotone" dataKey="sent" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorSent)" name="Emails Sent" />
                        <Area type="monotone" dataKey="opens" stroke="#8b5cf6" strokeWidth={3} fillOpacity={1} fill="url(#colorOpens)" name="Human Opens" />
                        <Area type="monotone" dataKey="proxy_opens" stroke="#f97316" strokeWidth={2} fillOpacity={1} fill="url(#colorProxyOpens)" name="Proxy Opens" />
                        <Area type="monotone" dataKey="clicks" stroke="#ec4899" strokeWidth={3} fillOpacity={1} fill="url(#colorClicks)" name="Total Clicks" />
                    </AreaChart>
                </ChartCard>

                <ChartCard title="Audience Segmentation" subtitle="Strategic engagement sectors">
                    <PieChart>
                        <Pie
                            data={segmentsData}
                            cx="50%"
                            cy="50%"
                            innerRadius={70}
                            outerRadius={95}
                            paddingAngle={8}
                            dataKey="value"
                            stroke="none"
                        >
                            {segmentsData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                        </Pie>
                        <Tooltip content={<CustomTooltip />} />
                        <Legend content={renderCustomLegend} />
                    </PieChart>
                </ChartCard>
            </div>

            {data.summary && (
                <div className="group rounded-[2.5rem] border border-border bg-card p-10 shadow-xl transition-all hover:border-primary/20">
                    <div className="flex items-center gap-4 mb-10">
                        <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
                            <Zap className="h-5 w-5" />
                        </div>
                        <div>
                            <h3 className="text-2xl font-black tracking-tight">Transmission Summary</h3>
                            <p className="text-xs font-bold text-muted-foreground uppercase tracking-widest opacity-60">Complete campaign telemetry</p>
                        </div>
                    </div>
                    <div className="grid gap-8 grid-cols-2 md:grid-cols-3 lg:grid-cols-6 mb-12">
                        {[
                            { label: 'Total Events', value: data.summary.total_events, icon: Activity },
                            { label: 'Unique Opens', value: data.summary.unique_opens, icon: Globe },
                            { label: 'Unique Clicks', value: data.summary.unique_clicks, icon: MousePointerClick },
                            { label: 'Avg Time Open', value: data.summary.avg_time_to_open ? formatDuration(data.summary.avg_time_to_open) : 'N/A', icon: Clock },
                            { label: 'Avg Time Click', value: data.summary.avg_time_to_click ? formatDuration(data.summary.avg_time_to_click) : 'N/A', icon: MousePointerClick },
                            { label: 'Total Opens', value: data.summary.event_counts.open || 0, icon: Globe },
                        ].map((stat, i) => (
                            <div key={i} className="space-y-2 p-6 rounded-3xl bg-muted/30 border border-border/50 hover:bg-muted/50 transition-colors">
                                <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">{stat.label}</p>
                                <p className="text-2xl font-black tabular-nums tracking-tighter">{stat.value}</p>
                            </div>
                        ))}
                    </div>
                    {data.summary.event_types_breakdown && data.summary.event_types_breakdown.length > 0 && (
                        <div className="space-y-6 pt-10 border-t border-border/40">
                            <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-muted-foreground">Type Synchronicity</h4>
                            <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
                                {data.summary.event_types_breakdown.map((item) => (
                                    <div key={item.event_type} className="group/item flex items-center justify-between p-5 rounded-2xl bg-muted/20 border border-border/30 hover:border-primary/20 hover:bg-muted/40 transition-all">
                                        <div className="space-y-1">
                                            <p className="text-xs font-black uppercase tracking-widest opacity-80">{item.event_type}</p>
                                            <p className="text-[10px] font-bold text-primary">{item.percentage.toFixed(1)}%</p>
                                        </div>
                                        <p className="text-2xl font-black tabular-nums">{item.count}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}

            <div className="group rounded-[2.5rem] border border-border bg-card p-10 shadow-xl transition-all hover:border-primary/20">
                <div className="flex items-center gap-4 mb-10">
                    <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
                        <MousePointer2 className="h-5 w-5" />
                    </div>
                    <div>
                        <h3 className="text-2xl font-black tracking-tight">Environment Analytics</h3>
                        <p className="text-xs font-bold text-muted-foreground uppercase tracking-widest opacity-60">Terminal and platform distribution</p>
                    </div>
                </div>
                <div className="grid gap-10 grid-cols-1 lg:grid-cols-3 mb-12">
                    {[
                        { title: 'Device Matrix', data: data.clickData.device, subtitle: 'Hardware distribution' },
                        { title: 'Browser Matrix', data: data.clickData.browser, subtitle: 'Application distribution' },
                        { title: 'OS Matrix', data: data.clickData.os, subtitle: 'System distribution' },
                    ].map((chart, i) => (
                        <div key={i} className="space-y-6">
                            <div className="h-[320px]">
                                {chart.data.length > 0 ? (
                                    <ResponsiveContainer width="100%" height="100%">
                                        <PieChart>
                                            <Pie
                                                data={chart.data}
                                                cx="50%"
                                                cy="50%"
                                                innerRadius={65}
                                                outerRadius={85}
                                                paddingAngle={6}
                                                dataKey="value"
                                                stroke="none"
                                            >
                                                {chart.data.map((entry: any, index: number) => (
                                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                                ))}
                                            </Pie>
                                            <Tooltip content={<CustomTooltip />} />
                                            <Legend content={renderCustomLegend} />
                                        </PieChart>
                                    </ResponsiveContainer>
                                ) : (
                                    <ResponsiveContainer width="100%" height="100%">
                                        <EmptyPieChart message="Insufficient Data" />
                                    </ResponsiveContainer>
                                )}
                            </div>
                            <div className="text-center pt-2">
                                <h4 className="text-sm font-bold uppercase tracking-widest">{chart.title}</h4>
                                <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest opacity-60">{chart.subtitle}</p>
                            </div>
                        </div>
                    ))}
                </div>
                <div className="pt-10 border-t border-border/40">
                    <div className="flex items-center gap-3 mb-8">
                        <LinkIcon className="h-4 w-4 text-primary" />
                        <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-muted-foreground">High-Interaction Links</h4>
                    </div>
                    {data.summary?.top_clicked_links && data.summary.top_clicked_links.length > 0 ? (
                        <div className="grid gap-4 grid-cols-1">
                            {data.summary.top_clicked_links.map((link: any, index: number) => (
                                <div key={index} className="group/link flex items-center justify-between p-6 rounded-2xl bg-muted/10 border border-border/40 hover:bg-muted/20 hover:border-primary/20 transition-all">
                                    <div className="flex-1 min-w-0 mr-4">
                                        <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground mb-1">Dest: {index + 1}</p>
                                        <p className="text-sm font-bold truncate text-foreground group-hover/link:text-primary transition-colors" title={link.url}>
                                            {link.url}
                                        </p>
                                    </div>
                                    <div className="shrink-0 text-right">
                                        <p className="text-2xl font-black tabular-nums">{link.clicks}</p>
                                        <p className="text-[10px] font-black uppercase tracking-widest opacity-40">Clicks</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center p-12 rounded-[2rem] bg-muted/5 border border-dashed border-border/50">
                            <LinkIcon className="h-8 w-8 text-muted-foreground/30 mb-4" />
                            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground opacity-60">No Link Interaction Data Available</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
