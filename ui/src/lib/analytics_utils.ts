import { CampaignEvent, TemporalAnalytics, EngagementMetrics, RecipientInsights } from './api';

/**
 * Helper function to detect if an event is from an email proxy/prefetch service
 * based on the raw metadata stored in the event
 */
function isProxyEvent(event: CampaignEvent): boolean {
    if (!event.raw) return false;
    
    try {
        const raw = typeof event.raw === 'string' ? JSON.parse(event.raw) : event.raw;
        
        // Check for proxy detection flag (added by backend)
        if (raw.is_proxy === true) {
            return true;
        }
        
        // Fallback: Check for common proxy indicators
        const userAgent = (raw.user_agent || '').toLowerCase();
        const proxyPatterns = [
            'googleimageproxy',
            'ggpht.com',
            'outlook.safelink',
            'protection.outlook',
            'amp.apple',
        ];
        
        return proxyPatterns.some(pattern => userAgent.includes(pattern));
    } catch (e) {
        return false;
    }
}

/**
 * Classify open events as proxy vs human opens
 * 
 * Simple rule: For the same combination of (campaign_id, email):
 * - First open event = proxy open (email client prefetch)
 * - All subsequent opens = actual human opens
 */
function classifyOpenEvents(events: CampaignEvent[]): Map<string, 'proxy' | 'human' | 'uncertain'> {
    const classifications = new Map<string, 'proxy' | 'human' | 'uncertain'>();
    
    // Group events by campaign + email
    const groups = new Map<string, CampaignEvent[]>();
    
    events.forEach(event => {
        if (event.type !== 'open') return;
        
        const key = `${event.campaign_id}_${event.email}`;
        if (!groups.has(key)) {
            groups.set(key, []);
        }
        groups.get(key)!.push(event);
    });
    
    // Classify each group: first = proxy, rest = human
    groups.forEach((groupEvents) => {
        // Sort by timestamp
        groupEvents.sort((a, b) => a.created_at - b.created_at);
        
        groupEvents.forEach((event, index) => {
            const eventKey = `${event.id}`;
            
            if (index === 0) {
                // First open = proxy prefetch
                classifications.set(eventKey, 'proxy');
            } else {
                // Subsequent opens = actual human
                classifications.set(eventKey, 'human');
            }
        });
    });
    
    return classifications;
}

