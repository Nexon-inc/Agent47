"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import {
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
} from "lucide-react"
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
    description: "Social Media Agent - Create posts, manage accounts",
    icon: "📱",
    color: "text-pink-500",
  },
  {
    key: "clara",
    name: "Clara",
    description: "Customer Support Agent - Handle tickets and chats",
    icon: "💬",
    color: "text-blue-500",
  },
  {
    key: "eric",
    name: "Eric",
    description: "Sales Agent - Qualify leads, generate proposals",
    icon: "💰",
    color: "text-green-500",
  },
  {
    key: "jackie",
    name: "Jackie",
    description: "Marketing Agent - Create campaigns, analyze performance",
    icon: "📊",
    color: "text-purple-500",
  },
  {
    key: "joe",
    name: "Joe",
    description: "Research Agent - Market research, competitor analysis",
    icon: "🔍",
    color: "text-orange-500",
  },
  {
    key: "purity",
    name: "Purity",
    description: "Business Intelligence Agent - Analytics and insights",
    icon: "📈",
    color: "text-indigo-500",
  },
  {
    key: "shakes",
    name: "Shakes",
    description: "Content Creation Agent - Write content, optimize SEO",
    icon: "✍️",
    color: "text-yellow-500",
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
    const unsubscribe = websocketService.subscribe('team_chat_message', (message) => {
      // Reload messages when new team chat message is received
      setTimeout(loadMessages, 300) // Small delay to ensure DB is updated
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

  // Check if user has team access
  const userPlan = user?.tier || "free"
  const canAccessTeam = userPlan !== "free"

  if (!canAccessTeam) {
    return (
      <div className="flex flex-col h-full bg-[#36393f] text-gray-100 items-center justify-center p-8">
        <Lock className="h-16 w-16 text-gray-600 mb-4" />
        <h3 className="text-xl font-semibold text-gray-300 mb-2">Team Chat Not Available</h3>
        <p className="text-gray-500 text-center max-w-md mb-6">
          Team chat is only available for Starter and Pro plans. Upgrade to collaborate with your team and use agents in team chat.
        </p>
        <Button
          onClick={() => window.location.href = '/pricing'}
          className="bg-[#5865f2] hover:bg-[#4752c4] text-white"
        >
          <Crown className="h-4 w-4 mr-2" />
          Upgrade Plan
        </Button>
      </div>
    )
  }

  if (!hasTeam && !isLoading) {
    return (
      <div className="flex flex-col h-full bg-[#36393f] text-gray-100 items-center justify-center p-8">
        <Users className="h-16 w-16 text-gray-600 mb-4" />
        <h3 className="text-xl font-semibold text-gray-300 mb-2">No Team Found</h3>
        <p className="text-gray-500 text-center max-w-md mb-6">
          You need to create or join a team to use team chat. Go to the Members tab to invite team members.
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full bg-[#0b0d11] text-gray-100 font-sans selection:bg-indigo-500/30">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-white/5 bg-[#0b0d11]/80 backdrop-blur-md sticky top-0 z-10">
        <div className="flex items-center space-x-2">
          <Hash className="h-5 w-5 text-gray-400" />
          <h2 className="text-lg font-semibold">team-chat</h2>
        </div>
        <div className="flex items-center space-x-2">
          <Users className="h-4 w-4 text-gray-400" />
          <span className="text-sm text-gray-400">Team Chat</span>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-8">
        <div className="max-w-4xl mx-auto space-y-8">
          {isLoading ? (
            <div className="flex items-center justify-center h-full">
              <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
            </div>
          ) : messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <MessageSquare className="h-12 w-12 text-gray-600 mb-4" />
              <h3 className="text-lg font-semibold text-gray-300 mb-2">No messages yet</h3>
              <p className="text-gray-500 mb-4">
                Start a conversation by typing a message or use /agent-name to call an agent
              </p>
              <div className="flex flex-wrap gap-2 justify-center">
                {AVAILABLE_AGENTS.slice(0, 3).map((agent) => (
                  <Button
                    key={agent.key}
                    variant="outline"
                    size="sm"
                    onClick={() => handleAgentSelect(agent)}
                    className="bg-[#2f3136] border-gray-600 text-gray-300 hover:bg-[#40444b]"
                  >
                    <Bot className="h-4 w-4 mr-2" />
                    {agent.name}
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
                          "h-9 w-9 rounded-xl flex items-center justify-center border border-white/10 shadow-lg bg-[#16171d]",
                          agentInfo?.color.replace("text-", "bg-").replace("-500", "-500/10")
                        )}>
                          <span className="text-xl">{agentInfo?.icon}</span>
                        </div>
                      ) : (
                        <Avatar className="h-9 w-9 rounded-xl border border-white/10 shadow-lg">
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
                            isAgent ? "text-white" : "text-gray-300"
                          )}>
                            {isAgent ? agentInfo?.name : message.user_name}
                          </span>
                          {isAgent && (
                            <div className="flex items-center space-x-1 bg-white/5 border border-white/10 px-1.5 py-0.5 rounded-md">
                              <Bot className="h-3 w-3 text-indigo-400" />
                              <span className="text-[10px] uppercase font-bold text-gray-500 tracking-wider">Assistant</span>
                            </div>
                          )}
                          <span className="text-[10px] text-white/20 font-medium">{formatTime(message.created_at)}</span>
                        </div>
                      )}

                      <div className={cn(
                        "px-4 py-3 rounded-2xl text-[15px] leading-relaxed",
                        isUser
                          ? "bg-[#1d1e24] text-gray-100 border border-white/5 rounded-tr-none shadow-xl"
                          : "bg-transparent text-gray-200 rounded-tl-none"
                      )}>
                        <div className="whitespace-pre-wrap break-words">
                          {message.content}
                        </div>

                        {/* File Attachments */}
                        {message.file_url && (
                          <div className="mt-3">
                            {message.file_url.match(/\.(jpg|jpeg|png|gif|webp|svg)$/i) ||
                              message.file_url.includes('storage') ||
                              message.file_url.includes('supabase') ? (
                              <div className="rounded-xl overflow-hidden border border-white/10 max-w-md shadow-2xl">
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
                                className="inline-flex items-center space-x-2 px-3 py-2 bg-white/5 border border-white/10 rounded-xl text-indigo-400 hover:text-indigo-300 hover:bg-white/10 transition-all"
                              >
                                <Paperclip className="h-4 w-4" />
                                <span className="text-sm font-medium">{message.file_name || "Attachment"}</span>
                              </a>
                            )}
                          </div>
                        )}

                        {message.audio_url && (
                          <div className="mt-3 bg-white/5 p-2 rounded-xl border border-white/10">
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

      {/* Floating Input Area */}
      <div className="fixed bottom-8 left-0 right-0 z-20 px-4">
        <div className="max-w-3xl mx-auto">
          {/* Agent Autocomplete */}
          {showAgentAutocomplete && filteredAgents.length > 0 && (
            <div className="mb-4 bg-[#16171d] border border-white/10 rounded-2xl overflow-hidden shadow-2xl backdrop-blur-xl">
              {filteredAgents.map((agent, index) => (
                <button
                  key={agent.key}
                  onClick={() => handleAgentSelect(agent)}
                  className={cn(
                    "w-full flex items-center space-x-3 px-5 py-3 text-left hover:bg-white/5 transition-colors",
                    index === selectedAgentIndex && "bg-white/5"
                  )}
                >
                  <div className={cn("text-2xl", agent.color)}>{agent.icon}</div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-gray-200">{agent.name}</span>
                      <Badge variant="outline" className="text-[10px] uppercase tracking-wider bg-white/5 border-white/10 text-gray-400">
                        Agent
                      </Badge>
                    </div>
                    <p className="text-xs text-gray-400">{agent.description}</p>
                  </div>
                  <span className="text-xs font-mono text-gray-500">/{agent.key}</span>
                </button>
              ))}
            </div>
          )}

          <div className="bg-[#16171d]/90 backdrop-blur-xl border border-white/10 rounded-2xl p-2 shadow-2xl flex items-end space-x-2">
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
                className="bg-transparent border-0 focus-visible:ring-0 text-gray-100 placeholder:text-white/20 h-12 text-base px-4"
              />
            </div>
            <div className="flex items-center pb-1 pr-1 space-x-1">
              <Button
                variant="ghost"
                size="icon"
                className="text-white/40 hover:text-white/70 hover:bg-white/5 rounded-xl h-10 w-10 transition-all"
              >
                <Paperclip className="h-5 w-5" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className={cn(
                  "text-white/40 hover:text-white/70 hover:bg-white/5 rounded-xl h-10 w-10 transition-all",
                  isRecording && "text-red-500 bg-red-500/10"
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
            <span className="inline-flex items-center space-x-2 text-[10px] uppercase tracking-widest text-white/20 font-medium">
              <Sparkles className="h-3 w-3" />
              <span>Type /agent-name to call an assistant</span>
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

