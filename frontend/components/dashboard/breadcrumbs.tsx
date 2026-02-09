"use client"

import Link from "next/link"
import { usePathname, useSearchParams } from "next/navigation"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"
import { Home } from "lucide-react"

// Map tab names to display names
const tabDisplayNames: Record<string, string> = {
  home: "Dashboard",
  "team-management": "Team Management",
  inbox: "Inbox",
  "agents-overview": "AI Personnel",
  "my-agents": "My Agents",
  history: "History",
  "platforms-overview": "Platforms",
  "tools-automation-overview": "Tools & Automation",
  analytics: "Analytics",
  integrations: "Integrations",
  settings: "Settings",
  "account-overview": "Account",
  "social-media": "Social Media",
  marketing: "Marketing",
  "explore-agents": "Explore Agents",
  aria: "Aria",
  clara: "Clara",
  eric: "Eric",
  jackie: "Jackie",
  shakes: "Shakes",
  joe: "Joe",
  purity: "Purity",
  janice: "Janice",
}

// Agent display names
const agentDisplayNames: Record<string, string> = {
  aria: "Aria - Social Media Agent",
  clara: "Clara - Customer Support Agent",
  eric: "Eric - Sales Agent",
  jackie: "Jackie - Marketing Agent",
  shakes: "Shakes - Content Creation Agent",
  joe: "Joe - Research Agent",
  purity: "Purity - Business Intelligence Agent",
  janice: "Janice - Marketing Agent",
}

export default function DashboardBreadcrumbs() {
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const tab = searchParams.get("tab") || "home"

  // Don't show breadcrumbs on home tab
  if (tab === "home" || pathname !== "/dashboard") {
    return null
  }

  const breadcrumbs = [
    {
      label: "Dashboard",
      href: "/dashboard?tab=home",
      icon: Home,
    },
  ]

  // Add current tab
  const displayName = tabDisplayNames[tab] || tab
  const isAgentTab = ["aria", "clara", "eric", "jackie", "shakes", "joe", "purity", "janice"].includes(tab)

  if (isAgentTab) {
    // For agent tabs, add "My Agents" as intermediate step
    breadcrumbs.push({
      label: "My Agents",
      href: "/dashboard?tab=my-agents",
      icon: null,
    })
    breadcrumbs.push({
      label: agentDisplayNames[tab] || displayName,
      href: null,
      icon: null,
    })
  } else {
    breadcrumbs.push({
      label: displayName,
      href: null,
      icon: null,
    })
  }

  return (
    <Breadcrumb className="mb-4">
      <BreadcrumbList>
        {breadcrumbs.map((crumb, index) => {
          const isLast = index === breadcrumbs.length - 1
          const Icon = crumb.icon

          return (
            <div key={index} className="flex items-center">
              <BreadcrumbItem>
                {isLast ? (
                  <BreadcrumbPage className="flex items-center gap-1.5">
                    {Icon && <Icon className="h-4 w-4" />}
                    {crumb.label}
                  </BreadcrumbPage>
                ) : (
                  <BreadcrumbLink asChild>
                    <Link href={crumb.href || "#"} className="flex items-center gap-1.5">
                      {Icon && <Icon className="h-4 w-4" />}
                      {crumb.label}
                    </Link>
                  </BreadcrumbLink>
                )}
              </BreadcrumbItem>
              {!isLast && <BreadcrumbSeparator />}
            </div>
          )
        })}
      </BreadcrumbList>
    </Breadcrumb>
  )
}

