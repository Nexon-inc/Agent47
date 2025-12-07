"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { 
  Users, 
  UserPlus,
  Search,
  Filter,
  Eye,
  Edit,
  Trash2,
  Shield,
  Mail,
  Calendar,
  Activity,
  RefreshCw,
  AlertCircle,
  X,
  Key,
  UserCheck,
  CreditCard,
  Clock,
  Globe,
  Phone,
  MapPin,
  Info,
  CheckCircle,
  XCircle
} from "lucide-react"
import AdminLayout from "@/components/admin/layout"
import { useAdminStore } from "@/lib/stores/admin-store"
import { adminAPI } from "@/lib/services/admin-api"
import { usePolling } from "@/lib/hooks/use-polling"

interface User {
  id: string
  user_id?: string
  email: string
  username?: string
  full_name?: string
  hashed_password?: string
  is_active: boolean
  is_verified: boolean
  tier?: string
  status?: string
  created_at: string
  last_login?: string
  website_url?: string
  phone?: string
  address?: string
  city?: string
  country?: string
  onboarding_completed?: boolean
  onboarding_step?: string
  is_admin?: boolean
  admin_permissions?: string[]
  profile?: any
  subscription?: any
  activities?: any[]
  errors?: any[]
  suspension_info?: any
}

export default function AdminUsersPage() {
  const [users, setUsers] = useState<User[]>([])
  const [adminUsers, setAdminUsers] = useState<string[]>([])
  const [searchQuery, setSearchQuery] = useState("")
  const [filterRole, setFilterRole] = useState("all")
  const [filterStatus, setFilterStatus] = useState("all")
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [userDetails, setUserDetails] = useState<any>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDetailsModal, setShowDetailsModal] = useState(false)
  const [isLoadingDetails, setIsLoadingDetails] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const { currentAdmin } = useAdminStore()

  const [usersData, setUsersData] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [usersError, setUsersError] = useState<any>(null)

  // Load initial data
  useEffect(() => {
    if (!currentAdmin) return
    
    const loadUsers = async () => {
      try {
        setIsLoading(true)
        const data = await adminAPI.getUsers(1, 200)
        setUsersData(data)
      } catch (err) {
        setUsersError(err)
      } finally {
        setIsLoading(false)
      }
    }
    loadUsers()
  }, [currentAdmin])

  // Subscribe to real-time user updates via WebSocket
  useEffect(() => {
    if (!currentAdmin) return

    const { websocketService } = require('@/lib/websocket-service')
    
    if (!websocketService.getConnectionStatus()) {
      websocketService.connect()
    }

    // Reload users when notifications indicate user changes
    const unsubscribe = websocketService.subscribe('notification', (message) => {
      if (message.data?.type === 'system_update' || message.data?.type === 'security_alert') {
        adminAPI.getUsers(1, 200).then(setUsersData).catch(setUsersError)
      }
    })

    return () => unsubscribe()
  }, [currentAdmin])

  const refetch = async () => {
    try {
      setIsLoading(true)
      const data = await adminAPI.getUsers(1, 200)
      setUsersData(data)
    } catch (err) {
      setUsersError(err)
    } finally {
      setIsLoading(false)
    }
  }

  // Fetch admin users list
  useEffect(() => {
    const fetchAdminUsers = async () => {
      try {
        const response = await adminAPI.getAdminUsers()
        if (response && response.admins) {
          const adminIds = response.admins.map((admin: any) => admin.user_id)
          setAdminUsers(adminIds)
        }
      } catch (err) {
        console.error("Failed to fetch admin users:", err)
      }
    }
    if (currentAdmin) {
      fetchAdminUsers()
    }
  }, [currentAdmin])

  useEffect(() => {
    if (usersData) {
      const usersList = usersData.users || usersData || []
      setUsers(usersList)
    }
    if (usersError) {
      setError(usersError.message || "Failed to load users")
    }
  }, [usersData, usersError])

  const fetchUserDetails = async (userId: string) => {
    setIsLoadingDetails(true)
    try {
      const details = await adminAPI.getUser(userId)
      setUserDetails(details)
      setShowDetailsModal(true)
    } catch (err) {
      alert(`Failed to load user details: ${err instanceof Error ? err.message : 'Unknown error'}`)
    } finally {
      setIsLoadingDetails(false)
    }
  }

  const filteredUsers = users.filter(user => {
    const userId = user.id || user.user_id || ""
    const isAdmin = adminUsers.includes(userId)
    
    const matchesSearch = !searchQuery || 
                         user.email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         user.username?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         user.full_name?.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesRole = filterRole === "all" || 
                       (filterRole === "admin" && isAdmin) ||
                       (filterRole === "user" && !isAdmin)
    const matchesStatus = filterStatus === "all" || 
                        (filterStatus === "active" && user.is_active) ||
                        (filterStatus === "inactive" && !user.is_active) ||
                        (filterStatus === "suspended" && user.status === "suspended")
    
    return matchesSearch && matchesRole && matchesStatus
  })

  const getTierColor = (tier: string) => {
    switch (tier?.toLowerCase()) {
      case 'enterprise': return 'bg-purple-900/50 text-purple-300 border-purple-700'
      case 'pro': return 'bg-blue-900/50 text-blue-300 border-blue-700'
      case 'starter': return 'bg-green-900/50 text-green-300 border-green-700'
      case 'free': return 'bg-gray-800 text-gray-300 border-gray-700'
      default: return 'bg-gray-800 text-gray-300 border-gray-700'
    }
  }

  const getStatusColor = (isActive: boolean, status?: string) => {
    if (status === "suspended") return 'bg-red-900/50 text-red-300 border-red-700'
    if (isActive) return 'bg-green-900/50 text-green-300 border-green-700'
    return 'bg-gray-800 text-gray-300 border-gray-700'
  }

  const handleCreateUser = () => {
    setShowCreateModal(true)
  }

  const handleViewDetails = async (user: User) => {
    setSelectedUser(user)
    await fetchUserDetails(user.id || user.user_id || "")
  }

  const handleEditUser = (user: User) => {
    setSelectedUser(user)
    setShowEditModal(true)
  }

  const handleDeleteUser = (userId: string) => {
    if (confirm('Are you sure you want to delete this user?')) {
      setUsers(prev => prev.filter(user => (user.id || user.user_id) !== userId))
    }
  }

  if (!currentAdmin) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Users className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-white">Access Denied</h3>
            <p className="mt-1 text-sm text-gray-500">
              You don't have permission to access user management.
            </p>
          </div>
        </div>
      </AdminLayout>
    )
  }

  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">User Management</h1>
            <p className="text-gray-400">Manage users, view credentials, and monitor activity</p>
          </div>
          <div className="flex gap-2">
            <Button 
              onClick={() => refetch()} 
              disabled={isLoading}
              className="bg-gray-800 hover:bg-gray-700"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button onClick={handleCreateUser} className="bg-green-600 hover:bg-green-700">
              <UserPlus className="h-4 w-4 mr-2" />
              Create User
            </Button>
          </div>
        </div>

        {error && (
          <div className="bg-red-900/20 border border-red-800 text-red-400 px-4 py-3 rounded-lg flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card className="bg-gray-900/50 border-gray-800 p-6 hover:border-green-500/50 transition-colors">
            <div className="flex items-center justify-between mb-4">
              <Users className="w-8 h-8 text-green-500" />
              <span className="text-sm text-gray-400">Total</span>
            </div>
            <div className="text-3xl font-bold text-white">{users.length}</div>
            <div className="text-sm text-gray-400 mt-2">Total users</div>
          </Card>
          
          <Card className="bg-gray-900/50 border-gray-800 p-6 hover:border-green-500/50 transition-colors">
            <div className="flex items-center justify-between mb-4">
              <Activity className="w-8 h-8 text-green-500" />
              <span className="text-sm text-gray-400">Active</span>
            </div>
            <div className="text-3xl font-bold text-white">
              {users.filter(u => u.is_active).length}
            </div>
            <div className="text-sm text-gray-400 mt-2">Active users</div>
          </Card>
          
          <Card className="bg-gray-900/50 border-gray-800 p-6 hover:border-red-500/50 transition-colors">
            <div className="flex items-center justify-between mb-4">
              <Shield className="w-8 h-8 text-red-500" />
              <span className="text-sm text-gray-400">Admins</span>
            </div>
            <div className="text-3xl font-bold text-white">
              {users.filter(u => adminUsers.includes(u.id || u.user_id || "")).length}
            </div>
            <div className="text-sm text-gray-400 mt-2">Admin users</div>
          </Card>
          
          <Card className="bg-gray-900/50 border-gray-800 p-6 hover:border-blue-500/50 transition-colors">
            <div className="flex items-center justify-between mb-4">
              <CreditCard className="w-8 h-8 text-blue-500" />
              <span className="text-sm text-gray-400">Tiers</span>
            </div>
            <div className="text-3xl font-bold text-white">
              {new Set(users.map(u => u.tier || "free")).size}
            </div>
            <div className="text-sm text-gray-400 mt-2">Active tiers</div>
          </Card>
        </div>

        {/* Filters */}
        <Card className="bg-gray-900/50 border-gray-800">
          <CardHeader>
            <CardTitle className="text-white">Users</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col sm:flex-row gap-4 mb-6">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                  <Input
                    placeholder="Search users..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 bg-gray-800 border-gray-700 text-white"
                  />
                </div>
              </div>
              <div className="flex gap-2">
                <select
                  value={filterRole}
                  onChange={(e) => setFilterRole(e.target.value)}
                  className="px-3 py-2 border border-gray-700 rounded-md text-sm bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-green-500"
                >
                  <option value="all">All Users</option>
                  <option value="admin">Admins</option>
                  <option value="user">Regular Users</option>
                </select>
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="px-3 py-2 border border-gray-700 rounded-md text-sm bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-green-500"
                >
                  <option value="all">All Status</option>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                  <option value="suspended">Suspended</option>
                </select>
              </div>
            </div>

            {/* Users List */}
            {isLoading && users.length === 0 ? (
              <div className="flex items-center justify-center h-32">
                <RefreshCw className="h-8 w-8 text-gray-400 animate-spin" />
              </div>
            ) : filteredUsers.length === 0 ? (
              <div className="text-center py-12">
                <Users className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-300 mb-2">No users found</h3>
                <p className="text-gray-500">No users match your search criteria</p>
              </div>
            ) : (
              <div className="space-y-4">
                {filteredUsers.map((user) => {
                  const userId = user.id || user.user_id || ""
                  const isAdmin = adminUsers.includes(userId)
                  return (
                    <div key={userId} className="flex items-center justify-between p-4 border border-gray-800 rounded-lg bg-gray-800/50 hover:bg-gray-800 transition-colors">
                      <div className="flex items-center space-x-4">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${isAdmin ? 'bg-red-500/20' : 'bg-green-500/20'}`}>
                          {isAdmin ? (
                            <Shield className="h-5 w-5 text-red-500" />
                          ) : (
                            <Users className="h-5 w-5 text-green-500" />
                          )}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="font-medium text-white">
                              {user.full_name || user.username || user.email.split("@")[0]}
                            </h3>
                            {isAdmin && (
                              <Badge className="bg-red-900/50 text-red-300 border-red-700">
                                Admin
                              </Badge>
                            )}
                          </div>
                          <p className="text-sm text-gray-400">{user.email}</p>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge className={getTierColor(user.tier || "free")}>
                              {user.tier || "free"}
                            </Badge>
                            <Badge className={getStatusColor(user.is_active, user.status)}>
                              {user.status || (user.is_active ? "active" : "inactive")}
                            </Badge>
                            {user.is_verified && (
                              <Badge className="bg-blue-900/50 text-blue-300 border-blue-700">
                                Verified
                              </Badge>
                            )}
                            {user.onboarding_completed && (
                              <Badge className="bg-green-900/50 text-green-300 border-green-700">
                                Onboarded
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="text-right mr-4">
                          <p className="text-sm text-gray-500">
                            {user.last_login ? `Last login: ${new Date(user.last_login).toLocaleString()}` : "Never logged in"}
                          </p>
                          <p className="text-sm text-gray-500">
                            Created: {new Date(user.created_at).toLocaleString()}
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => handleViewDetails(user)}
                            disabled={isLoadingDetails}
                            className="border-gray-700 hover:bg-gray-700"
                          >
                            <Eye className="h-4 w-4 mr-1" />
                            Details
                          </Button>
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => handleEditUser(user)}
                            className="border-gray-700 hover:bg-gray-700"
                          >
                            <Edit className="h-4 w-4 mr-1" />
                            Edit
                          </Button>
                          {!isAdmin && (
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={() => handleDeleteUser(userId)}
                              className="border-red-700 hover:bg-red-900/20 text-red-400"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Create User Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <Card className="w-full max-w-md bg-gray-900 border-gray-800">
              <CardHeader>
                <CardTitle className="text-white">Create New User</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Name
                    </label>
                    <Input placeholder="Enter full name" className="bg-gray-800 border-gray-700 text-white" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Email
                    </label>
                    <Input type="email" placeholder="Enter email address" className="bg-gray-800 border-gray-700 text-white" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Role
                    </label>
                    <select className="w-full px-3 py-2 border border-gray-700 rounded-md text-sm bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-green-500">
                      <option value="admin">Admin</option>
                      <option value="moderator">Moderator</option>
                      <option value="support">Support</option>
                    </select>
                  </div>
                  <div className="flex gap-2">
                    <Button 
                      className="flex-1"
                      onClick={() => setShowCreateModal(false)}
                    >
                      Create User
                    </Button>
                    <Button 
                      variant="outline" 
                      className="flex-1"
                      onClick={() => setShowCreateModal(false)}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* User Details Modal */}
        {showDetailsModal && selectedUser && userDetails && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <Card className="w-full max-w-4xl bg-gray-900 border-gray-800 max-h-[90vh] overflow-y-auto">
              <CardHeader className="flex items-center justify-between border-b border-gray-800">
                <CardTitle className="text-white flex items-center gap-2">
                  <UserCheck className="h-5 w-5" />
                  User Details: {userDetails.email || selectedUser.email}
                </CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setShowDetailsModal(false)
                    setUserDetails(null)
                  }}
                  className="text-gray-400 hover:text-white"
                >
                  <X className="h-4 w-4" />
                </Button>
              </CardHeader>
              <CardContent className="p-6 space-y-6">
                {/* Basic Information */}
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <Info className="h-5 w-5 text-blue-500" />
                    Basic Information
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-3 bg-gray-800/50 rounded-lg border border-gray-700">
                      <p className="text-xs text-gray-400 mb-1">Email</p>
                      <p className="text-white font-medium">{userDetails.email || selectedUser.email}</p>
                    </div>
                    <div className="p-3 bg-gray-800/50 rounded-lg border border-gray-700">
                      <p className="text-xs text-gray-400 mb-1">Username</p>
                      <p className="text-white font-medium">{userDetails.username || selectedUser.username || "N/A"}</p>
                    </div>
                    <div className="p-3 bg-gray-800/50 rounded-lg border border-gray-700">
                      <p className="text-xs text-gray-400 mb-1">Full Name</p>
                      <p className="text-white font-medium">{userDetails.profile?.full_name || userDetails.full_name || selectedUser.full_name || "N/A"}</p>
                    </div>
                    <div className="p-3 bg-gray-800/50 rounded-lg border border-gray-700">
                      <p className="text-xs text-gray-400 mb-1">User ID</p>
                      <p className="text-white font-medium text-xs">{userDetails.id || selectedUser.id || selectedUser.user_id}</p>
                    </div>
                  </div>
                </div>

                {/* Credentials */}
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <Key className="h-5 w-5 text-yellow-500" />
                    Credentials
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-3 bg-gray-800/50 rounded-lg border border-gray-700">
                      <p className="text-xs text-gray-400 mb-1">Password Hash</p>
                      <p className="text-white font-mono text-xs break-all">
                        {userDetails.hashed_password || selectedUser.hashed_password || "N/A"}
                      </p>
                    </div>
                    <div className="p-3 bg-gray-800/50 rounded-lg border border-gray-700">
                      <p className="text-xs text-gray-400 mb-1">Account Status</p>
                      <div className="flex items-center gap-2">
                        {userDetails.is_active !== false ? (
                          <CheckCircle className="h-4 w-4 text-green-500" />
                        ) : (
                          <XCircle className="h-4 w-4 text-red-500" />
                        )}
                        <span className="text-white">
                          {userDetails.is_active !== false ? "Active" : "Inactive"}
                        </span>
                        {userDetails.is_verified && (
                          <Badge className="bg-blue-900/20 text-blue-400 border-blue-800">Verified</Badge>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Account Type & Tier */}
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <CreditCard className="h-5 w-5 text-purple-500" />
                    Account Type & Tier
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-3 bg-gray-800/50 rounded-lg border border-gray-700">
                      <p className="text-xs text-gray-400 mb-1">User Type</p>
                      <Badge className={adminUsers.includes(userDetails.id || selectedUser.id || "") ? "bg-red-900/50 text-red-300 border-red-700" : "bg-gray-800 text-gray-300 border-gray-700"}>
                        {adminUsers.includes(userDetails.id || selectedUser.id || "") ? "Admin" : "Regular User"}
                      </Badge>
                      {adminUsers.includes(userDetails.id || selectedUser.id || "") && userDetails.admin_permissions && (
                        <p className="text-xs text-gray-400 mt-2">
                          Permissions: {userDetails.admin_permissions.join(", ")}
                        </p>
                      )}
                    </div>
                    <div className="p-3 bg-gray-800/50 rounded-lg border border-gray-700">
                      <p className="text-xs text-gray-400 mb-1">Tier</p>
                      <Badge className={getTierColor(userDetails.tier || selectedUser.tier || "free")}>
                        {userDetails.tier || selectedUser.tier || "free"}
                      </Badge>
                      {userDetails.subscription && (
                        <p className="text-xs text-gray-400 mt-2">
                          Subscription: {userDetails.subscription.status || "N/A"}
                        </p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Onboarding Information */}
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <UserCheck className="h-5 w-5 text-green-500" />
                    Onboarding Information
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-3 bg-gray-800/50 rounded-lg border border-gray-700">
                      <p className="text-xs text-gray-400 mb-1">Onboarding Status</p>
                      <div className="flex items-center gap-2">
                        {userDetails.onboarding_completed !== false ? (
                          <CheckCircle className="h-4 w-4 text-green-500" />
                        ) : (
                          <XCircle className="h-4 w-4 text-yellow-500" />
                        )}
                        <span className="text-white">
                          {userDetails.onboarding_completed !== false ? "Completed" : "In Progress"}
                        </span>
                      </div>
                      {userDetails.onboarding_step && (
                        <p className="text-xs text-gray-400 mt-2">
                          Current Step: {userDetails.onboarding_step}
                        </p>
                      )}
                    </div>
                    <div className="p-3 bg-gray-800/50 rounded-lg border border-gray-700">
                      <p className="text-xs text-gray-400 mb-1">Account Created</p>
                      <p className="text-white">
                        {new Date(userDetails.created_at || selectedUser.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Contact Information */}
                {(userDetails.profile || selectedUser.phone || selectedUser.address) && (
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                      <Phone className="h-5 w-5 text-blue-500" />
                      Contact Information
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {userDetails.profile?.phone || selectedUser.phone ? (
                        <div className="p-3 bg-gray-800/50 rounded-lg border border-gray-700">
                          <p className="text-xs text-gray-400 mb-1">Phone</p>
                          <p className="text-white">{userDetails.profile?.phone || selectedUser.phone}</p>
                        </div>
                      ) : null}
                      {userDetails.profile?.address || selectedUser.address ? (
                        <div className="p-3 bg-gray-800/50 rounded-lg border border-gray-700">
                          <p className="text-xs text-gray-400 mb-1">Address</p>
                          <p className="text-white">{userDetails.profile?.address || selectedUser.address}</p>
                        </div>
                      ) : null}
                      {userDetails.profile?.city || selectedUser.city ? (
                        <div className="p-3 bg-gray-800/50 rounded-lg border border-gray-700">
                          <p className="text-xs text-gray-400 mb-1">City</p>
                          <p className="text-white">{userDetails.profile?.city || selectedUser.city}</p>
                        </div>
                      ) : null}
                      {userDetails.profile?.country || selectedUser.country ? (
                        <div className="p-3 bg-gray-800/50 rounded-lg border border-gray-700">
                          <p className="text-xs text-gray-400 mb-1">Country</p>
                          <p className="text-white">{userDetails.profile?.country || selectedUser.country}</p>
                        </div>
                      ) : null}
                      {userDetails.website_url || selectedUser.website_url ? (
                        <div className="p-3 bg-gray-800/50 rounded-lg border border-gray-700">
                          <p className="text-xs text-gray-400 mb-1">Website</p>
                          <a href={userDetails.website_url || selectedUser.website_url} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">
                            {userDetails.website_url || selectedUser.website_url}
                          </a>
                        </div>
                      ) : null}
                    </div>
                  </div>
                )}

                {/* Activity & Login Information */}
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <Clock className="h-5 w-5 text-yellow-500" />
                    Activity & Login Information
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-3 bg-gray-800/50 rounded-lg border border-gray-700">
                      <p className="text-xs text-gray-400 mb-1">Last Login</p>
                      <p className="text-white">
                        {userDetails.last_login || selectedUser.last_login 
                          ? new Date(userDetails.last_login || selectedUser.last_login).toLocaleString()
                          : "Never"}
                      </p>
                    </div>
                    {userDetails.activities && userDetails.activities.length > 0 && (
                      <div className="p-3 bg-gray-800/50 rounded-lg border border-gray-700">
                        <p className="text-xs text-gray-400 mb-1">Recent Activities</p>
                        <p className="text-white text-sm">{userDetails.activities.length} activities</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Suspension Information */}
                {userDetails.suspension_info && Object.keys(userDetails.suspension_info).length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                      <AlertCircle className="h-5 w-5 text-red-500" />
                      Suspension Information
                    </h3>
                    <div className="p-3 bg-red-900/20 rounded-lg border border-red-800">
                      <p className="text-white text-sm">
                        Reason: {userDetails.suspension_info.reason || "N/A"}
                      </p>
                      {userDetails.suspension_info.suspended_by && (
                        <p className="text-gray-400 text-xs mt-1">
                          Suspended by: {userDetails.suspension_info.suspended_by}
                        </p>
                      )}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* Edit User Modal */}
        {showEditModal && selectedUser && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <Card className="w-full max-w-md bg-gray-900 border-gray-800">
              <CardHeader>
                <CardTitle className="text-white">Edit User</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Name
                    </label>
                    <Input defaultValue={selectedUser.name} className="bg-gray-800 border-gray-700 text-white" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Email
                    </label>
                    <Input type="email" defaultValue={selectedUser.email} className="bg-gray-800 border-gray-700 text-white" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Role
                    </label>
                    <select 
                      defaultValue={selectedUser.role}
                      className="w-full px-3 py-2 border border-gray-700 rounded-md text-sm bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-green-500"
                    >
                      <option value="superadmin">Super Admin</option>
                      <option value="admin">Admin</option>
                      <option value="moderator">Moderator</option>
                      <option value="support">Support</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Status
                    </label>
                    <select 
                      defaultValue={selectedUser.status}
                      className="w-full px-3 py-2 border border-gray-700 rounded-md text-sm bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-green-500"
                    >
                      <option value="active">Active</option>
                      <option value="inactive">Inactive</option>
                      <option value="suspended">Suspended</option>
                    </select>
                  </div>
                  <div className="flex gap-2">
                    <Button 
                      className="flex-1"
                      onClick={() => setShowEditModal(false)}
                    >
                      Save Changes
                    </Button>
                    <Button 
                      variant="outline" 
                      className="flex-1"
                      onClick={() => setShowEditModal(false)}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </AdminLayout>
  )
}
