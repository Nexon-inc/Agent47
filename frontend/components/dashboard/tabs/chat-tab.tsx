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
    Lightbulb
} from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
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

const TacticalHeader = ({ connectionStatus }: { connectionStatus: boolean }) => (
    <div className="flex items-center justify-between px-6 py-3 border-b border-slate-200 bg-white/95 backdrop-blur-sm sticky top-0 z-50">
        <div className="flex items-center space-x-3">
            <div className="h-8 w-8 bg-slate-100 rounded-lg border border-slate-200 flex items-center justify-center">
                <Radio className={`h-4 w-4 ${connectionStatus ? "text-emerald-600 animate-pulse" : "text-slate-400"}`} />
            </div>
            <div>
                <h1 className="text-sm font-black text-slate-900 uppercase tracking-widest leading-none">Strategy Room</h1>
                <p className="text-[10px] items-center mt-1 font-mono text-emerald-600 font-medium flex gap-2">
                    <span className={`inline-block w-2 h-2 rounded-full ${connectionStatus ? "bg-emerald-500 animate-ping" : "bg-red-500"}`} />
                    {connectionStatus ? "SECURE CHANNEL ACTIVE" : "CONNECTION LOST"}
                </p>
            </div>
        </div>
        <div className="flex items-center space-x-3">
            <Badge variant="outline" className="font-mono text-[10px] text-slate-500 border-slate-200 bg-slate-50">
                ENC: AES-256
            </Badge>
            <Badge variant="outline" className="font-mono text-[10px] text-slate-500 border-slate-200 bg-slate-50">
                LAT: 12ms
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
    const [isSidebarOpen, setIsSidebarOpen] = useState(true)

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
            await apiClient.updateIntercommunicationSetting(enabled)
            toast({
                title: enabled ? "Intercom Activated" : "Intercom Deactivated",
                description: enabled ? "Agents can now communicate with each other." : "Agents operating in silos.",
            })
        } catch (e) {
            setIntercomEnabled(!enabled) // Revert
            toast({
                title: "Update Failed",
                description: "Could not update intercommunication setting.",
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

    return (
        <div className="flex h-[calc(100vh-6rem)] bg-slate-50/50 overflow-hidden font-sans">

            {/* LEFT PANE: ROSTER */}
            <div className="w-64 border-r border-slate-200 bg-white flex flex-col hidden md:flex">
                <div className="p-4 border-b border-slate-100">
                    <h2 className="text-xs font-black text-slate-400 uppercase tracking-widest mb-3">Personnel Roster</h2>
                    <div className="relative">
                        <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-400" />
                        <Input className="h-8 pl-8 text-xs bg-slate-50 border-slate-200" placeholder="Filter agents..." />
                    </div>
                </div>
                <ScrollArea className="flex-1 p-3">
                    <div className="space-y-1">
                        {AVAILABLE_AGENTS.map(agent => (
                            <RosterItem
                                key={agent.key}
                                agent={agent}
                                onClick={() => {
                                    setInputMessage(`/${agent.key} `)
                                    inputRef.current?.focus()
                                }}
                            />
                        ))}
                    </div>
                </ScrollArea>
                <div className="p-4 border-t border-slate-100 bg-slate-50/50">
                    <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono">
                        <span>ONLINE: 7/7</span>
                        <span>CPU: 12%</span>
                    </div>
                </div>
            </div>

            {/* CENTER PANE: EXECUTION FLOOR */}
            <div className="flex-1 flex flex-col min-w-0 bg-white relative">
                <TacticalHeader connectionStatus={isConnected} />

                <div className="flex-1 overflow-y-auto px-4 py-4" id="messages-container">
                    <div className="max-w-3xl mx-auto space-y-6">
                        <div className="flex items-center justify-center my-8">
                            <span className="text-[10px] font-mono text-slate-300 uppercase tracking-widest">--- MISSION START ---</span>
                        </div>
                        {messages.map(msg => (
                            <MessageBlock key={msg.id} message={msg} agentInfo={AVAILABLE_AGENTS.find(a => a.key === msg.agent_key)} />
                        ))}
                        <div ref={messagesEndRef} />
                    </div>
                </div>

                {/* INPUT AREA */}
                <div className="p-4 border-t border-slate-200 bg-white/80 backdrop-blur-md">
                    <div className="max-w-3xl mx-auto flex items-end gap-3">
                        <div className="flex-1 bg-slate-50 border border-slate-200 rounded-xl p-2 focus-within:ring-2 focus-within:ring-emerald-500/20 focus-within:border-emerald-500 transition-all shadow-inner">
                            <Input
                                ref={inputRef}
                                className="border-0 bg-transparent shadow-none focus-visible:ring-0 text-slate-900 placeholder:text-slate-400 h-10"
                                placeholder="Transmit command..."
                                value={inputMessage}
                                onChange={e => setInputMessage(e.target.value)}
                                onKeyDown={handleKeyPress}
                            />
                            <div className="flex items-center justify-between px-2 pt-2 border-t border-slate-200/50 mt-1">
                                <div className="flex gap-1">
                                    <Button size="icon" variant="ghost" className="h-6 w-6 text-slate-400 hover:text-emerald-600"><Paperclip className="h-3.5 w-3.5" /></Button>
                                    <Button size="icon" variant="ghost" className="h-6 w-6 text-slate-400 hover:text-emerald-600"><Mic className="h-3.5 w-3.5" /></Button>
                                </div>
                                <span className="text-[10px] font-mono text-slate-300">SECURE // ENCRYPTED</span>
                            </div>
                        </div>
                        <Button
                            className="h-12 w-12 rounded-xl bg-slate-900 hover:bg-emerald-600 text-white shadow-lg transition-colors"
                            onClick={handleSendMessage}
                            disabled={isSending}
                        >
                            <Send className="h-5 w-5" />
                        </Button>
                    </div>
                </div>
            </div>

            {/* RIGHT PANE: COMMAND SIDEBAR */}
            <AnimatePresence initial={false}>
                {isSidebarOpen ? (
                    <motion.div
                        initial={{ width: 0, opacity: 0 }}
                        animate={{ width: 288, opacity: 1 }}
                        exit={{ width: 0, opacity: 0 }}
                        className="border-l border-slate-200 bg-slate-50 flex flex-col hidden xl:flex overflow-hidden"
                    >
                        <div className="p-4 border-b border-slate-200 flex justify-between items-center">
                            <h3 className="text-xs font-black text-slate-900 uppercase tracking-widest flex items-center gap-2">
                                <Activity className="h-4 w-4 text-emerald-600" />
                                Operations
                            </h3>
                            <Button size="icon" variant="ghost" className="h-6 w-6" onClick={() => setIsSidebarOpen(false)}>
                                <ChevronRight className="h-4 w-4 text-slate-400" />
                            </Button>
                        </div>
                        <div className="flex-1 p-4 space-y-4 overflow-y-auto">
                            {/* Intercom Toggle */}
                            <div className="bg-white rounded-xl p-3 border border-slate-200 shadow-sm space-y-3">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <Users className="h-4 w-4 text-indigo-500" />
                                        <span className="text-xs font-bold text-slate-700">Collaboration Mode</span>
                                    </div>
                                    <Switch checked={intercomEnabled} onCheckedChange={toggleIntercom} />
                                </div>
                                <p className="text-[10px] text-slate-500 leading-tight">
                                    When active, agents can communicate with each other to solve complex tasks.
                                </p>
                            </div>

                            {/* Upgrade CTA */}
                            <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl p-4 text-white shadow-md">
                                <div className="flex items-center gap-2 mb-2">
                                    <TrendingUp className="h-4 w-4 text-emerald-400" />
                                    <span className="text-xs font-bold">Scale Your Force</span>
                                </div>
                                <p className="text-[10px] text-slate-300 mb-3">Unlock advanced neural capabilities and unlimited agents.</p>
                                <Button
                                    size="sm"
                                    className="w-full bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-bold"
                                    onClick={() => router.push('/dashboard?tab=upgrade')}
                                >
                                    Upgrade Plan
                                </Button>
                            </div>

                            {/* Tactical Actions */}
                            <div>
                                <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3 mt-4">Tactical Actions</h3>
                                <div className="grid grid-cols-2 gap-2">
                                    <Button variant="outline" size="sm" className="h-20 flex flex-col gap-2 border-slate-200 hover:border-emerald-500 hover:bg-emerald-50 bg-white">
                                        <Zap className="h-5 w-5 text-amber-500" />
                                        <span className="text-[10px] font-bold">Fast Track</span>
                                    </Button>
                                    <Button variant="outline" size="sm" className="h-20 flex flex-col gap-2 border-slate-200 hover:border-red-500 hover:bg-red-50 bg-white">
                                        <Shield className="h-5 w-5 text-red-500" />
                                        <span className="text-[10px] font-bold">Lockdown</span>
                                    </Button>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                ) : (
                    <div className="w-12 border-l border-slate-200 bg-slate-50 flex flex-col items-center py-4 hidden xl:flex">
                        <Button size="icon" variant="ghost" onClick={() => setIsSidebarOpen(true)}>
                            <ChevronLeft className="h-4 w-4 text-slate-400" />
                        </Button>
                    </div>
                )}
            </AnimatePresence>

        </div>
    )
}
