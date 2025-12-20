"use client"

import { useState, useEffect } from "react"
import AdminLayout from "@/components/admin/layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { adminAPI } from "@/lib/services/admin-api"
import { useAdminStore } from "@/lib/stores/admin-store"
import { usePolling } from "@/lib/hooks/use-polling"
import { FileText, Filter, Download, RefreshCw, AlertCircle, Search } from "lucide-react"
import EmptyState from "@/components/admin/empty-state"

export default function LogsPage() {
  const { currentAdmin } = useAdminStore()
  const [logs, setLogs] = useState<any[]>([])
  const [filters, setFilters] = useState({
    level: "all",
    service: "all",
    search: ""
  })
  const [page, setPage] = useState(1)
  const [limit] = useState(100)
  const [error, setError] = useState<string | null>(null)

  const hasAccess = currentAdmin?.permissions?.includes("super_admin") || 
                    currentAdmin?.permissions?.includes("system_admin")

  // Poll logs every 5 seconds
  const { data: logsData, isLoading, error: logsError, refetch } = usePolling({
    fetchFn: async () => {
      try {
        return await adminAPI.getLogs(filters, page, limit)
      } catch (err) {
        throw err
      }
    },
    interval: 5000,
    enabled: !!currentAdmin && hasAccess
  })

  useEffect(() => {
    if (logsData) {
      setLogs(logsData.logs || logsData || [])
    }
    if (logsError) {
      setError(logsError.message || "Failed to load logs")
    }
  }, [logsData, logsError])

  if (!hasAccess) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <FileText className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-white">Access Denied</h3>
            <p className="mt-1 text-sm text-gray-500">You don't have permission to access logs.</p>
          </div>
        </div>
      </AdminLayout>
    )
  }

  if (error && !logs.length) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-red-400" />
            <h3 className="mt-2 text-sm font-medium text-white">Error Loading Logs</h3>
            <p className="mt-1 text-sm text-gray-500">{error}</p>
            <Button onClick={() => refetch()} className="mt-4">
              Retry
            </Button>
          </div>
        </div>
      </AdminLayout>
    )
  }

  const getLogLevelColor = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'error': return 'text-red-400 bg-red-900/20 border-red-800'
      case 'warning': return 'text-yellow-400 bg-yellow-900/20 border-yellow-800'
      case 'info': return 'text-blue-400 bg-blue-900/20 border-blue-800'
      case 'debug': return 'text-gray-400 bg-gray-900/20 border-gray-800'
      default: return 'text-gray-300 bg-gray-900/20 border-gray-800'
    }
  }

  return (
    <AdminLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Logs</h1>
            <p className="text-gray-400">View and analyze system logs</p>
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
            <Button className="bg-gray-800 hover:bg-gray-700">
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          </div>
        </div>

        {/* Filters */}
        <Card className="bg-gray-900/50 border-gray-800">
          <CardHeader>
            <CardTitle className="text-white">Filters</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search logs..."
                  value={filters.search}
                  onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                  className="pl-10 bg-gray-800 border-gray-700 text-white"
                />
              </div>
              <select
                value={filters.level}
                onChange={(e) => setFilters({ ...filters, level: e.target.value })}
                className="px-3 py-2 border border-gray-700 rounded-md text-sm bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                <option value="all">All Levels</option>
                <option value="error">Error</option>
                <option value="warning">Warning</option>
                <option value="info">Info</option>
                <option value="debug">Debug</option>
              </select>
              <select
                value={filters.service}
                onChange={(e) => setFilters({ ...filters, service: e.target.value })}
                className="px-3 py-2 border border-gray-700 rounded-md text-sm bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                <option value="all">All Services</option>
                <option value="backend">Backend</option>
                <option value="agents">Agents</option>
                <option value="database">Database</option>
                <option value="api">API</option>
              </select>
            </div>
          </CardContent>
        </Card>

        {/* Logs List */}
        {isLoading && !logs.length ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <RefreshCw className="h-8 w-8 text-gray-400 animate-spin mx-auto mb-2" />
              <p className="text-gray-400">Loading logs...</p>
            </div>
          </div>
        ) : logs.length === 0 ? (
          <EmptyState
            icon={FileText}
            title="No Logs Available"
            description="System logs will appear here once available."
          />
        ) : (
          <Card className="bg-gray-900/50 border-gray-800">
            <CardHeader>
              <CardTitle className="text-white">System Logs ({logs.length})</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-[600px] overflow-y-auto scrollbar-hide">
                {logs.map((log: any, index: number) => (
                  <div
                    key={index}
                    className={`p-3 rounded-lg border ${getLogLevelColor(log.level || log.severity || 'info')}`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-semibold uppercase">
                            {log.level || log.severity || 'INFO'}
                          </span>
                          <span className="text-xs text-gray-500">
                            {log.service || log.module || 'System'}
                          </span>
                          <span className="text-xs text-gray-500">
                            {log.timestamp ? new Date(log.timestamp).toLocaleString() : ''}
                          </span>
                        </div>
                        <p className="text-sm text-gray-300 whitespace-pre-wrap">
                          {log.message || log.content || JSON.stringify(log)}
                        </p>
                        {log.details && (
                          <details className="mt-2">
                            <summary className="text-xs text-gray-500 cursor-pointer">Details</summary>
                            <pre className="mt-2 text-xs bg-gray-950 p-2 rounded overflow-x-auto">
                              {JSON.stringify(log.details, null, 2)}
                            </pre>
                          </details>
                        )}
                      </div>
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

