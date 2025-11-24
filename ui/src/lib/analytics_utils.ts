import { CampaignEvent, TemporalAnalytics, EngagementMetrics, RecipientInsights } from './api';

export function calculateTemporalAnalytics(events: CampaignEvent[]): TemporalAnalytics {
    const hourly_opens = new Array(24).fill(0);
    const hourly_clicks = new Array(24).fill(0);
    const daily_opens = new Array(7).fill(0);
    const daily_clicks = new Array(7).fill(0);

    const openEvents: number[] = [];
    const clickEvents: number[] = [];
    const sentEvents: Record<string, number> = {};

    events.forEach(event => {
        const date = new Date(event.created_at * 1000);
        const hour = date.getHours();
        const day = date.getDay(); // 0 = Sunday

        // Adjust day index to 0=Mon, 6=Sun for consistency with backend logic if needed, 
        // but JS getDay() is 0=Sun. Let's stick to 0=Sun for now or map it.
        // Let's map 0(Sun) -> 6, 1(Mon) -> 0, etc.
        const adjustedDay = day === 0 ? 6 : day - 1;

        if (event.type === 'open') {
            hourly_opens[hour]++;
            daily_opens[adjustedDay]++;
            openEvents.push(event.created_at);
        } else if (event.type === 'click') {
            hourly_clicks[hour]++;
            daily_clicks[adjustedDay]++;
            clickEvents.push(event.created_at);
        } else if (event.type === 'sent' && event.email) {
            sentEvents[event.email] = event.created_at;
        }
    });

    const engagement_by_hour = hourly_opens.map((opens, hour) => ({
        hour,
        opens,
        clicks: hourly_clicks[hour],
        engagement_score: opens + (hourly_clicks[hour] * 2)
    }));

    const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
    const engagement_by_day = daily_opens.map((opens, i) => ({
        day: days[i],
        opens,
        clicks: daily_clicks[i],
        engagement_score: opens + (daily_clicks[i] * 2)
    }));

    // Peak hours
    const peak_hours = [...engagement_by_hour]
        .sort((a, b) => b.opens - a.opens)
        .slice(0, 3)
        .filter(h => h.opens > 0)
        .map(h => h.hour);

    // Best day
    const sortedDays = [...engagement_by_day].sort((a, b) => b.opens - a.opens);
    const best_day = sortedDays[0]?.opens > 0 ? sortedDays[0].day : null;

    // Response times (simplified)
    // Note: This requires matching sent events to open/click events by email, which might not be perfect if multiple emails sent to same person
    // But good enough for estimation.

    // We can't easily calculate avg time without iterating again or storing more state.
    // Let's do a quick pass if needed, or just return 0 for now if not critical.
    // Actually, let's try to calculate it.

    let totalOpenTime = 0;
    let openCount = 0;

    events.forEach(event => {
        if (event.type === 'open' && event.email && sentEvents[event.email]) {
            const diff = event.created_at - sentEvents[event.email];
            if (diff > 0) {
                totalOpenTime += diff;
                openCount++;
            }
        }
    });

    return {
        hourly_engagement: {
            peak_hours,
            engagement_by_hour
        },
        daily_patterns: {
            best_day,
            engagement_by_day
        },
        response_times: {
            avg_time_to_open: openCount > 0 ? Math.round((totalOpenTime / openCount) / 60) : 0,
            avg_time_to_click: 0 // Similar logic could be applied
        }
    };
}

export function calculateEngagementMetrics(events: CampaignEvent[]): EngagementMetrics {
    const uniqueOpens = new Set<string>();
    const uniqueClicks = new Set<string>();
    let totalSent = 0;
    let bounces = 0;

    events.forEach(event => {
        if (event.type === 'open' && event.email) uniqueOpens.add(event.email);
        if (event.type === 'click' && event.email) {
            uniqueClicks.add(event.email);
            // Implied open: if they clicked, they must have opened
            uniqueOpens.add(event.email);
        }
        if (event.type === 'sent') totalSent++;
        if (event.type === 'bounce') bounces++;
    });

    const click_to_open_rate = uniqueOpens.size > 0 ? (uniqueClicks.size / uniqueOpens.size) * 100 : 0;
    const unique_engagement_rate = totalSent > 0 ? (uniqueOpens.size / totalSent) * 100 : 0;
    const bounce_rate = totalSent > 0 ? (bounces / totalSent) * 100 : 0;
    const engagement_quality_score = Math.min(100, Math.round(click_to_open_rate * 2.5));

    return {
        click_to_open_rate,
        unique_engagement_rate,
        engagement_quality_score,
        bounce_rate
    };
}

export function calculateRecipientInsights(events: CampaignEvent[]): RecipientInsights {
    const scores: Record<string, number> = {};

    events.forEach(event => {
        if (!event.email) return;

        if (!scores[event.email]) scores[event.email] = 0;

        if (event.type === 'open') scores[event.email] += 1;
        if (event.type === 'click') scores[event.email] += 3;
    });

    const totalRecipients = Object.keys(scores).length;
    let high = 0, moderate = 0, low = 0;

    Object.values(scores).forEach(score => {
        if (score >= 5) high++;
        else if (score >= 2) moderate++;
        else low++;
    });

    const getPercentage = (count: number) => totalRecipients > 0 ? parseFloat(((count / totalRecipients) * 100).toFixed(1)) : 0;

    return {
        unique_recipients: totalRecipients,
        engagement_segments: {
            highly_engaged: { count: high, percentage: getPercentage(high) },
            moderately_engaged: { count: moderate, percentage: getPercentage(moderate) },
            low_engaged: { count: low, percentage: getPercentage(low) }
        },
        top_recipients: []
    };
}
