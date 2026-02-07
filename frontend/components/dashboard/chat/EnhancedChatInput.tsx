import React, { useState, useEffect, useRef } from 'react'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { Send, Paperclip, Mic, MicOff } from 'lucide-react'
import { cn } from '@/lib/utils'

interface SlashCommand {
    command: string
    description: string
    action: () => void
}

interface EnhancedChatInputProps {
    placeholder?: string
    value: string
    onChange: (value: string) => void
    onSend: () => void
    onFileUpload?: (file: File) => void
    onVoiceToggle?: () => void
    isVoiceActive?: boolean
    slashCommands?: SlashCommand[]
    disabled?: boolean
    className?: string
}

export function EnhancedChatInput({
    placeholder = 'Type your message...',
    value,
    onChange,
    onSend,
    onFileUpload,
    onVoiceToggle,
    isVoiceActive = false,
    slashCommands = [],
    disabled = false,
    className
}: EnhancedChatInputProps) {
    const [showAutocomplete, setShowAutocomplete] = useState(false)
    const [filteredCommands, setFilteredCommands] = useState<SlashCommand[]>([])
    const fileInputRef = useRef<HTMLInputElement>(null)
    const textareaRef = useRef<HTMLTextAreaElement>(null)

    // Handle slash command autocomplete
    useEffect(() => {
        const lastWord = value.split(' ').pop() || ''

        if (lastWord.startsWith('/') && lastWord.length > 1) {
            const searchTerm = lastWord.slice(1).toLowerCase()
            const filtered = slashCommands.filter(cmd =>
                cmd.command.toLowerCase().includes(searchTerm)
            )
            setFilteredCommands(filtered)
            setShowAutocomplete(filtered.length > 0)
        } else {
            setShowAutocomplete(false)
        }
    }, [value, slashCommands])

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            if (value.trim() && !disabled) {
                onSend()
            }
        }

        if (e.key === 'Escape') {
            setShowAutocomplete(false)
        }
    }

    const selectCommand = (command: SlashCommand) => {
        const words = value.split(' ')
        words[words.length - 1] = command.command + ' '
        onChange(words.join(' '))
        setShowAutocomplete(false)
        textareaRef.current?.focus()
        command.action()
    }

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (file && onFileUpload) {
            onFileUpload(file)
        }
    }

    return (
        <div className={cn("sticky bottom-0 bg-white border-t p-4", className)}>
            {/* Quick Commands Helper */}
            {slashCommands.length > 0 && (
                <div className="mb-2 text-xs text-slate-500">
                    💡 Quick Commands: {slashCommands.slice(0, 4).map(cmd => cmd.command).join(' ')}
                </div>
            )}

            {/* Input Area */}
            <div className="relative">
                <Textarea
                    ref={textareaRef}
                    placeholder={placeholder}
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={disabled}
                    className="pr-32 min-h-[80px] resize-none"
                    rows={3}
                />

                {/* Slash Command Autocomplete */}
                {showAutocomplete && (
                    <div className="absolute bottom-full mb-2 left-0 right-0 bg-white border rounded-lg shadow-lg p-2 max-h-48 overflow-y-auto z-10">
                        {filteredCommands.map((cmd) => (
                            <button
                                key={cmd.command}
                                className="w-full text-left px-3 py-2 hover:bg-slate-50 rounded transition-colors"
                                onClick={() => selectCommand(cmd)}
                            >
                                <span className="font-mono font-bold text-green-600">{cmd.command}</span>
                                <span className="text-xs text-slate-500 ml-2">- {cmd.description}</span>
                            </button>
                        ))}
                    </div>
                )}
            </div>

            {/* Toolbar */}
            <div className="flex items-center justify-between mt-2">
                <div className="flex gap-2">
                    {/* File Upload */}
                    {onFileUpload && (
                        <>
                            <input
                                ref={fileInputRef}
                                type="file"
                                className="hidden"
                                onChange={handleFileSelect}
                                accept="image/*,.pdf,.doc,.docx,.txt"
                            />
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => fileInputRef.current?.click()}
                                disabled={disabled}
                                title="Attach file"
                            >
                                <Paperclip className="h-4 w-4" />
                            </Button>
                        </>
                    )}

                    {/* Voice Input */}
                    {onVoiceToggle && (
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={onVoiceToggle}
                            disabled={disabled}
                            className={cn(isVoiceActive && 'text-red-500')}
                            title={isVoiceActive ? 'Stop recording' : 'Start voice input'}
                        >
                            {isVoiceActive ? (
                                <MicOff className="h-4 w-4" />
                            ) : (
                                <Mic className="h-4 w-4" />
                            )}
                        </Button>
                    )}

                    {/* Emoji Picker Placeholder */}
                    <Button
                        variant="ghost"
                        size="sm"
                        disabled={disabled}
                        title="Add emoji"
                    >
                        😊
                    </Button>
                </div>

                {/* Send Button */}
                <Button
                    size="sm"
                    onClick={onSend}
                    disabled={!value.trim() || disabled}
                    className="bg-green-600 hover:bg-green-700"
                >
                    <Send className="h-4 w-4" />
                </Button>
            </div>
        </div>
    )
}
