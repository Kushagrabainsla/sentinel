'use client';

import { useEffect, useState } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, AreaChart, Area, CartesianGrid } from 'recharts';
import { api, TemporalAnalytics, EngagementMetrics, RecipientInsights, DistributionItem, CampaignEventsResponse, Campaign } from '@/lib/api';
import { Loader2, Clock, Users, MousePointerClick, Zap, Globe, Monitor, Link as LinkIcon } from 'lucide-react';



interface AnalyticsChartsProps {
    campaignId: string;
    campaign?: Campaign;
    timeRange?: '24h' | '7d' | '30d' | 'all';
    country?: string;
    variationFilter?: string;
    onAvailableCountriesChange?: (countries: string[]) => void;
    onDataLoaded?: (summary: CampaignEventsResponse['summary']) => void;
}


const COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#f97316', '#10b981', '#06b6d4'];

// Helper function to format timestamp to date and time with user timezone
const formatTime = (timestamp: number, timezone?: string): string => {
    const date = new Date(timestamp * 1000);
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    
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

// Helper function to format hour in 12-hour format with AM/PM (for peak hours display)
const formatHour = (hour: number): string => {
    const h = hour % 12 || 12;
    const period = hour < 12 ? 'AM' : 'PM';
    return `${h} ${period}`;
};

const formatDuration = (seconds: number): string => {
    if (seconds < 60) {
        return `${Math.round(seconds)}s`;
    }
    return `${Math.round(seconds / 60)}m`;
};

// ... (existing imports)

export function AnalyticsCharts({ campaignId, campaign, timeRange = 'all', country = 'all', variationFilter, onAvailableCountriesChange, onDataLoaded }: AnalyticsChartsProps) {
    const [data, setData] = useState<{
        openData: {
            country: DistributionItem[];
        };
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
    const [userTimezone, setUserTimezone] = useState<string>(Intl.DateTimeFormat().resolvedOptions().timeZone);


    useEffect(() => {
        const fetchData = async () => {
            setIsLoading(true);
            try {
                // Get user timezone preference
                try {
                    const userResponse = await api.get('/auth/me');
                    if (userResponse.data?.user?.timezone) {
                        setUserTimezone(userResponse.data.user.timezone);
                    }
                } catch (error) {
                    console.log('Could not fetch user timezone, using browser default');
                }

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

                if (variationFilter) {
                    params.variation_id = variationFilter;
                }

                const response = await api.get(`/campaigns/${campaignId}/events`, { params });
                const { distributions, events } = response.data;
                console.log('Full response:', response.data);
                console.log('Distributions:', distributions);

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
                    const openData = {
                        country: distributions.open_data?.country_distribution || []
                    };
                    
                    const clickData = {
                        os: distributions.click_data?.os_distribution || [],
                        device: distributions.click_data?.device_distribution || [],
                        browser: distributions.click_data?.browser_distribution || [],
                        country: distributions.click_data?.country_distribution || []
                    };

                    console.log('Open data:', openData);
                    console.log('Click data:', clickData);

                    setData({
                        openData,
                        clickData,
                        temporal: temporal_analytics,
                        engagement: engagement_metrics,
                        insights: recipient_insights,
                        summary: response.data.summary
                    });

                    // Extract available countries from both click and open data
                    if (onAvailableCountriesChange) {
                        const clickCountries = distributions.click_data?.country_distribution?.map((d: any) => d.name) || [];
                        const openCountries = distributions.open_data?.country_distribution?.map((d: any) => d.name) || [];
                        
                        // Combine both, preferring click data but including open data as fallback
                        const allCountries = [...new Set([...clickCountries, ...openCountries])].filter(c => c && c !== 'Unknown');
                        
                        if (allCountries.length > 0) {
                            onAvailableCountriesChange(allCountries);
                        }
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
    }, [campaignId, timeRange, country, variationFilter]);

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
                <div className="h-[20px]">
                    {subtitle && <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>}
                </div>
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
            // Format the label - if it's a large number (timestamp), use formatTime, otherwise use formatHour
            const formattedLabel = label > 100 ? formatTime(label, userTimezone) : formatHour(label);

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

    // Helper to calculate total for percentages
    const calculateTotal = (data: any[]) => data.reduce((acc, item) => acc + item.value, 0);

    const renderCustomLegend = (props: any) => {
        const { payload } = props;
        const total = payload.reduce((acc: number, entry: any) => acc + entry.payload.value, 0);

        return (
            <ul className="flex flex-wrap justify-center gap-4 mt-4">
                {payload.map((entry: any, index: number) => {
                    const percentage = ((entry.payload.value / total) * 100).toFixed(1);
                    return (
                        <li key={`item-${index}`} className="flex items-center gap-2 text-sm">
                            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
                            <span className="text-muted-foreground">{entry.value}</span>
                            <span className="font-medium">
                                {entry.payload.value} ({percentage}%)
                            </span>
                        </li>
                    );
                })}
            </ul>
        );
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
                    value={
                        data?.summary?.unique_clicks != null && data?.summary?.unique_opens != null && data.summary.unique_opens > 0
                            ? Number(
                                ((data.summary.unique_clicks * 250) / data.summary.unique_opens).toFixed(0)
                              )
                            : 0
                    }
                    icon={Zap}
                    subtext="Quality of interactions"
                />
                <InsightCard
                    title="Click-to-Open Rate"
                    value={
                        data?.summary?.unique_clicks != null && data?.summary?.unique_opens != null && data.summary.unique_opens > 0
                            ? Number(
                                ((data.summary.unique_clicks * 100) / data.summary.unique_opens).toFixed(1)
                              )
                            : 0
                    }
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
                                    ? formatDuration(data.summary.avg_time_to_open)
                                    : 'N/A'}
                            </p>
                        </div>
                        <div className="space-y-1">
                            <p className="text-xs text-muted-foreground">Avg Time to Click</p>
                            <p className="text-2xl font-bold">
                                {data.summary.avg_time_to_click !== null
                                    ? formatDuration(data.summary.avg_time_to_click)
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
                        subtitle={`Times shown in ${userTimezone} timezone`}
                    >
                        <AreaChart data={data.temporal.hourly_engagement.engagement_by_hour}>
                            <defs>
                                <linearGradient id="colorOpens" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#2563eb" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
                                </linearGradient>
                                <linearGradient id="colorClicks" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#374151" />
                            <XAxis
                                dataKey="hour"
                                stroke="#9ca3af"
                                tick={false}
                                axisLine={true}
                            />
                            <YAxis
                                stroke="#9ca3af"
                                allowDecimals={false}
                            />
                            <Tooltip content={<CustomTooltip />} />
                            <Legend />
                            <Area type="monotone" dataKey="opens" stroke="#2563eb" fillOpacity={1} fill="url(#colorOpens)" name="Opens" />
                            <Area type="monotone" dataKey="clicks" stroke="#8b5cf6" fillOpacity={1} fill="url(#colorClicks)" name="Clicks" />
                        </AreaChart>
                    </ChartCard>
                </div>
                <div>
                    <ChartCard title="User Segmentation" subtitle="Engagement levels based on interaction patterns">


                        <PieChart>
                            <Pie
                                data={segmentsData}
                                cx="50%"
                                cy="50%"
                                innerRadius={60}
                                outerRadius={80}
                                paddingAngle={5}
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
            </div>

            {/* Click Analytics - Device/Browser/OS Distribution */}
            <div className="rounded-xl border border-border bg-card p-6 shadow-sm mb-6">
                <div className="mb-6">
                    <h3 className="text-lg font-semibold">Click Analytics</h3>
                    <p className="text-sm text-muted-foreground mt-1">Device, browser, and OS data from link clicks</p>
                </div>

                {/* Device/Browser/OS Distribution */}
                <div className="grid gap-6 grid-cols-1 md:grid-cols-3 mb-6">
                    <ChartCard title="Device Distribution" subtitle="Click source by device type">
                        {data.clickData.device.length > 0 ? (
                            <PieChart>
                                <Pie
                                    data={data.clickData.device}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={80}
                                    paddingAngle={5}
                                    dataKey="value"
                                    stroke="none"
                                >
                                    {data.clickData.device.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip content={<CustomTooltip />} />
                                <Legend content={renderCustomLegend} />
                            </PieChart>
                        ) : (
                            <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
                                No click data available
                            </div>
                        )}
                    </ChartCard>
                    <ChartCard title="Browser Distribution" subtitle="Click source by browser application">
                        {data.clickData.browser.length > 0 ? (
                            <PieChart>
                                <Pie
                                    data={data.clickData.browser}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={80}
                                    paddingAngle={5}
                                    dataKey="value"
                                    stroke="none"
                                >
                                    {data.clickData.browser.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip content={<CustomTooltip />} />
                                <Legend content={renderCustomLegend} />
                            </PieChart>
                        ) : (
                            <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
                                No click data available
                            </div>
                        )}
                    </ChartCard>
                    <ChartCard title="OS Distribution" subtitle="Click source by operating system">
                        {data.clickData.os.length > 0 ? (
                            <PieChart>
                                <Pie
                                    data={data.clickData.os}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={80}
                                    paddingAngle={5}
                                    dataKey="value"
                                    stroke="none"
                                >
                                    {data.clickData.os.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip content={<CustomTooltip />} />
                                <Legend content={renderCustomLegend} />
                            </PieChart>
                        ) : (
                            <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
                                No click data available
                            </div>
                        )}
                    </ChartCard>
                </div>

                {/* Separator */}
                {data.summary?.top_clicked_links && data.summary.top_clicked_links.length > 0 && (
                    <div className="border-t border-border my-6"></div>
                )}

                {/* Top Clicked Links */}
                {data.summary?.top_clicked_links && data.summary.top_clicked_links.length > 0 && (
                    <div>
                        <div className="flex items-center gap-2 mb-4">
                            <LinkIcon className="h-5 w-5 text-primary" />
                            <h4 className="text-md font-semibold">Top Clicked Links</h4>
                        </div>
                        <div className="space-y-3">
                            {data.summary.top_clicked_links.map((link: any, index: number) => (
                                <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors border border-border/50">
                                    <div className="flex-1 min-w-0 mr-4">
                                        <p className="text-sm font-medium truncate text-foreground" title={link.url}>
                                            {link.url}
                                        </p>
                                    </div>
                                    <div className="flex items-center gap-2 shrink-0">
                                        <div className="px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-medium">
                                            {link.clicks} {link.clicks === 1 ? 'click' : 'clicks'}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>

        </div >
    );
}
