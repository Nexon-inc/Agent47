"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Textarea } from "@/components/ui/textarea"
import {
  Globe,
  Headphones,
  FileText,
  DollarSign,
  Megaphone,
  Search,
  Lightbulb,
  Settings,
  Activity,
  Clock,
  TrendingUp,
  Users,
  Play,
  Pause,
  Save,
  X,
  Bot,
  Loader2,
  CheckCircle,
  AlertCircle,
  RefreshCw,
} from "lucide-react"
import { apiClient } from "@/lib/api-client"
import { useAuthStore } from "@/lib/stores/auth-store"
import { useUserStore } from "@/lib/stores/user-store"
import AgentSelectionModal from "../agent-selection-modal"

interface Agent {
  id: string
  name: string
  title: string
  description: string
  icon: any
  color: string
  status: "active" | "inactive" | "paused" | "error"
  settings: Record<string, boolean>
  customInstructions?: string
  isOnline: boolean
  isSelected?: boolean
  isLocked?: boolean
  canSelect?: boolean
}

const agentTemplates = [
  {
    id: "aria",
    name: "Aria",
    title: "Social Media Agent",
    description: "Automates social media posting, engagement tracking, and content optimization across all platforms.",
    icon: Globe,
    color: "bg-orange-500",
    defaultSettings: {
      autoPost: true,
      engagementTracking: true,
      contentOptimization: true,
      schedulingEnabled: true,
    },
  },
  {
    id: "clara",
    name: "Clara",
    title: "Customer Support Agent",
    description: "Handles customer inquiries with AI-powered responses, intelligent routing, and 24/7 availability.",
    icon: Headphones,
    color: "bg-purple-500",
    defaultSettings: {
      autoResponse: true,
      intelligentRouting: true,
      sentimentAnalysis: true,
      escalationRules: true,
    },
  },
  {
    id: "eric",
    name: "Eric",
    title: "Sales Agent",
    description: "Boosts sales with intelligent lead scoring, proposal generation, and automated pipeline management.",
    icon: DollarSign,
    color: "bg-amber-500",
    defaultSettings: {
      leadScoring: true,
      proposalGeneration: true,
      pipelineManagement: true,
      followUpAutomation: true,
    },
  },
  {
    id: "jackie",
    name: "Jackie",
    title: "Marketing Agent",
    description: "Optimizes marketing campaigns with data-driven insights, audience segmentation, and automation.",
    icon: Megaphone,
    color: "bg-pink-500",
    defaultSettings: {
      campaignOptimization: true,
      audienceSegmentation: true,
      abTesting: true,
      performanceTracking: true,
    },
  },
  {
    id: "shakes",
    name: "Shakes",
    title: "Content Creation Agent",
    description: "Creates engaging content with AI-powered writing, editing, and optimization for various platforms.",
    icon: FileText,
    color: "bg-green-500",
    defaultSettings: {
      contentGeneration: true,
      seoOptimization: true,
      plagiarismCheck: true,
      brandVoice: true,
    },
  },
  {
    id: "joe",
    name: "Joe",
    title: "Research Agent",
    description: "Conducts comprehensive market research and competitive analysis with AI-powered data collection.",
    icon: Search,
    color: "bg-blue-500",
    defaultSettings: {
      marketResearch: true,
      competitorAnalysis: true,
      trendAnalysis: true,
      dataVisualization: true,
    },
  },
  {
    id: "purity",
    name: "Purity",
    title: "Business Maker Agent",
    description: "Helps launch and scale businesses with AI-powered insights, from idea validation to business models.",
    icon: Lightbulb,
    color: "bg-indigo-500",
    defaultSettings: {
      ideaValidation: true,
      businessPlanning: true,
      financialModeling: true,
      marketAnalysis: true,
    },
  },
]

