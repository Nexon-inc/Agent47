"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import {
  BarChart3,
  Send,
  Mic,
  Paperclip,
  Smile,
  Loader2,
  Bot,
  User,
  CheckCircle,
  Clock,
  AlertCircle,
  Hash,
  Users,
  MessageSquare,
  Sparkles,
  Lock,
  Crown,
  Trophy,
  Target,
  Zap,
} from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { apiClient } from "@/lib/api-client"
import { useAuthStore } from "@/lib/stores/auth-store"
import { useToast } from "@/hooks/use-toast"
import { cn } from "@/lib/utils"
import { websocketService } from "@/lib/websocket-service"

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
  description: string
  icon: string
  color: string
}

const AVAILABLE_AGENTS: Agent[] = [
  {
    key: "aria",
    name: "Aria",
    description: "PR & Communications Director",
    icon: "📱",
    color: "text-blue-500",
  },
  {
    key: "clara",
    name: "Clara",
    description: "Customer Success Lead",
    icon: "🤝",
    color: "text-green-500",
  },
  {
    key: "eric",
    name: "Eric",
    description: "Senior Sales Representative",
    icon: "💼",
    color: "text-red-500",
  },
  {
    key: "jackie",
    name: "Jackie",
    description: "Growth Marketing Manager",
    icon: "🚀",
    color: "text-orange-500",
  },
  {
    key: "purity",
    name: "Purity",
    description: "Operations Strategist",
    icon: "🧠",
    color: "text-indigo-500",
  },
  {
    key: "shakes",
    name: "Shakes",
    description: "Lead Creative Designer",
    icon: "✍️",
    color: "text-purple-500",
  },
]

