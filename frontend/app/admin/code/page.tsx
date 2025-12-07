"use client"

import { useState, useEffect } from "react"
import AdminLayout from "@/components/admin/layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { adminAPI } from "@/lib/services/admin-api"
import { useAdminStore } from "@/lib/stores/admin-store"
import { usePolling } from "@/lib/hooks/use-polling"
import { FileText, AlertCircle, CheckCircle, RefreshCw, Code2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

export default function CodePage() {
  const { currentAdmin } = useAdminStore()
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const hasAccess = currentAdmin?.permissions?.includes("super_admin")

  const { data: healthData, isLoading: isLoadingHealth, error: healthError, refetch: refetchHealth } = usePolling({
    fetchFn: async () => await adminAPI.getCodeHealth(),
    interval: 60000,
    enabled: hasAccess
  })

  useEffect(() => {
    setIsLoading(isLoadingHealth)
  }, [isLoadingHealth])

  useEffect(() => {
    if (healthError) {
      setError(healthError.message || "Failed to load code health data")
    } else {
      setError(null)
    }
  }, [healthError])

  if (isLoading) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-400">Loading...</div>
        </div>
      </AdminLayout>
    )
  }

  if (!hasAccess) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <FileText className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-white">Access Denied</h3>
            <p className="mt-1 text-sm text-gray-500">Super admin access required.</p>
          </div>
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

  if (!hasAccess) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <FileText className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-white">Access Denied</h3>
            <p className="mt-1 text-sm text-gray-500">Super admin access required.</p>
          </div>
        </div>
      </AdminLayout>
    )
  }

  if (isLoading) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
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
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Code Management</h1>
            <p className="text-gray-400">Monitor code health and errors</p>
          </div>
          <Button onClick={() => refetchHealth()} disabled={isLoading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {/* Health Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Code Health Score</CardTitle>
              <Code2 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {healthData?.health_score?.toFixed(1) || '0.0'}%
              </div>
              <p className="text-xs text-muted-foreground">Overall code quality</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Errors</CardTitle>
              <AlertCircle className="h-4 w-4 text-red-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">
                {healthData?.total_errors || 0}
              </div>
              <p className="text-xs text-muted-foreground">Active issues</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Code Quality</CardTitle>
              <CheckCircle className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {healthData?.code_quality || 'N/A'}
              </div>
              <p className="text-xs text-muted-foreground">Current status</p>
            </CardContent>
          </Card>
        </div>

        {/* Health Details */}
        {healthData && (
          <Card>
            <CardHeader>
              <CardTitle>Code Health Details</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {healthData.error_summary && (
                  <div>
                    <div className="font-medium mb-2">Error Summary</div>
                    <div className="space-y-2">
                      {Object.entries(healthData.error_summary).map(([key, value]: [string, any]) => (
                        <div key={key} className="flex justify-between items-center p-2 border rounded">
                          <span className="text-sm">{key}</span>
                          <Badge variant="destructive">{value}</Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {healthData.metrics && (
                  <div>
                    <div className="font-medium mb-2">Metrics</div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      {Object.entries(healthData.metrics).map(([key, value]: [string, any]) => (
                        <div key={key} className="p-2 border rounded">
                          <div className="text-sm text-muted-foreground">{key}</div>
                          <div className="text-lg font-bold">{value}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </AdminLayout>
  )
}

