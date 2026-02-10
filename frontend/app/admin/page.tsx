"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import AdminLayout from "@/components/admin/layout"
import { useAdminStore } from "@/lib/stores/admin-store"
import { adminAPI } from "@/lib/services/admin-api"
import {
  ExecutiveROITicker,
  PersonnelTalentCard,
  InteractiveOrgChart,
  CompanyBrainVisual
} from "@/components/admin/command-center-components"
import { ShieldAlert, Info } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"

const personnelStats = [
  { name: "Aria", role: "Social Media manager", avatar: "AR", active: true, stats: [{ label: "Engagement", value: 95 }, { label: "Brand Tone", value: 88 }] },
  { name: "Joe", role: "Research Analyst", avatar: "JO", active: true, stats: [{ label: "Analytical", value: 99 }, { label: "Speed", value: 92 }] },
  { name: "Eric", role: "Sales Optimizer", avatar: "ER", active: false, stats: [{ label: "Closing", value: 96 }, { label: "Leads", value: 90 }] },
  { name: "Clara", role: "Support Specialist", avatar: "CL", active: true, stats: [{ label: "Accuracy", value: 98 }, { label: "Empathy", value: 94 }] },
]

function Badge({ status }: { status: "active" | "idle" }) {
  return (
    <div className={cn(
      "px-2 py-0.5 rounded text-[8px] font-black uppercase tracking-widest border",
      status === "active" ? "bg-green-500/10 text-green-500 border-green-500/20" : "bg-gray-800 text-gray-500 border-gray-700"
    )}>
      {status}
    </div>
  )
}

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

    const loadData = async () => {
      try {
        await fetchCurrentAdmin()
        const [health, metrics] = await Promise.all([
          adminAPI.getHealth().catch(() => null),
          adminAPI.getMetrics().catch(() => null)
        ])
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
          <div className="w-10 h-10 border-4 border-green-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
      </AdminLayout>
    )
  }

  return (
    <AdminLayout>
      <div className="space-y-8 pb-10">

        {/* Header Section */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse" />
              <span className="text-[10px] font-black text-green-500 uppercase tracking-widest">Systems Nominal</span>
            </div>
            <h1 className="text-4xl font-black text-white tracking-tight">Personnel Command Center</h1>
            <p className="text-gray-500 text-sm mt-1 uppercase tracking-wider">
              Workforce Overview for {currentAdmin?.email || "Founder"}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Alert className="bg-yellow-500/10 border-yellow-500/20 text-yellow-500 py-2 px-4 w-auto hidden lg:flex">
              <ShieldAlert className="h-4 w-4" />
              <AlertDescription className="text-[10px] font-bold uppercase tracking-tight ml-2">
                Manual Override: Tactical Stealth Mode Authorized
              </AlertDescription>
            </Alert>
          </div>
        </div>

        {/* ROI Ticker */}
        <ExecutiveROITicker />

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
          {/* Left/Middle Column: Org Chart & Brain */}
          <div className="xl:col-span-2 space-y-8">
            <InteractiveOrgChart />
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6">
              {personnelStats.map((p, i) => (
                <PersonnelTalentCard key={i} {...p} />
              ))}
            </div>
          </div>

          {/* Right Column: Company Brain & Internal Stats */}
          <div className="space-y-8">
            <CompanyBrainVisual />

            <Card className="bg-gray-900/40 border-gray-800 p-6 backdrop-blur-md">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                  <Info size={14} className="text-blue-500" />
                  <h3 className="text-xs font-bold text-white uppercase tracking-widest">Network Health</h3>
                </div>
                <Badge status="active" />
              </div>

              <div className="space-y-4">
                {[
                  { label: "Database Latency", val: "12ms", status: "green" },
                  { label: "Ollama/Gemini Uplink", val: "99.9%", status: "green" },
                  { label: "Redis Cache Sync", val: "Synced", status: "green" },
                  { label: "Worker Thread Load", val: "Low", status: "blue" },
                ].map((stat, i) => (
                  <div key={i} className="flex items-center justify-between p-3 bg-gray-950/50 rounded-xl border border-gray-800/50">
                    <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">{stat.label}</span>
                    <span className={cn("text-[10px] font-mono font-bold", stat.status === "green" ? "text-green-500" : "text-blue-500")}>
                      {stat.val}
                    </span>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </div>

      </div>
    </AdminLayout>
  )
}
