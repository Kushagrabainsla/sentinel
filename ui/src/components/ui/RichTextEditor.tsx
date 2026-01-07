'use client';

import React, { useCallback, useState } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Underline from '@tiptap/extension-underline';
import Link from '@tiptap/extension-link';
import { Bold, Italic, Underline as UnderlineIcon, List, ListOrdered, Heading1, Heading2, Link as LinkIcon, X, Check, ExternalLink, Trash2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface RichTextEditorProps {
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
}

export function RichTextEditor({ value, onChange, placeholder }: RichTextEditorProps) {
    const [isLinkInputVisible, setIsLinkInputVisible] = useState(false);
    const [linkUrl, setLinkUrl] = useState('');
    const [linkText, setLinkText] = useState('');

    const editor = useEditor({
        extensions: [
            StarterKit,
            Underline,
            Link.configure({
                openOnClick: false,
                autolink: true,
                HTMLAttributes: {
                    class: 'text-[#0000EE] underline decoration-[#0000EE] cursor-pointer',
                },
            }),
        ],
        content: value,
        editorProps: {
            attributes: {
                class: 'prose prose-sm dark:prose-invert max-w-none min-h-[200px] p-4 focus:outline-none',
            },
            handlePaste: (view, event) => {
                const text = event.clipboardData?.getData('text/plain');
                if (!text || !/^https?:\/\/\S+$/.test(text)) {
                    return false;
                }

                const { selection } = view.state;
                if (selection.empty) {
                    // If no selection, insert the URL as text and make it a link
                    editor?.chain().focus().insertContent(`<a href="${text}">${text}</a>`).run();
                    return true;
                }

                // Smoothly turn selection into a link when pasting a URL
                view.dispatch(view.state.tr.setMeta('addToHistory', true));
                editor?.chain().focus().extendMarkRange('link').setLink({ href: text }).run();
                return true;
            },
        },
        immediatelyRender: false,
        onUpdate: ({ editor }) => {
            onChange(editor.getHTML());
        },
    });

    // Sync editor content when value prop changes externally
    React.useEffect(() => {
        if (editor && value !== editor.getHTML()) {
            editor.commands.setContent(value);
        }
    }, [value, editor]);

    const setLink = useCallback(() => {
        if (!editor) return;

        const { from, to, empty } = editor.state.selection;
        const selectedText = empty ? '' : editor.state.doc.textBetween(from, to, ' ');
        const previousUrl = editor.getAttributes('link').href;

        if (isLinkInputVisible) {
            setIsLinkInputVisible(false);
            return;
        }

        setLinkText(selectedText);
        setLinkUrl(previousUrl || '');
        setIsLinkInputVisible(true);
    }, [editor, isLinkInputVisible]);

    const applyLink = useCallback(() => {
        if (!editor) return;

        if (linkUrl === '') {
            editor.chain().focus().extendMarkRange('link').unsetLink().run();
        } else {
            // Basic URL validation/prefixing
            let url = linkUrl;
            if (!/^https?:\/\/|^\/|^mailto:|^tel:/i.test(url)) {
                url = 'https://' + url;
            }

            const textToUse = linkText || url;
            const { selection } = editor.state;

            if (selection.empty || linkText !== editor.state.doc.textBetween(selection.from, selection.to, ' ')) {
                // If selection is empty OR text was modified in the link window, replace with new content
                // We use extendMarkRange('link') to ensure that if we are already inside a link, we replace the whole thing
                editor.chain().focus().extendMarkRange('link').insertContent(`<a href="${url}">${textToUse}</a>`).run();
            } else {
                // Just apply link to existing selection
                editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run();
            }
        }
        setIsLinkInputVisible(false);
        setLinkUrl('');
        setLinkText('');
    }, [editor, linkUrl, linkText]);

    const removeLink = useCallback(() => {
        if (!editor) return;
        editor.chain().focus().extendMarkRange('link').unsetLink().run();
    }, [editor]);

    if (!editor) {
        return null;
    }

    const ToolbarButton = ({
        onClick,
        isActive = false,
        children,
        title,
        className
    }: {
        onClick: () => void;
        isActive?: boolean;
        children: React.ReactNode;
        title?: string;
        className?: string;
    }) => (
        <button
            type="button"
            onClick={onClick}
            title={title}
            className={cn(
                "p-2 rounded-md hover:bg-muted transition-all duration-200",
                isActive ? "bg-primary/10 text-primary shadow-sm" : "text-muted-foreground",
                className
            )}
        >
            {children}
        </button>
    );

    return (
        <div className="rounded-xl border border-border bg-background shadow-sm flex flex-col min-h-[300px]">
            {/* Toolbar */}
            <div className="flex flex-wrap items-center gap-1 border-b border-border p-2 bg-muted/20 sticky top-0 z-10 rounded-t-xl">
                <ToolbarButton
                    onClick={() => editor.chain().focus().toggleBold().run()}
                    isActive={editor.isActive('bold')}
                    title="Bold (Cmd+B)"
                >
                    <Bold className="h-4 w-4" />
                </ToolbarButton>
                <ToolbarButton
                    onClick={() => editor.chain().focus().toggleItalic().run()}
                    isActive={editor.isActive('italic')}
                    title="Italic (Cmd+I)"
                >
                    <Italic className="h-4 w-4" />
                </ToolbarButton>
                <ToolbarButton
                    onClick={() => editor.chain().focus().toggleUnderline().run()}
                    isActive={editor.isActive('underline')}
                    title="Underline (Cmd+U)"
                >
                    <UnderlineIcon className="h-4 w-4" />
                </ToolbarButton>

                <div className="w-px h-6 bg-border mx-1" />

                <div className="relative flex items-center">
                    <ToolbarButton
                        onClick={setLink}
                        isActive={editor.isActive('link') || isLinkInputVisible}
                        title="Add Link"
                    >
                        <LinkIcon className="h-4 w-4" />
                    </ToolbarButton>

                    {isLinkInputVisible && (
                        <div className="absolute left-0 top-full mt-2 w-80 bg-background border border-border rounded-xl shadow-[0_10px_40px_rgba(0,0,0,0.2)] p-4 z-50 animate-in fade-in zoom-in-95 duration-200 ring-1 ring-black/5">
                            <div className="flex flex-col gap-4">
                                <div className="flex items-center justify-between">
                                    <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Link Configuration</span>
                                    <button onClick={() => setIsLinkInputVisible(false)} className="text-muted-foreground hover:text-foreground">
                                        <X className="h-3 w-3" />
                                    </button>
                                </div>

                                <div className="space-y-3">
                                    <div className="space-y-1.5">
                                        <label className="text-[9px] font-bold uppercase text-muted-foreground ml-1">Display Text</label>
                                        <input
                                            value={linkText}
                                            onChange={(e) => setLinkText(e.target.value)}
                                            placeholder="Text to display..."
                                            className="w-full bg-muted/50 border border-border rounded-lg px-3 py-2 text-xs font-medium outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all shadow-inner"
                                        />
                                    </div>

                                    <div className="space-y-1.5">
                                        <label className="text-[9px] font-bold uppercase text-muted-foreground ml-1">URL (Destination)</label>
                                        <div className="flex gap-2">
                                            <input
                                                autoFocus
                                                value={linkUrl}
                                                onChange={(e) => setLinkUrl(e.target.value)}
                                                onKeyDown={(e) => {
                                                    if (e.key === 'Enter') {
                                                        e.preventDefault();
                                                        applyLink();
                                                    }
                                                    if (e.key === 'Escape') {
                                                        setIsLinkInputVisible(false);
                                                    }
                                                }}
                                                placeholder="https://example.com"
                                                className="flex-1 bg-muted/50 border border-border rounded-lg px-3 py-2 text-xs font-medium outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all shadow-inner"
                                            />
                                            <button
                                                onClick={applyLink}
                                                className="bg-primary text-primary-foreground px-3 rounded-lg hover:opacity-90 transition-opacity flex items-center justify-center"
                                            >
                                                <Check className="h-4 w-4" />
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                <div className="w-px h-6 bg-border/50 mx-1" />

                <ToolbarButton
                    onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
                    isActive={editor.isActive('heading', { level: 1 })}
                    title="Heading 1"
                >
                    <Heading1 className="h-4 w-4" />
                </ToolbarButton>
                <ToolbarButton
                    onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
                    isActive={editor.isActive('heading', { level: 2 })}
                    title="Heading 2"
                >
                    <Heading2 className="h-4 w-4" />
                </ToolbarButton>

                <div className="w-px h-6 bg-border/50 mx-1" />

                <ToolbarButton
                    onClick={() => editor.chain().focus().toggleBulletList().run()}
                    isActive={editor.isActive('bulletList')}
                    title="Bullet List"
                >
                    <List className="h-4 w-4" />
                </ToolbarButton>
                <ToolbarButton
                    onClick={() => editor.chain().focus().toggleOrderedList().run()}
                    isActive={editor.isActive('orderedList')}
                    title="Ordered List"
                >
                    <ListOrdered className="h-4 w-4" />
                </ToolbarButton>
            </div>

            <EditorContent editor={editor} className="flex-1" />
        </div>
    );
}
