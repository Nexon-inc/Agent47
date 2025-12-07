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
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
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
    <div className="flex flex-col h-full bg-[#36393f] text-gray-100">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700 bg-[#2f3136]">
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
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
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
            const isSameUser = index > 0 && messages[index - 1].user_id === message.user_id
            const isSameAgent = index > 0 && 
              messages[index - 1].agent_key === message.agent_key &&
              messages[index - 1].agent_key !== null

            return (
              <div
                key={message.id}
                className={cn(
                  "flex items-start space-x-3 group hover:bg-[#2f3136]/50 rounded-lg p-2 -mx-2",
                  isSameUser && !isAgent && "mt-1",
                  isSameAgent && "mt-1"
                )}
              >
                {/* Avatar */}
                {(!isSameUser && !isAgent) || (!isSameAgent && isAgent) ? (
                  <Avatar className="h-10 w-10 flex-shrink-0">
                    {isAgent ? (
                      <AvatarFallback className={cn("bg-[#2f3136] border-2", agentInfo?.color.replace("text-", "border-"))}>
                        <Bot className={cn("h-5 w-5", agentInfo?.color)} />
                      </AvatarFallback>
                    ) : (
                      <>
                        <AvatarImage src={message.avatar_url} />
                        <AvatarFallback className="bg-[#5865f2]">
                          {message.user_name.charAt(0).toUpperCase()}
                        </AvatarFallback>
                      </>
                    )}
                  </Avatar>
                ) : (
                  <div className="w-10" /> // Spacer for same user messages
                )}

                {/* Message Content */}
                <div className="flex-1 min-w-0">
                  {(!isSameUser && !isAgent) || (!isSameAgent && isAgent) ? (
                    <div className="flex items-center space-x-2 mb-1">
                      <span className={cn("font-semibold", isAgent && agentInfo?.color)}>
                        {isAgent ? agentInfo?.name || message.agent_key : message.user_name}
                      </span>
                      {isAgent && (
                        <Badge variant="outline" className="text-xs bg-[#2f3136] border-gray-600">
                          <Bot className="h-3 w-3 mr-1" />
                          Agent
                        </Badge>
                      )}
                      <span className="text-xs text-gray-400">{formatTime(message.created_at)}</span>
                    </div>
                  ) : null}

                  <div className="text-gray-300 whitespace-pre-wrap break-words">
                    {message.content}
                  </div>

                  {/* Display generated images */}
                  {message.file_url && (
                    <div className="mt-3">
                      {/* Check if it's an image URL */}
                      {message.file_url.match(/\.(jpg|jpeg|png|gif|webp|svg)$/i) || 
                       message.file_url.includes('storage') || 
                       message.file_url.includes('supabase') ? (
                        <div className="rounded-lg overflow-hidden border border-gray-600 max-w-md">
                          <img
                            src={message.file_url}
                            alt="Generated image"
                            className="w-full h-auto"
                            onError={(e) => {
                              // Fallback to link if image fails to load
                              e.currentTarget.style.display = 'none'
                              const link = e.currentTarget.nextElementSibling as HTMLElement
                              if (link) link.style.display = 'block'
                            }}
                          />
                          <a
                            href={message.file_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="hidden text-blue-400 hover:text-blue-300 flex items-center space-x-2 p-2 bg-[#2f3136]"
                          >
                            <Paperclip className="h-4 w-4" />
                            <span>View Image</span>
                          </a>
                        </div>
                      ) : (
                        <a
                          href={message.file_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-400 hover:text-blue-300 flex items-center space-x-2"
                        >
                          <Paperclip className="h-4 w-4" />
                          <span>{message.file_name || "Attachment"}</span>
                        </a>
                      )}
                    </div>
                  )}

                  {message.audio_url && (
                    <div className="mt-2">
                      <audio controls className="w-full max-w-md">
                        <source src={message.audio_url} />
                      </audio>
                    </div>
                  )}
                </div>
              </div>
            )
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="px-4 py-3 border-t border-gray-700 bg-[#2f3136]">
        {/* Agent Autocomplete */}
        {showAgentAutocomplete && filteredAgents.length > 0 && (
          <div className="mb-2 bg-[#202225] border border-gray-600 rounded-lg overflow-hidden shadow-xl">
            {filteredAgents.map((agent, index) => (
              <button
                key={agent.key}
                onClick={() => handleAgentSelect(agent)}
                className={cn(
                  "w-full flex items-center space-x-3 px-4 py-2 text-left hover:bg-[#2f3136] transition-colors",
                  index === selectedAgentIndex && "bg-[#2f3136]"
                )}
              >
                <div className={cn("text-2xl", agent.color)}>{agent.icon}</div>
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-semibold text-gray-200">{agent.name}</span>
                    <Badge variant="outline" className="text-xs bg-[#2f3136] border-gray-600">
                      <Bot className="h-3 w-3 mr-1" />
                      Agent
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-400">{agent.description}</p>
                </div>
                <span className="text-xs text-gray-500">/{agent.key}</span>
              </button>
            ))}
          </div>
        )}

        <div className="flex items-end space-x-2">
          <div className="flex-1 relative">
            <Input
              ref={inputRef}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder={
                showAgentAutocomplete
                  ? "Select an agent or continue typing..."
                  : "Message #team-chat or /agent-name to call an agent"
              }
              className="bg-[#40444b] border-gray-600 text-gray-100 placeholder:text-gray-500 focus:border-gray-500"
            />
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="text-gray-400 hover:text-gray-300 hover:bg-[#40444b]"
          >
            <Paperclip className="h-5 w-5" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="text-gray-400 hover:text-gray-300 hover:bg-[#40444b]"
            onClick={() => setIsRecording(!isRecording)}
          >
            <Mic className={cn("h-5 w-5", isRecording && "text-red-500")} />
          </Button>
          <Button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isSending}
            className="bg-[#5865f2] hover:bg-[#4752c4] text-white"
          >
            {isSending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>

        {/* Help Text */}
        <div className="mt-2 text-xs text-gray-500">
          <span className="flex items-center space-x-1">
            <Sparkles className="h-3 w-3" />
            <span>
              Type <code className="bg-[#40444b] px-1 py-0.5 rounded">/agent-name</code> to call an agent
            </span>
          </span>
        </div>
      </div>
    </div>
  )
}

