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
} from "lucide-react"
import { useAuthStore } from "@/lib/stores/auth-store"
import { useUserStore } from "@/lib/stores/user-store"
import { apiClient } from "@/lib/api-client"
import AgentSelectionModal from "@/components/dashboard/agent-selection-modal"
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
  const [showAgentSelection, setShowAgentSelection] = useState(false)
  const [message, setMessage] = useState("")
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [activeTasks, setActiveTasks] = useState<Task[]>([])
  const [taskSummaries, setTaskSummaries] = useState<TaskSummary[]>([])
  const [userAgents, setUserAgents] = useState<any[]>([])
  const [intercommunicationEnabled, setIntercommunicationEnabled] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])

  // Load chat history from localStorage on mount
  useEffect(() => {
    if (user && isAuthenticated) {
      const storageKey = `chat_history_${user.id}_${selectedAgent?.id || 'all'}`
      try {
        const savedMessages = localStorage.getItem(storageKey)
        if (savedMessages) {
          const parsed = JSON.parse(savedMessages)
          // Convert timestamp strings back to Date objects
          const messagesWithDates = parsed.map((msg: any) => ({
            ...msg,
            timestamp: new Date(msg.timestamp)
          }))
          setChatMessages(messagesWithDates)
        }
      } catch (error) {
        console.error("Failed to load chat history:", error)
      }
    }
  }, [user, isAuthenticated, selectedAgent?.id])

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

  // Check if user needs to select agents
  useEffect(() => {
    if (user && isAuthenticated) {
      loadUserAgents().then(() => {
        if (userAgents.length === 0) {
          setShowAgentSelection(true)
        }
      }).catch((error) => {
        setShowAgentSelection(true)
      })
    }
  }, [user, isAuthenticated])

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
    navigator.clipboard.writeText(content)
    toast({
      title: "Copied!",
      description: "Message copied to clipboard",
    })
  }, [toast])

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

  const handleAgentSelectionComplete = () => {
    setShowAgentSelection(false)
    loadUserAgents()
  }

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
        const thinkingSteps = response.data.data?.thinking_steps || response.data.thinking_steps
        
        // Show thinking state if thinking steps are provided
        if (thinkingSteps && thinkingSteps.length > 0) {
          const thinkingMessage: ChatMessage = {
            id: (Date.now() + 0.5).toString(),
            type: "thinking",
            content: "Analyzing your request...",
            timestamp: new Date(),
            agentId: selectedAgent.id,
            thinkingSteps: thinkingSteps,
          }
          setChatMessages(prev => [...prev, thinkingMessage])
          
          // Wait a bit to show thinking state, then show response
          await new Promise(resolve => setTimeout(resolve, 2000))
          
          // Remove thinking message and add actual response
          setChatMessages(prev => prev.filter(msg => msg.id !== thinkingMessage.id))
        }
        
        // All agents return: { success: true, data: { response: "...", image_url: "..." } }
        const responseText = response.data.data?.response || response.data.data?.message || "I received your message and I'm processing it."
        const imageUrl = response.data.data?.image_url || response.data.image_url  // Extract image URL if present

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
        audioChunksRef.current.push(event.data)
      }

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/wav" })
        // Handle audio processing here
        console.log("Audio recorded:", audioBlob)
      }

      mediaRecorder.start()
      setIsRecording(true)
    } catch (error) {
      console.error("Failed to start recording:", error)
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
    }
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      console.log("File uploaded:", file)
      // Handle file processing here
    }
  }

  const handleIntercommunicate = async () => {
    if (!canUseIntercommunication) {
      console.log("Intercommunication not available for free tier")
      return
    }
    
    try {
      const newValue = !intercommunicationEnabled
      await apiClient.updateIntercommunicationSetting(newValue)
      setIntercommunicationEnabled(newValue)
      console.log(`Intercommunication ${newValue ? 'enabled' : 'disabled'}`)
    } catch (error) {
      console.error("Failed to toggle intercommunication:", error)
    }
  }

    return (
    <div className="p-6 space-y-6 relative">

      {/* Beta Disclaimer */}
      <div className="flex justify-center">
        <div className="bg-yellow-50 border border-yellow-200 rounded-full px-6 py-3 animate-pulse">
            <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-yellow-600" />
            <p className="text-sm text-yellow-800">
              This is still in beta, so the AI can make mistakes sometimes.
            </p>
              </div>
              </div>
            </div>


      {/* Welcome Section */}
        <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
          {user?.created_at && new Date(user.created_at).getTime() > Date.now() - 24 * 60 * 60 * 1000 
            ? `Welcome, ${user?.username || user?.name || "User"}! 👋`
            : `Welcome back, ${user?.username || user?.name || "User"}! 👋`
          }
        </h1>
          </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 lg:gap-6">
        {isLoading && userAgents.length === 0 ? (
          <>
            {[...Array(4)].map((_, i) => (
              <Card key={i}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-4 w-4 rounded" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-8 w-16 mb-2" />
                  <Skeleton className="h-3 w-32" />
                </CardContent>
              </Card>
            ))}
          </>
        ) : (
          <>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active Agents</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{userAgents.filter(agent => agent.status === "active").length}</div>
                <p className="text-xs text-muted-foreground">All systems operational</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active Tasks</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{activeTasks.length}</div>
                <p className="text-xs text-muted-foreground">{activeTasks.length} in progress</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Completed Tasks</CardTitle>
                <CheckCircle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{taskSummaries.length}</div>
                <p className="text-xs text-muted-foreground">No completions yet</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">0%</div>
                <p className="text-xs text-muted-foreground">Task completion rate</p>
              </CardContent>
            </Card>
          </>
        )}
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 gap-6">
        {/* Chat Interface - Full Width */}
        <div>
          <Card className="h-[500px] sm:h-[600px] flex flex-col overflow-hidden">
            {/* Modern Chat Header */}
            <div className="bg-gradient-to-r from-green-400 to-green-600 px-4 sm:px-6 py-4">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
                  {selectedAgent ? (
                    <>
                      <div className={`w-10 h-10 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center ring-2 ring-white/30 flex-shrink-0`}>
                        <selectedAgent.icon className="w-5 h-5 text-white" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <h3 className="text-base sm:text-lg font-bold text-white truncate">{selectedAgent.name}</h3>
                        <div className="text-xs sm:text-sm text-white/90 flex items-center">
                          <motion.div 
                            className="w-2 h-2 rounded-full bg-white mr-2"
                            animate={{ opacity: [1, 0.5, 1] }}
                            transition={{ duration: 2, repeat: Infinity }}
                          />
                          {selectedAgent.title}
                        </div>
                      </div>
                    </>
                  ) : (
                    <div>
                      <h3 className="text-base sm:text-lg font-bold text-white">Agent47 Chat</h3>
                      <p className="text-xs sm:text-sm text-white/90">Select an agent to start</p>
                    </div>
                  )}
                </div>
                {chatMessages.length > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleClearChat}
                    className="text-white hover:bg-white/20 flex-shrink-0"
                  >
                    <Trash2 className="w-4 h-4 sm:mr-2" />
                    <span className="hidden sm:inline">Clear</span>
                  </Button>
                )}
              </div>
            </div>
            <CardContent className="flex-1 flex flex-col p-0 bg-gray-50/50">
        {/* Chat Messages */}
              <div className="flex-1 overflow-y-auto space-y-4 p-4">
            {chatMessages.length === 0 ? (
                  <div className="text-center text-gray-500 py-12">
                    <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p className="text-sm">
                      {selectedAgent 
                        ? `Start a conversation with ${selectedAgent.name}`
                        : "Please select an agent to start chatting"
                      }
                    </p>
              </div>
            ) : (
                  chatMessages.map((msg) => {
                    const agent = msg.agentId ? agents.find(a => a.id === msg.agentId) : null
                    const isUserMessage = msg.type === "user"
                    const isSystemMessage = msg.type === "system"
                    const isThinking = msg.type === "thinking"
                    
                    // Get agent color gradient
                    const getAgentColor = () => {
                      if (!agent) return "from-gray-400 to-gray-600"
                      const colorMap: Record<string, string> = {
                        "bg-orange-500": "from-orange-400 to-orange-600",
                        "bg-purple-500": "from-purple-400 to-purple-600",
                        "bg-amber-500": "from-amber-400 to-amber-600",
                        "bg-pink-500": "from-pink-400 to-pink-600",
                        "bg-green-500": "from-green-400 to-green-600",
                        "bg-blue-500": "from-blue-400 to-blue-600",
                        "bg-indigo-500": "from-indigo-400 to-indigo-600",
                      }
                      return colorMap[agent.color] || "from-gray-400 to-gray-600"
                    }
                    
                    return (
                      <div
                        key={msg.id}
                        className={`flex ${isUserMessage ? "justify-end" : isSystemMessage ? "justify-center" : "justify-start"} group`}
                      >
                        {isSystemMessage ? (
                          <div className="bg-green-50 border border-green-200 rounded-xl px-4 py-2.5 text-sm text-green-700 max-w-[85%] shadow-sm">
                            <div className="prose prose-sm max-w-none text-center">
                              <ReactMarkdown
                                remarkPlugins={[remarkGfm]}
                                className="text-sm"
                                components={{
                                  p: ({ children }) => <p className="mb-1 last:mb-0 text-green-700">{children}</p>,
                                  strong: ({ children }) => <strong className="font-semibold text-green-800">{children}</strong>,
                                  em: ({ children }) => <em className="italic text-green-800">{children}</em>,
                                  code: ({ children }) => <code className="bg-green-100 px-1.5 py-0.5 rounded text-xs text-green-800 font-mono">{children}</code>,
                                }}
                              >
                                {msg.content}
                              </ReactMarkdown>
                            </div>
                          </div>
                        ) : (
                          <div className={`flex items-end gap-2 max-w-[80%] ${isUserMessage ? "flex-row-reverse" : ""}`}>
                            {/* Avatar */}
                            {(msg.type === "agent" || msg.type === "thinking") && agent && (
                              <div className={`w-9 h-9 rounded-full bg-gradient-to-r ${getAgentColor()} flex items-center justify-center text-white text-xs font-bold shadow-md flex-shrink-0 ${
                                isThinking ? "animate-pulse" : ""
                              }`}>
                                {agent.name.slice(0, 2).toUpperCase()}
                              </div>
                            )}
                            {isUserMessage && (
                              <div className="w-9 h-9 rounded-full bg-gradient-to-r from-green-400 to-green-600 flex items-center justify-center text-white shadow-md flex-shrink-0">
                                <User className="w-4 h-4" />
                              </div>
                            )}
                            
                            {/* Message Bubble */}
                            <div className="flex flex-col">
                              {(msg.type === "agent" || msg.type === "thinking") && agent && (
                                <span className="text-xs font-semibold mb-1 px-1 text-gray-600">
                                  {agent.name}
                                </span>
                              )}
                              
                              {isThinking ? (
                                <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3 shadow-sm">
                                  <div className="flex items-center gap-2 mb-2">
                                    <div className="flex space-x-1">
                                      {[0, 1, 2].map((dot) => (
                                        <motion.div
                                          key={dot}
                                          className="w-1.5 h-1.5 bg-gray-400 rounded-full"
                                          animate={{ 
                                            opacity: [0.3, 1, 0.3],
                                            scale: [1, 1.2, 1]
                                          }}
                                          transition={{
                                            duration: 1.5,
                                            repeat: Infinity,
                                            delay: dot * 0.2,
                                          }}
                                        />
                                      ))}
                                    </div>
                                    <span className="text-xs text-gray-500 italic">{msg.content}</span>
                                  </div>
                                  
                                  {/* Thinking Steps */}
                                  {msg.thinkingSteps && msg.thinkingSteps.length > 0 && (
                                    <div className="space-y-1.5 pt-2 border-t border-gray-100">
                                      {msg.thinkingSteps.map((step: string, stepIndex: number) => (
                                        <motion.div
                                          key={stepIndex}
                                          className="flex items-start gap-2 text-xs text-gray-600"
                                          initial={{ opacity: 0, x: -10 }}
                                          animate={{ 
                                            opacity: 1,
                                            x: 0
                                          }}
                                          transition={{ duration: 0.3, delay: stepIndex * 0.4 }}
                                        >
                                          <motion.div
                                            className="w-1.5 h-1.5 rounded-full bg-green-500 mt-1.5 flex-shrink-0"
                                            animate={{
                                              scale: [1, 1.3, 1],
                                              opacity: [0.5, 1, 0.5]
                                            }}
                                            transition={{ duration: 1, repeat: Infinity }}
                                          />
                                          <span className="leading-relaxed">{step}</span>
                                        </motion.div>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              ) : (
                                <div className="relative group/message">
                                  <div
                                    className={`rounded-2xl px-4 py-3 shadow-sm ${
                                      isUserMessage
                                        ? "bg-gradient-to-br from-green-400 to-green-600 text-white"
                                        : "bg-white border border-gray-200 text-gray-800"
                                    }`}
                                  >
                                    {msg.isVoice && (
                                      <div className="flex items-center gap-2 mb-2 pb-2 border-b border-white/20">
                                        <Mic className="w-3.5 h-3.5" />
                                        <span className="text-xs font-medium opacity-90">Voice Message</span>
                                      </div>
                                    )}
                                    
                                    {/* Message Actions */}
                                    <div className={`absolute ${isUserMessage ? 'left-2' : 'right-2'} -top-2 opacity-0 group-hover/message:opacity-100 transition-opacity z-10`}>
                                      <DropdownMenu>
                                        <DropdownMenuTrigger asChild>
                                          <Button
                                            variant="ghost"
                                            size="sm"
                                            className="h-6 w-6 p-0 bg-white shadow-md hover:bg-gray-100"
                                          >
                                            <MoreVertical className="h-3 w-3" />
                                          </Button>
                                        </DropdownMenuTrigger>
                                        <DropdownMenuContent align={isUserMessage ? "end" : "start"}>
                                          <DropdownMenuItem onClick={() => handleCopyMessage(msg.content)}>
                                            <Copy className="w-4 h-4 mr-2" />
                                            Copy
                                          </DropdownMenuItem>
                                          <DropdownMenuItem 
                                            onClick={() => handleDeleteMessage(msg.id)}
                                            className="text-red-600"
                                          >
                                            <Trash2 className="w-4 h-4 mr-2" />
                                            Delete
                                          </DropdownMenuItem>
                                        </DropdownMenuContent>
                                      </DropdownMenu>
                                    </div>

                                    {/* Message Content */}
                                    <div className="prose prose-sm max-w-none">
                                      {msg.type === "agent" || msg.type === "system" ? (
                                        <ReactMarkdown
                                          remarkPlugins={[remarkGfm]}
                                          className="text-sm"
                                          components={{
                                            p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                                            ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
                                            ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
                                            li: ({ children }) => <li className="ml-2">{children}</li>,
                                            code: ({ children, className }) => {
                                              const isInline = !className
                                              return isInline ? (
                                                <code className="bg-gray-200 px-1.5 py-0.5 rounded text-xs font-mono text-gray-800">{children}</code>
                                              ) : (
                                                <code className="block bg-gray-200 p-2 rounded text-xs font-mono text-gray-800 overflow-x-auto mb-2 border border-gray-300">{children}</code>
                                              )
                                            },
                                            pre: ({ children }) => <pre className="bg-gray-200 p-2 rounded text-xs font-mono text-gray-800 overflow-x-auto mb-2 border border-gray-300">{children}</pre>,
                                            a: ({ children, href }) => (
                                              <a href={href} target="_blank" rel="noopener noreferrer" className="underline text-green-600 hover:text-green-700">
                                                {children}
                                              </a>
                                            ),
                                            strong: ({ children }) => <strong className="font-semibold text-gray-900">{children}</strong>,
                                            em: ({ children }) => <em className="italic text-gray-700">{children}</em>,
                                            h1: ({ children }) => <h1 className="text-lg font-bold text-gray-900 mb-2">{children}</h1>,
                                            h2: ({ children }) => <h2 className="text-base font-bold text-gray-900 mb-2">{children}</h2>,
                                            h3: ({ children }) => <h3 className="text-sm font-bold text-gray-900 mb-1">{children}</h3>,
                                            blockquote: ({ children }) => <blockquote className="border-l-4 border-green-500 pl-3 italic text-gray-700 my-2">{children}</blockquote>,
                                          }}
                                        >
                                          {msg.content}
                                        </ReactMarkdown>
                                      ) : (
                                        <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                                      )}
                                    </div>
                                    
                                    {/* Display generated images */}
                                    {msg.imageUrl && (
                                      <div className="mt-3 rounded-lg overflow-hidden border border-gray-300 max-w-md">
                                        <img
                                          src={msg.imageUrl}
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
                                          href={msg.imageUrl}
                                          target="_blank"
                                          rel="noopener noreferrer"
                                          className="hidden text-green-600 hover:text-green-700 flex items-center space-x-2 p-2 bg-gray-50 text-sm"
                                        >
                                          <span>View Image</span>
                                        </a>
                                      </div>
                                    )}
                                    
                                    <p className={`text-xs mt-1.5 ${
                                      isUserMessage 
                                        ? "text-white/70" 
                                        : "text-gray-500"
                                    }`}>
                                      {msg.timestamp.toLocaleTimeString()}
                                    </p>
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    )
                  })
                )}
                {isLoading && selectedAgent && (
                  <div className="flex justify-start items-center gap-2">
                    <div className={`w-9 h-9 rounded-full bg-gradient-to-r ${
                      selectedAgent.color === "bg-orange-500" ? "from-orange-400 to-orange-600" :
                      selectedAgent.color === "bg-purple-500" ? "from-purple-400 to-purple-600" :
                      selectedAgent.color === "bg-amber-500" ? "from-amber-400 to-amber-600" :
                      selectedAgent.color === "bg-pink-500" ? "from-pink-400 to-pink-600" :
                      selectedAgent.color === "bg-green-500" ? "from-green-400 to-green-600" :
                      selectedAgent.color === "bg-blue-500" ? "from-blue-400 to-blue-600" :
                      selectedAgent.color === "bg-indigo-500" ? "from-indigo-400 to-indigo-600" :
                      "from-green-400 to-green-600"
                    } flex items-center justify-center text-white text-xs font-bold shadow-md`}>
                      {selectedAgent.name.slice(0, 2).toUpperCase()}
                    </div>
                    <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3 shadow-sm">
                      <div className="flex space-x-1.5">
                        {[0, 1, 2].map((i) => (
                          <motion.div
                            key={i}
                            className="w-2 h-2 bg-green-500 rounded-full"
                            animate={{ 
                              y: [0, -6, 0],
                              opacity: [0.5, 1, 0.5]
                            }}
                            transition={{
                              duration: 1.2,
                              repeat: Infinity,
                              delay: i * 0.15,
                            }}
                          />
                        ))}
                      </div>
                    </div>
                  </div>
            )}
            <div ref={messagesEndRef} />
        </div>

        {/* Chat Input Area */}
              <div className="bg-white border-t border-gray-200 px-4 py-4 space-y-2">
                <div className="flex items-center gap-2 sm:gap-3">
                  {/* File Upload */}
                  <label htmlFor="file-upload" className="flex-shrink-0">
                    <Button variant="outline" size="sm" asChild disabled={userAgents.length === 0} className="h-9 w-9 p-0">
                      <span>
                        <Upload className="w-4 h-4" />
                      </span>
                    </Button>
                  </label>
                  <input
                    id="file-upload"
                    type="file"
                    className="hidden"
                    onChange={handleFileUpload}
                  />
                  
                  {/* Agent Selector */}
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="outline" size="sm" disabled={userAgents.length === 0} className="h-9 px-2 sm:px-3">
                        <Bot className="w-4 h-4 sm:mr-2" />
                        <span className="hidden sm:inline">Agents</span>
                        <ChevronDown className="w-4 h-4 sm:ml-2" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="start" className="w-72 sm:w-80">
                      <DropdownMenuLabel>Select Agent</DropdownMenuLabel>
                      <DropdownMenuSeparator />
                      {userAgents.length > 0 ? (
                        userAgents.map((userAgent) => {
                          const agent = agents.find(a => a.id === userAgent.agent_id)
                          if (!agent) return null
                          return (
                            <DropdownMenuItem
                              key={agent.id}
                              onClick={() => handleAgentSwitch(agent.id)}
                              className="flex items-center gap-3 p-3"
                            >
                              <div className={`w-8 h-8 rounded-full ${agent.color} flex items-center justify-center flex-shrink-0`}>
                                <agent.icon className="w-4 h-4 text-white" />
                              </div>
                              <div className="flex-1 min-w-0">
                                <p className="font-medium truncate">{agent.name}</p>
                                <p className="text-xs text-gray-500 truncate">{agent.title}</p>
                              </div>
                            </DropdownMenuItem>
                          )
                        })
                      ) : (
                        <DropdownMenuItem disabled className="text-center text-gray-500">
                          No agents selected. Please select agents first.
                        </DropdownMenuItem>
                      )}
                      <DropdownMenuSeparator />
                      <DropdownMenuItem 
                        className="flex items-center gap-2 p-3"
                        onClick={() => handleIntercommunicate()}
                        disabled={!canUseIntercommunication}
                      >
                        <Network className="w-4 h-4 flex-shrink-0" />
                        <span className="text-sm">
                          {intercommunicationEnabled ? "Disable Intercommunication" : "Enable Intercommunication"}
                        </span>
                        {!canUseIntercommunication && (
                          <Badge variant="outline" className="ml-auto text-xs flex-shrink-0">
                            Upgrade Required
                          </Badge>
                        )}
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                  
                  {/* Message Input */}
                  <div className="flex-1 relative">
                    <Input
                      value={message}
                      onChange={(e) => setMessage(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder={isRecording ? "Listening..." : userAgents.length === 0 ? "Select agents first..." : "Type a message or use voice..."}
                      className="pr-20 sm:pr-24 text-sm bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent"
                      disabled={isLoading || userAgents.length === 0}
                    />
                    {isRecording && (
                      <motion.div
                        className="absolute right-12 top-1/2 -translate-y-1/2"
                        animate={{ scale: [1, 1.2, 1] }}
                        transition={{ duration: 1, repeat: Infinity }}
                      >
                        <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                      </motion.div>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={isRecording ? stopRecording : startRecording}
                      disabled={userAgents.length === 0}
                      className={`absolute right-2 top-1/2 transform -translate-y-1/2 h-7 w-7 p-0 ${
                        isRecording 
                          ? "bg-red-500 text-white hover:bg-red-600" 
                          : "hover:bg-gray-100"
                      }`}
                    >
                      {isRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                    </Button>
                  </div>
                  
                  {/* Send Button */}
                  <motion.button
                    type="button"
                    onClick={handleSendMessage}
                    disabled={isLoading || !message.trim() || userAgents.length === 0}
                    className={`h-9 px-3 sm:px-4 rounded-xl transition-all duration-300 flex items-center justify-center flex-shrink-0 ${
                      isRecording
                        ? "bg-red-500 text-white shadow-lg shadow-red-500/50"
                        : "bg-gradient-to-r from-green-400 to-green-600 text-white hover:shadow-lg hover:shadow-green-500/30"
                    } disabled:opacity-50 disabled:cursor-not-allowed`}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    {isRecording ? (
                      <Mic className="w-5 h-5" />
                    ) : (
                      <>
                        <Send className="w-4 h-4 sm:w-5 sm:h-5" />
                        <span className="hidden sm:inline ml-2">Send</span>
                      </>
                    )}
                  </motion.button>
                </div>
                
                {/* Voice Status Indicator */}
                {isRecording && (
                  <motion.div
                    className="flex items-center justify-center gap-2 text-red-600 text-xs font-medium"
                    initial={{ opacity: 0, y: -5 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -5 }}
                  >
                    <motion.div
                      animate={{ scale: [1, 1.3, 1] }}
                      transition={{ duration: 1, repeat: Infinity }}
                    >
                      <Mic className="w-4 h-4" />
                    </motion.div>
                    <span>Recording voice message...</span>
                  </motion.div>
                )}
                
                <div className="flex items-center justify-center pt-2">
                  <p className="text-xs text-gray-500 text-center">
                    The AI can make mistakes sometimes
                  </p>
                </div>
                </div>
              </CardContent>
            </Card>
      </div>

                    </div>

      {/* Tasks Section Removed - Chat tab should fill the space fully */}

      {/* Agent Selection Modal */}
      {showAgentSelection && (
      <AgentSelectionModal
        isOpen={showAgentSelection}
        onClose={() => setShowAgentSelection(false)}
          onConfirm={handleAgentSelectionComplete}
          userTier={user?.tier || "free"}
        />
      )}
    </div>
  )
}
