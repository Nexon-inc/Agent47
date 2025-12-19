"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import {
  Zap,
  Settings,
  Code,
  Bot,
  Workflow,
  Plus,
  Play,
  Pause,
  BarChart3,
  CheckCircle,
  AlertTriangle,
  RefreshCw,
  Loader2,
  Globe,
  Database,
  Shield,
  Activity,
  TrendingUp,
  Users,
  Mail,
  Calendar,
  FileText,
  Image,
  ImageIcon,
  Video,
  VideoIcon,
  Music,
  Map,
  ShoppingCart,
  ShoppingBag,
  CreditCard,
  MessageSquare,
  Bell,
  Clock,
  Wifi,
  WifiOff,
  Edit,
  Trash2,
  ExternalLink,
  Folder,
  Filter,
  Search,
  Download,
  Upload,
  Eye,
  EyeOff,
  Lock,
  Unlock,
  Star,
  Heart,
  Share2,
  Bookmark,
  Flag,
  Tag,
  Archive,
  Copy,
  Move,
  Link,
  Unlink,
  Maximize,
  Minimize,
  RotateCcw,
  RotateCw,
  ZoomIn,
  ZoomOut,
  Grid,
  List,
  Layout,
  AlignLeft,
  AlignCenter,
  AlignRight,
  Bold,
  Italic,
  Underline,
  Strikethrough,
  Quote,
  Code2,
  Link2,
  Table,
  Columns,
  Rows,
  PlusCircle,
  MinusCircle,
  XCircle,
  CheckCircle2,
  AlertCircle,
  Info,
  HelpCircle,
  X,
  ChevronDown,
  ChevronUp,
  ChevronLeft,
  ChevronRight,
  ArrowUp,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  MoreHorizontal,
  MoreVertical,
  Menu,
  MenuSquare,
  PanelLeft,
  PanelRight,
  PanelTop,
  PanelBottom,
  Sidebar,
  SidebarClose,
  SidebarOpen,
  Tabs,
  Tab,
  Window,
  Windows,
  Monitor,
  Laptop,
  Smartphone,
  Tablet,
  Headphones,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  PlayCircle,
  PauseCircle,
  StopCircle,
  SkipBack,
  SkipForward,
  Repeat,
  Shuffle,
  FastForward,
  Rewind,
  Radio,
  Tv,
  Camera,
  Film,
  Disc,
  Headphones,
  Speaker,
  Mic,
} from "lucide-react"
import { apiClient } from "@/lib/api-client"
import { useAuthStore } from "@/lib/stores/auth-store"
import { useUserStore } from "@/lib/stores/user-store"
import { useToast } from "@/hooks/use-toast"
import ApiKeyDialog from "@/components/dashboard/api-key-dialog"

interface Integration {
  id: number
  name: string
  display_name: string
  integration_type: string
  description: string
  provider: string
  api_version: string
  base_url: string
  status: string
  pricing_tier: string
  rate_limits: Record<string, any>
  supported_features: Record<string, any>
  authentication_methods: Record<string, any>
  created_at: string
  updated_at: string
}

interface IntegrationUsage {
  id: number
  user_id: number
  integration_id: number
  integration_name: string
  status: string
  connected_at?: string
  last_used?: string
  usage_count: number
  error_count: number
  success_rate: number
  credentials_status: string
  metadata?: any
}

interface IntegrationStats {
  total_integrations: number
  connected_count: number
  available_count: number
  by_type: Record<string, number>
  by_status: Record<string, number>
  total_usage: number
  success_rate: number
  error_rate: number
}

interface CalendarEvent {
  id: string
  title: string
  description: string
  start_time: string
  end_time: string
  event_type: string
  status: string
  created_at: string
  updated_at: string
  metadata: Record<string, any>
}

interface CalendarStats {
  total_events: number
  upcoming_events: number
  completed_events: number
  by_type: Record<string, number>
  by_status: Record<string, number>
}

