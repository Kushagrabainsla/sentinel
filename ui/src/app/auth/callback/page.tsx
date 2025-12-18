'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { toast } from 'sonner';
import { Loader2 } from 'lucide-react';
import { api } from '@/lib/api';

export default function AuthCallbackPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const [status, setStatus] = useState('Processing authentication...');

    useEffect(() => {
        const code = searchParams.get('code');
        const error = searchParams.get('error');

        if (error) {
            console.error('Google OAuth error:', error);
            toast.error('Failed to connect Google account: ' + error);
            router.push('/profile');
            return;
        }

        if (code) {
            handleCallback(code);
        } else {
            setStatus('No authorization code found.');
            setTimeout(() => router.push('/profile'), 2000);
        }
    }, [searchParams, router]);

    const handleCallback = async (code: string) => {
        try {
            setStatus('Connecting your Google account...');
            await api.post('/auth/google/callback', { code });
            toast.success('Google account connected successfully!');
            router.push('/profile');
        } catch (error: any) {
            console.error('Callback error:', error);
            toast.error('Failed to complete Google connection');
            router.push('/profile');
        }
    };

    return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
            <Loader2 className="h-12 w-12 animate-spin text-primary" />
            <h1 className="text-xl font-medium">{status}</h1>
            <p className="text-muted-foreground">Please wait while we redirect you.</p>
        </div>
    );
}
