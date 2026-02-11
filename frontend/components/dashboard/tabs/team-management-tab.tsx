"use client"

import { useState, useEffect, useCallback, useMemo } from "react"
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Users,
  UserPlus,
  Settings,
  Mail,
  Phone,
  MapPin,
  Calendar,
  Clock,
  CheckCircle,
  AlertCircle,
  Edit,
  Trash2,
  Filter,
  RefreshCw,
  Loader2,
  Plus,
  Search,
  Crown,
  Shield,
  User,
  Eye,
  EyeOff,
  MoreHorizontal,
  Activity,
  TrendingUp,
  Target,
  Award,
  Lock,
  Unlock,
  X,
  Send,
  Copy,
  ExternalLink,
  Bell,
  MessageSquare,
  BarChart3,
  Zap,
  Globe,
  Database,
  FileText,
  Image,
  Video,
  Music,
  Map,
  ShoppingCart,
  CreditCard,
  Headphones,
  Megaphone,
  FileText as FileTextIcon,
  Search as SearchIcon,
  Lightbulb,
  Zap as ZapIcon,
  Target as TargetIcon,
  MessageSquare as MessageSquareIcon,
  Calendar as CalendarIcon,
  DollarSign,
  Hash,
  Heart,
  Share2,
  Bookmark,
  Filter as FilterIcon,
  Download,
  Upload,
  Mic,
  MicOff,
  Send as SendIcon,
  Sparkles,
  Crown as CrownIcon,
  Lock as LockIcon,
  Unlock as UnlockIcon,
  Wifi,
  WifiOff,
  AlertTriangle,
  Info,
  TrendingDown,
  ArrowUp,
  ArrowDown,
  Minus,
  Plus as PlusIcon,
  ChevronDown,
  Edit as EditIcon,
  Copy as CopyIcon,
  Trash2 as Trash2Icon,
  MoreHorizontal as MoreHorizontalIcon,
  ExternalLink as ExternalLinkIcon,
  Link,
  ImageIcon,
  Video as VideoIcon,
  FileText as FileTextIconIcon,
  Music as MusicIcon,
  Map as MapIcon,
  ShoppingCart as ShoppingCartIcon,
  CreditCard as CreditCardIcon,
  Mail as MailIcon,
  Phone as PhoneIcon,
  MapPin as MapPinIcon,
  Globe2,
  Monitor,
  Smartphone,
  Tablet,
  Laptop,
  Headphones as HeadphonesIcon,
  Megaphone as MegaphoneIcon,
} from "lucide-react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import TeamChatTab from "./chat-tab"
import { apiClient } from "@/lib/api-client"
import { useAuthStore } from "@/lib/stores/auth-store"
import { useUserStore } from "@/lib/stores/user-store"
import { useToast } from "@/hooks/use-toast"
import { Checkbox } from "@/components/ui/checkbox"

interface TeamMember {
  id: number
  user_id: number
  email: string
  name: string
  role: string
  status: string
  joined_at: string
  last_active: string
  tasks_completed: number
  tasks_assigned: number
  performance_score: number
  permissions: string[]
  avatar_url?: string
  phone?: string
  department?: string
  manager_id?: number
  is_active: boolean
  created_at: string
  updated_at: string
}

interface TeamInvitation {
  id: number
  email: string
  role: string
  status: string
  invited_by: number
  invited_at: string
  expires_at: string
  token: string
  message?: string
}

interface TeamStats {
  total_members: number
  active_members: number
  pending_invitations: number
  total_tasks: number
  completed_tasks: number
  average_performance: number
  by_role: Record<string, number>
  by_status: Record<string, number>
}

interface Task {
  id: number
  title: string
  description: string
  assigned_to: number
  assigned_by: number
  status: string
  priority: string
  due_date: string
  created_at: string
  completed_at?: string
  estimated_hours: number
  actual_hours?: number
  tags: string[]
  metadata: Record<string, any>
}

