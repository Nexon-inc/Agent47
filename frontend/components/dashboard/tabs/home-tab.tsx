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
  Pencil,
  SquarePen,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useAuthStore } from "@/lib/stores/auth-store"
import { useUserStore } from "@/lib/stores/user-store"
import { apiClient } from "@/lib/api-client"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { useToast } from "@/hooks/use-toast"
import { Skeleton } from "@/components/ui/skeleton"

const formatTime = (dateStr: string) => {
  try {
    const date = new Date(dateStr)
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } catch (e) {
    return ""
  }
}

const agents = [
  {
    id: "aria",
    name: "Aria",
    title: "AI Social Media Specialist",
    description: "I help automate your social media workflow with intelligent posting, engagement tracking, and content optimization across all major platforms.",
    icon: Globe,
    color: "bg-orange-500",
  },
  {
    id: "clara",
    name: "Clara",
    title: "AI Customer Support Specialist",
    description: "I handle customer inquiries and support tickets with AI-powered responses, intelligent routing, and 24/7 availability.",
    icon: Headphones,
    color: "bg-purple-500",
  },
  {
    id: "eric",
    name: "Eric",
    title: "AI Sales Representative",
    description: "I boost your sales and conversions with intelligent lead scoring, proposal generation, and pipeline management.",
    icon: DollarSign,
    color: "bg-amber-500",
  },
  {
    id: "jackie",
    name: "Jackie",
    title: "AI Marketing Director",
    description: "I optimize your marketing campaigns with data-driven insights, audience segmentation, and automated workflows.",
    icon: Megaphone,
    color: "bg-pink-500",
  },
  {
    id: "shakes",
    name: "Shakes",
    title: "AI Creative Director",
    description: "I create engaging content for your audience with AI-powered writing, editing, and optimization tools.",
    icon: FileText,
    color: "bg-green-500",
  },
  {
    id: "joe",
    name: "Joe",
    title: "AI Research Analyst",
    description: "I conduct comprehensive market research and competitive analysis with AI-powered data collection and insights.",
    icon: Search,
    color: "bg-blue-500",
  },
  {
    id: "purity",
    name: "Purity",
    title: "AI Business Architect",
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
        content: `${selectedAgent.name} is not available in your current plan. Please select a specialist from your available workforce or upgrade your plan.`,
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
          content: `${selectedAgent.name} is not on your team. Please hire this specialist in the Recruitment tab first.`,
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
          content: `${selectedAgent.name} is currently off-duty. Please activate this specialist in the My Team tab to start chatting.`,
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
        title: newValue ? "Workforce Unity Established" : "Team Isolation Protocol Active",
        description: newValue ? "Your specialists are now coordinating via shared workforce intelligence." : "Specialists are now operating in standard isolated mode.",
      })
    } catch (error) {
      console.error("Failed to toggle intercommunication:", error)
      toast({
        title: "Communication Error",
        description: "Failed to update inter-agent communication preference.",
        variant: "destructive",
      })
    }
  }

  return (
    <div className="flex flex-col min-h-screen bg-white text-slate-900 font-sans selection:bg-emerald-500/30 relative">

      {/* Header - Minimalist Top Bar */}
      <div className="sticky top-0 z-[60] bg-white/95 backdrop-blur-xl border-b border-slate-100 px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center">
            <span className="text-sm font-black uppercase tracking-[0.3em] text-emerald-600">BETA</span>
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="icon"
              className="text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50 rounded-full transition-colors h-10 w-10"
              onClick={() => {
                setChatMessages([])
                toast({
                  title: "New Chat Started",
                  description: "Protocol initialized for a fresh session.",
                })
              }}
            >
              <SquarePen className="h-6 w-6" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50 rounded-full transition-colors h-10 w-10"
            >
              <History className="h-6 w-6" />
            </Button>
          </div>
        </div>
      </div>

      {/* Main Chat Content        {/* Chat History Area */}
      {/* Main Command Center Content */}
      <div className="flex-1 overflow-y-auto px-6 py-8 bg-slate-50/30">
        <div className="max-w-6xl mx-auto space-y-8">

          {/* Welcome & Status Header */}
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
            <div>
              <h1 className="text-4xl font-black text-slate-900 tracking-tight mb-2">
                Intelligence <span className="text-emerald-600">Hub</span>
              </h1>
              <p className="text-slate-500 font-medium text-lg max-w-xl leading-relaxed">
                Your AI-powered business command center. Monitor performance, coordinate specialists, and scale operations.
              </p>
            </div>
            <div className="flex items-center space-x-3 bg-white border border-slate-100 p-2 rounded-2xl shadow-sm">
              <div className="flex -space-x-2">
                {userAgents.slice(0, 3).map((ua, i) => {
                  const a = agents.find(ag => ag.id === ua.agent_id);
                  return (
                    <div key={i} className={cn("h-8 w-8 rounded-full border-2 border-white flex items-center justify-center shadow-sm text-white", a?.color)}>
                      {a && <a.icon className="h-4 w-4" />}
                    </div>
                  );
                })}
              </div>
              <div className="px-2">
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Status</p>
                <div className="flex items-center space-x-1.5">
                  <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-xs font-bold text-slate-900">{userAgents.length} Personnel Active</span>
                </div>
              </div>
            </div>
          </div>

          {/* Core Metrics Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="border-slate-100 shadow-sm rounded-[32px] overflow-hidden group hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="h-12 w-12 bg-emerald-50 rounded-2xl flex items-center justify-center text-emerald-600">
                    <TrendingUp className="h-6 w-6" />
                  </div>
                  <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-100 rounded-lg">+12.4%</Badge>
                </div>
                <h3 className="text-sm font-black text-slate-400 uppercase tracking-widest mb-1">Growth Index</h3>
                <p className="text-3xl font-black text-slate-900">84.2%</p>
              </CardContent>
            </Card>

            <Card className="border-slate-100 shadow-sm rounded-[32px] overflow-hidden group hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="h-12 w-12 bg-blue-50 rounded-2xl flex items-center justify-center text-blue-600">
                    <Activity className="h-6 w-6" />
                  </div>
                  <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-100 rounded-lg">Operational</Badge>
                </div>
                <h3 className="text-sm font-black text-slate-400 uppercase tracking-widest mb-1">Active Cycles</h3>
                <p className="text-3xl font-black text-slate-900">4,281</p>
              </CardContent>
            </Card>

            <Card className="border-slate-100 shadow-sm rounded-[32px] overflow-hidden group hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="h-12 w-12 bg-purple-50 rounded-2xl flex items-center justify-center text-purple-600">
                    <Target className="h-6 w-6" />
                  </div>
                  <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-100 rounded-lg">98% Success</Badge>
                </div>
                <h3 className="text-sm font-black text-slate-400 uppercase tracking-widest mb-1">Mission Accuracy</h3>
                <p className="text-3xl font-black text-slate-900">Elite</p>
              </CardContent>
            </Card>

            <Card className="border-slate-100 shadow-sm rounded-[32px] overflow-hidden group hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="h-12 w-12 bg-amber-50 rounded-2xl flex items-center justify-center text-amber-600">
                    <Zap className="h-6 w-6" />
                  </div>
                  <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-100 rounded-lg">Fast</Badge>
                </div>
                <h3 className="text-sm font-black text-slate-400 uppercase tracking-widest mb-1">Avg. Response</h3>
                <p className="text-3xl font-black text-slate-900">240ms</p>
              </CardContent>
            </Card>
          </div>

          {/* Operational Area */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

            {/* Strategy Room Entry */}
            <Card className="lg:col-span-2 border-slate-100 shadow-sm rounded-[40px] overflow-hidden bg-white group border-2 border-transparent hover:border-emerald-500/20 transition-all">
              <CardContent className="p-8">
                <div className="flex flex-col md:flex-row gap-8 items-center">
                  <div className="flex-1 space-y-4">
                    <div className="inline-flex items-center space-x-2 px-3 py-1 bg-emerald-50 text-emerald-700 rounded-full border border-emerald-100">
                      <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                      <span className="text-[10px] font-black uppercase tracking-widest">Team Comms Active</span>
                    </div>
                    <h2 className="text-3xl font-black text-slate-900 tracking-tight leading-tight">
                      Coordinate your Digital Workforce from the Strategy Room
                    </h2>
                    <p className="text-slate-500 font-medium leading-relaxed">
                      Cross-examine personnel, issue tactical commands, and monitor live operational feeds.
                    </p>
                    <Button
                      onClick={() => window.location.href = "/dashboard?tab=team-chat"}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white font-black uppercase tracking-widest text-xs px-8 h-12 rounded-2xl shadow-xl shadow-emerald-500/20 active:scale-95 transition-all"
                    >
                      Enter Strategy Room
                    </Button>
                  </div>
                  <div className="w-full md:w-64 h-64 bg-slate-50 rounded-[32px] border border-slate-100 flex items-center justify-center relative shadow-inner overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-transparent" />
                    <Bot className="h-24 w-24 text-emerald-100 animate-pulse" />
                    <Network className="absolute bottom-8 right-8 h-12 w-12 text-emerald-200/50" />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Personnel Status */}
            <Card className="border-slate-100 shadow-sm rounded-[40px] overflow-hidden bg-slate-900 text-white">
              <CardHeader className="p-8 pb-0">
                <CardTitle className="text-lg font-black uppercase tracking-widest text-slate-400">Specialists Inline</CardTitle>
                <CardDescription className="text-slate-500 font-bold uppercase text-[10px]">Neural Status Monitor</CardDescription>
              </CardHeader>
              <CardContent className="p-8 pt-6">
                <div className="space-y-6">
                  {userAgents.slice(0, 4).map((ua) => {
                    const a = agents.find(ag => ag.id === ua.agent_id);
                    if (!a) return null;
                    return (
                      <div key={ua.id} className="flex items-center justify-between group">
                        <div className="flex items-center space-x-4">
                          <div className={cn("h-10 w-10 rounded-xl flex items-center justify-center shadow-lg", a.color)}>
                            <a.icon className="h-5 w-5 text-white" />
                          </div>
                          <div>
                            <p className="font-black text-sm tracking-tight">{a.name}</p>
                            <p className="text-[10px] font-black uppercase tracking-widest text-slate-500">{a.title}</p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <div className="h-1 w-12 bg-slate-800 rounded-full overflow-hidden">
                            <div className="h-full bg-emerald-500 w-[85%] animate-pulse" />
                          </div>
                          <span className="text-[10px] font-black text-emerald-500 uppercase">Live</span>
                        </div>
                      </div>
                    );
                  })}
                  <Button
                    variant="ghost"
                    onClick={() => window.location.href = "/dashboard?tab=agents-overview"}
                    className="w-full bg-slate-800/50 hover:bg-slate-800 text-slate-400 hover:text-white rounded-xl py-6 font-black uppercase tracking-widest text-[10px] mt-4 border border-slate-800"
                  >
                    View All Personnel
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

        </div>
      </div>

      {/* Footer Branding */}
      <div className="px-6 py-8 border-t border-slate-100 bg-white">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-300">
            Agent47 Intelligence Engine • Command Center v2.0
          </p>
          <div className="flex items-center space-x-6 text-[10px] font-black uppercase tracking-widest text-slate-500">
            <a href="#" className="hover:text-emerald-600 transition-colors">Documentation</a>
            <a href="#" className="hover:text-emerald-600 transition-colors">API Access</a>
            <a href="#" className="hover:text-emerald-600 transition-colors">System Status</a>
          </div>
        </div>
      </div>
    </div>
  )
}
