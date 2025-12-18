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
    segment_id: z.string().min(1, 'Segment is required'),
    schedule_type: z.enum(['immediate', 'scheduled', 'ab_test']),
    scheduled_time: z.string().optional(),

    // Standard Campaign Fields
    subject: z.string().optional(),
    content: z.string().optional(),

    // A/B Test Fields
    test_percentage: z.number().min(5).max(90).optional(),
    decision_duration: z.number().min(1).max(72).optional(), // Hours
    variations: z.array(z.object({
        subject: z.string(),
        content: z.string(),
        tone: z.string().optional()
    })).optional()
}).superRefine((data, ctx) => {
    if (data.schedule_type === 'scheduled' && !data.scheduled_time) {
        ctx.addIssue({
            code: z.ZodIssueCode.custom,
            message: "Scheduled time is required",
            path: ["scheduled_time"]
        });
    }

    if (data.schedule_type === 'ab_test') {
        if (!data.variations || data.variations.length !== 3) {
            ctx.addIssue({
                code: z.ZodIssueCode.custom,
                message: "3 variations are required for A/B testing",
                path: ["variations"]
            });
        } else {
            data.variations.forEach((v, i) => {
                if (!v.subject) ctx.addIssue({ code: z.ZodIssueCode.custom, message: "Subject required", path: [`variations`, i, `subject`] });
                if (!v.content) ctx.addIssue({ code: z.ZodIssueCode.custom, message: "Content required", path: [`variations`, i, `content`] });
            });
        }
    } else {
        if (!data.subject) ctx.addIssue({ code: z.ZodIssueCode.custom, message: "Subject is required", path: ["subject"] });
        if (!data.content) ctx.addIssue({ code: z.ZodIssueCode.custom, message: "Content is required", path: ["content"] });
    }
});

type CampaignFormValues = z.infer<typeof campaignSchema>;

