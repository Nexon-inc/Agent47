"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { 
  BarChart3, 
  Users,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Activity,
  Calendar,
  RefreshCw,
  AlertCircle
} from "lucide-react"
import AdminLayout from "@/components/admin/layout"
import { useAdminStore } from "@/lib/stores/admin-store"
import { adminAPI } from "@/lib/services/admin-api"
import { usePolling } from "@/lib/hooks/use-polling"
import EmptyState from "@/components/admin/empty-state"

export default function AdminAnalyticsPage() {
  const [timeRange, setTimeRange] = useState("30d")
  const { currentAdmin } = useAdminStore()
  const [analyticsData, setAnalyticsData] = useState<any>(null)
  const [userAnalytics, setUserAnalytics] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  // Convert timeRange to days
  const getDays = (range: string) => {
    switch (range) {
      case "24h": return 1
      case "7d": return 7
      case "30d": return 30
      case "90d": return 90
      default: return 30
    }
  }

  const [overviewData, setOverviewData] = useState<any>(null)
  const [userData, setUserData] = useState<any>(null)
  const [isLoadingOverview, setIsLoadingOverview] = useState(true)
  const [isLoadingUsers, setIsLoadingUsers] = useState(true)
  const [overviewError, setOverviewError] = useState<any>(null)
  const [userError, setUserError] = useState<any>(null)

  // Load initial data
  useEffect(() => {
    if (!currentAdmin) return
    
    const loadData = async () => {
      try {
        setIsLoadingOverview(true)
        setIsLoadingUsers(true)
        const [overview, user] = await Promise.all([
          adminAPI.getAnalyticsOverview().catch(err => { setOverviewError(err); return null }),
          adminAPI.getUserAnalytics(getDays(timeRange)).catch(err => { setUserError(err); return null })
        ])
        if (overview) setOverviewData(overview)
        if (user) setUserData(user)
      } finally {
        setIsLoadingOverview(false)
        setIsLoadingUsers(false)
      }
    }
    loadData()
  }, [currentAdmin, timeRange])

  // Subscribe to real-time analytics updates via WebSocket
  useEffect(() => {
    if (!currentAdmin) return

    const { websocketService } = require('@/lib/websocket-service')
    
    if (!websocketService.getConnectionStatus()) {
      websocketService.connect()
    }

    const unsubscribe = websocketService.subscribe('notification', (message) => {
      if (message.data?.type === 'system_update' || message.data?.type === 'task_completed') {
        adminAPI.getAnalyticsOverview().then(setOverviewData).catch(setOverviewError)
        adminAPI.getUserAnalytics(getDays(timeRange)).then(setUserData).catch(setUserError)
      }
    })

    return () => unsubscribe()
  }, [currentAdmin, timeRange])

  useEffect(() => {
    if (overviewData) {
      setAnalyticsData(overviewData)
    }
    if (userData) {
      setUserAnalytics(userData)
    }
    if (overviewError || userError) {
      setError(overviewError?.message || userError?.message || "Failed to load analytics")
    }
  }, [overviewData, userData, overviewError, userError])

  // Check permissions
  const hasAccess = currentAdmin?.permissions?.includes("super_admin") || 
                    currentAdmin?.permissions?.includes("system_admin")

  const isLoading = isLoadingOverview || isLoadingUsers

  if (!hasAccess) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <BarChart3 className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-white">Access Denied</h3>
            <p className="mt-1 text-sm text-gray-500">
              You don't have permission to access analytics.
            </p>
          </div>
        </div>
      </AdminLayout>
    )
  }

  if (error && !analyticsData) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-red-400" />
            <h3 className="mt-2 text-sm font-medium text-white">Error Loading Analytics</h3>
            <p className="mt-1 text-sm text-gray-500">{error}</p>
            <Button 
              onClick={() => window.location.reload()} 
              className="mt-4"
            >
              Retry
            </Button>
          </div>
        </div>
      </AdminLayout>
    )
  }

  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Analytics Dashboard</h1>
            <p className="text-gray-400">Comprehensive business intelligence and metrics</p>
          </div>
          <div className="flex gap-2">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="px-3 py-2 border border-gray-700 rounded-md text-sm bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-green-500"
            >
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
              <option value="90d">Last 90 Days</option>
            </select>
            <Button 
              onClick={async () => {
                try {
                  const [overview, users] = await Promise.all([
                    adminAPI.getAnalyticsOverview(),
                    adminAPI.getUserAnalytics(getDays(timeRange))
                  ])
                  setAnalyticsData(overview)
                  setUserAnalytics(users)
                  setError(null)
                } catch (err) {
                  setError(err instanceof Error ? err.message : "Failed to refresh")
                }
              }} 
              disabled={isLoading}
              className="bg-green-600 hover:bg-green-700"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </div>

        {isLoading && !analyticsData ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <RefreshCw className="h-8 w-8 text-gray-400 animate-spin mx-auto mb-2" />
              <p className="text-gray-400">Loading analytics...</p>
            </div>
          </div>
        ) : !analyticsData ? (
          <EmptyState
            icon={BarChart3}
            title="No Analytics Data"
            description="Analytics data will appear here once available."
          />
        ) : (
          <>
            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card className="bg-gray-900/50 border-gray-800 p-6 hover:border-green-500/50 transition-colors">
                <div className="flex items-center justify-between mb-4">
                  <Users className="w-8 h-8 text-green-500" />
                  <span className="text-sm text-gray-400">Total</span>
                </div>
                <div className="text-3xl font-bold text-white">
                  {analyticsData?.total_users || userAnalytics?.total_users || 0}
                </div>
                <div className="text-sm text-gray-400 mt-2">Total users</div>
              </Card>
              
              <Card className="bg-gray-900/50 border-gray-800 p-6 hover:border-green-500/50 transition-colors">
                <div className="flex items-center justify-between mb-4">
                  <Activity className="w-8 h-8 text-green-500" />
                  <span className="text-sm text-gray-400">Active</span>
                </div>
                <div className="text-3xl font-bold text-white">
                  {analyticsData?.active_users || userAnalytics?.active_users || 0}
                </div>
                <div className="text-sm text-gray-400 mt-2">Active users</div>
              </Card>
              
              <Card className="bg-gray-900/50 border-gray-800 p-6 hover:border-yellow-500/50 transition-colors">
                <div className="flex items-center justify-between mb-4">
                  <DollarSign className="w-8 h-8 text-yellow-500" />
                  <span className="text-sm text-gray-400">Revenue</span>
                </div>
                <div className="text-3xl font-bold text-white">
                  ${analyticsData?.revenue?.toLocaleString() || userAnalytics?.revenue?.toLocaleString() || 0}
                </div>
                <div className="text-sm text-gray-400 mt-2">Total revenue</div>
              </Card>
              
              <Card className="bg-gray-900/50 border-gray-800 p-6 hover:border-blue-500/50 transition-colors">
                <div className="flex items-center justify-between mb-4">
                  <BarChart3 className="w-8 h-8 text-blue-500" />
                  <span className="text-sm text-gray-400">Growth</span>
                </div>
                <div className="text-3xl font-bold text-white">
                  {analyticsData?.growth_rate?.toFixed(1) || userAnalytics?.growth_rate?.toFixed(1) || 0}%
                </div>
                <div className="text-sm text-gray-400 mt-2">Growth rate</div>
              </Card>
            </div>

            {/* Detailed Analytics */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* User Growth */}
              <Card className="bg-gray-900/50 border-gray-800">
                <CardHeader>
                  <CardTitle className="text-white">User Growth</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-400">New Users</span>
                      <span className="font-medium text-white">{userAnalytics?.new_users || 0}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-400">Returning Users</span>
                      <span className="font-medium text-white">{userAnalytics?.returning_users || 0}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-400">Churned Users</span>
                      <span className="font-medium text-red-400">{userAnalytics?.churned_users || 0}</span>
                    </div>
                    <div className="pt-4 border-t border-gray-800">
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-medium text-gray-300">Net Growth</span>
                        <span className="font-bold text-green-500">
                          {userAnalytics?.net_growth ? `+${userAnalytics.net_growth}` : 0}
                        </span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Revenue Breakdown */}
              <Card className="bg-gray-900/50 border-gray-800">
                <CardHeader>
                  <CardTitle className="text-white">Revenue Breakdown</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {analyticsData?.revenue_breakdown ? (
                      Object.entries(analyticsData.revenue_breakdown).map(([plan, amount]: [string, any]) => (
                        <div key={plan} className="flex justify-between items-center">
                          <span className="text-sm text-gray-400">{plan}</span>
                          <span className="font-medium text-white">${amount?.toLocaleString() || 0}</span>
                        </div>
                      ))
                    ) : (
                      <div className="text-sm text-gray-500">No revenue data available</div>
                    )}
                    <div className="pt-4 border-t border-gray-800">
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-medium text-gray-300">Total Revenue</span>
                        <span className="font-bold text-white">
                          ${(analyticsData?.revenue || 0).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Performance Metrics */}
            <Card className="bg-gray-900/50 border-gray-800">
              <CardHeader>
                <CardTitle className="text-white">Performance Metrics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-500">
                      {analyticsData?.uptime?.toFixed(1) || 0}%
                    </div>
                    <div className="text-sm text-gray-400">Uptime</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-500">
                      {analyticsData?.avg_response_time || 0}ms
                    </div>
                    <div className="text-sm text-gray-400">Average Response Time</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-500">
                      {analyticsData?.api_success_rate?.toFixed(1) || 0}%
                    </div>
                    <div className="text-sm text-gray-400">API Success Rate</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </AdminLayout>
  )
}
