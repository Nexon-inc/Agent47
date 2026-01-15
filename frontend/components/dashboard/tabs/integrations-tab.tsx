"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { Check, ExternalLink, RefreshCw, Lock, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { useUserStore } from "@/lib/stores/user-store"
import { apiClient } from "@/lib/api-client"

// Types
interface Integration {
  id: string
  name: string
  display_name?: string
  description: string
  logo?: string
  icon_url?: string
  connected: boolean
  category: "social" | "marketing" | "crm" | "productivity" | "other"
  tier: "starter" | "pro" | "ecosystem"
  integration_type?: string
  pricing_tier?: string
}

export default function IntegrationsTab() {
  const { userPlan } = useUserStore()
  const [category, setCategory] = useState<string>("all")
  const [searchQuery, setSearchQuery] = useState("")
  const [integrations, setIntegrations] = useState<Integration[]>([])
  const [connectedIntegrations, setConnectedIntegrations] = useState<Set<string>>(new Set())
  const [isLoading, setIsLoading] = useState(true)
  const [isToggling, setIsToggling] = useState<string | null>(null)

  // Load integrations data
  useEffect(() => {
    loadIntegrationsData()
  }, [])

  // Subscribe to real-time integration updates via WebSocket
  useEffect(() => {
    const { websocketService } = require('@/lib/websocket-service')
    
    if (!websocketService.getConnectionStatus()) {
      websocketService.connect()
    }

    // Reload when integrations are connected/disconnected
    const unsubscribe = websocketService.subscribe('notification', (message) => {
      if (message.data?.type === 'integration_error' || message.data?.type === 'platform_update') {
        loadIntegrationsData()
      }
    })

    return () => unsubscribe()
  }, [])

  const loadIntegrationsData = async () => {
    try {
      setIsLoading(true)
      
      // Load available integrations and connected integrations in parallel
      const [availableResponse, connectedResponse] = await Promise.all([
        apiClient.get("/api/v1/integrations/").catch(() => ({ data: [] })),
        apiClient.get("/api/v1/integrations/connected").catch(() => ({ data: { integrations: [] } }))
      ])

      // Handle wrapped response from apiClient.get()
      const availableIntegrations = availableResponse?.data || availableResponse || []
      const connected = connectedResponse?.data?.integrations || connectedResponse?.data || []

      // Create a set of connected integration names
      const connectedSet = new Set(connected.map((int: any) => int.integration_name || int.name))

      // Map available integrations to our format
      const mappedIntegrations: Integration[] = availableIntegrations.map((int: any) => {
        // Map integration_type to category
        let category: Integration["category"] = "other"
        if (int.integration_type === "social_media") category = "social"
        else if (int.integration_type === "marketing") category = "marketing"
        else if (int.integration_type === "crm") category = "crm"
        else if (int.integration_type === "productivity") category = "productivity"

        // Map pricing_tier to tier
        let tier: Integration["tier"] = "starter"
        if (int.pricing_tier === "pro") tier = "pro"
        else if (int.pricing_tier === "ecosystem") tier = "ecosystem"

        return {
          id: int.name || int.id,
          name: int.display_name || int.name,
          description: int.description || `Connect to ${int.display_name || int.name}`,
          logo: int.icon_url || int.logo || "/placeholder.svg?height=64&width=64",
          connected: connectedSet.has(int.name),
          category,
          tier,
          integration_type: int.integration_type,
          pricing_tier: int.pricing_tier
        }
      })

      setIntegrations(mappedIntegrations)
      setConnectedIntegrations(connectedSet)
    } catch (error) {
      console.error("Failed to load integrations:", error)
    } finally {
      setIsLoading(false)
    }
  }

  // Filter integrations based on category and search
  const filteredIntegrations = integrations.filter((integration) => {
    const matchesCategory = category === "all" || integration.category === category
    const matchesSearch =
      integration.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      integration.description.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesCategory && matchesSearch
  })

  // Check if integration is available for current plan
  const isAvailableForPlan = (integration: Integration) => {
    if (userPlan === "free") return false
    if (userPlan === "starter") return integration.tier === "starter"
    if (userPlan === "pro") return integration.tier === "starter" || integration.tier === "pro"
    return true // ecosystem has access to all
  }

  // Toggle integration connection
  const toggleConnection = async (integrationId: string, isConnected: boolean) => {
    try {
      setIsToggling(integrationId)
      
      if (isConnected) {
        // Disconnect
        await apiClient.post(`/api/v1/integrations/disconnect/${integrationId}`)
        setConnectedIntegrations(prev => {
          const newSet = new Set(prev)
          newSet.delete(integrationId)
          return newSet
        })
        // Update local state
        setIntegrations(prev => prev.map(int => 
          int.id === integrationId ? { ...int, connected: false } : int
        ))
      } else {
        // Connect - initiate OAuth or direct connection
        try {
          // Try OAuth first
          const oauthResponse = await apiClient.get(`/api/v1/integrations/oauth/${integrationId}`).catch(() => null)
          if (oauthResponse?.data?.oauth_url || oauthResponse?.oauth_url) {
            // Redirect to OAuth URL
            window.location.href = oauthResponse.data?.oauth_url || oauthResponse.oauth_url
          } else {
            // If no OAuth, try direct connection endpoint
            try {
              await apiClient.post(`/api/v1/integrations/connect/${integrationId}`, {})
              // Reload integrations after connection
              await loadIntegrationsData()
            } catch (directError: any) {
              // If direct connection fails, might need credentials
              console.error("Direct connection failed, may require credentials:", directError)
              throw new Error("Connection requires authentication. Please check integration settings.")
            }
          }
        } catch (error: any) {
          // If OAuth not supported, might need direct credentials
          console.error("Failed to initiate connection:", error)
          throw error
        }
      }
    } catch (error) {
      console.error("Failed to toggle integration connection:", error)
    } finally {
      setIsToggling(null)
    }
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl md:text-3xl font-extrabold text-[#4B0082]  mb-4">Integrations</h1>
        <p className="text-gray-600  mb-6">
          Connect your agents to third-party services.
          {userPlan === "free"
            ? " Upgrade to unlock integrations."
            : userPlan === "starter"
              ? " Starter plan includes basic integrations."
              : userPlan === "pro"
                ? " Pro plan includes advanced integrations."
                : " Ecosystem plan includes all integrations."}
        </p>
      </div>

      {userPlan === "free" ? (
        <div className="bg-white  rounded-xl shadow-sm border border-gray-200  p-8 text-center">
          <div className="w-16 h-16 bg-gray-100  rounded-full flex items-center justify-center mx-auto mb-4">
            <Lock className="w-8 h-8 text-gray-400 " />
          </div>
          <h2 className="text-xl font-semibold text-gray-900  mb-2">Integrations Locked</h2>
          <p className="text-gray-600  mb-6 max-w-md mx-auto">
            Integrations are available on paid plans. Upgrade to connect your agents with third-party services.
          </p>
          <a
            href="/pricing"
            className="inline-flex items-center justify-center px-6 py-3 bg-[#00FF88] text-white font-semibold rounded-lg hover:bg-[#00FF88]/90 transition-colors"
          >
            Upgrade to Unlock
          </a>
        </div>
      ) : isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-[#1E90FF]" />
          <span className="ml-2 text-gray-600">Loading integrations...</span>
        </div>
      ) : (
        <>
          {/* Filters */}
          <div className="flex flex-wrap gap-4 mb-6">
            <div className="flex-1 min-w-[200px]">
              <input
                type="text"
                placeholder="Search integrations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full h-10 px-3 rounded-lg border border-gray-300  bg-white  text-gray-900  focus:outline-none focus:ring-2 focus:ring-[#1E90FF]"
              />
            </div>
            <div>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full h-10 px-3 rounded-lg border border-gray-300  bg-white  text-gray-900  focus:outline-none focus:ring-2 focus:ring-[#1E90FF]"
              >
                <option value="all">All Categories</option>
                <option value="social">Social Media</option>
                <option value="marketing">Marketing</option>
                <option value="crm">CRM</option>
                <option value="productivity">Productivity</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>

          {/* Integrations Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredIntegrations.map((integration) => {
              const isAvailable = isAvailableForPlan(integration)

              return (
                <motion.div
                  key={integration.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                  className={cn(
                    "bg-white  rounded-xl shadow-sm border overflow-hidden",
                    integration.connected
                      ? "border-[#1E90FF] [#1E90FF]"
                      : "border-gray-200 ",
                    !isAvailable && "opacity-60",
                  )}
                >
                  <div className="p-6">
                    <div className="flex items-center mb-4">
                      <div className="w-12 h-12 bg-gray-100  rounded-lg flex items-center justify-center mr-4">
                        <img
                          src={integration.logo || "/placeholder.svg"}
                          alt={integration.name}
                          className="w-8 h-8 object-contain"
                        />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900  flex items-center">
                          {integration.name}
                          {!isAvailable && (
                            <span className="ml-2 text-xs bg-gray-100  text-gray-500  px-2 py-0.5 rounded-full">
                              {integration.tier === "pro" ? "Pro" : "Ecosystem"}
                            </span>
                          )}
                        </h3>
                        <p className="text-sm text-gray-500 ">{integration.description}</p>
                      </div>
                    </div>

                    <div className="flex justify-between items-center">
                      {integration.connected ? (
                        <div className="flex items-center text-sm text-green-500">
                          <Check className="w-4 h-4 mr-1" />
                          Connected
                        </div>
                      ) : (
                        <div className="flex items-center text-sm text-gray-500 ">
                          {isAvailable ? "Not connected" : `Available in ${integration.tier} plan`}
                        </div>
                      )}

                      {isAvailable && (
                        <button
                          onClick={() => toggleConnection(integration.id, integration.connected)}
                          disabled={isToggling === integration.id}
                          className={cn(
                            "px-3 py-1.5 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed",
                            integration.connected
                              ? "bg-gray-100  text-gray-700  hover:bg-gray-200 :bg-gray-600"
                              : "bg-[#1E90FF] text-white hover:bg-[#1E90FF]/90",
                          )}
                        >
                          {isToggling === integration.id ? (
                            <div className="flex items-center">
                              <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                              {integration.connected ? "Disconnecting..." : "Connecting..."}
                            </div>
                          ) : integration.connected ? (
                            <div className="flex items-center">
                              <RefreshCw className="w-4 h-4 mr-1" />
                              Disconnect
                            </div>
                          ) : (
                            <div className="flex items-center">
                              <ExternalLink className="w-4 h-4 mr-1" />
                              Connect
                            </div>
                          )}
                        </button>
                      )}
                    </div>
                  </div>
                </motion.div>
              )
            })}
          </div>

          {filteredIntegrations.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-500 ">No integrations found matching your criteria.</p>
            </div>
          )}
        </>
      )}
    </div>
  )
}
