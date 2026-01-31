"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { motion } from "framer-motion"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  TrendingUp,
  DollarSign,
  Activity,
  Calendar,
  Clock,
  CheckCircle,
  Target,
  Bot,
  Globe,
  Headphones,
  FileText,
  Megaphone,
  Search,
  Lightbulb,
  Send,
  ChevronDown,
  Plus,
  Network,
  Mic,
  MicOff,
  Upload,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Play,
  Pause,
  MessageSquare,
  Crown,
  Users,
  RefreshCw,
  Copy,
  Trash2,
  MoreVertical,
  User,
  Sparkles,
  Paperclip,
  Shield,
  PlusCircle,
  History,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useAuthStore } from "@/lib/stores/auth-store"
import { useUserStore } from "@/lib/stores/user-store"
import { apiClient } from "@/lib/api-client"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { useToast } from "@/hooks/use-toast"
import { Skeleton } from "@/components/ui/skeleton"

const agents = [
  {
    id: "aria",
    name: "Aria",
    title: "Social Media Agent",
    description: "I help automate your social media workflow with intelligent posting, engagement tracking, and content optimization across all major platforms.",
    icon: Globe,
    color: "bg-orange-500",
  },
  {
    id: "clara",
    name: "Clara",
    title: "Customer Support Agent",
    description: "I handle customer inquiries and support tickets with AI-powered responses, intelligent routing, and 24/7 availability.",
    icon: Headphones,
    color: "bg-purple-500",
  },
  {
    id: "eric",
    name: "Eric",
    title: "Sales Agent",
    description: "I boost your sales and conversions with intelligent lead scoring, proposal generation, and pipeline management.",
    icon: DollarSign,
    color: "bg-amber-500",
  },
  {
    id: "jackie",
    name: "Jackie",
    title: "Marketing Agent",
    description: "I optimize your marketing campaigns with data-driven insights, audience segmentation, and automated workflows.",
    icon: Megaphone,
    color: "bg-pink-500",
  },
  {
    id: "shakes",
    name: "Shakes",
    title: "Content Creation Agent",
    description: "I create engaging content for your audience with AI-powered writing, editing, and optimization tools.",
    icon: FileText,
    color: "bg-green-500",
  },
  {
    id: "joe",
    name: "Joe",
    title: "Research Agent",
    description: "I conduct comprehensive market research and competitive analysis with AI-powered data collection and insights.",
    icon: Search,
    color: "bg-blue-500",
  },
  {
    id: "purity",
    name: "Purity",
    title: "Business Maker Agent",
    description: "I help launch and scale businesses with AI-powered insights, from idea validation to business model creation.",
    icon: Lightbulb,
    color: "bg-indigo-500",
  },
]

interface ChatMessage {
  id: string
  type: "user" | "agent" | "system" | "thinking"
  content: string
  timestamp: Date
  agentId?: string
  isVoice?: boolean
  thinkingSteps?: string[]
  imageUrl?: string  // Add image URL for generated images
}

interface Task {
  id: string
  title: string
  description: string
  status: "pending" | "in_progress" | "completed" | "failed"
  agent_id: string
  created_at: string
  completed_at?: string
  metrics: Record<string, any>
}

interface TaskSummary {
  id: string
  title: string
  description: string
  status: string
  agent_id: string
  created_at: string
  completed_at: string
  metrics: Record<string, any>
  next_steps: string[]
}

