'use client';

import { useState } from 'react';
import { Sparkles, X, Loader2, Plus, Trash2 } from 'lucide-react';
import { generateEmail } from '@/services/generate_email';
import { toast } from 'sonner';

interface AiGeneratorModalProps {
    onGenerate: (subject: string, content: string, variations?: Array<{ subject: string, content: string, tone: string }>) => void;
    mode?: 'single' | 'ab_test';
}

const GOAL_OPTIONS = [
    "Product Launch",
    "Newsletter",
    "Sale/Promotion",
    "Event Invitation",
    "User Onboarding"
];

const AUDIENCE_OPTIONS = [
    "New Users",
    "Active Users",
    "Churned Users",
    "All Customers",
    "Beta Testers"
];

interface LinkItem {
    url: string;
    text: string;
}

export function AiGeneratorModal({ onGenerate, mode = 'single' }: AiGeneratorModalProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [isGenerating, setIsGenerating] = useState(false);

    // Goal State
    const [selectedGoal, setSelectedGoal] = useState<string>('');
    const [customGoal, setCustomGoal] = useState('');

    // Audience State
    const [selectedAudiences, setSelectedAudiences] = useState<string[]>([]);
    const [customAudience, setCustomAudience] = useState('');

    // Other State
    const [keyPoints, setKeyPoints] = useState('');
    const [tone, setTone] = useState('Professional');
    const [selectedTones, setSelectedTones] = useState<string[]>([]);

    // Links State
    const [links, setLinks] = useState<LinkItem[]>([]);
    const [newLinkUrl, setNewLinkUrl] = useState('');
    const [newLinkText, setNewLinkText] = useState('');

    const handleAddLink = () => {
        if (newLinkUrl && newLinkText) {
            const newLinks = [...links, { url: newLinkUrl, text: newLinkText }];
            console.log('➕ Adding link:', { url: newLinkUrl, text: newLinkText });
            console.log('📋 Updated links array:', newLinks);
            setLinks(newLinks);
            setNewLinkUrl('');
            setNewLinkText('');
        }
    };

    const handleRemoveLink = (index: number) => {
        setLinks(links.filter((_, i) => i !== index));
    };

    const toggleAudience = (audience: string) => {
        if (selectedAudiences.includes(audience)) {
            setSelectedAudiences(selectedAudiences.filter(a => a !== audience));
        } else {
            setSelectedAudiences([...selectedAudiences, audience]);
        }
    };

    const toggleTone = (t: string) => {
        if (selectedTones.includes(t)) {
            setSelectedTones(selectedTones.filter(x => x !== t));
        } else {
            if (selectedTones.length < 3) {
                setSelectedTones([...selectedTones, t]);
            }
        }
    };

    const handleGenerate = async () => {
        const finalGoal = selectedGoal === 'Other' ? customGoal : selectedGoal;
        const finalAudiences = [...selectedAudiences];
        if (customAudience) finalAudiences.push(customAudience);

        if (!finalGoal || finalAudiences.length === 0) return;

        // Auto-add pending link if user forgot to click add
        let finalLinks = [...links];
        if (newLinkUrl && newLinkText) {
            console.log('⚠️ User forgot to click add link, auto-adding:', { url: newLinkUrl, text: newLinkText });
            finalLinks.push({ url: newLinkUrl, text: newLinkText });
        }

        console.log('🔗 Links in modal state before generation:', finalLinks);

        setIsGenerating(true);

        try {
            const data = await generateEmail({
                tone: mode === 'single' ? tone : undefined,
                tones: mode === 'ab_test' ? selectedTones : undefined,
                finalGoal,
                audiences: finalAudiences,
                keyPoints,
                links: finalLinks
            });
            console.log('🤖 AI Response:', data);
            onGenerate(data.subject, data.content, data.variations);
            setIsOpen(false);
            // Reset pending link fields
            setNewLinkUrl('');
            setNewLinkText('');
        } catch (error: any) {
            console.error('Generation error:', error);
            toast.error(error.response?.data?.message || 'Failed to generate content. Please try again.');
        } finally {
            setIsGenerating(false);
        }
    };

    if (!isOpen) {
        return (
            <button
                type="button"
                onClick={() => setIsOpen(true)}
                className="group relative inline-flex items-center gap-2.5 px-6 py-3 rounded-2xl bg-primary/10 text-primary hover:bg-primary transition-all duration-300 hover:text-primary-foreground hover:-translate-y-0.5 active:translate-y-0"
            >
                <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full scale-0 group-hover:scale-100 transition-transform duration-500 opacity-0 group-hover:opacity-40" />
                <Sparkles className="h-4 w-4 relative" />
                <span className="text-xs font-black uppercase tracking-[0.2em] relative">Synthesize via AI</span>
            </button>
        );
    }

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-background/60 backdrop-blur-xl p-4 overflow-y-auto">
            <div className="bg-card w-full max-w-2xl rounded-[2.5rem] border border-border shadow-2xl animate-in fade-in zoom-in slide-in-from-bottom-8 duration-500 my-8 overflow-hidden">
                <div className="relative border-b border-border p-8 flex items-center justify-between bg-gradient-to-b from-primary/[0.03] to-transparent">
                    <div className="flex items-center gap-4">
                        <div className="h-12 w-12 rounded-2xl bg-primary/10 text-primary flex items-center justify-center shadow-inner">
                            <Sparkles className="h-6 w-6" />
                        </div>
                        <div>
                            <h3 className="text-2xl font-black tracking-tight">Intelligence Module</h3>
                            <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest opacity-60">AI Content Extraction & Synthesis</p>
                        </div>
                    </div>
                    <button
                        onClick={() => setIsOpen(false)}
                        className="h-10 w-10 rounded-xl flex items-center justify-center text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-all group"
                    >
                        <X className="h-5 w-5 transition-transform group-hover:rotate-90" />
                    </button>
                </div>

                <div className="p-10 space-y-10 max-h-[65vh] overflow-y-auto custom-scrollbar">
                    {/* Goal Section */}
                    <div className="space-y-6">
                        <div className="flex items-center gap-3">
                            <div className="w-1 h-4 bg-primary rounded-full transition-all group-hover:h-6" />
                            <label className="text-xs font-black text-muted-foreground uppercase tracking-[0.2em]">Primary Objective</label>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                            {GOAL_OPTIONS.map(option => (
                                <label key={option} className={`flex items-center gap-3 p-4 border rounded-2xl cursor-pointer transition-all hover:border-primary/30 ${selectedGoal === option ? 'bg-primary/5 border-primary shadow-[0_0_20px_rgba(59,130,246,0.1)]' : 'border-border hover:bg-muted/50'}`}>
                                    <input
                                        type="radio"
                                        name="goal"
                                        value={option}
                                        checked={selectedGoal === option}
                                        onChange={(e) => setSelectedGoal(e.target.value)}
                                        className="h-4 w-4 border-2 border-primary/20 text-primary focus:ring-primary/20"
                                    />
                                    <span className={`text-sm font-bold ${selectedGoal === option ? 'text-primary' : 'text-muted-foreground'}`}>{option}</span>
                                </label>
                            ))}
                            <label className={`flex items-center gap-3 p-4 border rounded-2xl cursor-pointer transition-all hover:border-primary/30 ${selectedGoal === 'Other' ? 'bg-primary/5 border-primary shadow-[0_0_20px_rgba(59,130,246,0.1)]' : 'border-border hover:bg-muted/50'}`}>
                                <input
                                    type="radio"
                                    name="goal"
                                    value="Other"
                                    checked={selectedGoal === 'Other'}
                                    onChange={(e) => setSelectedGoal(e.target.value)}
                                    className="h-4 w-4 border-2 border-primary/20 text-primary focus:ring-primary/20"
                                />
                                <span className={`text-sm font-bold ${selectedGoal === 'Other' ? 'text-primary' : 'text-muted-foreground'}`}>Custom...</span>
                            </label>
                        </div>
                        {selectedGoal === 'Other' && (
                            <input
                                value={customGoal}
                                onChange={(e) => setCustomGoal(e.target.value)}
                                placeholder="Specify objectives..."
                                className="h-14 w-full rounded-2xl border border-border bg-background/50 px-5 py-2 text-base font-bold shadow-sm transition-all focus:ring-4 focus:ring-primary/10 focus:border-primary outline-none"
                            />
                        )}
                    </div>

                    {/* Audience Section */}
                    <div className="space-y-6">
                        <div className="flex items-center gap-3">
                            <div className="w-1 h-4 bg-primary rounded-full transition-all group-hover:h-6" />
                            <label className="text-xs font-black text-muted-foreground uppercase tracking-[0.2em]">Target Nodes (Audience)</label>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                            {AUDIENCE_OPTIONS.map(option => (
                                <label key={option} className={`flex items-center gap-3 p-4 border rounded-2xl cursor-pointer transition-all hover:border-primary/30 ${selectedAudiences.includes(option) ? 'bg-primary/5 border-primary shadow-[0_0_20px_rgba(59,130,246,0.1)]' : 'border-border hover:bg-muted/50'}`}>
                                    <input
                                        type="checkbox"
                                        checked={selectedAudiences.includes(option)}
                                        onChange={() => toggleAudience(option)}
                                        className="h-4 w-4 rounded border-2 border-primary/20 text-primary focus:ring-primary/20"
                                    />
                                    <span className={`text-sm font-bold ${selectedAudiences.includes(option) ? 'text-primary' : 'text-muted-foreground'}`}>{option}</span>
                                </label>
                            ))}
                        </div>
                        <div className="flex items-center gap-4">
                            <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground opacity-60">Supplemental:</span>
                            <input
                                value={customAudience}
                                onChange={(e) => setCustomAudience(e.target.value)}
                                placeholder="Additional criteria..."
                                className="h-12 flex-1 rounded-xl border border-border bg-background/20 px-5 py-2 text-sm font-bold shadow-sm transition-all focus:ring-4 focus:ring-primary/10 focus:border-primary outline-none"
                            />
                        </div>
                    </div>

                    {/* Key Points */}
                    <div className="space-y-6">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="w-1 h-4 bg-primary rounded-full transition-all group-hover:h-6" />
                                <label className="text-xs font-black text-muted-foreground uppercase tracking-[0.2em]">Core Payloads (Key Points)</label>
                            </div>
                        </div>
                        <textarea
                            value={keyPoints}
                            onChange={(e) => setKeyPoints(e.target.value)}
                            placeholder="• Bulleted core message points...&#10;• Essential campaign details...&#10;• Value proposition..."
                            className="flex min-h-[140px] w-full rounded-[1.5rem] border border-border bg-background/50 px-6 py-5 text-base font-medium shadow-sm transition-all focus:ring-4 focus:ring-primary/10 focus:border-primary outline-none resize-none leading-relaxed"
                        />
                    </div>

                    {/* Links Section */}
                    <div className="space-y-6">
                        <div className="flex items-center gap-3">
                            <div className="w-1 h-4 bg-primary rounded-full transition-all group-hover:h-6" />
                            <label className="text-xs font-black text-muted-foreground uppercase tracking-[0.2em]">Anchor Protocols (Links)</label>
                        </div>
                        <div className="flex flex-col sm:flex-row gap-4">
                            <input
                                value={newLinkText}
                                onChange={(e) => {
                                    const val = e.target.value;
                                    // If user pastes a URL into the text field, automatically move it to URL field
                                    if (/^https?:\/\/\S+$/.test(val) && !newLinkUrl) {
                                        setNewLinkUrl(val);
                                        // Try to extract a decent label from the domain
                                        try {
                                            const domain = new URL(val).hostname.replace('www.', '');
                                            setNewLinkText(domain.charAt(0).toUpperCase() + domain.slice(1));
                                        } catch (e) {
                                            setNewLinkText('');
                                        }
                                    } else {
                                        setNewLinkText(val);
                                    }
                                }}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' && newLinkText && newLinkUrl) {
                                        e.preventDefault();
                                        handleAddLink();
                                    }
                                }}
                                placeholder="Protocol Label (Text)"
                                className="h-14 flex-1 rounded-2xl border border-border bg-background/50 px-5 py-2 text-sm font-bold shadow-sm transition-all focus:ring-4 focus:ring-primary/10 focus:border-primary outline-none"
                            />
                            <div className="flex gap-2 flex-1">
                                <input
                                    value={newLinkUrl}
                                    onChange={(e) => setNewLinkUrl(e.target.value)}
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter' && newLinkText && newLinkUrl) {
                                            e.preventDefault();
                                            handleAddLink();
                                        }
                                    }}
                                    placeholder="Source URI (URL)"
                                    className="h-14 flex-1 rounded-2xl border border-border bg-background/50 px-5 py-2 text-sm font-bold shadow-sm transition-all focus:ring-4 focus:ring-primary/10 focus:border-primary outline-none"
                                />
                                <button
                                    type="button"
                                    onClick={handleAddLink}
                                    disabled={!newLinkText || !newLinkUrl}
                                    className="h-14 w-14 rounded-2xl inline-flex items-center justify-center transition-all bg-primary/10 text-primary hover:bg-primary hover:text-primary-foreground disabled:opacity-30 disabled:pointer-events-none shadow-sm"
                                >
                                    <Plus className="h-6 w-6" />
                                </button>
                            </div>
                        </div>
                        {links.length > 0 && (
                            <div className="grid gap-3 pt-2">
                                {links.map((link, index) => (
                                    <div key={index} className="group/link flex items-center justify-between p-5 rounded-2xl bg-muted/30 border border-border/50 hover:border-primary/20 transition-all hover:bg-muted/50">
                                        <div className="flex flex-col text-sm min-w-0 pr-4">
                                            <span className="font-black tracking-tight">{link.text}</span>
                                            <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest truncate opacity-60">{link.url}</span>
                                        </div>
                                        <button
                                            onClick={() => handleRemoveLink(index)}
                                            className="h-8 w-8 rounded-lg flex items-center justify-center text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-all"
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Tone */}
                    <div className="space-y-6">
                        <div className="flex items-center gap-3">
                            <div className="w-1 h-4 bg-primary rounded-full transition-all group-hover:h-6" />
                            <label className="text-xs font-black text-muted-foreground uppercase tracking-[0.2em]">
                                {mode === 'ab_test' ? 'Emotional Spectra (Select 3)' : 'Identity Resonance (Tone)'}
                            </label>
                        </div>

                        {mode === 'single' ? (
                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                                {["Professional", "Friendly", "Urgent", "Exciting"].map(t => (
                                    <button
                                        key={t}
                                        onClick={() => setTone(t)}
                                        className={`px-4 py-4 rounded-2xl text-xs font-black uppercase tracking-widest border transition-all ${tone === t ? 'bg-primary text-primary-foreground border-primary shadow-lg shadow-primary/20' : 'bg-background/40 border-border hover:border-primary/30 hover:bg-muted'}`}
                                    >
                                        {t}
                                    </button>
                                ))}
                            </div>
                        ) : (
                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                                {["Professional", "Friendly", "Urgent", "Exciting"].map(t => (
                                    <button
                                        key={t}
                                        onClick={() => toggleTone(t)}
                                        className={`px-4 py-4 rounded-2xl text-xs font-black uppercase tracking-widest border transition-all ${selectedTones.includes(t) ? 'bg-primary/10 text-primary border-primary font-black' : 'bg-background/40 border-border opacity-50 hover:opacity-100 hover:border-primary/20'}`}
                                    >
                                        {t}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                <div className="p-8 border-t border-border flex items-center justify-between bg-gradient-to-t from-primary/[0.03] to-transparent">
                    <button
                        onClick={() => setIsOpen(false)}
                        className="text-xs font-black uppercase tracking-[0.2em] text-muted-foreground hover:text-foreground transition-all"
                    >
                        Deactivate Interface
                    </button>
                    <button
                        onClick={handleGenerate}
                        disabled={(!selectedGoal && !customGoal) || (selectedAudiences.length === 0 && !customAudience) || isGenerating || (mode === 'ab_test' && selectedTones.length !== 3)}
                        className="relative group inline-flex items-center justify-center rounded-2xl text-sm font-black uppercase tracking-[0.2em] transition-all focus:ring-4 focus:ring-primary/20 disabled:pointer-events-none disabled:opacity-40 bg-primary text-primary-foreground shadow-2xl shadow-primary/30 hover:shadow-primary/40 hover:-translate-y-1 active:translate-y-0 h-16 px-12 overflow-hidden"
                    >
                        {isGenerating ? (
                            <>
                                <Loader2 className="mr-3 h-5 w-5 animate-spin" />
                                Extracting...
                            </>
                        ) : (
                            <>
                                <Sparkles className="mr-3 h-5 w-5 group-hover:rotate-12 transition-transform" />
                                Initiate Synthesis
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}
