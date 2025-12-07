"use client"

import { useState, useEffect } from "react"
import AdminLayout from "@/components/admin/layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import EmptyState from "@/components/admin/empty-state"
import { Server, Activity, Database, Cpu, RefreshCw, AlertCircle, HardDrive, MemoryStick, CheckCircle } from "lucide-react"
import { useAdminStore } from "@/lib/stores/admin-store"
import { adminAPI } from "@/lib/services/admin-api"
import { usePolling } from "@/lib/hooks/use-polling"

export default function AdminSystemPage() {
  const { currentAdmin } = useAdminStore()
  const [error, setError] = useState<string | null>(null)

  const hasAccess = currentAdmin?.permissions?.includes("super_admin")

  const [systemStatus, setSystemStatus] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [statusError, setStatusError] = useState<any>(null)

  // Load initial data
  useEffect(() => {
    if (!currentAdmin || !hasAccess) return
    
    const loadData = async () => {
      try {
        setIsLoading(true)
        const data = await adminAPI.getSystemStatus()
        setSystemStatus(data)
      } catch (err) {
        setStatusError(err)
      } finally {
        setIsLoading(false)
      }
    }
    loadData()
  }, [currentAdmin, hasAccess])

  // Subscribe to real-time system status updates via WebSocket
  useEffect(() => {
    if (!currentAdmin || !hasAccess) return

    const { websocketService } = require('@/lib/websocket-service')
    
    if (!websocketService.getConnectionStatus()) {
      websocketService.connect()
    }

    // Update system status when WebSocket sends system_status messages
    const unsubscribe = websocketService.subscribe('system_status', (message) => {
      if (message.data) {
        adminAPI.getSystemStatus().then(setSystemStatus).catch(setStatusError)
      }
    })

    return () => unsubscribe()
  }, [currentAdmin, hasAccess])

  const refetch = async () => {
    try {
      setIsLoading(true)
      const data = await adminAPI.getSystemStatus()
      setSystemStatus(data)
    } catch (err) {
      setStatusError(err)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (statusError) {
      setError(statusError.message || "Failed to load system status")
    }
  }, [statusError])

  if (!hasAccess) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Server className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-white">Access Denied</h3>
            <p className="mt-1 text-sm text-gray-500">Super admin access required.</p>
          </div>
        </div>
      </AdminLayout>
    )
  }

  if (error && !systemStatus) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-red-400" />
            <h3 className="mt-2 text-sm font-medium text-white">Error Loading System Status</h3>
            <p className="mt-1 text-sm text-gray-500">{error}</p>
            <Button onClick={() => refetch()} className="mt-4">
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
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">System Status</h1>
            <p className="text-gray-400">Monitor system health and performance</p>
          </div>
          <Button 
            onClick={() => refetch()} 
            disabled={isLoading}
            className="bg-gray-800 hover:bg-gray-700"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {isLoading && !systemStatus ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <RefreshCw className="h-8 w-8 text-gray-400 animate-spin mx-auto mb-2" />
              <p className="text-gray-400">Loading system status...</p>
            </div>
          </div>
        ) : !systemStatus ? (
          <EmptyState
            icon={Server}
            title="No System Data"
            description="System health metrics will appear here once available."
          />
        ) : (
          <>
            {/* System Health Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card className="bg-gray-900/50 border-gray-800">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-white">CPU Usage</CardTitle>
                  <Cpu className="h-4 w-4 text-blue-500" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-white">
                    {systemStatus?.cpu_usage?.toFixed(1) || systemStatus?.resources?.cpu || 0}%
                  </div>
                  <Progress 
                    value={systemStatus?.cpu_usage || systemStatus?.resources?.cpu || 0} 
                    className="mt-2" 
                  />
                </CardContent>
              </Card>

              <Card className="bg-gray-900/50 border-gray-800">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-white">Memory Usage</CardTitle>
                  <MemoryStick className="h-4 w-4 text-purple-500" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-white">
                    {systemStatus?.memory_usage?.toFixed(1) || systemStatus?.resources?.memory || 0}%
                  </div>
                  <Progress 
                    value={systemStatus?.memory_usage || systemStatus?.resources?.memory || 0} 
                    className="mt-2" 
                  />
                </CardContent>
              </Card>

              <Card className="bg-gray-900/50 border-gray-800">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-white">Disk Usage</CardTitle>
                  <HardDrive className="h-4 w-4 text-yellow-500" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-white">
                    {systemStatus?.disk_usage?.toFixed(1) || systemStatus?.resources?.disk || 0}%
                  </div>
                  <Progress 
                    value={systemStatus?.disk_usage || systemStatus?.resources?.disk || 0} 
                    className="mt-2" 
                  />
                </CardContent>
              </Card>

              <Card className="bg-gray-900/50 border-gray-800">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-white">System Status</CardTitle>
                  <Activity className="h-4 w-4 text-green-500" />
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-2">
                    <Badge className={systemStatus?.status === "healthy" ? "bg-green-900/20 text-green-400 border-green-800" : "bg-yellow-900/20 text-yellow-400 border-yellow-800"}>
                      {systemStatus?.status || "unknown"}
                    </Badge>
                  </div>
                  <p className="text-xs text-gray-400 mt-2">
                    Uptime: {systemStatus?.uptime || "N/A"}
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Services Status */}
            <Card className="bg-gray-900/50 border-gray-800">
              <CardHeader>
                <CardTitle className="text-white">Services Status</CardTitle>
              </CardHeader>
              <CardContent>
                {systemStatus?.services && systemStatus.services.length > 0 ? (
                  <div className="space-y-3">
                    {systemStatus.services.map((service: any) => (
                      <div key={service.name} className="flex items-center justify-between p-3 border border-gray-700 rounded-lg bg-gray-800/50">
                        <div className="flex items-center gap-3">
                          {service.status === "running" ? (
                            <CheckCircle className="h-5 w-5 text-green-500" />
                          ) : (
                            <AlertCircle className="h-5 w-5 text-red-500" />
                          )}
                          <div>
                            <h3 className="font-medium text-white">{service.name}</h3>
                            <p className="text-sm text-gray-400">{service.description || ""}</p>
                          </div>
                        </div>
                        <Badge className={service.status === "running" ? "bg-green-900/20 text-green-400 border-green-800" : "bg-red-900/20 text-red-400 border-red-800"}>
                          {service.status}
                        </Badge>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-400">No service information available</p>
                )}
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </AdminLayout>
  )
}

