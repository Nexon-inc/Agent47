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
import { Zap, ToggleLeft, ToggleRight, RefreshCw, AlertCircle, Plus } from "lucide-react"

export default function FeaturesPage() {
  const { currentAdmin } = useAdminStore()
  const [error, setError] = useState<string | null>(null)

  const hasAccess = currentAdmin?.permissions?.includes("super_admin") ||
    currentAdmin?.permissions?.includes("system_admin")

  const { data: featuresData, isLoading, error: featuresError, refetch } = usePolling({
    fetchFn: async () => {
      try {
        return await adminAPI.getFeatureFlags()
      } catch (err) {
        throw err
      }
    },
    interval: 30000,
    enabled: !!currentAdmin && hasAccess
  })

  useEffect(() => {
    if (featuresError) {
      setError(featuresError.message || "Failed to load feature flags")
    }
  }, [featuresError])

  const features = featuresData?.features || featuresData || []

  if (!hasAccess) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Zap className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-white">Access Denied</h3>
            <p className="mt-1 text-sm text-gray-500">You don't have permission to access feature flags.</p>
          </div>
        </div>
      </AdminLayout>
    )
  }

  if (error && features.length === 0) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-red-400" />
            <h3 className="mt-2 text-sm font-medium text-white">Error Loading Feature Flags</h3>
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
            <h1 className="text-3xl font-bold text-white mb-2">Feature Flags</h1>
            <p className="text-gray-400">Manage feature toggles and rollouts</p>
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
              Create Flag
            </Button>
          </div>
        </div>

        {isLoading && features.length === 0 ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <RefreshCw className="h-8 w-8 text-gray-400 animate-spin mx-auto mb-2" />
              <p className="text-gray-400">Loading feature flags...</p>
            </div>
          </div>
        ) : features.length === 0 ? (
          <EmptyState
            icon={Zap}
            title="No Feature Flags"
            description="Feature flags will appear here once created."
          />
        ) : (
          // Features List
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {(featuresData && (Array.isArray(featuresData.features) ? featuresData.features : (Array.isArray(featuresData) ? featuresData : []))).map((feature: any) => (
              <Card key={feature.key || feature.id || feature.name} className="bg-gray-900/50 border-gray-800">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <Zap className="h-5 w-5 text-yellow-500" />
                      <div>
                        <h3 className="font-medium text-white">{feature.name || feature.key}</h3>
                        <p className="text-sm text-gray-400">{feature.description || ""}</p>
                        <p className="text-xs text-gray-500 mt-1">
                          Key: {feature.key} • Created: {feature.created_at ? new Date(feature.created_at).toLocaleDateString() : "N/A"}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge className={feature.enabled ? "bg-green-900/20 text-green-400 border-green-800" : "bg-gray-900/20 text-gray-400 border-gray-800"}>
                        {feature.enabled ? "Enabled" : "Disabled"}
                      </Badge>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={async () => {
                          try {
                            await adminAPI.updateFeatureFlag(feature.key, { enabled: !feature.enabled })
                            refetch()
                          } catch (err) {
                            alert(`Failed to toggle feature: ${err instanceof Error ? err.message : 'Unknown error'}`)
                          }
                        }}
                      >
                        {feature.enabled ? (
                          <ToggleRight className="w-5 h-5 text-green-500" />
                        ) : (
                          <ToggleLeft className="w-5 h-5 text-gray-500" />
                        )}
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </AdminLayout>
  )
}

