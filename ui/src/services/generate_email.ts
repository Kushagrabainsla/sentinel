import { api } from '@/lib/api';

export interface GenerateEmailParams {
    tone: string;
    finalGoal: string;
    audiences: string[];
    keyPoints: string;
    links: Array<{ url: string; text: string }>;
}

export interface GenerateEmailResponse {
    subject: string;
    content: string;
}

export const generateEmail = async (params: GenerateEmailParams): Promise<GenerateEmailResponse> => {
    const response = await api.post('/generate-email', {
        tone: params.tone,
        finalGoal: params.finalGoal,
        audiences: params.audiences.join(', '),
        keyPoints: params.keyPoints,
        links: params.links
    });
    return response.data;
};
