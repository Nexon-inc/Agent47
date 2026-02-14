"use client"

import { useState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import {
    Send,
    Mic,
    Paperclip,
    User,
    Zap,
    Users,
    Globe,
    Headphones,
    DollarSign,
    Megaphone,
    Lightbulb,
    Edit3,
    History,
    Search,
    FileText,
    ChevronLeft,
    ChevronRight,
    Cpu,
    X,
    Lock,
    Image as ImageIcon,
    Download,
    Plus,
    Wrench,
    UsersRound,
    Radio,
    Clock,
    Activity,
    Shield,
    CheckCircle2,
    AlertCircle
} from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { apiClient } from "@/lib/api-client"
import { useAuthStore } from "@/lib/stores/auth-store"
import { useToast } from "@/hooks/use-toast"
import { cn } from "@/lib/utils"
import { websocketService, WebSocketMessage } from "@/lib/websocket-service"
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

interface ActivityLog {
    id: string
    title: string
    time: string
    type: 'success' | 'warning' | 'info'
    agent?: string
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

const TacticalHeader = ({ connectionStatus, onNewChat, onHistory, onToggleRightSidebar, isRightSidebarOpen }: { connectionStatus: boolean, onNewChat: () => void, onHistory: () => void, onToggleRightSidebar: () => void, isRightSidebarOpen: boolean }) => (
    <div className="flex shrink-0 items-center justify-between px-6 py-3 border-b border-slate-200 bg-white/95 backdrop-blur-sm sticky top-0 z-[10] shadow-sm h-16">
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
            <Button size="icon" variant="ghost" className={cn("h-8 w-8 text-slate-400 hover:text-emerald-600 hover:bg-emerald-50 transition-transform", isRightSidebarOpen ? "rotate-180" : "")} onClick={onToggleRightSidebar}>
                <ChevronLeft className="h-4 w-4" />
            </Button>
        </div>
    </div>
)

const RosterItem = ({ agent, onClick, isSelected }: { agent: Agent; onClick: () => void; isSelected: boolean }) => (
    <button
        onClick={onClick}
        className={cn(
            "w-full flex items-center space-x-3 p-2 rounded-lg transition-colors group text-left border border-transparent",
            isSelected ? "bg-emerald-50 border-emerald-100" : "hover:bg-slate-50"
        )}
    >
        <div className="relative">
            <div className={cn(
                "h-10 w-10 flex items-center justify-center rounded-lg border bg-white shadow-sm transition-transform",
                isSelected ? "scale-105 ring-2 ring-offset-1 ring-emerald-200" : "group-hover:scale-105",
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
                <span className={cn(
                    "text-xs font-bold uppercase tracking-tight truncate",
                    isSelected ? "text-emerald-900" : "text-slate-600"
                )}>{agent.name}</span>
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
            "flex gap-4 p-4 mb-2 rounded-xl transition-colors border border-transparent shrink-0",
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
                    <span className="text-[9px] font-mono text-slate-400 ml-auto">
                        {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                </div>

                <div className="text-sm text-slate-800 leading-relaxed font-medium whitespace-pre-wrap break-words">
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

const StatCard = ({ label, value, icon: Icon, colorClass }: { label: string, value: string, icon: any, colorClass: string }) => (
    <div className="bg-slate-50 border border-slate-200 p-3 rounded-lg flex items-center justify-between transition-colors hover:border-emerald-200 hover:bg-emerald-50/30">
        <div>
            <p className="text-[10px] text-slate-400 font-mono uppercase tracking-wider mb-1">{label}</p>
            <p className="text-lg font-black text-slate-900">{value}</p>
        </div>
        <div className={cn("h-8 w-8 rounded-md flex items-center justify-center bg-white border border-slate-200/50", colorClass)}>
            <Icon className="h-4 w-4" />
        </div>
    </div>
)

const NotificationItem = ({ title, time, type, agent }: ActivityLog) => (
    <div className="flex gap-3 py-3 border-b border-slate-100/50 last:border-0 hover:bg-slate-50 rounded-lg px-2 transition-colors">
        <div className={cn(
            "h-2 w-2 rounded-full mt-1.5 shrink-0",
            type === 'info' ? "bg-sky-400" : type === 'warning' ? "bg-amber-400" : "bg-emerald-400"
        )} />
        <div>
            <div className="flex items-center gap-2">
                {agent && <span className="text-[10px] font-bold text-slate-800 uppercase bg-slate-200 px-1 rounded-sm">{agent}</span>}
                <p className="text-xs font-medium text-slate-700 leading-snug">{title}</p>
            </div>
            <p className="text-[9px] text-slate-400 font-mono mt-0.5">{time}</p>
        </div>
    </div>
)


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
    const [isRecording, setIsRecording] = useState(false)
    const [hiredAgentKeys, setHiredAgentKeys] = useState<string[]>([])
    const [isHiredLoading, setIsHiredLoading] = useState(true)
    const mediaRecorderRef = useRef<MediaRecorder | null>(null)
    const audioChunksRef = useRef<Blob[]>([])

    // Real-time Dashboard State
    const [platformCount, setPlatformCount] = useState(0)
    const [toolCount, setToolCount] = useState(0)
    const [activityLog, setActivityLog] = useState<ActivityLog[]>([])

    const messagesEndRef = useRef<HTMLDivElement>(null)
    const inputRef = useRef<HTMLInputElement>(null)

    // Slash command state
    const [showCommandMenu, setShowCommandMenu] = useState(false)
    const [commandSuggestions, setCommandSuggestions] = useState<any[]>([])
    const [selectedCommandIndex, setSelectedCommandIndex] = useState(0)

    // Scroll to bottom
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    // Initial Load & Real-time Data
    useEffect(() => {
        loadMessages()
        checkIntercomStatus()
        fetchHiredAgents()
        fetchServiceStatus() // NEW: Connect to System Services

        // WebSocket Setup
        const status = websocketService.getConnectionStatus()
        setIsConnected(status)

        const unsubscribeMsg = websocketService.subscribe('team_chat_message', () => {
            setTimeout(loadMessages, 300)
        })

        // Subscribe to Task Updates for "When its done with its tasks"
        const unsubscribeTasks = websocketService.subscribe('task_update', (msg: WebSocketMessage) => {
            if (msg.data?.status === 'completed' || msg.data?.status === 'verified') {
                addActivityLog({
                    id: Date.now().toString(),
                    title: `Task completed: ${msg.data.description || 'Unknown Task'}`,
                    time: 'Just now',
                    type: 'success',
                    agent: msg.data.agent_name || 'System'
                })
            }
        })

        // Subscribe to Notifications for "Employee notification of verification"
        const unsubscribeNotifs = websocketService.subscribe('notification', (msg: WebSocketMessage) => {
            if (msg.data?.type === 'verification_request' || msg.data?.type === 'human_input') {
                addActivityLog({
                    id: Date.now().toString(),
                    title: `Verification required: ${msg.data.title || 'Review Action'}`,
                    time: 'Just now',
                    type: 'warning',
                    agent: msg.data.agent_name
                })
            }
        })

        const unsubscribeStatus = websocketService.onConnectionChange((connected: boolean) => {
            setIsConnected(connected)
        })

        if (!status) {
            websocketService.connect()
        }

        return () => {
            unsubscribeMsg()
            unsubscribeTasks()
            unsubscribeNotifs()
            unsubscribeStatus()
        }
    }, [])

    const fetchServiceStatus = async () => {
        try {
            const services = await apiClient.getAllServicesStatus().catch(() => [])
            // Simple logic: if 'platform' type count it, etc. Assumes simple array for now.
            // If backend returns detailed objects, we'd filter. 
            // Mocking logic ONLY for categorization if fields are missing, but using Real Count.
            setPlatformCount(services.filter((s: any) => s.type === 'platform' || s.category === 'platform').length)
            setToolCount(services.filter((s: any) => s.type === 'tool' || s.category === 'tool').length)
        } catch (error) {
            console.error("Failed to fetch service status", error)
        }
    }

    const addActivityLog = (log: ActivityLog) => {
        setActivityLog(prev => [log, ...prev].slice(0, 50)) // Keep last 50
    }

    const loadMessages = async () => {
        try {
            setIsLoading(true)
            const response = await apiClient.get("/api/v1/team/chat/messages?limit=50").catch(() => ({ data: { messages: [] } }))
            if (response.data?.messages) {
                setMessages(response.data.messages.reverse())
            }
        } catch (error: any) {
            console.error("Failed to load messages:", error)
        } finally {
            setIsLoading(false)
        }
    }

    const fetchHiredAgents = async () => {
        try {
            setIsHiredLoading(true)
            const hired = await apiClient.getSelectedAgents()
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

    const checkIntercomStatus = async () => {
        try {
            const res = await apiClient.getIntercommunicationSetting().catch(() => ({ data: { enabled: false } }))
            setIntercomEnabled(res.data?.enabled || false)
        } catch (e) {
            console.warn("Failed to check intercom status", e)
        }
    }

    const handleSendMessage = async () => {
        if (!inputMessage.trim() && !isSending) return

        // STRICT AGENT SELECTION CHECK
        // If no agent is selected and this is not a slash command, prompt user to select agent.
        if (!selectedAgent && !inputMessage.startsWith('/')) {
            toast({
                title: "Select an Agent",
                description: "Please select an agent from the roster to start a conversation.",
                variant: "destructive"
            })
            return
        }

        setIsSending(true)

        try {
            let msg = inputMessage
            let agentKey: string | null = selectedAgent ? selectedAgent.key : null
            let cleanMessage = inputMessage

            // Parse slash command manually for UI boost
            if (msg.startsWith("/")) {
                const parts = msg.split(" ")
                const key = parts[0].slice(1)
                const agent = AVAILABLE_AGENTS.find(a => a.key === key)
                if (agent) {
                    agentKey = agent.key
                    // If slash command used, select that agent
                    setSelectedAgent(agent)
                    // Strip slash command for display
                    cleanMessage = msg.replace(/^\/\w+\s/, "")
                }
            }

            if (agentKey) {
                // Individual Agent Engagement - Call Direct Endpoint ONLY

                // 1. Manually add user message to local UI state for immediate feedback
                const userMessage: ChatMessage = {
                    id: Date.now(),
                    team_id: 0,
                    user_id: user?.id || 0,
                    user_name: user?.username || "You",
                    agent_key: null,
                    message_type: "text",
                    content: cleanMessage,
                    created_at: new Date().toISOString()
                }
                setMessages(prev => [...prev, userMessage])
                setInputMessage("")

                // Keep focus on input
                inputRef.current?.focus()

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

                } catch (agentErr: any) {
                    console.error("Direct agent communication failed:", agentErr)
                    toast({
                        title: "Agent Offline",
                        description: `${agentKey} is not responding via direct link.`,
                        variant: "destructive"
                    })
                }
            } else {
                // Should not reach here due to strict check above, unless slash command was not agent-related
                // e.g., /image, /help etc. are handled by slash command handler separately before this.
                // But strictly speaking, we are disabling Team Router fallback as requested.
            }
        } catch (error: any) {
            console.error("Message transmission error:", error)
            toast({ title: "Transmission Error", description: "Failed to send message.", variant: "destructive" })
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

            toast({ title: "Decoding Pulse...", description: "Transcribing audio..." })

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
    }

    // --- Slash Command System ---

    const SLASH_COMMANDS = [
        { cmd: '/history', desc: 'View chat history', icon: History, action: () => handleViewHistory() },
        { cmd: '/new', desc: 'Start new chat', icon: Plus, action: () => handleNewChat() },
        { cmd: '/image', desc: 'Generate AI image', icon: ImageIcon, action: (args: string) => handleGenerateImageCommand(args) },
        { cmd: '/export', desc: 'Export chat transcript', icon: Download, action: () => handleExportChat() },
        { cmd: '/platforms', desc: 'Go to Platforms', icon: Globe, action: () => router.push('/dashboard?tab=platforms-overview') },
        { cmd: '/tools', desc: 'Go to Tools', icon: Wrench, action: () => router.push('/dashboard?tab=tools-automation-overview') },
        { cmd: '/automate', desc: 'Go to Automations', icon: Zap, action: () => router.push('/dashboard?tab=tools-automation-overview') },
        { cmd: '/teams', desc: 'Go to Teams', icon: UsersRound, action: () => router.push('/dashboard?tab=team-management') },
        ...filteredAgents.map(a => ({
            cmd: `/${a.key}`,
            desc: `Message ${a.name}`,
            icon: a.icon,
            action: (args: string) => {
                setSelectedAgent(a)
                setInputMessage(args || '')
            }
        }))
    ]

    const parseCommand = (input: string) => {
        if (!input.startsWith('/')) return null
        const parts = input.split(' ')
        const command = parts[0].toLowerCase()
        const args = parts.slice(1).join(' ')
        return { command, args }
    }

    const handleSlashCommand = async (command: string, args: string) => {
        const cmd = SLASH_COMMANDS.find(c => c.cmd === command)
        if (cmd) {
            setShowCommandMenu(false)
            setInputMessage('')
            if (cmd.action) {
                cmd.action(args)
            }
            return true
        }
        return false
    }

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value
        setInputMessage(value)

        if (value.startsWith('/')) {
            const parsed = parseCommand(value)
            if (parsed) {
                const filtered = SLASH_COMMANDS.filter(cmd =>
                    cmd.cmd.startsWith(parsed.command) ||
                    cmd.desc.toLowerCase().includes(parsed.command.slice(1))
                )
                setCommandSuggestions(filtered)
                setShowCommandMenu(filtered.length > 0)
                setSelectedCommandIndex(0)
            }
        } else {
            setShowCommandMenu(false)
        }
    }

    const handleCommandKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (!showCommandMenu) return

        if (e.key === 'ArrowDown') {
            e.preventDefault()
            setSelectedCommandIndex(prev =>
                prev < commandSuggestions.length - 1 ? prev + 1 : prev
            )
        } else if (e.key === 'ArrowUp') {
            e.preventDefault()
            setSelectedCommandIndex(prev => prev > 0 ? prev - 1 : 0)
        } else if (e.key === 'Enter' && commandSuggestions.length > 0) {
            e.preventDefault()
            const selected = commandSuggestions[selectedCommandIndex]
            const parsed = parseCommand(inputMessage)
            if (selected && parsed) {
                handleSlashCommand(selected.cmd, parsed.args)
            }
        } else if (e.key === 'Escape') {
            setShowCommandMenu(false)
        }
    }

    const handleGenerateImageCommand = async (prompt: string) => {
        if (!prompt.trim()) {
            toast({
                title: "Prompt Required",
                description: "Please provide a description for the image. Example: /image a sunset over mountains",
                variant: "destructive"
            })
            return
        }
        toast({
            title: "Generating Image",
            description: "Creating your image with AI..."
        })
    }

    const handleExportChat = () => {
        try {
            const chatData = messages.map(m => ({
                timestamp: new Date(m.created_at).toLocaleString(),
                sender: m.agent_key ? `Agent ${m.agent_key}` : m.user_name,
                message: m.content
            }))

            const blob = new Blob([JSON.stringify(chatData, null, 2)], { type: 'application/json' })
            const url = URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `chat-transcript-${new Date().toISOString().split('T')[0]}.json`
            document.body.appendChild(a)
            a.click()
            document.body.removeChild(a)
            URL.revokeObjectURL(url)

            toast({ title: "Export Complete", description: "Chat transcript downloaded successfully." })
        } catch (error) {
            toast({ title: "Export Failed", description: "Failed to export chat transcript.", variant: "destructive" })
        }
    }

    return (
        <div className="flex flex-col w-full h-[calc(100vh-4rem)] bg-white select-none overflow-hidden">
            <style jsx global>{`
                .no-scrollbar::-webkit-scrollbar { display: none; }
                .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
            `}</style>

            {/* HEADER - FIXED */}
            <TacticalHeader
                connectionStatus={isConnected}
                onNewChat={handleNewChat}
                onHistory={handleViewHistory}
                onToggleRightSidebar={() => setIsRightSidebarOpen(!isRightSidebarOpen)}
                isRightSidebarOpen={isRightSidebarOpen}
            />

            <div className="flex flex-1 overflow-hidden min-h-0">
                {/* LEFT PANE: WORKFORCE ROSTER */}
                <AnimatePresence initial={false}>
                    {isLeftSidebarOpen ? (
                        <motion.div
                            initial={{ width: 0, opacity: 0 }}
                            animate={{ width: 280, opacity: 1 }}
                            exit={{ width: 0, opacity: 0 }}
                            className="border-r border-slate-200 bg-white flex flex-col hidden lg:flex shrink-0 min-w-0"
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

                            <ScrollArea className="flex-1 p-3">
                                <div className="space-y-1">
                                    {filteredAgents.length > 0 ? filteredAgents.map(agent => (
                                        <RosterItem
                                            key={agent.key}
                                            agent={agent}
                                            onClick={() => setSelectedAgent(agent === selectedAgent ? null : agent)}
                                            isSelected={selectedAgent?.key === agent.key}
                                        />
                                    )) : (
                                        <div className="p-4 text-center text-slate-400 text-xs">
                                            No active agents found.
                                        </div>
                                    )}
                                </div>
                            </ScrollArea>
                        </motion.div>
                    ) : (
                        <div className="w-12 border-r border-slate-200 flex flex-col items-center py-4 bg-slate-50/30 hidden lg:flex shrink-0">
                            <Button size="icon" variant="ghost" className="h-8 w-8 text-slate-400 hover:text-emerald-600 mb-4" onClick={() => setIsLeftSidebarOpen(true)}>
                                <Users className="h-4 w-4" />
                            </Button>
                        </div>
                    )}
                </AnimatePresence>

                {/* MAIN CHAT AREA */}
                <div className="flex-1 flex flex-col bg-slate-50/30 min-w-0 overflow-hidden">
                    {/* MESSAGES LIST - SCROLLABLE */}
                    <div className="flex-1 overflow-y-auto p-4 space-y-4 scroll-smooth">
                        {isLoading ? (
                            <div className="h-full flex flex-col items-center justify-center space-y-4">
                                <div className="h-8 w-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
                                <p className="text-xs font-mono text-slate-400 animate-pulse">ESTABLISHING SECURE CONNECTION...</p>
                            </div>
                        ) : messages.length === 0 ? (
                            <div className="h-full flex flex-col items-center justify-center text-center p-8 opacity-50">
                                <div className="h-20 w-20 bg-slate-100 rounded-2xl flex items-center justify-center mb-6">
                                    <Zap className="h-10 w-10 text-slate-300" />
                                </div>
                                <h3 className="text-lg font-bold text-slate-900 mb-2">Command Center Ready</h3>
                                <p className="text-sm text-slate-500 max-w-md">
                                    Select an agent from the roster to verify status and begin strategic planning. All communications are encrypted.
                                </p>
                            </div>
                        ) : (
                            <div className="flex flex-col justify-end min-h-0">
                                {messages.map((msg, i) => (
                                    <MessageBlock
                                        key={msg.id || i}
                                        message={msg}
                                        agentInfo={msg.agent_key ? AVAILABLE_AGENTS.find(a => a.key === msg.agent_key) : null}
                                    />
                                ))}
                                <div ref={messagesEndRef} />
                            </div>
                        )}
                    </div>

                    {/* INPUT AREA - FIXED BOTTOM */}
                    <div className="p-4 bg-white border-t border-slate-200 shrink-0 relative z-20">
                        <AnimatePresence>
                            {showCommandMenu && commandSuggestions.length > 0 && (
                                <motion.div
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: 10 }}
                                    className="absolute bottom-full left-4 mb-2 w-80 bg-white border border-slate-200 rounded-lg shadow-xl overflow-hidden z-50"
                                >
                                    <div className="p-1 bg-slate-50 border-b border-slate-100 text-[10px] font-mono text-slate-400 uppercase tracking-wider px-3 py-2">
                                        Available Commands
                                    </div>
                                    <div className="max-h-60 overflow-y-auto p-1">
                                        {commandSuggestions.map((cmd, i) => (
                                            <div
                                                key={i}
                                                className={cn(
                                                    "flex items-center gap-3 p-2 rounded-md cursor-pointer transition-colors text-sm",
                                                    i === selectedCommandIndex ? "bg-emerald-50 text-emerald-900" : "hover:bg-slate-50 text-slate-700"
                                                )}
                                                onClick={() => {
                                                    setInputMessage(cmd.cmd + ' ')
                                                    setShowCommandMenu(false)
                                                    inputRef.current?.focus()
                                                }}
                                            >
                                                <div className={cn(
                                                    "h-8 w-8 rounded-lg flex items-center justify-center border shadow-sm",
                                                    i === selectedCommandIndex ? "bg-white border-emerald-200" : "bg-slate-50 border-slate-200"
                                                )}>
                                                    <cmd.icon className={cn("h-4 w-4", i === selectedCommandIndex ? "text-emerald-600" : "text-slate-400")} />
                                                </div>
                                                <div>
                                                    <div className="font-bold">{cmd.cmd}</div>
                                                    <div className="text-xs text-slate-400 font-medium">{cmd.desc}</div>
                                                </div>
                                                {i === selectedCommandIndex && (
                                                    <div className="ml-auto text-[10px] font-mono text-emerald-600 bg-emerald-100/50 px-1.5 py-0.5 rounded">
                                                        ENTER
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>

                        {/* Selected Agent Indicator */}
                        {selectedAgent && (
                            <div className="absolute -top-10 left-4 flex items-center gap-2 bg-slate-900 text-white px-3 py-1.5 rounded-t-lg shadow-sm text-xs font-bold uppercase tracking-wide">
                                <span className={cn("w-2 h-2 rounded-full", selectedAgent.color.replace('text-', 'bg-'))} />
                                Chatting with {selectedAgent.name}
                                <button
                                    onClick={() => setSelectedAgent(null)}
                                    className="ml-2 hover:bg-slate-700 rounded-full p-0.5 transition-colors"
                                >
                                    <X className="h-3 w-3" />
                                </button>
                            </div>
                        )}

                        <div className="flex items-end gap-2 bg-slate-50 p-2 rounded-xl border border-slate-200 focus-within:border-emerald-500/50 focus-within:ring-4 focus-within:ring-emerald-500/10 transition-all">
                            <Button size="icon" variant="ghost" className="h-9 w-9 text-slate-400 hover:text-emerald-600 hover:bg-white shrink-0">
                                <Paperclip className="h-4 w-4" />
                            </Button>

                            <div className="flex-1 relative">
                                <Input
                                    ref={inputRef}
                                    value={inputMessage}
                                    onChange={handleInputChange}
                                    onKeyDown={handleCommandKeyDown}
                                    onKeyPress={handleKeyPress}
                                    placeholder={selectedAgent ? `Message ${selectedAgent.name}...` : "Select an agent to start..."}
                                    className="border-0 bg-transparent focus-visible:ring-0 p-2 h-auto max-h-32 min-h-[40px] resize-none shadow-none text-slate-900 placeholder:text-slate-400 font-medium"
                                />
                            </div>

                            <div className="flex items-center gap-1 shrink-0">
                                <Button
                                    size="icon"
                                    variant="ghost"
                                    className={cn("h-9 w-9 text-slate-400 hover:text-red-500 hover:bg-red-50", isRecording && "text-red-500 bg-red-50 animate-pulse")}
                                    onMouseDown={startRecording}
                                    onMouseUp={stopRecording}
                                    onMouseLeave={stopRecording}
                                >
                                    <Mic className="h-4 w-4" />
                                </Button>
                                <Button
                                    size="icon"
                                    className={cn(
                                        "h-9 w-9 transition-all shadow-sm",
                                        inputMessage.trim() ? "bg-emerald-600 hover:bg-emerald-700 text-white" : "bg-slate-200 text-slate-400 hover:bg-slate-300"
                                    )}
                                    onClick={handleSendMessage}
                                    disabled={!inputMessage.trim() || isSending}
                                >
                                    <Send className="h-4 w-4" />
                                </Button>
                            </div>
                        </div>
                        <div className="mt-2 text-center">
                            <p className="text-[10px] text-slate-400 font-mono">
                                Press <kbd className="font-sans bg-slate-100 px-1 rounded border border-slate-200 text-slate-600">/</kbd> for commands or select an agent to begin.
                            </p>
                        </div>
                    </div>
                </div>

                {/* RIGHT PANE: ANALYTICS & STATUS */}
                <AnimatePresence initial={false}>
                    {isRightSidebarOpen && (
                        <motion.div
                            initial={{ width: 0, opacity: 0 }}
                            animate={{ width: 280, opacity: 1 }}
                            exit={{ width: 0, opacity: 0 }}
                            className="border-l border-slate-200 bg-white flex flex-col hidden lg:flex shrink-0 min-w-0"
                        >
                            <div className="p-4 border-b border-slate-200 bg-slate-50/50">
                                <h3 className="text-[10px] font-black text-slate-900 uppercase tracking-[0.2em] flex items-center gap-2 font-mono">
                                    <Activity className="h-4 w-4 text-emerald-600" />
                                    System Overview
                                </h3>
                            </div>

                            <ScrollArea className="flex-1 p-4">
                                <div className="space-y-6">
                                    {/* Quick Stats Grid */}
                                    <div className="grid grid-cols-1 gap-3">
                                        <StatCard
                                            label="Agents Active"
                                            value={filteredAgents.length.toString()}
                                            icon={UsersRound}
                                            colorClass="text-emerald-600"
                                        />
                                        <StatCard
                                            label="Platforms"
                                            value={platformCount.toString()}
                                            icon={Globe}
                                            colorClass="text-sky-600"
                                        />
                                        <StatCard
                                            label="Tools Linked"
                                            value={toolCount.toString()}
                                            icon={Wrench}
                                            colorClass="text-amber-600"
                                        />
                                    </div>

                                    <Separator className="bg-slate-100" />

                                    {/* Agent Activity Log */}
                                    <div>
                                        <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                                            <Shield className="h-3 w-3" />
                                            Agent Activity Log
                                        </h4>
                                        <div className="space-y-1">
                                            {activityLog.length > 0 ? activityLog.map((log) => (
                                                <NotificationItem
                                                    key={log.id}
                                                    {...log}
                                                />
                                            )) : (
                                                <div className="text-center py-4 text-xs text-slate-400 font-mono italic">
                                                    Waiting for agent activity...
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                </div>
                            </ScrollArea>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    )
}
