'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { toast } from 'sonner';
import { Loader2, ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { api } from '@/lib/api';

const segmentSchema = z.object({
    name: z.string().min(1, 'Name is required'),
    description: z.string().optional(),
    emails: z.string().optional(), // Comma separated emails
});

type SegmentFormValues = z.infer<typeof segmentSchema>;

export default function NewSegmentPage() {
    const router = useRouter();
    const [isLoading, setIsLoading] = useState(false);

    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<SegmentFormValues>({
        resolver: zodResolver(segmentSchema),
    });

    const onSubmit = async (data: SegmentFormValues) => {
        setIsLoading(true);
        try {
            const emailList = data.emails
                ? data.emails.split(',').map(e => e.trim()).filter(e => e.length > 0)
                : [];

            await api.post('/segments', {
                name: data.name,
                description: data.description,
                emails: emailList
            });

            toast.success('Segment created successfully');
            router.push('/segments');
        } catch (error: any) {
            console.error('Create segment error:', error);
            toast.error(error.response?.data?.message || 'Failed to create segment');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="max-w-2xl mx-auto space-y-8">
            <div className="flex items-center gap-4">
                <Link
                    href="/segments"
                    className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground"
                >
                    <ArrowLeft className="h-4 w-4" />
                </Link>
                <div>
                    <h1 className="text-3xl font-display font-bold tracking-tight">
                        Create Segment
                    </h1>
                    <p className="text-muted-foreground">
                        Create a new list of contacts for your campaigns
                    </p>
                </div>
            </div>

            <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                    <div className="space-y-2">
                        <label className="text-sm font-medium leading-none" htmlFor="name">
                            Segment Name
                        </label>
                        <input
                            {...register('name')}
                            id="name"
                            placeholder="e.g. Newsletter Subscribers"
                            className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                        />
                        {errors.name && (
                            <p className="text-sm text-destructive">{errors.name.message}</p>
                        )}
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-medium leading-none" htmlFor="description">
                            Description (Optional)
                        </label>
                        <textarea
                            {...register('description')}
                            id="description"
                            placeholder="What is this segment for?"
                            className="flex min-h-[80px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                        />
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-medium leading-none" htmlFor="emails">
                            Initial Emails (Optional)
                        </label>
                        <p className="text-xs text-muted-foreground">
                            Enter email addresses separated by commas
                        </p>
                        <textarea
                            {...register('emails')}
                            id="emails"
                            placeholder="john@example.com, jane@example.com"
                            className="flex min-h-[120px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 font-mono"
                        />
                    </div>

                    <div className="flex justify-end gap-4">
                        <Link
                            href="/segments"
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
                                'Create Segment'
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
