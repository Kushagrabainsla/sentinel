import { api } from '@/lib/api';

export interface GenerateEmailParams {
    tone?: string;
    tones?: string[];
    finalGoal: string;
    audiences: string[];
    keyPoints: string;
    links: Array<{ url: string; text: string }>;
}

export interface GenerateEmailResponse {
    subject: string;
    content: string;
    variations?: Array<{ subject: string; content: string; tone: string }>;
}

export const generateEmail = async (params: GenerateEmailParams): Promise<GenerateEmailResponse> => {
    // Call the Next.js API route directly, not through the backend proxy
    const response = await fetch('/api/generate-email', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            tone: params.tone,
            tones: params.tones,
            finalGoal: params.finalGoal,
            audiences: params.audiences.join(', '),
            keyPoints: params.keyPoints,
            links: params.links
        })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to generate email');
    }

    return response.json();
};
