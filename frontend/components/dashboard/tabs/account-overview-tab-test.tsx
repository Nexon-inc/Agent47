"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Switch } from "@/components/ui/switch"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  User,
  Bell,
  Activity,
  Edit,
  Save,
  X,
  Upload,
  RefreshCw,
  Loader2,
  Settings,
} from "lucide-react"
import { apiClient } from "@/lib/api-client"
import { useAuthStore } from "@/lib/stores/auth-store"

export default function AccountOverviewTab() {
  const { user, isAuthenticated, refreshUser, forceRefresh } = useAuthStore()
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    console.log("Account tab loaded")
    setIsLoading(false)
  }, [])

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Account Settings</h1>
      <p>Test component</p>
    </div>
  )
}
