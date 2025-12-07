"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import {
  LayoutDashboard,
  Users,
  Bot,
  Activity,
  Shield,
  Zap,
  Server,
  Database,
} from "lucide-react"
import AdminLayout from "@/components/admin/layout"
import { Card } from "@/components/ui/card"
import { useAdminStore } from "@/lib/stores/admin-store"
import { adminAPI } from "@/lib/services/admin-api"

export default function AdminPage() {
  const router = useRouter()
  const { currentAdmin, isAuthenticated, fetchCurrentAdmin } = useAdminStore()
  const [stats, setStats] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)
  
  useEffect(() => {
    const token = localStorage.getItem("admin_token")
    if (!token) {
      router.push("/admin/login")
      return
    }

    // Fetch current admin and stats
    const loadData = async () => {
      try {
        await fetchCurrentAdmin()
        const health = await adminAPI.getHealth().catch(() => null)
        const metrics = await adminAPI.getMetrics().catch(() => null)
        setStats({ health, metrics })
      } catch (error) {
        console.error("Failed to load admin data:", error)
        router.push("/admin/login")
      } finally {
        setIsLoading(false)
      }
    }

    loadData()
  }, [router, fetchCurrentAdmin])

  if (isLoading) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-400">Loading dashboard...</div>
        </div>
      </AdminLayout>
    )
  }

  return (
    <AdminLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Admin Dashboard</h1>
          <p className="text-gray-400">
            Welcome back, {currentAdmin?.email || "Admin"}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="bg-gray-900/50 border-gray-800 p-6 hover:border-green-500/50 transition-colors">
            <div className="flex items-center justify-between mb-4">
              <Users className="w-8 h-8 text-green-500" />
              <span className="text-sm text-gray-400">Users</span>
            </div>
            <div className="text-3xl font-bold text-white">
              {stats?.metrics?.total_users || 0}
            </div>
            <div className="text-sm text-gray-400 mt-2">Total users</div>
          </Card>

          <Card className="bg-gray-900/50 border-gray-800 p-6 hover:border-green-500/50 transition-colors">
            <div className="flex items-center justify-between mb-4">
              <Bot className="w-8 h-8 text-green-500" />
              <span className="text-sm text-gray-400">Agents</span>
            </div>
            <div className="text-3xl font-bold text-white">
              {stats?.metrics?.active_agents || 0}
            </div>
            <div className="text-sm text-gray-400 mt-2">Active agents</div>
          </Card>

          <Card className="bg-gray-900/50 border-gray-800 p-6 hover:border-yellow-500/50 transition-colors">
            <div className="flex items-center justify-between mb-4">
              <Activity className="w-8 h-8 text-yellow-500" />
              <span className="text-sm text-gray-400">System</span>
            </div>
            <div className="text-3xl font-bold text-white">
              {stats?.health?.status === "healthy" ? "✓" : "⚠"}
            </div>
            <div className="text-sm text-gray-400 mt-2">
              {stats?.health?.status || "Unknown"}
            </div>
          </Card>

          <Card className="bg-gray-900/50 border-gray-800 p-6 hover:border-green-500/50 transition-colors">
            <div className="flex items-center justify-between mb-4">
              <Shield className="w-8 h-8 text-green-500" />
              <span className="text-sm text-gray-400">Security</span>
            </div>
            <div className="text-3xl font-bold text-white">
              {stats?.metrics?.security_events || 0}
            </div>
            <div className="text-sm text-gray-400 mt-2">Security events</div>
          </Card>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="bg-gray-900/50 border-gray-800 p-6">
            <h3 className="text-xl font-semibold text-white mb-4">Quick Actions</h3>
            <div className="space-y-3">
              <button
                onClick={() => router.push("/admin/users")}
                className="w-full px-4 py-3 bg-gray-800 hover:bg-gray-700 text-white rounded-lg flex items-center gap-3 transition-colors"
              >
                <Users className="w-5 h-5" />
                <span>Manage Users</span>
              </button>
              <button
                onClick={() => router.push("/admin/agents")}
                className="w-full px-4 py-3 bg-gray-800 hover:bg-gray-700 text-white rounded-lg flex items-center gap-3 transition-colors"
              >
                <Bot className="w-5 h-5" />
                <span>Manage Agents</span>
              </button>
              <button
                onClick={() => router.push("/admin/system")}
                className="w-full px-4 py-3 bg-gray-800 hover:bg-gray-700 text-white rounded-lg flex items-center gap-3 transition-colors"
              >
                <Server className="w-5 h-5" />
                <span>System Status</span>
              </button>
            </div>
          </Card>

          <Card className="bg-gray-900/50 border-gray-800 p-6">
            <h3 className="text-xl font-semibold text-white mb-4">System Health</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Database</span>
                <span className="text-green-400">✓ Online</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">API Server</span>
                <span className="text-green-400">✓ Online</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Cache</span>
                <span className="text-green-400">✓ Online</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </AdminLayout>
  )
}
