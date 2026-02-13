"use client"

import { useState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { Switch } from "@/components/ui/switch"
import {
    BarChart3,
    Send,
    Mic,
    Paperclip,
    Bot,
    User,
    Zap,
    Activity,
    Shield,
    Cpu,
    Radio,
    Terminal,
    FileText,
    Clock,
    ChevronRight,
    ChevronLeft,
    MoreVertical,
    Search,
    Lock,
    Users,
    TrendingUp,
    Globe,
    Headphones,
    DollarSign,
    Megaphone,
    Lightbulb,
    Edit3,
    History,
    MessageSquare,
    Target,
    Layout,
    Scissors,
    Database
} from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { apiClient } from "@/lib/api-client"
import { useAuthStore } from "@/lib/stores/auth-store"
import { useToast } from "@/hooks/use-toast"
import { cn } from "@/lib/utils"
import { websocketService } from "@/lib/websocket-service"
import { useRouter } from "next/navigation"

// --- Interfaces ---

interface ChatMessage {
    id: number
    team_id: number
    user_id: number
    user_name: string
    agent_key?: string | null
    message_type: string
    content: string
    audio_url?: string | null
    file_url?: string | null
    file_name?: string | null
    reply_to_message_id?: number | null
    created_at: string
    avatar_url?: string
    thinking_steps?: string[]
}

interface Agent {
    key: string
    name: string
    title: string
    description: string
    icon: any
    color: string
    status: "idle" | "working" | "offline"
    specialty: string
}

// Updated Agent Data to match Overview Tab
const AVAILABLE_AGENTS: Agent[] = [
    { key: "aria", name: "Aria", title: "Social Media", description: "Social Media Management", icon: Globe, color: "text-orange-500", status: "idle", specialty: "Social Media" },
    { key: "clara", name: "Clara", title: "Customer Support", description: "Customer Support & Success", icon: Headphones, color: "text-purple-500", status: "idle", specialty: "Support" },
    { key: "eric", name: "Eric", title: "Sales", description: "Sales & Lead Generation", icon: DollarSign, color: "text-amber-500", status: "idle", specialty: "Sales" },
    { key: "jackie", name: "Jackie", title: "Marketing", description: "Marketing & Growth", icon: Megaphone, color: "text-pink-500", status: "idle", specialty: "Marketing" },
    { key: "shakes", name: "Shakes", title: "Content Creation", description: "Content Creation & Design", icon: FileText, color: "text-green-500", status: "idle", specialty: "Creative" },
    { key: "joe", name: "Joe", title: "Research", description: "Research & Analysis", icon: Search, color: "text-sky-400", status: "idle", specialty: "Research" },
    { key: "purity", name: "Purity", title: "Business Creation", description: "Business Development & Creation", icon: Lightbulb, color: "text-gray-500", status: "idle", specialty: "Strategy" },
]

// --- Components ---

const TacticalHeader = ({ connectionStatus, onNewChat, onHistory }: { connectionStatus: boolean, onNewChat: () => void, onHistory: () => void }) => (
    <div className="flex items-center justify-between px-6 py-3 border-b border-slate-200 bg-white/95 backdrop-blur-sm sticky top-0 z-50">
        <div className="flex items-center space-x-3">
            <div className="h-8 w-8 bg-slate-100 rounded-lg border border-slate-200 flex items-center justify-center">
                <Radio className={`h-4 w-4 ${connectionStatus ? "text-emerald-600 animate-pulse" : "text-slate-400"}`} />
            </div>
            <div>
                <h1 className="text-sm font-black text-slate-900 uppercase tracking-widest leading-none">Strategy Room</h1>
                <div className="flex items-center gap-3 mt-1">
                    <p className="text-[10px] font-mono text-emerald-600 font-medium flex items-center gap-2">
                        <span className={`inline-block w-2 h-2 rounded-full ${connectionStatus ? "bg-emerald-500 animate-ping" : "bg-red-500"}`} />
                        {connectionStatus ? "SECURE_CHANNEL // ACTIVE" : "CONNECTION_OFFLINE"}
                    </p>
                    <span className="text-[9px] font-mono text-slate-300">LAT: 12ms // ENC: AES-256</span>
                </div>
            </div>
        </div>
        <div className="flex items-center space-x-2">
            <Button size="icon" variant="ghost" className="h-8 w-8 text-slate-400 hover:text-emerald-600 hover:bg-emerald-50" onClick={onNewChat}>
                <Edit3 className="h-4 w-4" />
            </Button>
            <Button size="icon" variant="ghost" className="h-8 w-8 text-slate-400 hover:text-emerald-600 hover:bg-emerald-50" onClick={onHistory}>
                <History className="h-4 w-4" />
            </Button>
            <Separator orientation="vertical" className="h-4 mx-1" />
            <Badge variant="outline" className="font-mono text-[10px] text-emerald-600 border-emerald-200/50 bg-emerald-50/50">
                LOCKED_SESSION
            </Badge>
        </div>
    </div>
)

const RosterItem = ({ agent, onClick }: { agent: Agent; onClick: () => void }) => (
    <button
        onClick={onClick}
        className="w-full flex items-center space-x-3 p-2 rounded-lg hover:bg-slate-50 transition-colors group text-left"
    >
        <div className="relative">
            <div className={cn(
                "h-10 w-10 flex items-center justify-center rounded-lg border bg-white shadow-sm group-hover:scale-105 transition-transform",
                agent.color.replace("text-", "border-").replace("-500", "-100").replace("-400", "-100")
            )}>
                <agent.icon className={cn("h-5 w-5", agent.color)} />
            </div>
            <div className={cn(
                "absolute -bottom-1 -right-1 w-3 h-3 rounded-full border-2 border-white",
                agent.status === "working" ? "bg-amber-400 animate-pulse" : "bg-emerald-400"
            )} />
        </div>
        <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-900 uppercase tracking-tight truncate">{agent.name}</span>
                <span className="text-[9px] font-mono text-slate-400">{agent.status === "working" ? "BUSY" : "RDY"}</span>
            </div>
            <p className="text-[10px] text-slate-500 truncate">{agent.title}</p>
        </div>
    </button>
)

const MessageBlock = ({ message, agentInfo }: { message: ChatMessage; agentInfo?: Agent | null }) => {
    const isAgent = !!message.agent_key
    const { user } = useAuthStore()
    const isMe = message.user_id === user?.id && !isAgent

    return (
        <div className={cn(
            "flex gap-4 p-4 mb-2 rounded-xl transition-colors border border-transparent",
            isMe ? "bg-slate-50/50" : "hover:bg-slate-50/50 hover:border-slate-100"
        )}>
            <div className="shrink-0 pt-1">
                {isAgent ? (
                    <div className={cn(
                        "h-8 w-8 rounded-lg flex items-center justify-center border shadow-sm bg-white",
                        agentInfo?.color.replace("text-", "border-").replace("-500", "-200").replace("-400", "-200")
                    )}>
                        {agentInfo?.icon && <agentInfo.icon className={cn("h-4 w-4", agentInfo.color)} />}
                    </div>
                ) : (
                    <Avatar className="h-8 w-8 rounded-lg border border-slate-200">
                        <AvatarImage src={message.avatar_url} />
                        <AvatarFallback className="text-[10px] font-bold bg-slate-100 text-slate-600">
                            {message.user_name.charAt(0).toUpperCase()}
                        </AvatarFallback>
                    </Avatar>
                )}
            </div>

            <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                    <span className={cn(
                        "text-xs font-bold uppercase tracking-tight",
                        isAgent ? "text-slate-900" : "text-slate-700"
                    )}>
                        {isAgent ? agentInfo?.name : message.user_name}
                    </span>
                    {isAgent && (
                        <Badge variant="secondary" className="h-4 px-1 text-[9px] font-mono text-indigo-600 bg-indigo-50 border-indigo-100 rounded-sm">
                            AI UNIT
                        </Badge>
                    )}
                    <span className="text-[9px] font-mono text-slate-400 ml-auto">
                        {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                </div>

                <div className="text-sm text-slate-800 leading-relaxed font-medium whitespace-pre-wrap">
                    {message.content}
                </div>

                {message.audio_url && (
                    <div className="mt-3">
                        <audio controls className="h-8 w-full max-w-[200px] border border-emerald-100 rounded-lg bg-emerald-50/50">
                            <source src={message.audio_url} type="audio/mpeg" />
                        </audio>
                    </div>
                )}

                {isAgent && message.thinking_steps && message.thinking_steps.length > 0 && (
                    <div className="mt-3 pl-3 border-l-2 border-slate-200/60 space-y-1">
                        {message.thinking_steps.map((step, i) => (
                            <div key={i} className="flex items-center gap-2 text-[10px] text-slate-400 font-mono">
                                <Cpu className="h-3 w-3 opacity-50" />
                                <span>{step}</span>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}


export default function TeamChatTab() {
    const { user } = useAuthStore()
    const { toast } = useToast()
    const router = useRouter()

    // State
    const [messages, setMessages] = useState<ChatMessage[]>([])
    const [inputMessage, setInputMessage] = useState("")
    const [isLoading, setIsLoading] = useState(true)
    const [isSending, setIsSending] = useState(false)
    const [isConnected, setIsConnected] = useState(false)
    const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)
    const [intercomEnabled, setIntercomEnabled] = useState(false)
    const [isLeftSidebarOpen, setIsLeftSidebarOpen] = useState(true)
    const [isRightSidebarOpen, setIsRightSidebarOpen] = useState(true)
    const [opsOpen, setOpsOpen] = useState(true)
    const [actionsOpen, setActionsOpen] = useState(true)
    const [isRecording, setIsRecording] = useState(false)
    const mediaRecorderRef = useRef<MediaRecorder | null>(null)
    const audioChunksRef = useRef<Blob[]>([])

    // User Tier Logic
    const userPlan = (user as any)?.tier || 'free'
    const showUpgrade = userPlan !== 'pro'

    const messagesEndRef = useRef<HTMLDivElement>(null)
    const inputRef = useRef<HTMLInputElement>(null)

    // Scroll to bottom
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    // Initial Load
    useEffect(() => {
        loadMessages()
        checkIntercomStatus()

        // WebSocket Setup
        const status = websocketService.getConnectionStatus()
        setIsConnected(status)

        const unsubscribeMsg = websocketService.subscribe('team_chat_message', () => {
            setTimeout(loadMessages, 300)
        })

        const unsubscribeStatus = websocketService.onConnectionChange((connected: boolean) => {
            setIsConnected(connected)
        })

        if (!status) {
            websocketService.connect()
        }

        return () => {
            unsubscribeMsg()
            unsubscribeStatus()
        }
    }, [])

    const loadMessages = async () => {
        try {
            setIsLoading(true)
            const response = await apiClient.get("/api/v1/team/chat/messages?limit=50").catch(() => ({ data: { messages: [] } }))
            if (response.data?.messages) {
                setMessages(response.data.messages.reverse())
            }
        } catch (error) {
            console.error("Failed to load messages", error)
        } finally {
            setIsLoading(false)
        }
    }

    const checkIntercomStatus = async () => {
        try {
            // If user has access, fetch setting
            // Currently assuming if they can access this page they can check setting, 
            // but 'enabled' might be restricted by plan
            const res = await apiClient.getIntercommunicationSetting().catch(() => ({ data: { enabled: false } }))
            setIntercomEnabled(res.data?.enabled || false)
        } catch (e) {
            console.warn("Failed to check intercom status", e)
        }
    }

    const toggleIntercom = async (enabled: boolean) => {
        setIntercomEnabled(enabled)
        try {
            await (apiClient as any).updateIntercommunicationSetting(enabled)
            toast({
                title: enabled ? "Neural Link Established" : "Neural Link Severed",
                description: enabled ? "Agents are now operating in coordination." : "Agents are operating in isolated mode.",
            })
        } catch (e) {
            setIntercomEnabled(!enabled) // Revert
            toast({
                title: " Uplink Error",
                description: "Critical failure in neuro-sync protocol.",
                variant: "destructive"
            })
        }
    }

    const handleSendMessage = async () => {
        if (!inputMessage.trim() && !isSending) return
        setIsSending(true)

        try {
            let msg = inputMessage
            let agentKey = null

            // Quick slash command check
            if (selectedAgent) {
                msg = `/${selectedAgent.key} ${msg}`
                agentKey = selectedAgent.key
                setSelectedAgent(null) // Reset selection
            }

            // Parse slash command manually for UI boost
            if (msg.startsWith("/")) {
                const parts = msg.split(" ")
                const key = parts[0].slice(1)
                const agent = AVAILABLE_AGENTS.find(a => a.key === key)
                if (agent) agentKey = agent.key
            }

            if (agentKey) {
                // Agent Request
                await apiClient.post("/api/v1/team/agent-requests/create", {
                    agent_key: agentKey,
                    request_type: "chat",
                    request_data: { message: msg.replace(/^\/\w+\s/, ""), context: {} },
                })
                // Also add to chat log for visibility
                await apiClient.post("/api/v1/team/chat/message", {
                    content: msg,
                    message_type: "text"
                    // We don't verify agent_key here to avoid user impersonating agent visual
                })
            } else {
                // Normal message
                await apiClient.post("/api/v1/team/chat/message", {
                    content: msg,
                    message_type: "text"
                })
            }

            setInputMessage("")
            setTimeout(loadMessages, 300)

        } catch (error) {
            console.error(error)
            toast({ title: "Error sending message", variant: "destructive" })
        } finally {
            setIsSending(false)
        }
    }

    const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault()
            handleSendMessage()
        }
    }

    // --- Voice Implementation ---
    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
            const mediaRecorder = new MediaRecorder(stream)
            mediaRecorderRef.current = mediaRecorder
            audioChunksRef.current = []

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunksRef.current.push(event.data)
                }
            }

            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
                await processVoiceInput(audioBlob)
                // Stop all tracks to release microphone
                stream.getTracks().forEach(track => track.stop())
            }

            mediaRecorder.start()
            setIsRecording(true)
            toast({ title: "Neural Link Active", description: "Listening for command sequence..." })
        } catch (err) {
            console.error("Failed to start recording", err)
            toast({ title: "Link Error", description: "Microphone access denied or unavailable.", variant: "destructive" })
        }
    }

    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop()
            setIsRecording(false)
        }
    }

    const processVoiceInput = async (blob: Blob) => {
        try {
            const formData = new FormData()
            formData.append('audio_file', blob, 'recording.webm')

            toast({ title: "Decoding Pulse...", description: "Transcribing audio channel via Groq..." })

            const response = await apiClient.post("/api/v1/voice/transcribe", formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            })

            if (response.data?.text) {
                setInputMessage(response.data.text)
                toast({ title: "Signal Verified", description: "Audio successfully decoded." })
            }
        } catch (err) {
            console.error("Transcription failed", err)
            toast({ title: "Signal Loss", description: "Failed to decode audio sequence.", variant: "destructive" })
        }
    }

    // --- Session Management ---
    const handleNewChat = () => {
        setMessages([])
        toast({ title: "Buffer Cleared", description: "Initializing new strategic session." })
    }

    const handleViewHistory = () => {
        toast({ title: "Accessing Archives", description: "Retrieving previous mission logs..." })
        // Implementation for history view would go here
    }

    return (
        <div className="flex h-[calc(100vh-6rem)] bg-white overflow-hidden font-sans border border-emerald-100/50 rounded-2xl m-1 shadow-2xl">

            {/* LEFT PANE: WORKFORCE ROSTER (COLLAPSIBLE) */}
            <AnimatePresence initial={false}>
                {isLeftSidebarOpen ? (
                    <motion.div
                        initial={{ width: 0, opacity: 0 }}
                        animate={{ width: 280, opacity: 1 }}
                        exit={{ width: 0, opacity: 0 }}
                        className="border-r border-emerald-100 bg-white flex flex-col hidden lg:flex overflow-hidden relative"
                    >
                        <div className="p-4 border-b border-emerald-50 flex justify-between items-center bg-emerald-50/20">
                            <h3 className="text-[10px] font-black text-emerald-900 uppercase tracking-[0.2em] flex items-center gap-2 font-mono">
                                <Users className="h-4 w-4 text-emerald-600" />
                                Workforce Roster
                            </h3>
                            <Button size="icon" variant="ghost" className="h-6 w-6 hover:bg-emerald-100" onClick={() => setIsLeftSidebarOpen(false)}>
                                <ChevronLeft className="h-4 w-4 text-emerald-600" />
                            </Button>
                        </div>

                        <div className="p-3 border-b border-emerald-50">
                            <div className="relative">
                                <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-emerald-300" />
                                <Input className="h-8 pl-8 text-[11px] bg-emerald-50/30 border-emerald-100 font-mono text-emerald-900 placeholder:text-emerald-300 rounded-lg" placeholder="Search Agents..." />
                            </div>
                        </div>

                        <ScrollArea className="flex-1">
                            <div className="p-2 space-y-1">
                                {!intercomEnabled ? (
                                    AVAILABLE_AGENTS.map((agent) => (
                                        <button
                                            key={agent.key}
                                            onClick={() => {
                                                setSelectedAgent(agent)
                                                setInputMessage(`/${agent.key} `)
                                                inputRef.current?.focus()
                                            }}
                                            className={cn(
                                                "w-full flex items-center gap-3 p-3 rounded-xl text-left transition-all group relative overflow-hidden",
                                                selectedAgent?.key === agent.key
                                                    ? "bg-emerald-50 border border-emerald-100 shadow-sm scale-[1.02]"
                                                    : "hover:bg-emerald-50/50 border-transparent"
                                            )}
                                        >
                                            <div className={cn(
                                                "w-10 h-10 rounded-xl flex items-center justify-center transition-all border",
                                                selectedAgent?.key === agent.key ? "bg-emerald-500 text-white border-emerald-400" : "bg-white text-emerald-600 border-emerald-100 group-hover:border-emerald-200 shadow-sm"
                                            )}>
                                                <agent.icon className="h-5 w-5" />
                                            </div>
                                            <div className="flex flex-col min-w-0">
                                                <div className="flex items-center gap-2">
                                                    <span className={cn(
                                                        "font-bold text-[11px] uppercase tracking-tighter truncate",
                                                        selectedAgent?.key === agent.key ? "text-emerald-900" : "text-slate-600"
                                                    )}>{agent.name}</span>
                                                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                                                </div>
                                                <span className="text-[9px] text-emerald-600/60 font-mono font-medium truncate uppercase tracking-tighter">{agent.title}</span>
                                            </div>
                                        </button>
                                    ))
                                ) : (
                                    <div className="flex flex-col items-center justify-center py-12 px-4 text-center space-y-4">
                                        <div className="h-12 w-12 rounded-full bg-emerald-50 flex items-center justify-center">
                                            <Radio className="h-6 w-6 text-emerald-600 animate-pulse" />
                                        </div>
                                        <div>
                                            <p className="text-[10px] font-black text-emerald-900 uppercase tracking-widest font-mono">Neural_Link Active</p>
                                            <p className="text-[9px] text-slate-500 font-mono mt-1">Autonomous dispatch engaged. Direct personnel override offline.</p>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </ScrollArea>

                        {showUpgrade && (
                            <div className="p-4 bg-slate-900 m-3 rounded-xl text-white shadow-xl shadow-emerald-900/20">
                                <p className="text-[8px] font-mono mb-2 text-emerald-300 tracking-tighter">LICENSED FOR CORE OPERATIONS</p>
                                <Button
                                    className="w-full bg-emerald-500 hover:bg-emerald-600 h-8 text-[10px] font-black uppercase tracking-widest text-white border-0"
                                    onClick={() => router.push('/dashboard?tab=upgrade')}
                                >
                                    Scale Workforce
                                </Button>
                            </div>
                        )}
                    </motion.div>
                ) : (
                    <div className="w-14 border-r border-emerald-100 bg-emerald-50/10 flex flex-col items-center py-4 hidden lg:flex">
                        <Button size="icon" variant="ghost" className="hover:bg-emerald-100 mb-4" onClick={() => setIsLeftSidebarOpen(true)}>
                            <ChevronRight className="h-4 w-4 text-emerald-600" />
                        </Button>
                        <div className="flex flex-col gap-3">
                            {AVAILABLE_AGENTS.slice(0, 4).map((agent) => (
                                <button key={agent.key} onClick={() => {
                                    setIsLeftSidebarOpen(true)
                                    setSelectedAgent(agent)
                                }} className="w-8 h-8 rounded-lg bg-white border border-emerald-100 flex items-center justify-center text-emerald-600 shadow-sm">
                                    <agent.icon className="h-4 w-4" />
                                </button>
                            ))}
                        </div>
                    </div>
                )}
            </AnimatePresence>

            {/* MIDDLE PANE: EXECUTION FLOOR */}
            <div className="flex-1 flex flex-col h-full bg-emerald-50/5 relative min-w-0">
                <TacticalHeader
                    connectionStatus={isConnected}
                    onNewChat={handleNewChat}
                    onHistory={handleViewHistory}
                />

                <div className="flex-1 overflow-y-auto px-4 py-4" id="messages-container">
                    <div className="max-w-3xl mx-auto space-y-6">
                        <div className="flex items-center justify-center my-8">
                            <span className="text-[10px] font-mono text-emerald-600/30 uppercase tracking-[0.5em]">--- MISSION_OPERATIONS_INITIATED ---</span>
                        </div>
                        {messages.map(msg => (
                            <MessageBlock key={msg.id} message={msg} agentInfo={AVAILABLE_AGENTS.find(a => a.key === msg.agent_key)} />
                        ))}
                        <div className="h-32" /> {/* Spacer for floating input */}
                        <div ref={messagesEndRef} />
                    </div>
                </div>

                {/* INPUT AREA */}
                <div className="absolute bottom-6 left-1/2 -translate-x-1/2 w-full max-w-3xl px-4 z-50">
                    <motion.div
                        initial={{ y: 20, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        className="bg-white/80 backdrop-blur-xl border border-emerald-100/50 rounded-2xl p-2 shadow-2xl flex items-end gap-3 ring-1 ring-emerald-900/5"
                    >
                        <div className="flex-1 flex flex-col">
                            <Input
                                ref={inputRef}
                                className="border-0 bg-transparent shadow-none focus-visible:ring-0 text-slate-800 placeholder:text-emerald-200 h-10 font-medium px-4"
                                placeholder={isRecording ? "Recording audio channel..." : "Transmit command sequence..."}
                                value={inputMessage}
                                onChange={e => setInputMessage(e.target.value)}
                                onKeyDown={handleKeyPress}
                                disabled={isRecording}
                            />
                            <div className="flex items-center justify-between px-2 py-1 border-t border-emerald-50/50 mt-1">
                                <div className="flex gap-1">
                                    <DropdownMenu>
                                        <DropdownMenuTrigger asChild>
                                            <Button size="icon" variant="ghost" className="h-7 w-7 text-emerald-300 hover:text-emerald-600">
                                                <Paperclip className="h-4 w-4" />
                                            </Button>
                                        </DropdownMenuTrigger>
                                        <DropdownMenuContent align="start" className="w-56 p-1 bg-white/95 backdrop-blur-md border-emerald-100 rounded-xl shadow-xl">
                                            <DropdownMenuItem className="text-[10px] font-bold uppercase tracking-widest text-slate-700 focus:bg-emerald-50 focus:text-emerald-700 rounded-lg cursor-pointer py-2">
                                                <Globe className="mr-2 h-3.5 w-3.5 text-orange-500" />
                                                Social Media Asset
                                            </DropdownMenuItem>
                                            <DropdownMenuItem className="text-[10px] font-bold uppercase tracking-widest text-slate-700 focus:bg-emerald-50 focus:text-emerald-700 rounded-lg cursor-pointer py-2">
                                                <MessageSquare className="mr-2 h-3.5 w-3.5 text-purple-500" />
                                                Support Documentation
                                            </DropdownMenuItem>
                                            <DropdownMenuItem className="text-[10px] font-bold uppercase tracking-widest text-slate-700 focus:bg-emerald-50 focus:text-emerald-700 rounded-lg cursor-pointer py-2">
                                                <Target className="mr-2 h-3.5 w-3.5 text-amber-500" />
                                                Sales Lead Data
                                            </DropdownMenuItem>
                                            <DropdownMenuItem className="text-[10px] font-bold uppercase tracking-widest text-slate-700 focus:bg-emerald-50 focus:text-emerald-700 rounded-lg cursor-pointer py-2">
                                                <Layout className="mr-2 h-3.5 w-3.5 text-pink-500" />
                                                Marketing Campaign
                                            </DropdownMenuItem>
                                            <DropdownMenuItem className="text-[10px] font-bold uppercase tracking-widest text-slate-700 focus:bg-emerald-50 focus:text-emerald-700 rounded-lg cursor-pointer py-2">
                                                <Scissors className="mr-2 h-3.5 w-3.5 text-green-500" />
                                                Creative Brief
                                            </DropdownMenuItem>
                                            <DropdownMenuItem className="text-[10px] font-bold uppercase tracking-widest text-slate-700 focus:bg-emerald-50 focus:text-emerald-700 rounded-lg cursor-pointer py-2">
                                                <Database className="mr-2 h-3.5 w-3.5 text-sky-400" />
                                                Research Data
                                            </DropdownMenuItem>
                                        </DropdownMenuContent>
                                    </DropdownMenu>

                                    <Button
                                        size="icon"
                                        variant="ghost"
                                        className={cn(
                                            "h-7 w-7 transition-colors",
                                            isRecording ? "text-red-500 animate-pulse bg-red-50" : "text-emerald-300 hover:text-emerald-600"
                                        )}
                                        onClick={isRecording ? stopRecording : startRecording}
                                    >
                                        <Mic className="h-4 w-4" />
                                    </Button>
                                    <Badge variant="outline" className="h-5 text-[8px] font-mono bg-emerald-50/50 text-emerald-600 border-emerald-100 rounded-md">
                                        {isRecording ? "CAPTURE_ACTIVE" : "NEURAL_READY"}
                                    </Badge>
                                </div>
                                <span className="text-[9px] font-mono text-emerald-600/30 uppercase tracking-widest hidden sm:inline">SECURE_VOICE_LINK // GROQ_READY</span>
                            </div>
                        </div>
                        <Button
                            className="h-12 w-12 rounded-xl bg-emerald-900 hover:bg-emerald-600 text-white shadow-xl transition-all active:scale-95 border-0"
                            onClick={handleSendMessage}
                            disabled={isSending || !inputMessage.trim()}
                        >
                            <Send className="h-5 w-5" />
                        </Button>
                    </motion.div>
                </div>
            </div>

            {/* RIGHT PANE: MISSION OPERATIONS (COLLAPSIBLE) */}
            <AnimatePresence initial={false}>
                {isRightSidebarOpen ? (
                    <motion.div
                        initial={{ width: 0, opacity: 0 }}
                        animate={{ width: 300, opacity: 1 }}
                        exit={{ width: 0, opacity: 0 }}
                        className="border-l border-emerald-100 bg-white flex flex-col hidden xl:flex overflow-hidden relative shadow-sm"
                    >
                        <div className="p-4 border-b border-emerald-50 flex justify-between items-center bg-emerald-50/20">
                            <Button size="icon" variant="ghost" className="h-6 w-6 hover:bg-emerald-100" onClick={() => setIsRightSidebarOpen(false)}>
                                <ChevronRight className="h-4 w-4 text-emerald-600" />
                            </Button>
                            <h3 className="text-[10px] font-black text-emerald-900 uppercase tracking-[0.2em] flex items-center gap-2 font-mono">
                                <Activity className="h-4 w-4 text-emerald-600" />
                                Command Panel
                            </h3>
                        </div>

                        <div className="flex-1 p-4 space-y-4 overflow-y-auto">
                            {/* ACTIVE OPERATION SECTION */}
                            <div className="border border-emerald-100 rounded-xl overflow-hidden bg-white shadow-sm transition-all hover:border-emerald-200">
                                <button
                                    onClick={() => setOpsOpen(!opsOpen)}
                                    className="w-full flex items-center justify-between p-3 bg-emerald-50/20 hover:bg-emerald-50 transition-colors"
                                >
                                    <div className="flex items-center gap-2">
                                        <Bot className="h-4 w-4 text-emerald-600" />
                                        <span className="text-[10px] font-black text-emerald-900 uppercase tracking-widest font-mono">Operations</span>
                                    </div>
                                    <ChevronRight className={cn("h-4 w-4 text-emerald-600 transition-transform", opsOpen && "rotate-90")} />
                                </button>
                                <AnimatePresence>
                                    {opsOpen && (
                                        <motion.div initial={{ height: 0 }} animate={{ height: "auto" }} exit={{ height: 0 }} className="overflow-hidden">
                                            <div className="p-3 space-y-3 border-t border-emerald-50">
                                                <div className="flex items-center justify-between">
                                                    <span className="text-[10px] font-bold text-slate-700 uppercase font-mono">Link Workforce</span>
                                                    <Switch checked={intercomEnabled} onCheckedChange={toggleIntercom} />
                                                </div>
                                                <div className="p-2 bg-emerald-50/30 rounded-lg border border-emerald-100">
                                                    <p className="text-[9px] text-emerald-800 font-mono leading-relaxed">
                                                        LINK_STATE: {intercomEnabled ? "ESTABLISHED" : "INDEPENDENT"}
                                                        <br />
                                                        THREAT: MINIMAL
                                                    </p>
                                                </div>
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>

                            {/* TACTICAL ACTIONS SECTION */}
                            <div className="border border-emerald-100 rounded-xl overflow-hidden bg-white shadow-sm transition-all hover:border-emerald-200">
                                <button
                                    onClick={() => setActionsOpen(!actionsOpen)}
                                    className="w-full flex items-center justify-between p-3 bg-emerald-50/20 hover:bg-emerald-50 transition-colors"
                                >
                                    <div className="flex items-center gap-2">
                                        <Zap className="h-4 w-4 text-emerald-600" />
                                        <span className="text-[10px] font-black text-emerald-900 uppercase tracking-widest font-mono">Tactical Actions</span>
                                    </div>
                                    <ChevronRight className={cn("h-4 w-4 text-emerald-600 transition-transform", actionsOpen && "rotate-90")} />
                                </button>
                                <AnimatePresence>
                                    {actionsOpen && (
                                        <motion.div initial={{ height: 0 }} animate={{ height: "auto" }} exit={{ height: 0 }} className="overflow-hidden">
                                            <div className="p-3 grid grid-cols-2 gap-2 border-t border-emerald-50">
                                                <Button variant="outline" size="sm" className="h-16 flex flex-col gap-1 border-emerald-100 hover:border-emerald-500 hover:bg-emerald-50 bg-white group">
                                                    <TrendingUp className="h-4 w-4 text-emerald-500 transition-transform group-hover:scale-110" />
                                                    <span className="text-[8px] font-black uppercase tracking-tighter font-mono tracking-[0.1em]">Analyze</span>
                                                </Button>
                                                <Button variant="outline" size="sm" className="h-16 flex flex-col gap-1 border-emerald-100 hover:border-red-500 hover:bg-red-50 bg-white group">
                                                    <Shield className="h-4 w-4 text-red-500 transition-transform group-hover:scale-110" />
                                                    <span className="text-[8px] font-black uppercase tracking-tighter font-mono tracking-[0.1em]">Lockdown</span>
                                                </Button>
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>

                            {/* STATUS READOUT */}
                            <div className="p-3 bg-slate-900 rounded-xl border border-emerald-500/20 text-emerald-500 font-mono text-[9px] space-y-1 shadow-lg">
                                <p className="text-white font-black text-[10px] uppercase mb-2 flex items-center gap-2">
                                    <Terminal className="h-3 w-3" />
                                    Diagnostics
                                </p>
                                <div className="flex justify-between">
                                    <span>Sync</span>
                                    <span className="text-emerald-300">STABLE</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Load</span>
                                    <span className="text-emerald-300 text-[8px]">12% [OK]</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>State</span>
                                    <span className="text-emerald-300 font-bold">VERIFIED</span>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                ) : (
                    <div className="w-14 border-l border-emerald-100 bg-emerald-50/10 flex flex-col items-center py-4 hidden xl:flex">
                        <Button size="icon" variant="ghost" className="hover:bg-emerald-100 mb-4" onClick={() => setIsRightSidebarOpen(true)}>
                            <ChevronLeft className="h-4 w-4 text-emerald-600" />
                        </Button>
                        <div className="flex flex-col gap-3">
                            <Activity className="h-5 w-5 text-emerald-400" />
                            <Bot className="h-5 w-5 text-emerald-400 opacity-50" />
                            <Zap className="h-5 w-5 text-emerald-400 opacity-50" />
                        </div>
                    </div>
                )}
            </AnimatePresence>

        </div>
    )
}
