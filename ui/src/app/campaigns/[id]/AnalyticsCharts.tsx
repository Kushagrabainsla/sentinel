'use client';

import { useEffect, useState } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, AreaChart, Area, CartesianGrid } from 'recharts';
import { api, TemporalAnalytics, EngagementMetrics, RecipientInsights } from '@/lib/api';
import { Loader2, Clock, Users, MousePointerClick, Zap } from 'lucide-react';

interface AnalyticsChartsProps {
    campaignId: string;
    timeRange?: '24h' | '7d' | '30d' | 'all';
}

interface ChartData {
    name: string;
    value: number;
    [key: string]: string | number;
}

const COLORS = ['#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#3b82f6', '#6366f1'];

export function AnalyticsCharts({ campaignId, timeRange = 'all' }: AnalyticsChartsProps) {
    const [data, setData] = useState<{
        os: ChartData[];
        device: ChartData[];
        browser: ChartData[];
        geo: ChartData[];
        temporal: TemporalAnalytics;
        engagement: EngagementMetrics;
        insights: RecipientInsights;
    } | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            setIsLoading(true);
            try {
                const response = await api.get(`/campaigns/${campaignId}/events`);
                const { distributions, temporal_analytics, engagement_metrics, recipient_insights } = response.data;

                if (distributions) {
                    setData({
                        os: distributions.os_distribution,
                        device: distributions.device_distribution,
                        browser: distributions.browser_distribution,
                        geo: distributions.ip_distribution,
                        temporal: temporal_analytics,
                        engagement: engagement_metrics,
                        insights: recipient_insights
                    });
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
    }, [campaignId, timeRange]);

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

    const ChartCard = ({ title, children }: { title: string, children: React.ReactNode }) => (
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
            <h3 className="text-lg font-semibold mb-6">{title}</h3>
            <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                    {children}
                </ResponsiveContainer>
            </div>
        </div>
    );

    const CustomTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length) {
            return (
                <div className="bg-popover border border-border p-3 rounded-lg shadow-lg">
                    <p className="font-medium mb-2">{label}</p>
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
            <div className="grid gap-4 md:grid-cols-4">
                <InsightCard
                    title="Optimal Send Time"
                    value={data.temporal.hourly_engagement.optimal_send_time || 'N/A'}
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
                    value={`${data.engagement.click_to_open_rate}%`}
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

            {/* Advanced Charts Row 1 */}
            <div className="grid gap-6 md:grid-cols-3">
                <div className="md:col-span-2">
                    <ChartCard title="Hourly Engagement Pattern">
                        <AreaChart data={data.temporal.hourly_engagement.engagement_by_hour}>
                            <defs>
                                <linearGradient id="colorOpens" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#374151" />
                            <XAxis dataKey="hour" tickFormatter={(val) => `${val}:00`} stroke="#9ca3af" />
                            <YAxis stroke="#9ca3af" />
                            <Tooltip content={<CustomTooltip />} />
                            <Area type="monotone" dataKey="opens" stroke="#8b5cf6" fillOpacity={1} fill="url(#colorOpens)" name="Opens" />
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
            <div className="grid gap-6 md:grid-cols-2">
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
                <ChartCard title="Geographic Distribution">
                    <BarChart data={data.geo} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#374151" />
                        <XAxis type="number" hide />
                        <YAxis dataKey="name" type="category" width={100} tick={{ fill: '#9ca3af' }} />
                        <Tooltip content={<CustomTooltip />} />
                        <Bar dataKey="value" fill="#10b981" radius={[0, 4, 4, 0]}>
                            {data.geo.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                        </Bar>
                    </BarChart>
                </ChartCard>
            </div>
        </div>
    );
}
