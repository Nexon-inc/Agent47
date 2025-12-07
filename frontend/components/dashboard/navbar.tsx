"use client"

import { useEffect, useMemo, useState } from "react"
import { Bell, Search, Settings, User, LogOut, Clock } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { useAuthStore } from "@/lib/stores/auth-store"

export default function DashboardNavbar() {
  const { user, logout } = useAuthStore()
  const [notifications] = useState([])
  const [now, setNow] = useState<number>(Date.now())

  // Free tier countdown: 14 days from signup/first login
  const freeExpiry = useMemo(() => {
    const startedAt = user?.created_at ? new Date(user.created_at).getTime() : null
    if (!startedAt) return null
    const fourteenDays = 14 * 24 * 60 * 60 * 1000
    return startedAt + fourteenDays
  }, [user?.created_at])

  useEffect(() => {
    if (!freeExpiry) return
    const id = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(id)
  }, [freeExpiry])

  const remaining = freeExpiry ? Math.max(0, freeExpiry - now) : 0
  const days = Math.floor(remaining / (1000 * 60 * 60 * 24))
  const hours = Math.floor((remaining % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
  const minutes = Math.floor((remaining % (1000 * 60 * 60)) / (1000 * 60))
  const seconds = Math.floor((remaining % (1000 * 60)) / 1000)
  
  const isFreeTier = user?.subscription_plan === 'free' || !user?.subscription_plan
  const showUpgradeBanner = isFreeTier && remaining < 48 * 60 * 60 * 1000 // Show when less than 48 hours left

  const unreadCount = notifications.filter((n) => n.unread).length

  return (
    <header className="flex h-14 sm:h-16 shrink-0 items-center gap-2 border-b bg-white px-2 sm:px-4">
      <SidebarTrigger className="-ml-1" />

      <div className="flex flex-1 items-center justify-between min-w-0">
        {/* Empty center space */}
        <div></div>

        {/* Right side actions */}
        <div className="flex items-center gap-1 sm:gap-2 min-w-0">
          {/* Free Tier Countdown */}
          {isFreeTier && remaining > 0 && (
            <div className="flex items-center gap-1 sm:gap-2">
              <Badge 
                variant="outline"
                className="bg-green-500 text-white border-green-500 text-xs"
              >
                <span className="hidden sm:inline">{user?.subscription_plan?.charAt(0).toUpperCase() + user?.subscription_plan?.slice(1) || 'Free'} Plan</span>
                <span className="sm:hidden">{user?.subscription_plan?.charAt(0).toUpperCase() || 'F'}</span>
              </Badge>
              <div className="flex items-center gap-1 text-xs sm:text-sm text-gray-600">
                <Clock className="h-3 w-3 sm:h-4 sm:w-4" />
                <span className="hidden sm:inline">
                  {days > 0 ? `${days}d` : ''} {hours}h {minutes}m
                </span>
                <span className="sm:hidden">
                  {days > 0 ? `${days}d` : ''} {hours}h
                </span>
              </div>
              {showUpgradeBanner && (
                <div className="animate-pulse bg-gradient-to-r from-orange-500 to-red-500 text-white px-2 sm:px-3 py-1 rounded-full text-xs sm:text-sm font-medium whitespace-nowrap">
                  <span className="hidden sm:inline">Upgrade Now!</span>
                  <span className="sm:hidden">Upgrade!</span>
                </div>
              )}
            </div>
          )}
          {/* Notifications */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="relative h-8 w-8 sm:h-9 sm:w-auto sm:px-3">
                <Bell className="h-4 w-4" />
                {unreadCount > 0 && (
                  <Badge className="absolute -top-1 -right-1 h-5 w-5 rounded-full p-0 text-xs bg-red-500">
                    {unreadCount}
                  </Badge>
                )}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-72 sm:w-80">
              <DropdownMenuLabel>Notifications</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {notifications.length === 0 ? (
                <DropdownMenuItem disabled className="text-center text-gray-500">
                  No notifications
                </DropdownMenuItem>
              ) : (
                notifications.map((notification) => (
                  <DropdownMenuItem key={notification.id} className="flex flex-col items-start p-3">
                    <div className="flex w-full items-center justify-between">
                      <span className="font-medium">{notification.title}</span>
                      {notification.unread && <div className="h-2 w-2 rounded-full bg-green-500" />}
                    </div>
                    <span className="text-sm text-gray-500">{notification.time}</span>
                  </DropdownMenuItem>
                ))
              )}
            </DropdownMenuContent>
          </DropdownMenu>

          {/* User menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center">
                  <User className="h-4 w-4 text-white" />
                </div>
                <span className="hidden sm:inline">{user?.name}</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>My Account</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem>
                <User className="mr-2 h-4 w-4" />
                Profile
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Settings className="mr-2 h-4 w-4" />
                Settings
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="text-red-600" onClick={logout}>
                <LogOut className="mr-2 h-4 w-4" />
                Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  )
}
