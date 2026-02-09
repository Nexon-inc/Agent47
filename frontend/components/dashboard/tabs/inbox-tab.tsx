"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Inbox,
  Mail,
  Bell,
  CheckCircle,
  AlertCircle,
  Info,
  Star,
  Archive,
  Trash2,
  Reply,
  Forward,
  Eye,
  EyeOff,
  Filter,
  Search,
  RefreshCw,
  Loader2,
  Plus,
  Edit,
  Send,
  Clock,
  User,
  Users,
  Globe,
  Shield,
  Zap,
  Target,
  TrendingUp,
  Activity,
  BarChart3,
  Calendar,
  MessageSquare,
  FileText,
  Image,
  Video,
  Music,
  Map,
  ShoppingCart,
  CreditCard,
  Headphones,
  Megaphone,
  Settings,
  Crown,
  Lock,
  Unlock,
  MoreHorizontal,
  X,
  ChevronDown,
  ChevronUp,
  ChevronLeft,
  ChevronRight,
  ArrowUp,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  MoreVertical,
  Menu,
  MenuSquare,
  PanelLeft,
  PanelRight,
  PanelTop,
  PanelBottom,
  Sidebar,
  SidebarClose,
  SidebarOpen,
  Tabs,
  Tab,
  Window,
  Windows,
  Monitor,
  Laptop,
  Smartphone,
  Tablet,
  Headphones as HeadphonesIcon,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  PlayCircle,
  PauseCircle,
  StopCircle,
  SkipBack,
  SkipForward,
  Repeat,
  Shuffle,
  FastForward,
  Rewind,
  Radio,
  Tv,
  Camera,
  Video as VideoIcon,
  Film,
  Music as MusicIcon,
  Disc,
  Speaker,
} from "lucide-react"
import { apiClient } from "@/lib/api-client"
import { useAuthStore } from "@/lib/stores/auth-store"
import { useUserStore } from "@/lib/stores/user-store"
import { SkeletonList } from "@/components/dashboard/skeletons"
import EmptyState, { EmptyStates } from "@/components/dashboard/empty-state"
import ErrorDisplay from "@/components/dashboard/error-display"

interface InboxMessage {
  id: number
  title: string
  content: string
  message_type: string
  priority: string
  status: string
  sender_type: string
  sender_id: string
  sender_name: string
  sender_avatar?: string
  created_at: string
  read_at?: string
  metadata: Record<string, any>
  actions?: InboxAction[]
}

interface InboxAction {
  id: string
  label: string
  action_type: string
  url?: string
  data?: Record<string, any>
}

interface InboxStats {
  total_messages: number
  unread_count: number
  by_type: Record<string, number>
  by_priority: Record<string, number>
  by_status: Record<string, number>
}

interface InboxSettings {
  email_notifications: boolean
  push_notifications: boolean
  digest_frequency: string
  auto_archive_days: number
  priority_filter: string[]
}