export default function AgentsOverviewTab() {
  const { user } = useAuthStore()
  
  // Get user's subscription plan
  const userPlan = user?.subscription_plan || 'free'
  const canUseIntercommunication = userPlan === 'starter' || userPlan === 'pro'
  const [searchTerm, setSearchTerm] = useState("")
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState("")
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)
  const [agentSettings, setAgentSettings] = useState<Record<string, boolean>>({})
  const [customInstructions, setCustomInstructions] = useState("")
  const [agents, setAgents] = useState<Agent[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [saveStatus, setSaveStatus] = useState<"idle" | "success" | "error">("idle")
  const [refreshing, setRefreshing] = useState(false)
  const [intercommunicationEnabled, setIntercommunicationEnabled] = useState(false)
  const [showAgentSelection, setShowAgentSelection] = useState(false)

  // Debounce search term
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm)
    }, 300)
    return () => clearTimeout(timer)
  }, [searchTerm])

  // Load agents data on component mount
  useEffect(() => {
    loadAgentsData()
    loadIntercommunicationSetting()
  }, [])

  // Subscribe to real-time agent updates via WebSocket
  useEffect(() => {
    const { websocketService } = require('@/lib/websocket-service')
    
    if (!websocketService.getConnectionStatus()) {
      websocketService.connect()
    }

    // Subscribe to task updates and agent responses
    const unsubscribeTask = websocketService.subscribe('task_update', () => {
      loadAgentsData()
    })

    const unsubscribeAgent = websocketService.subscribe('agent_response', () => {
      loadAgentsData()
    })

    return () => {
      unsubscribeTask()
      unsubscribeAgent()
    }
  }, [])

  // Helper function to determine if user can select an agent
  const canUserSelectAgent = (agentId: string, userPlan: string, selectedAgents: any[]) => {
    const selectedCount = selectedAgents.length
    const maxAgents = userPlan === "free" ? 1 : userPlan === "starter" ? 4 : 7
    
    // If user has reached their limit, they can't select more
    if (selectedCount >= maxAgents) {
      return false
    }
    
    // Free users can't select Purity
    if (userPlan === "free" && agentId === "purity") {
      return false
    }
    
    return true
  }

  const loadAgentsData = async () => {
    try {
      setIsLoading(true)
      
      // Load agent health data and selected agents (no task metrics)
      const [healthResponse, selectedAgentsResponse] = await Promise.all([
        apiClient.getAgentHealth().catch(() => ({ data: { agents: [] } })), // Fallback if health endpoint fails
        apiClient.getSelectedAgents().catch(() => []) // Fallback if selected agents fails
      ])
      
      const healthData = healthResponse.data?.agents || []
      const selectedAgents = selectedAgentsResponse || []
      
      // Get user's subscription plan to determine agent limits
      const { userPlan } = useUserStore.getState()
      
      // Create agents with real data and proper selection logic
      const agentsWithRealData = agentTemplates.map(template => {
        const agentHealth = healthData.find((h: any) => h.agent_id === template.id)
        const selectedAgentData = selectedAgents.find((sa: any) => sa.agent_id === template.id)
        const isSelected = !!selectedAgentData
        const isLocked = selectedAgentData?.locked || false
        
        // Get agent status from selected agent data or health data
        const agentStatus = selectedAgentData?.status || agentHealth?.status || (isSelected ? "active" : "inactive")
        
        // Get configuration from selected agent data
        const config = selectedAgentData?.configuration || {}
        const customInstructions = config.custom_instructions || ""
        const configPreferences = config.preferences || {}
        
        // Merge default settings with configuration preferences
        const mergedSettings = { ...template.defaultSettings, ...configPreferences }
        
        // Determine if user can select this agent based on their plan
        const canSelect = canUserSelectAgent(template.id, userPlan, selectedAgents)
        
        return {
          ...template,
          status: agentStatus,
          settings: mergedSettings,
          customInstructions: customInstructions,
          isOnline: agentHealth?.is_online || false,
          isSelected: isSelected,
          isLocked: isLocked,
          canSelect: canSelect
        } as Agent
      })
      
      setAgents(agentsWithRealData)
    } catch (error) {
      console.error("Failed to load agents data:", error)
      // Fallback to template data without task metrics
      const fallbackAgents = agentTemplates.map(template => ({
        ...template,
        status: "inactive" as const,
        lastActive: "Never",
        settings: template.defaultSettings,
        isOnline: false,
        currentTask: undefined,
        performance: {
          responseTime: 0,
          accuracy: 0,
          uptime: 0
        }
      }))
      setAgents(fallbackAgents)
    } finally {
      setIsLoading(false)
      setRefreshing(false)
    }
  }

  const filteredAgents = agents.filter(
    (agent) =>
      agent.name.toLowerCase().includes(debouncedSearchTerm.toLowerCase()) ||
      agent.title.toLowerCase().includes(debouncedSearchTerm.toLowerCase()) ||
      agent.description.toLowerCase().includes(debouncedSearchTerm.toLowerCase()),
  )

  const handleToggleAgent = async (agentId: string) => {
    try {
      const agent = agents.find(a => a.id === agentId)
      if (!agent) return
      
      // Check if user can select this agent
      if (!agent.isSelected && !agent.canSelect) {
        console.log("User cannot select this agent due to plan limitations")
        return
      }
      
      // Toggle between active and paused/inactive
      const newStatus = agent.status === "active" ? "paused" : "active"
      
      // Update local state immediately for better UX
      setAgents(prev => prev.map(a => 
        a.id === agentId ? { ...a, status: newStatus } : a
      ))
      
      // Persist to backend
      try {
        const response = await apiClient.updateAgentStatus(agentId, newStatus)
        console.log("Agent status updated successfully:", response)
      } catch (e) {
        console.warn('Backend toggle failed, reverting', e)
        // Revert the change on error
        setAgents(prev => prev.map(a => 
          a.id === agentId ? { ...a, status: agent.status } : a
        ))
      }
      
    } catch (error) {
      console.error("Failed to toggle agent:", error)
      // Revert the change on error
      const agent = agents.find(a => a.id === agentId)
      if (agent) {
        setAgents(prev => prev.map(a => 
          a.id === agentId ? { ...a, status: agent.status } : a
        ))
      }
    }
  }

  const handleEditAgent = async (agent: Agent) => {
    setSelectedAgent(agent)
    setAgentSettings(agent.settings)
    
    // Load existing configuration from backend
    try {
      const configResponse = await apiClient.getAgentConfiguration(agent.id)
      const config = configResponse.data?.configuration || {}
      setCustomInstructions(config.custom_instructions || agent.customInstructions || "")
      
      // Merge with existing settings
      if (config.preferences) {
        setAgentSettings({ ...agent.settings, ...config.preferences })
      }
    } catch (error) {
      console.error("Failed to load agent configuration:", error)
      setCustomInstructions(agent.customInstructions || "")
    }
  }

  const handleSaveSettings = async () => {
    if (!selectedAgent) return
    
    try {
      setIsSaving(true)
      setSaveStatus("idle")
      
      // Persist to backend using configuration endpoint
      const response = await apiClient.updateAgentConfiguration(
        selectedAgent.id, 
        customInstructions,
        agentSettings
      )
      console.log("Agent configuration updated successfully:", response)
      
      // Update local state
      setAgents(prev => prev.map(agent => 
        agent.id === selectedAgent.id 
          ? { 
              ...agent, 
              settings: agentSettings,
              customInstructions 
            } 
          : agent
      ))
      
      setSaveStatus("success")
      setTimeout(() => {
        setSelectedAgent(null)
        setSaveStatus("idle")
      }, 1500)
      
    } catch (error) {
      console.error("Failed to save configuration:", error)
      setSaveStatus("error")
    } finally {
      setIsSaving(false)
    }
  }

  const loadIntercommunicationSetting = async () => {
    try {
      if (canUseIntercommunication) {
        const response = await apiClient.getIntercommunicationSetting()
        setIntercommunicationEnabled(response.data?.enabled || false)
      }
    } catch (error) {
      console.error("Failed to load intercommunication setting:", error)
    }
  }

  const handleRefresh = () => {
    setRefreshing(true)
    loadAgentsData()
  }

  const handleIntercommunicationToggle = async (enabled: boolean) => {
    try {
      // Update local state immediately for better UX
      setIntercommunicationEnabled(enabled)
      
      // Persist to backend
      const response = await apiClient.updateIntercommunicationSetting(enabled)
      console.log("Intercommunication setting updated successfully:", response)
      
    } catch (error) {
      console.error("Failed to toggle intercommunication:", error)
      // Revert the toggle on error
      setIntercommunicationEnabled(!enabled)
    }
  }

  const activeAgents = agents.filter((agent) => agent.status === "active").length

  return (
    <div className="p-3 sm:p-4 lg:p-6 space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 ">AI Agents</h1>
          <p className="text-gray-600  mt-1">
            Manage and monitor your {agents.length} AI agents
            {isLoading && <span className="ml-2 text-green-500">Loading...</span>}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            onClick={() => setShowAgentSelection(true)}
            className="flex items-center gap-2"
          >
            <Users className="w-4 h-4" />
            Select Agents
          </Button>
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Dialog>
            <DialogTrigger asChild>
              <Button>
                <Settings className="w-4 h-4 mr-2" />
                Manage All
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Manage All Agents</DialogTitle>
                <DialogDescription>Configure settings for all your AI agents</DialogDescription>
              </DialogHeader>
              <div className="space-y-6">
                {agents.map((agent) => (
                  <Card key={agent.id}>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-full ${agent.color} flex items-center justify-center`}>
                            <agent.icon className="w-5 h-5 text-white" />
                          </div>
                          <div>
                            <CardTitle className="text-lg">{agent.name}</CardTitle>
                            <CardDescription>{agent.title}</CardDescription>
                          </div>
                        </div>
                        <Switch
                          checked={agent.status === "active"}
                          onCheckedChange={() => handleToggleAgent(agent.id)}
                        />
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 gap-4">
                        {Object.entries(agent.settings).map(([key, value]) => (
                          <div key={key} className="flex items-center justify-between">
                            <Label htmlFor={`${agent.id}-${key}`} className="text-sm capitalize">
                              {key.replace(/([A-Z])/g, " $1").trim()}
                            </Label>
                            <Switch id={`${agent.id}-${key}`} checked={value as boolean} />
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="outline">Cancel</Button>
                <Button>Save All Changes</Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
        <Input
          placeholder="Search agents..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Intercommunication Toggle */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Agent Intercommunication
          </CardTitle>
          <CardDescription>
            {canUseIntercommunication 
              ? "Enable agents to communicate and collaborate with each other for maximum automation"
              : "Upgrade to Starter or Pro plan to enable agent intercommunication"
            }
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium">Intercommunication</p>
              <p className="text-xs text-muted-foreground">
                {canUseIntercommunication 
                  ? (intercommunicationEnabled 
                      ? "Agents can communicate and collaborate" 
                      : "Agents work independently")
                  : "Feature not available on Free plan"
                }
              </p>
            </div>
            <Switch
              checked={intercommunicationEnabled}
              onCheckedChange={handleIntercommunicationToggle}
              disabled={!canUseIntercommunication}
            />
          </div>
          {!canUseIntercommunication && (
            <div className="mt-3 p-3 bg-green-50  rounded-lg">
              <p className="text-sm text-green-700 ">
                💡 Upgrade to Starter or Pro plan to enable agent intercommunication and unlock maximum automation potential.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Agents</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeAgents}</div>
            <p className="text-xs text-muted-foreground">of {agents.length} total agents</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Selected Agents</CardTitle>
            <Bot className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{agents.filter(a => a.isSelected).length}</div>
            <p className="text-xs text-muted-foreground">agents configured</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Paused Agents</CardTitle>
            <Pause className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{agents.filter(a => a.status === "paused").length}</div>
            <p className="text-xs text-muted-foreground">temporarily inactive</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Online Agents</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{agents.filter(a => a.isOnline).length}</div>
            <p className="text-xs text-muted-foreground">currently online</p>
          </CardContent>
        </Card>
      </div>

      {/* Agents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredAgents.map((agent) => (
          <Card key={agent.id} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className={`w-12 h-12 rounded-full ${agent.color} flex items-center justify-center relative`}>
                    <agent.icon className="w-6 h-6 text-white" />
                    {agent.isOnline && (
                      <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-white animate-pulse" />
                    )}
                  </div>
                  <div>
                    <CardTitle className="text-lg">{agent.name}</CardTitle>
                    <CardDescription>{agent.title}</CardDescription>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge
                    variant={agent.status === "active" ? "default" : "secondary"}
                    className={
                      agent.status === "active"
                        ? "bg-green-100 text-green-800 border-green-200"
                        : agent.status === "paused"
                        ? "bg-yellow-100 text-yellow-800 border-yellow-200"
                        : "bg-gray-100 text-gray-800 border-gray-200"
                    }
                  >
                    <div
                      className={`w-2 h-2 rounded-full mr-1 ${
                        agent.status === "active" ? "bg-green-500" : 
                        agent.status === "paused" ? "bg-yellow-500" : "bg-gray-400"
                      }`}
                    />
                    {agent.status}
                  </Badge>
                  {agent.customInstructions && (
                    <Badge variant="outline" className="text-xs">
                      <Settings className="w-3 h-3 mr-1" />
                      Configured
                    </Badge>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-gray-600">{agent.description}</p>

              {agent.currentTask && (
                <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                    <span className="text-sm font-medium text-green-800">Currently working on:</span>
                  </div>
                  <p className="text-sm text-green-700 mt-1">{agent.currentTask}</p>
                </div>
              )}

                <div className="text-center">
                <div className="text-sm text-gray-600 ">
                  {agent.isOnline ? "Online" : "Offline"}
                </div>
              </div>


              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className={`flex-1 ${
                    agent.status === "active" 
                      ? "bg-green-50 hover:bg-green-100 text-green-700 border-green-300" 
                      : "bg-transparent"
                  }`}
                  onClick={() => handleToggleAgent(agent.id)}
                  disabled={isLoading || !agent.isSelected}
                  title={!agent.isSelected ? "Select this agent first" : agent.status === "active" ? "Pause agent" : "Activate agent"}
                >
                  {agent.status === "active" ? (
                    <>
                      <Pause className="w-4 h-4 mr-1" />
                      Pause
                    </>
                  ) : agent.status === "paused" ? (
                    <>
                      <Play className="w-4 h-4 mr-1" />
                      Resume
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 mr-1" />
                      Activate
                    </>
                  )}
                </Button>
                <Dialog>
                  <DialogTrigger asChild>
                    <Button variant="outline" size="sm" onClick={() => handleEditAgent(agent)}>
                      <Settings className="w-4 h-4" />
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-2xl">
                    <DialogHeader>
                      <DialogTitle className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-full ${agent.color} flex items-center justify-center`}>
                          <agent.icon className="w-4 h-4 text-white" />
                        </div>
                        Configure {agent.name}
                      </DialogTitle>
                      <DialogDescription>{agent.description}</DialogDescription>
                    </DialogHeader>
                    <div className="space-y-6">
                      <div className="space-y-4">
                        <div>
                          <h4 className="font-medium mb-2">Custom Instructions / Tweaks</h4>
                          <p className="text-sm text-gray-600 mb-3">
                            Add specific instructions or tweaks for this agent. The agent will strictly follow these instructions when processing your requests.
                          </p>
                          <Textarea 
                            placeholder="Example: Always use a professional tone, focus on B2B clients, prioritize email communication over social media, etc." 
                            className="min-h-[120px]"
                            value={customInstructions}
                            onChange={(e) => setCustomInstructions(e.target.value)}
                          />
                          <p className="text-xs text-gray-500 mt-2">
                            💡 Be specific and clear. These instructions will be added to the agent's system prompt and followed strictly.
                          </p>
                        </div>
                      </div>

                      <div className="space-y-4">
                        <h4 className="font-medium">Agent Preferences</h4>
                        <div className="grid grid-cols-2 gap-4">
                          {Object.entries(agentSettings).map(([key, value]) => (
                            <div key={key} className="flex items-center justify-between p-3 border rounded-lg">
                              <Label htmlFor={`${selectedAgent.id}-${key}`} className="text-sm capitalize cursor-pointer">
                                {key.replace(/([A-Z])/g, " $1").trim()}
                              </Label>
                              <Switch 
                                id={`${selectedAgent.id}-${key}`} 
                                checked={value as boolean}
                                onCheckedChange={(checked) => {
                                  setAgentSettings(prev => ({
                                    ...prev,
                                    [key]: checked
                                  }))
                                }}
                              />
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                    <div className="flex justify-end gap-2">
                      <Button 
                        variant="outline" 
                        onClick={() => setSelectedAgent(null)}
                        disabled={isSaving}
                      >
                        <X className="w-4 h-4 mr-1" />
                        Cancel
                      </Button>
                      <Button 
                        onClick={handleSaveSettings}
                        disabled={isSaving}
                        className="flex items-center gap-2"
                      >
                        {isSaving ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            Saving...
                          </>
                        ) : saveStatus === "success" ? (
                          <>
                            <CheckCircle className="w-4 h-4" />
                            Saved!
                          </>
                        ) : saveStatus === "error" ? (
                          <>
                            <AlertCircle className="w-4 h-4" />
                            Error
                          </>
                        ) : (
                          <>
                            <Save className="w-4 h-4" />
                            Save Changes
                          </>
                        )}
                      </Button>
                    </div>
                  </DialogContent>
                </Dialog>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader>
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-gray-200 rounded-full" />
                  <div className="space-y-2">
                    <div className="h-4 bg-gray-200 rounded w-20" />
                    <div className="h-3 bg-gray-200 rounded w-32" />
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="h-3 bg-gray-200 rounded w-full" />
                <div className="h-3 bg-gray-200 rounded w-3/4" />
                <div className="grid grid-cols-2 gap-4">
                  <div className="h-8 bg-gray-200 rounded" />
                  <div className="h-8 bg-gray-200 rounded" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {!isLoading && filteredAgents.length === 0 && (
        <Card>
          <CardContent className="p-8 text-center">
            <Search className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No agents found</h3>
            <p className="text-gray-500">Try adjusting your search criteria</p>
          </CardContent>
        </Card>
      )}

      {/* Agent Selection Modal */}
      <AgentSelectionModal
        isOpen={showAgentSelection}
        onClose={() => setShowAgentSelection(false)}
        onConfirm={() => {
          setShowAgentSelection(false)
          loadAgentsData() // Refresh agents after selection
        }}
      />
    </div>
  )
}
