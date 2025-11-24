import { GoogleGenerativeAI } from '@google/generative-ai';
import { NextResponse } from 'next/server';

export async function POST(
    request: Request,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { campaign, stats } = await request.json();
        const { id } = await params;

        // Initialize Gemini API with key from environment variables
        const apiKey = process.env.GEMINI_API_KEY;
        if (!apiKey) {
            return NextResponse.json(
                { error: 'GEMINI_API_KEY environment variable not set' },
                { status: 500 }
            );
        }
        const genAI = new GoogleGenerativeAI(apiKey);
        const model = genAI.getGenerativeModel({ model: 'gemini-2.5-flash' });

        const prompt = `
You are an expert email marketing analyst. Analyze the following campaign performance and provide actionable insights.

Campaign Details:
- Subject: "${campaign.email_subject}"
- Body Preview: "${campaign.email_body.substring(0, 500)}..."
- Type: ${campaign.type === 'S' ? 'Scheduled' : 'Immediate'}
- Status: ${campaign.status}

Performance Stats:
- Total Events: ${stats.total_events}
- Sent: ${stats.event_counts.sent || 0}
- Opened: ${stats.event_counts.open || 0}
- Clicked: ${stats.event_counts.click || 0}
- Unique Opens: ${stats.unique_opens}
- Unique Clicks: ${stats.unique_clicks}
- Avg Time to Open: ${stats.avg_time_to_open ? Math.round(stats.avg_time_to_open) + ' min' : 'N/A'}
- Avg Time to Click: ${stats.avg_time_to_click ? Math.round(stats.avg_time_to_click) + ' min' : 'N/A'}

Please provide a concise report in Markdown format with the following sections:
1. **Executive Summary**: A 2-3 sentence overview of the campaign's performance.
2. **Key Strengths**: What worked well? (e.g., high open rate, good subject line).
3. **Areas for Improvement**: What could be better? (e.g., low click-through rate).
4. **Actionable Recommendations**: 3 specific things to try in the next campaign. For each, provide ONE concrete example.

Return the response as a valid JSON object with the following structure:
{
  "executive_summary": "...",
  "key_strengths": ["strength 1", "strength 2"],
  "areas_for_improvement": ["improvement 1", "improvement 2"],
  "actionable_recommendations": [
    { "recommendation": "...", "example": "..." },
    { "recommendation": "...", "example": "..." },
    { "recommendation": "...", "example": "..." }
  ]
}

IMPORTANT: Return ONLY the JSON object. Do not wrap it in markdown code blocks.
`;

        const result = await model.generateContent(prompt);
        const response = await result.response;
        const text = response.text();

        // Clean up markdown code blocks if present (just in case)
        const cleanText = text.replace(/```json/g, '').replace(/```/g, '').trim();
        const jsonResponse = JSON.parse(cleanText);

        return NextResponse.json({ report: jsonResponse });

    } catch (error: any) {
        console.error('Gemini API error:', error);
        return NextResponse.json(
            { error: error.message || 'Failed to generate insights' },
            { status: 500 }
        );
    }
}
