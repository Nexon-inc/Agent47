"use client"

import type React from "react"
import { Suspense } from "react"

import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar"
import DashboardSidebar from "@/components/dashboard/sidebar"
import DashboardNavbar from "@/components/dashboard/navbar"
import DashboardBreadcrumbs from "@/components/dashboard/breadcrumbs"
import { useSearchParams } from "next/navigation"
import { cn } from "@/lib/utils"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const searchParams = useSearchParams()
  const currentTab = searchParams.get("tab")
  const isChatTab = currentTab === "chat"

  return (
    <SidebarProvider>
      <Suspense fallback={<div className="w-64 bg-gray-100 animate-pulse" />}>
        <DashboardSidebar />
      </Suspense>
      <SidebarInset className="bg-white">
        <DashboardNavbar />
        <main className={cn(
          "flex-1 bg-white",
          isChatTab ? "h-[calc(100vh-64px)] overflow-hidden p-0" : "overflow-auto p-4 md:p-6"
        )}>
          {!isChatTab && (
            <Suspense>
              <DashboardBreadcrumbs />
            </Suspense>
          )}
          {children}
        </main>
      </SidebarInset>
    </SidebarProvider>
  )
}
