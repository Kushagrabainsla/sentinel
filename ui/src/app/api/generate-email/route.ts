import { GoogleGenerativeAI } from '@google/generative-ai';
import { NextResponse } from 'next/server';

export async function POST(request: Request) {
    try {
        const { tone, finalGoal, audiences, keyPoints, links } = await request.json();

        // Initialize Gemini API with key from environment variables
        const apiKey = process.env.GEMINI_API_KEY;
        if (!apiKey) {
            return NextResponse.json(
                { key: apiKey },
                { status: 500 }
            );
        }
        const genAI = new GoogleGenerativeAI(apiKey);

        const model = genAI.getGenerativeModel({ model: 'gemini-2.5-flash' });

        const prompt = `
You are an AI assistant that generates professional HTML email content.

I will provide you with:
- tone: the writing tone to use (e.g., Formal, Friendly, Persuasive)
- finalGoal: the purpose of the email
- audiences: a list of audience types (e.g., Recruiters, Investors, Students)
- keyPoints: a newline-separated list of bullet points to include
- links: an optional list of objects [{ url, text }]

Return the following JSON structure:

{
  "subject": "...",
  "content": "..."   // full HTML string
}

Instructions:
1. Generate a concise subject line in this format:
   "<finalGoal> for <audiences comma-separated>"

2. Generate an HTML email body that includes:
   - Greeting: “Hello <audiences comma-separated>,”
   - A brief intro sentence explaining the goal.
   - A bullet list using the provided keyPoints.
   - If links exist, generate a section titled “Useful Links:” followed by <ul><li>..</li></ul>.
   - A polite closing: “Best regards, The Team”
   - Well-formatted HTML with <h2>, <p>, and <ul> tags.

3. Maintain the specified tone throughout.
4. IMPORTANT: Return ONLY the JSON object. Do not wrap it in markdown code blocks.

Input:
tone: ${tone}
finalGoal: ${finalGoal}
audiences: ${audiences}
keyPoints: ${keyPoints}
links: ${JSON.stringify(links)}
`;

        const result = await model.generateContent(prompt);
        const response = await result.response;
        const text = response.text();

        // Clean up markdown code blocks if present
        const cleanText = text.replace(/```json/g, '').replace(/```/g, '').trim();

        try {
            const jsonResponse = JSON.parse(cleanText);
            return NextResponse.json(jsonResponse);
        } catch (e) {
            console.error('Failed to parse Gemini response:', text);
            return NextResponse.json(
                { error: 'Failed to parse AI response' },
                { status: 500 }
            );
        }
    } catch (error: any) {
        console.error('Gemini API error:', error);
        return NextResponse.json(
            { error: error.message  },
            { status: 500 }
        );
    }
}