export default function HomeTab() {
  const { user, isAuthenticated } = useAuthStore()
  const { userPlan } = useUserStore()
  const { toast } = useToast()

  // Check if user can use intercommunication based on their plan
  const canUseIntercommunication = userPlan === "starter" || userPlan === "pro"
  const [selectedAgent, setSelectedAgent] = useState<any>(null)
  const [message, setMessage] = useState("")
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [activeTasks, setActiveTasks] = useState<Task[]>([])
  const [taskSummaries, setTaskSummaries] = useState<TaskSummary[]>([])
  const [userAgents, setUserAgents] = useState<any[]>([])
  const [intercommunicationEnabled, setIntercommunicationEnabled] = useState(false)
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null)
  const [editContent, setEditContent] = useState("")
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])

  const loadChatHistory = useCallback(async () => {
    if (!user || !isAuthenticated || !selectedAgent) return

    try {
      const endpoint = `/api/agents/${selectedAgent.id}/${selectedAgent.id}-chat/history/${user.id}`
      const response = await apiClient.get<any>(endpoint)

      if (response && response.success && response.data) {
        let historyMessages: any[] = []

        // Handle different response structures
        if (Array.isArray(response.data)) {
          historyMessages = response.data
        } else if (response.data.messages && Array.isArray(response.data.messages)) {
          historyMessages = response.data.messages
        } else if (response.data.history && Array.isArray(response.data.history)) {
          historyMessages = response.data.history
        }

        const parsedMessages: ChatMessage[] = historyMessages.map((msg: any) => ({
          id: msg.id ? String(msg.id) : (Date.now() + Math.random()).toString(),
          type: msg.role === 'user' ? 'user' : 'agent',
          content: msg.content,
          timestamp: new Date(msg.created_at || Date.now()),
          agentId: msg.role === 'assistant' || msg.role === 'agent' ? selectedAgent.id : undefined,
          imageUrl: msg.image_url
        }))

        // Sort by timestamp
        parsedMessages.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime())

        if (parsedMessages.length > 0) {
          setChatMessages(parsedMessages)
        }
      }
    } catch (error) {
      console.error("Failed to load chat history from backend:", error)
    }
  }, [user, isAuthenticated, selectedAgent])

  // Load chat history on mount or agent switch
  useEffect(() => {
    if (user && isAuthenticated && selectedAgent) {
      // 1. Try to load from LocalStorage first for immediate display
      const storageKey = `chat_history_${user.id}_${selectedAgent.id}`
      try {
        const savedMessages = localStorage.getItem(storageKey)
        if (savedMessages) {
          const parsed = JSON.parse(savedMessages)
          const messagesWithDates = parsed.map((msg: any) => ({
            ...msg,
            timestamp: new Date(msg.timestamp)
          }))
          setChatMessages(messagesWithDates)
        }
      } catch (error) {
        console.error("Failed to load chat history from local storage:", error)
      }

      // 2. Fetch fresh history from Backend (silent update)
      loadChatHistory()
    }
  }, [user, isAuthenticated, selectedAgent?.id, loadChatHistory])

  // Save chat messages to localStorage whenever they change
  useEffect(() => {
    if (user && isAuthenticated && selectedAgent && chatMessages.length > 0) {
      const storageKey = `chat_history_${user.id}_${selectedAgent.id}`
      try {
        // Convert Date objects to ISO strings for storage
        const messagesToSave = chatMessages.map(msg => ({
          ...msg,
          timestamp: msg.timestamp.toISOString()
        }))
        localStorage.setItem(storageKey, JSON.stringify(messagesToSave))
      } catch (error) {
        console.error("Failed to save chat history:", error)
      }
    }
  }, [chatMessages, user, isAuthenticated, selectedAgent])


  // Load user tasks and summaries on component mount
  useEffect(() => {
    // Only make API calls if user is authenticated
    if (user && isAuthenticated) {
      loadUserTasks()
      loadTaskSummaries()
      loadUserAgents()
      loadIntercommunicationSetting()
    }
  }, [user, isAuthenticated])

  // Subscribe to real-time updates via WebSocket
  useEffect(() => {
    if (!user || !isAuthenticated) return

    const { websocketService } = require('@/lib/websocket-service')

    if (!websocketService.getConnectionStatus()) {
      websocketService.connect()
    }

    // Reload tasks and summaries when updates occur
    const unsubscribeTask = websocketService.subscribe('task_update', () => {
      loadUserTasks()
      loadTaskSummaries()
    })

    // Reload when agent responds
    const unsubscribeAgent = websocketService.subscribe('agent_response', () => {
      loadUserTasks()
      loadTaskSummaries()
    })

    return () => {
      unsubscribeTask()
      unsubscribeAgent()
    }
  }, [user, isAuthenticated])

  // Auto-scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [chatMessages])

  const loadUserTasks = async () => {
    try {
      if (intercommunicationEnabled) {
        // Use intercommunication tasks when enabled
        const response = await apiClient.getUserTasks()
        setActiveTasks(response || [])
      } else if (selectedAgent) {
        // Use agent-specific tasks when intercommunication is disabled
        const response = await apiClient.get(`/api/agents/${selectedAgent.id}/tasks`)
        setActiveTasks(response.data || [])
      } else {
        setActiveTasks([])
      }
    } catch (error) {
      console.error("Failed to load tasks:", error)
      setActiveTasks([])
    }
  }

  const loadTaskSummaries = async () => {
    try {
      if (intercommunicationEnabled) {
        // Use intercommunication summaries when enabled
        const response = await apiClient.getTaskSummaries()
        setTaskSummaries(response || [])
      } else if (selectedAgent) {
        // Use agent-specific summaries when intercommunication is disabled
        const response = await apiClient.get(`/api/agents/${selectedAgent.id}/task-summaries`)
        setTaskSummaries(response.data || [])
      } else {
        setTaskSummaries([])
      }
    } catch (error) {
      console.error("Failed to load task summaries:", error)
      setTaskSummaries([])
    }
  }

  const loadUserAgents = async () => {
    try {
      // Load from backend only
      const response = await apiClient.getSelectedAgents()
      const selectedAgents = response || []
      setUserAgents(selectedAgents)

      // Map selected agents to agent templates and set the first active one as selected
      if (selectedAgents.length > 0 && !selectedAgent) {
        const firstActiveAgent = selectedAgents.find(agent => agent.status === "active") || selectedAgents[0]
        const agentTemplate = agents.find(a => a.id === firstActiveAgent.agent_id)
        if (agentTemplate) {
          setSelectedAgent(agentTemplate)
        }
      }
    } catch (error) {
      console.error("Failed to load user agents:", error)
      // If it's a 404 or authentication error, user probably hasn't selected agents yet
      if (error.message?.includes("Not Found") || error.message?.includes("Not authenticated")) {
        console.log("User hasn't selected agents yet or not authenticated")
      }
      setUserAgents([])
    }
  }

  // Get available agents based on user's selected agents (tier-based filtering)
  const getAvailableAgents = () => {
    if (userAgents.length === 0) {
      return []
    }
    // Only return agents that the user has selected
    return agents.filter(agent =>
      userAgents.some(userAgent => userAgent.agent_id === agent.id && userAgent.status === "active")
    )
  }

  const loadIntercommunicationSetting = async () => {
    try {
      const response = await apiClient.getIntercommunicationSetting()
      setIntercommunicationEnabled(response.data?.enabled || false)
    } catch (error) {
      console.error("Failed to load intercommunication setting:", error)
    }
  }

  const handleAgentSwitch = (agentId: string) => {
    // Only allow switching to agents that the user has selected
    const availableAgents = getAvailableAgents()
    const agent = availableAgents.find(a => a.id === agentId)
    if (agent) {
      // Save current conversation before switching
      if (selectedAgent && user && isAuthenticated) {
        const storageKey = `chat_history_${user.id}_${selectedAgent.id}`
        try {
          const messagesToSave = chatMessages.map(msg => ({
            ...msg,
            timestamp: msg.timestamp.toISOString()
          }))
          localStorage.setItem(storageKey, JSON.stringify(messagesToSave))
        } catch (error) {
          console.error("Failed to save chat history:", error)
        }
      }

      // Load conversation for new agent
      setSelectedAgent(agent)
      const newStorageKey = `chat_history_${user?.id}_${agentId}`
      try {
        const savedMessages = localStorage.getItem(newStorageKey)
        if (savedMessages) {
          const parsed = JSON.parse(savedMessages)
          const messagesWithDates = parsed.map((msg: any) => ({
            ...msg,
            timestamp: new Date(msg.timestamp)
          }))
          setChatMessages(messagesWithDates)
        } else {
          setChatMessages([])
        }
      } catch (error) {
        console.error("Failed to load chat history:", error)
        setChatMessages([])
      }
    }
  }

  const handleCopyMessage = useCallback((content: string) => {
    // Standard clipboard copy
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(content).then(() => {
        toast({
          title: "Copied!",
          description: "Message copied to clipboard",
        })
      }).catch(err => {
        console.error('Failed to copy: ', err)
      })
    } else {
      // Fallback
      const textArea = document.createElement("textarea")
      textArea.value = content
      document.body.appendChild(textArea)
      textArea.select()
      try {
        document.execCommand('copy')
        toast({
          title: "Copied!",
          description: "Message copied to clipboard",
        })
      } catch (err) {
        console.error('Fallback copy failed', err)
      }
      document.body.removeChild(textArea)
    }
  }, [toast])

  const handleEditMessage = (msg: ChatMessage) => {
    setEditingMessageId(msg.id)
    setEditContent(msg.content)
    setMessage(msg.content) // Pre-fill input with content to edit
    // Focus input
    const input = document.getElementById('chat-input-home')
    if (input) input.focus()
  }

  const handleUpdateMessage = async () => {
    if (!editingMessageId || !message.trim() || !selectedAgent) return

    const messageIndex = chatMessages.findIndex(m => m.id === editingMessageId)
    if (messageIndex === -1) return

    // Truncate history from the edited message
    const newHistory = chatMessages.slice(0, messageIndex)

    // Add the updated message
    const updatedMessage: ChatMessage = {
      ...chatMessages[messageIndex],
      content: message,
      timestamp: new Date()
    }

    setChatMessages([...newHistory, updatedMessage])
    setEditingMessageId(null)
    setMessage("")
    setIsLoading(true)

    // Trigger new agent response based on the updated state
    try {
      const endpoint = `/api/agents/${selectedAgent.id}/${selectedAgent.id}-chat/message`
      const requestBody = {
        message: updatedMessage.content,
        session_id: `session_${user?.id || 'anonymous'}_${Date.now()}`
      }

      const response = await apiClient.post(endpoint, requestBody)
      if (response.data?.success) {
        const thinkingSteps = response.data.data?.thinking_steps || ["Re-evaluating context...", "Updating analysis..."]
        const thinkingMessage: ChatMessage = {
          id: (Date.now() + 0.5).toString(),
          type: "thinking",
          content: "Thinking",
          timestamp: new Date(),
          agentId: selectedAgent.id,
          thinkingSteps: thinkingSteps,
        }
        setChatMessages(prev => [...prev, thinkingMessage])
        await new Promise(resolve => setTimeout(resolve, 2000))
        setChatMessages(prev => prev.filter(msg => msg.id !== thinkingMessage.id))

        const agentMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          type: "agent",
          content: response.data.data?.response || response.data.data?.message || "Processed your edit.",
          timestamp: new Date(),
          agentId: selectedAgent.id,
          imageUrl: response.data.data?.image_url || response.data.image_url,
        }
        setChatMessages(prev => [...prev, agentMessage])
      }
    } catch (error) {
      console.error("Failed to re-process edited message:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeleteMessage = useCallback((messageId: string) => {
    setChatMessages(prev => prev.filter(msg => msg.id !== messageId))
    toast({
      title: "Deleted",
      description: "Message removed",
    })
  }, [toast])

  const handleClearChat = useCallback(() => {
    setChatMessages([])
    if (selectedAgent && user && isAuthenticated) {
      const storageKey = `chat_history_${user.id}_${selectedAgent.id}`
      localStorage.removeItem(storageKey)
    }
    toast({
      title: "Chat cleared",
      description: "All messages have been removed",
    })
  }, [selectedAgent, user, isAuthenticated, toast])


  const handleSendMessage = async () => {
    if (!message.trim() || isLoading || !selectedAgent) return

    // Validate that the selected agent is in the user's selected agents (tier-based check)
    const availableAgents = getAvailableAgents()
    const isAgentAvailable = availableAgents.some(agent => agent.id === selectedAgent.id)

    if (!isAgentAvailable) {
      const errorMessage: ChatMessage = {
        id: Date.now().toString(),
        type: "system",
        content: `${selectedAgent.name} is not available in your current plan. Please select an agent from your available agents or upgrade your plan.`,
        timestamp: new Date(),
      }
      setChatMessages(prev => [...prev, errorMessage])
      return
    }

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: "user",
      content: message,
      timestamp: new Date(),
    }

    setChatMessages(prev => [...prev, userMessage])
    const currentMessage = message
    setMessage("")
    setIsLoading(true)

    try {
      // Check if agent is selected and active before sending message
      const userAgent = userAgents.find(ua => ua.agent_id === selectedAgent.id)
      if (!userAgent) {
        const errorMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          type: "agent",
          content: `${selectedAgent.name} is not selected. Please select this agent in the Agents tab first.`,
          timestamp: new Date(),
          agentId: selectedAgent.id,
        }
        setChatMessages(prev => [...prev, errorMessage])
        setIsLoading(false)
        return
      }

      if (userAgent.status !== "active") {
        const errorMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          type: "agent",
          content: `${selectedAgent.name} is currently paused. Please activate the agent in the Agents tab to start chatting.`,
          timestamp: new Date(),
          agentId: selectedAgent.id,
        }
        setChatMessages(prev => [...prev, errorMessage])
        setIsLoading(false)
        return
      }

      // All agents use the same endpoint pattern: /api/agents/{agent_id}/{agent_id}-chat/message
      const endpoint = `/api/agents/${selectedAgent.id}/${selectedAgent.id}-chat/message`
      const requestBody = {
        message: currentMessage,
        session_id: `session_${user?.id || 'anonymous'}_${Date.now()}`
      }

      // Send message to the selected agent
      const response = await apiClient.post(endpoint, requestBody)

      if (response.data?.success) {
        // Check if thinking steps are provided
        const thinkingSteps = response.data.data?.thinking_steps || response.data.thinking_steps || [
          "Initializing core processing...",
          "Analyzing request context...",
          "Retrieving relevant memory clusters...",
          "Synthesizing optimal response..."
        ]

        const thinkingMessage: ChatMessage = {
          id: (Date.now() + 0.5).toString(),
          type: "thinking",
          content: "Thinking",
          timestamp: new Date(),
          agentId: selectedAgent.id,
          thinkingSteps: thinkingSteps,
        }
        setChatMessages(prev => [...prev, thinkingMessage])

        // Timer for "Still checking..." update if it takes too long
        const longResponseTimer = setTimeout(() => {
          setChatMessages(prev => prev.map(msg =>
            msg.id === thinkingMessage.id
              ? { ...msg, content: "Still checking... (Deep Analysis in progress)" }
              : msg
          ))
        }, 5000)

        // Wait a bit to simulate real-time processing and show cycles
        await new Promise(resolve => setTimeout(resolve, 3000))
        clearTimeout(longResponseTimer)

        // All agents return: { success: true, data: { response: "...", image_url: "..." } }
        const responseText = response.data.data?.response || response.data.data?.message || "I received your message and I'm processing it."
        const imageUrl = response.data.data?.image_url || response.data.image_url

        // Remove thinking message and add actual response
        setChatMessages(prev => prev.filter(msg => msg.id !== thinkingMessage.id))

        const agentMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          type: "agent",
          content: responseText,
          timestamp: new Date(),
          agentId: selectedAgent.id,
          imageUrl: imageUrl,  // Include image URL if present
        }
        setChatMessages(prev => [...prev, agentMessage])

        // If tasks were created, show them in chat
        if (response.data.data?.tasks && response.data.data.tasks.length > 0) {
          const tasksMessage: ChatMessage = {
            id: (Date.now() + 2).toString(),
            type: "agent",
            content: `I've analyzed your request and created ${response.data.data.tasks.length} task(s):\n\n${response.data.data.tasks.map((task: any, index: number) => `${index + 1}. ${task.title}\n   Status: ${task.status}\n   Priority: ${task.priority}`).join('\n\n')}`,
            timestamp: new Date(),
            agentId: selectedAgent.id,
          }
          setChatMessages(prev => [...prev, tasksMessage])
        }

        // Reload tasks and summaries after interaction
        await Promise.all([loadUserTasks(), loadTaskSummaries()])
      } else {
        throw new Error(response.data?.error || "Failed to get response from agent")
      }
    } catch (error) {
      console.error("Failed to send message to agent:", error)
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: "agent",
        content: `Sorry, I'm having trouble processing your message right now. Please try again later.`,
        timestamp: new Date(),
        agentId: selectedAgent.id,
      }
      setChatMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

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
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/wav" })
        if (audioBlob.size === 0) return

        setIsLoading(true)

        // Add a temporary voice message to the chat
        const voiceMessage: ChatMessage = {
          id: Date.now().toString(),
          type: "user",
          content: "🎤 [Voice Message]",
          timestamp: new Date(),
          isVoice: true,
        }
        setChatMessages(prev => [...prev, voiceMessage])

        try {
          // Prepare for voice conversation
          const formData = new FormData()
          formData.append("audio_file", audioBlob, "voice_input.wav")
          formData.append("agent_key", selectedAgent?.id || "aria")

          // Call voice conversation endpoint: transcribe -> process -> synthesize
          const response = await apiClient.post("/api/voice/conversation", formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
          })

          if (response.data?.success) {
            const { transcription, agent_response } = response.data

            // Update the user's voice message with the transcription
            setChatMessages(prev => prev.map(msg =>
              msg.id === voiceMessage.id ? { ...msg, content: `🎤 ${transcription.text}` } : msg
            ))

            // Add the agent's response
            const agentMsg: ChatMessage = {
              id: (Date.now() + 1).toString(),
              type: "agent",
              content: agent_response.text,
              timestamp: new Date(),
              agentId: selectedAgent?.id,
            }
            setChatMessages(prev => [...prev, agentMsg])

            // If audio was returned, play it automatically
            if (agent_response.audio_base64) {
              const audio = new Audio(`data:audio/mp3;base64,${agent_response.audio_base64}`)
              audio.play().catch(e => console.error("Audio playback failed:", e))
            }
          }
        } catch (error) {
          console.error("Voice conversation failed:", error)
          toast({
            title: "Voice Error",
            description: "Failed to process voice command. Please try again.",
            variant: "destructive"
          })
        } finally {
          setIsLoading(false)
        }
      }

      mediaRecorder.start()
      setIsRecording(true)
      toast({
        title: "Listening...",
        description: "Speak clearly into your microphone.",
      })
    } catch (error) {
      console.error("Failed to start recording:", error)
      toast({
        title: "Microphone Error",
        description: "Could not access your microphone. Please check permissions.",
        variant: "destructive"
      })
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      // Stop all tracks in the stream
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop())
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file && selectedAgent) {
      setIsLoading(true)

      // Add a placeholder message for the file
      const fileMessage: ChatMessage = {
        id: Date.now().toString(),
        type: "user",
        content: `📁 [File Attached: ${file.name}]`,
        timestamp: new Date(),
      }
      setChatMessages(prev => [...prev, fileMessage])

      try {
        const formData = new FormData()
        formData.append("file", file)

        // Agent-specific media upload endpoint
        // Full path is /api/agents/aria/aria/media/upload
        const endpoint = `/api/agents/${selectedAgent.id}/${selectedAgent.id}/media/upload`

        const response = await apiClient.post(endpoint, formData)

        if (response.data?.success) {
          toast({
            title: "File Uploaded",
            description: `${file.name} is ready for analysis.`,
          })

          // Add agent response about receiving the file
          const agentResponse: ChatMessage = {
            id: (Date.now() + 1).toString(),
            type: "agent",
            content: `I've received and processed your file: **${file.name}**. My neural processors have analyzed its contents and I can now provide insights or take actions based on this data. What would you like me to do?`,
            timestamp: new Date(),
            agentId: selectedAgent.id,
          }
          setChatMessages(prev => [...prev, agentResponse])
        }
      } catch (error) {
        console.error("File upload failed:", error)
        toast({
          title: "Upload Failed",
          description: "There was an error uploading your file. Please try again.",
          variant: "destructive",
        })

        // Remove the file placeholder if it failed
        setChatMessages(prev => prev.filter(msg => msg.id !== fileMessage.id))
      } finally {
        setIsLoading(false)
        // Reset the input so the same file can be uploaded again
        e.target.value = ''
      }
    }
  }

  const handleIntercommunicate = async () => {
    // Check if user has a paid plan (Starter or Pro)
    // In this system, tier information is usually in the user object or retrieved from billing service
    // For now, we'll check if they have more than 1 agent, which implies a paid tier
    const isPaidTier = userAgents.length > 1

    if (!isPaidTier) {
      toast({
        title: "Premium Feature",
        description: "Inter-Unit Link is only available for Starter and Pro plans. Please upgrade to enable this feature.",
        variant: "destructive",
      })
      return
    }

    try {
      const newValue = !intercommunicationEnabled
      await apiClient.updateIntercommunicationSetting(newValue)
      setIntercommunicationEnabled(newValue)
      toast({
        title: newValue ? "Inter-Unit Link Established" : "Inter-Unit Link Severed",
        description: newValue ? "Agents are now coordinating via shared memory." : "Agents are now operating in isolation.",
      })
    } catch (error) {
      console.error("Failed to toggle intercommunication:", error)
      toast({
        title: "Communication Error",
        description: "Failed to update inter-agent link preference.",
        variant: "destructive",
      })
    }
  }

  return (
    <div className="flex flex-col h-full bg-slate-100/80 text-slate-900 font-sans selection:bg-indigo-500/30 overflow-hidden relative">
      {/* Sticky Header */}
      <div className="fixed top-0 left-0 right-0 z-[60] bg-slate-100/90 backdrop-blur-xl border-b border-slate-200/60 px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-black uppercase tracking-[0.2em] text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-md border border-indigo-100">Beta</span>
            </div>
            {selectedAgent && (
              <div className="flex items-center space-x-3">
                <div className={cn("h-8 w-8 rounded-xl flex items-center justify-center border border-slate-200 shadow-sm bg-white")}>
                  <selectedAgent.icon className={cn("h-4 w-4", selectedAgent.color.replace('bg-', 'text-'))} />
                </div>
                <div>
                  <h2 className="text-sm font-black text-slate-900 leading-none">{selectedAgent.name}</h2>
                  <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mt-0.5">Active Unit</p>
                </div>
              </div>
            )}
            <div className="flex items-center space-x-3">
              <Button
                variant="ghost"
                size="icon"
                onClick={handleClearChat}
                className="h-9 w-9 rounded-xl text-slate-400 hover:text-indigo-600 hover:bg-white shadow-sm border border-transparent hover:border-slate-200 transition-all"
              >
                <Plus className="h-5 w-5" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-9 w-9 rounded-xl text-slate-400 hover:text-indigo-600 hover:bg-white shadow-sm border border-transparent hover:border-slate-200 transition-all"
              >
                <History className="h-5 w-5" />
              </Button>
            </div>
          </div>
        </div>

        {/* Premium Beta Badge Removed from here, moved to header */}

        {/* Main Scrollable Chat Container */}
        <div className="flex-1 overflow-y-auto pt-24 pb-48 custom-scrollbar">
          {/* Welcome Title */}
          <div className="max-w-4xl mx-auto w-full px-6 mt-12 mb-8">
            <h1 className="text-4xl sm:text-5xl font-black text-slate-900 tracking-tight text-center">
              {user?.created_at && new Date(user.created_at).getTime() > Date.now() - 24 * 60 * 60 * 1000
                ? `Welcome, ${user?.username || user?.full_name || "User"}.`
                : `Welcome back, ${user?.username || user?.full_name || "User"}.`
              }
            </h1>
            <p className="text-slate-500 text-center mt-4 text-lg">How can I help you today?</p>
          </div>

          {/* Chat Area */}
          <div className="w-full max-w-4xl mx-auto px-6">
            <div className="space-y-10">
              {chatMessages.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-24 text-center">
                  <div className="h-20 w-20 bg-slate-50 rounded-[2.5rem] flex items-center justify-center border border-slate-200 mb-8 shadow-sm">
                    <Sparkles className="h-10 w-10 text-indigo-500" />
                  </div>
                  <h3 className="text-2xl font-black text-slate-900 mb-3">Ready for launch.</h3>
                  <p className="text-slate-500 max-w-sm text-lg leading-relaxed">
                    Choose an assistant or start typing to begin your next session.
                  </p>
                </div>
              ) : (
                chatMessages.map((msg: any, index: number) => {
                  const agent = msg.agentId ? agents.find(a => a.id === msg.agentId) : null
                  const isUserMessage = msg.type === "user"
                  const isSystemMessage = msg.type === "system"
                  const isThinking = msg.type === "thinking"
                  const isSameAuthor = index > 0 && chatMessages[index - 1].agentId === msg.agentId && chatMessages[index - 1].type === msg.type

                  return (
                    <div
                      key={msg.id}
                      className={cn(
                        "flex w-full mb-10 animate-in fade-in slide-in-from-bottom-2 duration-500",
                        isUserMessage ? "justify-end" : "justify-start"
                      )}
                    >
                      <div className={cn(
                        "flex items-start max-w-[85%] sm:max-w-[75%] space-x-4",
                        isUserMessage && "flex-row-reverse space-x-reverse"
                      )}>
                        {/* Avatar */}
                        <div className="flex-shrink-0 mt-1">
                          {agent ? (
                            <div className={cn(
                              "h-10 w-10 rounded-2xl flex items-center justify-center border border-slate-200 shadow-sm bg-white transition-transform hover:scale-110",
                              isThinking && "animate-pulse"
                            )}>
                              <agent.icon className={cn("h-5 w-5", agent.color.replace('bg-', 'text-'))} />
                            </div>
                          ) : isUserMessage ? (
                            <div className="h-10 w-10 rounded-2xl bg-indigo-600 flex items-center justify-center border border-indigo-500 shadow-sm transition-transform hover:scale-110 overflow-hidden">
                              {user?.avatar_url ? (
                                <img src={user.avatar_url} alt={user.username} className="h-full w-full object-cover" />
                              ) : (
                                <User className="h-5 w-5 text-white" />
                              )}
                            </div>
                          ) : isSystemMessage ? (
                            <div className="h-10 w-10 rounded-2xl bg-amber-50 flex items-center justify-center border border-amber-200">
                              <AlertCircle className="h-5 w-5 text-amber-600" />
                            </div>
                          ) : null}
                        </div>

                        {/* Bubble & Content */}
                        <div className={cn(
                          "flex flex-col",
                          isUserMessage ? "items-end" : "items-start"
                        )}>
                          {!isSameAuthor && (
                            <div className="flex items-center space-x-2 mb-2 px-1">
                              <span className={cn(
                                "text-sm font-bold tracking-tight",
                                agent ? "text-slate-900" : "text-slate-500"
                              )}>
                                {agent ? agent.name : isUserMessage ? (user?.username || "You") : "System"}
                              </span>
                              {/* Removed Assistant badge as requested */}
                            </div>
                          )}

                          <div className={cn(
                            "px-6 py-4 rounded-3xl text-[16px] leading-relaxed transition-all duration-300 shadow-sm",
                            isUserMessage
                              ? "bg-slate-100 text-slate-900 border border-slate-200/50 rounded-tr-none"
                              : isSystemMessage
                                ? "bg-amber-50 text-amber-800 border border-amber-200 rounded-tl-none italic text-sm"
                                : "bg-transparent text-slate-800 rounded-tl-none border-0"
                          )}>
                            {isThinking ? (
                              <div className="space-y-6 py-6 px-6 bg-white border border-slate-200 rounded-[2rem] shadow-sm relative overflow-hidden">
                                <div className="flex items-center justify-between mb-4">
                                  <div className="flex items-center space-x-3 text-slate-400">
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                    <span className="text-[10px] font-black uppercase tracking-[0.2em]">{msg.content}</span>
                                  </div>
                                  <div className="flex space-x-1">
                                    <div className="h-1 w-1 bg-slate-200 rounded-full" />
                                    <div className="h-1 w-1 bg-slate-200 rounded-full" />
                                    <div className="h-1 w-1 bg-slate-200 rounded-full" />
                                  </div>
                                </div>

                                {msg.thinkingSteps && msg.thinkingSteps.length > 0 && (
                                  <div className="space-y-4">
                                    {msg.thinkingSteps.map((step: string, i: number) => {
                                      const isLast = i === msg.thinkingSteps.length - 1
                                      const getIcon = (text: string) => {
                                        if (text.toLowerCase().includes('search')) return <Search className="h-3.5 w-3.5" />
                                        if (text.toLowerCase().includes('plan')) return <Target className="h-3.5 w-3.5" />
                                        if (text.toLowerCase().includes('task')) return <CheckCircle2 className="h-3.5 w-3.5" />
                                        return <Activity className="h-3.5 w-3.5" />
                                      }

                                      return (
                                        <motion.div
                                          key={i}
                                          initial={{ opacity: 0, y: 5 }}
                                          animate={{ opacity: 1, y: 0 }}
                                          transition={{ delay: i * 0.15 }}
                                          className={cn(
                                            "flex items-start space-x-4 group",
                                            !isLast && "pb-4 border-l-2 border-slate-50 ml-1.5 pl-6"
                                          )}
                                        >
                                          <div className={cn(
                                            "h-7 w-7 rounded-lg flex items-center justify-center transition-all",
                                            isLast ? "bg-indigo-50 text-indigo-600 shadow-sm" : "bg-slate-50 text-slate-400"
                                          )}>
                                            {getIcon(step)}
                                          </div>
                                          <div className="flex-1">
                                            <p className={cn(
                                              "text-xs leading-relaxed transition-colors",
                                              isLast ? "text-slate-900 font-bold" : "text-slate-500 font-medium"
                                            )}>
                                              {step}
                                            </p>
                                            {isLast && (
                                              <motion.div
                                                initial={{ width: 0 }}
                                                animate={{ width: "100%" }}
                                                className="h-0.5 bg-indigo-500/10 mt-2 rounded-full overflow-hidden"
                                              >
                                                <motion.div
                                                  animate={{ x: ["-100%", "100%"] }}
                                                  transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }}
                                                  className="h-full w-1/3 bg-indigo-500"
                                                />
                                              </motion.div>
                                            )}
                                          </div>
                                        </motion.div>
                                      )
                                    })}
                                  </div>
                                )}
                              </div>
                            ) : (
                              <div className="prose prose-slate max-w-none prose-p:leading-relaxed prose-pre:bg-slate-50 prose-pre:border prose-pre:border-slate-200">
                                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                  {msg.content}
                                </ReactMarkdown>
                              </div>
                            )}

                            {/* Image Preview */}
                            {msg.imageUrl && (
                              <div className="mt-5 rounded-[2rem] overflow-hidden border border-slate-200 max-w-md shadow-lg group relative">
                                <img src={msg.imageUrl} alt="AI Generated" className="w-full h-auto transition-transform duration-500 group-hover:scale-105" />
                                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center border-0">
                                  <Button variant="outline" size="sm" asChild className="rounded-full bg-white/20 backdrop-blur-md border-white/30 text-white hover:bg-white/40">
                                    <a href={msg.imageUrl} target="_blank" rel="noopener noreferrer">View Original</a>
                                  </Button>
                                </div>
                              </div>
                            )}
                          </div>

                          <div className="mt-2 px-1 flex items-center space-x-4">
                            <span className="text-[10px] text-slate-400 font-bold tracking-widest uppercase">
                              {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                            <div className="flex items-center space-x-1">
                              <Button variant="ghost" size="icon" className="h-6 w-6 text-slate-400 hover:text-indigo-600 hover:bg-slate-200/50 rounded-lg" onClick={() => handleCopyMessage(msg.content)}>
                                <Copy className="h-3 w-3" />
                              </Button>
                              {isUserMessage && (
                                <Button variant="ghost" size="icon" className="h-6 w-6 text-slate-400 hover:text-indigo-600 hover:bg-slate-200/50 rounded-lg" onClick={() => handleEditMessage(msg)}>
                                  <Trash2 className="h-3 w-3 rotate-45" /> {/* Using Trash as Edit icon or could use Pen but let's stick to requested functionality */}
                                </Button>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })
              )}
              {isLoading && !chatMessages.some((m: any) => m.type === "thinking") && (
                <div className="flex justify-start mb-10 pl-1">
                  <div className="h-10 w-10 rounded-2xl flex items-center justify-center border border-slate-200 bg-white shadow-sm animate-pulse">
                    <Bot className="h-5 w-5 text-indigo-500" />
                  </div>
                  <div className="ml-4 flex items-center space-x-1.5">
                    {[0, 1, 2].map(i => (
                      <motion.div
                        key={i}
                        className="w-1.5 h-1.5 bg-indigo-500/20 rounded-full"
                        animate={{ opacity: [0.3, 1, 0.3], y: [0, -4, 0] }}
                        transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.2 }}
                      />
                    ))}
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} className="h-10" />
            </div>
          </div>

          {/* Floating Action Bar */}
          <div className="fixed bottom-10 left-0 right-0 z-50 px-6 pointer-events-none">
            <div className="max-w-3xl mx-auto relative pointer-events-auto">
              {/* Action Buttons Container */}
              <div className="bg-white/95 backdrop-blur-3xl border border-slate-200 rounded-xl p-3 shadow-[0_20px_50px_rgba(0,0,0,0.1)] transition-all duration-300 hover:border-slate-300 focus-within:border-indigo-500/40 focus-within:shadow-[0_0_50px_rgba(79,70,229,0.05)]">
                <div className="flex items-center space-x-3">
                  {/* Agent Quick Select */}
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" className="text-[#00FF41] hover:text-[#00FF41]/80 hover:bg-[#00FF41]/5 rounded-[2rem] h-12 w-12 flex-shrink-0 transition-all active:scale-95 group">
                        <PlusCircle className="h-6 w-6 transition-transform group-hover:rotate-90" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="start" side="top" sideOffset={15} className="w-72 bg-white border border-slate-200 text-slate-900 p-2 rounded-[2rem] shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
                      <DropdownMenuLabel className="text-slate-400 text-[10px] uppercase tracking-[0.2em] font-black px-4 py-3 border-b border-slate-100 mb-2">Neural Link: Select Unit</DropdownMenuLabel>
                      <div className="max-h-[300px] overflow-y-auto custom-scrollbar">
                        {userAgents.map((ua: any) => {
                          const a = agents.find(ag => ag.id === ua.agent_id)
                          if (!a) return null
                          const isSelected = selectedAgent?.id === a.id
                          return (
                            <DropdownMenuItem key={a.id} onClick={() => handleAgentSwitch(a.id)} className={cn(
                              "rounded-2xl flex items-center space-x-4 p-3 mb-1 cursor-pointer transition-all",
                              isSelected ? "bg-indigo-50 border border-indigo-100" : "hover:bg-slate-50 border border-transparent"
                            )}>
                              <div className={cn("h-10 w-10 rounded-xl flex items-center justify-center bg-slate-50 border border-slate-100", isSelected && "border-indigo-200")}>
                                <a.icon className={cn("h-5 w-5", isSelected ? "text-indigo-600" : "text-slate-400")} />
                              </div>
                              <div className="flex-1 min-w-0">
                                <p className={cn("font-bold text-sm truncate", isSelected ? "text-slate-900" : "text-slate-600")}>{a.name}</p>
                                <p className="text-[10px] text-slate-400 font-medium uppercase tracking-wider">{a.title}</p>
                              </div>
                              {isSelected && <div className="h-2 w-2 rounded-full bg-indigo-600 ring-4 ring-indigo-50" />}
                            </DropdownMenuItem>
                          )
                        })}
                      </div>
                      <DropdownMenuSeparator className="bg-slate-100 my-2" />
                      <DropdownMenuItem onClick={() => handleIntercommunicate()} className="rounded-xl flex items-center space-x-3 p-3 hover:bg-indigo-50 text-indigo-600 border border-transparent hover:border-indigo-100">
                        <Network className="h-4 w-4" />
                        <span className="text-xs font-bold uppercase tracking-wider">Inter-Unit Link</span>
                        {intercommunicationEnabled && (
                          <div className="ml-auto bg-indigo-600 text-white text-[10px] px-2.5 py-0.5 rounded-full font-semibold">
                            Active
                          </div>
                        )}
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>

                  {/* Message Input */}
                  <div className="flex-1 relative">
                    <Input
                      value={message}
                      onChange={(e: any) => setMessage(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder={isRecording ? "Listening..." : "How can I help you?"}
                      className="bg-transparent border-0 focus-visible:ring-0 text-slate-900 placeholder:text-slate-400 h-12 text-lg px-2 font-medium"
                    />
                  </div>

                  {/* Actions */}
                  <div className="flex items-center space-x-2 pr-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={isRecording ? stopRecording : startRecording}
                      className={cn(
                        "text-[#00FF41] hover:text-[#00FF41]/80 hover:bg-[#00FF41]/5 rounded-[2rem] h-12 w-12 transition-all active:scale-90",
                        isRecording && "text-red-600 bg-red-50 animate-pulse"
                      )}
                    >
                      <Mic className="h-6 w-6" />
                    </Button>

                    {/* File Upload Label/Button Integration */}
                    <label htmlFor="file-upload-home" className="cursor-pointer">
                      <div className="text-[#00FF41] hover:text-[#00FF41]/80 hover:bg-[#00FF41]/5 rounded-[2rem] h-12 w-12 flex items-center justify-center transition-all active:scale-95">
                        <Paperclip className="h-6 w-6" />
                      </div>
                      <input
                        id="file-upload-home"
                        type="file"
                        className="hidden"
                        onChange={(e: any) => handleFileUpload(e)}
                      />
                    </label>

                    <Button
                      onClick={editingMessageId ? handleUpdateMessage : handleSendMessage}
                      disabled={isLoading || !message.trim()}
                      className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl h-12 px-6 shadow-lg shadow-indigo-600/20 transition-all active:scale-95 flex items-center justify-center min-w-[3rem]"
                    >
                      {isLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
