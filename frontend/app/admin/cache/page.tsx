"use client"

import { useState, useEffect } from "react"
import AdminLayout from "@/components/admin/layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { adminAPI } from "@/lib/services/admin-api"
import { useAdminStore } from "@/lib/stores/admin-store"
import { usePolling } from "@/lib/hooks/use-polling"
import EmptyState from "@/components/admin/empty-state"
import { Activity, Trash2, RefreshCw, AlertCircle } from "lucide-react"

export default function CachePage() {
  const { currentAdmin } = useAdminStore()
  const [error, setError] = useState<string | null>(null)
  const [isClearing, setIsClearing] = useState(false)

  const hasAccess = currentAdmin?.permissions?.includes("super_admin") || 
                    currentAdmin?.permissions?.includes("system_admin")

  const [cacheStats, setCacheStats] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [cacheError, setCacheError] = useState<any>(null)

  // Load initial data
  useEffect(() => {
    if (!currentAdmin || !hasAccess) return
    
    const loadData = async () => {
      try {
        setIsLoading(true)
        const data = await adminAPI.getCacheStatistics()
        setCacheStats(data)
      } catch (err) {
        setCacheError(err)
      } finally {
        setIsLoading(false)
      }
    }
    loadData()
  }, [currentAdmin, hasAccess])

  // Subscribe to real-time cache updates via WebSocket
  useEffect(() => {
    if (!currentAdmin || !hasAccess) return

    const { websocketService } = require('@/lib/websocket-service')
    
    if (!websocketService.getConnectionStatus()) {
      websocketService.connect()
    }

    const unsubscribe = websocketService.subscribe('system_status', (message) => {
      if (message.data?.components?.redis) {
        adminAPI.getCacheStatistics().then(setCacheStats).catch(setCacheError)
      }
    })

    return () => unsubscribe()
  }, [currentAdmin, hasAccess])

  const refetch = async () => {
    try {
      setIsLoading(true)
      const data = await adminAPI.getCacheStatistics()
      setCacheStats(data)
    } catch (err) {
      setCacheError(err)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (cacheError) {
      setError(cacheError.message || "Failed to load cache statistics")
    }
  }, [cacheError])

  const handleClearCache = async () => {
    if (!confirm("Are you sure you want to clear all cache?")) return
    
    setIsClearing(true)
    try {
      await adminAPI.clearCache()
      alert("Cache cleared successfully")
      refetch()
    } catch (err) {
      alert(`Failed to clear cache: ${err instanceof Error ? err.message : 'Unknown error'}`)
    } finally {
      setIsClearing(false)
    }
  }

  if (!hasAccess) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Activity className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-white">Access Denied</h3>
            <p className="mt-1 text-sm text-gray-500">You don't have permission to access cache management.</p>
          </div>
        </div>
      </AdminLayout>
    )
  }

  if (error && !cacheStats) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-red-400" />
            <h3 className="mt-2 text-sm font-medium text-white">Error Loading Cache Statistics</h3>
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
            <h1 className="text-3xl font-bold text-white mb-2">Cache Management</h1>
            <p className="text-gray-400">Monitor and manage system cache</p>
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
            <Button 
              onClick={handleClearCache}
              disabled={isClearing}
              className="bg-red-600 hover:bg-red-700"
            >
              <Trash2 className={`w-4 h-4 mr-2 ${isClearing ? 'animate-spin' : ''}`} />
              Clear Cache
            </Button>
          </div>
        </div>

        {isLoading && !cacheStats ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <RefreshCw className="h-8 w-8 text-gray-400 animate-spin mx-auto mb-2" />
              <p className="text-gray-400">Loading cache statistics...</p>
            </div>
          </div>
        ) : !cacheStats ? (
          <EmptyState
            icon={Activity}
            title="No Cache Data"
            description="Cache statistics will appear here once available."
          />
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card className="bg-gray-900/50 border-gray-800 p-6">
                <div className="flex items-center justify-between mb-4">
                  <Activity className="w-8 h-8 text-blue-500" />
                  <span className="text-sm text-gray-400">Hit Rate</span>
                </div>
                <div className="text-3xl font-bold text-white">
                  {cacheStats?.hit_rate?.toFixed(1) || cacheStats?.statistics?.hit_rate?.toFixed(1) || 0}%
                </div>
                <div className="text-sm text-gray-400 mt-2">Cache hit rate</div>
              </Card>

              <Card className="bg-gray-900/50 border-gray-800 p-6">
                <div className="flex items-center justify-between mb-4">
                  <Activity className="w-8 h-8 text-green-500" />
                  <span className="text-sm text-gray-400">Entries</span>
                </div>
                <div className="text-3xl font-bold text-white">
                  {cacheStats?.entries || cacheStats?.statistics?.entries || 0}
                </div>
                <div className="text-sm text-gray-400 mt-2">Cached entries</div>
              </Card>

              <Card className="bg-gray-900/50 border-gray-800 p-6">
                <div className="flex items-center justify-between mb-4">
                  <Activity className="w-8 h-8 text-yellow-500" />
                  <span className="text-sm text-gray-400">Size</span>
                </div>
                <div className="text-3xl font-bold text-white">
                  {cacheStats?.size_mb?.toFixed(1) || cacheStats?.statistics?.size_mb?.toFixed(1) || 0} MB
                </div>
                <div className="text-sm text-gray-400 mt-2">Cache size</div>
              </Card>
            </div>

            {cacheStats?.cache_types && Object.keys(cacheStats.cache_types).length > 0 && (
              <Card className="bg-gray-900/50 border-gray-800">
                <CardHeader>
                  <CardTitle className="text-white">Cache by Type</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {Object.entries(cacheStats.cache_types).map(([type, stats]: [string, any]) => (
                      <div key={type} className="flex items-center justify-between p-3 border border-gray-700 rounded-lg bg-gray-800/50">
                        <div>
                          <h3 className="font-medium text-white">{type}</h3>
                          <p className="text-sm text-gray-400">
                            {stats.entries || 0} entries • {stats.size_mb?.toFixed(2) || 0} MB
                          </p>
                        </div>
                        <span className="text-sm text-gray-400">
                          {stats.hit_rate?.toFixed(1) || 0}% hit rate
                        </span>
                      </div>
                    ))}
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

