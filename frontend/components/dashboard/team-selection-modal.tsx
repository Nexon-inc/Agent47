"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Check, Bot, Crown, Lock } from "lucide-react"
import { useAuthStore } from "@/lib/stores/auth-store"
import { useUserStore } from "@/lib/stores/user-store"
import { apiClient } from "@/lib/api-client"

interface Employee {
  id: string
  name: string
  title: string
  description: string
  tier: "free" | "starter" | "pro"
  icon: string
}

interface TeamSelectionModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
}

const employees: Employee[] = [
  {
    id: "aria",
    name: "Aria",
    title: "AI Social Media Manager",
    description: "Expertly manages your brand presence and engagement across all social platforms.",
    tier: "free",
    icon: "📱"
  },
  {
    id: "clara",
    name: "Clara",
    title: "AI Support Specialist",
    description: "Provides empathetic, high-EQ customer support and technical troubleshooting 24/7.",
    tier: "free",
    icon: "🎧"
  },
  {
    id: "eric",
    name: "Eric",
    title: "AI Sales Representative",
    description: "Optimizes lead generation and closes deals with data-driven sales strategies.",
    tier: "free",
    icon: "💼"
  },
  {
    id: "jackie",
    name: "Jackie",
    title: "AI Marketing Director",
    description: "Architects high-performance marketing campaigns and accelerates brand growth.",
    tier: "free",
    icon: "📢"
  },
  {
    id: "joe",
    name: "Joe",
    title: "AI Research Analyst",
    description: "Conducts deep market research and provides actionable competitor insights.",
    tier: "free",
    icon: "🔍"
  },
  {
    id: "shakes",
    name: "Shakes",
    title: "AI Creative Director",
    description: "Crafts compelling narratives and high-conversion content across all formats.",
    tier: "free",
    icon: "✍️"
  },
  {
    id: "purity",
    name: "Purity",
    title: "AI Business Architect",
    description: "Strategizes venture architecture and complex financial forecasting for scaling.",
    tier: "starter",
    icon: "📊"
  }
]

