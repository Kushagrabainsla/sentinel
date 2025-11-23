'use client';

import { useEffect, useState } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, AreaChart, Area, CartesianGrid } from 'recharts';
import { api, TemporalAnalytics, EngagementMetrics, RecipientInsights, DistributionItem, CampaignEventsResponse, Campaign } from '@/lib/api';
import { Loader2, Clock, Users, MousePointerClick, Zap } from 'lucide-react';



interface AnalyticsChartsProps {
    campaignId: string;
    campaign?: Campaign;
    timeRange?: '24h' | '7d' | '30d' | 'all';
    country?: string;
    onAvailableCountriesChange?: (countries: string[]) => void;
    onDataLoaded?: (summary: CampaignEventsResponse['summary']) => void;
}


const COLORS = ['#2563eb', '#0891b2', '#7c3aed', '#db2777', '#ea580c', '#16a34a'];

// Helper function to format hour in 12-hour format with AM/PM
const formatHour = (hour: number): string => {
    const h = hour % 12 || 12;
    const period = hour < 12 ? 'AM' : 'PM';
    return `${h} ${period}`;
};

// ... (existing imports)

export function AnalyticsCharts({ campaignId, campaign, timeRange = 'all', country = 'all', onAvailableCountriesChange, onDataLoaded }: AnalyticsChartsProps) {
    const [data, setData] = useState<{
        os: DistributionItem[];
        device: DistributionItem[];
        browser: DistributionItem[];
        geo: DistributionItem[];
        temporal: TemporalAnalytics;
        engagement: EngagementMetrics;
        insights: RecipientInsights;
        summary?: CampaignEventsResponse['summary'];
    } | null>(null);
    const [isLoading, setIsLoading] = useState(true);


    useEffect(() => {
        const fetchData = async () => {
            setIsLoading(true);
            try {
                // Simulate network delay
                await new Promise(resolve => setTimeout(resolve, 500));

                // Real API Call Logic
                const now = Math.floor(Date.now() / 1000);
                let from_epoch = 0;

                switch (timeRange) {
                    case '24h':
                        from_epoch = now - 86400;
                        break;
                    case '7d':
                        from_epoch = now - 604800;
                        break;
                    case '30d':
                        from_epoch = now - 2592000;
                        break;
                    case 'all':
                    default:
                        from_epoch = 0;
                        break;
                }

                const params: any = {
                    from_epoch,
                    to_epoch: now,
                    limit: 1000
                };

                if (country && country !== 'all') {
                    params.country_code = country;
                }

                const response = await api.get(`/campaigns/${campaignId}/events`, { params });
                const { distributions, events } = response.data;

                // Calculate metrics client-side if not provided by backend
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
                    setData({
                        os: distributions.os_distribution,
                        device: distributions.device_distribution,
                        browser: distributions.browser_distribution,
                        geo: distributions.ip_distribution,
                        temporal: temporal_analytics,
                        engagement: engagement_metrics,
                        insights: recipient_insights,
                        summary: response.data.summary
                    });

                    // Extract available countries
                    if (distributions.country_distribution && onAvailableCountriesChange) {
                        const countries = distributions.country_distribution.map((d: any) => d.name);
                        onAvailableCountriesChange(countries);
                    }

                    // Pass summary data to parent
                    if (response.data.summary && onDataLoaded) {
                        onDataLoaded(response.data.summary);
                    }
                }
            } catch (error) {
                console.error('Failed to fetch analytics:', error);
            } finally {
                setIsLoading(false);
            }
        };

        if (campaignId) {
            fetchData();
        }
    }, [campaignId, timeRange, country]);

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

    const InsightCard = ({ title, value, icon: Icon, subtext }: { title: string, value: string | number, icon: any, subtext?: string }) => (
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm flex items-start justify-between">
            <div>
                <p className="text-sm font-medium text-muted-foreground">{title}</p>
                <h3 className="text-2xl font-bold mt-2">{value}</h3>
                {subtext && <p className="text-xs text-muted-foreground mt-1">{subtext}</p>}
            </div>
            <div className="p-3 rounded-lg bg-primary/10 text-primary">
                <Icon className="h-5 w-5" />
            </div>
        </div>
    );

    const ChartCard = ({ title, subtitle, children }: { title: string, subtitle?: string, children: React.ReactNode }) => (
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
            <div className="mb-6">
                <h3 className="text-lg font-semibold">{title}</h3>
                {subtitle && <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>}
            </div>
            <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                    {children}
                </ResponsiveContainer>
            </div>
        </div>
    );

    const CustomTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length) {
            // Format the label if it's a number (hour)
            const formattedLabel = typeof label === 'number' ? formatHour(label) : label;

            return (
                <div className="bg-popover border border-border p-3 rounded-lg shadow-lg">
                    <p className="font-medium mb-2">{formattedLabel}</p>
                    {payload.map((entry: any, index: number) => (
                        <div key={index} className="flex items-center gap-2 text-sm">
                            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
                            <span className="text-muted-foreground capitalize">{entry.name}:</span>
                            <span className="font-medium">{entry.value}</span>
                        </div>
                    ))}
                </div>
            );
        }
        return null;
    };

    // Prepare user segments data
    const segmentsData = [
        { name: 'Highly Engaged', value: data.insights.engagement_segments.highly_engaged.count },
        { name: 'Moderately Engaged', value: data.insights.engagement_segments.moderately_engaged.count },
        { name: 'Low Engagement', value: data.insights.engagement_segments.low_engaged.count },
    ].filter(item => item.value > 0);

    return (
        <div className="space-y-6">
            {/* Key Insights Grid */}
            <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
                <InsightCard
                    title="Optimal Send Time"
                    value={data.temporal.hourly_engagement.peak_hours.length > 0
                        ? `${formatHour(data.temporal.hourly_engagement.peak_hours[0])} - ${formatHour(data.temporal.hourly_engagement.peak_hours[0] + 1)}`
                        : 'N/A'}
                    icon={Clock}
                    subtext="Based on open rates"
                />
                <InsightCard
                    title="Engagement Score"
                    value={data.engagement.engagement_quality_score}
                    icon={Zap}
                    subtext="Quality of interactions"
                />
                <InsightCard
                    title="Click-to-Open Rate"
                    value={`${Number(data.engagement.click_to_open_rate).toFixed(3)}%`}
                    icon={MousePointerClick}
                    subtext="Effectiveness of content"
                />
                <InsightCard
                    title="Unique Recipients"
                    value={data.insights.unique_recipients}
                    icon={Users}
                    subtext="Total reach"
                />
            </div>

            {/* Summary Stats Section */}
            {data.summary && (
                <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
                    <h3 className="text-lg font-semibold mb-4">Campaign Summary</h3>
                    <div className="grid gap-4 grid-cols-2 md:grid-cols-3 lg:grid-cols-6">
                        <div className="space-y-1">
                            <p className="text-xs text-muted-foreground">Total Events</p>
                            <p className="text-2xl font-bold">{data.summary.total_events}</p>
                        </div>
                        <div className="space-y-1">
                            <p className="text-xs text-muted-foreground">Unique Opens</p>
                            <p className="text-2xl font-bold">{data.summary.unique_opens}</p>
                        </div>
                        <div className="space-y-1">
                            <p className="text-xs text-muted-foreground">Unique Clicks</p>
                            <p className="text-2xl font-bold">{data.summary.unique_clicks}</p>
                        </div>
                        <div className="space-y-1">
                            <p className="text-xs text-muted-foreground">Avg Time to Open</p>
                            <p className="text-2xl font-bold">
                                {data.summary.avg_time_to_open !== null
                                    ? `${Math.round(data.summary.avg_time_to_open)}m`
                                    : 'N/A'}
                            </p>
                        </div>
                        <div className="space-y-1">
                            <p className="text-xs text-muted-foreground">Avg Time to Click</p>
                            <p className="text-2xl font-bold">
                                {data.summary.avg_time_to_click !== null
                                    ? `${Math.round(data.summary.avg_time_to_click)}m`
                                    : 'N/A'}
                            </p>
                        </div>
                        <div className="space-y-1">
                            <p className="text-xs text-muted-foreground">Opens</p>
                            <p className="text-2xl font-bold">{data.summary.event_counts.open || 0}</p>
                        </div>
                    </div>

                    {/* Event Type Breakdown */}
                    {data.summary.event_types_breakdown && data.summary.event_types_breakdown.length > 0 && (
                        <div className="mt-6">
                            <h4 className="text-sm font-medium mb-3">Event Type Breakdown</h4>
                            <div className="grid gap-3 grid-cols-2 md:grid-cols-4">
                                {data.summary.event_types_breakdown.map((item) => (
                                    <div key={item.event_type} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                                        <div>
                                            <p className="text-sm font-medium capitalize">{item.event_type}</p>
                                            <p className="text-xs text-muted-foreground">{item.percentage.toFixed(1)}%</p>
                                        </div>
                                        <p className="text-lg font-bold">{item.count}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}




            {/* Advanced Charts Row 1 */}
            <div className="grid gap-6 grid-cols-1 lg:grid-cols-3">
                <div className="lg:col-span-2">
                    <ChartCard
                        title="Hourly Engagement Pattern"
                        subtitle={`Times shown in ${Intl.DateTimeFormat().resolvedOptions().timeZone} timezone`}
                    >
                        <AreaChart data={data.temporal.hourly_engagement.engagement_by_hour}>
                            <defs>
                                <linearGradient id="colorOpens" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#2563eb" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#374151" />
                            <XAxis
                                dataKey="hour"
                                tickFormatter={(val) => {
                                    // Convert 24-hour format to 12-hour format with AM/PM
                                    // Data is already in user's local timezone
                                    const hour = val % 12 || 12;
                                    const period = val < 12 ? 'AM' : 'PM';
                                    return `${hour} ${period}`;
                                }}
                                stroke="#9ca3af"
                            />
                            <YAxis stroke="#9ca3af" />
                            <Tooltip content={<CustomTooltip />} />
                            <Area type="monotone" dataKey="opens" stroke="#2563eb" fillOpacity={1} fill="url(#colorOpens)" name="Opens" />
                        </AreaChart>
                    </ChartCard>
                </div>
                <div>
                    <ChartCard title="User Segmentation">


                        <PieChart>
                            <Pie
                                data={segmentsData}
                                cx="50%"
                                cy="50%"
                                innerRadius={60}
                                outerRadius={80}
                                paddingAngle={5}
                                dataKey="value"
                            >
                                {segmentsData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip content={<CustomTooltip />} />
                            <Legend />
                        </PieChart>
                    </ChartCard>
                </div>
            </div>

            {/* Distribution Charts Row 2 */}
            <div className="grid gap-6 grid-cols-1 md:grid-cols-2">
                <ChartCard title="Device Distribution">
                    <PieChart>
                        <Pie
                            data={data.device}
                            cx="50%"
                            cy="50%"
                            innerRadius={60}
                            outerRadius={80}
                            paddingAngle={5}
                            dataKey="value"
                        >
                            {data.device.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                        </Pie>
                        <Tooltip content={<CustomTooltip />} />
                        <Legend />
                    </PieChart>
                </ChartCard>
                <ChartCard title="Browser Distribution">
                    <PieChart>
                        <Pie
                            data={data.browser}
                            cx="50%"
                            cy="50%"
                            innerRadius={60}
                            outerRadius={80}
                            paddingAngle={5}
                            dataKey="value"
                        >
                            {data.browser.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                        </Pie>
                        <Tooltip content={<CustomTooltip />} />
                        <Legend />
                    </PieChart>
                </ChartCard>
            </div>
        </div >
    );
}
