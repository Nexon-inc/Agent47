"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  Globe,
  Instagram,
  Linkedin,
  Twitter,
  Youtube,
  Facebook,
  Mail,
  ShoppingBag,
  BarChart,
  Plus,
  Settings,
  CheckCircle,
  AlertCircle,
  XCircle,
  TrendingUp,
  Users,
  Activity,
  Zap,
  RefreshCw,
  Loader2,
  ExternalLink,
  Wifi,
  WifiOff,
  AlertTriangle,
} from "lucide-react"
import { apiClient } from "@/lib/api-client"
import { useAuthStore } from "@/lib/stores/auth-store"
import { useToast } from "@/hooks/use-toast"
import { SkeletonCard, SkeletonStats } from "@/components/dashboard/skeletons"
import EmptyState, { EmptyStates } from "@/components/dashboard/empty-state"

interface Platform {
  id: number
  name: string
  display_name: string
  platform_type: string
  description: string
  api_version: string
  base_url: string
  status: string
  rate_limits: Record<string, any>
  supported_features: Record<string, any>
  authentication_methods: Record<string, any>
  created_at: string
  updated_at: string
}

interface PlatformConnection {
  id: number
  user_id: number
  platform_id: number
  platform_name: string
  display_name: string
  status: string
  connected_at?: string
  last_sync?: string
  credentials_status: string
  error_message?: string
  metadata?: any
}

interface PlatformMetrics {
  platform_id: number
  platform_name: string
  posts_count: number
  followers_count: number
  engagement_rate: number
  last_activity?: string
  health_score: number
  error_count: number
  success_rate: number
}

