"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  DollarSign,
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

interface Lead {
  id: string
  name: string
  email: string
  company: string
  status: string
  source: string
  value: number
  created_at: string
  last_contact: string
  notes: string
  priority: string
  assigned_to: string
  tags: string[]
}

interface Deal {
  id: string
  title: string
  value: number
  stage: string
  probability: number
  close_date: string
  created_at: string
  updated_at: string
  lead_id: string
  notes: string
  assigned_to: string
  tags: string[]
}

interface AnalyticsData {
  total_leads: number
  qualified_leads: number
  conversion_rate: number
  total_deals: number
  won_deals: number
  lost_deals: number
  total_revenue: number
  average_deal_size: number
  sales_cycle_days: number
  lead_sources: Record<string, number>
  deal_stages: Record<string, number>
  monthly_revenue: Record<string, number>
  top_performers: Array<{
    name: string
    deals_won: number
    revenue: number
  }>
  conversion_funnel: Record<string, number>
  deal_close_rate: number
  source_breakdown: Record<string, number>
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

export default function EricTab() {
  const { user } = useAuthStore()
  const { userPlan } = useUserStore()
  
  const [isLoadingData, setIsLoadingData] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  
  // Data state
  const [leads, setLeads] = useState<Lead[]>([])
  const [deals, setDeals] = useState<Deal[]>([])
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null)
  const [tasks, setTasks] = useState<Task[]>([])
  const [taskSummaries, setTaskSummaries] = useState<TaskSummary[]>([])
  
  // Settings state
  const [automateEnabled, setAutomateEnabled] = useState(false)
  const [customInstructions, setCustomInstructions] = useState("")
  const [isSavingSettings, setIsSavingSettings] = useState(false)

  // Load data on mount
  useEffect(() => {
    loadEricData()
    loadEricSettings()
  }, [])

  // Subscribe to real-time task updates via WebSocket
  useEffect(() => {
    const { websocketService } = require('@/lib/websocket-service')
    
    if (!websocketService.getConnectionStatus()) {
      websocketService.connect()
    }

    const unsubscribe = websocketService.subscribe('task_update', (message) => {
      if (message.data?.agent_id === 'eric' || message.data?.agent_key === 'eric') {
        loadEricData()
      }
    })

    return () => unsubscribe()
  }, [])

  const loadEricData = async () => {
    try {
      setIsLoadingData(true)
      setIsRefreshing(true)
      
      // Load all data in parallel
      const [leadsResponse, dealsResponse, analyticsResponse, tasksResponse, summariesResponse] = await Promise.all([
        apiClient.get("/api/agents/eric/leads").catch(() => ({ data: [] })),
        apiClient.get("/api/agents/eric/deals").catch(() => ({ data: [] })),
        apiClient.get("/api/agents/eric/analytics/summary").catch(() => ({ data: null })),
        apiClient.get("/api/agents/eric/tasks").catch(() => ({ data: [] })),
        apiClient.get("/api/agents/eric/task-summaries").catch(() => ({ data: [] }))
      ])
      
      setLeads(leadsResponse.data || [])
      setDeals(dealsResponse.data || [])
      setAnalyticsData(analyticsResponse.data)
      setTasks(tasksResponse.data || [])
      setTaskSummaries(summariesResponse.data || [])
      setLastUpdated(new Date())
      
    } catch (error) {
      console.error("Failed to load Eric data:", error)
    } finally {
      setIsLoadingData(false)
      setIsRefreshing(false)
    }
  }

  const loadEricSettings = async () => {
    try {
      const [automateResponse, instructionsResponse] = await Promise.all([
        apiClient.get("/api/agents/eric/settings/automate").catch(() => ({ data: { enabled: false } })),
        apiClient.get("/api/agents/eric/settings/instructions").catch(() => ({ data: { instructions: "" } }))
      ])
      
      setAutomateEnabled(automateResponse.data?.enabled || false)
      setCustomInstructions(instructionsResponse.data?.instructions || "")
    } catch (error) {
      console.error("Failed to load Eric settings:", error)
    }
  }

