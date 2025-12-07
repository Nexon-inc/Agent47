"use client"

import { useState, useEffect } from "react"
import AdminLayout from "@/components/admin/layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import EmptyState from "@/components/admin/empty-state"
import { Shield, AlertTriangle, Lock, Eye, UserCheck, RefreshCw, AlertCircle } from "lucide-react"
import { useAdminStore } from "@/lib/stores/admin-store"
import { adminAPI } from "@/lib/services/admin-api"
import { usePolling } from "@/lib/hooks/use-polling"

export default function AdminSecurityPage() {
  const { currentAdmin } = useAdminStore()
  const [error, setError] = useState<string | null>(null)
  const [auditLogs, setAuditLogs] = useState<any[]>([])
  const [threats, setThreats] = useState<any[]>([])

  const hasAccess = currentAdmin?.permissions?.includes("super_admin")

  const { data: auditData, isLoading: isLoadingAudit, error: auditError, refetch: refetchAudit } = usePolling({
    fetchFn: async () => {
      try {
        return await adminAPI.getAuditLogs(1, 50)
      } catch (err) {
        throw err
      }
    },
    interval: 15000,
    enabled: !!currentAdmin && hasAccess
  })

  const { data: threatsData, isLoading: isLoadingThreats, error: threatsError, refetch: refetchThreats } = usePolling({
    fetchFn: async () => {
      try {
        return await adminAPI.getSecurityThreats()
      } catch (err) {
        throw err
      }
    },
    interval: 20000,
    enabled: !!currentAdmin && hasAccess
  })

  useEffect(() => {
    if (auditData) {
      setAuditLogs(auditData.logs || auditData || [])
    }
    if (threatsData) {
      setThreats(threatsData.threats || threatsData || [])
    }
    if (auditError || threatsError) {
      setError(auditError?.message || threatsError?.message || "Failed to load security data")
    }
  }, [auditData, threatsData, auditError, threatsError])

  if (!hasAccess) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Shield className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-white">Access Denied</h3>
            <p className="mt-1 text-sm text-gray-500">Super admin access required.</p>
          </div>
        </div>
      </AdminLayout>
    )
  }

  const isLoading = isLoadingAudit || isLoadingThreats

  if (error && auditLogs.length === 0 && threats.length === 0) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-red-400" />
            <h3 className="mt-2 text-sm font-medium text-white">Error Loading Security Data</h3>
            <p className="mt-1 text-sm text-gray-500">{error}</p>
            <Button onClick={() => { refetchAudit(); refetchThreats(); }} className="mt-4">
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
            <h1 className="text-3xl font-bold text-white mb-2">Security Dashboard</h1>
            <p className="text-gray-400">Monitor and manage system security</p>
          </div>
          <Button 
            onClick={() => { refetchAudit(); refetchThreats(); }} 
            disabled={isLoading}
            className="bg-gray-800 hover:bg-gray-700"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {/* Security Threats */}
        <Card className="bg-gray-900/50 border-gray-800">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
              Security Threats ({threats.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoadingThreats && threats.length === 0 ? (
              <div className="flex items-center justify-center py-8">
                <RefreshCw className="h-6 w-6 text-gray-400 animate-spin" />
              </div>
            ) : threats.length === 0 ? (
              <div className="text-center py-8">
                <Shield className="h-12 w-12 text-green-500 mx-auto mb-2" />
                <p className="text-gray-400">No security threats detected</p>
              </div>
            ) : (
              <div className="space-y-3">
                {threats.map((threat: any, index: number) => (
                  <div key={index} className="flex items-center justify-between p-3 border border-red-800 rounded-lg bg-red-900/20">
                    <div className="flex items-center gap-3">
                      <AlertTriangle className="h-5 w-5 text-red-500" />
                      <div>
                        <h3 className="font-medium text-white">{threat.type || threat.title || "Security Threat"}</h3>
                        <p className="text-sm text-gray-400">{threat.description || threat.message || ""}</p>
                        <p className="text-xs text-gray-500 mt-1">
                          {threat.timestamp ? new Date(threat.timestamp).toLocaleString() : ""}
                        </p>
                      </div>
                    </div>
                    <Badge className="bg-red-900/20 text-red-400 border-red-800">
                      {threat.severity || "high"}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Audit Logs */}
        <Card className="bg-gray-900/50 border-gray-800">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Eye className="h-5 w-5 text-blue-500" />
              Audit Logs ({auditLogs.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoadingAudit && auditLogs.length === 0 ? (
              <div className="flex items-center justify-center py-8">
                <RefreshCw className="h-6 w-6 text-gray-400 animate-spin" />
              </div>
            ) : auditLogs.length === 0 ? (
              <EmptyState
                icon={Eye}
                title="No Audit Logs"
                description="Security audit logs will appear here."
              />
            ) : (
              <div className="space-y-2 max-h-[600px] overflow-y-auto scrollbar-hide">
                {auditLogs.map((log: any, index: number) => (
                  <div key={index} className="flex items-center justify-between p-3 border border-gray-700 rounded-lg bg-gray-800/50">
                    <div className="flex items-center gap-3">
                      {log.action_type === "login" ? (
                        <UserCheck className="h-4 w-4 text-green-500" />
                      ) : log.action_type === "logout" ? (
                        <Lock className="h-4 w-4 text-gray-500" />
                      ) : (
                        <Eye className="h-4 w-4 text-blue-500" />
                      )}
                      <div>
                        <p className="text-sm font-medium text-white">{log.action || log.description || "Security Event"}</p>
                        <p className="text-xs text-gray-400">
                          {log.user_id || log.admin_id || "System"} • {log.ip_address || ""}
                        </p>
                        <p className="text-xs text-gray-500">
                          {log.timestamp ? new Date(log.timestamp).toLocaleString() : ""}
                        </p>
                      </div>
                    </div>
                    <Badge className="bg-gray-900/20 text-gray-400 border-gray-800">
                      {log.action_type || "event"}
                    </Badge>
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

