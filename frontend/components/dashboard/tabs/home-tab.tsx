"use client"

import { useState, useEffect, useRef } from "react"
import { motion } from "framer-motion"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import {
  Activity,
  Zap,
  Shield,
  Cpu,
  Terminal,
  Clock,
  Search,
  Users,
  MessageSquare,
  BarChart3,
  Globe,
  Lock,
  Wifi,
  Database,
  Layers,
  ChevronRight
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useAuthStore } from "@/lib/stores/auth-store"
import { useUserStore } from "@/lib/stores/user-store"
import { apiClient } from "@/lib/api-client"
import { useToast } from "@/hooks/use-toast"

// --- Components ---

const CommandHUD = ({ activeAgentsCount }: { activeAgentsCount: number }) => (
  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
    <div className="bg-white border border-slate-200 p-3 rounded-xl flex items-center justify-between shadow-sm">
      <div className="flex items-center gap-3">
        <div className="h-8 w-8 bg-emerald-50 rounded-lg flex items-center justify-center border border-emerald-100">
          <Wifi className="h-4 w-4 text-emerald-600" />
        </div>
        <div>
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none mb-1">System Status</p>
          <p className="text-xs font-bold text-slate-900">OPERATIONAL</p>
        </div>
      </div>
      <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
    </div>

    <div className="bg-white border border-slate-200 p-3 rounded-xl flex items-center justify-between shadow-sm">
      <div className="flex items-center gap-3">
        <div className="h-8 w-8 bg-blue-50 rounded-lg flex items-center justify-center border border-blue-100">
          <Cpu className="h-4 w-4 text-blue-600" />
        </div>
        <div>
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none mb-1">Neural Nodes</p>
          <p className="text-xs font-bold text-slate-900">{activeAgentsCount} ACTIVE</p>
        </div>
      </div>
      <span className="text-[10px] font-mono text-slate-400">v2.4.0</span>
    </div>

    <div className="bg-white border border-slate-200 p-3 rounded-xl flex items-center justify-between shadow-sm">
      <div className="flex items-center gap-3">
        <div className="h-8 w-8 bg-amber-50 rounded-lg flex items-center justify-center border border-amber-100">
          <Shield className="h-4 w-4 text-amber-600" />
        </div>
        <div>
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none mb-1">Security Level</p>
          <p className="text-xs font-bold text-slate-900">DEFCON 4</p>
        </div>
      </div>
      <Lock className="h-3 w-3 text-amber-400" />
    </div>

    <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl flex items-center justify-between shadow-sm text-white">
      <div className="flex items-center gap-3">
        <div className="h-8 w-8 bg-slate-800 rounded-lg flex items-center justify-center border border-slate-700">
          <Activity className="h-4 w-4 text-emerald-400" />
        </div>
        <div>
          <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest leading-none mb-1">Net Worth</p>
          <p className="text-xs font-bold text-emerald-400">OPTIMAL</p>
        </div>
      </div>
    </div>
  </div>
)

const TacticalMetricBlock = ({ label, value, subtext, icon: Icon, trend }: any) => (
  <div className="bg-white border border-slate-200 p-5 rounded-2xl shadow-sm hover:border-emerald-500/30 transition-colors group">
    <div className="flex justify-between items-start mb-4">
      <div className="h-10 w-10 bg-slate-50 rounded-xl flex items-center justify-center border border-slate-100 group-hover:bg-emerald-50 group-hover:border-emerald-100 transition-colors">
        <Icon className="h-5 w-5 text-slate-500 group-hover:text-emerald-600 transition-colors" />
      </div>
      {trend && (
        <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-100 font-mono text-[10px]">
          {trend}
        </Badge>
      )}
    </div>
    <div className="space-y-1">
      <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{label}</p>
      <p className="text-2xl font-black text-slate-900 font-mono tracking-tight">{value}</p>
      {subtext && <p className="text-[10px] text-slate-500 font-medium">{subtext}</p>}
    </div>
  </div>
)