export default function PlatformsOverviewTab() {
  const { user } = useAuthStore()
  const [selectedCategory, setSelectedCategory] = useState("All")
  const [availablePlatforms, setAvailablePlatforms] = useState<Platform[]>([])
  const [connectedPlatforms, setConnectedPlatforms] = useState<PlatformConnection[]>([])
  const [platformMetrics, setPlatformMetrics] = useState<PlatformMetrics[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const [connectingPlatformId, setConnectingPlatformId] = useState<number | null>(null)
  const { toast } = useToast()

  // Social Media Platform icons mapping (ONLY social media)
  const platformIcons = {
    instagram: Instagram,
    linkedin: Linkedin,
    twitter: Twitter,
    facebook: Facebook,
    youtube: Youtube,
    tiktok: Globe,
    pinterest: Globe,
    snapchat: Globe,
    reddit: Globe,
    discord: Globe,
    threads: Globe,
  }

  const platformColors = {
    instagram: "from-pink-500 to-purple-600",
    linkedin: "from-blue-600 to-blue-700",
    twitter: "from-gray-800 to-black",
    facebook: "from-blue-700 to-blue-800",
    youtube: "from-red-600 to-red-700",
    tiktok: "from-black to-gray-800",
    pinterest: "from-red-500 to-red-600",
    snapchat: "from-yellow-400 to-yellow-500",
    reddit: "from-orange-500 to-orange-600",
    discord: "from-indigo-500 to-indigo-600",
    threads: "from-gray-700 to-gray-900",
  }

  // Load platforms data
  useEffect(() => {
    loadPlatformsData()
  }, [])

  // Subscribe to real-time platform updates via WebSocket
  useEffect(() => {
    const { websocketService } = require('@/lib/websocket-service')
    
    if (!websocketService.getConnectionStatus()) {
      websocketService.connect()
    }

    // Reload when platform connections change
    const unsubscribe = websocketService.subscribe('notification', (message) => {
      if (message.data?.type === 'platform_update' || message.data?.type === 'integration_error') {
        loadPlatformsData()
      }
    })

    return () => unsubscribe()
  }, [])

  // Check for OAuth callback success and refresh
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search)
    const success = urlParams.get("success")
    const platform = urlParams.get("platform")
    
    if (success === "platform_connected" && platform) {
      // Refresh platforms data to show newly connected platform
      loadPlatformsData()
      
      // Clean up URL parameters
      const newUrl = window.location.pathname + window.location.search.replace(/[?&]success=[^&]*|[?&]platform=[^&]*/g, '').replace(/^&/, '?')
      if (newUrl !== window.location.pathname) {
        window.history.replaceState({}, '', newUrl)
      }
    }
  }, [])

  const loadPlatformsData = async () => {
    try {
      setIsLoading(true)
      setIsRefreshing(true)
      
      // Load platforms from OAuth router - get ALL available platforms
      const [platformsResponse, connectionsResponse, metricsResponse] = await Promise.all([
        apiClient.get("/api/v1/platforms/").catch(() => ({ data: [] })),
        apiClient.get("/api/v1/platforms/connected").catch(() => ({ data: { platforms: [] } })),
        apiClient.get("/api/platforms/metrics").catch(() => ({ data: [] }))
      ])
      
      // Get all platforms (not just social media) - user can connect any platform
      const allPlatforms = platformsResponse.data || []
      
      // Extract platforms array from connections response
      const connectedPlatformsList = connectionsResponse.data?.platforms || connectionsResponse.data || []
      
      setAvailablePlatforms(allPlatforms)
      setConnectedPlatforms(connectedPlatformsList)
      setPlatformMetrics(metricsResponse.data || [])
      setLastUpdated(new Date())
      
    } catch (error) {
      console.error("Failed to load platforms data:", error)
      // Generate fallback data
      generateFallbackData()
    } finally {
      setIsLoading(false)
      setIsRefreshing(false)
    }
  }

  const generateFallbackData = () => {
    // Set empty data when API is not available
    setAvailablePlatforms([])
    setConnectedPlatforms([])
    setPlatformMetrics([])
    setLastUpdated(new Date())
  }

  const handleConnectPlatform = async (platform: Platform) => {
    setConnectingPlatformId(platform.id)
    try {
      // Get OAuth authorization URL from backend
      const response = await apiClient.get(`/api/v1/platforms/connect/${platform.name}`)
      
      if (response.data?.success && response.data?.auth_url) {
        toast({
          title: "Redirecting...",
          description: `Redirecting to ${platform.display_name} to authorize the connection.`,
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
      console.error("Failed to connect platform:", error)
      const errorMessage = error?.response?.data?.detail || error?.message || "Failed to connect platform"
      toast({
        title: "Connection error",
        description: errorMessage,
        variant: "destructive",
      })
    } finally {
      setConnectingPlatformId(null)
    }
  }

  const handleDisconnectPlatform = async (platform: Platform) => {
    try {
      await apiClient.post(`/api/v1/platforms/disconnect/${platform.name}`)
      await loadPlatformsData()
      toast({
        title: "Platform disconnected",
        description: `${platform.display_name} has been disconnected.`,
      })
    } catch (error: any) {
      console.error("Failed to disconnect platform:", error)
      const errorMessage = error?.response?.data?.detail || error?.message || "Failed to disconnect platform"
      toast({
        title: "Disconnect failed",
        description: errorMessage,
        variant: "destructive",
      })
    }
  }

  const handleTestConnection = async (platformId: number) => {
    try {
      await apiClient.post("/api/platforms/test-connection", null, {
        params: { platform_id: platformId }
      })
      await loadPlatformsData()
    } catch (error) {
      console.error("Failed to test connection:", error)
    }
  }

  const handleSyncData = async (platformId: number) => {
    try {
      await apiClient.post("/api/platforms/sync", null, {
        params: { platform_id: platformId }
      })
      await loadPlatformsData()
    } catch (error) {
      console.error("Failed to sync data:", error)
    }
  }

  const formatTimeAgo = (timestamp: string): string => {
    const now = new Date()
    const date = new Date(timestamp)
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)
    
    if (diffInSeconds < 60) return "Just now"
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`
    if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)} days ago`
    return date.toLocaleDateString()
  }

  // Get platform metrics for a specific platform
  const getPlatformMetrics = (platformId: number): PlatformMetrics | undefined => {
    return platformMetrics.find(m => m.platform_id === platformId)
  }

  // Filter platforms - show all platforms, filter by category if selected
  const filteredPlatforms = availablePlatforms.filter((platform) => {
    if (selectedCategory === "All") return true
    return platform.platform_type === selectedCategory.toLowerCase().replace(' ', '_')
  })

  // Calculate stats
  const connectedCount = connectedPlatforms.filter(p => 
    p.status === "connected" || p.status === "active"
  ).length
  const totalFollowers = platformMetrics.reduce((sum, m) => sum + m.followers_count, 0)
  const avgEngagement = platformMetrics.length > 0 
    ? platformMetrics.reduce((sum, m) => sum + m.engagement_rate, 0) / platformMetrics.length 
    : 0
  const avgHealthScore = platformMetrics.length > 0
    ? platformMetrics.reduce((sum, m) => sum + m.health_score, 0) / platformMetrics.length
    : 0

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "connected":
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case "error":
        return <AlertCircle className="w-4 h-4 text-red-500" />
      case "disconnected":
        return <XCircle className="w-4 h-4 text-gray-400" />
      default:
        return <XCircle className="w-4 h-4 text-gray-400" />
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "connected":
        return (
          <Badge className="bg-green-100 text-green-800  ">
            <div className="w-2 h-2 bg-green-500 rounded-full mr-1 animate-pulse" />
            Connected
          </Badge>
        )
      case "error":
        return (
          <Badge variant="destructive">
            <div className="w-2 h-2 bg-red-500 rounded-full mr-1" />
            Error
          </Badge>
        )
      case "disconnected":
        return (
          <Badge variant="secondary">
            <div className="w-2 h-2 bg-gray-400 rounded-full mr-1" />
            Disconnected
          </Badge>
        )
      default:
        return (
          <Badge variant="secondary">
            <div className="w-2 h-2 bg-gray-400 rounded-full mr-1" />
            Unknown
          </Badge>
        )
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 ">Social Media Platforms</h1>
          <p className="text-slate-600  mt-1">
            Connect and manage your social media accounts
            {lastUpdated && (
              <span className="text-xs text-gray-500 ml-2">
                Last updated: {lastUpdated.toLocaleTimeString()}
              </span>
            )}
          </p>
        </div>
        <div className="flex space-x-2">
          <Button 
            variant="outline" 
            size="sm" 
            onClick={loadPlatformsData}
            disabled={isRefreshing}
          >
            {isRefreshing ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4 mr-2" />
            )}
            Refresh
          </Button>
          <Button 
            className="bg-green-600 hover:bg-green-700"
            onClick={() => {
              // Open platform selection modal or navigate to platforms page
              // This button should trigger platform connection flow
              if (availablePlatforms.length > 0) {
                // If there are available platforms, show first one or a selection
                const firstPlatform = availablePlatforms[0]
                handleConnectPlatform(firstPlatform)
              } else {
                // Reload platforms if none available
                loadPlatformsData()
              }
            }}
          >
          <Plus className="w-4 h-4 mr-2" />
          Connect Platform
        </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-600 ">Connected</p>
                <p className="text-2xl font-bold text-slate-900 ">
                  {isLoading ? "..." : connectedCount}
                </p>
              </div>
              <div className="w-12 h-12 bg-green-100  rounded-lg flex items-center justify-center">
                <Zap className="w-6 h-6 text-green-600 " />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-600 ">Total Followers</p>
                <p className="text-2xl font-bold text-slate-900 ">
                  {isLoading ? "..." : `${(totalFollowers / 1000).toFixed(1)}K`}
                </p>
              </div>
              <div className="w-12 h-12 bg-blue-100  rounded-lg flex items-center justify-center">
                <Users className="w-6 h-6 text-blue-600 " />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-600 ">Avg Engagement</p>
                <p className="text-2xl font-bold text-slate-900 ">
                  {isLoading ? "..." : `${avgEngagement.toFixed(1)}%`}
                </p>
              </div>
              <div className="w-12 h-12 bg-purple-100  rounded-lg flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-purple-600 " />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-600 ">Health Score</p>
                <p className="text-2xl font-bold text-slate-900 ">
                  {isLoading ? "..." : `${avgHealthScore.toFixed(0)}%`}
                </p>
              </div>
              <div className="w-12 h-12 bg-amber-100  rounded-lg flex items-center justify-center">
                <Activity className="w-6 h-6 text-amber-600 " />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Category Filter - All Platform Types */}
      <div className="flex flex-wrap gap-2">
        {["All", "Social Media", "Business", "Content", "Analytics", "Productivity", "E-commerce", "Communication"].map((category) => (
          <button
            key={category}
            onClick={() => setSelectedCategory(category)}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              selectedCategory === category
                ? "bg-green-100 text-green-800  "
                : "bg-slate-100 text-slate-600 hover:bg-slate-200   :bg-slate-700"
            }`}
          >
            {category}
          </button>
        ))}
      </div>

      {/* Platforms Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : filteredPlatforms.length === 0 ? (
        <EmptyState
          icon={Globe}
          title={EmptyStates.noPlatforms.title}
          description={selectedCategory !== "All" 
            ? `No platforms found in ${selectedCategory}. Try selecting a different category.` 
            : EmptyStates.noPlatforms.description}
          action={{
            label: EmptyStates.noPlatforms.actionLabel,
            onClick: () => {
              // This will be handled by the Connect Platform button
              const button = document.querySelector('[data-connect-platform]') as HTMLButtonElement
              button?.click()
            }
          }}
        />
      ) : (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredPlatforms.map((platform) => {
            const platformNameKey = platform.name.toLowerCase() as keyof typeof platformIcons
            const IconComponent = platformIcons[platformNameKey] || Globe
            const platformColor = platformColors[platformNameKey] || "from-gray-500 to-gray-600"
            // Find connection by platform name (OAuth router uses platform name, not ID)
            const connection = connectedPlatforms.find(c => 
              c.platform_name === platform.name || c.platform_id === platform.id
            )
            const metrics = getPlatformMetrics(platform.id)
            const isConnected = connection?.status === "connected" || connection?.status === "active"
            const hasError = connection?.status === "error" || connection?.status === "disconnected"
            const displayName = platform.display_name || platform.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())

          return (
            <Card key={platform.id} className="hover:shadow-lg transition-shadow duration-200">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div
                        className={`w-12 h-12 bg-gradient-to-r ${platformColor} rounded-lg flex items-center justify-center shadow-sm`}
                    >
                      <IconComponent className="w-6 h-6 text-white" />
                    </div>
                    <div>
                        <CardTitle className="text-lg text-gray-900">{displayName}</CardTitle>
                        <p className="text-sm text-slate-600 capitalize">
                          {platform.platform_type?.replace('_', ' ') || 'Social Media'}
                        </p>
                      </div>
                    </div>
                    {connection && getStatusBadge(connection.status)}
                </div>
              </CardHeader>

              <CardContent className="space-y-4">
                {/* Stats */}
                  {metrics && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-slate-500 ">Followers</p>
                        <p className="text-lg font-semibold text-slate-900 ">
                          {(metrics.followers_count / 1000).toFixed(1)}K
                        </p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-500 ">Engagement</p>
                        <p className="text-lg font-semibold text-slate-900 ">
                          {metrics.engagement_rate.toFixed(1)}%
                        </p>
                  </div>
                </div>
                  )}

                {/* Activity */}
                  {metrics && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-slate-500 ">Posts</p>
                        <p className="text-sm text-slate-600 ">{metrics.posts_count}</p>
                  </div>
                  <div>
                        <p className="text-xs text-slate-500 ">Health Score</p>
                        <p className="text-sm text-slate-600 ">{metrics.health_score}%</p>
                  </div>
                </div>
                  )}

                  {/* Connection Info */}
                  {connection && (
                    <div className="space-y-2">
                      <p className="text-xs text-slate-500 ">Last Sync</p>
                      <p className="text-sm text-slate-600 ">
                        {connection.last_sync ? formatTimeAgo(connection.last_sync) : "Never"}
                      </p>
                      {hasError && connection.error_message && (
                        <p className="text-xs text-red-600 ">
                          {connection.error_message}
                        </p>
                      )}
                    </div>
                  )}

                {/* Actions */}
                <div className="flex space-x-2 pt-2">
                    {isConnected ? (
                      <>
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => handleTestConnection(platform.id)}
                        >
                          <Wifi className="w-4 h-4 mr-1" />
                          Test
                        </Button>
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => handleSyncData(platform.id)}
                        >
                          <RefreshCw className="w-4 h-4 mr-1" />
                          Sync
                        </Button>
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => handleDisconnectPlatform(platform)}
                        >
                          <WifiOff className="w-4 h-4 mr-1" />
                          Disconnect
                        </Button>
                      </>
                    ) : hasError ? (
                      <>
                        <Button 
                          size="sm" 
                          className="flex-1"
                          onClick={() => handleConnectPlatform(platform)}
                          disabled={connectingPlatformId === platform.id}
                        >
                          {connectingPlatformId === platform.id ? (
                            <>
                              <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                              Connecting...
                            </>
                          ) : (
                            <>
                              <AlertTriangle className="w-4 h-4 mr-1" />
                              Fix Connection
                            </>
                          )}
                        </Button>
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => handleDisconnectPlatform(platform)}
                        >
                          <WifiOff className="w-4 h-4" />
                        </Button>
                      </>
                    ) : (
                      <Button 
                        size="sm" 
                        className="flex-1"
                        onClick={() => handleConnectPlatform(platform)}
                        disabled={connectingPlatformId === platform.id}
                      >
                        {connectingPlatformId === platform.id ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                            Connecting...
                          </>
                        ) : (
                          <>
                            <Plus className="w-4 h-4 mr-1" />
                            Connect
                          </>
                        )}
                  </Button>
                    )}
                  <Button variant="outline" size="sm">
                    <Settings className="w-4 h-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
      )}

    </div>
  )
}