  const handleAutomateToggle = async (enabled: boolean) => {
    try {
      setIsSavingSettings(true)
      await apiClient.put("/api/agents/eric/settings/automate", { enabled })
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
      await apiClient.put("/api/agents/eric/settings/instructions", { instructions: customInstructions })
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
          <span>Loading Eric data...</span>
              </div>
          </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-amber-100 rounded-lg">
            <DollarSign className="h-6 w-6 text-amber-600" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Eric - Sales Agent</h2>
            <p className="text-gray-600">AI-powered sales automation and lead management</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadEricData}
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
                Enable automatic sales processes and lead management
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
              placeholder="Enter custom instructions for Eric to follow..."
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
                <Users className="h-8 w-8 text-blue-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Leads</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {analyticsData.total_leads.toLocaleString()}
                  </p>
                  </div>
                </div>
          </CardContent>
        </Card>

        <Card>
              <CardContent className="p-6">
              <div className="flex items-center">
                <Target className="h-8 w-8 text-green-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Conversion Rate</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {analyticsData.conversion_rate}%
                  </p>
                  </div>
                </div>
          </CardContent>
        </Card>

        <Card>
              <CardContent className="p-6">
              <div className="flex items-center">
                <DollarSign className="h-8 w-8 text-purple-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Revenue</p>
                  <p className="text-2xl font-bold text-gray-900">
                    ${analyticsData.total_revenue.toLocaleString()}
                  </p>
                  </div>
                </div>
          </CardContent>
        </Card>

        <Card>
              <CardContent className="p-6">
              <div className="flex items-center">
                <BarChart3 className="h-8 w-8 text-orange-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Avg Deal Size</p>
                  <p className="text-2xl font-bold text-gray-900">
                    ${analyticsData.average_deal_size.toLocaleString()}
                  </p>
                  </div>
                </div>
          </CardContent>
        </Card>
      </div>
      )}

          {/* Recent Leads */}
          <Card>
            <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Users className="h-5 w-5" />
            <span>Recent Leads</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
          {leads.length > 0 ? (
              <div className="space-y-4">
                {leads.slice(0, 5).map((lead) => (
                <div key={lead.id} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium">{lead.name}</h3>
                    <div className="flex items-center space-x-2">
                      <Badge className={getPriorityColor(lead.priority)}>
                        {lead.priority}
                        </Badge>
                      <Badge className={getStatusColor(lead.status)}>
                        {lead.status}
                      </Badge>
                      </div>
                    </div>
                  <p className="text-sm text-gray-600 mb-2">{lead.company} • {lead.email}</p>
                  <div className="flex items-center justify-between text-sm text-gray-500">
                    <span>Source: {lead.source}</span>
                    <span>Value: ${lead.value.toLocaleString()}</span>
                    <span>Created: {new Date(lead.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                ))}
                  </div>
          ) : (
            <div className="text-center py-8">
              <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No leads found</p>
              <p className="text-sm text-gray-500">Leads will appear here when Eric generates them</p>
            </div>
          )}
                </CardContent>
              </Card>

      {/* Active Deals */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Target className="h-5 w-5" />
            <span>Active Deals</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {deals.length > 0 ? (
          <div className="space-y-4">
              {deals.filter(deal => deal.stage !== 'closed-won' && deal.stage !== 'closed-lost').slice(0, 5).map((deal) => (
                <div key={deal.id} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium">{deal.title}</h3>
                    <div className="flex items-center space-x-2">
                      <Badge className={getStatusColor(deal.stage)}>
                        {deal.stage}
                        </Badge>
                      <span className="text-sm font-medium">${deal.value.toLocaleString()}</span>
                      </div>
                    </div>
                  <p className="text-sm text-gray-600 mb-2">{deal.notes}</p>
                  <div className="flex items-center justify-between text-sm text-gray-500">
                    <span>Probability: {deal.probability}%</span>
                    <span>Close Date: {new Date(deal.close_date).toLocaleDateString()}</span>
                    </div>
                  </div>
            ))}
          </div>
          ) : (
            <div className="text-center py-8">
              <Target className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No active deals</p>
              <p className="text-sm text-gray-500">Deals will appear here when Eric creates them</p>
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
              <p className="text-sm text-gray-500">Tasks will appear here when Eric creates them</p>
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
