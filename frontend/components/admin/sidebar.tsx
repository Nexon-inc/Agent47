"use client"

import type React from "react"

import { useState, useEffect } from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import {
  LayoutDashboard,
  Users,
  Bot,
  CreditCard,
  Settings,
  BarChart2,
  Sun,
  Moon,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  LogOut,
  FileText,
  X,
  Shield,
  Database,
  Server,
  AlertTriangle,
  Mail,
  HelpCircle,
  Zap,
  Target,
  Terminal,
  UserCheck,
  BarChart3,
  Activity,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useTheme } from "next-themes"
import { useAdminStore } from "@/lib/stores/admin-store"

type MenuItem = {
  name: string
  path: string
  icon: React.ElementType
  permissions: string[] // Use backend permission values
}

const menuItems: MenuItem[] = [
  {
    name: "Dashboard",
    path: "/admin",
    icon: LayoutDashboard,
    permissions: ["super_admin", "system_admin", "basic_admin", "read_only"],
  },
  {
    name: "Users",
    path: "/admin/users",
    icon: Users,
    permissions: ["super_admin", "system_admin", "basic_admin"],
  },
  {
    name: "Agents",
    path: "/admin/agents",
    icon: Bot,
    permissions: ["super_admin", "system_admin"],
  },
  {
    name: "Analytics",
    path: "/admin/analytics",
    icon: BarChart3,
    permissions: ["super_admin", "system_admin"],
  },
  {
    name: "Security",
    path: "/admin/security",
    icon: Shield,
    permissions: ["super_admin"],
  },
  {
    name: "Integrations",
    path: "/admin/integrations",
    icon: Zap,
    permissions: ["super_admin", "system_admin"],
  },
  {
    name: "Platforms",
    path: "/admin/platforms",
    icon: Server,
    permissions: ["super_admin", "system_admin"],
  },
  {
    name: "Finance",
    path: "/admin/finance",
    icon: CreditCard,
    permissions: ["super_admin", "system_admin"],
  },
  {
    name: "Goals",
    path: "/admin/goals",
    icon: Target,
    permissions: ["super_admin", "system_admin"],
  },
  {
    name: "Code",
    path: "/admin/code",
    icon: FileText,
    permissions: ["super_admin"],
  },
  {
    name: "System",
    path: "/admin/system",
    icon: Settings,
    permissions: ["super_admin"],
  },
  {
    name: "Database",
    path: "/admin/database",
    icon: Database,
    permissions: ["super_admin"],
  },
  {
    name: "Servers",
    path: "/admin/servers",
    icon: Server,
    permissions: ["super_admin"],
  },
  {
    name: "Alerts",
    path: "/admin/alerts",
    icon: AlertTriangle,
    permissions: ["super_admin", "system_admin"],
  },
  {
    name: "Communications",
    path: "/admin/communications",
    icon: Mail,
    permissions: ["super_admin", "system_admin"],
  },
  {
    name: "Support",
    path: "/admin/support",
    icon: HelpCircle,
    permissions: ["super_admin", "system_admin"],
  },
  {
    name: "Terminal",
    path: "/admin/terminal",
    icon: Terminal,
    permissions: ["super_admin"],
  },
  {
    name: "Impersonate",
    path: "/admin/impersonate",
    icon: UserCheck,
    permissions: ["super_admin"],
  },
  {
    name: "Settings",
    path: "/admin/settings",
    icon: Settings,
    permissions: ["super_admin", "system_admin"],
  },
  {
    name: "Logs",
    path: "/admin/logs",
    icon: FileText,
    permissions: ["super_admin", "system_admin"],
  },
  {
    name: "Features",
    path: "/admin/features",
    icon: Zap,
    permissions: ["super_admin"],
  },
  {
    name: "Cache",
    path: "/admin/cache",
    icon: Activity,
    permissions: ["super_admin"],
  },
  {
    name: "Reports",
    path: "/admin/reports",
    icon: BarChart2,
    permissions: ["super_admin", "system_admin"],
  },
  {
    name: "Chat",
    path: "/admin/chat",
    icon: Mail,
    permissions: ["super_admin", "system_admin"],
  },
  {
    name: "Billing",
    path: "/admin/billing",
    icon: CreditCard,
    permissions: ["super_admin", "system_admin"],
  },
]

interface AdminSidebarProps {
  onCollapseChange?: (collapsed: boolean) => void
}

