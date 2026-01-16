"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Check, Bot, Crown, Lock } from "lucide-react"
import { useAuthStore } from "@/lib/stores/auth-store"
import { useUserStore } from "@/lib/stores/user-store"
import { apiClient } from "@/lib/api-client"

interface Agent {
  id: string
  name: string
  title: string
  description: string
  tier: "free" | "starter" | "pro"
  icon: string
}

interface AgentSelectionModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
}

const agents: Agent[] = [
    {
      id: "aria",
      name: "Aria",
      title: "Social Media Agent",
    description: "Manages your social media presence across all platforms",
      tier: "free",
    icon: "📱"
    },
    {
      id: "clara",
      name: "Clara",
      title: "Customer Support Agent",
    description: "Handles customer inquiries and support tickets",
    tier: "free",
    icon: "🎧"
    },
    {
      id: "eric",
      name: "Eric",
      title: "Sales Agent",
    description: "Manages sales processes and lead generation",
    tier: "free",
    icon: "💼"
    },
    {
      id: "jackie",
      name: "Jackie",
      title: "Marketing Agent",
    description: "Creates and manages marketing campaigns",
    tier: "free",
    icon: "📢"
  },
  {
    id: "joe",
    name: "Joe",
    title: "Research Agent",
    description: "Conducts market research and data analysis",
    tier: "free",
    icon: "🔍"
    },
    {
      id: "shakes",
      name: "Shakes",
      title: "Content Creation Agent",
    description: "Creates engaging content for all your needs",
    tier: "free",
    icon: "✍️"
    },
    {
      id: "purity",
      name: "Purity",
    title: "Business Intelligence Agent",
    description: "Provides business insights and analytics",
    tier: "starter",
    icon: "📊"
  }
]

