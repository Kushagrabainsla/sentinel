import axios from 'axios';

const API_URL = '/api/proxy';

export const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add a request interceptor to inject the API key
api.interceptors.request.use(
    (config) => {
        if (typeof window !== 'undefined') {
            const apiKey = localStorage.getItem('sentinel_api_key');
            if (apiKey) {
                config.headers['X-API-Key'] = apiKey;
            }
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Add a response interceptor to handle auth errors
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && (error.response.status === 401 || error.response.status === 403)) {
            // Clear authentication data
            if (typeof window !== 'undefined') {
                localStorage.removeItem('sentinel_api_key');
                localStorage.removeItem('sentinel_user_name');
                // Redirect to login
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

export interface User {
    id: string;
    name: string;
    email: string;
    api_key: string;
    status: string;
    timezone?: string;
    created_at?: number;
    google_connected?: boolean;
    google_email?: string;
    gmail_enabled?: boolean;
}

export interface Segment {
    id: string;
    name: string;
    description?: string;
    contact_count: number;
    status: string;
}

export interface Campaign {
    id: string;
    name: string;
    email_subject: string;
    email_body: string;
    status: string;
    state: string;
    recipient_count?: number;
    type: 'I' | 'S' | 'AB';
    schedule_at?: number;
    created_at: number;
    variations?: Array<{
        subject: string;
        content: string;
        tone: string;
    }>;
}

export interface CampaignEvent {
    id: string;
    campaign_id: string;
    type: string; // 'open', 'sent', 'click', etc.
    created_at: number;
    recipient_id?: string;
    email?: string;
    raw?: string;
    metadata?: any;
}

export interface DistributionItem {
    name: string;
    value: number;
    [key: string]: string | number;
}

export interface HourlyEngagement {
    hour: number;
    sent: number;
    opens: number;
    clicks: number;
    engagement_score: number;
}

export interface DailyEngagement {
    day: string;
    opens: number;
    clicks: number;
    engagement_score: number;
}

export interface TemporalAnalytics {
    hourly_engagement: {
        peak_hours: number[];
        engagement_by_hour: HourlyEngagement[];
    };
    daily_patterns: {
        best_day: string | null;
        engagement_by_day: DailyEngagement[];
    };
    response_times: {
        avg_time_to_open: number;
        avg_time_to_click: number;
    };
}

export interface EngagementMetrics {
    click_to_open_rate: number;
    unique_engagement_rate: number;
    engagement_quality_score: number;
    bounce_rate: number;
}

export interface RecipientInsights {
    unique_recipients: number;
    engagement_segments: {
        highly_engaged: { count: number; percentage: number };
        moderately_engaged: { count: number; percentage: number };
        low_engaged: { count: number; percentage: number };
    };
    top_recipients: any[];
}

export interface CampaignEventsResponse {
    events: CampaignEvent[];
    summary: {
        total_events: number;
        event_counts: Record<string, number>;
        event_types_breakdown?: Array<{
            event_type: string;
            count: number;
            percentage: number;
        }>;
        campaign_id: string;
        campaign_name: string;
        time_range?: {
            from_epoch: string;
            to_epoch: string;
        };
        unique_opens: number;
        unique_clicks: number;
        unique_recipients?: number;
        top_clicked_links?: any[];
        avg_time_to_open: number | null;
        avg_time_to_click: number | null;
    };
    distributions: {
        open_data?: {
            country_distribution: DistributionItem[];
        };
        click_data?: {
            os_distribution: DistributionItem[];
            device_distribution: DistributionItem[];
            browser_distribution: DistributionItem[];
            country_distribution: DistributionItem[];
        };
    };
    temporal_analytics: TemporalAnalytics;
    engagement_metrics: EngagementMetrics;
    recipient_insights: RecipientInsights;
    has_more: boolean;
}
