'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { toast } from 'sonner';
import { Loader2, ArrowLeft, Calendar as CalendarIcon } from 'lucide-react';
import Link from 'next/link';
import { api, Segment } from '@/lib/api';
import { Controller } from 'react-hook-form';
import { RichTextEditor } from '@/components/ui/RichTextEditor';
import { AiGeneratorModal } from '@/components/campaigns/AiGeneratorModal';

const campaignSchema = z.object({
    name: z.string().min(1, 'Name is required'),
    subject: z.string().min(1, 'Subject is required'),
    content: z.string().min(1, 'Content is required'),
    segment_id: z.string().min(1, 'Segment is required'),
    schedule_type: z.enum(['immediate', 'scheduled']),
    scheduled_time: z.string().optional(),
}).refine((data) => {
    if (data.schedule_type === 'scheduled' && !data.scheduled_time) {
        return false;
    }
    return true;
}, {
    message: "Scheduled time is required for scheduled campaigns",
    path: ["scheduled_time"],
});

type CampaignFormValues = z.infer<typeof campaignSchema>;

export default function NewCampaignPage() {
    const router = useRouter();
    const [isLoading, setIsLoading] = useState(false);
    const [segments, setSegments] = useState<Segment[]>([]);

    const {
        register,
        handleSubmit,
        watch,
        setValue,
        control,
        formState: { errors },
    } = useForm<CampaignFormValues>({
        resolver: zodResolver(campaignSchema),
        defaultValues: {
            schedule_type: 'immediate',
        },
    });

    const scheduleType = watch('schedule_type');

    useEffect(() => {
        const fetchSegments = async () => {
            try {
                const response = await api.get('/segments');
                setSegments(response.data.segments || []);
            } catch (error) {
                console.error('Failed to fetch segments:', error);
                toast.error('Failed to load segments');
            }
        };
        fetchSegments();
    }, []);

    const onSubmit = async (data: CampaignFormValues) => {
        setIsLoading(true);
        try {
            const payload: any = {
                name: data.name,
                subject: data.subject,
                html_body: data.content,
                segment_id: data.segment_id,
                type: data.schedule_type === 'immediate' ? 'I' : 'S',
                delivery_type: 'SEG',
            };

            if (data.schedule_type === 'scheduled' && data.scheduled_time) {
                payload.schedule_at = Math.floor(new Date(data.scheduled_time).getTime() / 1000);
            }

            await api.post('/campaigns', payload);

            toast.success('Campaign created successfully');
            router.push('/campaigns');
        } catch (error: any) {
            console.error('Create campaign error:', error);
            toast.error(error.response?.data?.message || 'Failed to create campaign');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="max-w-3xl mx-auto space-y-8 pb-12">
            <div className="flex items-center gap-4">
                <Link
                    href="/campaigns"
                    className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground"
                >
                    <ArrowLeft className="h-4 w-4" />
                </Link>
                <div>
                    <h1 className="text-3xl font-display font-bold tracking-tight">
                        Create Campaign
                    </h1>
                    <p className="text-muted-foreground">
                        Design and schedule your new email campaign
                    </p>
                </div>
            </div>

            <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
                    <div className="space-y-4">
                        <h3 className="text-lg font-semibold">Campaign Details</h3>
                        <div className="grid gap-4 md:grid-cols-2">
                            <div className="space-y-2">
                                <label className="text-sm font-medium leading-none" htmlFor="name">
                                    Campaign Name
                                </label>
                                <input
                                    {...register('name')}
                                    id="name"
                                    placeholder="e.g. Monthly Newsletter"
                                    className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                                />
                                {errors.name && (
                                    <p className="text-sm text-destructive">{errors.name.message}</p>
                                )}
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-medium leading-none" htmlFor="segment_id">
                                    Target Segment
                                </label>
                                <select
                                    {...register('segment_id')}
                                    id="segment_id"
                                    className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                                >
                                    <option value="">Select a segment</option>
                                    {segments.map((segment) => (
                                        <option key={segment.id} value={segment.id}>
                                            {segment.name} ({segment.contact_count} contacts)
                                        </option>
                                    ))}
                                </select>
                                {errors.segment_id && (
                                    <p className="text-sm text-destructive">{errors.segment_id.message}</p>
                                )}
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium leading-none" htmlFor="subject">
                                Email Subject
                            </label>
                            <input
                                {...register('subject')}
                                id="subject"
                                placeholder="Enter a catchy subject line"
                                className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                            />
                            {errors.subject && (
                                <p className="text-sm text-destructive">{errors.subject.message}</p>
                            )}
                        </div>
                    </div>

                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <h3 className="text-lg font-semibold">Email Content</h3>
                            <AiGeneratorModal
                                onGenerate={(subject, content) => {
                                    setValue('subject', subject, { shouldValidate: true });
                                    setValue('content', content, { shouldValidate: true });
                                    toast.success('Content generated successfully!');
                                }}
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-medium leading-none" htmlFor="content">
                                HTML Content
                            </label>
                            <Controller
                                name="content"
                                control={control}
                                render={({ field }) => (
                                    <RichTextEditor
                                        value={field.value}
                                        onChange={field.onChange}
                                        placeholder="Write your email content here..."
                                    />
                                )}
                            />
                            {errors.content && (
                                <p className="text-sm text-destructive">{errors.content.message}</p>
                            )}
                        </div>
                    </div>

                    <div className="space-y-4">
                        <h3 className="text-lg font-semibold">Schedule</h3>
                        <div className="space-y-4">
                            <div className="flex items-center gap-4">
                                <label className="flex items-center gap-2 text-sm font-medium">
                                    <input
                                        type="radio"
                                        value="immediate"
                                        {...register('schedule_type')}
                                        className="h-4 w-4 text-primary focus:ring-primary"
                                    />
                                    Send Immediately
                                </label>
                                <label className="flex items-center gap-2 text-sm font-medium">
                                    <input
                                        type="radio"
                                        value="scheduled"
                                        {...register('schedule_type')}
                                        className="h-4 w-4 text-primary focus:ring-primary"
                                    />
                                    Schedule for Later
                                </label>
                            </div>

                            {scheduleType === 'scheduled' && (
                                <div className="space-y-2">
                                    <label className="text-sm font-medium leading-none" htmlFor="scheduled_time">
                                        Date & Time
                                    </label>
                                    <input
                                        type="datetime-local"
                                        {...register('scheduled_time')}
                                        id="scheduled_time"
                                        className="flex h-9 w-full max-w-xs rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                                    />
                                    {errors.scheduled_time && (
                                        <p className="text-sm text-destructive">{errors.scheduled_time.message}</p>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="flex justify-end gap-4 pt-4 border-t border-border">
                        <Link
                            href="/campaigns"
                            className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground h-9 px-4 py-2"
                        >
                            Cancel
                        </Link>
                        <button
                            type="submit"
                            disabled={isLoading}
                            className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow hover:bg-primary/90 h-9 px-4 py-2"
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Creating...
                                </>
                            ) : (
                                scheduleType === 'immediate' ? 'Send Now' : 'Schedule Campaign'
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
