"use client"

import { useState, useEffect } from "react"
import AdminLayout from "@/components/admin/layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { adminAPI } from "@/lib/services/admin-api"
import { useAdminStore } from "@/lib/stores/admin-store"
import { usePolling } from "@/lib/hooks/use-polling"
import EmptyState from "@/components/admin/empty-state"
import { Server, Plus, Activity, RefreshCw, AlertCircle, X } from "lucide-react"

export default function PlatformsPage() {
  const { currentAdmin } = useAdminStore()
  const [error, setError] = useState<string | null>(null)

  const hasAccess = currentAdmin?.permissions?.includes("super_admin")

  const { data: connectionsData, isLoading, error: connectionsError, refetch } = usePolling({
    fetchFn: async () => {
      try {
        return await adminAPI.getPlatformConnections(true)
      } catch (err) {
        throw err
      }
    },
    interval: 30000,
    enabled: !!currentAdmin && hasAccess
  })

  useEffect(() => {
    if (connectionsError) {
      setError(connectionsError.message || "Failed to load platform connections")
    }
  }, [connectionsError])

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

  const connections = connectionsData?.connections || []
  const totalConnections = connectionsData?.total || connections.length
  const activeConnections = connections.filter((c: any) => c.is_active).length

  if (error && connections.length === 0) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-red-400" />
            <h3 className="mt-2 text-sm font-medium text-white">Error Loading Platforms</h3>
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
            <h1 className="text-3xl font-bold text-white mb-2">Platforms</h1>
            <p className="text-gray-400">Manage platform connections and assignments</p>
          </div>
          <div className="flex gap-2">
            <Button 
              onClick={() => refetch()} 
              disabled={isLoading}
              className="bg-gray-800 hover:bg-gray-700"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button className="bg-green-600 hover:bg-green-700">
              <Plus className="w-4 h-4 mr-2" />
              Connect Platform
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="bg-gray-900/50 border-gray-800 p-6">
            <div className="flex items-center justify-between mb-4">
              <Server className="w-8 h-8 text-green-500" />
              <span className="text-sm text-gray-400">Total</span>
            </div>
            <div className="text-3xl font-bold text-white">{totalConnections}</div>
            <div className="text-sm text-gray-400 mt-2">Connected platforms</div>
          </Card>

          <Card className="bg-gray-900/50 border-gray-800 p-6">
            <div className="flex items-center justify-between mb-4">
              <Activity className="w-8 h-8 text-blue-500" />
              <span className="text-sm text-gray-400">Active</span>
            </div>
            <div className="text-3xl font-bold text-white">{activeConnections}</div>
            <div className="text-sm text-gray-400 mt-2">Active connections</div>
          </Card>
        </div>

        {isLoading && connections.length === 0 ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <RefreshCw className="h-8 w-8 text-gray-400 animate-spin mx-auto mb-2" />
              <p className="text-gray-400">Loading platforms...</p>
            </div>
          </div>
        ) : connections.length === 0 ? (
          <EmptyState
            icon={Server}
            title="No Platforms Connected"
            description="Connect platforms to enable agent integrations"
          />
        ) : (
          <Card className="bg-gray-900/50 border-gray-800">
            <CardHeader>
              <CardTitle className="text-white">Platform Connections</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {connections.map((connection: any) => (
                  <div key={connection.id} className="flex items-center justify-between p-4 border border-gray-700 rounded-lg bg-gray-800/50">
                    <div className="flex items-center gap-4">
                      <Server className="h-6 w-6 text-green-500" />
                      <div>
                        <h3 className="font-medium text-white">{connection.platform_display_name || connection.platform}</h3>
                        <p className="text-sm text-gray-400">
                          {connection.account_name}
                          {connection.account_handle && ` (@${connection.account_handle})`}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          {connection.assigned_agents?.length || 0} agent(s) assigned
                          {connection.last_used && ` • Last used: ${new Date(connection.last_used).toLocaleString()}`}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge className={connection.is_active ? "bg-green-900/20 text-green-400 border-green-800" : "bg-gray-900/20 text-gray-400 border-gray-800"}>
                        {connection.status || (connection.is_active ? "active" : "inactive")}
                      </Badge>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={async () => {
                          if (confirm(`Disconnect ${connection.platform_display_name || connection.platform}?`)) {
                            try {
                              await adminAPI.disconnectPlatform(connection.id)
                              refetch()
                            } catch (err) {
                              alert(`Failed to disconnect: ${err instanceof Error ? err.message : 'Unknown error'}`)
                            }
                          }
                        }}
                        className="text-red-400 hover:text-red-300"
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </AdminLayout>
  )
}

