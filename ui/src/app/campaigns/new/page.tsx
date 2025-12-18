'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { toast } from 'sonner';
import { Loader2, ArrowLeft, Calendar as CalendarIcon, Users, Clock, Send, Activity, ChevronDown } from 'lucide-react';
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
        <div className="max-w-4xl mx-auto space-y-12 pb-24">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 px-2">
                <div className="flex items-start gap-6">
                    <Link
                        href="/campaigns"
                        className="flex h-12 w-12 items-center justify-center rounded-2xl bg-card border border-border shadow-sm hover:bg-primary/10 hover:text-primary transition-all group"
                    >
                        <ArrowLeft className="h-6 w-6 transition-transform group-hover:-translate-x-1" />
                    </Link>
                    <div className="space-y-1">
                        <div className="flex items-center gap-2 mb-1">
                            <div className="w-1 h-4 bg-primary rounded-full" />
                            <h2 className="text-[10px] font-black uppercase tracking-[0.2em] text-primary/80">Campaign Architect</h2>
                        </div>
                        <h1 className="text-4xl font-display font-black tracking-tight text-foreground">
                            Create New Campaign
                        </h1>
                        <p className="text-muted-foreground font-medium">
                            Synthesize your message and target the right audience
                        </p>
                    </div>
                </div>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-10">
                {/* Section 1: Identity & Audience */}
                <div className="group rounded-[2.5rem] bg-card border border-border p-10 shadow-xl transition-all hover:border-primary/20 relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-8 opacity-5 pointer-events-none">
                        <Users className="h-24 w-24" />
                    </div>

                    <div className="relative space-y-8">
                        <div className="flex items-center gap-4 border-b border-border/50 pb-6">
                            <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
                                <Users className="h-5 w-5" />
                            </div>
                            <div>
                                <h3 className="text-xl font-bold">Identity & Audience</h3>
                                <p className="text-sm text-muted-foreground">Define who will receive this transmission</p>
                            </div>
                        </div>

                        <div className="grid gap-8 md:grid-cols-2">
                            <div className="space-y-3">
                                <label className="text-xs font-black text-muted-foreground uppercase tracking-widest ml-1" htmlFor="name">
                                    Internal Campaign Name
                                </label>
                                <input
                                    {...register('name')}
                                    id="name"
                                    placeholder="e.g. Q4 Growth Acceleration"
                                    className="flex h-14 w-full rounded-2xl border border-border bg-background/50 px-5 py-2 text-base font-medium shadow-sm transition-all focus:ring-4 focus:ring-primary/10 focus:border-primary outline-none"
                                />
                                {errors.name && (
                                    <p className="text-xs font-bold text-destructive mt-1 flex items-center gap-1">
                                        <div className="w-1 h-3 bg-destructive rounded-full" /> {errors.name.message}
                                    </p>
                                )}
                            </div>

                            <div className="space-y-3">
                                <label className="text-xs font-black text-muted-foreground uppercase tracking-widest ml-1" htmlFor="segment_id">
                                    Target Recipient Segment
                                </label>
                                <div className="relative group/select">
                                    <select
                                        {...register('segment_id')}
                                        id="segment_id"
                                        className="flex h-14 w-full rounded-2xl border border-border bg-background/50 px-5 py-2 text-base font-medium shadow-sm transition-all focus:ring-4 focus:ring-primary/10 focus:border-primary outline-none appearance-none pr-10"
                                    >
                                        <option value="">Select a target group</option>
                                        {segments.map((segment) => (
                                            <option key={segment.id} value={segment.id}>
                                                {segment.name} — {segment.contact_count} contacts
                                            </option>
                                        ))}
                                    </select>
                                    <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground pointer-events-none group-focus-within/select:text-primary transition-colors" />
                                </div>
                                {errors.segment_id && (
                                    <p className="text-xs font-bold text-destructive mt-1 flex items-center gap-1">
                                        <div className="w-1 h-3 bg-destructive rounded-full" /> {errors.segment_id.message}
                                    </p>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Section 2: Creative & Content */}
                <div className="group rounded-[2.5rem] bg-card border border-border p-10 shadow-xl transition-all hover:border-primary/20 overflow-hidden">
                    <div className="space-y-8">
                        <div className="flex items-center justify-between border-b border-border/50 pb-6">
                            <div className="flex items-center gap-4">
                                <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
                                    <CalendarIcon className="h-5 w-5" />
                                </div>
                                <div>
                                    <h3 className="text-xl font-bold">Creative & Intelligence</h3>
                                    <p className="text-sm text-muted-foreground">Draft your message or use AI synthesis</p>
                                </div>
                            </div>
                            <AiGeneratorModal
                                mode={scheduleType === 'ab_test' ? 'ab_test' : 'single'}
                                onGenerate={(s, c, variations) => {
                                    if (scheduleType === 'ab_test') {
                                        if (variations && variations.length > 0) {
                                            const validVariations = variations.slice(0, 3);
                                            setValue('variations', validVariations, { shouldValidate: true });
                                            toast.success('AI synthesized 3 distinct variations!');
                                        }
                                    } else {
                                        setValue('subject', s, { shouldValidate: true });
                                        setValue('content', c, { shouldValidate: true });
                                        toast.success('AI content masterfully generated!');
                                    }
                                }}
                            />
                        </div>

                        {scheduleType === 'ab_test' ? (
                            <div className="space-y-10">
                                {/* A/B Test Config Slider */}
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-10 p-8 bg-primary/5 rounded-3xl border border-primary/10">
                                    <div className="space-y-4">
                                        <div className="flex justify-between items-center px-1">
                                            <label className="text-sm font-bold uppercase tracking-widest text-primary">Test Pool</label>
                                            <span className="text-lg font-black">{watch('test_percentage')}%</span>
                                        </div>
                                        <input
                                            type="range"
                                            min="5"
                                            max="90"
                                            step="5"
                                            {...register('test_percentage', { valueAsNumber: true })}
                                            className="w-full h-2 bg-primary/20 rounded-lg appearance-none cursor-pointer accent-primary"
                                        />
                                        <p className="text-xs text-muted-foreground font-medium">Portion of audience receiving variations before the winner is chosen.</p>
                                    </div>
                                    <div className="space-y-4">
                                        <label className="text-sm font-bold uppercase tracking-widest text-primary block px-1">Decision Horizon</label>
                                        <div className="relative">
                                            <input
                                                type="number"
                                                min="1"
                                                max="72"
                                                {...register('decision_duration', { valueAsNumber: true })}
                                                className="flex h-12 w-full rounded-xl border border-primary/20 bg-background/50 px-4 py-2 text-base font-bold shadow-sm focus:ring-4 focus:ring-primary/10 outline-none"
                                            />
                                            <span className="absolute right-4 top-1/2 -translate-y-1/2 text-xs font-black text-primary/40 uppercase">Hours</span>
                                        </div>
                                        <p className="text-xs text-muted-foreground font-medium">Statistical window for determining the highest engagement rate.</p>
                                    </div>
                                </div>

                                {/* Variation Tabs */}
                                <div className="space-y-6">
                                    <div className="flex p-1.5 bg-muted rounded-2xl w-fit mx-auto">
                                        {[0, 1, 2].map((i) => (
                                            <button
                                                key={i}
                                                type="button"
                                                onClick={() => setActiveVariation(i as 0 | 1 | 2)}
                                                className={`relative px-8 py-3 text-sm font-black rounded-xl transition-all ${activeVariation === i
                                                    ? 'bg-card text-primary shadow-lg'
                                                    : 'text-muted-foreground hover:text-foreground'
                                                    }`}
                                            >
                                                VARIANT {['A', 'B', 'C'][i]}
                                                {activeVariation === i && (
                                                    <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-primary" />
                                                )}
                                            </button>
                                        ))}
                                    </div>

                                    <div className="space-y-6 bg-background/30 rounded-[2rem] p-8 border border-border/50 animate-in fade-in slide-in-from-bottom-2 duration-300" key={activeVariation}>
                                        <div className="space-y-3">
                                            <label className="text-xs font-black text-muted-foreground uppercase tracking-widest ml-1">Variation {['A', 'B', 'C'][activeVariation]} Subject</label>
                                            <input
                                                {...register(`variations.${activeVariation}.subject`)}
                                                placeholder="Enter magnetic subject line..."
                                                className="flex h-14 w-full rounded-2xl border border-border bg-background px-5 py-2 text-lg font-bold shadow-sm transition-all focus:ring-4 focus:ring-primary/10 outline-none"
                                            />
                                            {errors.variations?.[activeVariation]?.subject && (
                                                <p className="text-xs font-bold text-destructive mt-1">{errors.variations[activeVariation]?.subject?.message}</p>
                                            )}
                                        </div>

                                        <div className="space-y-3">
                                            <label className="text-xs font-black text-muted-foreground uppercase tracking-widest ml-1">Variation {['A', 'B', 'C'][activeVariation]} Content</label>
                                            <Controller
                                                name={`variations.${activeVariation}.content`}
                                                control={control}
                                                render={({ field }) => (
                                                    <div className="rounded-3xl border border-border overflow-hidden bg-background">
                                                        <RichTextEditor
                                                            value={field.value || ''}
                                                            onChange={field.onChange}
                                                            placeholder="Compose the narrative for this variation..."
                                                        />
                                                    </div>
                                                )}
                                            />
                                            {errors.variations?.[activeVariation]?.content && (
                                                <p className="text-xs font-bold text-destructive mt-1">{errors.variations[activeVariation]?.content?.message}</p>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="space-y-8">
                                <div className="space-y-3">
                                    <label className="text-xs font-black text-muted-foreground uppercase tracking-widest ml-1" htmlFor="subject">
                                        Primary Subject Line
                                    </label>
                                    <input
                                        {...register('subject')}
                                        id="subject"
                                        placeholder="Target the recipient's attention..."
                                        className="flex h-14 w-full rounded-2xl border border-border bg-background px-5 py-2 text-lg font-bold shadow-sm transition-all focus:ring-4 focus:ring-primary/10 outline-none"
                                    />
                                    {errors.subject && (
                                        <p className="text-xs font-bold text-destructive mt-1">{errors.subject.message}</p>
                                    )}
                                </div>
                                <div className="space-y-3">
                                    <label className="text-xs font-black text-muted-foreground uppercase tracking-widest ml-1" htmlFor="content">
                                        Transmission Content (HTML)
                                    </label>
                                    <Controller
                                        name="content"
                                        control={control}
                                        render={({ field }) => (
                                            <div className="rounded-3xl border border-border overflow-hidden bg-background shadow-inner">
                                                <RichTextEditor
                                                    value={field.value || ''}
                                                    onChange={field.onChange}
                                                    placeholder="Construct your message logic and styling..."
                                                />
                                            </div>
                                        )}
                                    />
                                    {errors.content && (
                                        <p className="text-xs font-bold text-destructive mt-1">{errors.content.message}</p>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Section 3: Scheduling Logic */}
                <div className="group rounded-[2.5rem] bg-card border border-border p-10 shadow-xl transition-all hover:border-primary/20 overflow-hidden">
                    <div className="space-y-8">
                        <div className="flex items-center gap-4 border-b border-border/50 pb-6">
                            <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
                                <Clock className="h-5 w-5" />
                            </div>
                            <div>
                                <h3 className="text-xl font-bold">Execution Strategy</h3>
                                <p className="text-sm text-muted-foreground">Determine the temporal logic for dispatch</p>
                            </div>
                        </div>

                        <div className="grid gap-6 sm:grid-cols-3">
                            {[
                                { id: 'immediate', label: 'Real-time', desc: 'Instant dispatch', icon: Send },
                                { id: 'scheduled', label: 'Temporal', desc: 'Futuristic timing', icon: CalendarIcon },
                                { id: 'ab_test', label: 'Automated', desc: 'Neural optimization', icon: Activity },
                            ].map((type) => (
                                <label
                                    key={type.id}
                                    className={`relative flex flex-col items-center gap-4 p-6 rounded-3xl border-2 cursor-pointer transition-all ${scheduleType === type.id
                                        ? 'border-primary bg-primary/5 shadow-lg'
                                        : 'border-border bg-background hover:border-primary/30 hover:bg-muted/50'
                                        }`}
                                >
                                    <input
                                        type="radio"
                                        value={type.id}
                                        {...register('schedule_type')}
                                        className="sr-only"
                                    />
                                    <div className={`p-3 rounded-2xl ${scheduleType === type.id ? 'bg-primary text-white shadow-lg shadow-primary/20' : 'bg-muted text-muted-foreground'}`}>
                                        <type.icon className="h-6 w-6" />
                                    </div>
                                    <div className="text-center">
                                        <div className={`font-black text-sm uppercase tracking-widest ${scheduleType === type.id ? 'text-primary' : 'text-foreground'}`}>
                                            {type.label}
                                        </div>
                                        <div className="text-[10px] font-bold text-muted-foreground uppercase opacity-60">
                                            {type.desc}
                                        </div>
                                    </div>
                                    {scheduleType === type.id && (
                                        <div className="absolute top-3 right-3">
                                            <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                                        </div>
                                    )}
                                </label>
                            ))}
                        </div>

                        {scheduleType === 'scheduled' && (
                            <div className="space-y-4 p-8 bg-muted/30 rounded-[2rem] border border-border/50 animate-in zoom-in-95 duration-200">
                                <label className="text-xs font-black text-muted-foreground uppercase tracking-widest ml-1" htmlFor="scheduled_time">
                                    Temporal Dispatch Horizon
                                </label>
                                <div className="relative max-w-sm">
                                    <input
                                        type="datetime-local"
                                        {...register('scheduled_time')}
                                        id="scheduled_time"
                                        className="flex h-14 w-full rounded-2xl border border-border bg-background px-5 py-2 text-base font-bold shadow-sm transition-all focus:ring-4 focus:ring-primary/10 outline-none"
                                    />
                                </div>
                                {errors.scheduled_time && (
                                    <p className="text-xs font-bold text-destructive mt-1 flex items-center gap-1">
                                        <div className="w-1 h-3 bg-destructive rounded-full" /> {errors.scheduled_time.message}
                                    </p>
                                )}
                            </div>
                        )}
                    </div>
                </div>

                {/* Submit Section */}
                <div className="flex flex-col sm:flex-row items-center justify-end gap-6 pt-10 border-t border-border">
                    <Link
                        href="/campaigns"
                        className="text-sm font-bold uppercase tracking-widest text-muted-foreground hover:text-foreground transition-colors px-6"
                    >
                        Abort Draft
                    </Link>
                    <button
                        type="submit"
                        disabled={isLoading}
                        className="w-full sm:w-auto inline-flex items-center justify-center rounded-2xl text-base font-black uppercase tracking-[0.1em] transition-all focus:ring-4 focus:ring-primary/20 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow-2xl shadow-primary/30 hover:shadow-primary/40 hover:-translate-y-1 active:translate-y-0 h-16 px-12 group"
                    >
                        {isLoading ? (
                            <>
                                <Loader2 className="mr-3 h-5 w-5 animate-spin" />
                                Processing Neural Logic...
                            </>
                        ) : (
                            <>
                                {scheduleType === 'immediate' ? 'Initiate Transmission' : 'Finalize Strategy'}
                                <ArrowLeft className="ml-3 h-5 w-5 rotate-180 transition-transform group-hover:translate-x-1" />
                            </>
                        )}
                    </button>
                </div>
            </form>
        </div>
    );
}
