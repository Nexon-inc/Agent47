"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  FileText,
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

interface BusinessIdea {
  id: string
  title: string
  description: string
  industry: string
  market_size: number
  competition_level: string
  feasibility_score: number
  revenue_potential: number
  created_at: string
  updated_at: string
  tags: string[]
  status: string
  priority: string
}

interface MarketResearch {
  id: string
  business_idea_id: string
  market_size: number
  growth_rate: number
  target_demographics: Record<string, any>
  competitor_analysis: Record<string, any>
  trends: string[]
  opportunities: string[]
  threats: string[]
  created_at: string
  updated_at: string
}

interface AnalyticsData {
    total_ideas: number
  analyzed_ideas: number
  average_feasibility: number
  total_market_size: number
  by_industry: Record<string, number>
  by_feasibility: Record<string, number>
  by_status: Record<string, number>
  top_opportunities: Array<{
    idea: string
    score: number
    market_size: number
  }>
  trend_analysis: Record<string, any>
  market_insights: Record<string, any>
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

export default function PurityTab() {
  const { user } = useAuthStore()
  const { userPlan } = useUserStore()
  
  const [isLoadingData, setIsLoadingData] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  
  // Data state
  const [businessIdeas, setBusinessIdeas] = useState<BusinessIdea[]>([])
  const [marketResearch, setMarketResearch] = useState<MarketResearch[]>([])
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null)
  const [tasks, setTasks] = useState<Task[]>([])
  const [taskSummaries, setTaskSummaries] = useState<TaskSummary[]>([])
  
  // Settings state
  const [automateEnabled, setAutomateEnabled] = useState(false)
  const [customInstructions, setCustomInstructions] = useState("")
  const [isSavingSettings, setIsSavingSettings] = useState(false)

  // Load data on mount
  useEffect(() => {
    loadPurityData()
    loadPuritySettings()
  }, [])

  // Subscribe to real-time task updates via WebSocket
  useEffect(() => {
    const { websocketService } = require('@/lib/websocket-service')
    
    if (!websocketService.getConnectionStatus()) {
      websocketService.connect()
    }

    const unsubscribe = websocketService.subscribe('task_update', (message) => {
      if (message.data?.agent_id === 'purity' || message.data?.agent_key === 'purity') {
        loadPurityData()
      }
    })

    return () => unsubscribe()
  }, [])

  const loadPurityData = async () => {
    try {
      setIsLoadingData(true)
      setIsRefreshing(true)
      
      // Load all data in parallel
      const [ideasResponse, researchResponse, analyticsResponse, tasksResponse, summariesResponse] = await Promise.all([
        apiClient.get("/api/agents/purity/business-ideas").catch(() => ({ data: [] })),
        apiClient.get("/api/agents/purity/market-research").catch(() => ({ data: [] })),
        apiClient.get("/api/agents/purity/analytics/summary").catch(() => ({ data: null })),
        apiClient.get("/api/agents/purity/tasks").catch(() => ({ data: [] })),
        apiClient.get("/api/agents/purity/task-summaries").catch(() => ({ data: [] }))
      ])
      
      setBusinessIdeas(ideasResponse.data || [])
      setMarketResearch(researchResponse.data || [])
      setAnalyticsData(analyticsResponse.data)
      setTasks(tasksResponse.data || [])
      setTaskSummaries(summariesResponse.data || [])
      setLastUpdated(new Date())
      
    } catch (error) {
      console.error("Failed to load Purity data:", error)
    } finally {
      setIsLoadingData(false)
      setIsRefreshing(false)
    }
  }

  const loadPuritySettings = async () => {
    try {
      const [automateResponse, instructionsResponse] = await Promise.all([
        apiClient.get("/api/agents/purity/settings/automate").catch(() => ({ data: { enabled: false } })),
        apiClient.get("/api/agents/purity/settings/instructions").catch(() => ({ data: { instructions: "" } }))
      ])
      
      setAutomateEnabled(automateResponse.data?.enabled || false)
      setCustomInstructions(instructionsResponse.data?.instructions || "")
    } catch (error) {
      console.error("Failed to load Purity settings:", error)
    }
  }