export default function AdminSidebar({ onCollapseChange }: AdminSidebarProps) {
  const pathname = usePathname()
  const router = useRouter()
  const { theme, setTheme } = useTheme()
  const { currentAdmin, logout, permissionsLoaded, isLoading, error } = useAdminStore()

  // Debug logging to help identify why sidebar/updates might be missing
  useEffect(() => {
    if (typeof window !== 'undefined') {
      console.log("[AdminSidebar] State:", {
        isLoading,
        permissionsLoaded,
        hasAdmin: !!currentAdmin,
        perms: currentAdmin?.permissions,
        error: error
      })
    }
  }, [isLoading, permissionsLoaded, currentAdmin, error])
  const [isProfileOpen, setIsProfileOpen] = useState(false)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [isCollapsed, setIsCollapsed] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('admin_sidebar_collapsed') === 'true'
    }
    return false
  })

  // Check if user has permission for a menu item
  const hasPermission = (item: MenuItem): boolean => {
    if (!currentAdmin || !currentAdmin.permissions) return false
    // Super admin has access to everything
    if (currentAdmin.permissions.includes("super_admin")) return true
    // Check if user has any of the required permissions
    return item.permissions.some(perm => currentAdmin.permissions.includes(perm))
  }

  // Filter menu items based on permissions
  const visibleMenuItems = menuItems.filter(hasPermission)

  // Close mobile menu when path changes
  useEffect(() => {
    setIsMobileMenuOpen(false)
  }, [pathname])

  // Get user initials for avatar
  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
  }

  // Toggle theme between light and dark
  const toggleTheme = () => {
    setTheme(theme === "dark" ? "light" : "dark")
  }

  // Navigate to a path
  const navigateTo = (path: string) => {
    router.push(path)
  }

  // Handle menu item click
  const handleMenuClick = (path: string) => {
    if (pathname !== path) {
      router.push(path)
    }
  }

  return (
    <>
      {/* Mobile overlay */}
      {isMobileMenuOpen && (
        <div className="fixed inset-0 bg-black/50 z-40 md:hidden" onClick={() => setIsMobileMenuOpen(false)} />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed top-0 left-0 z-50 h-full bg-gray-900/95 backdrop-blur-sm text-gray-100 flex flex-col transition-all duration-300",
          "border-r border-gray-800/50",
          isCollapsed ? "w-16" : "w-64",
          "md:translate-x-0",
          isMobileMenuOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0",
        )}
      >
        {/* Close button (mobile only) */}
        <button className="absolute top-4 right-4 p-1 text-white md:hidden" onClick={() => setIsMobileMenuOpen(false)}>
          <X size={20} />
        </button>

        {/* Logo and collapse toggle */}
        <div className="p-2 flex items-center justify-between">
          <Link href="/admin" className="flex items-center transition-all hover:text-green-400">
            {!isCollapsed && <span className="text-xl font-bold">Agent47</span>}
            {!isCollapsed && <span className="text-xs ml-1 bg-green-500 px-1 rounded">Admin</span>}
            {isCollapsed && <span className="text-xl font-bold">A</span>}
          </Link>
          <button
            onClick={() => {
              const newCollapsed = !isCollapsed
              setIsCollapsed(newCollapsed)
              if (typeof window !== 'undefined') {
                localStorage.setItem('admin_sidebar_collapsed', String(newCollapsed))
                // Dispatch event for layout to listen
                window.dispatchEvent(new CustomEvent('sidebar-collapse', { detail: { collapsed: newCollapsed } }))
              }
              if (onCollapseChange) {
                onCollapseChange(newCollapsed)
              }
            }}
            className="p-1 text-gray-400 hover:text-white transition-colors hidden md:block"
            title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {isCollapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </button>
        </div>

        {/* Menu */}
        <nav className="flex-1 px-2 py-4 overflow-y-auto scrollbar-hide">
          {error ? (
            <div className="px-3 py-4 text-center">
              <AlertTriangle className="w-8 h-8 text-red-500 mx-auto mb-2" />
              {!isCollapsed && (
                <div className="space-y-2">
                  <p className="text-xs text-red-400 font-medium">Failed to load permissions</p>
                  <p className="text-[10px] text-gray-500 truncate">{error}</p>
                </div>
              )}
            </div>
          ) : isLoading || !permissionsLoaded ? (
            <div className="flex flex-col items-center justify-center h-32 space-y-2">
              <div className="w-5 h-5 border-2 border-green-500 border-t-transparent rounded-full animate-spin"></div>
              {!isCollapsed && <span className="text-xs text-gray-400">Loading permissions...</span>}
            </div>
          ) : visibleMenuItems.length === 0 ? (
            <div className="px-3 py-4 text-center">
              <Shield className="w-8 h-8 text-gray-600 mx-auto mb-2" />
              {!isCollapsed && (
                <p className="text-xs text-gray-500">No clearance level assigned. Contact system admin.</p>
              )}
            </div>
          ) : (
            <ul className="space-y-1">
              {visibleMenuItems.map((item) => (
                <li key={item.name}>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.preventDefault()
                      e.stopPropagation()
                      handleMenuClick(item.path)
                    }}
                    className={cn(
                      "flex items-center px-3 py-2 rounded-lg transition-colors text-sm cursor-pointer w-full text-left",
                      "hover:bg-gray-800/50 hover:text-white",
                      pathname === item.path ? "bg-green-600/20 border-l-2 border-green-500 font-semibold text-green-400" : "text-gray-400",
                      isCollapsed && "justify-center"
                    )}
                    title={isCollapsed ? item.name : undefined}
                  >
                    <item.icon className={cn("w-5 h-5", !isCollapsed && "mr-3", isCollapsed && "mx-auto")} />
                    {!isCollapsed && <span>{item.name}</span>}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </nav>

        {/* Theme toggle */}
        <div className="px-2 py-2">
          <button
            onClick={toggleTheme}
            className={cn(
              "flex items-center px-3 py-2 rounded-lg hover:bg-gray-800/50 transition-colors text-sm w-full text-gray-400",
            )}
          >
            {theme === "dark" ? (
              <>
                <Sun className="w-5 h-5 mr-3" />
                <span>Light Mode</span>
              </>
            ) : (
              <>
                <Moon className="w-5 h-5 mr-3" />
                <span>Dark Mode</span>
              </>
            )}
          </button>
        </div>

        {/* Profile */}
        <div className="p-2 border-t border-gray-800/50">
          <div
            className={cn("flex items-center p-2 rounded-lg cursor-pointer hover:bg-gray-800/50 text-gray-300", isCollapsed && "justify-center")}
            onClick={() => setIsProfileOpen(!isProfileOpen)}
          >
            <div className="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center text-white font-semibold flex-shrink-0">
              {currentAdmin?.email ? (
                getInitials(currentAdmin.email.split("@")[0] || "Admin")
              ) : (
                "A"
              )}
            </div>
            {!isCollapsed && (
              <>
                <div className="flex-1 min-w-0 ml-3">
                  <p className="text-sm font-medium truncate">{currentAdmin?.email?.split("@")[0] || "Admin"}</p>
                  <p className="text-xs text-green-400 truncate">
                    {currentAdmin?.permissions?.includes("super_admin") ? "Super Admin" :
                      currentAdmin?.permissions?.includes("system_admin") ? "System Admin" :
                        currentAdmin?.permissions?.includes("basic_admin") ? "Basic Admin" : "Admin"}
                  </p>
                </div>
                <ChevronDown className={cn("w-4 h-4 transition-transform", isProfileOpen ? "rotate-180" : "")} />
              </>
            )}
          </div>

          {/* Profile dropdown */}
          {isProfileOpen && !isCollapsed && (
            <div className="mt-2 py-2 bg-gray-800/90 backdrop-blur-sm rounded-lg border border-gray-700/50">
              <Link
                href="/admin/settings"
                className="flex items-center px-4 py-2 text-sm hover:bg-gray-600 text-gray-300"
              >
                <Users className="w-4 h-4 mr-3" />
                Settings
              </Link>
              <Link
                href="/admin/logs"
                className="flex items-center px-4 py-2 text-sm hover:bg-gray-600 text-gray-300"
              >
                <FileText className="w-4 h-4 mr-3" />
                Audit Logs
              </Link>
              <button
                onClick={async () => {
                  await logout()
                  router.push("/admin/login")
                }}
                className="flex items-center w-full px-4 py-2 text-sm hover:bg-gray-600 text-left text-gray-300"
              >
                <LogOut className="w-4 h-4 mr-3" />
                Sign Out
              </button>
            </div>
          )}
        </div>
      </aside>

      {/* Mobile menu button - this will be used in the navbar */}
      <button
        className="md:hidden fixed top-3 left-3 z-30 p-2 rounded-md bg-gray-900/90 backdrop-blur-sm border border-gray-800 text-white"
        onClick={() => setIsMobileMenuOpen(true)}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <line x1="3" y1="12" x2="21" y2="12"></line>
          <line x1="3" y1="6" x2="21" y2="6"></line>
          <line x1="3" y1="18" x2="21" y2="18"></line>
        </svg>
      </button>
    </>
  )
}