export default function InboxTab() {
  const { user } = useAuthStore()
  const { userPlan } = useUserStore()

  const [messages, setMessages] = useState<InboxMessage[]>([])
  const [inboxStats, setInboxStats] = useState<InboxStats | null>(null)
  const [inboxSettings, setInboxSettings] = useState<InboxSettings | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const [error, setError] = useState<Error | string | null>(null)

  // Dialog states
  const [showSettingsDialog, setShowSettingsDialog] = useState(false)
  const [selectedMessage, setSelectedMessage] = useState<InboxMessage | null>(null)
  const [showMessageDialog, setShowMessageDialog] = useState(false)

  // Search and filter states
  const [searchTerm, setSearchTerm] = useState("")
  const [typeFilter, setTypeFilter] = useState("all")
  const [priorityFilter, setPriorityFilter] = useState("all")
  const [statusFilter, setStatusFilter] = useState("all")
  const [showUnreadOnly, setShowUnreadOnly] = useState(false)

  // Load data on mount
  useEffect(() => {
    loadInboxData()
    loadInboxSettings()
  }, [])

  // Subscribe to real-time notifications via WebSocket
  useEffect(() => {
    const { websocketService } = require('@/lib/websocket-service')

    // Ensure WebSocket is connected
    if (!websocketService.getConnectionStatus()) {
      websocketService.connect()
    }

    // Subscribe to notifications
    const unsubscribe = websocketService.subscribe('notification', (message) => {
      // Reload inbox when new notification arrives
      loadInboxData()
    })

    return () => {
      unsubscribe()
    }
  }, [])

  const loadInboxData = async () => {
    try {
      setIsLoading(true)
      setIsRefreshing(true)
      setError(null)

      // Load inbox data in parallel
      const [messagesResponse, statsResponse] = await Promise.all([
        apiClient.get("/api/inbox/messages").catch(() => ({ data: [] })),
        apiClient.get("/api/inbox/stats").catch(() => ({ data: null }))
      ])

      let allMessages = messagesResponse.data || []

      // Add welcome message if user just joined and has no messages
      if (allMessages.length === 0 && user) {
        const welcomeMessage: InboxMessage = {
          id: 0,
          user_id: user.id || 0,
          sender_name: "Agent47",
          sender_type: "system",
          sender_id: "system",
          title: `Welcome to Agent47, ${user.username || user.email.split('@')[0]}!`,
          content: `Hello ${user.username || user.email.split('@')[0]}! 👋\n\nWelcome to Agent47, your AI-powered workforce platform. We're excited to have you on board!\n\nHere's what you can do:\n• Select and onboard your AI employees\n• Connect to your favorite platforms and tools\n• Automate your workflows\n• Track your activity and history\n\nGet started by exploring the Personnel tab and selecting the employees that best fit your needs. If you have any questions, check out our documentation or contact support.\n\nHappy automating!`,
          message_type: "welcome",
          priority: "high",
          status: "unread",
          metadata: {},
          created_at: new Date().toISOString(),
          actions: []
        }
        allMessages = [welcomeMessage, ...allMessages]
      }

      setMessages(allMessages)
      setInboxStats(statsResponse.data)
      setLastUpdated(new Date())

    } catch (error) {
      console.error("Failed to load inbox data:", error)
      const errorMessage = error instanceof Error ? error.message : "Failed to load inbox messages"
      setError(errorMessage)
      // Set empty data when API is not available
      setMessages([])
      setInboxStats(null)
      setLastUpdated(new Date())
    } finally {
      setIsLoading(false)
      setIsRefreshing(false)
    }
  }

  const loadInboxSettings = async () => {
    try {
      const response = await apiClient.get("/api/inbox/settings").catch(() => ({ data: null }))
      setInboxSettings(response.data)
    } catch (error) {
      console.error("Failed to load inbox settings:", error)
    }
  }

  const handleMarkAsRead = async (messageId: number) => {
    try {
      await apiClient.put(`/api/inbox/messages/${messageId}/read`)
      await loadInboxData()
    } catch (error) {
      console.error("Failed to mark message as read:", error)
    }
  }

  const handleMarkAsUnread = async (messageId: number) => {
    try {
      await apiClient.put(`/api/inbox/messages/${messageId}/unread`)
      await loadInboxData()
    } catch (error) {
      console.error("Failed to mark message as unread:", error)
    }
  }

  const handleArchiveMessage = async (messageId: number) => {
    try {
      await apiClient.put(`/api/inbox/messages/${messageId}/archive`)
      await loadInboxData()
    } catch (error) {
      console.error("Failed to archive message:", error)
    }
  }

  const handleDeleteMessage = async (messageId: number) => {
    try {
      await apiClient.delete(`/api/inbox/messages/${messageId}`)
      await loadInboxData()
    } catch (error) {
      console.error("Failed to delete message:", error)
    }
  }

  const handleExecuteAction = async (messageId: number, action: InboxAction) => {
    try {
      await apiClient.post(`/api/inbox/messages/${messageId}/actions/${action.id}`, action.data)
      await loadInboxData()
    } catch (error) {
      console.error("Failed to execute action:", error)
    }
  }

  const handleUpdateSettings = async (settings: InboxSettings) => {
    try {
      await apiClient.put("/api/inbox/settings", settings)
      setInboxSettings(settings)
      setShowSettingsDialog(false)
    } catch (error) {
      console.error("Failed to update inbox settings:", error)
    }
  }

  const getMessageTypeIcon = (type: string) => {
    switch (type) {
      case "system": return <Settings className="h-4 w-4" />
      case "notification": return <Bell className="h-4 w-4" />
      case "update": return <Info className="h-4 w-4" />
      case "alert": return <AlertCircle className="h-4 w-4" />
      case "success": return <CheckCircle className="h-4 w-4" />
      case "task": return <Target className="h-4 w-4" />
      case "analytics": return <BarChart3 className="h-4 w-4" />
      case "calendar": return <Calendar className="h-4 w-4" />
      case "team": return <Users className="h-4 w-4" />
      case "billing": return <CreditCard className="h-4 w-4" />
      default: return <Mail className="h-4 w-4" />
    }
  }

  const getMessageTypeColor = (type: string) => {
    switch (type) {
      case "system": return "bg-gray-100 text-gray-800"
      case "notification": return "bg-blue-100 text-blue-800"
      case "update": return "bg-green-100 text-green-800"
      case "alert": return "bg-red-100 text-red-800"
      case "success": return "bg-green-100 text-green-800"
      case "task": return "bg-purple-100 text-purple-800"
      case "analytics": return "bg-orange-100 text-orange-800"
      case "calendar": return "bg-blue-100 text-blue-800"
      case "team": return "bg-indigo-100 text-indigo-800"
      case "billing": return "bg-yellow-100 text-yellow-800"
      default: return "bg-gray-100 text-gray-800"
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high": return "bg-red-100 text-red-800"
      case "medium": return "bg-yellow-100 text-yellow-800"
      case "low": return "bg-green-100 text-green-800"
      default: return "bg-gray-100 text-gray-800"
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "unread": return "bg-blue-100 text-blue-800"
      case "read": return "bg-gray-100 text-gray-800"
      case "archived": return "bg-gray-100 text-gray-800"
      case "deleted": return "bg-red-100 text-red-800"
      default: return "bg-gray-100 text-gray-800"
    }
  }

  const filteredMessages = messages.filter(message => {
    const matchesSearch = (message.title?.toLowerCase() || "").includes(searchTerm.toLowerCase()) ||
      (message.content?.toLowerCase() || "").includes(searchTerm.toLowerCase())
    const matchesType = typeFilter === "all" || message.message_type === typeFilter
    const matchesPriority = priorityFilter === "all" || message.priority === priorityFilter
    const matchesStatus = statusFilter === "all" || message.status === statusFilter
    const matchesUnread = !showUnreadOnly || message.status === "unread"
    return (
      matchesSearch && matchesType && matchesPriority && matchesStatus && matchesUnread
    )
  })

  return (
    <div className="space-y-6 p-4 md:p-6">
      {/* Error Display */}
      {error && (
        <ErrorDisplay
          error={error}
          title="Failed to load inbox"
          onRetry={loadInboxData}
        />
      )}

      {/* Loading State */}
      {isLoading && !error && (
        <div className="space-y-4">
          <SkeletonList items={5} />
        </div>
      )}

      {/* Content */}
      {!isLoading && !error && (
        <>
          {/* Header */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Inbox className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Inbox</h2>
                <p className="text-gray-600">System updates, notifications, and important messages</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={loadInboxData}
                disabled={isRefreshing}
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              <Dialog open={showSettingsDialog} onOpenChange={setShowSettingsDialog}>
                <DialogTrigger asChild>
                  <Button variant="outline" size="sm">
                    <Settings className="h-4 w-4 mr-2" />
                    Settings
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Inbox Settings</DialogTitle>
                    <DialogDescription>
                      Configure your inbox preferences and notification settings.
                    </DialogDescription>
                  </DialogHeader>
                  {inboxSettings && (
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <Label htmlFor="email-notifications">Email Notifications</Label>
                        <Switch
                          id="email-notifications"
                          checked={inboxSettings.email_notifications}
                          onCheckedChange={(checked) =>
                            setInboxSettings({ ...inboxSettings, email_notifications: checked })
                          }
                        />
                      </div>
                      <div className="flex items-center justify-between">
                        <Label htmlFor="push-notifications">Push Notifications</Label>
                        <Switch
                          id="push-notifications"
                          checked={inboxSettings.push_notifications}
                          onCheckedChange={(checked) =>
                            setInboxSettings({ ...inboxSettings, push_notifications: checked })
                          }
                        />
                      </div>
                      <div>
                        <Label htmlFor="digest-frequency">Digest Frequency</Label>
                        <Select
                          value={inboxSettings.digest_frequency}
                          onValueChange={(value) =>
                            setInboxSettings({ ...inboxSettings, digest_frequency: value })
                          }
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="immediate">Immediate</SelectItem>
                            <SelectItem value="hourly">Hourly</SelectItem>
                            <SelectItem value="daily">Daily</SelectItem>
                            <SelectItem value="weekly">Weekly</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  )}
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setShowSettingsDialog(false)}>
                      Cancel
                    </Button>
                    <Button onClick={() => inboxSettings && handleUpdateSettings(inboxSettings)}>
                      Save Settings
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
              {lastUpdated && (
                <span className="text-sm text-gray-500">
                  Last updated: {lastUpdated.toLocaleTimeString()}
                </span>
              )}
            </div>
          </div>

          {/* Stats Overview */}
          {inboxStats && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center">
                    <Inbox className="h-8 w-8 text-blue-600" />
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Total Messages</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {inboxStats.total_messages}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center">
                    <Bell className="h-8 w-8 text-red-600" />
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Unread</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {inboxStats.unread_count}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center">
                    <CheckCircle className="h-8 w-8 text-green-600" />
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Read</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {inboxStats.by_status.read || 0}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center">
                    <Archive className="h-8 w-8 text-gray-600" />
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Archived</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {inboxStats.by_status.archived || 0}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Filters */}
          <Card>
            <CardContent className="p-4">
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
                <Input
                  placeholder="Search messages..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="flex-1"
                />
                <Select value={typeFilter} onValueChange={setTypeFilter}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Types</SelectItem>
                    <SelectItem value="system">System</SelectItem>
                    <SelectItem value="notification">Notification</SelectItem>
                    <SelectItem value="update">Update</SelectItem>
                    <SelectItem value="alert">Alert</SelectItem>
                    <SelectItem value="task">Task</SelectItem>
                    <SelectItem value="analytics">Analytics</SelectItem>
                    <SelectItem value="calendar">Calendar</SelectItem>
                    <SelectItem value="team">Team</SelectItem>
                    <SelectItem value="billing">Billing</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={priorityFilter} onValueChange={setPriorityFilter}>
                  <SelectTrigger className="w-full sm:w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Priorities</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="low">Low</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-full sm:w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="unread">Unread</SelectItem>
                    <SelectItem value="read">Read</SelectItem>
                    <SelectItem value="archived">Archived</SelectItem>
                  </SelectContent>
                </Select>
                <div className="flex items-center space-x-2">
                  <Switch
                    id="unread-only"
                    checked={showUnreadOnly}
                    onCheckedChange={setShowUnreadOnly}
                  />
                  <Label htmlFor="unread-only">Unread only</Label>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Messages */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Mail className="h-5 w-5" />
                <span>Messages</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {filteredMessages.length === 0 ? (
                <EmptyState
                  icon={Inbox}
                  title="No messages found"
                  description={searchTerm || typeFilter !== "all" || priorityFilter !== "all" || statusFilter !== "all" || showUnreadOnly
                    ? "Try adjusting your search or filter criteria."
                    : "Your inbox is empty. Messages from your workforce and system will appear here."}
                />
              ) : (
                <div className="space-y-4">
                  {filteredMessages.map((message) => (
                    <div key={message.id} className="border rounded-lg p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex items-start space-x-3 flex-1">
                          <div className="flex-shrink-0">
                            {getMessageTypeIcon(message.message_type)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center space-x-2 mb-1">
                              <h3 className="font-medium text-gray-900 truncate">
                                {message.title}
                              </h3>
                              <div className="flex items-center space-x-1">
                                <Badge className={getMessageTypeColor(message.message_type)}>
                                  {message.message_type}
                                </Badge>
                                <Badge className={getPriorityColor(message.priority)}>
                                  {message.priority}
                                </Badge>
                                <Badge className={getStatusColor(message.status)}>
                                  {message.status}
                                </Badge>
                              </div>
                            </div>
                            <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                              {message.content}
                            </p>
                            <div className="flex items-center space-x-4 text-xs text-gray-500">
                              <span>From: {message.sender_name}</span>
                              <span>{new Date(message.created_at).toLocaleString()}</span>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2 ml-4">
                          {message.status === "unread" ? (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleMarkAsRead(message.id)}
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                          ) : (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleMarkAsUnread(message.id)}
                            >
                              <EyeOff className="h-4 w-4" />
                            </Button>
                          )}
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setSelectedMessage(message)
                              setShowMessageDialog(true)
                            }}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleArchiveMessage(message.id)}
                          >
                            <Archive className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDeleteMessage(message.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>

                      {/* Message Actions */}
                      {message.actions && message.actions.length > 0 && (
                        <div className="mt-3 pt-3 border-t">
                          <div className="flex items-center space-x-2">
                            {message.actions.map((action) => (
                              <Button
                                key={action.id}
                                variant="outline"
                                size="sm"
                                onClick={() => handleExecuteAction(message.id, action)}
                              >
                                {action.label}
                              </Button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}

      {/* Message Detail Dialog */}
      <Dialog open={showMessageDialog} onOpenChange={setShowMessageDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{selectedMessage?.title}</DialogTitle>
            <DialogDescription>
              From: {selectedMessage?.sender_name} • {new Date(selectedMessage?.created_at || '').toLocaleString()}
            </DialogDescription>
          </DialogHeader>
          {selectedMessage && (
            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                <Badge className={getMessageTypeColor(selectedMessage.message_type)}>
                  {selectedMessage.message_type}
                </Badge>
                <Badge className={getPriorityColor(selectedMessage.priority)}>
                  {selectedMessage.priority}
                </Badge>
                <Badge className={getStatusColor(selectedMessage.status)}>
                  {selectedMessage.status}
                </Badge>
              </div>
              <div className="prose max-w-none">
                <p className="text-gray-700 whitespace-pre-wrap">
                  {selectedMessage.content}
                </p>
              </div>
              {selectedMessage.actions && selectedMessage.actions.length > 0 && (
                <div className="flex items-center space-x-2">
                  {selectedMessage.actions.map((action) => (
                    <Button
                      key={action.id}
                      variant="outline"
                      onClick={() => handleExecuteAction(selectedMessage.id, action)}
                    >
                      {action.label}
                    </Button>
                  ))}
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowMessageDialog(false)}>
              Close
            </Button>
            {selectedMessage && selectedMessage.status === "unread" && (
              <Button onClick={() => {
                handleMarkAsRead(selectedMessage.id)
                setShowMessageDialog(false)
              }}>
                Mark as Read
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
