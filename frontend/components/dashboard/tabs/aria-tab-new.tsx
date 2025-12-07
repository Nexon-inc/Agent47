"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Globe,
  TrendingUp,
  Users,
  Eye,
  Bell,
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
  Target,
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
  Globe2,
  Monitor,
  Smartphone,
  Tablet,
  Laptop,
  Headphones,
  Megaphone,
  FileText as FileTextIcon,
  Search,
  Lightbulb,
  Zap as ZapIcon,
  Target as TargetIcon,
  MessageSquare as MessageSquareIcon,
  Calendar as CalendarIcon,
  DollarSign as DollarSignIcon,
  Hash as HashIcon,
  Heart as HeartIcon,
  Share2 as Share2Icon,
  Bookmark as BookmarkIcon,
  Filter as FilterIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Mic as MicIcon,
  MicOff as MicOffIcon,
  Send as SendIcon,
  Sparkles as SparklesIcon,
  Crown as CrownIcon,
  Lock as LockIcon,
  Unlock as UnlockIcon,
  Wifi as WifiIcon,
  WifiOff as WifiOffIcon,
  AlertTriangle as AlertTriangleIcon,
  Info as InfoIcon,
  TrendingDown as TrendingDownIcon,
  ArrowUp as ArrowUpIcon,
  ArrowDown as ArrowDownIcon,
  Minus as MinusIcon,
  Plus as PlusIcon,
  Edit as EditIcon,
  Copy as CopyIcon,
  Trash2 as Trash2Icon,
  MoreHorizontal as MoreHorizontalIcon,
  ExternalLink as ExternalLinkIcon,
  Link as LinkIcon,
  ImageIcon as ImageIconIcon,
  Video as VideoIcon,
  FileText as FileTextIconIcon,
  Music as MusicIcon,
  Map as MapIcon,
  ShoppingCart as ShoppingCartIcon,
  CreditCard as CreditCardIcon,
  Mail as MailIcon,
  Phone as PhoneIcon,
  MapPin as MapPinIcon,
  Globe2 as Globe2Icon,
  Monitor as MonitorIcon,
  Smartphone as SmartphoneIcon,
  Tablet as TabletIcon,
  Laptop as LaptopIcon,
  Headphones as HeadphonesIcon,
  Megaphone as MegaphoneIcon,
} from "lucide-react"
import { useAuthStore } from "@/lib/stores/auth-store"
import { useUserStore } from "@/lib/stores/user-store"
import { apiClient } from "@/lib/api-client"

interface SocialAccount {
  id: string
  platform: string
  handle: string
  followers: number
  is_connected: boolean
  last_sync: string
  engagement_rate?: number
  posts_count?: number
  verified?: boolean
}

interface AnalyticsData {
  total_reach: number
  engagement_rate: number
  new_followers: number
  top_posts: any[]
  platform_breakdown: Record<string, number>
  total_posts: number
  total_likes: number
  total_comments: number
  total_shares: number
  growth_rate: number
  best_performing_platform: string
  optimal_posting_time: string
  audience_demographics: Record<string, any>
  content_performance: Record<string, any>
  hashtag_performance: Record<string, any>
  competitor_analysis: Record<string, any>
  trend_analysis: Record<string, any>
  campaign_performance: Record<string, any>
  roi_metrics: Record<string, any>
  future_recommendations: string[]
}

interface RecentPost {
  id: string
  platform: string
  content: string
  media_type: string
  engagement: number
  reach: number
  likes: number
  comments: number
  shares: number
  posted_at: string
  status: string
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

export default function AriaTabNew() {
  const { user } = useAuthStore()
  const { userPlan } = useUserStore()
  
  const [isLoadingData, setIsLoadingData] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  
  // Data state
  const [socialAccounts, setSocialAccounts] = useState<SocialAccount[]>([])
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null)
  const [recentPosts, setRecentPosts] = useState<RecentPost[]>([])
  const [tasks, setTasks] = useState<Task[]>([])
  const [taskSummaries, setTaskSummaries] = useState<TaskSummary[]>([])
  
  // Settings state
  const [automateEnabled, setAutomateEnabled] = useState(false)
  const [customInstructions, setCustomInstructions] = useState("")
  const [isSavingSettings, setIsSavingSettings] = useState(false)

  // Load data on mount
  useEffect(() => {
    loadAriaData()
    loadAriaSettings()
  }, [])

  // Subscribe to real-time task updates via WebSocket
  useEffect(() => {
    const { websocketService } = require('@/lib/websocket-service')
    
    if (!websocketService.getConnectionStatus()) {
      websocketService.connect()
    }

    const unsubscribe = websocketService.subscribe('task_update', (message) => {
      if (message.data?.agent_id === 'aria' || message.data?.agent_key === 'aria') {
        loadAriaData()
      }
    })

    return () => unsubscribe()
  }, [])

