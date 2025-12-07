"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Lightbulb,
  TrendingUp,
  Users,
  Target,
  BarChart3,
  Clock,
  RefreshCw,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Play,
  Pause,
  Settings,
  Zap,
  Activity,
  MessageSquare,
  Calendar,
  DollarSign,
  Hash,
  Heart,
  Share2,
  Bookmark,
  Filter,
  Download,
  Upload,
  Mic,
  MicOff,
  Send,
  Sparkles,
  Crown,
  Lock,
  Unlock,
  Wifi,
  WifiOff,
  AlertTriangle,
  Info,
  TrendingDown,
  ArrowUp,
  ArrowDown,
  Minus,
  Plus,
  Edit,
  Copy,
  Trash2,
  MoreHorizontal,
  ExternalLink,
  Link,
  ImageIcon,
  Video,
  FileText,
  Music,
  Map,
  ShoppingCart,
  CreditCard,
  Mail,
  Phone,
  MapPin,
  Globe,
  Monitor,
  Smartphone,
  Tablet,
  Laptop,
  Headphones,
  Megaphone,
} from "lucide-react"
import { useAuthStore } from "@/lib/stores/auth-store"
import { useUserStore } from "@/lib/stores/user-store"
import { apiClient } from "@/lib/api-client"

interface ContentIdea {
  id: string
  title: string
  description: string
  type: string
  status: string
  target_audience: string
  keywords: string[]
  estimated_effort: string
  potential_reach: number
  created_at: string
  updated_at: string
  tags: string[]
}

interface AnalyticsData {
  total_ideas: number
  approved_ideas: number
  content_pieces: number
  average_engagement: number
  total_reach: number
  conversion_rate: number
  by_type: Record<string, number>
  by_status: Record<string, number>
  by_audience: Record<string, number>
  top_performing_content: Array<{
    title: string
    engagement: number
    reach: number
  }>
  trend_analysis: Record<string, any>
  audience_insights: Record<string, any>
}

interface Task {
  id: string
  title: string
  description: string
  status: string
  priority: string
  due_date: string
  created_at: string
  completed_at?: string
  agent_id: string
  user_id: string
  metadata: Record<string, any>
}

interface TaskSummary {
  id: string
    title: string
  summary: string
  status: string
  created_at: string
  completed_at?: string
  metrics: Record<string, any>
  next_steps: string[]
}

