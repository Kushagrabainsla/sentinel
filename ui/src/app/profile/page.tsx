'use client';

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { toast } from 'sonner';
import { Loader2, Copy, RefreshCw, Eye, EyeOff, Save, Mail, CheckCircle2, AlertCircle, Trash2 } from 'lucide-react';
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
        <div className="max-w-4xl mx-auto space-y-8 pb-12">
            <div>
                <h1 className="text-3xl font-display font-bold tracking-tight">
                    Profile Settings
                </h1>
                <p className="text-muted-foreground">
                    Manage your account settings and API keys
                </p>
            </div>

            <div className="grid gap-8 md:grid-cols-2">
                {/* Profile Information */}
                <div className="space-y-6">
                    <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
                        <h2 className="text-xl font-semibold mb-4">Personal Information</h2>
                        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium leading-none" htmlFor="email">
                                    Email Address
                                </label>
                                <input
                                    disabled
                                    value={user?.email || ''}
                                    className="flex h-9 w-full rounded-md border border-input bg-muted px-3 py-1 text-sm shadow-sm opacity-50 cursor-not-allowed"
                                />
                                <p className="text-xs text-muted-foreground">Email cannot be changed</p>
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-medium leading-none" htmlFor="name">
                                    Full Name
                                </label>
                                <input
                                    {...register('name')}
                                    id="name"
                                    className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                                />
                                {errors.name && (
                                    <p className="text-sm text-destructive">{errors.name.message}</p>
                                )}
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-medium leading-none" htmlFor="timezone">
                                    Timezone
                                </label>
                                <select
                                    {...register('timezone')}
                                    id="timezone"
                                    className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                                >
                                    {TIMEZONES.map((tz) => (
                                        <option key={tz} value={tz}>
                                            {tz}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div className="pt-2">
                                <button
                                    type="submit"
                                    disabled={isSaving}
                                    className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow hover:bg-primary/90 h-9 px-4 py-2"
                                >
                                    {isSaving ? (
                                        <>
                                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                            Saving...
                                        </>
                                    ) : (
                                        <>
                                            <Save className="mr-2 h-4 w-4" />
                                            Save Changes
                                        </>
                                    )}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>

                {/* API Key Management */}
                <div className="space-y-6">
                    <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
                        <h2 className="text-xl font-semibold mb-4">API Configuration</h2>
                        <div className="space-y-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium leading-none">
                                    Your API Key
                                </label>
                                <div className="relative">
                                    <input
                                        readOnly
                                        type={showApiKey ? "text" : "password"}
                                        value={user?.api_key || ''}
                                        className="flex h-9 w-full rounded-md border border-input bg-muted px-3 py-1 text-sm shadow-sm pr-20 font-mono"
                                    />
                                    <div className="absolute right-1 top-1 flex items-center gap-1">
                                        <button
                                            onClick={() => setShowApiKey(!showApiKey)}
                                            className="p-1.5 text-muted-foreground hover:text-foreground transition-colors rounded-md hover:bg-background"
                                            title={showApiKey ? "Hide API Key" : "Show API Key"}
                                        >
                                            {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                        </button>
                                        <button
                                            onClick={copyApiKey}
                                            className="p-1.5 text-muted-foreground hover:text-foreground transition-colors rounded-md hover:bg-background"
                                            title="Copy API Key"
                                        >
                                            <Copy className="h-4 w-4" />
                                        </button>
                                    </div>
                                </div>
                                <p className="text-xs text-muted-foreground">
                                    Keep this key secret. It grants full access to your account.
                                </p>
                            </div>

                            <div className="pt-2">
                                <button
                                    onClick={handleRegenerateApiKey}
                                    disabled={isRegenerating}
                                    className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 border border-destructive/50 text-destructive hover:bg-destructive/10 h-9 px-4 py-2"
                                >
                                    {isRegenerating ? (
                                        <>
                                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                            Regenerating...
                                        </>
                                    ) : (
                                        <>
                                            <RefreshCw className="mr-2 h-4 w-4" />
                                            Regenerate Key
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Google Integration Card */}
                    <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
                        <h2 className="text-xl font-semibold mb-4">Email Integration</h2>
                        <div className="space-y-4">
                            {user?.google_connected ? (
                                <>
                                    <div className="flex items-center gap-3 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                                        <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                                        <div className="flex-1">
                                            <p className="text-sm font-medium">Connected to Google</p>
                                            <p className="text-xs text-muted-foreground">{user.google_email}</p>
                                        </div>
                                        <button
                                            onClick={handleDisconnectGoogle}
                                            className="p-1.5 text-muted-foreground hover:text-destructive transition-colors rounded-md hover:bg-destructive/10"
                                            title="Disconnect Google Account"
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </button>
                                    </div>

                                    <div className="space-y-3">
                                        <div className="flex items-center justify-between">
                                            <div className="space-y-0.5">
                                                <label className="text-sm font-medium">Use Gmail for Campaigns</label>
                                                <p className="text-xs text-muted-foreground">
                                                    When enabled, emails will be sent through your Gmail account instead of our default server.
                                                </p>
                                            </div>
                                            <button
                                                onClick={() => handleToggleGmail(!user.gmail_enabled)}
                                                disabled={isUpdatingGmailStatus}
                                                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${user.gmail_enabled ? 'bg-primary' : 'bg-input'}`}
                                            >
                                                <span
                                                    className={`inline-block h-4 w-4 transform rounded-full bg-background transition-transform ${user.gmail_enabled ? 'translate-x-6' : 'translate-x-1'}`}
                                                />
                                            </button>
                                        </div>
                                    </div>
                                </>
                            ) : (
                                <>
                                    <div className="flex items-start gap-3 p-3 rounded-lg bg-orange-500/10 border border-orange-500/20">
                                        <AlertCircle className="h-5 w-5 text-orange-500 shrink-0 mt-0.5" />
                                        <div>
                                            <p className="text-sm font-medium text-orange-900 dark:text-orange-400">Gmail Not Connected</p>
                                            <p className="text-xs text-orange-800/80 dark:text-orange-400/80">
                                                Authorizing Gmail allows you to send marketing emails directly from your own mailbox, improving deliverability.
                                            </p>
                                        </div>
                                    </div>
                                    <button
                                        onClick={handleConnectGoogle}
                                        disabled={isConnectingGoogle}
                                        className="w-full inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-background border border-input hover:bg-accent hover:text-accent-foreground h-9 px-4 py-2"
                                    >
                                        {isConnectingGoogle ? (
                                            <>
                                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                                Connecting...
                                            </>
                                        ) : (
                                            <>
                                                <Mail className="mr-2 h-4 w-4 text-red-500" />
                                                Connect Gmail Account
                                            </>
                                        )}
                                    </button>
                                </>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
