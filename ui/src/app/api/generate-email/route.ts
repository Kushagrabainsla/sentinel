import { GoogleGenerativeAI } from '@google/generative-ai';
import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const { tone, tones, finalGoal, audiences, keyPoints, links } = await request.json();

    // Initialize Gemini API with key from environment variables
    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) {
      return NextResponse.json(
        { key: `GEMINI_API_KEY environment variable not set` },
        { status: 500 }
      );
    }
    const genAI = new GoogleGenerativeAI(apiKey);
    const model = genAI.getGenerativeModel({ model: 'gemini-2.5-flash' });

    // Support both single tone (legacy) and multiple tones (A/B test)
    const tonesArray = tones || (tone ? [tone] : ['Professional']);
    const isMultipleTones = tonesArray.length > 1;

    let prompt: string;

    if (isMultipleTones) {
      // A/B Testing: Generate multiple variations
      prompt = `
You are an AI assistant that generates professional HTML email content.

I will provide you with:
- tones: a list of writing tones to use (generate one email for each tone)
- finalGoal: the purpose of the email
- audiences: a list of audience types (e.g., Recruiters, Investors, Students)
- keyPoints: a newline-separated list of bullet points to include
- links: an optional list of objects [{ url, text }]

Return a JSON array with one object per tone:

[
  {
    "subject": "...",
    "content": "...",   // full HTML string
    "tone": "Professional"
  },
  {
    "subject": "...",
    "content": "...",
    "tone": "Friendly"
  },
  ...
]

Instructions:
1. For each tone, generate a unique subject line that reflects that tone.
2. Generate an HTML email body that includes:
   - Greeting appropriate to the tone
   - A brief intro sentence explaining the goal in that tone
   - A bullet list using the provided keyPoints (use <ul><li> tags)
   - **IMPORTANT**: If links array is provided and not empty, you MUST include a "Useful Links" or "Learn More" section with clickable links using this format:
     <h3>Useful Links</h3>
     <ul>
       <li><a href="URL" style="color: #2563eb; text-decoration: underline;">LINK_TEXT</a></li>
     </ul>
   - A polite closing appropriate to the tone
   - Well-formatted HTML with <h2>, <p>, and <ul> tags
3. Make each variation distinctly different in tone and style.
4. IMPORTANT: Return ONLY the JSON array. Do not wrap it in markdown code blocks.

Input:
tones: ${JSON.stringify(tonesArray)}
finalGoal: ${finalGoal}
audiences: ${audiences}
keyPoints: ${keyPoints}
links: ${JSON.stringify(links)}
${links && links.length > 0 ? '\n⚠️ CRITICAL: The links array has ' + links.length + ' link(s). You MUST include ALL of them in the email body!' : ''}
`;
    } else {
      // Single tone (legacy)
      prompt = `
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
   - Greeting: "Hello <audiences comma-separated>,"
   - A brief intro sentence explaining the goal.
   - A bullet list using the provided keyPoints (use <ul><li> tags).
   - **IMPORTANT**: If links array is provided and not empty, you MUST include a "Useful Links" or "Learn More" section with clickable links using this format:
     <h3>Useful Links</h3>
     <ul>
       <li><a href="URL" style="color: #2563eb; text-decoration: underline;">LINK_TEXT</a></li>
     </ul>
   - A polite closing: "Best regards, The Team"
   - Well-formatted HTML with <h2>, <p>, and <ul> tags.

3. Maintain the specified tone throughout.
4. IMPORTANT: Return ONLY the JSON object. Do not wrap it in markdown code blocks.

Input:
tone: ${tonesArray[0]}
finalGoal: ${finalGoal}
audiences: ${audiences}
keyPoints: ${keyPoints}
links: ${JSON.stringify(links)}
${links && links.length > 0 ? '\n⚠️ CRITICAL: The links array has ' + links.length + ' link(s). You MUST include ALL of them in the email body!' : ''}
`;
    }

    // Log the request for debugging
    console.log('🔍 Email Generation Request:', {
      tones: tonesArray,
      finalGoal,
      audiences,
      keyPoints: keyPoints.substring(0, 100) + '...',
      linksCount: links?.length || 0,
      links
    });

    const result = await model.generateContent(prompt);
    const response = await result.response;
    const text = response.text();

    console.log('📨 LLM Response (first 500 chars):', text.substring(0, 500));

    // Clean up markdown code blocks if present
    const cleanText = text.replace(/```json/g, '').replace(/```/g, '').trim();

    try {
      const jsonResponse = JSON.parse(cleanText);

      console.log('✅ Parsed JSON response:', {
        hasSubject: !!jsonResponse.subject || !!jsonResponse[0]?.subject,
        hasContent: !!jsonResponse.content || !!jsonResponse[0]?.content,
        isArray: Array.isArray(jsonResponse),
        variationsCount: Array.isArray(jsonResponse) ? jsonResponse.length : 0
      });

      if (isMultipleTones) {
        // Return variations array
        return NextResponse.json({
          subject: jsonResponse[0]?.subject || '',
          content: jsonResponse[0]?.content || '',
          variations: jsonResponse
        });
      } else {
        // Return single result
        console.log('📧 Generated email content length:', jsonResponse.content?.length || 0);
        console.log('🔗 Content includes link tags:', jsonResponse.content?.includes('<a href') || false);
        return NextResponse.json(jsonResponse);
      }
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
      { error: error.message },
      { status: 500 }
    );
  }
}
