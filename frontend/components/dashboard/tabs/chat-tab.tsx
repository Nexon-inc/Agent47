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
    Database,
    Image as ImageIcon
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

// --- Color Helpers ---
const getAgentColor = (color: string) => {
    const base = color.replace('text-', '')
    return {
        text: color,
        bg: `bg-${base.replace('-500', '-50').replace('-400', '-50')}`,
        border: `border-${base.replace('-500', '-200').replace('-400', '-200')}`,
        accent: `bg-${base}`,
        darkText: `text-${base.replace('-500', '-900').replace('-400', '-900')}`,
    }
}

// --- Components ---

const TacticalHeader = ({ connectionStatus, onNewChat, onHistory }: { connectionStatus: boolean, onNewChat: () => void, onHistory: () => void }) => (
    <div className="flex items-center justify-between px-6 py-3 border-b border-slate-200 bg-white/95 backdrop-blur-sm sticky top-0 z-[60] shadow-sm">
        <div className="flex items-center space-x-3">
            <div className="h-8 w-8 bg-slate-50 rounded-lg border border-slate-200 flex items-center justify-center">
                <Radio className={`h-4 w-4 ${connectionStatus ? "text-emerald-600 animate-pulse" : "text-slate-400"}`} />
            </div>
            <div>
                <h1 className="text-sm font-black uppercase tracking-widest leading-none text-slate-900">Strategy Room</h1>
                <div className="flex items-center gap-3 mt-1">
                    <p className="text-[10px] font-mono text-emerald-600 font-medium flex items-center gap-2">
                        <span className={`inline-block w-2 h-2 rounded-full ${connectionStatus ? "bg-emerald-500 animate-ping" : "bg-red-500"}`} />
                        {connectionStatus ? "SECURE_CHANNEL // ACTIVE" : "CONNECTION_OFFLINE"}
                    </p>
                    <span className="text-[9px] font-mono text-slate-400">LAT: 12ms // ENC: AES-256</span>
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
            <Separator orientation="vertical" className="h-4 mx-1 bg-slate-200" />
            <Badge variant="outline" className="font-mono text-[10px] text-emerald-600 border-emerald-200 bg-emerald-50/50">
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
                        agentInfo ? getAgentColor(agentInfo.color).border : "border-slate-200"
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
    const [hiredAgentKeys, setHiredAgentKeys] = useState<string[]>([])
    const [isHiredLoading, setIsHiredLoading] = useState(true)
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
        fetchHiredAgents()

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
        // Skip team chat history if an individual agent is selected and no team context exists
        if (agentKey) {
            console.log(`[Chat] Individual engagement with ${agentKey}. Skipping team history sync.`);
            setIsLoading(false);
            return;
        }

        try {
            setIsLoading(true)
            const response = await apiClient.get("/api/v1/team/chat/messages?limit=50").catch(() => ({ data: { messages: [] } }))
            if (response.data?.messages) {
                setMessages(response.data.messages.reverse())
            }
        } catch (error: any) {
            console.error("Failed to load command history:", error)
        } finally {
            setIsLoading(false)
        }
    }

    const fetchHiredAgents = async () => {
        try {
            setIsHiredLoading(true)
            const hired = await apiClient.getSelectedAgents()
            // Backend might return agent objects with key, agent_key, or agent_id
            const keys = hired.map((a: any) => a.key || a.agent_key || a.agent_id || a.id)
            setHiredAgentKeys(keys)
        } catch (error) {
            console.error("Failed to fetch hired agents", error)
        } finally {
            setIsHiredLoading(false)
        }
    }

    const filteredAgents = AVAILABLE_AGENTS.filter(agent =>
        !isHiredLoading && hiredAgentKeys.includes(agent.key)
    )

    // If loading or we have none, we might want to default to nothing 
    // but keep a fallback for development if needed. 
    // The user wants strictly "chosen employees only".

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
                // Individual Agent Engagement - Call Direct Endpoint ONLY
                // We no longer hit the team chat endpoints to avoid 404s when no team exists.

                // 1. Manually add user message to local UI state for immediate feedback
                const userMessage: ChatMessage = {
                    id: Date.now(),
                    team_id: 0,
                    user_id: user?.id || 0,
                    user_name: user?.username || "You",
                    agent_key: null,
                    message_type: "text",
                    content: msg,
                    created_at: new Date().toISOString()
                }
                setMessages(prev => [...prev, userMessage])
                setInputMessage("")

                try {
                    // 2. Call the direct agent endpoint for immediate response
                    const response = await apiClient.post(`/api/agents/${agentKey}/${agentKey}-chat/message`, {
                        message: msg.replace(/^\/\w+\s/, ""),
                        session_id: "default-session"
                    })

                    // Handle response Data
                    const responseData = response.data?.data || response.data
                    const responseText = responseData?.response || responseData?.content || responseData?.text_content || "I have processed your request."

                    // 3. Manually add agent response to local UI state
                    const agentMessage: ChatMessage = {
                        id: Date.now() + 1,
                        team_id: 0,
                        user_id: 0, // System/Agent
                        user_name: agentKey.charAt(0).toUpperCase() + agentKey.slice(1),
                        agent_key: agentKey,
                        message_type: "agent_output",
                        content: responseText,
                        created_at: new Date().toISOString()
                    }
                    setMessages(prev => [...prev, agentMessage])

                    // We skip saving to team-output to bypass the 404 team check
                } catch (agentErr: any) {
                    console.error("Direct agent communication failed:", agentErr)
                    toast({
                        title: "Agent Offline",
                        description: `${agentKey} is not responding via direct link.`,
                        variant: "destructive"
                    })
                }
            } else {
                // Normal generalized team message (requires a team)
                try {
                    await apiClient.post("/api/v1/team/chat/message", {
                        content: msg,
                        message_type: "text"
                    })
                    setInputMessage("")
                    setTimeout(loadMessages, 300)
                } catch (err: any) {
                    if (err.response?.status === 404) {
                        toast({
                            title: "Team Required",
                            description: "Strategic coordination requires a Strategic Command (Team). Select an individual agent for 1-on-1 tactics.",
                            variant: "destructive"
                        })
                    } else {
                        throw err
                    }
                }
            }
        } catch (error: any) {
            console.error("Message transmission error:", error)
            if (error.response?.status !== 404) {
                toast({ title: "Signal Lost", description: "Failed to transmit command sequence.", variant: "destructive" })
            }
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
        <div className="flex w-full h-full overflow-hidden bg-white select-none relative">
            <style jsx global>{`
                /* Hide scrollbar for Chrome, Safari and Opera */
                .no-scrollbar::-webkit-scrollbar {
                    display: none;
                }

                /* Hide scrollbar for IE, Edge and Firefox */
                .no-scrollbar {
                    -ms-overflow-style: none;  /* IE and Edge */
                    scrollbar-width: none;  /* Firefox */
                }

                * {
                    scrollbar-width: none !important;
                    -ms-overflow-style: none !important;
                }
                *::-webkit-scrollbar {
                    display: none !important;
                }
            `}</style>

            {/* LEFT PANE: WORKFORCE ROSTER (COLLAPSIBLE) */}
            <AnimatePresence initial={false}>
                {isLeftSidebarOpen ? (
                    <motion.div
                        initial={{ width: 0, opacity: 0 }}
                        animate={{ width: 280, opacity: 1 }}
                        exit={{ width: 0, opacity: 0 }}
                        className="border-r border-slate-200 bg-white flex flex-col hidden lg:flex overflow-hidden relative"
                    >
                        <div className="p-4 border-b border-slate-200 flex justify-between items-center bg-slate-50/50">
                            <h3 className="text-[10px] font-black text-slate-900 uppercase tracking-[0.2em] flex items-center gap-2 font-mono">
                                <Users className="h-4 w-4 text-emerald-600" />
                                Workforce Roster
                            </h3>
                            <Button size="icon" variant="ghost" className="h-6 w-6 text-slate-400 hover:text-emerald-600 hover:bg-emerald-50" onClick={() => setIsLeftSidebarOpen(false)}>
                                <ChevronLeft className="h-4 w-4" />
                            </Button>
                        </div>

                        <div className="p-3 border-b border-slate-100 bg-slate-50/50">
                            <div className="relative">
                                <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-400" />
                                <Input className="h-8 pl-8 text-[11px] bg-white border-slate-200 font-mono text-slate-900 placeholder:text-slate-400 rounded-lg shadow-sm" placeholder="Search Agents..." />
                            </div>
                        </div>

                        <ScrollArea className="flex-1 no-scrollbar">
                            <div className="p-2 space-y-1">
                                {!intercomEnabled ? (
                                    filteredAgents.map((agent) => (
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
                                                    ? `${getAgentColor(agent.color).bg} ${getAgentColor(agent.color).border} border shadow-sm scale-[1.02]`
                                                    : `hover:${getAgentColor(agent.color).bg}/50 border-transparent`
                                            )}
                                        >
                                            <div className={cn(
                                                "w-10 h-10 rounded-xl flex items-center justify-center transition-all border",
                                                selectedAgent?.key === agent.key
                                                    ? `${getAgentColor(agent.color).accent} text-white border-transparent`
                                                    : `bg-white ${agent.color} ${getAgentColor(agent.color).border.replace('border-', 'border-opacity-50 border-')} group-hover:border-opacity-100 shadow-sm`
                                            )}>
                                                <agent.icon className="h-5 w-5" />
                                            </div>
                                            <div className="flex flex-col min-w-0">
                                                <div className="flex items-center gap-2">
                                                    <span className={cn(
                                                        "font-bold text-[11px] uppercase tracking-tighter truncate",
                                                        selectedAgent?.key === agent.key ? getAgentColor(agent.color).darkText : "text-slate-600"
                                                    )}>{agent.name}</span>
                                                    <div className={cn("w-1.5 h-1.5 rounded-full animate-pulse", getAgentColor(agent.color).accent)} />
                                                </div>
                                                <span className={cn("text-[9px] font-mono font-medium truncate uppercase tracking-tighter", getAgentColor(agent.color).text, "opacity-60")}>{agent.title}</span>
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
                    <div className="w-14 border-r border-slate-200 bg-white flex flex-col items-center py-4 space-y-4 hidden lg:flex">
                        <Button size="icon" variant="ghost" className="text-slate-400 hover:text-emerald-600 hover:bg-emerald-50" onClick={() => setIsLeftSidebarOpen(true)}>
                            <ChevronRight className="h-4 w-4" />
                        </Button>
                        <div className="flex flex-col gap-3">
                            {filteredAgents.map((agent) => (
                                <button key={agent.key} onClick={() => {
                                    setIsLeftSidebarOpen(true)
                                    setSelectedAgent(agent)
                                }} className={cn(
                                    "w-9 h-9 rounded-lg border flex items-center justify-center shadow-sm transition-all bg-white hover:border-slate-300",
                                    agent.color.replace("text-", "border-").replace("-500", "-100").replace("-400", "-100")
                                )}>
                                    <agent.icon className={cn("h-5 w-5", agent.color)} />
                                </button>
                            ))}
                        </div>
                    </div>
                )}
            </AnimatePresence>

            {/* MIDDLE PANE: EXECUTION FLOOR */}
            <div className="flex-1 flex flex-col h-full bg-emerald-50/5 relative min-w-0 overflow-hidden">
                <TacticalHeader
                    connectionStatus={isConnected}
                    onNewChat={handleNewChat}
                    onHistory={handleViewHistory}
                />

                <div className="flex-1 overflow-y-auto px-4 py-8 scroll-smooth isolate no-scrollbar" id="messages-container">
                    <div className="max-w-3xl mx-auto space-y-6">
                        <div className="flex items-center justify-center my-8">
                            <span className="text-[10px] font-mono text-slate-400 uppercase tracking-[0.5em]">--- MISSION_OPERATIONS_INITIATED ---</span>
                        </div>
                        {messages.map(msg => (
                            <MessageBlock key={msg.id} message={msg} agentInfo={AVAILABLE_AGENTS.find(a => a.key === msg.agent_key)} />
                        ))}
                        <div className="h-40" /> {/* Spacer for floating input */}
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
                                        <DropdownMenuContent align="start" className="w-64 p-2 bg-white border-slate-200 rounded-xl shadow-2xl">
                                            <div className="px-2 py-1.5 border-b border-slate-100 mb-1">
                                                <p className="text-[9px] font-black text-emerald-600 uppercase tracking-widest font-mono">Neural Interface / Assets</p>
                                            </div>
                                            <div className="grid grid-cols-2 gap-1">
                                                <DropdownMenuItem className="text-[10px] font-bold uppercase tracking-widest text-slate-600 focus:bg-emerald-50 focus:text-emerald-700 rounded-lg cursor-pointer py-2">
                                                    <FileText className="mr-2 h-3.5 w-3.5 text-blue-500" />
                                                    PDF / Docs
                                                </DropdownMenuItem>
                                                <DropdownMenuItem className="text-[10px] font-bold uppercase tracking-widest text-slate-600 focus:bg-emerald-50 focus:text-emerald-700 rounded-lg cursor-pointer py-2">
                                                    <ImageIcon className="mr-2 h-3.5 w-3.5 text-emerald-500" />
                                                    Assets / Img
                                                </DropdownMenuItem>
                                                <DropdownMenuItem className="text-[10px] font-bold uppercase tracking-widest text-slate-600 focus:bg-emerald-50 focus:text-emerald-700 rounded-lg cursor-pointer py-2">
                                                    <Terminal className="mr-2 h-3.5 w-3.5 text-amber-500" />
                                                    Scripts
                                                </DropdownMenuItem>
                                                <DropdownMenuItem className="text-[10px] font-bold uppercase tracking-widest text-slate-600 focus:bg-emerald-50 focus:text-emerald-700 rounded-lg cursor-pointer py-2">
                                                    <Zap className="mr-2 h-3.5 w-3.5 text-purple-500" />
                                                    Prompts
                                                </DropdownMenuItem>
                                                <DropdownMenuItem className="text-[10px] font-bold uppercase tracking-widest text-slate-600 focus:bg-emerald-50 focus:text-emerald-700 rounded-lg cursor-pointer py-2">
                                                    <Activity className="mr-2 h-3.5 w-3.5 text-red-500" />
                                                    Briefs
                                                </DropdownMenuItem>
                                                <DropdownMenuItem className="text-[10px] font-bold uppercase tracking-widest text-slate-600 focus:bg-emerald-50 focus:text-emerald-700 rounded-lg cursor-pointer py-2">
                                                    <Globe className="mr-2 h-3.5 w-3.5 text-sky-500" />
                                                    Ads / Social
                                                </DropdownMenuItem>
                                                <DropdownMenuItem className="text-[10px] font-bold uppercase tracking-widest text-slate-600 focus:bg-emerald-50 focus:text-emerald-700 rounded-lg cursor-pointer py-2">
                                                    <MoreVertical className="mr-2 h-3.5 w-3.5 text-slate-400" />
                                                    Drive / Links
                                                </DropdownMenuItem>
                                                <DropdownMenuItem className="text-[10px] font-bold uppercase tracking-widest text-slate-600 focus:bg-emerald-50 focus:text-emerald-700 rounded-lg cursor-pointer py-2">
                                                    <Shield className="mr-2 h-3.5 w-3.5 text-emerald-500" />
                                                    Cloud Storage
                                                </DropdownMenuItem>
                                            </div>
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
                        className="border-l border-slate-200 bg-white flex flex-col hidden xl:flex overflow-hidden relative"
                    >
                        <div className="p-4 border-b border-slate-200 flex justify-between items-center bg-slate-50/50">
                            <Button size="icon" variant="ghost" className="h-6 w-6 text-slate-400 hover:text-emerald-600 hover:bg-emerald-50" onClick={() => setIsRightSidebarOpen(false)}>
                                <ChevronRight className="h-4 w-4" />
                            </Button>
                            <h3 className="text-[10px] font-black text-slate-900 uppercase tracking-[0.2em] flex items-center gap-2 font-mono">
                                <Activity className="h-4 w-4 text-emerald-600" />
                                Command Panel
                            </h3>
                        </div>

                        <div className="flex-1 p-4 space-y-4 overflow-y-auto bg-slate-50/30 no-scrollbar">
                            {/* ACTIVE OPERATION SECTION */}
                            <div className="border border-slate-200 rounded-xl overflow-hidden bg-white shadow-sm transition-all hover:border-emerald-500/30">
                                <button
                                    onClick={() => setOpsOpen(!opsOpen)}
                                    className="w-full flex items-center justify-between p-3 bg-slate-50 hover:bg-slate-100 transition-colors"
                                >
                                    <div className="flex items-center gap-2">
                                        <Bot className="h-4 w-4 text-emerald-600" />
                                        <span className="text-[10px] font-black text-slate-900 uppercase tracking-widest font-mono">Operations</span>
                                    </div>
                                    <ChevronRight className={cn("h-4 w-4 text-slate-400 transition-transform", opsOpen && "rotate-90")} />
                                </button>
                                <AnimatePresence>
                                    {opsOpen && (
                                        <motion.div initial={{ height: 0 }} animate={{ height: "auto" }} exit={{ height: 0 }} className="overflow-hidden">
                                            <div className="p-3 space-y-3 border-t border-slate-100">
                                                <div className="flex items-center justify-between">
                                                    <span className="text-[10px] font-bold text-slate-700 uppercase font-mono">Neural Link</span>
                                                    <Switch
                                                        checked={intercomEnabled}
                                                        onCheckedChange={toggleIntercom}
                                                        className="data-[state=checked]:bg-emerald-500"
                                                        disabled={userPlan !== 'starter' && userPlan !== 'pro'}
                                                    />
                                                </div>
                                                <div className="p-2 bg-slate-50 rounded-lg border border-slate-100">
                                                    {userPlan === 'starter' || userPlan === 'pro' ? (
                                                        <p className="text-[9px] text-emerald-600 font-mono leading-relaxed">
                                                            LINK_STATE: {intercomEnabled ? "ESTABLISHED" : "INDEPENDENT"}
                                                            <br />
                                                            THREAT: MINIMAL
                                                        </p>
                                                    ) : (
                                                        <p className="text-[9px] text-amber-600 font-mono leading-relaxed">
                                                            RESTRICTED: STARTER/PRO_ONLY
                                                            <br />
                                                            Contact HQ for neural upgrade.
                                                        </p>
                                                    )}
                                                </div>
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>

                            {/* TACTICAL ACTIONS SECTION */}
                            <div className="border border-slate-200 rounded-xl overflow-hidden bg-white shadow-sm transition-all hover:border-emerald-500/30">
                                <button
                                    onClick={() => setActionsOpen(!actionsOpen)}
                                    className="w-full flex items-center justify-between p-3 bg-slate-50 hover:bg-slate-100 transition-colors"
                                >
                                    <div className="flex items-center gap-2">
                                        <Zap className="h-4 w-4 text-emerald-600" />
                                        <span className="text-[10px] font-black text-slate-900 uppercase tracking-widest font-mono">Tactical Actions</span>
                                    </div>
                                    <ChevronRight className={cn("h-4 w-4 text-slate-400 transition-transform", actionsOpen && "rotate-90")} />
                                </button>
                                <AnimatePresence>
                                    {actionsOpen && (
                                        <motion.div initial={{ height: 0 }} animate={{ height: "auto" }} exit={{ height: 0 }} className="overflow-hidden">
                                            <div className="p-3 grid grid-cols-2 gap-2 border-t border-slate-100">
                                                <Button variant="outline" size="sm" className="h-16 flex flex-col gap-1 border-slate-200 hover:border-emerald-500 hover:bg-emerald-50 bg-white group shadow-sm transition-all">
                                                    <TrendingUp className="h-4 w-4 text-emerald-500 transition-transform group-hover:scale-110" />
                                                    <span className="text-[8px] font-black uppercase tracking-tighter font-mono tracking-[0.1em] text-slate-600">Analyze</span>
                                                </Button>
                                                <Button variant="outline" size="sm" className="h-16 flex flex-col gap-1 border-slate-200 hover:border-red-500 hover:bg-red-50 bg-white group shadow-sm transition-all">
                                                    <Shield className="h-4 w-4 text-red-500 transition-transform group-hover:scale-110" />
                                                    <span className="text-[8px] font-black uppercase tracking-tighter font-mono tracking-[0.1em] text-slate-600">Lockdown</span>
                                                </Button>
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        </div>
                    </motion.div>
                ) : (
                    <div className="w-14 border-l border-slate-200 bg-white flex flex-col items-center py-4 space-y-6 hidden xl:flex">
                        <Button size="icon" variant="ghost" className="text-slate-400 hover:text-emerald-600 hover:bg-emerald-50" onClick={() => setIsRightSidebarOpen(true)}>
                            <ChevronLeft className="h-4 w-4" />
                        </Button>
                        <div className="flex flex-col gap-4">
                            <Activity className="h-5 w-5 text-emerald-600" />
                            <Bot className="h-5 w-5 text-slate-400 hover:text-emerald-600 cursor-pointer transition-colors" />
                            <Zap className="h-5 w-5 text-slate-400 hover:text-emerald-600 cursor-pointer transition-colors" />
                            <Shield className="h-5 w-5 text-slate-400 hover:text-red-500 cursor-pointer transition-colors" />
                            <TrendingUp className="h-5 w-5 text-slate-400 hover:text-emerald-600 cursor-pointer transition-colors" />
                        </div>
                    </div>
                )}
            </AnimatePresence>
        </div>
    )
}