export default function NewCampaignPage() {
    const router = useRouter();
    const [isLoading, setIsLoading] = useState(false);
    const [segments, setSegments] = useState<Segment[]>([]);
    const [activeVariation, setActiveVariation] = useState<0 | 1 | 2>(0);

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
            test_percentage: 20,
            decision_duration: 4,
            variations: [
                { subject: '', content: '', tone: 'A' },
                { subject: '', content: '', tone: 'B' },
                { subject: '', content: '', tone: 'C' }
            ]
        },
    });

    const scheduleType = watch('schedule_type');

    useEffect(() => {
        const fetchSegments = async () => {
            try {
                const response = await api.get('/segments');
                const allSegments = response.data.segments || [];
                // Only show active segments in the dropdown for selection
                setSegments(allSegments.filter((s: Segment) => s.status === 'A'));
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
                segment_id: data.segment_id,
                delivery_type: 'SEG',
            };

            if (data.schedule_type === 'ab_test') {
                payload.type = 'AB';
                payload.variations = data.variations;

                // Calculate decision time
                const decisionTime = Math.floor(Date.now() / 1000) + ((data.decision_duration || 4) * 3600);

                payload.ab_test_config = {
                    test_percentage: data.test_percentage,
                    decision_time: decisionTime
                };

                // For A/B test, we don't set top-level subject/content
                payload.subject = "A/B Test Campaign";
                payload.html_body = "<p>A/B Test Campaign</p>";
            } else {
                payload.type = data.schedule_type === 'immediate' ? 'I' : 'S';
                payload.subject = data.subject;
                payload.html_body = data.content;

                if (data.schedule_type === 'scheduled' && data.scheduled_time) {
                    payload.schedule_at = Math.floor(new Date(data.scheduled_time).getTime() / 1000);
                }
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
                    </div>

                    {scheduleType === 'ab_test' ? (
                        <div className="space-y-6">
                            <div className="flex items-center justify-between">
                                <h3 className="text-lg font-semibold">A/B Test Variations</h3>
                                <AiGeneratorModal
                                    mode="ab_test"
                                    onGenerate={(s, c, variations) => {
                                        console.log('Received variations:', variations);
                                        if (variations && variations.length > 0) {
                                            // Take first 3 if more than 3
                                            const validVariations = variations.slice(0, 3);
                                            setValue('variations', validVariations, { shouldValidate: true });

                                            if (validVariations.length === 3) {
                                                toast.success('3 Variations generated!');
                                            } else {
                                                toast.warning(`Generated ${validVariations.length} variations. 3 are required for A/B testing.`);
                                            }
                                        } else {
                                            toast.error('Failed to generate variations. Please try again.');
                                            console.error('No variations received');
                                        }
                                    }}
                                />
                            </div>

                            {/* A/B Test Config */}
                            <div className="grid grid-cols-2 gap-6 p-4 bg-muted/30 rounded-lg border border-border">
                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Test Percentage ({watch('test_percentage')}%)</label>
                                    <input
                                        type="range"
                                        min="5"
                                        max="90"
                                        step="5"
                                        {...register('test_percentage', { valueAsNumber: true })}
                                        className="w-full"
                                    />
                                    <p className="text-xs text-muted-foreground">Percentage of users to test on (split 3 ways)</p>
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Test Duration (Hours)</label>
                                    <input
                                        type="number"
                                        min="1"
                                        max="72"
                                        {...register('decision_duration', { valueAsNumber: true })}
                                        className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm"
                                    />
                                    <p className="text-xs text-muted-foreground">Time to wait before declaring a winner</p>
                                </div>
                            </div>

                            {/* Tabs */}
                            <div className="space-y-4">
                                <div className="flex gap-2 border-b border-border">
                                    {[0, 1, 2].map((i) => (
                                        <button
                                            key={i}
                                            type="button"
                                            onClick={() => setActiveVariation(i as 0 | 1 | 2)}
                                            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeVariation === i
                                                ? 'border-primary text-primary'
                                                : 'border-transparent text-muted-foreground hover:text-foreground'
                                                }`}
                                        >
                                            Variation {['A', 'B', 'C'][i]}
                                            {watch(`variations.${i}.tone`) && <span className="ml-2 text-xs bg-muted px-1.5 py-0.5 rounded">{watch(`variations.${i}.tone`)}</span>}
                                        </button>
                                    ))}
                                </div>

                                <div className="space-y-4 animate-in fade-in slide-in-from-left-2 duration-200" key={activeVariation}>
                                    <div className="space-y-2">
                                        <label className="text-sm font-medium">Subject Line ({['A', 'B', 'C'][activeVariation]})</label>
                                        <input
                                            {...register(`variations.${activeVariation}.subject`)}
                                            placeholder={`Subject for Variation ${['A', 'B', 'C'][activeVariation]}`}
                                            className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                                        />
                                        {errors.variations?.[activeVariation]?.subject && (
                                            <p className="text-sm text-destructive">{errors.variations[activeVariation]?.subject?.message}</p>
                                        )}
                                    </div>

                                    <div className="space-y-2">
                                        <label className="text-sm font-medium">Content ({['A', 'B', 'C'][activeVariation]})</label>
                                        <Controller
                                            name={`variations.${activeVariation}.content`}
                                            control={control}
                                            render={({ field }) => (
                                                <RichTextEditor
                                                    value={field.value || ''}
                                                    onChange={field.onChange}
                                                    placeholder={`Content for Variation ${['A', 'B', 'C'][activeVariation]}...`}
                                                />
                                            )}
                                        />
                                        {errors.variations?.[activeVariation]?.content && (
                                            <p className="text-sm text-destructive">{errors.variations[activeVariation]?.content?.message}</p>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ) : (
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
                            <div className="space-y-2">
                                <label className="text-sm font-medium leading-none" htmlFor="content">
                                    HTML Content
                                </label>
                                <Controller
                                    name="content"
                                    control={control}
                                    render={({ field }) => (
                                        <RichTextEditor
                                            value={field.value || ''}
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
                    )}

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
                                <label className="flex items-center gap-2 text-sm font-medium">
                                    <input
                                        type="radio"
                                        value="ab_test"
                                        {...register('schedule_type')}
                                        className="h-4 w-4 text-primary focus:ring-primary"
                                    />
                                    A/B Test Automation
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
