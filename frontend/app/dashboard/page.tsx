"use client"

import { Suspense, useEffect, useState, lazy } from "react"
import { useSearchParams } from "next/navigation"
import { useAuthStore } from "@/lib/stores/auth-store"
import { apiClient } from "@/lib/api-client"
import AgentSelectionModal from "@/components/dashboard/agent-selection-modal"
import { useToast } from "@/hooks/use-toast"
import { ErrorBoundary } from "@/components/dashboard/error-boundary"
import { SkeletonAgentGrid } from "@/components/dashboard/skeletons"

// Import core tab components (eagerly loaded)
import HomeTab from "@/components/dashboard/tabs/home-tab"
import TeamManagementTab from "@/components/dashboard/tabs/team-management-tab"
import InboxTab from "@/components/dashboard/tabs/inbox-tab"
import AgentsOverviewTab from "@/components/dashboard/tabs/agents-overview-tab"
import HistoryTab from "@/components/dashboard/tabs/history-tab"
import PlatformsOverviewTab from "@/components/dashboard/tabs/platforms-overview-tab"
import ToolsAutomationOverviewTab from "@/components/dashboard/tabs/tools-automation-overview-tab"
import AccountOverviewTab from "@/components/dashboard/tabs/account-overview-tab"
import AnalyticsTab from "@/components/dashboard/tabs/analytics-tab"
import IntegrationsTab from "@/components/dashboard/tabs/integrations-tab"
import SettingsTab from "@/components/dashboard/tabs/settings-tab"
import SocialMediaTab from "@/components/dashboard/tabs/social-media-tab"
import MarketingTab from "@/components/dashboard/tabs/marketing-tab"
import MyAgentsTab from "@/components/dashboard/tabs/my-agents-tab"
import ExploreAgentsTab from "@/components/dashboard/tabs/explore-agents-tab"
import TeamChatTab from "@/components/dashboard/tabs/team-chat-tab"

// Lazy load individual agent tabs (code splitting)
const AriaTab = lazy(() => import("@/components/dashboard/tabs/aria-tab-new"))
const ClaraTab = lazy(() => import("@/components/dashboard/tabs/clara-tab"))
const EricTab = lazy(() => import("@/components/dashboard/tabs/eric-tab"))
const JackieTab = lazy(() => import("@/components/dashboard/tabs/jackie-tab"))
const ShakesTab = lazy(() => import("@/components/dashboard/tabs/shakes-tab"))
const JoeTab = lazy(() => import("@/components/dashboard/tabs/joe-tab"))
const PurityTab = lazy(() => import("@/components/dashboard/tabs/purity-tab"))

