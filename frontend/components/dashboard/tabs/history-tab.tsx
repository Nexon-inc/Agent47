"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Clock,
  Search,
  MessageSquare,
  CheckCircle,
  Globe,
  Headphones,
  FileText,
  DollarSign,
  Megaphone,
  Lightbulb,
  Calendar,
  Bot,
  ChevronRight,
  RefreshCw,
  Loader2,
  Download,
  Filter,
  User,
} from "lucide-react"
import { apiClient } from "@/lib/api-client"
import { useAuthStore } from "@/lib/stores/auth-store"
import { useToast } from "@/hooks/use-toast"
import { SkeletonList } from "@/components/dashboard/skeletons"
import EmptyState, { EmptyStates } from "@/components/dashboard/empty-state"
import { History } from "lucide-react"

// Mock data removed - only real user data will be displayed

interface Conversation {
  id: string
  agent: string
  icon: any
  color: string
  bgColor: string
  title: string
  lastMessage: string
  timestamp: string
  status: string
  messageCount: number
  messages: Array<{
    type: string
    content: string
    time: string
  }>
}

interface Task {
  id: string
  agent: string
  icon: any
  color: string
  task: string
  timestamp: string
  status: string
  details: string
}

export default function HistoryTab() {
  const { user } = useAuthStore()
  const { toast } = useToast()
  const [searchTerm, setSearchTerm] = useState("")
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState("")
  const [selectedAgent, setSelectedAgent] = useState("all")
  const [selectedStatus, setSelectedStatus] = useState("all")
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null)

  // Data states
  const [conversationHistory, setConversationHistory] = useState<Conversation[]>([])
  const [taskHistory, setTaskHistory] = useState<Task[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  // Account and navigation history
  const [accountHistory, setAccountHistory] = useState<any[]>([])
  const [navigationHistory, setNavigationHistory] = useState<any[]>([])

  // Agent icons mapping
  const agentIcons = {
    aria: Globe,
    clara: Headphones,
    eric: DollarSign,
    jackie: Megaphone,
    shakes: FileText,
    joe: Search,
    purity: Lightbulb,
  }

  const agentColors = {
    aria: { color: "text-orange-500", bgColor: "bg-orange-500" },
    clara: { color: "text-purple-500", bgColor: "bg-purple-500" },
    eric: { color: "text-amber-500", bgColor: "bg-amber-500" },
    jackie: { color: "text-pink-500", bgColor: "bg-pink-500" },
    shakes: { color: "text-green-500", bgColor: "bg-green-500" },
    joe: { color: "text-blue-500", bgColor: "bg-blue-500" },
    purity: { color: "text-indigo-500", bgColor: "bg-indigo-500" },
  }

  // Debounce search term
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm)
    }, 300)
    return () => clearTimeout(timer)
  }, [searchTerm])

  // Load history data
  useEffect(() => {
    loadHistoryData()
    loadAccountHistory()
    loadNavigationHistory()
  }, [])

  // Subscribe to real-time task updates via WebSocket
  useEffect(() => {
    const { websocketService } = require('@/lib/websocket-service')

    if (!websocketService.getConnectionStatus()) {
      websocketService.connect()
    }

    // Reload history when tasks are completed or updated
    const unsubscribe = websocketService.subscribe('task_update', (message) => {
      if (message.data?.status === 'completed' || message.data?.status === 'in_progress') {
        loadHistoryData()
      }
    })

    return () => unsubscribe()
  }, [])

  const loadAccountHistory = () => {
    // Load account creation and signup history
    if (user) {
      const history: any[] = []

      // Account created event
      if (user.created_at) {
        history.push({
          id: `account_created_${user.id}`,
          type: "account",
          event: "Account Created",
          description: `Account created with email ${user.email}`,
          timestamp: new Date(user.created_at),
          icon: "📝",
          details: {
            email: user.email,
            tier: user.tier,
            username: user.username
          }
        })
      }

      // Last login event
      if (user.last_login) {
        history.push({
          id: `last_login_${user.id}`,
          type: "account",
          event: "Last Login",
          description: "You logged in to your account",
          timestamp: new Date(user.last_login),
          icon: "🔐",
          details: {}
        })
      }

      // Onboarding completed event
      if (user.onboarding_completed) {
        history.push({
          id: `onboarding_${user.id}`,
          type: "account",
          event: "Onboarding Completed",
          description: "You completed your account onboarding",
          timestamp: user.onboarding_completed_at ? new Date(user.onboarding_completed_at) : new Date(user.created_at),
          icon: "✅",
          details: user.onboarding_data
        })
      }

      // Sort by timestamp (newest first)
      history.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
      setAccountHistory(history)
    }
  }

  const loadNavigationHistory = () => {
    // Track navigation to different tabs and pages
    try {
      const stored = localStorage.getItem('navigationHistory')
      const history = stored ? JSON.parse(stored) : []
      setNavigationHistory(history)
    } catch (error) {
      console.error("Failed to load navigation history:", error)
      setNavigationHistory([])
    }
  }

  const trackNavigation = (tabName: string) => {
    // Record tab visit
    const currentHistory = navigationHistory || []
    const newEntry = {
      id: `${tabName}_${Date.now()}`,
      tab: tabName,
      timestamp: new Date(),
      icon: getTabIcon(tabName)
    }

    const updated = [newEntry, ...currentHistory].slice(0, 50) // Keep last 50 navigation items
    setNavigationHistory(updated)
    localStorage.setItem('navigationHistory', JSON.stringify(updated))
  }

  const getTabIcon = (tabName: string) => {
    const icons: Record<string, string> = {
      home: "🏠",
      agents: "🤖",
      platforms: "🌐",
      tools: "🔧",
      history: "📋",
      inbox: "📬",
      calendar: "📅",
      settings: "⚙️",
      account: "👤",
    }
    return icons[tabName] || "📍"
  }

  const loadHistoryData = async () => {
    try {
      setIsLoading(true)
      setIsRefreshing(true)

      // Load tasks and summaries to create history
      const [tasksResponse, summariesResponse] = await Promise.all([
        apiClient.get("/api/intercommunication/tasks"),
        apiClient.get("/api/intercommunication/summaries")
      ])

      const tasks = tasksResponse.data
      const summaries = summariesResponse.data

      // Create conversation history from tasks
      const conversations: Conversation[] = []
      const taskHistoryData: Task[] = []

      // Group tasks by conversation/session
      const taskGroups = new Map<string, any[]>()
      tasks.forEach((task: any) => {
        const key = `${task.agent_id}_${task.user_id}_${new Date(task.created_at).toDateString()}`
        if (!taskGroups.has(key)) {
          taskGroups.set(key, [])
        }
        taskGroups.get(key)!.push(task)
      })

      // Create conversations from task groups
      taskGroups.forEach((groupTasks, key) => {
        const firstTask = groupTasks[0]
        const agentId = firstTask.agent_id
        const agentName = agentId.charAt(0).toUpperCase() + agentId.slice(1)

        // Find corresponding summary
        const summary = summaries.find((s: any) =>
          s.agent_id === agentId &&
          new Date(s.created_at).toDateString() === new Date(firstTask.created_at).toDateString()
        )

        const conversation: Conversation = {
          id: key,
          agent: agentName,
          icon: agentIcons[agentId as keyof typeof agentIcons] || Bot,
          color: agentColors[agentId as keyof typeof agentColors]?.color || "text-gray-500",
          bgColor: agentColors[agentId as keyof typeof agentColors]?.bgColor || "bg-gray-500",
          title: summary?.title || `${agentName} Session`,
          lastMessage: summary?.summary || "Task completed successfully",
          timestamp: formatTimeAgo(new Date(firstTask.updated_at)),
          status: groupTasks.some(t => t.status === "completed") ? "completed" : "in-progress",
          messageCount: groupTasks.length,
          messages: groupTasks.map((task: any) => ({
            type: "agent",
            content: task.description || task.title,
            time: new Date(task.created_at).toLocaleTimeString()
          }))
        }

        conversations.push(conversation)
      })

      // Create task history from individual tasks
      tasks.forEach((task: any) => {
        const agentId = task.agent_id
        const agentName = agentId.charAt(0).toUpperCase() + agentId.slice(1)

        const taskItem: Task = {
          id: task.id,
          agent: agentName,
          icon: agentIcons[agentId as keyof typeof agentIcons] || Bot,
          color: agentColors[agentId as keyof typeof agentColors]?.bgColor || "bg-gray-500",
          task: task.title,
          timestamp: formatTimeAgo(new Date(task.updated_at)),
          status: task.status,
          details: task.description || "Task completed"
        }

        taskHistoryData.push(taskItem)
      })

      // Sort by timestamp (newest first)
      conversations.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      taskHistoryData.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())

      setConversationHistory(conversations)
      setTaskHistory(taskHistoryData)
      setLastUpdated(new Date())

    } catch (error) {
      console.error("Failed to load history data:", error)
      // Generate fallback data
      generateFallbackData()
    } finally {
      setIsLoading(false)
      setIsRefreshing(false)
    }
  }

  const generateFallbackData = () => {
    // Set empty data instead of using mock data
    // This ensures we don't show fake data when API fails
    setConversationHistory([])
    setTaskHistory([])
    setLastUpdated(new Date())
  }

  const formatTimeAgo = (date: Date): string => {
    const now = new Date()
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)

    if (diffInSeconds < 60) return "Just now"
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`
    if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)} days ago`
    return date.toLocaleDateString()
  }

  const handleRefresh = () => {
    loadHistoryData()
  }

  const handleExport = async () => {
    try {
      // Export conversation history
      const conversationsData = filteredConversations.map(conv => ({
        id: conv.id,
        agent: conv.agent,
        title: conv.title,
        status: conv.status,
        messageCount: conv.messageCount,
        timestamp: conv.timestamp,
        lastMessage: conv.lastMessage
      }))

      // Also include task history
      const tasksData = filteredTasks.map(task => ({
        id: task.id,
        agent: task.agent,
        task: task.task,
        status: task.status,
        timestamp: task.timestamp,
        details: task.details
      }))

      const csvContent = [
        "Type,Agent,Title/Task,Status,Messages,Timestamp,Details",
        ...conversationsData.map(conv =>
          `"Conversation","${conv.agent}","${conv.title}","${conv.status}",${conv.messageCount},"${conv.timestamp}","${conv.lastMessage}"`
        ),
        ...tasksData.map(task =>
          `"Task","${task.agent}","${task.task}","${task.status}",,"${task.timestamp}","${task.details}"`
        )
      ].join("\n")

      const blob = new Blob([csvContent], { type: 'text/csv' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `history-export-${new Date().toISOString().split('T')[0]}.csv`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      toast({
        title: "Export successful",
        description: "History exported to CSV file",
      })
    } catch (error) {
      console.error("Failed to export history:", error)
      toast({
        title: "Export failed",
        description: "Failed to export history. Please try again.",
        variant: "destructive",
      })
    }
  }

  const filteredConversations = conversationHistory.filter((conv) => {
    const matchesSearch =
      conv.title.toLowerCase().includes(debouncedSearchTerm.toLowerCase()) ||
      conv.agent.toLowerCase().includes(debouncedSearchTerm.toLowerCase())
    const matchesAgent = selectedAgent === "all" || conv.agent.toLowerCase() === selectedAgent
    const matchesStatus = selectedStatus === "all" || conv.status === selectedStatus

    return matchesSearch && matchesAgent && matchesStatus
  })

  const filteredTasks = taskHistory.filter((task) => {
    const matchesSearch =
      task.task.toLowerCase().includes(debouncedSearchTerm.toLowerCase()) ||
      task.agent.toLowerCase().includes(debouncedSearchTerm.toLowerCase())
    const matchesAgent = selectedAgent === "all" || task.agent.toLowerCase() === selectedAgent
    const matchesStatus = selectedStatus === "all" || task.status === selectedStatus

    return matchesSearch && matchesAgent && matchesStatus
  })

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 ">History</h1>
          <p className="text-gray-600  mt-1">
            View your conversation and task history with your AI workforce
            {lastUpdated && (
              <span className="ml-2 text-sm text-gray-500">
                Last updated: {lastUpdated.toLocaleTimeString()}
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button variant="outline" size="sm" onClick={handleExport}>
            <Download className="w-4 h-4 mr-2" />
            Export History
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                placeholder="Search conversations and tasks..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={selectedAgent} onValueChange={setSelectedAgent}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by agent" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Personnel</SelectItem>
                <SelectItem value="aria">Aria</SelectItem>
                <SelectItem value="clara">Clara</SelectItem>
                <SelectItem value="eric">Eric</SelectItem>
                <SelectItem value="jackie">Jackie</SelectItem>
                <SelectItem value="shakes">Shakes</SelectItem>
                <SelectItem value="joe">Joe</SelectItem>
                <SelectItem value="purity">Purity</SelectItem>
              </SelectContent>
            </Select>
            <Select value={selectedStatus} onValueChange={setSelectedStatus}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="in-progress">In Progress</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* History Tabs */}
      <Tabs defaultValue="conversations" className="space-y-6">
        <TabsList>
          <TabsTrigger value="conversations">
            <MessageSquare className="w-4 h-4 mr-2" />
            Conversations ({filteredConversations.length})
          </TabsTrigger>
          <TabsTrigger value="tasks">
            <CheckCircle className="w-4 h-4 mr-2" />
            Tasks ({filteredTasks.length})
          </TabsTrigger>
          <TabsTrigger value="account">
            <User className="w-4 h-4 mr-2" />
            Account Activity ({accountHistory.length})
          </TabsTrigger>
          <TabsTrigger value="navigation">
            <Globe className="w-4 h-4 mr-2" />
            Navigation ({navigationHistory.length})
          </TabsTrigger>
        </TabsList>

        {/* Account Activity Tab */}
        <TabsContent value="account" className="space-y-4">
          {accountHistory.length === 0 ? (
            <EmptyState
              icon={User}
              title="No Account Activity"
              description="Your account activities will appear here"
            />
          ) : (
            <div className="space-y-4">
              {accountHistory.map((activity) => (
                <Card key={activity.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-start gap-4">
                      <div className="text-2xl">{activity.icon}</div>
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-900">{activity.event}</h3>
                        <p className="text-sm text-gray-600 mt-1">{activity.description}</p>
                        {Object.keys(activity.details || {}).length > 0 && (
                          <div className="mt-3 p-3 bg-gray-50 rounded text-xs space-y-1">
                            {Object.entries(activity.details).map(([key, value]: [string, any]) => (
                              <div key={key} className="flex items-center justify-between">
                                <span className="text-gray-600 capitalize">{key}:</span>
                                <span className="font-medium text-gray-900">
                                  {typeof value === 'object' ? JSON.stringify(value).substring(0, 50) : String(value)}
                                </span>
                              </div>
                            ))}
                          </div>
                        )}
                        <span className="text-xs text-gray-500 mt-2 block">
                          {activity.timestamp instanceof Date
                            ? activity.timestamp.toLocaleString()
                            : new Date(activity.timestamp).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Navigation History Tab */}
        <TabsContent value="navigation" className="space-y-4">
          {navigationHistory.length === 0 ? (
            <EmptyState
              icon={Globe}
              title="No Navigation History"
              description="Your tab visits will be tracked here as you navigate"
            />
          ) : (
            <div className="space-y-4">
              {navigationHistory.map((nav, index) => (
                <Card key={nav.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">{nav.icon}</span>
                        <div>
                          <h3 className="font-semibold text-gray-900 capitalize">{nav.tab}</h3>
                          <p className="text-sm text-gray-500">Visit #{navigationHistory.length - index}</p>
                        </div>
                      </div>
                      <span className="text-sm text-gray-500">
                        {nav.timestamp instanceof Date
                          ? nav.timestamp.toLocaleTimeString()
                          : new Date(nav.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="conversations" className="space-y-4">
          {isLoading ? (
            <SkeletonList items={5} />
          ) : filteredConversations.length === 0 ? (
            <EmptyState
              icon={History}
              title={EmptyStates.noHistory.title}
              description={debouncedSearchTerm || selectedAgent !== "all" || selectedStatus !== "all"
                ? "Try adjusting your search or filter criteria"
                : EmptyStates.noHistory.description}
              action={debouncedSearchTerm || selectedAgent !== "all" || selectedStatus !== "all" ? {
                label: "Clear Filters",
                onClick: () => {
                  setSearchTerm("")
                  setSelectedAgent("all")
                  setSelectedStatus("all")
                }
              } : undefined}
            />
          ) : (
            <div className="space-y-4">
              {filteredConversations.map((conversation) => (
                <Card key={conversation.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div
                          className={`w-10 h-10 rounded-full ${conversation.bgColor} flex items-center justify-center`}
                        >
                          <conversation.icon className="w-5 h-5 text-white" />
                        </div>
                        <div className="flex-1">
                          <h3 className="font-semibold text-gray-900">{conversation.title}</h3>
                          <p className="text-sm text-gray-500 mt-1">{conversation.lastMessage}</p>
                          <div className="flex items-center gap-4 mt-2">
                            <span className="text-xs text-gray-400 flex items-center">
                              <Bot className="w-3 h-3 mr-1" />
                              {conversation.agent}
                            </span>
                            <span className="text-xs text-gray-400 flex items-center">
                              <MessageSquare className="w-3 h-3 mr-1" />
                              {conversation.messageCount} messages
                            </span>
                            <span className="text-xs text-gray-400 flex items-center">
                              <Clock className="w-3 h-3 mr-1" />
                              {conversation.timestamp}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-3">
                        <Badge
                          variant="outline"
                          className={
                            conversation.status === "completed"
                              ? "bg-green-50 text-green-700 border-green-200"
                              : "bg-yellow-50 text-yellow-700 border-yellow-200"
                          }
                        >
                          <CheckCircle className="w-3 h-3 mr-1" />
                          {conversation.status}
                        </Badge>
                        <Dialog>
                          <DialogTrigger asChild>
                            <Button variant="outline" size="sm">
                              <ChevronRight className="w-4 h-4" />
                            </Button>
                          </DialogTrigger>
                          <DialogContent className="max-w-2xl max-h-[80vh]">
                            <DialogHeader>
                              <DialogTitle className="flex items-center gap-3">
                                <div
                                  className={`w-8 h-8 rounded-full ${conversation.bgColor} flex items-center justify-center`}
                                >
                                  <conversation.icon className="w-4 h-4 text-white" />
                                </div>
                                {conversation.title}
                              </DialogTitle>
                              <DialogDescription>
                                Conversation with {conversation.agent} • {conversation.timestamp}
                              </DialogDescription>
                            </DialogHeader>
                            <ScrollArea className="h-96 w-full border rounded-lg p-4">
                              <div className="space-y-4">
                                {conversation.messages.map((msg, index) => (
                                  <div
                                    key={index}
                                    className={`flex ${msg.type === "user" ? "justify-end" : "justify-start"}`}
                                  >
                                    <div
                                      className={`max-w-[80%] rounded-lg p-3 ${msg.type === "user" ? "bg-gradient-to-br from-green-400 to-green-600 text-white" : "bg-gray-50 border"
                                        }`}
                                    >
                                      <p className="text-sm">{msg.content}</p>
                                      <p className="text-xs opacity-70 mt-1">{msg.time}</p>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </ScrollArea>
                          </DialogContent>
                        </Dialog>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="tasks" className="space-y-4">
          {isLoading ? (
            <SkeletonList items={5} />
          ) : filteredTasks.length === 0 ? (
            <EmptyState
              icon={CheckCircle}
              title="No tasks found"
              description={debouncedSearchTerm || selectedAgent !== "all" || selectedStatus !== "all"
                ? "Try adjusting your search or filter criteria"
                : "Your completed tasks will appear here once your workforce starts working."}
              action={debouncedSearchTerm || selectedAgent !== "all" || selectedStatus !== "all" ? {
                label: "Clear Filters",
                onClick: () => {
                  setSearchTerm("")
                  setSelectedAgent("all")
                  setSelectedStatus("all")
                }
              } : undefined}
            />
          ) : (
            <div className="space-y-4">
              {filteredTasks.map((task) => (
                <Card key={task.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className={`w-10 h-10 rounded-full ${task.color} flex items-center justify-center`}>
                          <task.icon className="w-5 h-5 text-white" />
                        </div>
                        <div className="flex-1">
                          <h3 className="font-semibold text-gray-900">{task.task}</h3>
                          <p className="text-sm text-gray-500 mt-1">{task.details}</p>
                          <div className="flex items-center gap-4 mt-2">
                            <span className="text-xs text-gray-400 flex items-center">
                              <Bot className="w-3 h-3 mr-1" />
                              {task.agent}
                            </span>
                            <span className="text-xs text-gray-400 flex items-center">
                              <Clock className="w-3 h-3 mr-1" />
                              {task.timestamp}
                            </span>
                          </div>
                        </div>
                      </div>
                      <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                        <CheckCircle className="w-3 h-3 mr-1" />
                        {task.status}
                      </Badge>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Conversations</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{conversationHistory.length}</div>
            <p className="text-xs text-muted-foreground">All time conversations</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tasks Completed</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{taskHistory.filter(t => t.status === "completed").length}</div>
            <p className="text-xs text-muted-foreground">Completed tasks</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
