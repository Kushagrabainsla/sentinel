'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { CheckCircle2, Loader2, Mail, XCircle } from 'lucide-react';
import { toast } from 'sonner';
import { api } from '@/lib/api';

type VerificationState = 'waiting' | 'verifying' | 'verified' | 'error';

export default function VerifyEmailPage() {
    const router = useRouter();
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
                setMessage(response.data.message || 'Email verified. Redirecting you to the dashboard...');
                // AuthGuard sends signed-out users on to /login, which returns to the dashboard after sign-in.
                setTimeout(() => router.replace('/dashboard'), 1500);
            })
            .catch((error) => {
                setState('error');
                setMessage(error.response?.data?.error || 'This verification link is invalid or expired.');
            });
    }, [router]);

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
    const title = state === 'verified' ? 'Email Verified' : state === 'error' ? 'Verification Failed' : 'Verify Your Email';

    return (
        <div className="min-h-screen flex items-center justify-center bg-background relative overflow-hidden p-6">
            {/* Ambient Background Glows */}
            <div className="absolute top-[-10%] right-[-10%] w-[40%] h-[40%] bg-primary/10 blur-[120px] rounded-full pointer-events-none" />
            <div className="absolute bottom-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/5 blur-[120px] rounded-full pointer-events-none" />

            <div className="w-full max-w-lg space-y-12 relative z-10">
                <div className="text-center space-y-4">
                    <div className="flex justify-center mb-8">
                        <div className="relative group">
                            <div className="absolute -inset-1 bg-gradient-to-r from-primary to-purple-600 rounded-2xl blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200"></div>
                            <div className="relative h-20 w-20 bg-card border border-border rounded-2xl flex items-center justify-center shadow-2xl transition-transform group-hover:scale-105 duration-300">
                                <img src="/images/sentinel-logo.png" alt="Sentinel Logo" className="h-12 w-auto" />
                            </div>
                        </div>
                    </div>
                    <div className="space-y-2">
                        <p className="text-xs font-black text-primary uppercase tracking-[0.3em]">
                            Step 2 of 2
                        </p>
                        <h1 className="text-5xl font-display font-black tracking-tighter text-foreground">
                            {title}
                        </h1>
                        <p className="text-muted-foreground font-medium text-lg">
                            {message}
                        </p>
                    </div>
                </div>

                <div className="group rounded-[2.5rem] bg-card/60 backdrop-blur-xl border border-border p-10 shadow-2xl transition-all hover:border-primary/20 relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-8 opacity-5 pointer-events-none group-hover:rotate-12 transition-transform duration-500">
                        <Icon className="h-24 w-24" />
                    </div>

                    {state === 'verifying' && (
                        <div className="flex justify-center py-6 relative">
                            <Loader2 className="h-10 w-10 animate-spin text-primary" aria-label="Verifying email" />
                        </div>
                    )}

                    {state === 'verified' && (
                        <Link
                            href="/dashboard"
                            className="w-full inline-flex items-center justify-center rounded-2xl text-base font-black uppercase tracking-[0.2em] transition-all focus:ring-4 focus:ring-primary/20 bg-primary text-primary-foreground shadow-2xl shadow-primary/30 hover:shadow-primary/40 hover:-translate-y-1 active:translate-y-0 h-16 px-12 pt-1 relative"
                        >
                            Continue to Dashboard
                        </Link>
                    )}

                    {(state === 'waiting' || state === 'error') && (
                        <form
                            onSubmit={(event) => {
                                event.preventDefault();
                                resend();
                            }}
                            className="space-y-4 relative"
                        >
                            <div className="space-y-2">
                                <label className="text-xs font-black text-muted-foreground uppercase tracking-widest ml-1" htmlFor="verification-email">
                                    Email Address
                                </label>
                                <div className="relative">
                                    <Mail className="absolute left-5 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground group-focus-within:text-primary transition-colors" />
                                    <input
                                        id="verification-email"
                                        type="email"
                                        autoComplete="email"
                                        value={email}
                                        onChange={(event) => setEmail(event.target.value)}
                                        placeholder="name@example.com"
                                        className="flex h-16 w-full rounded-2xl border border-border bg-background/50 px-5 py-2 pl-14 text-base font-bold shadow-sm transition-all focus:ring-4 focus:ring-primary/10 focus:border-primary outline-none"
                                    />
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={isResending}
                                className="w-full inline-flex items-center justify-center rounded-2xl text-base font-black uppercase tracking-[0.2em] transition-all focus:ring-4 focus:ring-primary/20 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow-2xl shadow-primary/30 hover:shadow-primary/40 hover:-translate-y-1 active:translate-y-0 h-16 px-12 group pt-1"
                            >
                                {isResending ? (
                                    <>
                                        <Loader2 className="mr-3 h-5 w-5 animate-spin" />
                                        Sending...
                                    </>
                                ) : (
                                    'Resend Verification'
                                )}
                            </button>
                        </form>
                    )}
                </div>

                <div className="text-center">
                    <p className="text-sm font-medium text-muted-foreground uppercase tracking-widest opacity-80">
                        {state === 'verified' ? 'Not redirected?' : 'Already verified?'}{' '}
                        <Link href={state === 'verified' ? '/dashboard' : '/login'} className="font-black text-primary hover:text-primary/80 transition-colors border-b-2 border-primary/20 hover:border-primary">
                            {state === 'verified' ? 'Go to Dashboard' : 'Sign In'}
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
}
