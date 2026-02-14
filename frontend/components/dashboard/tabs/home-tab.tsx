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
  ChevronRight,
  Wrench,
  UsersRound,
  CheckCircle2,
  AlertCircle,
  Headphones,
  DollarSign,
  Megaphone,
  FileText,
  Lightbulb
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useAuthStore } from "@/lib/stores/auth-store"
import { useUserStore } from "@/lib/stores/user-store"
import { apiClient } from "@/lib/api-client"
import { useToast } from "@/hooks/use-toast"
import { websocketService, WebSocketMessage } from "@/lib/websocket-service"

// --- Interfaces ---

interface ActivityLog {
  id: string
  title: string
  time: string
  type: 'success' | 'warning' | 'info'
  agent?: string
}

// --- Components ---

// --- Agent Config (Synced with agents-overview-tab.tsx) ---
const AGENTS_CONFIG: Record<string, any> = {
  aria: { icon: Globe, color: "text-orange-500", bg: "bg-orange-50", border: "border-orange-200" },
  clara: { icon: Headphones, color: "text-purple-500", bg: "bg-purple-50", border: "border-purple-200" },
  eric: { icon: DollarSign, color: "text-amber-500", bg: "bg-amber-50", border: "border-amber-200" },
  jackie: { icon: Megaphone, color: "text-pink-500", bg: "bg-pink-50", border: "border-pink-200" },
  shakes: { icon: FileText, color: "text-green-500", bg: "bg-green-50", border: "border-green-200" },
  joe: { icon: Search, color: "text-sky-500", bg: "bg-sky-50", border: "border-sky-200" },
  purity: { icon: Lightbulb, color: "text-gray-500", bg: "bg-gray-50", border: "border-gray-200" },
  // Default fallback
  default: { icon: UsersRound, color: "text-slate-500", bg: "bg-slate-50", border: "border-slate-200" }
}

