'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { toast } from 'sonner';
import { Loader2, Mail, Lock } from 'lucide-react';
import { api } from '@/lib/api';

const loginSchema = z.object({
    email: z.string().email('Invalid email address'),
    password: z.string().min(1, 'Password is required'),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export default function LoginPage() {
    const router = useRouter();
    const [isLoading, setIsLoading] = useState(false);

    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<LoginFormValues>({
        resolver: zodResolver(loginSchema),
    });

    const onSubmit = async (data: LoginFormValues) => {
        setIsLoading(true);
        try {
            const response = await api.post('/auth/login', data);
            const { api_key, name } = response.data.user;

            // Store API key and user info
            localStorage.setItem('sentinel_api_key', api_key);
            localStorage.setItem('sentinel_user_name', name);

            toast.success('Welcome back!');
            router.push('/dashboard');
        } catch (error: any) {
            console.error('Login error:', error);
            toast.error(error.response?.data?.message || 'Failed to login. Please check your credentials.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-background relative overflow-hidden p-6">
            {/* Ambient Background Glows */}
            <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/10 blur-[120px] rounded-full pointer-events-none" />
            <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-primary/5 blur-[120px] rounded-full pointer-events-none" />

            <div className="w-full max-w-lg space-y-12 relative z-10">
                <div className="text-center space-y-4">
                    <div className="flex justify-center mb-8">
                        <div className="relative group">
                            <div className="absolute -inset-1 bg-gradient-to-r from-primary to-purple-600 rounded-2xl blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200"></div>
                            <div className="relative h-20 w-20 bg-card border border-border rounded-2xl flex items-center justify-center shadow-2xl">
                                <img src="/images/sentinel-logo.png" alt="Sentinel Logo" className="h-12 w-auto" />
                            </div>
                        </div>
                    </div>
                    <div className="space-y-2">
                        <h1 className="text-5xl font-display font-black tracking-tighter text-foreground">
                            Welcome Back
                        </h1>
                        <p className="text-muted-foreground font-medium text-lg">
                            Sign in to access your email campaigns
                        </p>
                    </div>
                </div>

                <div className="group rounded-[2.5rem] bg-card/60 backdrop-blur-xl border border-border p-10 shadow-2xl transition-all hover:border-primary/20 relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-8 opacity-5 pointer-events-none group-hover:scale-110 transition-transform">
                        <Lock className="h-24 w-24" />
                    </div>

                    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 relative">
                        <div className="space-y-2">
                            <label className="text-xs font-black text-muted-foreground uppercase tracking-widest ml-1" htmlFor="email">
                                Email Address
                            </label>
                            <div className="relative">
                                <Mail className="absolute left-5 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground group-focus-within:text-primary transition-colors" />
                                <input
                                    {...register('email')}
                                    id="email"
                                    type="email"
                                    placeholder="name@example.com"
                                    className="flex h-16 w-full rounded-2xl border border-border bg-background/50 px-5 py-2 pl-14 text-base font-bold shadow-sm transition-all focus:ring-4 focus:ring-primary/10 focus:border-primary outline-none"
                                />
                            </div>
                            {errors.email && (
                                <p className="text-xs font-bold text-destructive mt-1 flex items-center gap-1">
                                    <div className="w-1 h-3 bg-destructive rounded-full" /> {errors.email.message}
                                </p>
                            )}
                        </div>

                        <div className="space-y-2">
                            <label className="text-xs font-black text-muted-foreground uppercase tracking-widest ml-1" htmlFor="password">
                                Password
                            </label>
                            <div className="relative">
                                <Lock className="absolute left-5 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground group-focus-within:text-primary transition-colors" />
                                <input
                                    {...register('password')}
                                    id="password"
                                    type="password"
                                    placeholder="••••••••"
                                    className="flex h-16 w-full rounded-2xl border border-border bg-background/50 px-5 py-2 pl-14 text-base font-bold shadow-sm transition-all focus:ring-4 focus:ring-primary/10 focus:border-primary outline-none"
                                />
                            </div>
                            {errors.password && (
                                <p className="text-xs font-bold text-destructive mt-1 flex items-center gap-1">
                                    <div className="w-1 h-3 bg-destructive rounded-full" /> {errors.password.message}
                                </p>
                            )}
                        </div>

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full inline-flex items-center justify-center rounded-2xl text-base font-black uppercase tracking-[0.2em] transition-all focus:ring-4 focus:ring-primary/20 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow-2xl shadow-primary/30 hover:shadow-primary/40 hover:-translate-y-1 active:translate-y-0 h-16 px-12 group pt-1"
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 className="mr-3 h-5 w-5 animate-spin" />
                                    Signing in...
                                </>
                            ) : (
                                'Sign In'
                            )}
                        </button>
                    </form>
                </div>

                <div className="text-center">
                    <p className="text-sm font-medium text-muted-foreground uppercase tracking-widest opacity-80">
                        Don't have an account?{' '}
                        <Link href="/register" className="font-black text-primary hover:text-primary/80 transition-colors border-b-2 border-primary/20 hover:border-primary">
                            Create Account
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
}
