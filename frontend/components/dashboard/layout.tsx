"use client"

import type React from "react"
import { Suspense } from "react"

import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar"
import DashboardSidebar from "@/components/dashboard/sidebar"
import DashboardNavbar from "@/components/dashboard/navbar"
import DashboardBreadcrumbs from "@/components/dashboard/breadcrumbs"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <SidebarProvider>
      <Suspense fallback={<div className="w-64 bg-gray-100 animate-pulse" />}>
        <DashboardSidebar />
      </Suspense>
      <SidebarInset className="bg-white">
        <DashboardNavbar />
        <main className="flex-1 overflow-auto p-4 md:p-6 bg-white">
          <Suspense>
            <DashboardBreadcrumbs />
          </Suspense>
          {children}
        </main>
      </SidebarInset>
    </SidebarProvider>
  )
}