export default function ToolsAutomationOverviewTab() {
  const { user } = useAuthStore()
  const { userPlan } = useUserStore()
  const [selectedType, setSelectedType] = useState<string>("All")
  const [integrations, setIntegrations] = useState<Integration[]>([])
  const [integrationUsage, setIntegrationUsage] = useState<IntegrationUsage[]>([])
  const [integrationStats, setIntegrationStats] = useState<IntegrationStats | null>(null)
  const [calendarEvents, setCalendarEvents] = useState<CalendarEvent[]>([])
  const [calendarStats, setCalendarStats] = useState<CalendarStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const [apiKeyDialogOpen, setApiKeyDialogOpen] = useState(false)
  const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null)
  const [connectingIntegrationId, setConnectingIntegrationId] = useState<number | string | null>(null)
  const { toast } = useToast()

  // Connection instructions for common integrations
  const getConnectionInstructions = (integration: Integration): string | undefined => {
    const instructions: Record<string, string> = {
      mailchimp: "Go to Mailchimp → Account → Extras → API keys. Create a new API key and paste it here.",
      sendgrid: "Go to SendGrid → Settings → API Keys. Create a new API key with 'Full Access' permissions.",
      hubspot: "Go to HubSpot → Settings → Integrations → Private Apps. Create a new app and copy the API key.",
      salesforce: "Go to Salesforce → Setup → App Manager → New Connected App. Create OAuth credentials.",
      shopify: "Go to Shopify Admin → Apps → Develop apps → Create an app. Copy the Admin API access token.",
      google_analytics: "Go to Google Cloud Console → APIs & Services → Credentials. Create an API key.",
      stripe: "Go to Stripe Dashboard → Developers → API keys. Copy your Secret key.",
      slack: "Go to Slack → Your Workspace → Settings → Apps → Manage → Custom Integrations → Create New App.",
      zapier: "Go to Zapier → My Apps → Create a Zapier App. Generate API credentials.",
      notion: "Go to Notion → Settings & Members → Connections → Develop or manage integrations. Create a new integration.",
    }
    return instructions[integration.name.toLowerCase()]
  }

  // Integration type icons mapping - All tools/integrations (non-social)
  const integrationIcons: Record<string, any> = {
    // Analytics
    analytics: BarChart3,
    google_analytics: BarChart3,
    mixpanel: BarChart3,
    amplitude: BarChart3,
    // CRM/Business
    crm: Users,
    hubspot: Users,
    salesforce: Activity,
    pipedrive: Users,
    zoho: Users,
    freshsales: Users,
    // E-commerce
    shopify: ShoppingCart,
    stripe: CreditCard,
    // Communication
    communication: MessageSquare,
    email: Mail,
    mailchimp: Mail,
    sendgrid: Mail,
    constant_contact: Mail,
    slack: MessageSquare,
    discord: MessageSquare,
    microsoft_teams: MessageSquare,
    zoom: VideoIcon,
    google_meet: VideoIcon,
    // Productivity
    productivity: Zap,
    trello: FileText,
    asana: FileText,
    notion: FileText,
    // Automation
    automation: Workflow,
    zapier: Zap,
    ifttt: Zap,
    webhook: Zap,
    // Content
    wordpress: Globe,
    medium: FileText,
    substack: FileText,
    contentful: FileText,
    // Calendar
    calendar: Calendar,
    calendly: Calendar,
    // Design
    figma: Image,
    canva: Image,
    // Storage
    storage: Database,
    dropbox: Folder,
    // Security
    security: Shield,
    // Default
    default: Settings
  }

  // Load data on mount
  useEffect(() => {
    loadIntegrationsData()
  }, [])

  // Subscribe to real-time integration and calendar updates via WebSocket
  useEffect(() => {
    const { websocketService } = require('@/lib/websocket-service')
    
    if (!websocketService.getConnectionStatus()) {
      websocketService.connect()
    }

    // Reload when integrations change or calendar events update
    const unsubscribe = websocketService.subscribe('notification', (message) => {
      if (message.data?.type === 'integration_error' || 
          message.data?.type === 'platform_update' ||
          message.data?.type === 'task_completed') {
        loadIntegrationsData()
      }
    })

    return () => unsubscribe()
  }, [])

  const loadIntegrationsData = async () => {
    try {
      setIsLoading(true)
      setIsRefreshing(true)
      
      // Load integrations, usage, stats, and calendar data in parallel
      // Also load platforms to get non-social media tools
      const [integrationsResponse, usageResponse, statsResponse, calendarResponse, calendarStatsResponse, platformsResponse] = await Promise.all([
        apiClient.get("/api/integrations/").catch(() => ({ data: [] })),
        apiClient.get("/api/integrations/usage").catch(() => ({ data: [] })),
        apiClient.get("/api/integrations/stats").catch(() => ({ data: null })),
        apiClient.get("/api/calendar/events").catch(() => ({ data: [] })),
        apiClient.get("/api/calendar/stats").catch(() => ({ data: null })),
        apiClient.get("/api/v1/platforms/").catch(() => ({ data: [] }))
      ])
      
      // Filter platforms to get non-social media tools
      const nonSocialPlatforms = (platformsResponse.data || []).filter(
        (platform: any) => platform.platform_type !== "social_media"
      )
      
      // Combine integrations with non-social platforms
      // Convert platforms to integration format
      const platformIntegrations = nonSocialPlatforms.map((platform: any) => ({
        id: platform.id || platform.name,
        name: platform.name,
        display_name: platform.display_name,
        integration_type: platform.platform_type || "business",
        description: platform.description || `Connect your ${platform.display_name} account`,
        provider: platform.display_name,
        api_version: platform.api_version || "1.0",
        base_url: platform.base_url || "",
        status: platform.status || "active",
        pricing_tier: "free",
        rate_limits: platform.rate_limits || {},
        supported_features: platform.supported_features || {},
        authentication_methods: platform.authentication_methods || { oauth2: true },
        created_at: platform.created_at || new Date().toISOString(),
        updated_at: platform.updated_at || new Date().toISOString()
      }))
      
      // Combine both sources
      const allIntegrations = [...(integrationsResponse.data || []), ...platformIntegrations]
      
      setIntegrations(allIntegrations)
      setIntegrationUsage(usageResponse.data || [])
      setIntegrationStats(statsResponse.data)
      setCalendarEvents(calendarResponse.data || [])
      setCalendarStats(calendarStatsResponse.data)
      setLastUpdated(new Date())
      
    } catch (error) {
      console.error("Failed to load integrations data:", error)
      // Set empty data when API is not available
      generateFallbackData()
    } finally {
      setIsLoading(false)
      setIsRefreshing(false)
    }
  }

  const generateFallbackData = () => {
    // Set empty data when API is not available
    setIntegrations([])
    setIntegrationUsage([])
    setIntegrationStats(null)
    setCalendarEvents([])
    setCalendarStats(null)
    setLastUpdated(new Date())
  }

  const handleConnectIntegration = async (integrationId: number) => {
    const integration = integrations.find(i => i.id === integrationId)
    if (!integration) return

    // Check if it needs API key
    const authMethods = integration.authentication_methods || {}
    if (authMethods.api_key || authMethods.api_secret || authMethods.bearer_token) {
      // Open API key dialog
      setSelectedIntegration(integration)
      setApiKeyDialogOpen(true)
    } else {
      // Use OAuth or direct connection
      await handleDirectConnect(integrationId)
    }
  }

  const handleDirectConnect = async (integrationId: number) => {
    setConnectingIntegrationId(integrationId)
    try {
      await apiClient.post("/api/integrations/connect", null, {
        params: { integration_id: integrationId }
      })
      await loadIntegrationsData()
      toast({
        title: "Integration connected",
        description: "Your integration has been connected successfully.",
      })
    } catch (error: any) {
      console.error("Failed to connect integration:", error)
      toast({
        title: "Connection failed",
        description: error?.response?.data?.detail || "Failed to connect integration. Please try again.",
        variant: "destructive",
      })
    } finally {
      setConnectingIntegrationId(null)
    }
  }

  const handleApiKeyConnect = async (credentials: Record<string, string>) => {
    if (!selectedIntegration) return

    setConnectingIntegrationId(selectedIntegration.id)
    try {
      // Use secure integration router endpoint
      await apiClient.post(`/api/v1/integrations/connect/${selectedIntegration.name}`, credentials)
      await loadIntegrationsData()
      toast({
        title: "Integration connected",
        description: `${selectedIntegration.display_name} has been connected successfully.`,
      })
    } catch (error: any) {
      console.error("Failed to connect integration with API key:", error)
      const errorMessage = error?.response?.data?.detail || "Failed to connect integration. Please check your credentials."
      toast({
        title: "Connection failed",
        description: errorMessage,
        variant: "destructive",
      })
      throw error // Re-throw to let dialog handle it
    } finally {
      setConnectingIntegrationId(null)
    }
  }

  const handleConnectPlatformIntegration = async (integration: Integration) => {
    setConnectingIntegrationId(integration.id)
    try {
      // Use OAuth flow for platform-based integrations
      const response = await apiClient.get(`/api/v1/platforms/connect/${integration.name}`)
      
      if (response.data?.success && response.data?.auth_url) {
        toast({
          title: "Redirecting...",
          description: `Redirecting to ${integration.display_name} to authorize the connection.`,
        })
        // Redirect user to OAuth authorization page
        window.location.href = response.data.auth_url
      } else {
        console.error("Failed to get OAuth URL:", response.data)
        toast({
          title: "Connection failed",
          description: "Failed to initiate connection. Please try again.",
          variant: "destructive",
        })
      }
    } catch (error: any) {
      console.error("Failed to connect platform integration:", error)
      const errorMessage = error?.response?.data?.detail || error?.message || "Failed to connect integration"
      toast({
        title: "Connection error",
        description: errorMessage,
        variant: "destructive",
      })
    } finally {
      setConnectingIntegrationId(null)
    }
  }

  const handleDisconnectIntegration = async (integrationId: number) => {
    const integration = integrations.find(i => i.id === integrationId)
    try {
      await apiClient.post("/api/integrations/disconnect", null, {
        params: { integration_id: integrationId }
      })
      await loadIntegrationsData()
      toast({
        title: "Integration disconnected",
        description: integration ? `${integration.display_name} has been disconnected.` : "Integration has been disconnected.",
      })
    } catch (error: any) {
      console.error("Failed to disconnect integration:", error)
      toast({
        title: "Disconnect failed",
        description: error?.response?.data?.detail || "Failed to disconnect integration. Please try again.",
        variant: "destructive",
      })
    }
  }

  const handleRefresh = () => {
    loadIntegrationsData()
  }

  const getIntegrationIcon = (integration: Integration) => {
    // Try to get icon by integration name first, then by type
    const iconName = integration.name.toLowerCase().replace(/[^a-z0-9]/g, '_')
    const IconComponent = integrationIcons[iconName] || 
                         integrationIcons[integration.integration_type] || 
                         integrationIcons.default
    return <IconComponent className="h-5 w-5 text-current" />
  }

  const getIntegrationColor = (integration: Integration): string => {
    // Integration-specific colors
    const colorMap: Record<string, string> = {
      hubspot: "from-orange-500 to-orange-600",
      salesforce: "from-blue-500 to-blue-600",
      shopify: "from-green-600 to-green-700",
      stripe: "from-indigo-500 to-indigo-600",
      mailchimp: "from-yellow-500 to-yellow-600",
      sendgrid: "from-green-500 to-green-600",
      google_analytics: "from-orange-500 to-orange-600",
      slack: "from-purple-500 to-purple-600",
      zapier: "from-orange-500 to-orange-600",
      notion: "from-gray-700 to-gray-900",
      trello: "from-blue-500 to-blue-600",
      asana: "from-purple-500 to-purple-600",
      figma: "from-purple-500 to-purple-600",
      canva: "from-blue-500 to-blue-600",
      wordpress: "from-blue-500 to-blue-600",
    }
    
    const iconName = integration.name.toLowerCase().replace(/[^a-z0-9]/g, '_')
    return colorMap[iconName] || "from-gray-500 to-gray-600"
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "connected": return "bg-green-100 text-green-800"
      case "disconnected": return "bg-gray-100 text-gray-800"
      case "error": return "bg-red-100 text-red-800"
      case "pending": return "bg-yellow-100 text-yellow-800"
      default: return "bg-gray-100 text-gray-800"
    }
  }

  const getEventTypeColor = (type: string) => {
    switch (type) {
      case "meeting": return "bg-green-100 text-green-800"
      case "task": return "bg-green-100 text-green-800"
      case "reminder": return "bg-yellow-100 text-yellow-800"
      case "deadline": return "bg-red-100 text-red-800"
      default: return "bg-gray-100 text-gray-800"
    }
  }

  const filteredIntegrations = selectedType === "All" 
    ? integrations 
    : integrations.filter(integration => integration.integration_type === selectedType.toLowerCase())

  const upcomingEvents = calendarEvents.filter(event => 
    new Date(event.start_time) > new Date() && event.status !== "completed"
  ).slice(0, 5)

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Skeleton className="h-12 w-12 rounded-lg" />
            <div className="space-y-2">
              <Skeleton className="h-6 w-48" />
              <Skeleton className="h-4 w-64" />
            </div>
          </div>
          <Skeleton className="h-10 w-24" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <Skeleton className="h-8 w-8 rounded" />
                  <div className="ml-4 space-y-2">
                    <Skeleton className="h-4 w-24" />
                    <Skeleton className="h-6 w-12" />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-5 w-32" />
                <Skeleton className="h-4 w-48 mt-2" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-20 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-green-100 rounded-lg">
            <Zap className="h-6 w-6 text-green-600" />
          </div>
        <div>
            <h2 className="text-2xl font-bold text-gray-900">Tools & Automation</h2>
            <p className="text-gray-600">Manage integrations, automations, and calendar events</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Button 
            variant="outline" 
            size="sm" 
            onClick={handleRefresh}
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

      {/* Stats Overview */}
      <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Settings className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Integrations</p>
                <p className="text-2xl font-bold text-gray-900">
                  {integrationStats?.total_integrations || 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <CheckCircle className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Connected</p>
                <p className="text-2xl font-bold text-gray-900">
                  {integrationStats?.connected_count || 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Calendar className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Upcoming Events</p>
                <p className="text-2xl font-bold text-gray-900">
                  {calendarStats?.upcoming_events || 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Activity className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Success Rate</p>
                <p className="text-2xl font-bold text-gray-900">
                  {integrationStats?.success_rate?.toFixed(1) || 0}%
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Calendar Events */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Calendar className="h-5 w-5" />
            <span>Upcoming Events</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {upcomingEvents.length > 0 ? (
            <div className="space-y-4">
              {upcomingEvents.map((event) => (
                <div key={event.id} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium">{event.title}</h3>
                    <div className="flex items-center space-x-2">
                      <Badge className={getEventTypeColor(event.event_type)}>
                        {event.event_type}
                      </Badge>
                      <Badge className={getStatusColor(event.status)}>
                        {event.status}
                      </Badge>
                </div>
                  </div>
                  <p className="text-sm text-gray-600 mb-2">{event.description}</p>
                  <div className="flex items-center justify-between text-sm text-gray-500">
                    <span>Start: {new Date(event.start_time).toLocaleString()}</span>
                    <span>End: {new Date(event.end_time).toLocaleString()}</span>
                  </div>
                </div>
          ))}
        </div>
      ) : (
            <div className="text-center py-8">
              <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No upcoming events</p>
              <p className="text-sm text-gray-500">Events will appear here when scheduled</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Integrations */}
      <Card>
        <CardHeader>
                <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <Settings className="h-5 w-5" />
              <span>Available Integrations</span>
            </CardTitle>
            <Select value={selectedType} onValueChange={setSelectedType}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="All">All Types</SelectItem>
                <SelectItem value="Analytics">Analytics</SelectItem>
                <SelectItem value="Productivity">Productivity</SelectItem>
                <SelectItem value="Communication">Communication</SelectItem>
                <SelectItem value="Calendar">Calendar</SelectItem>
                <SelectItem value="Email">Email</SelectItem>
                <SelectItem value="CRM">CRM</SelectItem>
                <SelectItem value="Automation">Automation</SelectItem>
                <SelectItem value="Social">Social</SelectItem>
                <SelectItem value="Storage">Storage</SelectItem>
                <SelectItem value="Security">Security</SelectItem>
              </SelectContent>
            </Select>
                </div>
              </CardHeader>
        <CardContent>
          {filteredIntegrations.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
              {filteredIntegrations.map((integration) => {
                const isConnected = integrationUsage.some(usage => 
                  usage.integration_id === integration.id && usage.status === "connected"
                )
                const usage = integrationUsage.find(usage => usage.integration_id === integration.id)
                
                return (
                  <div key={integration.id} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        <div className={`w-10 h-10 bg-gradient-to-r ${getIntegrationColor(integration)} rounded-lg flex items-center justify-center`}>
                          {getIntegrationIcon(integration)}
                        </div>
                        <div>
                          <h3 className="font-medium text-gray-900">{integration.display_name || integration.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</h3>
                          <p className="text-xs text-gray-500">{integration.integration_type?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'Integration'}</p>
                        </div>
                      </div>
                      <Badge className={getStatusColor(isConnected ? "connected" : "disconnected")}>
                        {isConnected ? "Connected" : "Available"}
                      </Badge>
                    </div>
                    
                    <p className="text-sm text-gray-600 mb-3">{integration.description}</p>
                    
                    <div className="flex items-center justify-between text-sm text-gray-500 mb-3">
                      <span>Provider: {integration.provider}</span>
                      <span>Tier: {integration.pricing_tier}</span>
                    </div>
                    
                    {usage && isConnected && (
                      <div className="mb-3 p-2 bg-gray-50 rounded text-sm">
                        <div className="flex justify-between">
                          <span>Usage: {usage.usage_count}</span>
                          <span>Success: {usage.success_rate.toFixed(1)}%</span>
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          Last used: {usage.last_used ? new Date(usage.last_used).toLocaleDateString() : "Never"}
                        </div>
                    </div>
                  )}

                  <div className="flex space-x-2">
                    {isConnected ? (
                        <Button 
                          variant="outline"
                          size="sm"
                          onClick={() => handleDisconnectIntegration(integration.id)}
                          className="flex-1"
                        >
                          <WifiOff className="h-4 w-4 mr-2" />
                          Disconnect
                        </Button>
                      ) : (
                        <Button 
                          size="sm" 
                          onClick={() => {
                            // Check if it's a platform that supports OAuth
                            if (integration.authentication_methods?.oauth2 && !integration.authentication_methods?.api_key) {
                              // Use OAuth flow for platforms
                              handleConnectPlatformIntegration(integration)
                            } else {
                              // Use API key flow for integrations
                              handleConnectIntegration(integration.id)
                            }
                          }}
                          className="flex-1"
                          disabled={connectingIntegrationId === integration.id}
                        >
                          {connectingIntegrationId === integration.id ? (
                            <>
                              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                              Connecting...
                            </>
                          ) : (
                            <>
                              <Wifi className="h-4 w-4 mr-2" />
                              Connect
                            </>
                          )}
                        </Button>
                      )}
                      <Button variant="outline" size="sm">
                        <ExternalLink className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
          )
        })}
      </div>
          ) : (
            <div className="text-center py-8">
              <Settings className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No integrations available</p>
              <p className="text-sm text-gray-500">Integrations will appear here when available</p>
      </div>
      )}
        </CardContent>
      </Card>

      {/* Connected Integrations Usage */}
      {integrationUsage.length > 0 && (
      <Card>
        <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Activity className="h-5 w-5" />
              <span>Integration Usage</span>
            </CardTitle>
        </CardHeader>
        <CardContent>
            <div className="space-y-4">
              {integrationUsage.map((usage) => {
                const integration = integrations.find(i => i.id === usage.integration_id)
                if (!integration) return null

                return (
                  <div key={usage.id} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                        {getIntegrationIcon(integration)}
                        <h3 className="font-medium">{integration.display_name}</h3>
                        </div>
                      <Badge className={getStatusColor(usage.status)}>
                        {usage.status}
                  </Badge>
                </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <p className="text-gray-600">Usage Count</p>
                        <p className="font-medium">{usage.usage_count}</p>
                      </div>
                      <div>
                        <p className="text-gray-600">Success Rate</p>
                        <p className="font-medium">{usage.success_rate.toFixed(1)}%</p>
                      </div>
                      <div>
                        <p className="text-gray-600">Error Count</p>
                        <p className="font-medium">{usage.error_count}</p>
                      </div>
                      <div>
                        <p className="text-gray-600">Last Used</p>
                        <p className="font-medium">
                          {usage.last_used ? new Date(usage.last_used).toLocaleDateString() : "Never"}
                        </p>
                  </div>
                </div>
              </div>
                )
              })}
            </div>
        </CardContent>
      </Card>
      )}

      {/* API Key Dialog */}
      {selectedIntegration && (
        <ApiKeyDialog
          isOpen={apiKeyDialogOpen}
          onClose={() => {
            setApiKeyDialogOpen(false)
            setSelectedIntegration(null)
          }}
          integration={selectedIntegration}
          onConnect={handleApiKeyConnect}
          connectionInstructions={getConnectionInstructions(selectedIntegration)}
        />
      )}
    </div>
  )
}
