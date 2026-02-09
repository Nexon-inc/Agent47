"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  Check,
  Clock,
  Settings,
  ChevronDown,
  ChevronUp,
  X,
  Instagram,
  Twitter,
  Mail,
  BarChart,
  Pause,
  Play,
  RefreshCw,
  Megaphone,
  Globe,
  Headphones,
  DollarSign,
  FileText,
  Search,
  Lightbulb,
  Loader2,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useUserStore } from "@/lib/stores/user-store"
import { apiClient } from "@/lib/api-client"
import { useAuthStore } from "@/lib/stores/auth-store"

// Types
type EmployeeId = "aria" | "clara" | "shakes" | "eric" | "jackie" | "joe" | "purity"

interface Employee {
  id: EmployeeId
  name: string
  type: string
  description: string
  color: string
  active: boolean
  tasks: {
    id: number
    title: string
    time: string
    icon: React.ElementType
  }[]
  settings: {
    dailyLimit: number
    autoRespond: boolean
    notifications: boolean
    integrations: string[]
  }
}

// Employee metadata
const employeeMetadata: Record<string, { name: string; type: string; description: string; color: string; icon: React.ElementType }> = {
  aria: { name: "Aria", type: "AI Social Media Manager", description: "Strategic distribution and real-time social engagement", color: "bg-gradient-to-br from-[#FF6B1A] to-[#FF8C3E]", icon: Globe },
  clara: { name: "Clara", type: "AI Support Specialist", description: "Omnichannel customer resolution and empathy", color: "bg-gradient-to-br from-purple-400 to-purple-600", icon: Headphones },
  eric: { name: "Eric", type: "AI Sales Representative", description: "Automated lead qualification and CRM optimization", color: "bg-gradient-to-br from-amber-400 to-amber-600", icon: DollarSign },
  jackie: { name: "Jackie", type: "AI Marketing Director", description: "Full-funnel strategy and audience scaling", color: "bg-gradient-to-br from-pink-400 to-pink-600", icon: Megaphone },
  shakes: { name: "Shakes", type: "AI Creative Director", description: "Narrative architecture and high-conversion assets", color: "bg-gradient-to-br from-green-400 to-green-600", icon: FileText },
  joe: { name: "Joe", type: "AI Research Analyst", description: "Cross-platform data mining and market intelligence", color: "bg-gradient-to-br from-blue-400 to-blue-600", icon: Search },
  purity: { name: "Purity", type: "AI Business Architect", description: "Venture strategy and operational modeling", color: "bg-gradient-to-br from-indigo-400 to-indigo-600", icon: Lightbulb },
}

const taskIcons: Record<string, React.ElementType> = {
  social: Instagram,
  email: Mail,
  analytics: BarChart,
  sales: DollarSign,
  marketing: Megaphone,
  content: FileText,
  default: BarChart,
}

