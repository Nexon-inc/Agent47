"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { 
  Server, 
  Database, 
  Activity,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Wifi,
  HardDrive,
  Cpu,
  Memory
} from "lucide-react"

interface SystemStatus {
  servers: {
    [key: string]: {
      status: 'online' | 'offline' | 'warning'
      cpu: number
      memory: number
      disk: number
      uptime: number
      response_time: number
    }
  }
  database: {
    status: 'healthy' | 'warning' | 'error'
    connections: number
    queries_per_second: number
    response_time: number
    disk_usage: number
  }
  alerts: {
    critical: number
    warning: number
    info: number
  }
  overall_status: 'healthy' | 'warning' | 'error'
}

export default function SystemStatus() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())

  useEffect(() => {
    fetchSystemStatus()
  }, [])

  // Subscribe to real-time system status updates via WebSocket
  useEffect(() => {
    const { websocketService } = require('@/lib/websocket-service')
    
    if (!websocketService.getConnectionStatus()) {
      websocketService.connect()
    }

    // Update system status when WebSocket sends system_status messages
    const unsubscribe = websocketService.subscribe('system_status', (message) => {
      if (message.data) {
        const healthData = message.data
        const systemStatus: SystemStatus = {
          servers: {
            'api-server': {
              status: healthData.status === 'healthy' ? 'online' : healthData.status === 'degraded' ? 'warning' : 'offline',
              cpu: 0,
              memory: 0,
              disk: 0,
              uptime: 0
            }
          },
          database: {
            status: healthData.components?.supabase === 'healthy' ? 'healthy' : healthData.components?.supabase === 'unhealthy' ? 'error' : 'warning',
            connections: 0,
            queries_per_second: 0
          },
          alerts: {
            critical: 0,
            warning: healthData.status === 'degraded' ? 1 : 0,
            info: 0
          },
          overall_status: healthData.status === 'healthy' ? 'healthy' : healthData.status === 'degraded' ? 'warning' : 'error'
        }
        setSystemStatus(systemStatus)
        setLastUpdate(new Date())
      }
    })

    return () => unsubscribe()
  }, [])

  const fetchSystemStatus = async () => {
    try {
      // Fetch real system status from backend health endpoint
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/health`)
      
      if (!response.ok) {
        throw new Error(`Health check failed: ${response.status}`)
      }

      const healthData = await response.json()
      
      // Transform health data to our SystemStatus format
      const systemStatus: SystemStatus = {
        servers: {
          'api-server': {
            status: healthData.status === 'healthy' ? 'online' : healthData.status === 'degraded' ? 'warning' : 'offline',
            cpu: 0, // Not available from health endpoint
            memory: 0, // Not available from health endpoint
            disk: 0, // Not available from health endpoint
            uptime: 0, // Not available from health endpoint
            response_time: 0 // Not available from health endpoint
          }
        },
        database: {
          status: healthData.components?.supabase === 'healthy' ? 'healthy' : 
                  healthData.components?.supabase === 'unhealthy' ? 'error' : 'warning',
          connections: 0, // Not available from health endpoint
          queries_per_second: 0, // Not available from health endpoint
          response_time: 0, // Not available from health endpoint
          disk_usage: 0 // Not available from health endpoint
        },
        alerts: {
          critical: healthData.status === 'unhealthy' ? 1 : 0,
          warning: healthData.status === 'degraded' ? 1 : 0,
          info: 0
        },
        overall_status: healthData.status === 'healthy' ? 'healthy' : 
                       healthData.status === 'degraded' ? 'warning' : 'error'
      }

      // Add agent servers if available
      if (healthData.components?.agents) {
        Object.entries(healthData.components.agents).forEach(([agentName, agentData]: [string, any]) => {
          systemStatus.servers[`agent-${agentName}`] = {
            status: agentData.status === 'running' ? 'online' : 'offline',
            cpu: 0,
            memory: 0,
            disk: 0,
            uptime: 0,
            response_time: 0
          }
        })
      }

      setSystemStatus(systemStatus)
      setLastUpdate(new Date())
    } catch (error) {
      console.error("Failed to fetch system status:", error)
      // Set error state
      setSystemStatus({
        servers: {},
        database: {
          status: 'error',
          connections: 0,
          queries_per_second: 0,
          response_time: 0,
          disk_usage: 0
        },
        alerts: {
          critical: 1,
          warning: 0,
          info: 0
        },
        overall_status: 'error'
      })
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
      case 'healthy':
        return 'text-green-600'
      case 'warning':
        return 'text-yellow-600'
      case 'offline':
      case 'error':
        return 'text-red-600'
      default:
        return 'text-gray-600'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online':
      case 'healthy':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />
      case 'offline':
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />
      default:
        return <Activity className="h-4 w-4 text-gray-500" />
    }
  }

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400)
    const hours = Math.floor((seconds % 86400) / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    
    if (days > 0) return `${days}d ${hours}h`
    if (hours > 0) return `${hours}h ${minutes}m`
    return `${minutes}m`
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            System Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!systemStatus) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            System Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <XCircle className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">Status Unavailable</h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Unable to fetch system status
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            System Status
          </div>
          <div className="flex items-center gap-2">
            <Badge className={
              systemStatus.overall_status === 'healthy' ? 'bg-green-100 text-green-800' :
              systemStatus.overall_status === 'warning' ? 'bg-yellow-100 text-yellow-800' :
              'bg-red-100 text-red-800'
            }>
              {systemStatus.overall_status}
            </Badge>
            <span className="text-xs text-gray-500">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </span>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Database Status */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-medium flex items-center gap-2">
              <Database className="h-4 w-4" />
              Database
            </h3>
            <div className="flex items-center gap-2">
              {getStatusIcon(systemStatus.database.status)}
              <span className={`text-sm font-medium ${getStatusColor(systemStatus.database.status)}`}>
                {systemStatus.database.status}
              </span>
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-lg font-bold">{systemStatus.database.connections}</div>
              <div className="text-xs text-gray-500">Connections</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold">{systemStatus.database.queries_per_second}</div>
              <div className="text-xs text-gray-500">QPS</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold">{systemStatus.database.response_time.toFixed(1)}ms</div>
              <div className="text-xs text-gray-500">Response</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold">{systemStatus.database.disk_usage.toFixed(1)}%</div>
              <div className="text-xs text-gray-500">Disk</div>
            </div>
          </div>
        </div>

        {/* Servers Status */}
        <div>
          <h3 className="font-medium flex items-center gap-2 mb-3">
            <Server className="h-4 w-4" />
            Servers
          </h3>
          <div className="space-y-3">
            {Object.entries(systemStatus.servers).map(([name, server]) => (
              <div key={name} className="border rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Server className="h-4 w-4" />
                    <span className="font-medium text-sm">{name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {getStatusIcon(server.status)}
                    <span className={`text-sm font-medium ${getStatusColor(server.status)}`}>
                      {server.status}
                    </span>
                  </div>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                  <div>
                    <div className="flex items-center gap-1 mb-1">
                      <Cpu className="h-3 w-3" />
                      <span>CPU</span>
                    </div>
                    <Progress value={server.cpu} className="h-2" />
                    <span className="text-gray-500">{server.cpu.toFixed(1)}%</span>
                  </div>
                  <div>
                    <div className="flex items-center gap-1 mb-1">
                      <Memory className="h-3 w-3" />
                      <span>Memory</span>
                    </div>
                    <Progress value={server.memory} className="h-2" />
                    <span className="text-gray-500">{server.memory.toFixed(1)}%</span>
                  </div>
                  <div>
                    <div className="flex items-center gap-1 mb-1">
                      <HardDrive className="h-3 w-3" />
                      <span>Disk</span>
                    </div>
                    <Progress value={server.disk} className="h-2" />
                    <span className="text-gray-500">{server.disk.toFixed(1)}%</span>
                  </div>
                  <div>
                    <div className="flex items-center gap-1 mb-1">
                      <Wifi className="h-3 w-3" />
                      <span>Uptime</span>
                    </div>
                    <div className="text-gray-500">{formatUptime(server.uptime)}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Alerts Summary */}
        <div>
          <h3 className="font-medium mb-3">Active Alerts</h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
              <div className="text-lg font-bold text-red-600">{systemStatus.alerts.critical}</div>
              <div className="text-xs text-gray-500">Critical</div>
            </div>
            <div className="text-center p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
              <div className="text-lg font-bold text-yellow-600">{systemStatus.alerts.warning}</div>
              <div className="text-xs text-gray-500">Warning</div>
            </div>
            <div className="text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <div className="text-lg font-bold text-blue-600">{systemStatus.alerts.info}</div>
              <div className="text-xs text-gray-500">Info</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
