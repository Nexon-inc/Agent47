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
} from "lucide-react"
import { apiClient } from "@/lib/api-client"
import { useAuthStore } from "@/lib/stores/auth-store"
import { useToast } from "@/hooks/use-toast"
import { SkeletonList } from "@/components/dashboard/skeletons"
import EmptyState, { EmptyStates } from "@/components/dashboard/empty-state"
import { History } from "lucide-react"

const conversationHistory = [
  {
    id: 1,
    agent: "Aria",
    icon: Globe,
    color: "text-orange-500",
    bgColor: "bg-orange-500",
    title: "Social Media Campaign Setup",
    lastMessage: "Campaign scheduled for next week across all platforms",
    timestamp: "2 hours ago",
    status: "completed",
    messageCount: 12,
    messages: [
      { type: "user", content: "I need to set up a social media campaign for our new product launch", time: "2:30 PM" },
      {
        type: "agent",
        content: "I'd be happy to help you set up a social media campaign! What's the product and target audience?",
        time: "2:31 PM",
      },
      { type: "user", content: "It's a new fitness app targeting millennials aged 25-35", time: "2:32 PM" },
      {
        type: "agent",
        content:
          "Perfect! I'll create a comprehensive campaign across Instagram, Facebook, and Twitter. Let me draft some content ideas.",
        time: "2:33 PM",
      },
    ],
  },
  {
    id: 2,
    agent: "Clara",
    icon: Headphones,
    color: "text-purple-500",
    bgColor: "bg-purple-500",
    title: "Customer Support Automation",
    lastMessage: "Automated responses set up for common inquiries",
    timestamp: "4 hours ago",
    status: "completed",
    messageCount: 8,
    messages: [
      { type: "user", content: "Can you help me set up automated responses for customer support?", time: "10:15 AM" },
      {
        type: "agent",
        content: "I can help you create intelligent automated responses. What are the most common customer inquiries?",
        time: "10:16 AM",
      },
    ],
  },
  {
    id: 3,
    agent: "Eric",
    icon: DollarSign,
    color: "text-amber-500",
    bgColor: "bg-amber-500",
    title: "Sales Pipeline Review",
    lastMessage: "Generated 15 new qualified leads",
    timestamp: "6 hours ago",
    status: "completed",
    messageCount: 15,
    messages: [
      { type: "user", content: "I need help reviewing our sales pipeline", time: "8:30 AM" },
      {
        type: "agent",
        content: "I'll analyze your current pipeline and identify opportunities for improvement.",
        time: "8:31 AM",
      },
    ],
  },
  {
    id: 4,
    agent: "Jackie",
    icon: Megaphone,
    color: "text-pink-500",
    bgColor: "bg-pink-500",
    title: "Email Marketing Campaign",
    lastMessage: "Campaign launched with 34% open rate",
    timestamp: "1 day ago",
    status: "completed",
    messageCount: 10,
    messages: [
      { type: "user", content: "Let's create an email marketing campaign for Black Friday", time: "Yesterday 3:00 PM" },
      {
        type: "agent",
        content: "Great timing! I'll create a compelling Black Friday email campaign with personalized offers.",
        time: "Yesterday 3:01 PM",
      },
    ],
  },
  {
    id: 5,
    agent: "Purity",
    icon: Lightbulb,
    color: "text-indigo-500",
    bgColor: "bg-indigo-500",
    title: "Business Strategy Session",
    lastMessage: "Market analysis completed with recommendations",
    timestamp: "2 days ago",
    status: "completed",
    messageCount: 20,
    messages: [
      { type: "user", content: "I need help developing a business strategy for Q1", time: "2 days ago 2:00 PM" },
      {
        type: "agent",
        content: "I'll help you create a comprehensive Q1 strategy. Let's start with market analysis.",
        time: "2 days ago 2:01 PM",
      },
    ],
  },
]

const taskHistory = [
  {
    id: 1,
    agent: "Aria",
    icon: Globe,
    color: "bg-orange-500",
    task: "Posted Instagram story for product launch",
    timestamp: "30 minutes ago",
    status: "completed",
    details: "Engagement: 2.3K views, 145 likes, 23 comments",
  },
  {
    id: 2,
    agent: "Clara",
    icon: Headphones,
    color: "bg-purple-500",
    task: "Resolved customer ticket #1234",
    timestamp: "1 hour ago",
    status: "completed",
    details: "Issue: Billing inquiry, Resolution time: 5 minutes",
  },
  {
    id: 3,
    agent: "Eric",
    icon: DollarSign,
    color: "bg-amber-500",
    task: "Generated sales proposal for Enterprise client",
    timestamp: "2 hours ago",
    status: "completed",
    details: "Proposal value: $45,000, Follow-up scheduled",
  },
  {
    id: 4,
    agent: "Jackie",
    icon: Megaphone,
    color: "bg-pink-500",
    task: "Launched email campaign to 5,000 subscribers",
    timestamp: "3 hours ago",
    status: "completed",
    details: "Open rate: 34%, Click rate: 8.2%",
  },
  {
    id: 5,
    agent: "Shakes",
    icon: FileText,
    color: "bg-green-500",
    task: "Created blog post: '10 Marketing Trends for 2024'",
    timestamp: "4 hours ago",
    status: "completed",
    details: "Word count: 1,200, SEO score: 95/100",
  },
]

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
            View your conversation and task history with AI agents
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
                <SelectItem value="all">All Agents</SelectItem>
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
        </TabsList>

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
                                      className={`max-w-[80%] rounded-lg p-3 ${
                                        msg.type === "user" ? "bg-gradient-to-br from-green-400 to-green-600 text-white" : "bg-gray-50 border"
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
                : "Your completed tasks will appear here once agents start working."}
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
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Conversations</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{conversationHistory.length}</div>
            <p className="text-xs text-muted-foreground">+2 from last week</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tasks Completed</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{taskHistory.length}</div>
            <p className="text-xs text-muted-foreground">+12 from yesterday</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">98.5%</div>
            <p className="text-xs text-muted-foreground">+0.5% from last month</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