export default function MyTeamTab() {
  const { userPlan } = useUserStore()
  const { user } = useAuthStore()
  const [expandedAgent, setExpandedAgent] = useState<EmployeeId | null>(null)
  const [managingAgent, setManagingAgent] = useState<EmployeeId | null>(null)
  const [agents, setAgents] = useState<Employee[]>([])
  const [isLoading, setIsLoading] = useState(true)

  // Load agents data from backend
  useEffect(() => {
    if (user) {
      loadAgentsData()
    }
  }, [user])

  // Subscribe to real-time agent status updates via WebSocket
  useEffect(() => {
    if (!user) return

    const { websocketService } = require('@/lib/websocket-service')

    if (!websocketService.getConnectionStatus()) {
      websocketService.connect()
    }

    // Subscribe to task updates (affects agent status)
    const unsubscribeTask = websocketService.subscribe('task_update', () => {
      loadAgentsData()
    })

    // Subscribe to agent responses
    const unsubscribeAgent = websocketService.subscribe('agent_response', () => {
      loadAgentsData()
    })

    return () => {
      unsubscribeTask()
      unsubscribeAgent()
    }
  }, [user])

  const loadAgentsData = async () => {
    try {
      setIsLoading(true)

      // Load dashboard data which includes agent details
      const dashboardResponse = await apiClient.get("/api/v1/user-admin/dashboard").catch(() => ({ data: null }))

      if (dashboardResponse.data?.agents) {
        const agentDetails = dashboardResponse.data.agents

        // Transform backend data to frontend format
        const transformedAgents: Employee[] = agentDetails.map((agentData: any) => {
          const agentId = agentData.agent_key as EmployeeId
          const metadata = employeeMetadata[agentId] || {
            name: agentId.charAt(0).toUpperCase() + agentId.slice(1),
            type: "Employee",
            description: "AI Workforce",
            color: "bg-gradient-to-br from-gray-400 to-gray-600",
            icon: BarChart
          }

          // Transform recent tasks
          const tasks = (agentData.recent_tasks || []).slice(0, 5).map((task: any, index: number) => {
            // Determine icon based on task title/description
            let icon = taskIcons.default
            const taskLower = (task.title || "").toLowerCase()
            if (taskLower.includes("social") || taskLower.includes("instagram") || taskLower.includes("twitter")) icon = Instagram
            else if (taskLower.includes("email") || taskLower.includes("mail")) icon = Mail
            else if (taskLower.includes("analytics") || taskLower.includes("metric")) icon = BarChart
            else if (taskLower.includes("sales") || taskLower.includes("lead")) icon = DollarSign
            else if (taskLower.includes("marketing") || taskLower.includes("campaign")) icon = Megaphone
            else if (taskLower.includes("content") || taskLower.includes("blog")) icon = FileText

            // Format time
            let timeStr = "Just now"
            if (task.created_at) {
              const created = new Date(task.created_at)
              const now = new Date()
              const diffMs = now.getTime() - created.getTime()
              const diffMins = Math.floor(diffMs / 60000)
              const diffHours = Math.floor(diffMs / 3600000)
              const diffDays = Math.floor(diffMs / 86400000)

              if (diffMins < 1) timeStr = "Just now"
              else if (diffMins < 60) timeStr = `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`
              else if (diffHours < 24) timeStr = `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
              else timeStr = `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
            }

            return {
              id: task.id || index,
              title: task.title || "Task",
              time: timeStr,
              icon
            }
          })

          return {
            id: agentId,
            name: metadata.name,
            type: metadata.type,
            description: metadata.description,
            color: metadata.color,
            active: agentData.status === "active",
            tasks,
            settings: {
              dailyLimit: agentData.configuration?.daily_limit || 20,
              autoRespond: agentData.automation_enabled || false,
              notifications: true,
              integrations: agentData.configuration?.integrations || [],
            }
          }
        })

        // Filter by user plan limits
        const maxAgents = userPlan === "free" ? 1 : userPlan === "starter" ? 3 : userPlan === "pro" ? 6 : 999
        setAgents(transformedAgents.slice(0, maxAgents))
      } else {
        setAgents([])
      }
    } catch (error) {
      console.error("Failed to load agents data:", error)
      setAgents([])
    } finally {
      setIsLoading(false)
    }
  }

  // Toggle employee expansion
  const toggleExpand = (agentId: EmployeeId) => {
    setExpandedAgent(expandedAgent === agentId ? null : agentId)
  }

  // Toggle employee active status
  const toggleAgentActive = async (agentId: EmployeeId) => {
    try {
      const agent = agents.find(a => a.id === agentId)
      const newStatus = agent?.active ? "paused" : "active"

      // Update backend - would need an endpoint for this
      // For now, update local state optimistically
      setAgents(agents.map((agent) => (agent.id === agentId ? { ...agent, active: !agent.active } : agent)))

      // TODO: Call backend API to update agent status
      // await apiClient.put(`/api/v1/user-admin/agents/${agentId}/status`, { status: newStatus })
    } catch (error) {
      console.error("Failed to toggle agent status:", error)
      // Revert on error
      setAgents(agents.map((agent) => (agent.id === agentId ? { ...agent, active: !agent.active } : agent)))
    }
  }

  // Update employee settings
  const updateAgentSettings = async (agentId: EmployeeId, settings: Partial<Employee["settings"]>) => {
    try {
      // Update local state optimistically
      setAgents(
        agents.map((agent) =>
          agent.id === agentId ? { ...agent, settings: { ...agent.settings, ...settings } } : agent,
        ),
      )

      // TODO: Call backend API to save settings
      // await apiClient.put(`/api/v1/user-admin/agents/${agentId}/settings`, settings)
    } catch (error) {
      console.error("Failed to update agent settings:", error)
    }
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl md:text-3xl font-extrabold text-[#4B0082]  mb-4">Active Workforce</h1>
        <p className="text-gray-600  mb-6">
          Manage your active employees and their assignments.
          {userPlan === "free"
            ? " Free tier allows 1 active employee."
            : userPlan === "starter"
              ? " Starter plan allows 3 active employees."
              : userPlan === "pro"
                ? " Pro plan allows 6 active employees."
                : " Ecosystem plan allows unlimited digital staff."}
        </p>
      </div>

      {/* Loading State */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-[#1E90FF]" />
          <span className="ml-2 text-gray-600">Connecting to workforce...</span>
        </div>
      ) : agents.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-600 mb-4">No employees onboarded yet.</p>
          <p className="text-sm text-gray-500">Add team members from the Recruitment tab to get started.</p>
        </div>
      ) : (
        /* Agent Cards */
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {agents.map((agent) => (
            <div
              key={agent.id}
              className="bg-white  rounded-xl shadow-sm border border-gray-200  overflow-hidden"
            >
              <div className={cn("p-4", agent.color)}>
                <div className="flex justify-between items-center">
                  <div className="flex items-center">
                    <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center mr-4">
                      <span className="text-white font-bold text-xl">{agent.name[0]}</span>
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-white">{agent.name}</h3>
                      <p className="text-white/80">{agent.type}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span
                      className={cn(
                        "flex items-center text-xs font-medium px-2 py-1 rounded-full",
                        agent.active ? "bg-green-500/20 text-white" : "bg-gray-500/20 text-white",
                      )}
                    >
                      {agent.active ? (
                        <>
                          <Check className="w-3 h-3 mr-1" />
                          Active
                        </>
                      ) : (
                        <>
                          <Clock className="w-3 h-3 mr-1" />
                          Paused
                        </>
                      )}
                    </span>
                  </div>
                </div>
              </div>

              <div className="p-4">
                <div className="flex justify-between mb-4">
                  <h4 className="font-medium text-gray-900 ">Assigned Tasks</h4>
                  <button
                    onClick={() => toggleExpand(agent.id)}
                    className="text-[#1E90FF] hover:text-[#00FF88] transition-colors text-sm flex items-center"
                  >
                    {expandedAgent === agent.id ? (
                      <>
                        Show Less
                        <ChevronUp className="ml-1 w-4 h-4" />
                      </>
                    ) : (
                      <>
                        View All
                        <ChevronDown className="ml-1 w-4 h-4" />
                      </>
                    )}
                  </button>
                </div>

                <ul className="space-y-3">
                  {agent.tasks.slice(0, expandedAgent === agent.id ? undefined : 3).map((task) => (
                    <li key={task.id} className="flex items-start">
                      <div
                        className={cn(
                          "w-8 h-8 rounded-full flex items-center justify-center mr-3 flex-shrink-0",
                          agent.color.replace("bg-gradient-to-br", "bg"),
                        )}
                      >
                        <task.icon className="w-4 h-4 text-white" />
                      </div>
                      <div>
                        <p className="text-gray-900  font-medium text-sm">{task.title}</p>
                        <p className="text-xs text-gray-500 ">{task.time}</p>
                      </div>
                    </li>
                  ))}
                </ul>

                <div className="flex justify-between mt-6 pt-4 border-t border-gray-100 ">
                  <button
                    onClick={() => toggleAgentActive(agent.id)}
                    className={cn(
                      "flex items-center px-3 py-1.5 rounded-lg text-sm font-medium transition-colors",
                      agent.active
                        ? "bg-gray-100  text-gray-700  hover:bg-gray-200 :bg-gray-600"
                        : "bg-[#00FF88] text-white hover:bg-[#00FF88]/90",
                    )}
                  >
                    {agent.active ? (
                      <>
                        <Pause className="w-4 h-4 mr-1" />
                        Pause
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4 mr-1" />
                        Activate
                      </>
                    )}
                  </button>

                  <button
                    onClick={() => setManagingAgent(agent.id)}
                    className="flex items-center px-3 py-1.5 bg-[#1E90FF] text-white rounded-lg text-sm font-medium hover:bg-[#1E90FF]/90 transition-colors"
                  >
                    <Settings className="w-4 h-4 mr-1" />
                    Configure
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Settings Modal */}
      <AnimatePresence>
        {managingAgent && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ type: "spring", damping: 25 }}
              className="bg-white  rounded-xl max-w-md w-full max-h-[80vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              {(() => {
                const agent = agents.find((a) => a.id === managingAgent)
                if (!agent) return null

                return (
                  <>
                    <div className={cn("p-6 relative", agent.color)}>
                      <button
                        onClick={() => setManagingAgent(null)}
                        className="absolute top-4 right-4 text-white/80 hover:text-white"
                      >
                        <X className="w-6 h-6" />
                      </button>

                      <div className="flex items-center">
                        <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center mr-4">
                          <span className="text-white font-bold text-xl">{agent.name[0]}</span>
                        </div>
                        <div>
                          <h3 className="text-xl font-bold text-white">{agent.name} Settings</h3>
                          <p className="text-white/80">{agent.type}</p>
                        </div>
                      </div>
                    </div>

                    <div className="p-6">
                      <div className="space-y-6">
                        <div>
                          <label className="flex items-center justify-between mb-2">
                            <span className="text-gray-700  font-medium">Task Capacity</span>
                            <span className="text-sm text-gray-500 ">
                              {agent.settings.dailyLimit} tasks/day
                            </span>
                          </label>
                          <input
                            type="range"
                            min="5"
                            max={userPlan === "free" ? 10 : userPlan === "starter" ? 30 : 100}
                            value={agent.settings.dailyLimit}
                            onChange={(e) =>
                              updateAgentSettings(agent.id, { dailyLimit: Number.parseInt(e.target.value) })
                            }
                            className="w-full h-2 bg-gray-200  rounded-lg appearance-none cursor-pointer"
                          />
                          <div className="flex justify-between text-xs text-gray-500  mt-1">
                            <span>5</span>
                            <span>{userPlan === "free" ? 10 : userPlan === "starter" ? 30 : 100}</span>
                          </div>
                        </div>

                        <div className="flex items-center justify-between">
                          <span className="text-gray-700  font-medium">Autonomous Execution</span>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              checked={agent.settings.autoRespond}
                              onChange={() =>
                                updateAgentSettings(agent.id, { autoRespond: !agent.settings.autoRespond })
                              }
                              className="sr-only peer"
                            />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-[#1E90FF] :ring-[#1E90FF] rounded-full peer  peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all  peer-checked:bg-[#1E90FF]"></div>
                          </label>
                        </div>

                        <div className="flex items-center justify-between">
                          <span className="text-gray-700  font-medium">Notifications</span>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              checked={agent.settings.notifications}
                              onChange={() =>
                                updateAgentSettings(agent.id, { notifications: !agent.settings.notifications })
                              }
                              className="sr-only peer"
                            />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-[#1E90FF] :ring-[#1E90FF] rounded-full peer  peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all  peer-checked:bg-[#1E90FF]"></div>
                          </label>
                        </div>

                        <div>
                          <label className="block text-gray-700  font-medium mb-2">
                            Integrations
                          </label>
                          <div className="bg-gray-50  rounded-lg p-3">
                            {userPlan === "free" ? (
                              <div className="text-center py-2">
                                <p className="text-sm text-gray-500  mb-2">
                                  Integrations available in paid plans
                                </p>
                                <a
                                  href="/pricing"
                                  className="text-[#1E90FF] hover:text-[#00FF88] transition-colors text-sm font-medium"
                                >
                                  Upgrade to Unlock
                                </a>
                              </div>
                            ) : (
                              <div className="space-y-2">
                                {agent.settings.integrations.map((integration, index) => (
                                  <div key={index} className="flex items-center justify-between">
                                    <span className="text-sm text-gray-700 ">{integration}</span>
                                    <button className="text-[#1E90FF] hover:text-[#00FF88] transition-colors">
                                      <RefreshCw className="w-4 h-4" />
                                    </button>
                                  </div>
                                ))}
                                <button className="w-full text-center py-2 text-sm text-[#1E90FF] hover:text-[#00FF88] transition-colors font-medium">
                                  + Add Integration
                                </button>
                              </div>
                            )}
                          </div>
                        </div>

                        {userPlan !== "free" && (
                          <div>
                            <label className="block text-gray-700  font-medium mb-2">
                              Advanced Settings
                            </label>
                            <div className="bg-gray-50  rounded-lg p-3">
                              <button className="w-full text-left py-2 text-sm text-gray-700  hover:text-[#1E90FF] transition-colors">
                                Customize Responses
                              </button>
                              <button className="w-full text-left py-2 text-sm text-gray-700  hover:text-[#1E90FF] transition-colors">
                                Schedule Availability
                              </button>
                              <button className="w-full text-left py-2 text-sm text-gray-700  hover:text-[#1E90FF] transition-colors">
                                Export Agent Data
                              </button>
                            </div>
                          </div>
                        )}

                        <div className="pt-4 border-t border-gray-200  flex justify-between">
                          {userPlan !== "free" && (
                            <button className="text-red-500 hover:text-red-600 transition-colors text-sm font-medium">
                              Offboard Employee
                            </button>
                          )}
                          <button
                            onClick={() => setManagingAgent(null)}
                            className="px-4 py-2 bg-[#1E90FF] text-white rounded-lg text-sm font-medium hover:bg-[#1E90FF]/90 transition-colors"
                          >
                            Save Changes
                          </button>
                        </div>
                      </div>
                    </div>
                  </>
                )
              })()}
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}
