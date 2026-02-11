"use client"

import Link from "next/link"
import { useSearchParams } from "next/navigation"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import {
  Sidebar,
  SidebarHeader,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarFooter,
  SidebarRail,
} from "@/components/ui/sidebar"
import { useAuthStore } from "@/lib/stores/auth-store"
import { useRouter } from "next/navigation"

import { Home, BarChart3, Globe, Zap, Settings, Inbox, Users, LogOut, Bot, History, UserPlus, TrendingUp } from "lucide-react"

const navigationItems = [
  {
    title: "Dashboard",
    icon: Home,
    href: "/dashboard?tab=home",
  },
  {
    title: "Strategy Room",
    icon: Users,
    href: "/dashboard?tab=team-chat",
  },
  {
    title: "AI Personnel",
    icon: Bot,
    href: "/dashboard?tab=agents-overview",
  },
  {
    title: "Platforms",
    icon: Globe,
    href: "/dashboard?tab=platforms-overview",
  },
  {
    title: "Tools",
    icon: Zap,
    href: "/dashboard?tab=tools-automation-overview",
  },
  {
    title: "Organization",
    icon: Users,
    href: "/dashboard?tab=team-management",
  },
  {
    title: "Personnel Box",
    icon: Inbox,
    href: "/dashboard?tab=inbox",
  },
  {
    title: "Workforce Analytics",
    icon: BarChart3,
    href: "/dashboard?tab=analytics",
  },
  {
    title: "Operational Logs",
    icon: History,
    href: "/dashboard?tab=history",
  },
  {
    title: "Account Settings",
    icon: Settings,
    href: "/dashboard?tab=account-overview",
  },
]

export default function DashboardSidebar() {
  const searchParams = useSearchParams()
  const currentTab = searchParams.get("tab") ?? "home"
  const { user, logout } = useAuthStore()
  const router = useRouter()

  const isActive = (href: string) => {
    if (!href) return false
    const tab = new URLSearchParams(href.includes("?") ? href.split("?")[1] : "").get("tab")
    return tab === currentTab
  }

  return (
    <Sidebar collapsible="icon" className="border-r">
      <SidebarHeader className="border-b p-4">
        <Link href="/dashboard?tab=home" prefetch={true} className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-gradient-to-br from-green-400 to-green-600 rounded-lg flex items-center justify-center shrink-0">
            <span className="text-white font-bold text-sm">47</span>
          </div>
          <span className="text-slate-900 font-bold text-xl group-data-[collapsible=icon]:hidden">
            Agent<span className="text-green-500">47</span>
          </span>
        </Link>

      </SidebarHeader>

      <SidebarContent className="p-2">
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu className="space-y-1">
              {navigationItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    asChild
                    tooltip={item.title}
                    isActive={isActive(item.href)}
                    className={cn(
                      "group flex items-center px-3 py-2.5 rounded-lg relative transition-all duration-200 w-full",
                      isActive(item.href)
                        ? "bg-emerald-50 text-emerald-900 font-bold border border-emerald-100"
                        : "text-slate-700 hover:bg-slate-50 hover:text-slate-900 font-medium",
                    )}
                  >
                    <Link href={item.href} prefetch={true} className="flex items-center w-full">
                      <item.icon
                        className={cn(
                          "h-5 w-5 shrink-0",
                          isActive(item.href)
                            ? "text-emerald-600"
                            : "text-slate-500",
                        )}
                      />
                      <span className="ml-3 truncate group-data-[collapsible=icon]:hidden">{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="border-t p-2">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              asChild
              tooltip="Sign Out"
              className="flex items-center px-3 py-2.5 text-sm font-medium text-slate-600 rounded-lg hover:bg-red-50 hover:text-red-600 transition-colors"
            >
              <button
                type="button"
                onClick={async (e) => {
                  e.preventDefault()
                  await logout()
                  // ensure storage/cookies cleared then navigate to auth
                  router.push('/auth')
                }}
                className="flex items-center w-full text-left"
              >
                <LogOut className="h-5 w-5 shrink-0" />
                <span className="ml-3 group-data-[collapsible=icon]:hidden">Sign Out</span>
              </button>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>
  )
}