export default function TeamSelectionModal({ isOpen, onClose, onConfirm }: TeamSelectionModalProps) {
  const { user, isAuthenticated } = useAuthStore()
  const { userPlan } = useUserStore()
  const [selectedEmployees, setSelectedAgents] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isLoadingExisting, setIsLoadingExisting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load existing selected agents when modal opens
  useEffect(() => {
    if (isOpen && isAuthenticated) {
      setError(null) // Clear any previous errors
      loadExistingEmployees()
    }
  }, [isOpen, isAuthenticated])

  const loadExistingEmployees = async () => {
    try {
      const onboardedEmployees = await apiClient.getSelectedAgents()
      if (onboardedEmployees && onboardedEmployees.length > 0) {
        // Extract agent IDs from the response - handle both agent_id and id fields
        const agentIds = onboardedEmployees
          .filter((agent: any) => agent.status === "active" || agent.status === "enabled")
          .map((agent: any) => agent.agent_id || agent.agent_key || agent.id || agent.key)
          .filter(Boolean)
        setSelectedAgents(agentIds)
        setError(null)
      } else {
        // No existing agents - start with empty selection
        setSelectedAgents([])
        setError(null)
      }
    } catch (error) {
      console.error("Error loading existing agents:", error)
      // Silently handle errors - user might not have agents selected yet
      // Just start with empty selection so they can select new agents
      setSelectedAgents([])
      setError(null)
    } finally {
      setIsLoadingExisting(false)
    }
  }

  // Determine limits based on user plan
  const getEmployeeLimits = () => {
    switch (userPlan) {
      case "free":
        return { max: 1, available: employees.filter(a => a.tier === "free" && a.id !== "purity") }
      case "starter":
        return { max: 4, available: employees.filter(a => a.tier === "free" || a.tier === "starter") }
      case "pro":
        return { max: 7, available: employees }
      default:
        return { max: 1, available: employees.filter(a => a.tier === "free" && a.id !== "purity") }
    }
  }

  const { max, available } = getEmployeeLimits()

  const canSelectEmployee = (agentId: string) => {
    if (selectedEmployees.includes(agentId)) return true
    return selectedEmployees.length < max
  }

  const handleEmployeeToggle = (agentId: string) => {
    if (selectedEmployees.includes(agentId)) {
      setSelectedAgents(selectedEmployees.filter(id => id !== agentId))
    } else if (canSelectEmployee(agentId)) {
      setSelectedAgents([...selectedEmployees, agentId])
    }
  }

  const handleConfirm = async () => {
    if (selectedEmployees.length === 0) {
      setError("Please select at least one agent")
      return
    }

    // Validate tier limits
    if (selectedEmployees.length > max) {
      setError(`You can only select up to ${max} employee${max > 1 ? 's' : ''} with your ${userPlan} plan.`)
      return
    }

    // Remove authentication check - users can select agents immediately after signup
    setIsLoading(true)
    setError(null)

    try {
      // Save selected agents to backend - this saves to UserSelectedAgent table
      const response = await apiClient.saveSelectedAgents(selectedEmployees)

      if (response && (response.success || response.agents)) {
        // Successfully saved to user profile
        console.log("Agents saved successfully:", response)

        // Show warning if team is now locked
        if (response.locked) {
          if (userPlan === "free") {
            const trialEnd = user?.created_at
              ? new Date(new Date(user.created_at).getTime() + 14 * 24 * 60 * 60 * 1000)
              : null
            const endDateStr = trialEnd ? trialEnd.toLocaleDateString() : "soon"
            alert(`Team expansion successful! Your workforce is now locked until your trial period ends on ${endDateStr}. Upgrade your plan to modify your team immediately.`)
          } else if (userPlan === "starter" || userPlan === "pro") {
            const lockEndDate = response.lock_end_date
              ? new Date(response.lock_end_date).toLocaleDateString()
              : "1 month from now"
            const maxAgents = userPlan === "starter" ? 4 : 7
            alert(`Team expansion successful! You've onboarded ${selectedEmployees.length} of ${maxAgents} employees. Your workforce is now locked for 1 month until ${lockEndDate}.`)
          } else {
            alert("Team expansion successful! Your workforce is now locked until your subscription period ends.")
          }
        }

        onConfirm()
      } else {
        setError(response?.error || "Failed to save employee selection. Please try again.")
      }
    } catch (error: any) {
      console.error("Error saving employee selection:", error)
      console.error("Error details:", {
        message: error?.message,
        response: error?.response,
        status: error?.response?.status,
        data: error?.response?.data
      })

      // Build friendly error message
      let errorMessage = "Failed to save employee selection. Please try again."
      if (error?.message) {
        errorMessage = error.message
      } else if (error?.response?.data?.detail) {
        errorMessage = error.response.data.detail
      } else if (typeof error === 'string') {
        errorMessage = error
      }

      setError(errorMessage)

      // If it's a lock error, show upgrade option
      if (errorMessage.includes("locked")) {
        setTimeout(() => {
          if (confirm("Your workforce is locked. Would you like to expand your plan to unlock them?")) {
            window.location.href = "/pricing"
          }
        }, 1000)
      }
    } finally {
      setIsLoading(false)
    }
  }

  const getUpgradeMessage = () => {
    if (userPlan === "free" && selectedEmployees.length >= 1) {
      return "Upgrade to Starter to hire up to 4 employees, or Pro for the full workforce"
    }
    if (userPlan === "starter" && selectedEmployees.length >= 4) {
      return "Upgrade to Pro to hire the full workforce"
    }
    return null
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-2 sm:p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[95vh] sm:max-h-[90vh] overflow-y-auto">
        <div className="p-4 sm:p-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4 sm:mb-6">
            <div className="flex-1 min-w-0">
              <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Onboard Your AI Team</h2>
              <p className="text-sm sm:text-base text-gray-600 mt-1">
                Hire up to {max} team member{max > 1 ? 's' : ''} based on your {userPlan} plan
              </p>
              {isLoadingExisting && (
                <p className="text-xs sm:text-sm text-green-600 mt-1">Loading your current selections...</p>
              )}
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              <Badge variant={userPlan === "free" ? "secondary" : userPlan === "starter" ? "default" : "default"} className="text-xs">
                {userPlan === "free" && <Lock className="w-3 h-3 mr-1" />}
                {userPlan === "starter" && <Crown className="w-3 h-3 mr-1" />}
                {userPlan === "pro" && <Crown className="w-3 h-3 mr-1" />}
                {userPlan?.toUpperCase()}
              </Badge>
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4 mb-4 sm:mb-6">
            {available.map((agent) => {
              const isSelected = selectedEmployees.includes(agent.id)
              const canSelect = canSelectEmployee(agent.id)
              const isLocked = !canSelect && !isSelected

              return (
                <Card
                  key={agent.id}
                  className={`cursor-pointer transition-all duration-200 ${isSelected
                    ? "ring-2 ring-green-500 bg-green-50"
                    : isLocked
                      ? "opacity-50 cursor-not-allowed"
                      : "hover:shadow-md"
                    }`}
                  onClick={(e: React.MouseEvent) => {
                    e.stopPropagation();
                    if (!isLocked) {
                      handleEmployeeToggle(agent.id);
                    }
                  }}
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="text-2xl">{agent.icon}</div>
                        <div>
                          <CardTitle className="text-lg">{agent.name}</CardTitle>
                          <CardDescription className="text-sm">{agent.title}</CardDescription>
                        </div>
                      </div>
                      {isSelected && (
                        <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                          <Check className="w-4 h-4 text-white" />
                        </div>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-600">{agent.description}</p>
                    {agent.tier !== "free" && (
                      <Badge variant="outline" className="mt-2">
                        {agent.tier === "starter" ? "Starter+" : "Pro"}
                      </Badge>
                    )}
                  </CardContent>
                </Card>
              )
            })}
          </div>

          {getUpgradeMessage() && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
              <p className="text-green-800 text-sm">{getUpgradeMessage()}</p>
            </div>
          )}

          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
            <div className="text-sm text-gray-600">
              {selectedEmployees.length} of {max} employees onboarded
            </div>
            <div className="flex gap-2 sm:gap-3">
              <Button variant="outline" onClick={onClose} disabled={isLoading} className="flex-1 sm:flex-initial">
                Cancel
              </Button>
              <Button
                onClick={handleConfirm}
                disabled={selectedEmployees.length === 0 || isLoading}
                className="flex-1 sm:flex-initial min-w-[120px]"
              >
                {isLoading ? (
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span className="hidden sm:inline">Saving...</span>
                    <span className="sm:hidden">Saving</span>
                  </div>
                ) : (
                  <>
                    <span className="hidden sm:inline">Confirm Onboarding</span>
                    <span className="sm:hidden">Confirm</span>
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