export default function TeamChatTab() {
  const { user } = useAuthStore()
  const { toast } = useToast()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputMessage, setInputMessage] = useState("")
  const [isLoading, setIsLoading] = useState(true)
  const [isSending, setIsSending] = useState(false)
  const [showAgentAutocomplete, setShowAgentAutocomplete] = useState(false)
  const [autocompleteQuery, setAutocompleteQuery] = useState("")
  const [selectedAgentIndex, setSelectedAgentIndex] = useState(0)
  const [isRecording, setIsRecording] = useState(false)
  const [hasTeam, setHasTeam] = useState(true)
  const [isCoordinatorActive, setIsCoordinatorActive] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const unsubscribeRef = useRef<(() => void) | null>(null)

  // Scroll to bottom when messages change
  useEffect(() => {
    if (messages.length > 0) {
      // Use requestAnimationFrame to ensure the DOM has updated before scrolling
      requestAnimationFrame(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
      })
    }
  }, [messages])

  // Load initial messages and setup WebSocket
  useEffect(() => {
    loadMessages()

    // Subscribe to team chat messages via WebSocket
    const unsubscribe = websocketService.subscribe('team_chat_message', (message: any) => {
      // Reload messages when new team chat message is received
      setTimeout(loadMessages, 300) // Small delay to ensure DB is updated

      // If it's a coordinator message, show activity
      if (message.agent_key === 'system') {
        setIsCoordinatorActive(true)
        setTimeout(() => setIsCoordinatorActive(false), 5000)
      }
    })

    unsubscribeRef.current = unsubscribe

    // Ensure WebSocket is connected
    if (!websocketService.getConnectionStatus()) {
      websocketService.connect()
    }

    return () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current()
      }
    }
  }, [])

  // Handle slash command detection
  useEffect(() => {
    if (inputMessage.startsWith("/")) {
      const query = inputMessage.slice(1).toLowerCase()
      setAutocompleteQuery(query)
      setShowAgentAutocomplete(true)

      // Filter agents based on query
      const filtered = AVAILABLE_AGENTS.filter(
        (agent) =>
          agent.key.toLowerCase().startsWith(query) ||
          agent.name.toLowerCase().startsWith(query)
      )

      if (filtered.length === 0) {
        setShowAgentAutocomplete(false)
      } else {
        setSelectedAgentIndex(0)
      }
    } else {
      setShowAgentAutocomplete(false)
    }
  }, [inputMessage])

  const loadMessages = async () => {
    try {
      setIsLoading(true)
      const response = await apiClient.get("/api/v1/team/chat/messages?limit=100").catch((error: any) => {
        // Check if it's a 403 (no team access) or 404 (no team)
        if (error?.response?.status === 403 || error?.response?.status === 404) {
          setHasTeam(false)
          return { data: { messages: [] } }
        }
        return { data: { messages: [] } }
      })
      if (response.data?.messages) {
        setMessages(response.data.messages.reverse()) // Reverse to show oldest first
        setHasTeam(true)
      } else {
        setMessages([])
      }
    } catch (error: any) {
      console.error("Failed to load messages:", error)
      if (error?.response?.status === 403 || error?.response?.status === 404) {
        setHasTeam(false)
      }
      setMessages([])
    } finally {
      setIsLoading(false)
    }
  }


  const parseSlashCommand = (message: string): { agentKey: string | null; content: string } | null => {
    if (!message.startsWith("/")) return null

    const parts = message.trim().split(/\s+/)
    const command = parts[0].slice(1).toLowerCase() // Remove '/'
    const content = parts.slice(1).join(" ")

    // Find matching agent
    const agent = AVAILABLE_AGENTS.find(
      (a) => a.key.toLowerCase() === command || a.name.toLowerCase() === command
    )

    if (agent) {
      return { agentKey: agent.key, content }
    }

    return null
  }

  const handleSendMessage = async () => {
    if (!inputMessage.trim() && !isSending) return

    try {
      setIsSending(true)

      // Check if it's a slash command
      const command = parseSlashCommand(inputMessage)

      if (command && command.agentKey) {
        // Send agent request
        await apiClient.post("/api/v1/team/agent-requests/create", {
          agent_key: command.agentKey,
          request_type: "chat",
          request_data: {
            message: command.content || "Hello",
            context: {},
          },
        })

        // Also send a user message showing what was requested
        await apiClient.post("/api/v1/team/chat/message", {
          content: inputMessage,
          message_type: "text",
          agent_key: command.agentKey,
        })

        toast({
          title: "Agent Requested",
          description: `${AVAILABLE_AGENTS.find((a) => a.key === command.agentKey)?.name} is processing your request...`,
        })
      } else {
        // Regular message
        await apiClient.post("/api/v1/team/chat/message", {
          content: inputMessage,
          message_type: "text",
        })
      }

      setInputMessage("")
      setShowAgentAutocomplete(false)

      // Reload messages to show new one
      setTimeout(loadMessages, 500)
    } catch (error: any) {
      console.error("Failed to send message:", error)
      toast({
        title: "Error",
        description: error?.response?.data?.detail || "Failed to send message",
        variant: "destructive",
      })
    } finally {
      setIsSending(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      if (showAgentAutocomplete && e.key === "Enter") {
        // Select agent from autocomplete
        const filtered = AVAILABLE_AGENTS.filter(
          (agent) =>
            agent.key.toLowerCase().startsWith(autocompleteQuery) ||
            agent.name.toLowerCase().startsWith(autocompleteQuery)
        )
        if (filtered.length > 0) {
          const selected = filtered[selectedAgentIndex]
          setInputMessage(`/${selected.key} `)
          setShowAgentAutocomplete(false)
          inputRef.current?.focus()
        }
      } else {
        handleSendMessage()
      }
    } else if (e.key === "ArrowDown" && showAgentAutocomplete) {
      e.preventDefault()
      const filtered = AVAILABLE_AGENTS.filter(
        (agent) =>
          agent.key.toLowerCase().startsWith(autocompleteQuery) ||
          agent.name.toLowerCase().startsWith(autocompleteQuery)
      )
      setSelectedAgentIndex((prev) => Math.min(prev + 1, filtered.length - 1))
    } else if (e.key === "ArrowUp" && showAgentAutocomplete) {
      e.preventDefault()
      setSelectedAgentIndex((prev) => Math.max(prev - 1, 0))
    } else if (e.key === "Escape") {
      setShowAgentAutocomplete(false)
    }
  }

  const handleAgentSelect = (agent: Agent) => {
    setInputMessage(`/${agent.key} `)
    setShowAgentAutocomplete(false)
    inputRef.current?.focus()
  }

  const getAgentInfo = (agentKey: string | null | undefined): Agent | null => {
    if (!agentKey) return null
    return AVAILABLE_AGENTS.find((a) => a.key === agentKey) || null
  }

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / 60000)

    if (minutes < 1) return "just now"
    if (minutes < 60) return `${minutes}m ago`
    if (date.toDateString() === now.toDateString()) {
      return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    }
    return date.toLocaleDateString([], { month: "short", day: "numeric" })
  }


  const filteredAgents = AVAILABLE_AGENTS.filter(
    (agent) =>
      agent.key.toLowerCase().startsWith(autocompleteQuery) ||
      agent.name.toLowerCase().startsWith(autocompleteQuery)
  )

  if (!hasTeam && !isLoading) {
    return (
      <div className="flex flex-col h-full bg-white text-slate-900 items-center justify-center p-8">
        <Users className="h-16 w-16 text-slate-200 mb-4" />
        <h3 className="text-xl font-semibold text-slate-900 mb-2">No Team Found</h3>
        <p className="text-slate-500 text-center max-w-md mb-6">
          You need to create or join a team to use team chat. Go to the Members tab to invite team members.
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col min-h-[calc(100vh-8rem)] bg-white text-slate-900 font-sans selection:bg-indigo-500/30 relative">
      {/* Header - Fixed Sticky behavior */}
      <div className="flex flex-col border-b border-slate-200 bg-white/95 backdrop-blur-xl sticky top-0 z-50 -mx-4 md:-mx-6 shadow-sm">
        <div className="flex items-center justify-between px-6 py-4">
          <div className="flex items-center space-x-2">
            <Hash className="h-5 w-5 text-slate-400" />
            <h2 className="text-lg font-black text-slate-900 uppercase tracking-tight">Strategy Room</h2>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 bg-slate-100 px-3 py-1 rounded-full border border-slate-200">
              <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Secure Line</span>
            </div>
          </div>
        </div>

        {/* Employee Activity Bar */}
        <div className="px-6 py-3 border-t border-slate-100 flex items-center space-x-6 overflow-x-auto no-scrollbar scroll-smooth">
          {AVAILABLE_AGENTS.map((agent) => (
            <button
              key={agent.key}
              onClick={() => handleAgentSelect(agent)}
              className="flex items-center space-x-2 group shrink-0 transition-opacity hover:opacity-100 opacity-80"
            >
              <div className={cn(
                "h-8 w-8 rounded-lg flex items-center justify-center border transition-all text-sm",
                agent.color.replace("text-", "border-").replace("-500", "-200"),
                agent.color.replace("text-", "bg-").replace("-500", "-50/50"),
                "group-hover:scale-110 group-hover:shadow-sm"
              )}>
                {agent.icon}
              </div>
              <div className="flex flex-col items-start leading-none">
                <span className="text-[10px] font-black text-slate-900 uppercase tracking-tight">{agent.name}</span>
                <div className="flex items-center space-x-1 mt-0.5">
                  <div className={cn("h-1 w-1 rounded-full", isCoordinatorActive ? "bg-green-500 animate-pulse" : "bg-slate-300")} />
                  <span className="text-[8px] font-bold text-slate-400 uppercase tracking-tighter">
                    {isCoordinatorActive ? "Synthesizing" : "Ready"}
                  </span>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-8">
        <div className="max-w-4xl mx-auto space-y-8">
          {isLoading ? (
            <div className="flex items-center justify-center h-48">
              <Loader2 className="h-6 w-6 animate-spin text-slate-300" />
            </div>
          ) : messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center min-h-[400px] text-center bg-slate-50/50 rounded-[40px] border border-dashed border-slate-200">
              <div className="w-16 h-16 bg-white rounded-2xl flex items-center justify-center shadow-sm mb-6">
                <MessageSquare className="h-8 w-8 text-slate-200" />
              </div>
              <h3 className="text-xl font-black text-slate-900 mb-2 uppercase tracking-tight">Strategy Room Initialized</h3>
              <p className="text-sm text-slate-500 mb-8 max-w-sm mx-auto leading-relaxed font-medium">
                The secure line is open. Brief your workforce or select an employee below to begin the mission.
              </p>
              <div className="flex flex-wrap gap-3 justify-center">
                {AVAILABLE_AGENTS.map((agent) => (
                  <Button
                    key={agent.key}
                    variant="outline"
                    onClick={() => handleAgentSelect(agent)}
                    className="h-12 bg-white border-slate-200 text-slate-900 hover:bg-slate-50 rounded-xl font-black uppercase tracking-tight text-[10px] px-5 group"
                  >
                    <span className="mr-2 text-base group-hover:scale-125 transition-transform">{agent.icon}</span>
                    Call {agent.name}
                  </Button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((message, index) => {
              const isAgent = !!message.agent_key
              const agentInfo = getAgentInfo(message.agent_key)
              const isUser = message.user_id === user?.id && !isAgent
              const isSameAuthor = index > 0 &&
                (isAgent ? messages[index - 1].agent_key === message.agent_key : messages[index - 1].user_id === message.user_id) &&
                !messages[index - 1].agent_key === !message.agent_key

              return (
                <div
                  key={message.id}
                  className={cn(
                    "flex w-full mb-6 animate-in fade-in slide-in-from-bottom-2 duration-300",
                    isUser ? "justify-end" : "justify-start"
                  )}
                >
                  <div className={cn(
                    "flex items-start max-w-[85%] sm:max-w-[75%] space-x-3",
                    isUser && "flex-row-reverse space-x-reverse"
                  )}>
                    {/* Avatar */}
                    <div className="flex-shrink-0 mt-1">
                      {isAgent ? (
                        <div className={cn(
                          "h-9 w-9 rounded-xl flex items-center justify-center border border-slate-200 shadow-sm bg-white",
                          agentInfo?.color.replace("text-", "bg-").replace("-500", "-50")
                        )}>
                          <span className="text-xl">{agentInfo?.icon}</span>
                        </div>
                      ) : (
                        <Avatar className="h-9 w-9 rounded-xl border border-slate-200 shadow-sm">
                          <AvatarImage src={message.avatar_url} />
                          <AvatarFallback className="bg-indigo-600 text-white font-bold text-xs">
                            {message.user_name.charAt(0).toUpperCase()}
                          </AvatarFallback>
                        </Avatar>
                      )}
                    </div>

                    {/* Bubble & Content */}
                    <div className={cn(
                      "flex flex-col",
                      isUser ? "items-end" : "items-start"
                    )}>
                      {!isSameAuthor && (
                        <div className="flex items-center space-x-2 mb-1.5 px-1">
                          <span className={cn(
                            "text-sm font-semibold tracking-tight",
                            isAgent ? "text-slate-900" : "text-slate-600"
                          )}>
                            {isAgent ? agentInfo?.name : message.user_name}
                          </span>
                          {isAgent && (
                            <div className="flex items-center space-x-1 bg-slate-50 border border-slate-200 px-1.5 py-0.5 rounded-md">
                              <Bot className="h-3 w-3 text-indigo-600" />
                              <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Assistant</span>
                            </div>
                          )}
                          <span className="text-[10px] text-slate-400 font-medium">{formatTime(message.created_at)}</span>
                        </div>
                      )}

                      <div className={cn(
                        "px-5 py-4 rounded-[24px] text-[15px] leading-relaxed relative overflow-hidden group/bubble transition-all",
                        isUser
                          ? "bg-slate-50 text-slate-900 border border-slate-200/50 rounded-tr-none shadow-sm"
                          : cn(
                            "bg-white border-2 rounded-tl-none shadow-md",
                            agentInfo?.color.replace("text-", "border-").replace("-500", "-100")
                          )
                      )}>
                        {/* Agent Decorative Background Gradient */}
                        {isAgent && (
                          <div className={cn(
                            "absolute top-0 right-0 w-32 h-32 opacity-[0.03] pointer-events-none -mr-16 -mt-16 rounded-full blur-3xl",
                            agentInfo?.color.replace("text-", "bg-")
                          )} />
                        )}

                        <div className="whitespace-pre-wrap break-words relative z-10">
                          {message.content.split('\n').map((line: string, idx: number) => {
                            // Specialized Rich Card Rendering for specific line starts
                            if (line.trim().startsWith('📊') || line.trim().startsWith('📈')) {
                              return (
                                <div key={idx} className="my-4 p-4 bg-slate-50 rounded-2xl border border-slate-100 flex items-center space-x-4 shadow-inner">
                                  <div className={cn("p-3 rounded-xl", agentInfo?.color.replace("text-", "bg-").replace("-500", "-100"))}>
                                    <BarChart3 className={cn("h-5 w-5", agentInfo?.color)} />
                                  </div>
                                  <div>
                                    <h4 className="text-xs font-black text-slate-900 uppercase tracking-widest leading-none mb-1">Impact Metric</h4>
                                    <p className="text-lg font-black text-slate-800 tracking-tight">{line.replace(/^[📊📈]\s*/, '')}</p>
                                  </div>
                                </div>
                              )
                            }

                            if (line.trim().startsWith('🚀') || line.trim().startsWith('⚡')) {
                              return (
                                <div key={idx} className={cn(
                                  "my-4 p-4 rounded-2xl border-2 flex flex-col space-y-2 shadow-sm",
                                  agentInfo?.color.replace("text-", "border-").replace("-500", "-200"),
                                  agentInfo?.color.replace("text-", "bg-").replace("-500", "-50/30")
                                )}>
                                  <div className="flex items-center space-x-2">
                                    <Zap className={cn("h-4 w-4", agentInfo?.color)} />
                                    <h4 className="text-[10px] font-black text-slate-900 uppercase tracking-widest">Recommended Action</h4>
                                  </div>
                                  <p className="font-bold text-slate-800 leading-tight">{line.replace(/^[🚀⚡]\s*/, '')}</p>
                                  <Button size="sm" className={cn("mt-2 h-8 rounded-lg font-black uppercase tracking-tighter text-[10px] w-fit", agentInfo?.color.replace("text-", "bg-"))}>
                                    Execute Now
                                  </Button>
                                </div>
                              )
                            }

                            // Standard Line Formatting
                            if (line.trim().startsWith('📅') || line.trim().startsWith('📝') || line.trim().startsWith('✅') || line.trim().startsWith('✨')) {
                              return (
                                <div key={idx} className="mt-4 first:mt-0 mb-2">
                                  <span className="font-black text-slate-900 flex items-center gap-2 uppercase text-xs tracking-tight bg-slate-50 w-fit px-2 py-1 rounded-md border border-slate-100">
                                    {line}
                                  </span>
                                </div>
                              )
                            } else if (line.trim().startsWith('•') || line.trim().startsWith('-')) {
                              return (
                                <div key={idx} className="flex items-start gap-3 mt-2 ml-1">
                                  <div className={cn("w-1.5 h-1.5 rounded-full mt-2 shrink-0", agentInfo ? agentInfo.color.replace("text-", "bg-") : "bg-indigo-500")} />
                                  <span className="text-slate-700 font-medium">{line.replace(/^[•-]\s*/, '')}</span>
                                </div>
                              )
                            } else if (line.trim().match(/^\d+\./)) {
                              return (
                                <div key={idx} className="flex items-start gap-3 mt-2 ml-1">
                                  <span className={cn("font-black shrink-0 text-sm", agentInfo?.color)}>{line.match(/^\d+\./)?.[0]}</span>
                                  <span className="text-slate-700 font-medium">{line.replace(/^\d+\.\s*/, '')}</span>
                                </div>
                              )
                            } else if (line.trim() === '') {
                              return <div key={idx} className="h-3" />
                            }
                            return <div key={idx} className={cn(idx === 0 ? '' : 'mt-1.5', isAgent ? "font-medium text-slate-700" : "text-slate-800")}>{line}</div>
                          })}
                        </div>

                        {/* Thinking Steps Rendering */}
                        {isAgent && message.thinking_steps && (
                          <div className="mt-6 pt-4 border-t border-slate-100 space-y-2 relative z-10">
                            <div className="flex items-center gap-2 text-[10px] uppercase font-black text-slate-400 tracking-widest mb-3">
                              <Sparkles className={cn("h-3 w-3", agentInfo?.color)} />
                              Strategic Calculation
                            </div>
                            <div className="space-y-1.5">
                              {message.thinking_steps.map((step: string, sIdx: number) => (
                                <motion.div
                                  key={sIdx}
                                  initial={{ opacity: 0, x: -5 }}
                                  animate={{ opacity: 1, x: 0 }}
                                  transition={{ delay: sIdx * 0.1 }}
                                  className="flex items-center gap-2.5 text-[11px] text-slate-500 font-bold uppercase tracking-tight"
                                >
                                  <div className={cn("h-1 w-1 rounded-full", agentInfo?.color.replace("text-", "bg-"))} />
                                  <span>{step}</span>
                                </motion.div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* File Attachments */}
                        {message.file_url && (
                          <div className="mt-3">
                            {message.file_url.match(/\.(jpg|jpeg|png|gif|webp|svg)$/i) ||
                              message.file_url.includes('storage') ||
                              message.file_url.includes('supabase') ? (
                              <div className="rounded-xl overflow-hidden border border-slate-200 max-w-md shadow-lg">
                                <img
                                  src={message.file_url}
                                  alt="Attached image"
                                  className="w-full h-auto transition-transform hover:scale-[1.02]"
                                />
                              </div>
                            ) : (
                              <a
                                href={message.file_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center space-x-2 px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-indigo-600 hover:text-indigo-700 hover:bg-slate-100 transition-all"
                              >
                                <Paperclip className="h-4 w-4" />
                                <span className="text-sm font-medium">{message.file_name || "Attachment"}</span>
                              </a>
                            )}
                          </div>
                        )}

                        {message.audio_url && (
                          <div className="mt-3 bg-slate-50 p-2 rounded-xl border border-slate-200 shadow-inner">
                            <audio controls className="h-8 max-w-full">
                              <source src={message.audio_url} />
                            </audio>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )
            })
          )}
        </div>
        <div ref={messagesEndRef} className="h-24" />
      </div>

      {/* Floating Sticky Input Area */}
      <div className="sticky bottom-4 md:bottom-6 z-50 pb-8 pt-4 -mx-4 md:-mx-6 px-4 pointer-events-none">
        <div className="max-w-3xl mx-auto">
          {/* Agent Autocomplete */}
          {showAgentAutocomplete && filteredAgents.length > 0 && (
            <div className="mb-4 bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-2xl animate-in fade-in slide-in-from-bottom-2 duration-300">
              {filteredAgents.map((agent, index) => (
                <button
                  key={agent.key}
                  onClick={() => handleAgentSelect(agent)}
                  className={cn(
                    "w-full flex items-center space-x-3 px-5 py-3 text-left hover:bg-slate-50 transition-colors",
                    index === selectedAgentIndex && "bg-slate-50"
                  )}
                >
                  <div className={cn("text-2xl", agent.color)}>{agent.icon}</div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-slate-900">{agent.name}</span>
                      <div className="bg-slate-100 border border-slate-200 text-slate-500 text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-md font-bold">
                        Agent
                      </div>
                    </div>
                    <p className="text-xs text-slate-500">{agent.description}</p>
                  </div>
                  <span className="text-xs font-mono text-slate-400">/{agent.key}</span>
                </button>
              ))}
            </div>
          )}

          <div className="bg-white/95 backdrop-blur-xl border border-slate-200 rounded-2xl p-2 shadow-[0_20px_50px_rgba(0,0,0,0.1)] flex items-end space-x-2">
            <div className="flex-1 relative">
              <Input
                ref={inputRef}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder={
                  showAgentAutocomplete
                    ? "Select an agent..."
                    : "Message #team-chat or /agent-name"
                }
                className="bg-transparent border-0 focus-visible:ring-0 text-slate-900 placeholder:text-slate-400 h-12 text-base px-4"
              />
            </div>
            <div className="flex items-center pb-1 pr-1 space-x-1">
              <Button
                variant="ghost"
                size="icon"
                className="text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-xl h-10 w-10 transition-all"
              >
                <Paperclip className="h-5 w-5" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className={cn(
                  "text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-xl h-10 w-10 transition-all",
                  isRecording && "text-red-600 bg-red-50"
                )}
                onClick={() => setIsRecording(!isRecording)}
              >
                <Mic className="h-5 w-5" />
              </Button>
              <Button
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || isSending}
                className="bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl h-10 w-10 p-0 shadow-lg shadow-indigo-500/20 transition-all active:scale-95"
              >
                {isSending ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  <Send className="h-5 w-5" />
                )}
              </Button>
            </div>
          </div>

          {/* Help Tooltip */}
          <div className="mt-3 text-center">
            <span className="inline-flex items-center space-x-2 text-[10px] uppercase tracking-widest text-slate-400 font-bold">
              <Sparkles className="h-3 w-3 text-indigo-500" />
              <span>Type /agent-name to call an assistant</span>
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