export default function TeamManagementTab() {
  const { user } = useAuthStore()
  const { userPlan } = useUserStore()

  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([])
  const [teamInvitations, setTeamInvitations] = useState<TeamInvitation[]>([])
  const [teamStats, setTeamStats] = useState<TeamStats | null>(null)
  const [teamTasks, setTeamTasks] = useState<Task[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  // Dialog states
  const [showInviteDialog, setShowInviteDialog] = useState(false)
  const [showEditDialog, setShowEditDialog] = useState(false)
  const [selectedMember, setSelectedMember] = useState<TeamMember | null>(null)

  // Form states
  const [inviteEmail, setInviteEmail] = useState("")
  const [inviteRole, setInviteRole] = useState("member")
  const [inviteMessage, setInviteMessage] = useState("")
  const [isInviting, setIsInviting] = useState(false)

  // Search and filter states
  const [searchTerm, setSearchTerm] = useState("")
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState("")
  const [roleFilter, setRoleFilter] = useState("all")
  const [statusFilter, setStatusFilter] = useState("all")

  // Bulk selection states
  const [selectedMembers, setSelectedMembers] = useState<number[]>([])
  const [isSelecting, setIsSelecting] = useState(false)

  const { toast } = useToast()

  // Debounce search term
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm)
    }, 300)
    return () => clearTimeout(timer)
  }, [searchTerm])

  // Get tier limits
  const getTierLimits = () => {
    switch (userPlan) {
      case "free":
        return { maxMembers: 0, maxTasks: 0 }
      case "starter":
        return { maxMembers: 7, maxTasks: 50 }
      case "pro":
        return { maxMembers: 14, maxTasks: 100 }
      default:
        return { maxMembers: 0, maxTasks: 0 }
    }
  }

  const tierLimits = getTierLimits()
  const canInviteMembers = userPlan !== "free" && teamMembers.length < tierLimits.maxMembers

  // Load data on mount
  useEffect(() => {
    if (userPlan !== "free") {
      loadTeamData()
    } else {
      setIsLoading(false)
    }
  }, [userPlan])

  const loadTeamData = async () => {
    try {
      setIsLoading(true)
      setIsRefreshing(true)

      // Load team data in parallel
      const [membersResponse, invitationsResponse, statsResponse, tasksResponse] = await Promise.all([
        apiClient.get("/api/team/members").catch(() => ({ data: [] })),
        apiClient.get("/api/team/invitations").catch(() => ({ data: [] })),
        apiClient.get("/api/team/stats").catch(() => ({ data: null })),
        apiClient.get("/api/team/tasks").catch(() => ({ data: [] }))
      ])

      setTeamMembers(membersResponse.data || [])
      setTeamInvitations(invitationsResponse.data || [])
      setTeamStats(statsResponse.data)
      setTeamTasks(tasksResponse.data || [])
      setLastUpdated(new Date())

    } catch (error) {
      console.error("Failed to load team data:", error)
      // Set empty data when API is not available
      setTeamMembers([])
      setTeamInvitations([])
      setTeamStats(null)
      setTeamTasks([])
      setLastUpdated(new Date())
    } finally {
      setIsLoading(false)
      setIsRefreshing(false)
    }
  }

  const handleInviteMember = async () => {
    if (!inviteEmail || !canInviteMembers) return

    try {
      setIsInviting(true)
      await apiClient.post("/api/team/invite", {
        email: inviteEmail,
        role: inviteRole,
        message: inviteMessage
      })

      toast({
        title: "Invitation sent",
        description: `Invitation sent to ${inviteEmail}`,
      })

      // Reset form
      setInviteEmail("")
      setInviteRole("member")
      setInviteMessage("")
      setShowInviteDialog(false)

      // Reload data
      await loadTeamData()
    } catch (error) {
      console.error("Failed to invite member:", error)
      toast({
        title: "Error",
        description: "Failed to send invitation. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsInviting(false)
    }
  }

  const handleRemoveMember = async (memberId: number) => {
    try {
      await apiClient.delete(`/api/team/members/${memberId}`)
      await loadTeamData()
    } catch (error) {
      console.error("Failed to remove member:", error)
    }
  }

  const handleUpdateMemberRole = async (memberId: number, newRole: string) => {
    try {
      await apiClient.put(`/api/team/members/${memberId}`, { role: newRole })
      await loadTeamData()
    } catch (error) {
      console.error("Failed to update member role:", error)
    }
  }

  const handleCancelInvitation = async (invitationId: number) => {
    try {
      await apiClient.delete(`/api/team/invitations/${invitationId}`)
      await loadTeamData()
    } catch (error) {
      console.error("Failed to cancel invitation:", error)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active": return "bg-green-100 text-green-800"
      case "pending": return "bg-yellow-100 text-yellow-800"
      case "inactive": return "bg-gray-100 text-gray-800"
      case "suspended": return "bg-red-100 text-red-800"
      default: return "bg-gray-100 text-gray-800"
    }
  }

  const getRoleColor = (role: string) => {
    switch (role) {
      case "admin": return "bg-green-100 text-green-800"
      case "manager": return "bg-green-100 text-green-800"
      case "member": return "bg-green-100 text-green-800"
      case "viewer": return "bg-gray-100 text-gray-800"
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

  const filteredMembers = useMemo(() => {
    return teamMembers.filter(member => {
      const matchesSearch = member.name.toLowerCase().includes(debouncedSearchTerm.toLowerCase()) ||
        member.email.toLowerCase().includes(debouncedSearchTerm.toLowerCase())
      const matchesRole = roleFilter === "all" || member.role === roleFilter
      const matchesStatus = statusFilter === "all" || member.status === statusFilter
      return matchesSearch && matchesRole && matchesStatus
    })
  }, [teamMembers, debouncedSearchTerm, roleFilter, statusFilter])

  const handleSelectMember = (memberId: number) => {
    setSelectedMembers(prev =>
      prev.includes(memberId)
        ? prev.filter(id => id !== memberId)
        : [...prev, memberId]
    )
  }

  const handleSelectAll = () => {
    if (selectedMembers.length === filteredMembers.length) {
      setSelectedMembers([])
    } else {
      setSelectedMembers(filteredMembers.map(m => m.id))
    }
  }

  const handleBulkAction = async (action: "remove" | "activate" | "deactivate" | "changeRole", role?: string) => {
    if (selectedMembers.length === 0) {
      toast({
        title: "No selection",
        description: "Please select at least one member",
        variant: "destructive",
      })
      return
    }

    try {
      const promises = selectedMembers.map(memberId => {
        switch (action) {
          case "remove":
            return apiClient.delete(`/api/team/members/${memberId}`)
          case "activate":
            return apiClient.put(`/api/team/members/${memberId}`, { status: "active" })
          case "deactivate":
            return apiClient.put(`/api/team/members/${memberId}`, { status: "inactive" })
          case "changeRole":
            if (role) {
              return apiClient.put(`/api/team/members/${memberId}`, { role })
            }
            return Promise.resolve()
          default:
            return Promise.resolve()
        }
      })

      await Promise.all(promises)

      toast({
        title: "Success",
        description: `${selectedMembers.length} member(s) updated successfully`,
      })

      setSelectedMembers([])
      setIsSelecting(false)
      await loadTeamData()
    } catch (error) {
      console.error("Failed to perform bulk action:", error)
      toast({
        title: "Error",
        description: "Failed to update members. Please try again.",
        variant: "destructive",
      })
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center space-x-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span>Loading team data...</span>
        </div>
      </div>
    )
  }

  // Free tier users can't access team management
  if (userPlan === "free") {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <Users className="h-6 w-6 text-green-600" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Team Management</h2>
              <p className="text-gray-600">Collaborate with your team members</p>
            </div>
          </div>
        </div>

        <Card>
          <CardContent className="p-12 text-center">
            <Lock className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Team Management Not Available</h3>
            <p className="text-gray-600 mb-6">
              Team management features are not available on the free plan. Upgrade to Starter or Pro to invite team members and collaborate.
            </p>
            <div className="space-y-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-2">Starter Plan</h4>
                <p className="text-sm text-gray-600">Up to 7 team members, 50 tasks per month</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-2">Pro Plan</h4>
                <p className="text-sm text-gray-600">Up to 14 team members, 100 tasks per month</p>
              </div>
            </div>
            <Button className="mt-6" onClick={() => window.location.href = '/pricing'}>
              <Crown className="h-4 w-4 mr-2" />
              Upgrade Plan
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <Users className="h-6 w-6 text-blue-600" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Team Management</h2>
            <p className="text-gray-600">Manage your team members and collaborate effectively</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadTeamData}
            disabled={isRefreshing}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          {canInviteMembers && (
            <Dialog open={showInviteDialog} onOpenChange={setShowInviteDialog}>
              <DialogTrigger asChild>
                <Button>
                  <UserPlus className="h-4 w-4 mr-2" />
                  Invite Member
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Invite Team Member</DialogTitle>
                  <DialogDescription>
                    Send an invitation to join your team. You can invite up to {tierLimits.maxMembers} members on your {userPlan} plan.
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="email">Email Address</Label>
                    <Input
                      id="email"
                      type="email"
                      value={inviteEmail}
                      onChange={(e) => setInviteEmail(e.target.value)}
                      placeholder="colleague@company.com"
                    />
                  </div>
                  <div>
                    <Label htmlFor="role">Role</Label>
                    <Select value={inviteRole} onValueChange={setInviteRole}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="member">Member</SelectItem>
                        <SelectItem value="manager">Manager</SelectItem>
                        <SelectItem value="admin">Admin</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="message">Message (Optional)</Label>
                    <Textarea
                      id="message"
                      value={inviteMessage}
                      onChange={(e) => setInviteMessage(e.target.value)}
                      placeholder="Welcome to our team!"
                      rows={3}
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setShowInviteDialog(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleInviteMember} disabled={isInviting || !inviteEmail}>
                    {isInviting ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <Send className="h-4 w-4 mr-2" />
                    )}
                    Send Invitation
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          )}
          {lastUpdated && (
            <span className="text-sm text-gray-500">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      {/* Tabs for Members and Chat */}
      <Tabs defaultValue="members" className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="members" className="flex items-center space-x-2">
            <Users className="h-4 w-4" />
            <span>Members</span>
          </TabsTrigger>
          <TabsTrigger value="chat" className="flex items-center space-x-2">
            <MessageSquare className="h-4 w-4" />
            <span>Team Chat</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="members" className="space-y-6 mt-6">
          {/* Stats Overview */}
          {teamStats && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center">
                    <Users className="h-8 w-8 text-green-600" />
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Team Members</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {teamStats.total_members}/{tierLimits.maxMembers}
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
                      <p className="text-sm font-medium text-gray-600">Active Members</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {teamStats.active_members}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center">
                    <Clock className="h-8 w-8 text-yellow-600" />
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Pending Invitations</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {teamStats.pending_invitations}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center">
                    <Target className="h-8 w-8 text-green-600" />
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Completed Tasks</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {teamStats.completed_tasks}/{teamStats.total_tasks}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Pending Invitations */}
          {teamInvitations.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Mail className="h-5 w-5" />
                  <span>Pending Invitations</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {teamInvitations.map((invitation) => (
                    <div key={invitation.id} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <Avatar>
                            <AvatarFallback>
                              {invitation.email.charAt(0).toUpperCase()}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <p className="font-medium">{invitation.email}</p>
                            <p className="text-sm text-gray-600">
                              Role: {invitation.role} • Invited {new Date(invitation.invited_at).toLocaleDateString()}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Badge className={getStatusColor(invitation.status)}>
                            {invitation.status}
                          </Badge>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleCancelInvitation(invitation.id)}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                      {invitation.message && (
                        <p className="text-sm text-gray-600 mt-2">{invitation.message}</p>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Team Members */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center space-x-2">
                  {isSelecting && (
                    <Checkbox
                      checked={selectedMembers.length === filteredMembers.length && filteredMembers.length > 0}
                      onCheckedChange={handleSelectAll}
                      className="mr-2"
                    />
                  )}
                  <Users className="h-5 w-5" />
                  <span>Team Members</span>
                  {selectedMembers.length > 0 && (
                    <Badge variant="secondary" className="ml-2">
                      {selectedMembers.length} selected
                    </Badge>
                  )}
                </CardTitle>
                <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:space-x-2 w-full sm:w-auto">
                  <Input
                    placeholder="Search members..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full sm:w-48 lg:w-64"
                  />
                  <div className="flex gap-2">
                    <Select value={roleFilter} onValueChange={setRoleFilter}>
                      <SelectTrigger className="w-full sm:w-28 lg:w-32">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Roles</SelectItem>
                        <SelectItem value="admin">Admin</SelectItem>
                        <SelectItem value="manager">Manager</SelectItem>
                        <SelectItem value="member">Member</SelectItem>
                        <SelectItem value="viewer">Viewer</SelectItem>
                      </SelectContent>
                    </Select>
                    <Select value={statusFilter} onValueChange={setStatusFilter}>
                      <SelectTrigger className="w-full sm:w-28 lg:w-32">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Status</SelectItem>
                        <SelectItem value="active">Active</SelectItem>
                        <SelectItem value="inactive">Inactive</SelectItem>
                        <SelectItem value="pending">Pending</SelectItem>
                      </SelectContent>
                    </Select>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setIsSelecting(!isSelecting)
                        setSelectedMembers([])
                      }}
                      className="whitespace-nowrap"
                    >
                      {isSelecting ? "Cancel" : "Select"}
                    </Button>
                  </div>
                </div>
              </div>
              {isSelecting && selectedMembers.length > 0 && (
                <div className="mt-4 flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-2 p-3 bg-green-50 rounded-lg">
                  <span className="text-sm font-medium">
                    {selectedMembers.length} member(s) selected
                  </span>
                  <div className="flex flex-wrap gap-2 sm:ml-auto">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleBulkAction("activate")}
                      className="flex-1 sm:flex-initial"
                    >
                      Activate
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleBulkAction("deactivate")}
                      className="flex-1 sm:flex-initial"
                    >
                      Deactivate
                    </Button>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button size="sm" variant="outline" className="flex-1 sm:flex-initial">
                          <span className="hidden sm:inline">Change Role</span>
                          <span className="sm:hidden">Role</span>
                          <ChevronDown className="w-4 h-4 ml-2" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent>
                        <DropdownMenuItem onClick={() => handleBulkAction("changeRole", "member")}>
                          Member
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleBulkAction("changeRole", "manager")}>
                          Manager
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleBulkAction("changeRole", "admin")}>
                          Admin
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => handleBulkAction("remove")}
                      className="flex-1 sm:flex-initial"
                    >
                      <Trash2 className="w-4 h-4 sm:mr-2" />
                      <span className="hidden sm:inline">Remove</span>
                    </Button>
                  </div>
                </div>
              )}
            </CardHeader>
            <CardContent>
              {filteredMembers.length > 0 ? (
                <div className="space-y-4">
                  {filteredMembers.map((member) => (
                    <div key={member.id} className={`border rounded-lg p-4 ${selectedMembers.includes(member.id) ? 'bg-green-50 border-green-300' : ''}`}>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          {isSelecting && (
                            <Checkbox
                              checked={selectedMembers.includes(member.id)}
                              onCheckedChange={() => handleSelectMember(member.id)}
                            />
                          )}
                          <Avatar>
                            <AvatarImage src={member.avatar_url} />
                            <AvatarFallback>
                              {member.name.charAt(0).toUpperCase()}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <p className="font-medium">{member.name}</p>
                            <p className="text-sm text-gray-600">{member.email}</p>
                            <div className="flex items-center space-x-2 mt-1">
                              <Badge className={getRoleColor(member.role)}>
                                {member.role}
                              </Badge>
                              <Badge className={getStatusColor(member.status)}>
                                {member.status}
                              </Badge>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center space-x-4">
                          <div className="text-right text-sm">
                            <p className="text-gray-600">Tasks Completed</p>
                            <p className="font-medium">{member.tasks_completed}</p>
                          </div>
                          <div className="text-right text-sm">
                            <p className="text-gray-600">Performance</p>
                            <p className="font-medium">{member.performance_score}%</p>
                          </div>
                          <div className="flex items-center space-x-2">
                            <Select
                              value={member.role}
                              onValueChange={(newRole) => handleUpdateMemberRole(member.id, newRole)}
                            >
                              <SelectTrigger className="w-24">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="member">Member</SelectItem>
                                <SelectItem value="manager">Manager</SelectItem>
                                <SelectItem value="admin">Admin</SelectItem>
                              </SelectContent>
                            </Select>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleRemoveMember(member.id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      </div>
                      <div className="mt-3 text-sm text-gray-600">
                        <p>Joined: {new Date(member.joined_at).toLocaleDateString()}</p>
                        <p>Last active: {new Date(member.last_active).toLocaleDateString()}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">No team members found</p>
                  <p className="text-sm text-gray-500">
                    {searchTerm ? "Try adjusting your search criteria" : "Invite team members to get started"}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Team Tasks */}
          {teamTasks.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Target className="h-5 w-5" />
                  <span>Recent Team Tasks</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {teamTasks.slice(0, 5).map((task) => {
                    const assignee = teamMembers.find(member => member.id === task.assigned_to)
                    return (
                      <div key={task.id} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="font-medium">{task.title}</h3>
                          <div className="flex items-center space-x-2">
                            <Badge className={getPriorityColor(task.priority)}>
                              {task.priority}
                            </Badge>
                            <Badge className={getStatusColor(task.status)}>
                              {task.status}
                            </Badge>
                          </div>
                        </div>
                        <p className="text-sm text-gray-600 mb-2">{task.description}</p>
                        <div className="flex items-center justify-between text-sm text-gray-500">
                          <span>Assigned to: {assignee?.name || "Unknown"}</span>
                          <span>Due: {new Date(task.due_date).toLocaleDateString()}</span>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="chat" className="mt-6">
          <div className="h-[calc(100vh-300px)] min-h-[600px]">
            <TeamChatTab />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