export function calculateTemporalAnalytics(events: CampaignEvent[], excludeProxyOpens: boolean = true): TemporalAnalytics {
    const hourly_opens = new Array(24).fill(0);
    const hourly_proxy_opens = new Array(24).fill(0);
    const hourly_clicks = new Array(24).fill(0);
    const daily_opens = new Array(7).fill(0);
    const daily_proxy_opens = new Array(7).fill(0);
    const daily_clicks = new Array(7).fill(0);

    const openEvents: number[] = [];
    const clickEvents: number[] = [];
    const sentEvents: Record<string, number> = {};

    // Create a map to track events by timestamp for timeline view
    const timelineMap: Record<number, { 
        sent: number; 
        opens: number; 
        proxy_opens: number;
        clicks: number; 
        timestamp: number;
    }> = {};
    
    // Always classify open events to track proxy opens separately
    const openClassifications = classifyOpenEvents(events);

    events.forEach(event => {
        const date = new Date(event.created_at * 1000);
        const hour = date.getHours();
        const day = date.getDay(); // 0 = Sunday

        // Adjust day index to 0=Mon, 6=Sun for consistency with backend logic if needed, 
        // but JS getDay() is 0=Sun. Let's stick to 0=Sun for now or map it.
        // Let's map 0(Sun) -> 6, 1(Mon) -> 0, etc.
        const adjustedDay = day === 0 ? 6 : day - 1;

        // Initialize timeline entry if not exists
        if (!timelineMap[event.created_at]) {
            timelineMap[event.created_at] = { 
                sent: 0, 
                opens: 0, 
                proxy_opens: 0,
                clicks: 0, 
                timestamp: event.created_at 
            };
        }

        if (event.type === 'open') {
            const classification = openClassifications.get(event.id);
            
            // Track proxy opens separately
            if (classification === 'proxy') {
                hourly_proxy_opens[hour]++;
                daily_proxy_opens[adjustedDay]++;
                timelineMap[event.created_at].proxy_opens++;
                
                // Skip proxy opens from main counts if requested
                if (excludeProxyOpens) {
                    return;
                }
            }
            
            hourly_opens[hour]++;
            daily_opens[adjustedDay]++;
            openEvents.push(event.created_at);
            timelineMap[event.created_at].opens++;
        } else if (event.type === 'click') {
            hourly_clicks[hour]++;
            daily_clicks[adjustedDay]++;
            clickEvents.push(event.created_at);
            timelineMap[event.created_at].clicks++;
        } else if (event.type === 'sent') {
            if (event.email) {
                sentEvents[event.email] = event.created_at;
            }
            timelineMap[event.created_at].sent++;
        }
    });

    // Convert timeline map to sorted array with all event types
    const engagement_by_hour = Object.values(timelineMap)
        .sort((a, b) => a.timestamp - b.timestamp)
        .map(item => ({
            hour: item.timestamp, // Using timestamp instead of hour number
            sent: item.sent,
            opens: item.opens,
            proxy_opens: item.proxy_opens,
            clicks: item.clicks,
            engagement_score: item.opens + (item.clicks * 2)
        }));

    const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
    const engagement_by_day = daily_opens.map((opens, i) => ({
        day: days[i],
        opens,
        proxy_opens: daily_proxy_opens[i],
        clicks: daily_clicks[i],
        engagement_score: opens + (daily_clicks[i] * 2)
    }));

    // Peak hours (still using hourly aggregation for this metric)
    const hourlyAggregation = hourly_opens.map((opens, hour) => ({ hour, opens }));
    const peak_hours = [...hourlyAggregation]
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
            // Skip proxy opens if requested
            if (excludeProxyOpens) {
                const classification = openClassifications.get(event.id);
                if (classification === 'proxy') {
                    return; // Skip this event
                }
            }
            
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

export function calculateEngagementMetrics(events: CampaignEvent[], excludeProxyOpens: boolean = true): EngagementMetrics {
    const uniqueOpens = new Set<string>();
    const uniqueClicks = new Set<string>();
    let totalSent = 0;
    let bounces = 0;
    
    // Classify open events if excluding proxies
    const openClassifications = excludeProxyOpens ? classifyOpenEvents(events) : new Map();

    events.forEach(event => {
        if (event.type === 'open' && event.email) {
            // Skip proxy opens if requested
            if (excludeProxyOpens) {
                const classification = openClassifications.get(event.id);
                if (classification === 'proxy') {
                    return; // Skip this event
                }
            }
            uniqueOpens.add(event.email);
        }
        if (event.type === 'click' && event.email) uniqueClicks.add(event.email);
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

export function calculateRecipientInsights(events: CampaignEvent[], excludeProxyOpens: boolean = true): RecipientInsights {
    const scores: Record<string, number> = {};
    
    // Classify open events if excluding proxies
    const openClassifications = excludeProxyOpens ? classifyOpenEvents(events) : new Map();

    events.forEach(event => {
        if (!event.email) return;

        if (!scores[event.email]) scores[event.email] = 0;

        if (event.type === 'open') {
            // Skip proxy opens if requested
            if (excludeProxyOpens) {
                const classification = openClassifications.get(event.id);
                if (classification === 'proxy') {
                    return; // Skip this event
                }
            }
            scores[event.email] += 1;
        }
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

/**
 * Get statistics about proxy vs human opens in the campaign
 */
export function getProxyOpenStats(events: CampaignEvent[]) {
    const openEvents = events.filter(e => e.type === 'open');
    const classifications = classifyOpenEvents(openEvents);
    
    let proxyOpens = 0;
    let humanOpens = 0;
    let uncertainOpens = 0;
    
    openEvents.forEach(event => {
        const classification = classifications.get(event.id);
        if (classification === 'proxy') {
            proxyOpens++;
        } else if (classification === 'human') {
            humanOpens++;
        } else {
            uncertainOpens++;
        }
    });
    
    const totalOpens = openEvents.length;
    
    return {
        total_opens: totalOpens,
        proxy_opens: proxyOpens,
        human_opens: humanOpens,
        uncertain_opens: uncertainOpens,
        proxy_percentage: totalOpens > 0 ? ((proxyOpens / totalOpens) * 100).toFixed(1) : '0',
        human_percentage: totalOpens > 0 ? ((humanOpens / totalOpens) * 100).toFixed(1) : '0',
    };
}

/**
 * Export helper functions for external use
 */
export { isProxyEvent, classifyOpenEvents };
