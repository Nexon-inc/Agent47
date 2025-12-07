"use client"

import { LucideIcon } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface EmptyStateProps {
  icon: LucideIcon
  title: string
  description?: string
  action?: {
    label: string
    onClick: () => void
    variant?: "default" | "outline" | "secondary"
  }
  className?: string
}

export default function EmptyState({ 
  icon: Icon, 
  title, 
  description, 
  action,
  className 
}: EmptyStateProps) {
  return (
    <Card className={cn("border-dashed", className)}>
      <CardContent className="flex flex-col items-center justify-center text-center p-12">
        <div className="w-16 h-16 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center mb-4">
          <Icon className="w-8 h-8 text-gray-400 dark:text-gray-500" />
        </div>
        <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">{title}</h3>
        {description && (
          <p className="text-gray-600 dark:text-gray-400 max-w-md mb-6">{description}</p>
        )}
        {action && (
          <Button
            onClick={action.onClick}
            variant={action.variant || "default"}
            className="mt-2"
          >
            {action.label}
          </Button>
        )}
      </CardContent>
    </Card>
  )
}

// Predefined empty states for common scenarios
export const EmptyStates = {
  noAgents: {
    icon: "Bot" as const,
    title: "No Agents Selected",
    description: "You haven't selected any agents yet. Select agents to start automating your workflow.",
    actionLabel: "Select Agents"
  },
  noHistory: {
    icon: "History" as const,
    title: "No Activity Yet",
    description: "Your agent activities and interactions will appear here once you start using them.",
    actionLabel: "Go to Dashboard"
  },
  noPlatforms: {
    icon: "Globe" as const,
    title: "No Platforms Connected",
    description: "Connect your first platform to start automating tasks and workflows.",
    actionLabel: "Connect Platform"
  },
  noAnalytics: {
    icon: "BarChart3" as const,
    title: "No Analytics Data",
    description: "Analytics will appear once you start using agents and completing tasks.",
    actionLabel: "View Agents"
  },
  noInbox: {
    icon: "Inbox" as const,
    title: "No Messages",
    description: "Your messages and notifications will appear here.",
    actionLabel: "Refresh"
  },
  noTeam: {
    icon: "Users" as const,
    title: "No Team Members",
    description: "Invite team members to collaborate and manage your agents together.",
    actionLabel: "Invite Members"
  },
  noIntegrations: {
    icon: "Zap" as const,
    title: "No Integrations",
    description: "Connect third-party services to extend your agent capabilities.",
    actionLabel: "Browse Integrations"
  }
}