export default function AgentSelectionModal({ isOpen, onClose, onConfirm }: AgentSelectionModalProps) {
  const { user, isAuthenticated } = useAuthStore()
  const { userPlan } = useUserStore()
  const [selectedAgents, setSelectedAgents] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isLoadingExisting, setIsLoadingExisting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load existing selected agents when modal opens
  useEffect(() => {
    if (isOpen && isAuthenticated) {
      setError(null) // Clear any previous errors
      setIsLoadingExisting(true)
      // Check if agents are locked before loading
      checkIfLocked().then((locked) => {
        if (locked) {
          setError("Your agents are locked and cannot be changed. Please upgrade your plan to unlock them.")
          setIsLoadingExisting(false)
          // Close modal after showing error
          setTimeout(() => {
            onClose()
          }, 3000)
        } else {
          loadExistingAgents()
        }
      }).catch((err) => {
        console.error('Error checking agent lock status:', err)
        // Don't show error, just proceed to load
        setIsLoadingExisting(false)
        loadExistingAgents()
      })
    }
  }, [isOpen, isAuthenticated])

  const checkIfLocked = async (): Promise<boolean> => {
    try {
      const existingAgents = await apiClient.getSelectedAgents()
      if (existingAgents && existingAgents.length > 0) {
        return existingAgents.some((agent: any) => agent.locked === true)
      }
      return false
    } catch (error) {
      console.error("Error checking lock status:", error)
      return false
    }
  }

  const loadExistingAgents = async () => {
    try {
      const existingAgents = await apiClient.getSelectedAgents()
      if (existingAgents && existingAgents.length > 0) {
        // Extract agent IDs from the response - handle both agent_id and id fields
        const agentIds = existingAgents
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
      // If it's an auth error, try to refresh token once and retry
      const errMsg = (error as any)?.message || ''
      const status = (error as any)?.response?.status
      if (status === 401 || errMsg.toLowerCase().includes('not authenticated') || errMsg.toLowerCase().includes('unauthorized') || errMsg.toLowerCase().includes('invalid token')) {
        try {
          const refreshed = await apiClient.refreshAccessToken()
          if (refreshed) {
            try {
              const retryAgents = await apiClient.getSelectedAgents()
              if (retryAgents && retryAgents.length > 0) {
                const agentIds = retryAgents
                  .filter((agent: any) => agent.status === "active" || agent.status === "enabled")
                  .map((agent: any) => agent.agent_id || agent.agent_key || agent.id || agent.key)
                  .filter(Boolean)
                setSelectedAgents(agentIds)
                setError(null)
              } else {
                setSelectedAgents([])
                setError(null)
              }
              return
            } catch (retryErr) {
              console.warn('Retry loading agents after refresh failed:', retryErr)
            }
          }
        } catch (e) {
          console.warn('Token refresh failed:', e)
        }
        // Don't show auth error - user might not have selected agents yet
        // Just start with empty selection
        setSelectedAgents([])
        setError(null)
      } else {
        // If no agents exist yet, that's fine - start with empty selection
        setSelectedAgents([])
        setError(null)
      }
    } finally {
      setIsLoadingExisting(false)
    }
  }

  // Determine limits based on user plan
  const getAgentLimits = () => {
    switch (userPlan) {
      case "free":
        return { max: 1, available: agents.filter(a => a.tier === "free" && a.id !== "purity") }
      case "starter":
        return { max: 4, available: agents.filter(a => a.tier === "free" || a.tier === "starter") }
      case "pro":
        return { max: 7, available: agents }
      default:
        return { max: 1, available: agents.filter(a => a.tier === "free" && a.id !== "purity") }
    }
  }

  const { max, available } = getAgentLimits()

  const canSelectAgent = (agentId: string) => {
    if (selectedAgents.includes(agentId)) return true
    return selectedAgents.length < max
  }

  const handleAgentToggle = (agentId: string) => {
    if (selectedAgents.includes(agentId)) {
      setSelectedAgents(selectedAgents.filter(id => id !== agentId))
    } else if (canSelectAgent(agentId)) {
      setSelectedAgents([...selectedAgents, agentId])
    }
  }

  const handleConfirm = async () => {
    if (selectedAgents.length === 0) {
      setError("Please select at least one agent")
      return
    }

    // Validate tier limits
    if (selectedAgents.length > max) {
      setError(`You can only select up to ${max} agent${max > 1 ? 's' : ''} with your ${userPlan} plan.`)
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      // Save selected agents to backend - this saves to UserSelectedAgent table
      const response = await apiClient.saveSelectedAgents(selectedAgents)

      if (response && (response.success || response.agents)) {
        // Successfully saved to user profile
        console.log("Agents saved successfully:", response)
        
        // Show warning if agents are now locked
        if (response.locked) {
          if (userPlan === "free") {
            const trialEnd = user?.created_at 
              ? new Date(new Date(user.created_at).getTime() + 14 * 24 * 60 * 60 * 1000)
              : null
            const endDateStr = trialEnd ? trialEnd.toLocaleDateString() : "soon"
            alert(`Agents saved successfully! Your agents are now locked until your trial period ends on ${endDateStr}. Upgrade your plan to unlock immediately.`)
          } else if (userPlan === "starter" || userPlan === "pro") {
            const lockEndDate = response.lock_end_date 
              ? new Date(response.lock_end_date).toLocaleDateString()
              : "1 month from now"
            const maxAgents = userPlan === "starter" ? 4 : 7
            alert(`Agents saved successfully! You've selected ${selectedAgents.length} of ${maxAgents} agents. Your agents are now locked for 1 month until ${lockEndDate}.`)
          } else {
            alert("Agents saved successfully! Your agents are now locked until your subscription period ends.")
          }
        }
        
        onConfirm()
      } else {
        setError(response?.error || "Failed to save agent selection. Please try again.")
      }
    } catch (error: any) {
      console.error("Error saving agent selection:", error)
      console.error("Error details:", {
        message: error?.message,
        response: error?.response,
        status: error?.response?.status,
        data: error?.response?.data
      })
      
      // Build friendly error message and handle auth errors by attempting a refresh+retry
      let errorMessage = "Failed to save agent selection. Please try again."
      if (error?.message) {
        errorMessage = error.message
      } else if (error?.response?.data?.detail) {
        errorMessage = error.response.data.detail
      } else if (typeof error === 'string') {
        errorMessage = error
      }

      // Check for authentication errors - try refresh once before showing message
      const isAuthErr = errorMessage.toLowerCase().includes('not authenticated') || 
                        errorMessage.toLowerCase().includes('unauthorized') ||
                        errorMessage.toLowerCase().includes('invalid token') ||
                        error?.response?.status === 401

      if (isAuthErr) {
        try {
          const refreshed = await apiClient.refreshAccessToken()
          if (refreshed) {
            // Retry saving once
            const retryResp = await apiClient.saveSelectedAgents(selectedAgents)
            if (retryResp && (retryResp.success || retryResp.agents)) {
              console.log('Agents saved successfully after token refresh:', retryResp)
              onConfirm()
              return
            }
          }
        } catch (e) {
          console.warn('Token refresh + retry failed:', e)
        }

        errorMessage = "Authentication failed. Please log out and log back in to refresh your session."
      }

      setError(errorMessage)
      
      // If it's a lock error, show upgrade option
      if (errorMessage.includes("locked")) {
        setTimeout(() => {
          if (confirm("Your agents are locked. Would you like to upgrade your plan to unlock them?")) {
            window.location.href = "/pricing"
          }
        }, 1000)
      }
    } finally {
      setIsLoading(false)
    }
  }

  const getUpgradeMessage = () => {
    if (userPlan === "free" && selectedAgents.length >= 1) {
      return "Upgrade to Starter to select up to 4 agents, or Pro for all 7 agents"
    }
    if (userPlan === "starter" && selectedAgents.length >= 4) {
      return "Upgrade to Pro to select all 7 agents"
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
              <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Choose Your AI Agents</h2>
              <p className="text-sm sm:text-base text-gray-600 mt-1">
                Select up to {max} agent{max > 1 ? 's' : ''} based on your {userPlan} plan
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
              const isSelected = selectedAgents.includes(agent.id)
              const canSelect = canSelectAgent(agent.id)
              const isLocked = !canSelect && !isSelected
              
              return (
                <Card 
                  key={agent.id} 
                  className={`cursor-pointer transition-all duration-200 ${
                    isSelected 
                      ? "ring-2 ring-green-500 bg-green-50" 
                      : isLocked 
                        ? "opacity-50 cursor-not-allowed" 
                        : "hover:shadow-md"
                  }`}
                  onClick={(e: React.MouseEvent) => {
                    e.stopPropagation();
                    if (!isLocked) {
                      handleAgentToggle(agent.id);
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
              {selectedAgents.length} of {max} agents selected
            </div>
            <div className="flex gap-2 sm:gap-3">
              <Button variant="outline" onClick={onClose} disabled={isLoading} className="flex-1 sm:flex-initial">
                Cancel
              </Button>
              <Button 
                onClick={handleConfirm} 
                disabled={selectedAgents.length === 0 || isLoading}
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
                    <span className="hidden sm:inline">Confirm Selection</span>
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
