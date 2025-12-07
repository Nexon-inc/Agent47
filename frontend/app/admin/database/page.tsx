"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { 
  Database, 
  Activity,
  HardDrive,
  Clock,
  AlertTriangle,
  CheckCircle,
  Download,
  Upload,
  RefreshCw,
  Settings,
  BarChart3
} from "lucide-react"
import { useAdminStore } from "@/lib/stores/admin-store"
import { adminAPI } from "@/lib/services/admin-api"
import { usePolling } from "@/lib/hooks/use-polling"
import AdminLayout from "@/components/admin/layout"
import EmptyState from "@/components/admin/empty-state"
import { AlertCircle } from "lucide-react"

export default function AdminDatabasePage() {
  const [activeTab, setActiveTab] = useState("overview")
  const [error, setError] = useState<string | null>(null)
  
  const { currentAdmin } = useAdminStore()
  const hasAccess = currentAdmin?.permissions?.includes("super_admin")

  const [dbStatus, setDbStatus] = useState<any>(null)
  const [isLoadingStatus, setIsLoadingStatus] = useState(true)
  const [dbError, setDbError] = useState<any>(null)

  // Load initial data
  useEffect(() => {
    if (!currentAdmin || !hasAccess) return
    
    const loadData = async () => {
      try {
        setIsLoadingStatus(true)
        const data = await adminAPI.getDatabaseStatus()
        setDbStatus(data)
      } catch (err) {
        setDbError(err)
      } finally {
        setIsLoadingStatus(false)
      }
    }
    loadData()
  }, [currentAdmin, hasAccess])

  // Subscribe to real-time database updates via WebSocket
  useEffect(() => {
    if (!currentAdmin || !hasAccess) return

    const { websocketService } = require('@/lib/websocket-service')
    
    if (!websocketService.getConnectionStatus()) {
      websocketService.connect()
    }

    const unsubscribe = websocketService.subscribe('system_status', (message) => {
      if (message.data?.components?.supabase) {
        adminAPI.getDatabaseStatus().then(setDbStatus).catch(setDbError)
      }
    })

    return () => unsubscribe()
  }, [currentAdmin, hasAccess])

  const refetch = async () => {
    try {
      setIsLoadingStatus(true)
      const data = await adminAPI.getDatabaseStatus()
      setDbStatus(data)
    } catch (err) {
      setDbError(err)
    } finally {
      setIsLoadingStatus(false)
    }
  }

  useEffect(() => {
    if (dbError) {
      setError(dbError.message || "Failed to load database status")
    }
  }, [dbError])

  if (!hasAccess) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Database className="mx-auto h-12 w-12 text-gray-400" />
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
            <h1 className="text-3xl font-bold text-white mb-2">Database Management</h1>
            <p className="text-gray-400">Monitor and manage database performance</p>
          </div>
          <Button 
            onClick={() => refetch()} 
            disabled={isLoadingStatus}
            className="bg-gray-800 hover:bg-gray-700"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoadingStatus ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 bg-gray-800 p-1 rounded-lg">
          {[
            { id: "overview", name: "Overview", icon: BarChart3 },
            { id: "tables", name: "Tables", icon: Database },
            { id: "alerts", name: "Alerts", icon: AlertTriangle },
            { id: "backup", name: "Backup", icon: Download },
            { id: "migrations", name: "Migrations", icon: Settings }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? "bg-gray-700 text-white shadow-sm"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              <tab.icon className="h-4 w-4 mr-2" />
              {tab.name}
            </button>
          ))}
        </div>

        {error && !dbStatus ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <AlertCircle className="mx-auto h-12 w-12 text-red-400" />
              <h3 className="mt-2 text-sm font-medium text-white">Error Loading Database Status</h3>
              <p className="mt-1 text-sm text-gray-500">{error}</p>
              <Button onClick={() => refetch()} className="mt-4">
                Retry
              </Button>
            </div>
          </div>
        ) : isLoadingStatus && !dbStatus ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <RefreshCw className="h-8 w-8 text-gray-400 animate-spin mx-auto mb-2" />
              <p className="text-gray-400">Loading database status...</p>
            </div>
          </div>
        ) : (
          <>
            {activeTab === "overview" && (
              <div className="space-y-6">
                {/* Performance Metrics */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <Card className="bg-gray-900/50 border-gray-800">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium text-white">Active Connections</CardTitle>
                      <Activity className="h-4 w-4 text-green-500" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-white">
                        {dbStatus?.active_connections || dbStatus?.connections?.active || 0}
                      </div>
                      <p className="text-xs text-gray-400">
                        {dbStatus?.total_connections || dbStatus?.connections?.total || 0} total connections
                      </p>
                    </CardContent>
                  </Card>
                  
                  <Card className="bg-gray-900/50 border-gray-800">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium text-white">Queries/Second</CardTitle>
                      <BarChart3 className="h-4 w-4 text-blue-500" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-white">
                        {dbStatus?.queries_per_second?.toFixed(1) || dbStatus?.performance?.qps || 0}
                      </div>
                      <p className="text-xs text-gray-400">
                        Cache hit: {dbStatus?.cache_hit_rate?.toFixed(1) || dbStatus?.performance?.cache_hit || 0}%
                      </p>
                    </CardContent>
                  </Card>
                  
                  <Card className="bg-gray-900/50 border-gray-800">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium text-white">Disk Usage</CardTitle>
                      <HardDrive className="h-4 w-4 text-yellow-500" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-white">
                        {dbStatus?.disk_usage?.toFixed(1) || dbStatus?.storage?.usage_percent || 0}%
                      </div>
                      <Progress 
                        value={dbStatus?.disk_usage || dbStatus?.storage?.usage_percent || 0} 
                        className="mt-2" 
                      />
                    </CardContent>
                  </Card>
                  
                  <Card className="bg-gray-900/50 border-gray-800">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium text-white">Uptime</CardTitle>
                      <Clock className="h-4 w-4 text-purple-500" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-white">
                        {dbStatus?.uptime || "N/A"}
                      </div>
                      <p className="text-xs text-gray-400">
                        {dbStatus?.table_count || 0} tables, {dbStatus?.total_size || "0 GB"}
                      </p>
                    </CardContent>
                  </Card>
                </div>

                {/* System Resources */}
                <Card className="bg-gray-900/50 border-gray-800">
                  <CardHeader>
                    <CardTitle className="text-white">System Resources</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      <div>
                        <div className="flex justify-between text-sm mb-2 text-gray-300">
                          <span>CPU Usage</span>
                          <span>{dbStatus?.cpu_usage?.toFixed(1) || dbStatus?.resources?.cpu || 0}%</span>
                        </div>
                        <Progress value={dbStatus?.cpu_usage || dbStatus?.resources?.cpu || 0} className="h-2" />
                      </div>
                      <div>
                        <div className="flex justify-between text-sm mb-2 text-gray-300">
                          <span>Memory Usage</span>
                          <span>{dbStatus?.memory_usage?.toFixed(1) || dbStatus?.resources?.memory || 0}%</span>
                        </div>
                        <Progress value={dbStatus?.memory_usage || dbStatus?.resources?.memory || 0} className="h-2" />
                      </div>
                      <div>
                        <div className="flex justify-between text-sm mb-2 text-gray-300">
                          <span>Cache Hit Ratio</span>
                          <span>{dbStatus?.cache_hit_rate?.toFixed(1) || dbStatus?.performance?.cache_hit || 0}%</span>
                        </div>
                        <Progress value={dbStatus?.cache_hit_rate || dbStatus?.performance?.cache_hit || 0} className="h-2" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {activeTab === "tables" && (
              <Card className="bg-gray-900/50 border-gray-800">
                <CardHeader>
                  <CardTitle className="text-white">Database Tables</CardTitle>
                </CardHeader>
                <CardContent>
                  {dbStatus?.tables && dbStatus.tables.length > 0 ? (
                    <div className="space-y-4">
                      {dbStatus.tables.map((table: any) => (
                        <div key={table.name} className="flex items-center justify-between p-4 border border-gray-700 rounded-lg bg-gray-800/50">
                          <div className="flex items-center space-x-4">
                            <Database className="h-5 w-5 text-green-500" />
                            <div>
                              <h3 className="font-medium text-white">{table.name}</h3>
                              <p className="text-sm text-gray-400">
                                {table.rows?.toLocaleString() || 0} rows • {table.size || "N/A"}
                              </p>
                            </div>
                          </div>
                          <Badge className={table.status === "active" ? "bg-green-900/20 text-green-400 border-green-800" : "bg-gray-900/20 text-gray-400 border-gray-800"}>
                            {table.status || "unknown"}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <EmptyState
                      icon={Database}
                      title="No Tables Found"
                      description="Database table information will appear here."
                    />
                  )}
                </CardContent>
              </Card>
            )}

            {activeTab === "alerts" && (
              <Card>
                <CardHeader>
                  <CardTitle>Database Alerts</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-start justify-between p-4 border border-gray-200 rounded-lg">
                      <div className="flex items-start space-x-3">
                        <AlertTriangle className="h-5 w-5 text-yellow-500 mt-0.5" />
                        <div>
                          <h3 className="font-medium text-gray-900 dark:text-white">Database connections approaching limit</h3>
                          <p className="text-sm text-gray-500">
                            {new Date().toLocaleString()}
                          </p>
                        </div>
                      </div>
                      <Badge className="bg-yellow-100 text-yellow-800">warning</Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {activeTab === "backup" && (
              <Card className="bg-gray-900/50 border-gray-800">
                <CardHeader>
                  <CardTitle className="text-white">Database Backup</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <Button 
                        className="w-full bg-green-600 hover:bg-green-700"
                        onClick={async () => {
                          try {
                            await adminAPI.createDatabaseBackup()
                            alert("Backup created successfully")
                            refetch()
                          } catch (err) {
                            alert(`Failed to create backup: ${err instanceof Error ? err.message : 'Unknown error'}`)
                          }
                        }}
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Create Backup
                      </Button>
                      <Button variant="outline" className="w-full border-gray-700 text-white hover:bg-gray-800">
                        <Upload className="h-4 w-4 mr-2" />
                        Restore Backup
                      </Button>
                    </div>
                    <div className="p-4 bg-gray-800/50 rounded-lg border border-gray-700">
                      <h4 className="font-medium mb-2 text-white">Recent Backups</h4>
                      <p className="text-sm text-gray-400">No recent backups found.</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {activeTab === "migrations" && (
              <Card>
                <CardHeader>
                  <CardTitle>Database Migrations</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <Button className="w-full">
                        <Settings className="h-4 w-4 mr-2" />
                        Run Migrations
                      </Button>
                      <Button variant="outline" className="w-full">
                        <RefreshCw className="h-4 w-4 mr-2" />
                        Check Status
                      </Button>
                    </div>
                    <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <h4 className="font-medium mb-2">Migration Status</h4>
                      <p className="text-sm text-gray-500">All migrations are up to date.</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </>
        )}
      </div>
    </AdminLayout>
  )
} 
