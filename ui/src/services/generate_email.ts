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
    // Call the backend Lambda endpoint
    const response = await api.post('/ai/generate-email', {
        tone: params.tone,
        tones: params.tones,
        finalGoal: params.finalGoal,
        audiences: params.audiences.join(', '),
        keyPoints: params.keyPoints,
        links: params.links
    });

    return response.data;
};