function DashboardContent() {
  const searchParams = useSearchParams()
  const tab = searchParams.get("tab") ?? "home"
  const { user, isAuthenticated } = useAuthStore()
  const [showAgentSelection, setShowAgentSelection] = useState(false)
  const [isCheckingAgents, setIsCheckingAgents] = useState(true)
  const { toast } = useToast()

  // Handle OAuth callback redirects
  useEffect(() => {
    const success = searchParams.get("success")
    const platform = searchParams.get("platform")
    const error = searchParams.get("error")
    const errorCode = searchParams.get("error_code")
    
    if (success === "platform_connected" && platform) {
      // Show success message
      toast({
        title: "Platform connected",
        description: `Successfully connected to ${platform}. You can now use it in your workflows.`,
      })
      
      // If we're on platforms tab, it will auto-refresh
      // If not, we could redirect to platforms tab
      if (tab !== "platforms-overview") {
        // Optionally redirect to platforms tab to see the connection
        // window.location.href = "/dashboard?tab=platforms-overview"
      }
    }
    
    if (error) {
      const errorMessage = searchParams.get("error_message") || errorCode || "Unknown error"
      console.error(`Platform connection error: ${errorMessage}`)
      toast({
        title: "Connection failed",
        description: errorMessage,
        variant: "destructive",
      })
    }
  }, [searchParams, tab])

  // Check if user has selected agents on dashboard load (only once)
  const [hasCheckedAgents, setHasCheckedAgents] = useState(false)
  
  useEffect(() => {
    const checkUserAgents = async () => {
      // Prevent duplicate checks
      if (hasCheckedAgents) return
      if (!isAuthenticated || !user) {
        setIsCheckingAgents(false)
        return
      }
      
      try {
        setIsCheckingAgents(true)
        setHasCheckedAgents(true) // Mark as checked immediately to prevent duplicates
        const selectedAgents = await apiClient.getSelectedAgents({ suppressTierRedirect: true })
        if (!selectedAgents || selectedAgents.length === 0) {
          // No agents selected - show modal only if not already showing
          if (!showAgentSelection) {
            setShowAgentSelection(true)
          }
        }
      } catch (error) {
        // If error (e.g., 404), user hasn't selected agents yet
        console.log("No agents selected yet, showing modal", error)
        // Only show modal if it's not already open
        if (!showAgentSelection) {
          setShowAgentSelection(true)
        }
      } finally {
        setIsCheckingAgents(false)
      }
    }

    checkUserAgents()
  }, [isAuthenticated, user, hasCheckedAgents, showAgentSelection])

  const handleAgentSelectionComplete = () => {
    setShowAgentSelection(false)
  }

  const renderTabContent = () => {
    switch (tab) {
      case "home":
        return <HomeTab />
      case "team-management":
        return <TeamManagementTab />
      case "team-chat":
        return <TeamChatTab />
      case "inbox":
        return <InboxTab />
      case "agents-overview":
        return <AgentsOverviewTab />
      case "history":
        return <HistoryTab />
      case "platforms-overview":
        return <PlatformsOverviewTab />
      case "tools-automation-overview":
        return <ToolsAutomationOverviewTab />
      case "account-overview":
        return <AccountOverviewTab />

      // Individual agent tabs (lazy loaded)
      case "aria":
        return (
          <Suspense fallback={<SkeletonAgentGrid count={3} />}>
            <AriaTab />
          </Suspense>
        )
      case "clara":
        return (
          <Suspense fallback={<SkeletonAgentGrid count={3} />}>
            <ClaraTab />
          </Suspense>
        )
      case "eric":
        return (
          <Suspense fallback={<SkeletonAgentGrid count={3} />}>
            <EricTab />
          </Suspense>
        )
      case "jackie":
        return (
          <Suspense fallback={<SkeletonAgentGrid count={3} />}>
            <JackieTab />
          </Suspense>
        )
      case "shakes":
        return (
          <Suspense fallback={<SkeletonAgentGrid count={3} />}>
            <ShakesTab />
          </Suspense>
        )
      case "joe":
        return (
          <Suspense fallback={<SkeletonAgentGrid count={3} />}>
            <JoeTab />
          </Suspense>
        )
      case "purity":
        return (
          <Suspense fallback={<SkeletonAgentGrid count={3} />}>
            <PurityTab />
          </Suspense>
        )
      case "janice":
        return (
          <Suspense fallback={<SkeletonAgentGrid count={3} />}>
            <JackieTab />
          </Suspense>
        )

      // Other tabs
      case "analytics":
        return <AnalyticsTab />
      case "integrations":
        return <IntegrationsTab />
      case "settings":
        return <SettingsTab />
      case "social-media":
        return <SocialMediaTab />
      case "marketing":
        return <MarketingTab />
      case "my-agents":
        return <MyAgentsTab />
      case "explore-agents":
        return <ExploreAgentsTab />

      default:
        return <HomeTab />
    }
  }

  return (
    <ErrorBoundary>
      {renderTabContent()}
      {!isCheckingAgents && (
        <AgentSelectionModal
          isOpen={showAgentSelection}
          onClose={() => setShowAgentSelection(false)}
          onConfirm={handleAgentSelectionComplete}
        />
      )}
    </ErrorBoundary>
  )
}

export default function DashboardPage() {
  return (
    <Suspense fallback={<div className="p-6">Loading...</div>}>
      <DashboardContent />
    </Suspense>
  )
}
