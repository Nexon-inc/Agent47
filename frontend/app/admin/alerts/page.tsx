"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { 
  AlertTriangle, 
  Bell,
  CheckCircle,
  XCircle,
  RefreshCw,
  Search,
  Filter,
  Settings
} from "lucide-react"
import { useAdminStore } from "@/lib/stores/admin-store"
import AdminLayout from "@/components/admin/layout"
import { adminAPI } from "@/lib/services/admin-api"
import { usePolling } from "@/lib/hooks/use-polling"

interface Alert {
  id: string
  type: string
  severity: string
  message: string
  timestamp: string
  resolved: boolean
  acknowledged: boolean
  source: string
}

export default function AdminAlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [filterSeverity, setFilterSeverity] = useState("all")
  const [filterStatus, setFilterStatus] = useState("all")
  const [searchQuery, setSearchQuery] = useState("")
  const [error, setError] = useState<string | null>(null)
  
  const { currentAdmin } = useAdminStore()

  const hasAccess = currentAdmin?.permissions?.includes("super_admin") || 
                    currentAdmin?.permissions?.includes("system_admin")

  const [alertsData, setAlertsData] = useState<any>(null)
  const [isLoadingAlerts, setIsLoadingAlerts] = useState(true)
  const [alertsError, setAlertsError] = useState<any>(null)

  // Load initial data
  useEffect(() => {
    if (!hasAccess) return
    
    const loadAlerts = async () => {
      try {
        setIsLoadingAlerts(true)
        const severity = filterSeverity !== "all" ? filterSeverity : undefined
        const status = filterStatus !== "all" ? filterStatus : undefined
        const data = await adminAPI.getAlerts(severity, status)
        setAlertsData(data)
      } catch (err) {
        setAlertsError(err)
      } finally {
        setIsLoadingAlerts(false)
      }
    }
    loadAlerts()
  }, [hasAccess, filterSeverity, filterStatus])

  // Subscribe to real-time alerts via WebSocket
  useEffect(() => {
    if (!hasAccess) return

    const { websocketService } = require('@/lib/websocket-service')
    
    if (!websocketService.getConnectionStatus()) {
      websocketService.connect()
    }

    // Reload alerts when new alerts arrive
    const unsubscribe = websocketService.subscribe('alert', () => {
      const severity = filterSeverity !== "all" ? filterSeverity : undefined
      const status = filterStatus !== "all" ? filterStatus : undefined
      adminAPI.getAlerts(severity, status).then(setAlertsData).catch(setAlertsError)
    })

    return () => unsubscribe()
  }, [hasAccess, filterSeverity, filterStatus])

  const refetchAlerts = async () => {
    try {
      setIsLoadingAlerts(true)
      const severity = filterSeverity !== "all" ? filterSeverity : undefined
      const status = filterStatus !== "all" ? filterStatus : undefined
      const data = await adminAPI.getAlerts(severity, status)
      setAlertsData(data)
    } catch (err) {
      setAlertsError(err)
    } finally {
      setIsLoadingAlerts(false)
    }
  }

  useEffect(() => {
    if (alertsData?.alerts) {
      setAlerts(alertsData.alerts.map((alert: any) => ({
        id: alert.alert_id || alert.id,
        type: alert.alert_type || alert.type,
        severity: alert.severity,
        message: alert.message,
        timestamp: alert.timestamp || alert.created_at,
        resolved: alert.status === 'resolved' || alert.resolved || false,
        acknowledged: alert.acknowledged || false,
        source: alert.source || alert.alert_source || 'unknown'
      })))
    }
  }, [alertsData])

  useEffect(() => {
    if (alertsError) {
      setError(alertsError.message || "Failed to fetch alerts. Please try again.")
    } else {
      setError(null)
    }
  }, [alertsError])

  useEffect(() => {
    setIsLoading(isLoadingAlerts)
  }, [isLoadingAlerts])

  const fetchAlerts = () => {
    refetchAlerts()
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "critical": return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300"
      case "warning": return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300"
      case "info": return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300"
      default: return "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300"
    }
  }

  const filteredAlerts = alerts.filter(alert => {
    const matchesSeverity = filterSeverity === "all" || alert.severity === filterSeverity
    const matchesStatus = filterStatus === "all" || 
      (filterStatus === "resolved" && alert.resolved) ||
      (filterStatus === "unresolved" && !alert.resolved)
    const matchesSearch = alert.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         alert.source.toLowerCase().includes(searchQuery.toLowerCase())
    
    return matchesSeverity && matchesStatus && matchesSearch
  })

  const acknowledgeAlert = async (alertId: string) => {
    try {
      await adminAPI.acknowledgeAlert(alertId)
      await refetchAlerts()
    } catch (error: any) {
      setError(error.message || "Failed to acknowledge alert")
      console.error("Failed to acknowledge alert:", error)
    }
  }

  const resolveAlert = async (alertId: string) => {
    try {
      await adminAPI.resolveAlert(alertId)
      await refetchAlerts()
    } catch (error: any) {
      setError(error.message || "Failed to resolve alert")
      console.error("Failed to resolve alert:", error)
    }
  }

  if (!hasAccess) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <AlertTriangle className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">Access Denied</h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              You don't have permission to access alert management.
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
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Alert Management</h1>
            <p className="text-gray-600 dark:text-gray-400">Monitor and manage system alerts</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline">
              <Settings className="h-4 w-4 mr-2" />
              Configure
            </Button>
            <Button onClick={fetchAlerts} disabled={isLoading}>
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </div>

        {/* Alert Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Alerts</CardTitle>
              <Bell className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{alerts.length}</div>
              <p className="text-xs text-muted-foreground">
                Last 24 hours
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Critical</CardTitle>
              <AlertTriangle className="h-4 w-4 text-red-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">
                {alerts.filter(a => a.severity === 'critical').length}
              </div>
              <p className="text-xs text-muted-foreground">
                Requires immediate attention
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Unresolved</CardTitle>
              <XCircle className="h-4 w-4 text-yellow-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-yellow-600">
                {alerts.filter(a => !a.resolved).length}
              </div>
              <p className="text-xs text-muted-foreground">
                Pending resolution
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Resolved</CardTitle>
              <CheckCircle className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                {alerts.filter(a => a.resolved).length}
              </div>
              <p className="text-xs text-muted-foreground">
                Successfully handled
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Filters */}
        <Card>
          <CardHeader>
            <CardTitle>Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col sm:flex-row gap-4 mb-6">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                  <Input
                    placeholder="Search alerts..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
              <div className="flex gap-2">
                <select
                  value={filterSeverity}
                  onChange={(e) => setFilterSeverity(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-green-500 dark:bg-gray-800 dark:border-gray-600"
                >
                  <option value="all">All Severities</option>
                  <option value="critical">Critical</option>
                  <option value="warning">Warning</option>
                  <option value="info">Info</option>
                </select>
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-green-500 dark:bg-gray-800 dark:border-gray-600"
                >
                  <option value="all">All Status</option>
                  <option value="unresolved">Unresolved</option>
                  <option value="resolved">Resolved</option>
                </select>
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-center">
                  <AlertTriangle className="h-5 w-5 text-red-500 mr-2" />
                  <span className="text-red-700">{error}</span>
                </div>
              </div>
            )}

            {/* Alerts List */}
            {isLoading ? (
              <div className="flex items-center justify-center h-32">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
              </div>
            ) : filteredAlerts.length === 0 ? (
              <div className="text-center py-8">
                <Bell className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No alerts found</h3>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  All systems are running smoothly.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {filteredAlerts.map((alert) => (
                  <div key={alert.id} className="flex items-start justify-between p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
                    <div className="flex items-start space-x-3">
                      <AlertTriangle className={`h-5 w-5 mt-0.5 ${
                        alert.severity === 'critical' ? 'text-red-500' : 
                        alert.severity === 'warning' ? 'text-yellow-500' : 'text-blue-500'
                      }`} />
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-medium text-gray-900 dark:text-white">{alert.message}</h3>
                          <Badge className={getSeverityColor(alert.severity)}>
                            {alert.severity}
                          </Badge>
                          {alert.resolved && (
                            <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300">
                              <CheckCircle className="h-3 w-3 mr-1" />
                              Resolved
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-gray-500">
                          Source: {alert.source} • {new Date(alert.timestamp).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {!alert.resolved && (
                        <>
                          {!alert.acknowledged && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => acknowledgeAlert(alert.id)}
                            >
                              Acknowledge
                            </Button>
                          )}
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => resolveAlert(alert.id)}
                          >
                            Resolve
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </AdminLayout>
  )
}
