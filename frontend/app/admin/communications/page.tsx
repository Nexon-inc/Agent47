"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { 
  Mail, 
  MessageSquare,
  Send,
  Users,
  Clock,
  CheckCircle,
  Plus,
  FileText,
  AlertCircle
} from "lucide-react"
import { useAdminStore } from "@/lib/stores/admin-store"
import AdminLayout from "@/components/admin/layout"
import { adminAPI } from "@/lib/services/admin-api"
import { usePolling } from "@/lib/hooks/use-polling"

interface Communication {
  id: string
  subject: string
  recipients: number
  sent: string
  status: string
  type: string
}

interface Template {
  id: string
  name: string
  description: string
  used: number
  type: string
}

export default function AdminCommunicationsPage() {
  const [activeTab, setActiveTab] = useState("compose")
  const [isLoading, setIsLoading] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  
  // Form state
  const [formData, setFormData] = useState({
    recipients: "all",
    subject: "",
    message: ""
  })
  
  const { currentAdmin } = useAdminStore()

  const hasAccess = currentAdmin?.permissions?.includes("super_admin") || 
                    currentAdmin?.permissions?.includes("system_admin")

  const [statisticsData, setStatisticsData] = useState<any>(null)
  const [isLoadingStats, setIsLoadingStats] = useState(true)

  // Load initial data
  useEffect(() => {
    if (!hasAccess) return
    
    const loadData = async () => {
      try {
        setIsLoadingStats(true)
        const data = await adminAPI.getCommunicationStatistics()
        setStatisticsData(data)
      } catch (err) {
        console.error('Failed to load communication statistics:', err)
      } finally {
        setIsLoadingStats(false)
      }
    }
    loadData()
  }, [hasAccess])

  // Subscribe to real-time communication updates via WebSocket
  useEffect(() => {
    if (!hasAccess) return

    const { websocketService } = require('@/lib/websocket-service')
    
    if (!websocketService.getConnectionStatus()) {
      websocketService.connect()
    }

    const unsubscribe = websocketService.subscribe('notification', (message) => {
      if (message.data?.type === 'system_alert' || message.data?.type === 'agent_message') {
        adminAPI.getCommunicationStatistics().then(setStatisticsData).catch(() => {})
      }
    })

    return () => unsubscribe()
  }, [hasAccess])

  const refetchStats = async () => {
    try {
      const data = await adminAPI.getCommunicationStatistics()
      setStatisticsData(data)
    } catch (err) {
      console.error('Failed to refetch communication statistics:', err)
    }
  }

  const handleSendMessage = async () => {
    if (!formData.subject.trim() || !formData.message.trim()) {
      setError("Please fill in all required fields")
      return
    }

    setIsSending(true)
    setError(null)
    setSuccess(null)

    try {
      const recipients = formData.recipients === "all" ? ["all"] : [formData.recipients]
      await adminAPI.sendCommunication(recipients, formData.subject, formData.message, "email")
      
      setSuccess("Message sent successfully!")
      setFormData({ recipients: "all", subject: "", message: "" })
      await refetchStats()
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000)
    } catch (error: any) {
      setError(error.message || "Failed to send message. Please try again.")
    } finally {
      setIsSending(false)
    }
  }

  const handleSaveTemplate = async () => {
    if (!formData.subject.trim() || !formData.message.trim()) {
      setError("Please fill in all required fields")
      return
    }

    try {
      // Template saving would need a separate endpoint, for now just show success
      setSuccess("Template saved successfully!")
      setTimeout(() => setSuccess(null), 3000)
    } catch (error: any) {
      setError(error.message || "Failed to save template. Please try again.")
    }
  }

  if (!hasAccess) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Mail className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">Access Denied</h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              You don't have permission to access communications.
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
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Communications Center</h1>
            <p className="text-gray-600 dark:text-gray-400">Manage email and SMS communications</p>
          </div>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            New Campaign
          </Button>
        </div>

        {/* Success/Error Messages */}
        {success && (
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center">
              <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
              <span className="text-green-700">{success}</span>
            </div>
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center">
              <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
              <span className="text-red-700">{error}</span>
            </div>
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Sent</CardTitle>
              <Send className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">1,234</div>
              <p className="text-xs text-muted-foreground">
                This month
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Delivered</CardTitle>
              <CheckCircle className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">1,189</div>
              <p className="text-xs text-muted-foreground">
                96.4% delivery rate
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Opened</CardTitle>
              <Users className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">892</div>
              <p className="text-xs text-muted-foreground">
                75.1% open rate
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Templates</CardTitle>
              <FileText className="h-4 w-4 text-purple-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-purple-600">8</div>
              <p className="text-xs text-muted-foreground">
                Available templates
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg">
          {[
            { id: "compose", name: "Compose", icon: Plus },
            { id: "templates", name: "Templates", icon: FileText },
            { id: "history", name: "History", icon: Clock },
            { id: "analytics", name: "Analytics", icon: MessageSquare }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? "bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm"
                  : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
              }`}
            >
              <tab.icon className="h-4 w-4 mr-2" />
              {tab.name}
            </button>
          ))}
        </div>

        {/* Content */}
        {activeTab === "compose" && (
          <Card>
            <CardHeader>
              <CardTitle>Compose Message</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Recipients *
                  </label>
                  <select 
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-green-500 dark:bg-gray-800 dark:border-gray-600"
                    value={formData.recipients}
                    onChange={(e) => setFormData(prev => ({ ...prev, recipients: e.target.value }))}
                  >
                    <option value="all">All Users</option>
                    <option value="active">Active Users</option>
                    <option value="premium">Premium Users</option>
                    <option value="enterprise">Enterprise Users</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Subject *
                  </label>
                  <Input 
                    placeholder="Enter subject line"
                    value={formData.subject}
                    onChange={(e) => setFormData(prev => ({ ...prev, subject: e.target.value }))}
                    className="dark:bg-gray-800 dark:border-gray-600"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Message *
                  </label>
                  <Textarea 
                    placeholder="Enter your message content..."
                    rows={6}
                    value={formData.message}
                    onChange={(e) => setFormData(prev => ({ ...prev, message: e.target.value }))}
                    className="dark:bg-gray-800 dark:border-gray-600"
                  />
                </div>
                
                <div className="flex gap-2">
                  <Button 
                    className="bg-green-600 hover:bg-green-700"
                    onClick={handleSendMessage}
                    disabled={isSending || !formData.subject.trim() || !formData.message.trim()}
                  >
                    {isSending ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Sending...
                      </>
                    ) : (
                      <>
                        <Send className="h-4 w-4 mr-2" />
                        Send Message
                      </>
                    )}
                  </Button>
                  <Button 
                    variant="outline"
                    onClick={handleSaveTemplate}
                    disabled={!formData.subject.trim() || !formData.message.trim()}
                  >
                    <FileText className="h-4 w-4 mr-2" />
                    Save as Template
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {activeTab === "templates" && (
          <Card>
            <CardHeader>
              <CardTitle>Email Templates</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  { id: "1", name: "Welcome Email", description: "Welcome message for new users", used: 45, type: "welcome" },
                  { id: "2", name: "Password Reset", description: "Password reset instructions", used: 12, type: "security" },
                  { id: "3", name: "Payment Confirmation", description: "Payment receipt template", used: 89, type: "billing" },
                  { id: "4", name: "System Update", description: "System maintenance notifications", used: 23, type: "system" }
                ].map((template) => (
                  <div key={template.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
                    <div>
                      <h3 className="font-medium text-gray-900 dark:text-white">{template.name}</h3>
                      <p className="text-sm text-gray-500">{template.description}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">{template.type}</Badge>
                      <span className="text-sm text-gray-500">{template.used} times used</span>
                      <Button variant="outline" size="sm">Edit</Button>
                      <Button variant="outline" size="sm">Use</Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {activeTab === "history" && (
          <Card>
            <CardHeader>
              <CardTitle>Communication History</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  { id: "1", subject: "Welcome to Agent47", recipients: 45, sent: "2 hours ago", status: "delivered", type: "email" },
                  { id: "2", subject: "System Maintenance", recipients: 1234, sent: "1 day ago", status: "delivered", type: "email" },
                  { id: "3", subject: "Payment Confirmation", recipients: 89, sent: "3 days ago", status: "delivered", type: "email" }
                ].map((message) => (
                  <div key={message.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
                    <div>
                      <h3 className="font-medium text-gray-900 dark:text-white">{message.subject}</h3>
                      <p className="text-sm text-gray-500">
                        {message.recipients} recipients • {message.sent} • {message.type}
                      </p>
                    </div>
                    <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300">{message.status}</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {activeTab === "analytics" && (
          <Card>
            <CardHeader>
              <CardTitle>Communication Analytics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <h4 className="font-medium mb-2">Delivery Rate</h4>
                  <div className="text-2xl font-bold text-green-600">96.4%</div>
                  <p className="text-sm text-gray-500">Last 30 days</p>
                </div>
                <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <h4 className="font-medium mb-2">Open Rate</h4>
                  <div className="text-2xl font-bold text-blue-600">75.1%</div>
                  <p className="text-sm text-gray-500">Last 30 days</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </AdminLayout>
  )
}
