"use client"

import { useState } from "react"
import { Check, Copy, Info, AlertTriangle, Lightbulb } from "lucide-react"
import { cn } from "@/lib/utils"

// --- CodeBlock Component ---
interface CodeBlockProps {
    code: string
    language?: string
    filename?: string
}

export function CodeBlock({ code, language, filename }: CodeBlockProps) {
    const [copied, setCopied] = useState(false)

    const copyToClipboard = () => {
        navigator.clipboard.writeText(code)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }

    return (
        <div className="my-6 rounded-xl overflow-hidden border border-gray-200 shadow-sm bg-slate-900 group">
            {(filename || language) && (
                <div className="flex items-center justify-between px-4 py-2 border-b border-white/5 bg-white/5 backdrop-blur-md">
                    <span className="text-[10px] font-mono text-gray-400 uppercase tracking-widest leading-none">
                        {filename || language}
                    </span>
                    <button
                        onClick={copyToClipboard}
                        className="text-gray-400 hover:text-white transition-colors"
                    >
                        {copied ? <Check size={14} className="text-green-500" /> : <Copy size={14} />}
                    </button>
                </div>
            )}
            <div className="relative">
                {!filename && !language && (
                    <button
                        onClick={copyToClipboard}
                        className="absolute top-2 right-2 p-1.5 rounded-md bg-white/5 text-gray-400 opacity-0 group-hover:opacity-100 hover:text-white transition-all shadow-lg"
                    >
                        {copied ? <Check size={14} className="text-green-500" /> : <Copy size={14} />}
                    </button>
                )}
                <pre className="p-4 text-sm font-mono text-gray-300 overflow-x-auto selection:bg-green-500/30">
                    <code>{code}</code>
                </pre>
            </div>
        </div>
    )
}

// --- Callout Component ---
interface CalloutProps {
    children: React.ReactNode
    type?: "info" | "warning" | "tip" | "error"
}

export function Callout({ children, type = "info" }: CalloutProps) {
    const styles = {
        info: {
            bg: "bg-blue-50/50 border-blue-100",
            text: "text-blue-900",
            icon: <Info className="text-blue-500" />,
            title: "Note"
        },
        warning: {
            bg: "bg-amber-50/50 border-amber-100",
            text: "text-amber-900",
            icon: <AlertTriangle className="text-amber-500" />,
            title: "Caution"
        },
        tip: {
            bg: "bg-green-50/50 border-green-100",
            text: "text-green-900",
            icon: <Lightbulb className="text-green-500" />,
            title: "Tip"
        },
        error: {
            bg: "bg-red-50/50 border-red-100",
            text: "text-red-900",
            icon: <AlertTriangle className="text-red-500" />,
            title: "Important"
        }
    }

    const { bg, text, icon, title } = styles[type]

    return (
        <div className={cn("my-6 p-4 rounded-xl border flex items-start space-x-3", bg)}>
            <div className="mt-0.5">{icon}</div>
            <div className="flex-1">
                <span className={cn("block text-xs font-bold uppercase tracking-widest mb-1", text)}>
                    {title}
                </span>
                <div className={cn("text-sm leading-relaxed", text)}>
                    {children}
                </div>
            </div>
        </div>
    )
}

// --- StepCard Component ---
interface StepItem {
    number: number
    title: string
    content: string | React.ReactNode
}

export function Steps({ items }: { items: StepItem[] }) {
    return (
        <div className="space-y-8 my-10">
            {items.map((step, idx) => (
                <div key={idx} className="flex group">
                    <div className="mr-6 flex flex-col items-center">
                        <div className="w-10 h-10 rounded-full bg-green-100 text-green-700 border-2 border-green-200 flex items-center justify-center font-bold shadow-sm transition-transform group-hover:scale-110">
                            {step.number}
                        </div>
                        {idx !== items.length - 1 && (
                            <div className="w-0.5 flex-1 bg-gradient-to-b from-green-200 to-transparent my-2" />
                        )}
                    </div>
                    <div className="pb-8">
                        <h4 className="text-lg font-bold text-gray-900 mb-2">{step.title}</h4>
                        <div className="text-gray-600 leading-relaxed text-sm">
                            {step.content}
                        </div>
                    </div>
                </div>
            ))}
        </div>
    )
}