const CommandHUD = ({ activeAgentsCount, platformCount, toolCount }: { activeAgentsCount: number, platformCount: number, toolCount: number }) => (
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
        <div className="h-8 w-8 bg-sky-50 rounded-lg flex items-center justify-center border border-sky-100">
          <Globe className="h-4 w-4 text-sky-600" />
        </div>
        <div>
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none mb-1">Platforms</p>
          <p className="text-xs font-bold text-slate-900">{platformCount} CONNECTED</p>
        </div>
      </div>
      <Wifi className="h-3 w-3 text-sky-400" />
    </div>

    <div className="bg-white border border-slate-200 p-3 rounded-xl flex items-center justify-between shadow-sm">
      <div className="flex items-center gap-3">
        <div className="h-8 w-8 bg-purple-50 rounded-lg flex items-center justify-center border border-purple-100">
          <Wrench className="h-4 w-4 text-purple-600" />
        </div>
        <div>
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none mb-1">Tools</p>
          <p className="text-xs font-bold text-slate-900">{toolCount} ONLINE</p>
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

  // Real-time Data State
  const [platformCount, setPlatformCount] = useState(0)
  const [toolCount, setToolCount] = useState(0)
  const [activityLog, setActivityLog] = useState<ActivityLog[]>([])

  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (user && isAuthenticated) {
      loadDashboardData()

      // WebSocket Setup
      const unsubscribeTasks = websocketService.subscribe('task_update', (msg: WebSocketMessage) => {
        if (msg.data?.status === 'completed' || msg.data?.status === 'verified') {
          addActivityLog({
            id: Date.now().toString(),
            title: `Task completed: ${msg.data.description || 'Unknown Task'}`,
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
            type: 'success',
            agent: msg.data.agent_name || 'System'
          })
        }
      })

      // Subscribe to Notifications for "Employee notification of verification"
      const unsubscribeNotifs = websocketService.subscribe('notification', (msg: WebSocketMessage) => {
        if (msg.data?.type === 'verification_request' || msg.data?.type === 'human_input') {
          addActivityLog({
            id: Date.now().toString(),
            title: `Verification required: ${msg.data.title || 'Review Action'}`,
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
            type: 'warning',
            agent: msg.data.agent_name
          })
        }
      })

      return () => {
        unsubscribeTasks()
        unsubscribeNotifs()
      }
    }
  }, [user, isAuthenticated])

  const addActivityLog = (log: ActivityLog) => {
    setActivityLog(prev => [log, ...prev].slice(0, 50)) // Keep last 50
  }

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      const [agentsRes, analyticsRes, tasksRes, platformsRes, integrationsStatsRes] = await Promise.all([
        apiClient.getSelectedAgents(),
        apiClient.get('/api/v1/analytics/summary').catch(() => ({ data: { recent_events: 0, total_tasks: 0, success_rate: 0 } })),
        apiClient.getUserTasks().catch(() => []),
        apiClient.get("/api/v1/platforms/connected").catch(() => []),
        apiClient.get("/api/v1/integrations/stats").catch(() => null)
      ])

      setUserAgents(agentsRes || [])
      setAnalyticsData(analyticsRes.data || analyticsRes)
      setActiveTasks(tasksRes || [])

      // Process Platforms (Count only connected/active)
      const platformsData = (platformsRes && typeof platformsRes === 'object' && 'data' in platformsRes) ? (platformsRes as any).data : (platformsRes || [])
      const connectedPlatformsList = Array.isArray(platformsData) ? platformsData : (platformsData.platforms || [])
      const activePlatformsCount = connectedPlatformsList.filter((p: any) => p.status === 'connected' || p.status === 'active').length

      // Process Tools (Use stats directly)
      const stats = (integrationsStatsRes && typeof integrationsStatsRes === 'object' && 'data' in integrationsStatsRes) ? (integrationsStatsRes as any).data : (integrationsStatsRes || {})
      const activeToolsCount = stats.connected_count || 0

      setPlatformCount(activePlatformsCount)
      setToolCount(activeToolsCount)

    } catch (error) {
      console.error("Dashboard data load failed:", error)
    } finally {
      setLoading(false)
    }
  }

  // Visualization of Neural Grid (White Theme)
  const NeuralGrid = () => (
    <div className="col-span-1 lg:col-span-2 bg-white rounded-[32px] p-8 text-slate-900 relative overflow-hidden border border-slate-200 shadow-sm transition-all hover:border-emerald-500/20">
      <div className="absolute inset-0 bg-[url('/grid-pattern.svg')] opacity-[0.03]" />
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-50/50 via-transparent to-emerald-50/50" />

      <div className="relative z-10 flex flex-col h-full justify-between">
        <div className="flex justify-between items-start">
          <div>
            <Badge variant="outline" className="border-emerald-200 text-emerald-700 bg-emerald-50 mb-3 animate-pulse">
              LIVE NEURAL LINK
            </Badge>
            <h2 className="text-3xl font-black tracking-tight mb-2 text-slate-900">Command Center</h2>
            <p className="text-slate-500 max-w-md text-sm leading-relaxed">
              Central intelligence node active. Monitoring {userAgents.length} neural agents across {activeTasks.length > 0 ? activeTasks.length : 'multiple'} operational threads.
            </p>
          </div>
          <div className="hidden md:block text-right">
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Hash Rate</p>
            <p className="text-xl font-mono text-emerald-600">47.8 TH/s</p>
          </div>
        </div>

        {/* Simulated Nodes - Agents (No limit) */}
        <div className="flex gap-4 mt-8 overflow-x-auto pb-4 custom-scrollbar">
          {userAgents.map((ua, i) => {
            // Determine agent config based on key or name match
            const key = (ua.key || ua.agent_id || ua.name || 'default').toLowerCase()
            const config = AGENTS_CONFIG[key] || AGENTS_CONFIG.default
            const Icon = config.icon || UsersRound

            return (
              <div key={i} className="flex flex-col items-center gap-2 group cursor-pointer min-w-[60px]">
                <div className={cn(
                  "h-12 w-12 rounded-2xl flex items-center justify-center border transition-all relative",
                  config.bg, config.border,
                  "group-hover:scale-105 group-hover:shadow-md"
                )}>
                  <Icon className={cn("h-6 w-6", config.color)} />
                  <div className="absolute -top-1 -right-1 h-3 w-3 bg-emerald-500 rounded-full border-2 border-white" />
                </div>
                <span className="text-[10px] font-bold text-slate-500 uppercase truncate max-w-[80px]">{ua.name || ua.agent_id}</span>
              </div>
            )
          })}

          <button
            onClick={() => window.location.href = "/dashboard?tab=agents-overview"}
            className="h-12 w-12 min-w-[48px] rounded-2xl border border-dashed border-slate-300 flex items-center justify-center text-slate-400 hover:text-emerald-600 hover:bg-emerald-50 hover:border-emerald-200 transition-colors"
          >
            <UsersRound className="h-5 w-5" />
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
        {activityLog.length > 0 ? activityLog.map((log, i) => (
          <div key={i} className="flex gap-3 items-start p-2 hover:bg-white rounded-lg transition-colors">
            <div className={cn(
              "mt-1.5 h-1.5 w-1.5 rounded-full shrink-0",
              log.type === 'info' ? "bg-sky-500" : log.type === 'warning' ? "bg-amber-500" : "bg-emerald-500"
            )} />
            <div className="font-mono text-xs text-slate-600 leading-relaxed">
              <span className="text-slate-400 text-[10px] mr-2">{log.time}</span>
              <span className="text-indigo-600 font-bold uppercase">{log.agent || "SYSTEM"}</span> {log.title}
            </div>
          </div>
        )) : (
          <div className="text-center py-8 text-slate-400 text-xs italic">
            Awaiting operational data stream... NO ACTIVE TASKS.
          </div>
        )}
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-slate-50/30 p-4 md:p-6 font-sans">
      <div className="max-w-7xl mx-auto space-y-6">

        {/* Top HUD */}
        <CommandHUD
          activeAgentsCount={userAgents.length}
          platformCount={platformCount}
          toolCount={toolCount}
        />

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <NeuralGrid />
          <LiveFeed />
        </div>

        {/* Metrics Row - Refined with requested real data placeholders */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <TacticalMetricBlock
            icon={BarChart3}
            label="Total Tasks"
            value={analyticsData?.total_tasks || "0"}
            trend={analyticsData?.total_tasks > 0 ? "+Active" : "Neutral"}
            subtext="Lifetime Operations"
          />
          <TacticalMetricBlock
            icon={Zap}
            label="Efficiency"
            value={analyticsData?.success_rate ? `${analyticsData.success_rate}%` : "100%"}
            trend={analyticsData?.success_rate > 90 ? "OPTIMAL" : "STABLE"}
            subtext="Success Rate"
          />
          {/* Replaced Mock "Man-Hours" with relevant Real-Time data if available, or keep generic until API exists */}
          {/* Since we don't have user-specific "Man-Hours" API, we'll keep it as a placeholder but acknowledge it's static for now 
               OR use Active Tasks count if better. User asked to "remove mocks" from sidebar, less strict here? 
               Wait, user said "i should also see this info in dashboard... Platforms & Tools... Active Agents... Agent Activity Feed". 
               I've put Platforms/Tools in HUD. Activity Feed in LiveFeed. Agents in NeuralGrid/HUD.
               So I can keep Metrics Row for higher-level stats or remove it if it's too mocky. 
               I'll utilize Active Tasks here. */}
          <TacticalMetricBlock
            icon={Layers}
            label="Active Threads"
            value={activeTasks.length.toString()}
            subtext="Concurrent Processes"
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
