"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Search, Bell, HelpCircle, ChevronDown, X, User } from "lucide-react"
import { cn } from "@/lib/utils"

// Mock alerts data
const alerts: any[] = []

// Mock recent users for impersonation
const recentUsers: any[] = []

export default function AdminNavbar() {
  const pathname = usePathname()
  const [searchQuery, setSearchQuery] = useState("")
  const [showSearchMobile, setShowSearchMobile] = useState(false)
  const [showAlerts, setShowAlerts] = useState(false)
  const [showImpersonation, setShowImpersonation] = useState(false)

  const alertsRef = useRef<HTMLDivElement>(null)
  const impersonationRef = useRef<HTMLDivElement>(null)

  // Get breadcrumb from pathname
  const getBreadcrumb = () => {
    const paths = (pathname || "").split("/").filter(Boolean)

    if (paths.length === 0) return []

    const breadcrumbs = [{ name: "Admin", path: "/admin" }]

    if (paths.length > 1 && paths[0] === "admin") {
      const currentPath = paths[1]
      breadcrumbs.push({
        name: currentPath.charAt(0).toUpperCase() + currentPath.slice(1),
        path: `/${paths[0]}/${currentPath}`,
      })
    }

    return breadcrumbs
  }

  const breadcrumbs = getBreadcrumb()

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (alertsRef.current && !alertsRef.current.contains(event.target as Node)) {
        setShowAlerts(false)
      }
      if (impersonationRef.current && !impersonationRef.current.contains(event.target as Node)) {
        setShowImpersonation(false)
      }
    }

    document.addEventListener("mousedown", handleClickOutside)
    return () => {
      document.removeEventListener("mousedown", handleClickOutside)
    }
  }, [])

  // Handle search submit
  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // Handle search logic here
    console.log("Searching for:", searchQuery)
  }

  // Handle alert resolution
  const handleResolveAlert = (id: number) => {
    // In a real app, this would call an API
    console.log("Resolving alert:", id)
  }

  // Handle user impersonation
  const handleImpersonate = (userId: string) => {
    // In a real app, this would call an API
    console.log("Impersonating user:", userId)
  }

  return (
    <header className="sticky top-0 left-0 right-0 h-16 bg-gray-900/95 backdrop-blur-sm border-b border-gray-800/50 z-30">
      <div className="h-full px-4 flex items-center justify-between">
        {/* Left section - Breadcrumb (hidden on mobile when search is active) */}
        <div className={cn("hidden md:flex items-center space-x-2", showSearchMobile ? "hidden" : "flex")}>
          {breadcrumbs.map((crumb, index) => (
            <div key={crumb.path} className="flex items-center">
              {index > 0 && <span className="mx-2 text-gray-400">/</span>}
              <Link
                href={crumb.path}
                className="text-sm text-gray-300 hover:text-green-400"
              >
                {crumb.name}
              </Link>
            </div>
          ))}
        </div>

        {/* Center - Search (full width on mobile when active) */}
        <div className={cn("relative", showSearchMobile ? "w-full" : "hidden md:block w-auto md:w-80 lg:w-96")}>
          <form onSubmit={handleSearchSubmit}>
            <div className="relative">
              <input
                type="text"
                placeholder="Search users, agents, or IDs..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full h-10 pl-10 pr-4 rounded-lg border border-gray-700 bg-gray-800 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500"
              />
              <Search className="absolute left-3 top-2.5 w-5 h-5 text-gray-400" />

              {/* Close button for mobile search */}
              {showSearchMobile && (
                <button type="button" className="absolute right-3 top-2.5" onClick={() => setShowSearchMobile(false)}>
                  <X className="w-5 h-5 text-gray-400" />
                </button>
              )}
            </div>
          </form>
        </div>

        {/* Right section - Icons */}
        <div className="flex items-center space-x-4">
          {/* Mobile search toggle */}
          {!showSearchMobile && (
            <button className="md:hidden" onClick={() => setShowSearchMobile(true)}>
              <Search className="w-5 h-5 text-gray-300" />
            </button>
          )}

          {/* Alerts */}
          <div className="relative" ref={alertsRef}>
            <button className="relative p-1" onClick={() => setShowAlerts(!showAlerts)}>
              <Bell className="w-5 h-5 text-gray-300" />
              {alerts.filter((a) => !a.read).length > 0 && (
                <span className="absolute top-0 right-0 w-4 h-4 bg-red-500 rounded-full text-xs text-white flex items-center justify-center">
                  {alerts.filter((a) => !a.read).length}
                </span>
              )}
            </button>

            {/* Alerts dropdown */}
            {showAlerts && (
              <div className="absolute right-0 mt-2 w-80 bg-gray-900/95 backdrop-blur-sm rounded-lg shadow-lg border border-gray-800 z-10">
                <div className="p-3 border-b border-gray-800">
                  <h3 className="font-medium text-white">Notifications</h3>
                </div>
                <div className="max-h-96 overflow-y-auto">
                  {alerts.length > 0 ? (
                    <div className="divide-y divide-gray-800">
                      {alerts.map((alert) => (
                        <div key={alert.id} className="p-4 hover:bg-gray-800">
                          <div className="flex justify-between">
                            <p
                              className={cn(
                                "text-sm",
                                alert.read
                                  ? "text-gray-500"
                                  : "text-white font-medium",
                              )}
                            >
                              {alert.message}
                            </p>
                            <button className="text-green-500 text-xs hover:text-green-400" onClick={() => handleResolveAlert(alert.id)}>
                              Resolve
                            </button>
                          </div>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{alert.time}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-4 text-center text-gray-500">No notifications</div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Impersonation - Superadmin only */}
          <div className="relative hidden md:block" ref={impersonationRef}>
            <button
              className="flex items-center space-x-1 text-sm text-gray-300 border border-gray-700 rounded-lg px-3 py-1.5 hover:bg-gray-800"
              onClick={() => setShowImpersonation(!showImpersonation)}
            >
              <User className="w-4 h-4 mr-1" />
              <span>Impersonate</span>
              <ChevronDown className="w-4 h-4" />
            </button>

            {/* Impersonation dropdown */}
            {showImpersonation && (
              <div className="absolute right-0 mt-2 w-64 bg-gray-900/95 backdrop-blur-sm rounded-lg shadow-lg border border-gray-800 z-10">
                <div className="p-3 border-b border-gray-800">
                  <h3 className="font-medium text-white">Recent Users</h3>
                </div>
                <div className="max-h-96 overflow-y-auto">
                  {recentUsers.map((user) => (
                    <button
                      key={user.id}
                      className="w-full p-3 text-left hover:bg-gray-800 flex items-center"
                      onClick={() => handleImpersonate(user.id)}
                    >
                      <div className="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center text-white font-semibold mr-3">
                        {user.name.charAt(0)}
                      </div>
                      <div>
                        <p className="text-sm font-medium text-white">{user.name}</p>
                        <p className="text-xs text-gray-400">{user.email}</p>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Help */}
          <Link href="/admin/help" className="p-1">
            <HelpCircle className="w-5 h-5 text-gray-300" />
          </Link>
        </div>
      </div>
    </header>
  )
}
