'use client';

import { useState } from 'react';
import { Sparkles, X, Loader2, Plus, Trash2 } from 'lucide-react';
import { generateEmail } from '@/services/generate_email';

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
            onGenerate(data.subject, data.content, data.variations);
            setIsOpen(false);
            // Reset pending link fields
            setNewLinkUrl('');
            setNewLinkText('');
        } catch (error) {
            console.error('Generation error:', error);
            // You might want to add a toast error here
        } finally {
            setIsGenerating(false);
        }
    };

    if (!isOpen) {
        return (
            <button
                type="button"
                onClick={() => setIsOpen(true)}
                className="flex items-center gap-2 text-sm font-medium text-purple-600 hover:text-purple-700 transition-colors"
            >
                <Sparkles className="h-4 w-4" />
                Generate with AI
            </button>
        );
    }

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 overflow-y-auto">
            <div className="bg-card w-full max-w-2xl rounded-xl border border-border shadow-lg animate-in fade-in zoom-in duration-200 my-8">
                <div className="flex items-center justify-between border-b border-border p-4">
                    <div className="flex items-center gap-2">
                        <div className="h-8 w-8 rounded-lg bg-purple-100 flex items-center justify-center text-purple-600">
                            <Sparkles className="h-4 w-4" />
                        </div>
                        <h3 className="font-semibold">Generate Campaign Content</h3>
                    </div>
                    <button
                        onClick={() => setIsOpen(false)}
                        className="text-muted-foreground hover:text-foreground transition-colors"
                    >
                        <X className="h-4 w-4" />
                    </button>
                </div>

                <div className="p-6 space-y-6 max-h-[70vh] overflow-y-auto">
                    {/* Goal Section */}
                    <div className="space-y-3">
                        <label className="text-sm font-medium">Campaign Goal</label>
                        <div className="grid grid-cols-2 gap-2">
                            {GOAL_OPTIONS.map(option => (
                                <label key={option} className="flex items-center gap-2 p-2 border border-border rounded-md hover:bg-muted/50 cursor-pointer">
                                    <input
                                        type="radio"
                                        name="goal"
                                        value={option}
                                        checked={selectedGoal === option}
                                        onChange={(e) => setSelectedGoal(e.target.value)}
                                        className="text-purple-600 focus:ring-purple-600"
                                    />
                                    <span className="text-sm">{option}</span>
                                </label>
                            ))}
                            <label className="flex items-center gap-2 p-2 border border-border rounded-md hover:bg-muted/50 cursor-pointer">
                                <input
                                    type="radio"
                                    name="goal"
                                    value="Other"
                                    checked={selectedGoal === 'Other'}
                                    onChange={(e) => setSelectedGoal(e.target.value)}
                                    className="text-purple-600 focus:ring-purple-600"
                                />
                                <span className="text-sm">Other</span>
                            </label>
                        </div>
                        {selectedGoal === 'Other' && (
                            <input
                                value={customGoal}
                                onChange={(e) => setCustomGoal(e.target.value)}
                                placeholder="Enter your custom goal"
                                className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                            />
                        )}
                    </div>

                    {/* Audience Section */}
                    <div className="space-y-3">
                        <label className="text-sm font-medium">Target Audience</label>
                        <div className="grid grid-cols-2 gap-2">
                            {AUDIENCE_OPTIONS.map(option => (
                                <label key={option} className="flex items-center gap-2 p-2 border border-border rounded-md hover:bg-muted/50 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={selectedAudiences.includes(option)}
                                        onChange={() => toggleAudience(option)}
                                        className="rounded border-gray-300 text-purple-600 focus:ring-purple-600"
                                    />
                                    <span className="text-sm">{option}</span>
                                </label>
                            ))}
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-sm text-muted-foreground whitespace-nowrap">Other:</span>
                            <input
                                value={customAudience}
                                onChange={(e) => setCustomAudience(e.target.value)}
                                placeholder="Add custom audience"
                                className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                            />
                        </div>
                    </div>

                    {/* Key Points */}
                    <div className="space-y-2">
                        <label className="text-sm font-medium">Key Points (one per line)</label>
                        <textarea
                            value={keyPoints}
                            onChange={(e) => setKeyPoints(e.target.value)}
                            placeholder="- 50% off all items&#10;- Valid until Friday&#10;- Free shipping"
                            className="flex min-h-[80px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                        />
                    </div>

                    {/* Links Section */}
                    <div className="space-y-3">
                        <label className="text-sm font-medium">Include Links</label>
                        <div className="flex gap-2">
                            <input
                                value={newLinkText}
                                onChange={(e) => setNewLinkText(e.target.value)}
                                placeholder="Link Text (e.g. Visit Website)"
                                className="flex h-9 flex-1 rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                            />
                            <input
                                value={newLinkUrl}
                                onChange={(e) => setNewLinkUrl(e.target.value)}
                                placeholder="URL (e.g. https://example.com)"
                                className="flex h-9 flex-1 rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                            />
                            <button
                                type="button"
                                onClick={handleAddLink}
                                disabled={!newLinkText || !newLinkUrl}
                                className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground h-9 w-9"
                            >
                                <Plus className="h-4 w-4" />
                            </button>
                        </div>
                        {links.length > 0 && (
                            <div className="space-y-2">
                                {links.map((link, index) => (
                                    <div key={index} className="flex items-center justify-between p-2 rounded-md bg-muted/50 border border-border">
                                        <div className="flex flex-col text-sm">
                                            <span className="font-medium">{link.text}</span>
                                            <span className="text-xs text-muted-foreground">{link.url}</span>
                                        </div>
                                        <button
                                            onClick={() => handleRemoveLink(index)}
                                            className="text-muted-foreground hover:text-destructive transition-colors"
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Tone */}
                    <div className="space-y-2">
                        <label className="text-sm font-medium">
                            {mode === 'ab_test' ? 'Select 3 Tones' : 'Tone'}
                        </label>

                        {mode === 'single' ? (
                            <select
                                value={tone}
                                onChange={(e) => setTone(e.target.value)}
                                className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                            >
                                <option value="Professional">Professional</option>
                                <option value="Friendly">Friendly</option>
                                <option value="Urgent">Urgent</option>
                                <option value="Exciting">Exciting</option>
                            </select>
                        ) : (
                            <div className="grid grid-cols-2 gap-2">
                                {["Professional", "Friendly", "Urgent", "Exciting"].map(t => (
                                    <label key={t} className={`flex items-center gap-2 p-2 border rounded-md cursor-pointer ${selectedTones.includes(t) ? 'bg-purple-50 border-purple-200' : 'border-border hover:bg-muted/50'}`}>
                                        <input
                                            type="checkbox"
                                            checked={selectedTones.includes(t)}
                                            onChange={() => toggleTone(t)}
                                            className="rounded border-gray-300 text-purple-600 focus:ring-purple-600"
                                        />
                                        <span className="text-sm">{t}</span>
                                    </label>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                <div className="flex justify-end gap-3 p-4 border-t border-border bg-muted/20 rounded-b-xl">
                    <button
                        onClick={() => setIsOpen(false)}
                        className="px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleGenerate}
                        disabled={(!selectedGoal && !customGoal) || (selectedAudiences.length === 0 && !customAudience) || isGenerating || (mode === 'ab_test' && selectedTones.length !== 3)}
                        className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isGenerating ? (
                            <>
                                <Loader2 className="h-4 w-4 animate-spin" />
                                Generating...
                            </>
                        ) : (
                            <>
                                <Sparkles className="h-4 w-4" />
                                Generate Content
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}