export default function ShakesTab() {
  const { user } = useAuthStore()
  const { userPlan } = useUserStore()
  
  const [isLoadingData, setIsLoadingData] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  
  // Data state
  const [contentIdeas, setContentIdeas] = useState<ContentIdea[]>([])
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null)
  const [tasks, setTasks] = useState<Task[]>([])
  const [taskSummaries, setTaskSummaries] = useState<TaskSummary[]>([])
  
  // Settings state
  const [automateEnabled, setAutomateEnabled] = useState(false)
  const [customInstructions, setCustomInstructions] = useState("")
  const [isSavingSettings, setIsSavingSettings] = useState(false)

  // Load data on mount
  useEffect(() => {
    loadShakesData()
    loadShakesSettings()
  }, [])

  // Subscribe to real-time task updates via WebSocket
  useEffect(() => {
    const { websocketService } = require('@/lib/websocket-service')
    
    if (!websocketService.getConnectionStatus()) {
      websocketService.connect()
    }

    const unsubscribe = websocketService.subscribe('task_update', (message) => {
      if (message.data?.agent_id === 'shakes' || message.data?.agent_key === 'shakes') {
        loadShakesData()
      }
    })

    return () => unsubscribe()
  }, [])

  const loadShakesData = async () => {
    try {
      setIsLoadingData(true)
      setIsRefreshing(true)
      
      // Load all data in parallel
      const [ideasResponse, analyticsResponse, tasksResponse, summariesResponse] = await Promise.all([
        apiClient.get("/api/agents/shakes/content-ideas").catch(() => ({ data: [] })),
        apiClient.get("/api/agents/shakes/analytics/summary").catch(() => ({ data: null })),
        apiClient.get("/api/agents/shakes/tasks").catch(() => ({ data: [] })),
        apiClient.get("/api/agents/shakes/task-summaries").catch(() => ({ data: [] }))
      ])
      
      setContentIdeas(ideasResponse.data || [])
      setAnalyticsData(analyticsResponse.data)
      setTasks(tasksResponse.data || [])
      setTaskSummaries(summariesResponse.data || [])
      setLastUpdated(new Date())
      
    } catch (error) {
      console.error("Failed to load Shakes data:", error)
    } finally {
      setIsLoadingData(false)
      setIsRefreshing(false)
    }
  }

  const loadShakesSettings = async () => {
    try {
      const [automateResponse, instructionsResponse] = await Promise.all([
        apiClient.get("/api/agents/shakes/settings/automate").catch(() => ({ data: { enabled: false } })),
        apiClient.get("/api/agents/shakes/settings/instructions").catch(() => ({ data: { instructions: "" } }))
      ])
      
      setAutomateEnabled(automateResponse.data?.enabled || false)
      setCustomInstructions(instructionsResponse.data?.instructions || "")
    } catch (error) {
      console.error("Failed to load Shakes settings:", error)
    }
  }

  const handleAutomateToggle = async (enabled: boolean) => {
    try {
      setIsSavingSettings(true)
      await apiClient.put("/api/agents/shakes/settings/automate", { enabled })
      setAutomateEnabled(enabled)
    } catch (error) {
      console.error("Failed to update automate setting:", error)
    } finally {
      setIsSavingSettings(false)
    }
  }

  const handleSaveInstructions = async () => {
    try {
      setIsSavingSettings(true)
      await apiClient.put("/api/agents/shakes/settings/instructions", { instructions: customInstructions })
    } catch (error) {
      console.error("Failed to save custom instructions:", error)
    } finally {
      setIsSavingSettings(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active": return "bg-green-100 text-green-800"
      case "paused": return "bg-yellow-100 text-yellow-800"
      case "error": return "bg-red-100 text-red-800"
      case "draft": return "bg-gray-100 text-gray-800"
      case "approved": return "bg-blue-100 text-blue-800"
      case "rejected": return "bg-red-100 text-red-800"
      default: return "bg-gray-100 text-gray-800"
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high": return "bg-red-100 text-red-800"
      case "medium": return "bg-yellow-100 text-yellow-800"
      case "low": return "bg-green-100 text-green-800"
      default: return "bg-gray-100 text-gray-800"
    }
  }

  if (isLoadingData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center space-x-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span>Loading Shakes data...</span>
              </div>
          </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-yellow-100 rounded-lg">
            <Lightbulb className="h-6 w-6 text-yellow-600" />
          </div>
        <div>
            <h2 className="text-2xl font-bold text-gray-900">Shakes - Content Creation Agent</h2>
            <p className="text-gray-600">AI-powered content ideation and creative writing</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadShakesData}
            disabled={isRefreshing}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
        </Button>
          {lastUpdated && (
            <span className="text-sm text-gray-500">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      {/* Settings Panel */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Settings className="h-5 w-5" />
            <span>Agent Settings</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label htmlFor="automate" className="text-sm font-medium">
                Automate
              </Label>
              <p className="text-sm text-gray-600">
                Enable automatic content ideation and creation
              </p>
            </div>
            <Switch
              id="automate"
              checked={automateEnabled}
              onCheckedChange={handleAutomateToggle}
              disabled={isSavingSettings}
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="instructions" className="text-sm font-medium">
              Custom Instructions
            </Label>
            <Textarea
              id="instructions"
              placeholder="Enter custom instructions for Shakes to follow..."
              value={customInstructions}
              onChange={(e) => setCustomInstructions(e.target.value)}
              rows={3}
            />
            <Button
              size="sm"
              onClick={handleSaveInstructions}
              disabled={isSavingSettings}
            >
              {isSavingSettings ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <CheckCircle2 className="h-4 w-4 mr-2" />
              )}
              Save Instructions
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Analytics Overview */}
      {analyticsData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-6">
              <div className="flex items-center">
                <Lightbulb className="h-8 w-8 text-yellow-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Ideas</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {analyticsData.total_ideas.toLocaleString()}
                  </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
              <div className="flex items-center">
                <CheckCircle2 className="h-8 w-8 text-green-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Approved Ideas</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {analyticsData.approved_ideas.toLocaleString()}
                  </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
              <div className="flex items-center">
                <TrendingUp className="h-8 w-8 text-purple-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Avg Engagement</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {analyticsData.average_engagement}%
                  </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
              <div className="flex items-center">
                <Users className="h-8 w-8 text-orange-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Reach</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {analyticsData.total_reach.toLocaleString()}
                  </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
      )}

      {/* Recent Content Ideas */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Lightbulb className="h-5 w-5" />
            <span>Recent Content Ideas</span>
          </CardTitle>
        </CardHeader>
            <CardContent>
          {contentIdeas.length > 0 ? (
              <div className="space-y-4">
              {contentIdeas.slice(0, 5).map((idea) => (
                <div key={idea.id} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium">{idea.title}</h3>
                    <div className="flex items-center space-x-2">
                      <Badge className={getStatusColor(idea.status)}>
                        {idea.status}
                        </Badge>
                      <span className="text-sm font-medium">{idea.potential_reach} reach</span>
                      </div>
                    </div>
                  <p className="text-sm text-gray-600 mb-2">{idea.description}</p>
                  <div className="flex items-center justify-between text-sm text-gray-500">
                    <span>Type: {idea.type}</span>
                    <span>Audience: {idea.target_audience}</span>
                    <span>Effort: {idea.estimated_effort}</span>
                    </div>
                  {idea.keywords.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {idea.keywords.slice(0, 3).map((keyword, index) => (
                        <Badge key={index} variant="outline" className="text-xs">
                            {keyword}
                          </Badge>
                        ))}
                      {idea.keywords.length > 3 && (
                        <Badge variant="outline" className="text-xs">
                          +{idea.keywords.length - 3} more
                        </Badge>
                      )}
                      </div>
                  )}
                    </div>
              ))}
                    </div>
          ) : (
            <div className="text-center py-8">
              <Lightbulb className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No content ideas found</p>
              <p className="text-sm text-gray-500">Content ideas will appear here when Shakes generates them</p>
                  </div>
          )}
        </CardContent>
      </Card>

      {/* Active Tasks */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Target className="h-5 w-5" />
            <span>Active Tasks</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {tasks.length > 0 ? (
          <div className="space-y-4">
              {tasks.filter(task => task.status !== 'completed').slice(0, 5).map((task) => (
                <div key={task.id} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium">{task.title}</h3>
                    <div className="flex items-center space-x-2">
                      <Badge className={getPriorityColor(task.priority)}>
                        {task.priority}
                        </Badge>
                      <Badge className={getStatusColor(task.status)}>
                        {task.status}
                        </Badge>
                      </div>
                    </div>
                  <p className="text-sm text-gray-600 mb-2">{task.description}</p>
                  <div className="flex items-center justify-between text-sm text-gray-500">
                    <span>Created: {new Date(task.created_at).toLocaleDateString()}</span>
                    {task.due_date && (
                      <span>Due: {new Date(task.due_date).toLocaleDateString()}</span>
                    )}
                    </div>
                  </div>
            ))}
          </div>
          ) : (
            <div className="text-center py-8">
              <Target className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No active tasks</p>
              <p className="text-sm text-gray-500">Tasks will appear here when Shakes creates them</p>
                </div>
          )}
        </CardContent>
      </Card>

      {/* Task Summaries */}
        <Card>
          <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <FileText className="h-5 w-5" />
            <span>Task Summaries</span>
          </CardTitle>
          </CardHeader>
            <CardContent>
          {taskSummaries.length > 0 ? (
            <div className="space-y-4">
              {taskSummaries.slice(0, 3).map((summary) => (
                <div key={summary.id} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium">{summary.title}</h3>
                    <Badge className={getStatusColor(summary.status)}>
                      {summary.status}
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-600 mb-3">{summary.summary}</p>
                  {summary.next_steps && summary.next_steps.length > 0 && (
                    <div className="mt-3">
                      <p className="text-sm font-medium text-gray-700 mb-2">Next Steps:</p>
                      <ul className="text-sm text-gray-600 space-y-1">
                        {summary.next_steps.map((step, index) => (
                          <li key={index} className="flex items-center space-x-2">
                            <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                            <span>{step}</span>
                          </li>
                        ))}
                      </ul>
                          </div>
                  )}
                  <div className="mt-3 text-sm text-gray-500">
                    Created: {new Date(summary.created_at).toLocaleDateString()}
                          </div>
                        </div>
                      ))}
                    </div>
          ) : (
            <div className="text-center py-8">
              <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No task summaries</p>
              <p className="text-sm text-gray-500">Summaries will appear here when tasks are completed</p>
                  </div>
          )}
          </CardContent>
        </Card>
    </div>
  )
}
