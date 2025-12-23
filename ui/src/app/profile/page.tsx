'use client';

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { toast } from 'sonner';
import {
    Loader2, Copy, RefreshCw, Eye, EyeOff, Save, Mail,
    CheckCircle2, AlertCircle, Trash2, Globe, User as UserIcon,
    Key, Lock, Shield, ExternalLink, ChevronDown
} from 'lucide-react';
import { api, User } from '@/lib/api';

const profileSchema = z.object({
    name: z.string().min(1, 'Name is required'),
    timezone: z.string().optional(),
});

type ProfileFormValues = z.infer<typeof profileSchema>;

const TIMEZONES = [
    "UTC",
    "America/New_York",
    "America/Los_Angeles",
    "America/Chicago",
    "Europe/London",
    "Europe/Paris",
    "Europe/Berlin",
    "Asia/Tokyo",
    "Asia/Shanghai",
    "Asia/Singapore",
    "Australia/Sydney",
    "Pacific/Auckland",
];

export default function ProfilePage() {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [isRegenerating, setIsRegenerating] = useState(false);
    const [showApiKey, setShowApiKey] = useState(false);
    const [isConnectingGoogle, setIsConnectingGoogle] = useState(false);
    const [isUpdatingGmailStatus, setIsUpdatingGmailStatus] = useState(false);

    const {
        register,
        handleSubmit,
        setValue,
        formState: { errors },
    } = useForm<ProfileFormValues>({
        resolver: zodResolver(profileSchema),
    });

    useEffect(() => {
        fetchUser();
    }, []);

    const fetchUser = async () => {
        try {
            const response = await api.get('/auth/me');
            const userData = response.data.user;
            setUser(userData);
            setValue('name', userData.name);
            setValue('timezone', userData.timezone || 'UTC');
        } catch (error) {
            console.error('Failed to fetch user:', error);
            toast.error('Failed to load profile');
        } finally {
            setIsLoading(false);
        }
    };

    const onSubmit = async (data: ProfileFormValues) => {
        setIsSaving(true);
        try {
            const response = await api.post('/auth/update', data);
            setUser(response.data.user);
            toast.success('Profile updated successfully');
        } catch (error: any) {
            console.error('Update profile error:', error);
            toast.error(error.response?.data?.message || 'Failed to update profile');
        } finally {
            setIsSaving(false);
        }
    };

    const handleRegenerateApiKey = async () => {
        if (!confirm('Are you sure you want to regenerate your API key? The old key will stop working immediately.')) {
            return;
        }

        setIsRegenerating(true);
        try {
            const response = await api.post('/auth/regenerate-key');
            const newApiKey = response.data.api_key;

            if (user) {
                setUser({ ...user, api_key: newApiKey });
            }

            // Update local storage if needed
            localStorage.setItem('sentinel_api_key', newApiKey);

            toast.success('API key regenerated successfully');
        } catch (error: any) {
            console.error('Regenerate key error:', error);
            toast.error(error.response?.data?.message || 'Failed to regenerate API key');
        } finally {
            setIsRegenerating(false);
        }
    };

    const copyApiKey = () => {
        if (user?.api_key) {
            navigator.clipboard.writeText(user.api_key);
            toast.success('API key copied to clipboard');
        }
    };

    const handleConnectGoogle = async () => {
        setIsConnectingGoogle(true);
        try {
            const response = await api.get('/auth/google/url');
            window.location.href = response.data.url;
        } catch (error: any) {
            console.error('Failed to get Google auth URL:', error);
            toast.error('Failed to initiate Google connection');
            setIsConnectingGoogle(false);
        }
    };

    const handleToggleGmail = async (enabled: boolean) => {
        setIsUpdatingGmailStatus(true);
        try {
            const response = await api.post('/auth/google/toggle-gmail', { enabled });
            setUser(response.data.user);
            toast.success(enabled ? 'Gmail sending enabled' : 'Gmail sending disabled');
        } catch (error: any) {
            console.error('Toggle Gmail error:', error);
            toast.error('Failed to update Gmail settings');
        } finally {
            setIsUpdatingGmailStatus(false);
        }
    };

    const handleDisconnectGoogle = async () => {
        if (!confirm('Are you sure you want to disconnect your Google account? You will no longer be able to send emails through Gmail.')) {
            return;
        }

        try {
            const response = await api.post('/auth/google/disconnect');
            setUser(response.data.user);
            toast.success('Google account disconnected');
        } catch (error: any) {
            console.error('Disconnect Google error:', error);
            toast.error('Failed to disconnect Google account');
        }
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-96">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    return (
        <div className="max-w-6xl mx-auto space-y-10 pb-20">
            {/* Hero Header Section */}
            <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-primary/10 via-background to-background border border-border p-8 md:p-12 shadow-xl">
                <div className="absolute top-0 right-0 -mt-20 -mr-20 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />
                <div className="flex flex-col md:flex-row items-center gap-8 relative z-10">
                    <div className="w-32 h-32 rounded-3xl bg-gradient-to-tr from-blue-600 to-blue-600/60 flex items-center justify-center text-white shadow-2xl ring-8 ring-background">
                        <UserIcon className="w-12 h-12 opacity-90" />
                    </div>
                    <div className="flex-1 text-center md:text-left space-y-3">
                        <div className="flex flex-wrap items-center justify-center md:justify-start gap-4">
                            <h1 className="text-4xl font-display font-bold tracking-tight">
                                {user?.name || 'Your Profile'}
                            </h1>

                        </div>
                        <p className="text-xl text-muted-foreground flex items-center justify-center md:justify-start gap-2">
                            <Mail className="w-5 h-5 text-primary/60" />
                            {user?.email}
                        </p>
                        <div className="pt-4 flex flex-wrap items-center justify-center md:justify-start gap-6 text-sm text-muted-foreground">
                            <div className="flex items-center gap-2 bg-muted/50 px-4 py-2 rounded-xl border border-border transition-colors hover:bg-muted">
                                <CheckCircle2 className="w-4 h-4 text-primary" />
                                <span className="font-medium">Account Verified</span>
                            </div>
                            {user?.created_at && (
                                <div className="flex items-center gap-2 bg-muted/50 px-4 py-2 rounded-xl border border-border transition-colors hover:bg-muted">
                                    <Globe className="w-4 h-4 text-primary/60" />
                                    <span>Joined {new Date(user.created_at * 1000).toLocaleDateString(undefined, { month: 'long', year: 'numeric' })}</span>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Personal Information Card */}
                <div className="rounded-3xl border border-border bg-card/60 backdrop-blur-sm p-8 shadow-sm transition-all hover:shadow-md hover:border-primary/20 flex flex-col h-full">
                    <div className="flex items-center gap-4 mb-8">
                        <div className="p-3 rounded-2xl bg-blue-500/10 text-blue-500">
                            <Save className="w-7 h-7" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-bold">Personal Information</h2>
                            <p className="text-sm text-muted-foreground">Manage your identity and preferences</p>
                        </div>
                    </div>

                    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 flex-1">
                        <div className="space-y-2">
                            <label className="text-sm font-semibold tracking-wide flex items-center gap-2" htmlFor="email">
                                <Mail className="w-4 h-4 text-muted-foreground" />
                                Email Address
                            </label>
                            <input
                                disabled
                                value={user?.email || ''}
                                className="flex h-12 w-full rounded-xl border border-input bg-muted/50 px-4 py-2 text-sm shadow-sm opacity-60 cursor-not-allowed font-medium"
                            />
                            <p className="text-xs text-muted-foreground italic ml-1">Account email cannot be changed for security</p>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-semibold tracking-wide flex items-center gap-2" htmlFor="name">
                                <UserIcon className="w-4 h-4 text-muted-foreground" />
                                Full Name
                            </label>
                            <input
                                {...register('name')}
                                id="name"
                                placeholder="Enter your full name"
                                className="flex h-12 w-full rounded-xl border border-input bg-background px-4 py-2 text-sm shadow-sm transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/20 focus-visible:border-primary"
                            />
                            {errors.name && (
                                <p className="text-xs text-destructive mt-1 font-medium">{errors.name.message}</p>
                            )}
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-semibold tracking-wide flex items-center gap-2" htmlFor="timezone">
                                <Globe className="w-4 h-4 text-muted-foreground" />
                                Default Timezone
                            </label>
                            <div className="relative group/select">
                                <select
                                    {...register('timezone')}
                                    id="timezone"
                                    className="flex h-12 w-full rounded-xl border border-input bg-background px-4 py-2 text-sm shadow-sm transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/20 focus-visible:border-primary appearance-none cursor-pointer pr-10"
                                >
                                    {TIMEZONES.map((tz) => (
                                        <option key={tz} value={tz}>
                                            {tz.replace('_', ' ')}
                                        </option>
                                    ))}
                                </select>
                                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none group-focus-within/select:text-primary transition-colors" />
                            </div>
                        </div>

                        <div className="pt-4 mt-auto">
                            <button
                                type="submit"
                                disabled={isSaving}
                                className="w-full inline-flex items-center justify-center rounded-xl text-sm font-bold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary hover:scale-[1.02] active:scale-[0.98] disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow-lg h-12 px-8"
                            >
                                {isSaving ? (
                                    <>
                                        <Loader2 className="mr-3 h-5 w-5 animate-spin" />
                                        Updating Profile...
                                    </>
                                ) : (
                                    <>
                                        <Save className="mr-3 h-5 w-5" />
                                        Save Changes
                                    </>
                                )}
                            </button>
                        </div>
                    </form>
                </div>

                {/* Right Column Stack */}
                <div className="space-y-8">
                    {/* API Configuration Card */}
                    <div className="rounded-3xl border border-border bg-card/60 backdrop-blur-sm p-8 shadow-sm transition-all hover:shadow-md hover:border-blue-500/20">
                        <div className="flex items-center gap-4 mb-8">
                            <div className="p-3 rounded-2xl bg-blue-500/10 text-blue-500">
                                <RefreshCw className="w-7 h-7" />
                            </div>
                            <div>
                                <h2 className="text-2xl font-bold">API Configuration</h2>
                                <p className="text-sm text-muted-foreground">Manage your secret access keys</p>
                            </div>
                        </div>

                        <div className="space-y-6">
                            <div className="space-y-2">
                                <label className="text-sm font-semibold tracking-wide flex items-center gap-2">
                                    <Key className="w-4 h-4 text-muted-foreground" />
                                    Active API Key
                                </label>
                                <div className="relative group">
                                    <input
                                        readOnly
                                        type={showApiKey ? "text" : "password"}
                                        value={user?.api_key || ''}
                                        className="flex h-12 w-full rounded-xl border border-input bg-muted/30 px-4 py-2 text-sm shadow-inner pr-24 font-mono transition-all group-hover:bg-muted/50"
                                    />
                                    <div className="absolute right-2 top-2 flex items-center gap-1">
                                        <button
                                            onClick={() => setShowApiKey(!showApiKey)}
                                            className="p-2 text-muted-foreground hover:text-foreground hover:bg-background/80 transition-all rounded-lg"
                                            title={showApiKey ? "Hide API Key" : "Show API Key"}
                                        >
                                            {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                        </button>
                                        <button
                                            onClick={copyApiKey}
                                            className="p-2 text-muted-foreground hover:text-primary hover:bg-primary/10 transition-all rounded-lg"
                                            title="Copy API Key"
                                        >
                                            <Copy className="h-4 w-4" />
                                        </button>
                                    </div>
                                </div>
                                <p className="text-[11px] text-amber-600/80 font-medium flex items-center gap-1 ml-1">
                                    <AlertCircle className="w-3 h-3" />
                                    Warning: Treat this key like a password.
                                </p>
                            </div>

                            <div className="pt-2">
                                <button
                                    onClick={handleRegenerateApiKey}
                                    disabled={isRegenerating}
                                    className="w-full inline-flex items-center justify-center rounded-xl text-sm font-bold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-destructive/20 border border-destructive/30 text-destructive hover:bg-destructive/5 hover:border-destructive h-12 px-6"
                                >
                                    {isRegenerating ? (
                                        <>
                                            <Loader2 className="mr-3 h-5 w-5 animate-spin" />
                                            Generating New Key...
                                        </>
                                    ) : (
                                        <>
                                            <RefreshCw className="mr-3 h-5 w-5" />
                                            Regenerate Secret Key
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Email Integration Card */}
                    <div className="rounded-3xl border border-border bg-card/60 backdrop-blur-sm p-8 shadow-sm transition-all hover:shadow-md hover:border-blue-500/20">
                        <div className="flex items-center gap-4 mb-8">
                            <div className="p-3 rounded-2xl bg-blue-500/10 text-blue-500">
                                <Mail className="w-7 h-7" />
                            </div>
                            <div>
                                <h2 className="text-2xl font-bold">Email Integration</h2>
                                <p className="text-sm text-muted-foreground">Authorize third-party email providers</p>
                            </div>
                        </div>

                        <div className="space-y-6">
                            {user?.google_connected ? (
                                <div className="space-y-6">
                                    <div className="flex items-center gap-4 p-5 rounded-2xl bg-emerald-500/5 border border-emerald-500/10 relative group">
                                        <div className="w-12 h-12 rounded-xl bg-emerald-500/20 flex items-center justify-center text-emerald-600">
                                            <CheckCircle2 className="h-6 w-6" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-bold text-foreground">Google Connected</p>
                                            <p className="text-xs text-muted-foreground truncate">{user.google_email}</p>
                                        </div>
                                        <button
                                            onClick={handleDisconnectGoogle}
                                            className="p-3 text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-all rounded-xl border border-transparent hover:border-destructive/20"
                                            title="Disconnect Google Account"
                                        >
                                            <Trash2 className="h-5 w-5" />
                                        </button>
                                    </div>

                                    <div className="space-y-4 pt-2">
                                        <div className="flex items-center justify-between p-4 rounded-2xl bg-muted/30 border border-border/50">
                                            <div className="space-y-1 pr-4">
                                                <label className="text-sm font-bold flex items-center gap-2">
                                                    Use Gmail for Campaigns
                                                </label>
                                                <p className="text-[11px] text-muted-foreground leading-relaxed">
                                                    Route all outgoing emails through your personal Gmail SMTP for higher deliverability.
                                                </p>
                                            </div>
                                            <button
                                                onClick={() => handleToggleGmail(!user.gmail_enabled)}
                                                disabled={isUpdatingGmailStatus}
                                                className={`relative inline-flex h-7 w-12 shrink-0 items-center rounded-full transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${user.gmail_enabled ? 'bg-emerald-500' : 'bg-input hover:bg-input/80'}`}
                                            >
                                                <span
                                                    className={`inline-block h-5 w-5 transform rounded-full bg-white shadow-md transition-transform duration-200 ${user.gmail_enabled ? 'translate-x-6' : 'translate-x-1'}`}
                                                />
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="space-y-6">
                                    <div className="flex items-start gap-4 p-5 rounded-2xl bg-amber-500/5 border border-amber-500/10">
                                        <div className="p-2 rounded-lg bg-amber-500/10 text-amber-600 shrink-0">
                                            <AlertCircle className="h-6 w-6" />
                                        </div>
                                        <div>
                                            <p className="text-sm font-bold text-foreground">Gmail Not Optimized</p>
                                            <p className="text-xs text-muted-foreground leading-relaxed mt-1">
                                                Connecting your Gmail account improves email deliverability and helps you avoid spam filters.
                                            </p>
                                        </div>
                                    </div>
                                    <button
                                        onClick={handleConnectGoogle}
                                        disabled={isConnectingGoogle}
                                        className="w-full inline-flex items-center justify-center rounded-xl text-sm font-bold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary hover:bg-muted bg-background border border-input h-12 px-6 shadow-sm hover:scale-[1.01]"
                                    >
                                        {isConnectingGoogle ? (
                                            <>
                                                <Loader2 className="mr-3 h-5 w-5 animate-spin text-primary" />
                                                Initiating Secure OAuth...
                                            </>
                                        ) : (
                                            <>
                                                <svg className="mr-3 h-5 w-5" viewBox="0 0 24 24">
                                                    <path
                                                        fill="currentColor"
                                                        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                                                        style={{ fill: '#4285F4' }}
                                                    />
                                                    <path
                                                        fill="currentColor"
                                                        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                                                        style={{ fill: '#34A853' }}
                                                    />
                                                    <path
                                                        fill="currentColor"
                                                        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                                                        style={{ fill: '#FBBC05' }}
                                                    />
                                                    <path
                                                        fill="currentColor"
                                                        d="M12 5.38c1.62 0 3.06.56 4.21 1.66l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                                                        style={{ fill: '#EA4335' }}
                                                    />
                                                </svg>
                                                Connect Google Account
                                            </>
                                        )}
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
