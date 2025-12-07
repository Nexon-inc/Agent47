"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { 
  Server, 
  Activity,
  HardDrive,
  Clock,
  AlertTriangle,
  CheckCircle,
  Play,
  Pause,
  RefreshCw
} from "lucide-react"
import { useAdminStore } from "@/lib/stores/admin-store"
import AdminLayout from "@/components/admin/layout"
import { adminAPI } from "@/lib/services/admin-api"
import { usePolling } from "@/lib/hooks/use-polling"

export default function AdminServersPage() {
  const [error, setError] = useState<string | null>(null)
  const { currentAdmin } = useAdminStore()

  const hasAccess = currentAdmin?.permissions?.includes("super_admin")

  const [statusData, setStatusData] = useState<any>(null)
  const [alertsData, setAlertsData] = useState<any>(null)
  const [isLoadingStatus, setIsLoadingStatus] = useState(true)
  const [isLoadingAlerts, setIsLoadingAlerts] = useState(true)
  const [statusError, setStatusError] = useState<any>(null)
  const [alertsError, setAlertsError] = useState<any>(null)

  // Load initial data
  useEffect(() => {
    if (!hasAccess) return
    
    const loadData = async () => {
      try {
        setIsLoadingStatus(true)
        setIsLoadingAlerts(true)
        const [status, alerts] = await Promise.all([
          adminAPI.getServerStatus().catch(err => { setStatusError(err); return null }),
          adminAPI.getServerAlerts().catch(err => { setAlertsError(err); return null })
        ])
        if (status) setStatusData(status)
        if (alerts) setAlertsData(alerts)
      } finally {
        setIsLoadingStatus(false)
        setIsLoadingAlerts(false)
      }
    }
    loadData()
  }, [hasAccess])

  // Subscribe to real-time updates via WebSocket
  useEffect(() => {
    if (!hasAccess) return

    const { websocketService } = require('@/lib/websocket-service')
    
    if (!websocketService.getConnectionStatus()) {
      websocketService.connect()
    }

    // Reload server status and alerts when system status updates
    const unsubscribe = websocketService.subscribe('system_status', () => {
      adminAPI.getServerStatus().then(setStatusData).catch(setStatusError)
      adminAPI.getServerAlerts().then(setAlertsData).catch(setAlertsError)
    })

    // Also subscribe to alerts
    const unsubscribeAlerts = websocketService.subscribe('alert', () => {
      adminAPI.getServerAlerts().then(setAlertsData).catch(setAlertsError)
    })

    return () => {
      unsubscribe()
      unsubscribeAlerts()
    }
  }, [hasAccess])

  const refetchStatus = async () => {
    try {
      const data = await adminAPI.getServerStatus()
      setStatusData(data)
    } catch (err) {
      setStatusError(err)
    }
  }

  useEffect(() => {
    if (statusError || alertsError) {
      setError(statusError?.message || alertsError?.message || "Failed to load server data")
    } else {
      setError(null)
    }
  }, [statusError, alertsError])

  if (!hasAccess) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Server className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-white">Access Denied</h3>
            <p className="mt-1 text-sm text-gray-500">
              Super admin access required.
            </p>
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
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Server Management</h1>
            <p className="text-gray-600 dark:text-gray-400">Monitor and manage server infrastructure</p>
          </div>
          <Button onClick={() => refetchStatus()} disabled={isLoadingStatus}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoadingStatus ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {/* Server Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Servers</CardTitle>
              <Server className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{statusData?.total_servers || 0}</div>
              <p className="text-xs text-muted-foreground">
                {statusData?.online_servers || 0} online, {statusData?.offline_servers || 0} offline
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{statusData?.avg_cpu_usage?.toFixed(1) || '0.0'}%</div>
              <Progress value={statusData?.avg_cpu_usage || 0} className="mt-2" />
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Memory Usage</CardTitle>
              <HardDrive className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{statusData?.avg_memory_usage?.toFixed(1) || '0.0'}%</div>
              <Progress value={statusData?.avg_memory_usage || 0} className="mt-2" />
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Alerts</CardTitle>
              <AlertTriangle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{alertsData?.alerts?.length || 0}</div>
              <p className="text-xs text-muted-foreground">
                Active server alerts
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Server List */}
        <Card>
          <CardHeader>
            <CardTitle>Server Status</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoadingStatus ? (
              <div className="flex items-center justify-center h-32">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
              </div>
            ) : error ? (
              <div className="text-center py-8 text-red-400">{error}</div>
            ) : statusData?.servers?.length > 0 ? (
              <div className="space-y-4">
                {statusData.servers.map((server: any) => (
                  <div key={server.server_id || server.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center space-x-4">
                      <Server className="h-5 w-5 text-gray-400" />
                      <div>
                        <h3 className="font-medium text-gray-900 dark:text-white">{server.name || server.server_name}</h3>
                        <p className="text-sm text-gray-500">
                          CPU: {server.cpu_usage?.toFixed(1) || 0}% • Memory: {server.memory_usage?.toFixed(1) || 0}% • Uptime: {server.uptime || 'N/A'}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge className={server.status === 'online' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                        {server.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">No servers found</div>
            )}
          </CardContent>
        </Card>
      </div>
    </AdminLayout>
  )
}
