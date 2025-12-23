'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { toast } from 'sonner';
import { Loader2, ArrowLeft, Users, Plus } from 'lucide-react';
import Link from 'next/link';
import { api } from '@/lib/api';

const segmentSchema = z.object({
    name: z.string().min(1, 'Name is required'),
    description: z.string().optional(),
    emails: z.string().min(1, 'At least one email is required'), // Comma separated emails
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
        <div className="max-w-3xl mx-auto space-y-12 pb-24">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 px-2">
                <div className="flex items-start gap-6">
                    <Link
                        href="/segments"
                        className="flex h-12 w-12 items-center justify-center rounded-2xl bg-card border border-border shadow-sm hover:bg-primary/10 hover:text-primary transition-all group"
                    >
                        <ArrowLeft className="h-6 w-6 transition-transform group-hover:-translate-x-1" />
                    </Link>
                    <div className="space-y-1">
                        <div className="flex items-center gap-2 mb-1">
                            <div className="w-1 h-4 bg-primary rounded-full" />
                            <h2 className="text-[10px] font-black uppercase tracking-[0.2em] text-primary/80">Segments</h2>
                        </div>
                        <h1 className="text-4xl font-display font-black tracking-tight text-foreground">
                            Create New Segment
                        </h1>
                        <p className="text-muted-foreground font-medium">
                            Create groups of contacts to send emails to
                        </p>
                    </div>
                </div>
            </div>

            <div className="group rounded-[2.5rem] bg-card border border-border p-10 shadow-xl transition-all hover:border-primary/20 relative overflow-hidden">
                <div className="absolute top-0 right-0 p-8 opacity-5 pointer-events-none transition-transform group-hover:scale-110">
                    <Users className="h-32 w-32" />
                </div>

                <form onSubmit={handleSubmit(onSubmit)} className="relative space-y-10">
                    <div className="space-y-8">
                        <div className="grid gap-8">
                            <div className="space-y-3">
                                <label className="text-xs font-black text-muted-foreground uppercase tracking-widest ml-1" htmlFor="name">
                                    Segment Name
                                </label>
                                <input
                                    {...register('name')}
                                    id="name"
                                    placeholder="e.g. Newsletter Subscribers"
                                    className="flex h-14 w-full rounded-2xl border border-border bg-background/50 px-5 py-2 text-lg font-bold shadow-sm transition-all focus:ring-4 focus:ring-primary/10 focus:border-primary outline-none"
                                />
                                {errors.name && (
                                    <p className="text-xs font-bold text-destructive mt-1 flex items-center gap-1">
                                        <div className="w-1 h-3 bg-destructive rounded-full" /> {errors.name.message}
                                    </p>
                                )}
                            </div>

                            <div className="space-y-3">
                                <label className="text-xs font-black text-muted-foreground uppercase tracking-widest ml-1" htmlFor="description">
                                    Description (Optional)
                                </label>
                                <textarea
                                    {...register('description')}
                                    id="description"
                                    placeholder="Describe what this group is for..."
                                    className="flex min-h-[100px] w-full rounded-2xl border border-border bg-background/50 px-5 py-4 text-base font-medium shadow-sm transition-all focus:ring-4 focus:ring-primary/10 focus:border-primary outline-none resize-none"
                                />
                            </div>

                            <div className="space-y-4">
                                <div>
                                    <label className="text-xs font-black text-muted-foreground uppercase tracking-widest ml-1" htmlFor="emails">
                                        Email Addresses
                                    </label>
                                    <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider opacity-60 ml-1 mt-1">
                                        Enter email addresses separated by commas
                                    </p>
                                </div>
                                <textarea
                                    {...register('emails')}
                                    id="emails"
                                    placeholder="user1@example.com, user2@example.com..."
                                    className="flex min-h-[160px] w-full rounded-2xl border border-border bg-background/50 px-5 py-4 text-base font-medium shadow-sm transition-all focus:ring-4 focus:ring-primary/10 focus:border-primary outline-none font-mono resize-none"
                                />
                                {errors.emails && (
                                    <p className="text-xs font-bold text-destructive mt-1 flex items-center gap-1">
                                        <div className="w-1 h-3 bg-destructive rounded-full" /> {errors.emails.message}
                                    </p>
                                )}
                            </div>
                        </div>
                    </div>

                    <div className="flex flex-col sm:flex-row items-center justify-end gap-6 pt-10 border-t border-border/50">
                        <Link
                            href="/segments"
                            className="text-sm font-bold uppercase tracking-widest text-muted-foreground hover:text-foreground transition-colors px-6"
                        >
                            Cancel
                        </Link>
                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full sm:w-auto inline-flex items-center justify-center rounded-2xl text-base font-black uppercase tracking-[0.1em] transition-all focus:ring-4 focus:ring-primary/20 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow-2xl shadow-primary/30 hover:shadow-primary/40 hover:-translate-y-1 active:translate-y-0 h-16 px-12 group"
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 className="mr-3 h-5 w-5 animate-spin" />
                                    Creating...
                                </>
                            ) : (
                                <>
                                    Create Segment
                                    <Plus className="ml-3 h-5 w-5 transition-transform group-hover:rotate-90" />
                                </>
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