  const loadAriaData = async () => {
    try {
      setIsLoadingData(true)
      setIsRefreshing(true)
      
      // Load all data in parallel
      const [accountsResponse, analyticsResponse, postsResponse, tasksResponse, summariesResponse] = await Promise.all([
        apiClient.get("/api/agents/aria/accounts").catch(() => ({ data: [] })),
        apiClient.get("/api/agents/aria/analytics/summary").catch(() => ({ data: null })),
        apiClient.get("/api/agents/aria/posts/recent").catch(() => ({ data: [] })),
        apiClient.get("/api/agents/aria/tasks").catch(() => ({ data: [] })),
        apiClient.get("/api/agents/aria/task-summaries").catch(() => ({ data: [] }))
      ])
      
      setSocialAccounts(accountsResponse.data || [])
      setAnalyticsData(analyticsResponse.data)
      setRecentPosts(postsResponse.data || [])
      setTasks(tasksResponse.data || [])
      setTaskSummaries(summariesResponse.data || [])
      setLastUpdated(new Date())
      
    } catch (error) {
      console.error("Failed to load Aria data:", error)
    } finally {
      setIsLoadingData(false)
      setIsRefreshing(false)
    }
  }

  const loadAriaSettings = async () => {
    try {
      const [automateResponse, instructionsResponse] = await Promise.all([
        apiClient.get("/api/agents/aria/settings/automate").catch(() => ({ data: { enabled: false } })),
        apiClient.get("/api/agents/aria/settings/instructions").catch(() => ({ data: { instructions: "" } }))
      ])
      
      setAutomateEnabled(automateResponse.data?.enabled || false)
      setCustomInstructions(instructionsResponse.data?.instructions || "")
    } catch (error) {
      console.error("Failed to load Aria settings:", error)
    }
  }

  const handleAutomateToggle = async (enabled: boolean) => {
    try {
      setIsSavingSettings(true)
      await apiClient.put("/api/agents/aria/settings/automate", { enabled })
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
      await apiClient.put("/api/agents/aria/settings/instructions", { instructions: customInstructions })
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
          <span>Loading Aria data...</span>
              </div>
          </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <Globe className="h-6 w-6 text-blue-600" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Aria - Social Media Agent</h2>
            <p className="text-gray-600">AI-powered social media management and content creation</p>
                </div>
              </div>
                  <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadAriaData}
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
                Enable automatic social media management based on your preferences
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
              placeholder="Enter custom instructions for Aria to follow..."
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
                  <p className="text-sm font-medium text-gray-600">Total Reach</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {analyticsData.total_reach.toLocaleString()}
                  </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
              <div className="flex items-center">
                <TrendingUp className="h-8 w-8 text-green-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Engagement Rate</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {analyticsData.engagement_rate}%
                  </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
              <div className="flex items-center">
                <Users className="h-8 w-8 text-purple-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">New Followers</p>
                  <p className="text-2xl font-bold text-gray-900">
                    +{analyticsData.new_followers}
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
                  <p className="text-sm font-medium text-gray-600">Total Posts</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {analyticsData.total_posts}
                  </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
      )}

          {/* Social Accounts */}
          <Card>
            <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Globe className="h-5 w-5" />
            <span>Connected Social Accounts</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
          {socialAccounts.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {socialAccounts.map((account) => (
                <div key={account.id} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium">{account.platform}</h3>
                    <Badge className={account.is_connected ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"}>
                      {account.is_connected ? "Connected" : "Disconnected"}
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-600 mb-2">@{account.handle}</p>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">{account.followers.toLocaleString()} followers</span>
                    <span className="text-gray-500">{account.last_sync}</span>
                  </div>
                  </div>
                ))}
              </div>
          ) : (
            <div className="text-center py-8">
              <Globe className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No social accounts connected</p>
              <p className="text-sm text-gray-500">Connect your social media accounts to get started</p>
            </div>
          )}
            </CardContent>
          </Card>

      {/* Recent Posts */}
          <Card>
            <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <MessageSquare className="h-5 w-5" />
            <span>Recent Posts</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
          {recentPosts.length > 0 ? (
            <div className="space-y-4">
              {recentPosts.slice(0, 5).map((post) => (
                <div key={post.id} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <Badge variant="outline">{post.platform}</Badge>
                      <Badge className={getStatusColor(post.status)}>
                        {post.status}
                      </Badge>
                    </div>
                    <span className="text-sm text-gray-500">{post.posted_at}</span>
                </div>
                  <p className="text-sm text-gray-800 mb-3 line-clamp-2">{post.content}</p>
                  <div className="flex items-center space-x-4 text-sm text-gray-600">
                    <span className="flex items-center space-x-1">
                      <Heart className="h-4 w-4" />
                      <span>{post.likes}</span>
                    </span>
                    <span className="flex items-center space-x-1">
                      <MessageSquare className="h-4 w-4" />
                      <span>{post.comments}</span>
                    </span>
                    <span className="flex items-center space-x-1">
                      <Share2 className="h-4 w-4" />
                      <span>{post.shares}</span>
                    </span>
                    <span className="flex items-center space-x-1">
                      <Eye className="h-4 w-4" />
                      <span>{post.reach}</span>
                    </span>
              </div>
            </div>
          ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <MessageSquare className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No recent posts</p>
              <p className="text-sm text-gray-500">Start creating content to see your posts here</p>
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
              <p className="text-sm text-gray-500">Tasks will appear here when Aria creates them</p>
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