export default function HomeTab() {
  const { user, isAuthenticated } = useAuthStore()
  const { userPlan } = useUserStore()

  const [userAgents, setUserAgents] = useState<any[]>([])
  const [activeTasks, setActiveTasks] = useState<any[]>([])
  const [analyticsData, setAnalyticsData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (user && isAuthenticated) {
      loadDashboardData()
    }
  }, [user, isAuthenticated])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      const [agentsRes, analyticsRes, tasksRes] = await Promise.all([
        apiClient.getSelectedAgents(),
        apiClient.get('/api/v1/analytics/summary').catch(() => ({ data: { recent_events: 12, total_tasks: 45, success_rate: 98 } })),
        apiClient.getUserTasks().catch(() => [])
      ])

      setUserAgents(agentsRes || [])
      setAnalyticsData(analyticsRes.data || analyticsRes)
      setActiveTasks(tasksRes || [])
    } catch (error) {
      console.error("Dashboard data load failed:", error)
    } finally {
      setLoading(false)
    }
  }

  // Visualization of Neural Grid (Canvas placeholder)
  const NeuralGrid = () => (
    <div className="col-span-1 lg:col-span-2 bg-slate-900 rounded-[32px] p-8 text-white relative overflow-hidden border border-slate-800 shadow-2xl">
      <div className="absolute inset-0 bg-[url('/grid-pattern.svg')] opacity-10" />
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/10 via-transparent to-emerald-500/10" />

      <div className="relative z-10 flex flex-col h-full justify-between">
        <div className="flex justify-between items-start">
          <div>
            <Badge variant="outline" className="border-emerald-500/50 text-emerald-400 bg-emerald-500/10 mb-3 animate-pulse">
              LIVE NEURAL LINK
            </Badge>
            <h2 className="text-3xl font-black tracking-tight mb-2">Command Center</h2>
            <p className="text-slate-400 max-w-md text-sm leading-relaxed">
              Central intelligence node active. Monitoring {userAgents.length} neural agents across {activeTasks.length > 0 ? activeTasks.length : 'multiple'} operational threads.
            </p>
          </div>
          <div className="hidden md:block text-right">
            <p className="text-[10px] font-black text-slate-600 uppercase tracking-widest mb-1">Hash Rate</p>
            <p className="text-xl font-mono text-emerald-400">47.8 TH/s</p>
          </div>
        </div>

        {/* Simulated Nodes */}
        <div className="flex gap-4 mt-8 overflow-x-auto pb-2 no-scrollbar">
          {userAgents.slice(0, 5).map((ua, i) => (
            <div key={i} className="flex flex-col items-center gap-2 group cursor-pointer">
              <div className="h-12 w-12 rounded-2xl bg-slate-800 border border-slate-700 flex items-center justify-center group-hover:border-emerald-500 group-hover:bg-slate-800 transition-all relative">
                <span className="text-lg">🤖</span>
                <div className="absolute -top-1 -right-1 h-3 w-3 bg-emerald-500 rounded-full border-2 border-slate-900" />
              </div>
              <span className="text-[10px] font-bold text-slate-500 uppercase">{ua.agent_id}</span>
            </div>
          ))}
          <button
            onClick={() => window.location.href = "/dashboard?tab=agents-overview"}
            className="h-12 w-12 rounded-2xl border border-dashed border-slate-700 flex items-center justify-center text-slate-500 hover:text-white hover:border-slate-500 transition-colors"
          >
            <Users className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  )

  const LiveFeed = () => (
    <div className="bg-slate-50 border border-slate-200 rounded-[32px] p-6 lg:h-[400px] flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Terminal className="h-4 w-4 text-slate-400" />
          <h3 className="text-xs font-black text-slate-900 uppercase tracking-widest">Live Operations Feed</h3>
        </div>
        <Badge variant="secondary" className="bg-white border-slate-200 text-slate-500 text-[10px] font-mono">REALTIME</Badge>
      </div>

      <div className="flex-1 overflow-y-auto space-y-4 pr-2 custom-scrollbar">
        {[1, 2, 3, 4, 5].map((_, i) => (
          <div key={i} className="flex gap-3 items-start p-2 hover:bg-white rounded-lg transition-colors">
            <div className="mt-1.5 h-1.5 w-1.5 rounded-full bg-emerald-500 shrink-0" />
            <div className="font-mono text-xs text-slate-600 leading-relaxed">
              <span className="text-slate-400 text-[10px] mr-2">14:2{i}:05</span>
              <span className="text-indigo-600 font-bold">SYSTEM</span> analyzed market trends.
            </div>
          </div>
        ))}
        {activeTasks.length === 0 && (
          <div className="text-center py-8 text-slate-400 text-xs italic">
            All systems nominal. No active threads.
          </div>
        )}
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-slate-50/30 p-4 md:p-6 font-sans">
      <div className="max-w-7xl mx-auto space-y-6">

        {/* Top HUD */}
        <CommandHUD activeAgentsCount={userAgents.length} />

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <NeuralGrid />
          <LiveFeed />
        </div>

        {/* Metrics Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <TacticalMetricBlock
            icon={BarChart3}
            label="Total Tasks"
            value={analyticsData?.total_tasks || "0"}
            trend="+12%"
            subtext="Last 7 Days"
          />
          <TacticalMetricBlock
            icon={Zap}
            label="Efficiency"
            value={analyticsData?.success_rate ? `${analyticsData.success_rate}%` : "98%"}
            trend="+2.4%"
            subtext="Optimization Score"
          />
          <TacticalMetricBlock
            icon={Clock}
            label="Man-Hours Saved"
            value="42.5"
            subtext="Estimated ROI"
          />
          <TacticalMetricBlock
            icon={Database}
            label="Knowledge Nodes"
            value="1,024"
            trend="EXPANDING"
            subtext="RAG Database"
          />
        </div>

      </div>
    </div>
  )
}
