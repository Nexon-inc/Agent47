"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { cn } from "@/lib/utils"
import AdminSidebar from "./sidebar"
import AdminNavbar from "./navbar"

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const [isMounted, setIsMounted] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  const { fetchCurrentAdmin, isAuthenticated, isLoading } = useAdminStore()

  // Prevent hydration mismatch and load data
  useEffect(() => {
    setIsMounted(true)
    // Force dark mode for admin
    document.documentElement.classList.add("dark")

    // Fetch admin data if not already authenticated
    if (!isAuthenticated && !isLoading) {
      const token = localStorage.getItem("admin_token")
      if (token) {
        fetchCurrentAdmin().catch(err => console.error("AdminLayout: Failed to fetch admin:", err))
      }
    }
  }, [fetchCurrentAdmin, isAuthenticated, isLoading])

  useEffect(() => {
    // Listen for sidebar collapse state changes
    const handleStorageChange = () => {
      // Check if sidebar is collapsed from localStorage or state
      const collapsed = localStorage.getItem('admin_sidebar_collapsed') === 'true'
      setSidebarCollapsed(collapsed)
    }

    // Check initial state
    const collapsed = localStorage.getItem('admin_sidebar_collapsed') === 'true'
    setSidebarCollapsed(collapsed)

    // Listen for custom event from sidebar
    window.addEventListener('sidebar-collapse', handleStorageChange)
    return () => window.removeEventListener('sidebar-collapse', handleStorageChange)
  }, [])

  if (!isMounted) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-950 flex relative overflow-hidden">
      <AdminSidebar onCollapseChange={setSidebarCollapsed} />

      <div
        className={cn(
          "flex-1 flex flex-col min-h-screen relative z-10 transition-all duration-300",
          sidebarCollapsed ? "md:ml-16" : "md:ml-64"
        )}
      >
        <AdminNavbar />

        <main className="flex-1 p-4 md:p-6 lg:p-8 pt-20 md:pt-20 relative z-10 overflow-x-hidden">
          {children}
        </main>
      </div>
    </div>
  )
}
