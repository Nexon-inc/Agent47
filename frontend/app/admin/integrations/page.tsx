"use client"

import { useState, useEffect } from "react"
import AdminLayout from "@/components/admin/layout"
import { Card } from "@/components/ui/card"
import { adminAPI } from "@/lib/services/admin-api"
import { useAdminStore } from "@/lib/stores/admin-store"
import { usePolling } from "@/lib/hooks/use-polling"
import { Zap, Activity, AlertTriangle, CheckCircle } from "lucide-react"

export default function IntegrationsPage() {
  const [integrations, setIntegrations] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const { currentAdmin } = useAdminStore()
  const hasAccess = currentAdmin?.permissions?.includes("super_admin") || 
                    currentAdmin?.permissions?.includes("system_admin")

  const [overviewData, setOverviewData] = useState<any>(null)
  const [statisticsData, setStatisticsData] = useState<any>(null)
  const [isLoadingOverview, setIsLoadingOverview] = useState(true)
  const [isLoadingStats, setIsLoadingStats] = useState(true)
  const [overviewError, setOverviewError] = useState<any>(null)

  // Load initial data
  useEffect(() => {
    if (!hasAccess) return
    
    const loadData = async () => {
      try {
        setIsLoadingOverview(true)
        setIsLoadingStats(true)
        const [overview, stats] = await Promise.all([
          adminAPI.getIntegrationsOverview().catch(err => { setOverviewError(err); return null }),
          adminAPI.getIntegrationStatistics().catch(() => null)
        ])
        if (overview) setOverviewData(overview)
        if (stats) setStatisticsData(stats)
      } finally {
        setIsLoadingOverview(false)
        setIsLoadingStats(false)
      }
    }
    loadData()
  }, [hasAccess])

  // Subscribe to real-time integration updates via WebSocket
  useEffect(() => {
    if (!hasAccess) return

    const { websocketService } = require('@/lib/websocket-service')
    
    if (!websocketService.getConnectionStatus()) {
      websocketService.connect()
    }

    const unsubscribe = websocketService.subscribe('notification', (message) => {
      if (message.data?.type === 'integration_error' || message.data?.type === 'platform_update') {
        adminAPI.getIntegrationsOverview().then(setOverviewData).catch(setOverviewError)
        adminAPI.getIntegrationStatistics().then(setStatisticsData).catch(() => {})
      }
    })

    return () => unsubscribe()
  }, [hasAccess])

  useEffect(() => {
    setIsLoading(isLoadingOverview || isLoadingStats)
  }, [isLoadingOverview, isLoadingStats])

  useEffect(() => {
    if (overviewError) {
      setError(overviewError.message || "Failed to load integrations")
    } else {
      setError(null)
    }
  }, [overviewError])

  useEffect(() => {
    if (overviewData?.integrations) {
      setIntegrations(overviewData.integrations)
    }
  }, [overviewData])

  if (isLoading) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-400">Loading...</div>
        </div>
      </AdminLayout>
    )
  }

  if (error) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-red-400">{error}</div>
        </div>
      </AdminLayout>
    )
  }

  return (
    <AdminLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Integrations</h1>
          <p className="text-gray-400">Manage and monitor system integrations</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="bg-gray-900/50 border-gray-800 p-6">
            <div className="flex items-center justify-between mb-4">
              <Zap className="w-8 h-8 text-green-500" />
              <span className="text-sm text-gray-400">Total</span>
            </div>
            <div className="text-3xl font-bold text-white">{statisticsData?.total_integrations || overviewData?.total_integrations || 0}</div>
            <div className="text-sm text-gray-400 mt-2">Active integrations</div>
          </Card>

          <Card className="bg-gray-900/50 border-gray-800 p-6">
            <div className="flex items-center justify-between mb-4">
              <Activity className="w-8 h-8 text-blue-500" />
              <span className="text-sm text-gray-400">Healthy</span>
            </div>
            <div className="text-3xl font-bold text-white">{statisticsData?.healthy_integrations || overviewData?.healthy_integrations || 0}</div>
            <div className="text-sm text-gray-400 mt-2">Operational integrations</div>
          </Card>

          <Card className="bg-gray-900/50 border-gray-800 p-6">
            <div className="flex items-center justify-between mb-4">
              <AlertTriangle className="w-8 h-8 text-yellow-500" />
              <span className="text-sm text-gray-400">Issues</span>
            </div>
            <div className="text-3xl font-bold text-white">{statisticsData?.unhealthy_integrations || overviewData?.unhealthy_integrations || 0}</div>
            <div className="text-sm text-gray-400 mt-2">Requires attention</div>
          </Card>
        </div>

        <Card className="bg-gray-900/50 border-gray-800 p-6">
          <div className="text-center py-12">
            <Zap className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-300 mb-2">No integrations configured</h3>
            <p className="text-gray-500">Integrations will appear here once configured</p>
          </div>
        </Card>
      </div>
    </AdminLayout>
  )
}

