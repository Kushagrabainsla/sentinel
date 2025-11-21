import { CampaignEventsResponse } from '@/lib/api';

export const dummyCampaignEvents: CampaignEventsResponse = {
    events: [],
    summary: {
        total_events: 1250,
        event_counts: {
            sent: 1000,
            delivered: 980,
            opened: 450,
            clicked: 120,
            bounced: 20,
            spam: 5
        },
        campaign_id: "f58a0bb3-d202-4e64-b2db-9aa4431c6815",
        campaign_name: "Monthly Newsletter"
    },
    distributions: {
        os_distribution: [
            { name: "Windows", value: 450 },
            { name: "macOS", value: 320 },
            { name: "iOS", value: 180 },
            { name: "Android", value: 150 },
            { name: "Linux", value: 50 }
        ],
        device_distribution: [
            { name: "Desktop", value: 600 },
            { name: "Mobile", value: 350 },
            { name: "Tablet", value: 50 }
        ],
        browser_distribution: [
            { name: "Chrome", value: 550 },
            { name: "Safari", value: 250 },
            { name: "Firefox", value: 100 },
            { name: "Edge", value: 80 },
            { name: "Other", value: 20 }
        ],
        ip_distribution: [
            { name: "United States", value: 400 },
            { name: "United Kingdom", value: 150 },
            { name: "Germany", value: 100 },
            { name: "Canada", value: 80 },
            { name: "France", value: 70 },
            { name: "Other", value: 200 }
        ]
    },
    temporal_analytics: {
        hourly_engagement: {
            peak_hours: [10, 14, 19],
            engagement_by_hour: Array.from({ length: 24 }, (_, i) => ({
                hour: i,
                opens: Math.floor(Math.random() * 50),
                clicks: Math.floor(Math.random() * 10),
                engagement_score: Math.floor(Math.random() * 100)
            }))
        },
        daily_patterns: {
            best_day: "Wednesday",
            engagement_by_day: [
                { day: "Mon", opens: 120, clicks: 30, engagement_score: 75 },
                { day: "Tue", opens: 150, clicks: 40, engagement_score: 80 },
                { day: "Wed", opens: 200, clicks: 60, engagement_score: 90 },
                { day: "Thu", opens: 180, clicks: 50, engagement_score: 85 },
                { day: "Fri", opens: 140, clicks: 35, engagement_score: 78 },
                { day: "Sat", opens: 80, clicks: 15, engagement_score: 60 },
                { day: "Sun", opens: 90, clicks: 20, engagement_score: 65 }
            ]
        },
        response_times: {
            avg_time_to_open: 45, // minutes
            avg_time_to_click: 12 // minutes
        }
    },
    engagement_metrics: {
        click_to_open_rate: 26.6,
        unique_engagement_rate: 45.0,
        engagement_quality_score: 85,
        bounce_rate: 2.0
    },
    recipient_insights: {
        unique_recipients: 980,
        engagement_segments: {
            highly_engaged: { count: 150, percentage: 15.3 },
            moderately_engaged: { count: 300, percentage: 30.6 },
            low_engaged: { count: 530, percentage: 54.1 }
        },
        top_recipients: []
    },
    has_more: false
};
