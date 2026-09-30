'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { CheckCircle2, Loader2, Mail, RefreshCw, XCircle } from 'lucide-react';
import { toast } from 'sonner';
import { api } from '@/lib/api';

type VerificationState = 'waiting' | 'verifying' | 'verified' | 'error';

export default function VerifyEmailPage() {
    const [state, setState] = useState<VerificationState>('waiting');
    const [message, setMessage] = useState('Check your inbox and open the verification link.');
    const [email, setEmail] = useState('');
    const [isResending, setIsResending] = useState(false);

    useEffect(() => {
        const pendingEmail = sessionStorage.getItem('sentinel_pending_verification_email') || '';
        setEmail(pendingEmail);

        const params = new URLSearchParams(window.location.hash.slice(1));
        const token = params.get('token');
        if (!token) return;

        window.history.replaceState(null, '', '/verify-email');
        setState('verifying');
        setMessage('Verifying your email address...');

        api.post('/auth/verify-email', { token })
            .then((response) => {
                sessionStorage.removeItem('sentinel_pending_verification_email');
                setState('verified');
                setMessage(response.data.message || 'Email verified. You can now sign in.');
            })
            .catch((error) => {
                setState('error');
                setMessage(error.response?.data?.error || 'This verification link is invalid or expired.');
            });
    }, []);

    const resend = async () => {
        const normalizedEmail = email.trim();
        if (!normalizedEmail) {
            toast.error('Enter your email address.');
            return;
        }

        setIsResending(true);
        try {
            const response = await api.post('/auth/resend-verification', { email: normalizedEmail });
            sessionStorage.setItem('sentinel_pending_verification_email', normalizedEmail);
            toast.success(response.data.message);
        } catch {
            toast.error('Could not resend the verification email. Please try again.');
        } finally {
            setIsResending(false);
        }
    };

    const Icon = state === 'verified' ? CheckCircle2 : state === 'error' ? XCircle : Mail;

    return (
        <main className="min-h-screen flex items-center justify-center bg-background p-6">
            <section className="w-full max-w-lg rounded-[2.5rem] border border-border bg-card/70 p-8 sm:p-10 text-center shadow-2xl backdrop-blur-xl">
                <div className="mx-auto mb-7 flex h-16 w-16 items-center justify-center rounded-2xl border border-border bg-background">
                    {state === 'verifying' ? (
                        <Loader2 className="h-7 w-7 animate-spin text-primary" aria-label="Verifying email" />
                    ) : (
                        <Icon className={`h-7 w-7 ${state === 'error' ? 'text-destructive' : 'text-primary'}`} aria-hidden="true" />
                    )}
                </div>

                <h1 className="text-4xl font-display font-black tracking-tight text-foreground">
                    {state === 'verified' ? 'Email Verified' : state === 'error' ? 'Verification Failed' : 'Verify Your Email'}
                </h1>
                <p className="mx-auto mt-4 max-w-sm text-base font-medium leading-relaxed text-muted-foreground">
                    {message}
                </p>

                {state !== 'verified' && state !== 'verifying' && (
                    <div className="mt-8 space-y-3 text-left">
                        <label className="ml-1 block text-xs font-black uppercase tracking-widest text-muted-foreground" htmlFor="verification-email">
                            Email address
                        </label>
                        <input
                            id="verification-email"
                            type="email"
                            autoComplete="email"
                            value={email}
                            onChange={(event) => setEmail(event.target.value)}
                            placeholder="name@example.com"
                            className="h-14 w-full rounded-2xl border border-border bg-background/60 px-5 text-base font-bold outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
                        />
                        <button
                            type="button"
                            onClick={resend}
                            disabled={isResending}
                            className="inline-flex h-14 w-full items-center justify-center rounded-2xl bg-primary px-6 text-sm font-black uppercase tracking-widest text-primary-foreground transition hover:-translate-y-0.5 disabled:pointer-events-none disabled:opacity-50"
                        >
                            {isResending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
                            Resend verification
                        </button>
                    </div>
                )}

                <Link
                    href="/login"
                    className="mt-7 inline-flex min-h-11 items-center justify-center text-sm font-black uppercase tracking-widest text-primary underline-offset-4 hover:underline"
                >
                    {state === 'verified' ? 'Continue to sign in' : 'Back to sign in'}
                </Link>
            </section>
        </main>
    );
}
