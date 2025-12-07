"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { 
  UserCheck, 
  Search,
  User,
  Clock,
  AlertTriangle,
  LogOut,
  Eye
} from "lucide-react"
import { useAdminStore } from "@/lib/stores/admin-store"
import AdminLayout from "@/components/admin/layout"
import { adminAPI } from "@/lib/services/admin-api"

export default function AdminImpersonatePage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedUser, setSelectedUser] = useState<any>(null)
  const [isImpersonating, setIsImpersonating] = useState(false)
  const { currentAdmin } = useAdminStore()

  const hasAccess = currentAdmin?.permissions?.includes("super_admin")

  if (!hasAccess) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <UserCheck className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-white">Access Denied</h3>
            <p className="mt-1 text-sm text-gray-500">
              Super admin access required.
            </p>
          </div>
        </div>
      </AdminLayout>
    )
  }

  const [users, setUsers] = useState<any[]>([])
  const [currentSession, setCurrentSession] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadUsers = async () => {
      try {
        const usersData = await adminAPI.getUsers(1, 100)
        if (usersData.users) {
          setUsers(usersData.users)
        }
      } catch (err: any) {
        setError(err.message || "Failed to load users")
      }
    }
    if (hasAccess) {
      loadUsers()
    }
  }, [hasAccess])

  const filteredUsers = users.filter(user => 
    (user.email || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (user.full_name || user.username || '').toLowerCase().includes(searchQuery.toLowerCase())
  )

  const startImpersonation = async (user: any) => {
    try {
      const session = await adminAPI.startImpersonation(user.user_id || user.id, "Admin support session")
      setCurrentSession(session)
      setSelectedUser(user)
      setIsImpersonating(true)
    } catch (err: any) {
      setError(err.message || "Failed to start impersonation")
    }
  }

  const stopImpersonation = async () => {
    if (currentSession?.session_id) {
      try {
        await adminAPI.endImpersonation(currentSession.session_id)
      } catch (err: any) {
        setError(err.message || "Failed to end impersonation")
      }
    }
    setIsImpersonating(false)
    setSelectedUser(null)
    setCurrentSession(null)
  }

  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">User Impersonation</h1>
            <p className="text-gray-600 dark:text-gray-400">Impersonate users for support and debugging</p>
          </div>
          {isImpersonating && (
            <Button variant="destructive" onClick={stopImpersonation}>
              <LogOut className="h-4 w-4 mr-2" />
              Stop Impersonation
            </Button>
          )}
        </div>

        {/* Current Session */}
        {isImpersonating && selectedUser && (
          <Card className="border-blue-200 bg-blue-50 dark:bg-blue-900/20">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <User className="h-5 w-5 text-blue-600" />
                  <div>
                    <h3 className="font-medium text-blue-800 dark:text-blue-200">
                      Currently impersonating: {selectedUser.name}
                    </h3>
                    <p className="text-sm text-blue-700 dark:text-blue-300">
                      {selectedUser.email} • {selectedUser.tier} tier
                    </p>
                  </div>
                </div>
                <Badge className="bg-blue-100 text-blue-800">
                  <Clock className="h-3 w-3 mr-1" />
                  Active Session
                </Badge>
              </div>
            </CardContent>
          </Card>
        )}

        {/* User Search */}
        <Card>
          <CardHeader>
            <CardTitle>Find User to Impersonate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  placeholder="Search by email or name..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>

              {/* User List */}
              <div className="space-y-2">
                {filteredUsers.map((user) => (
                  <div key={user.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                    <div className="flex items-center gap-3">
                      <User className="h-5 w-5 text-gray-400" />
                      <div>
                        <h3 className="font-medium text-gray-900 dark:text-white">{user.name}</h3>
                        <p className="text-sm text-gray-500">{user.email}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge className={
                        user.tier === 'premium' ? 'bg-purple-100 text-purple-800' :
                        user.tier === 'starter' ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-800'
                      }>
                        {user.tier}
                      </Badge>
                      <Badge className={
                        user.status === 'active' ? 'bg-green-100 text-green-800' :
                        'bg-red-100 text-red-800'
                      }>
                        {user.status}
                      </Badge>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => startImpersonation(user)}
                        disabled={isImpersonating}
                      >
                        <Eye className="h-4 w-4 mr-1" />
                        Impersonate
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Security Notice */}
        <Card className="border-yellow-200 bg-yellow-50 dark:bg-yellow-900/20">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
              <div>
                <h3 className="font-medium text-yellow-800 dark:text-yellow-200">Security Notice</h3>
                <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
                  User impersonation is logged and monitored. Only use this feature for legitimate support 
                  and debugging purposes. All actions performed while impersonating will be attributed to 
                  the impersonated user.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </AdminLayout>
  )
}