  const handleAutomateToggle = async (enabled: boolean) => {
    try {
      setIsSavingSettings(true)
      await apiClient.put("/api/agents/purity/settings/automate", { enabled })
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
      await apiClient.put("/api/agents/purity/settings/instructions", { instructions: customInstructions })
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
      case "analyzed": return "bg-blue-100 text-blue-800"
      case "validated": return "bg-green-100 text-green-800"
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

  const getFeasibilityColor = (score: number) => {
    if (score >= 80) return "bg-green-100 text-green-800"
    if (score >= 60) return "bg-yellow-100 text-yellow-800"
    return "bg-red-100 text-red-800"
  }

  if (isLoadingData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center space-x-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span>Loading Purity data...</span>
              </div>
          </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-emerald-100 rounded-lg">
            <FileText className="h-6 w-6 text-emerald-600" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Purity - Business Intelligence Agent</h2>
            <p className="text-gray-600">AI-powered business idea analysis and market research</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadPurityData}
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
                Enable automatic business analysis and market research
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
              placeholder="Enter custom instructions for Purity to follow..."
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
                <FileText className="h-8 w-8 text-emerald-600" />
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
                <BarChart3 className="h-8 w-8 text-green-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Analyzed Ideas</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {analyticsData.analyzed_ideas.toLocaleString()}
                  </p>
                  </div>
            </div>
          </CardContent>
        </Card>

        <Card>
              <CardContent className="p-6">
              <div className="flex items-center">
                <Target className="h-8 w-8 text-purple-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Avg Feasibility</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {analyticsData.average_feasibility}%
                  </p>
                  </div>
            </div>
          </CardContent>
        </Card>

        <Card>
              <CardContent className="p-6">
              <div className="flex items-center">
                <DollarSign className="h-8 w-8 text-orange-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Market Size</p>
                  <p className="text-2xl font-bold text-gray-900">
                    ${analyticsData.total_market_size.toLocaleString()}B
                  </p>
                  </div>
            </div>
          </CardContent>
        </Card>
      </div>
      )}

          {/* Recent Business Ideas */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <FileText className="h-5 w-5" />
            <span>Recent Business Ideas</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
          {businessIdeas.length > 0 ? (
              <div className="space-y-4">
              {businessIdeas.slice(0, 5).map((idea) => (
                <div key={idea.id} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium">{idea.title}</h3>
                    <div className="flex items-center space-x-2">
                      <Badge className={getFeasibilityColor(idea.feasibility_score)}>
                        {idea.feasibility_score}% feasible
                        </Badge>
                      <Badge className={getStatusColor(idea.status)}>
                        {idea.status}
                        </Badge>
                      </div>
                    </div>
                  <p className="text-sm text-gray-600 mb-2">{idea.description}</p>
                  <div className="flex items-center justify-between text-sm text-gray-500">
                    <span>Industry: {idea.industry}</span>
                    <span>Market: ${idea.market_size.toLocaleString()}B</span>
                        <span>Revenue: ${idea.revenue_potential.toLocaleString()}</span>
                    </div>
                  {idea.tags.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {idea.tags.slice(0, 3).map((tag, index) => (
                        <Badge key={index} variant="outline" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                      {idea.tags.length > 3 && (
                        <Badge variant="outline" className="text-xs">
                          +{idea.tags.length - 3} more
                        </Badge>
                      )}
                    </div>
                  )}
                    </div>
              ))}
                    </div>
          ) : (
            <div className="text-center py-8">
              <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No business ideas found</p>
              <p className="text-sm text-gray-500">Business ideas will appear here when Purity generates them</p>
                  </div>
          )}
                </CardContent>
              </Card>

      {/* Market Research */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <BarChart3 className="h-5 w-5" />
            <span>Market Research</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {marketResearch.length > 0 ? (
          <div className="space-y-4">
              {marketResearch.slice(0, 3).map((research) => (
                <div key={research.id} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium">Market Analysis</h3>
                    <div className="flex items-center space-x-2">
                      <Badge className="bg-blue-100 text-blue-800">
                        {research.growth_rate}% growth
                        </Badge>
                      <span className="text-sm font-medium">${research.market_size.toLocaleString()}B</span>
                    </div>
                      </div>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                      <p className="font-medium text-gray-700 mb-1">Opportunities:</p>
                      <ul className="text-gray-600 space-y-1">
                        {research.opportunities.slice(0, 2).map((opp, index) => (
                          <li key={index} className="flex items-center space-x-1">
                            <span className="w-1 h-1 bg-green-500 rounded-full"></span>
                            <span>{opp}</span>
                          </li>
                        ))}
                      </ul>
                      </div>
                      <div>
                      <p className="font-medium text-gray-700 mb-1">Threats:</p>
                      <ul className="text-gray-600 space-y-1">
                        {research.threats.slice(0, 2).map((threat, index) => (
                          <li key={index} className="flex items-center space-x-1">
                            <span className="w-1 h-1 bg-red-500 rounded-full"></span>
                            <span>{threat}</span>
                          </li>
                        ))}
                      </ul>
                          </div>
                        </div>
                      </div>
              ))}
                    </div>
          ) : (
            <div className="text-center py-8">
              <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No market research found</p>
              <p className="text-sm text-gray-500">Market research will appear here when Purity analyzes ideas</p>
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
              <p className="text-sm text-gray-500">Tasks will appear here when Purity creates them</p>
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
