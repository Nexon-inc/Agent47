"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { 
  HelpCircle, 
  MessageSquare,
  Clock,
  CheckCircle,
  AlertTriangle,
  User,
  AlertCircle,
  Search,
  Plus,
  Eye
} from "lucide-react"
import { useAdminStore } from "@/lib/stores/admin-store"
import AdminLayout from "@/components/admin/layout"
import { adminAPI } from "@/lib/services/admin-api"
import { usePolling } from "@/lib/hooks/use-polling"

interface Ticket {
  id: string
  subject: string
  user: string
  priority: string
  status: string
  created: string
  category: string
  assigned_to?: string
}

interface Article {
  id: string
  title: string
  category: string
  views: number
  last_updated: string
}

export default function AdminSupportPage() {
  const [activeTab, setActiveTab] = useState("tickets")
  const [isLoading, setIsLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const [filterPriority, setFilterPriority] = useState("all")
  const [filterStatus, setFilterStatus] = useState("all")
  const [error, setError] = useState<string | null>(null)
  const [tickets, setTickets] = useState<Ticket[]>([])
  
  const { currentAdmin } = useAdminStore()

  const hasAccess = currentAdmin?.permissions?.includes("super_admin") || 
                    currentAdmin?.permissions?.includes("system_admin")

  const [ticketsData, setTicketsData] = useState<any>(null)
  const [statisticsData, setStatisticsData] = useState<any>(null)
  const [isLoadingTickets, setIsLoadingTickets] = useState(true)
  const [isLoadingStats, setIsLoadingStats] = useState(true)
  const [ticketsError, setTicketsError] = useState<any>(null)

  // Load initial data
  useEffect(() => {
    if (!hasAccess) return
    
    const loadData = async () => {
      try {
        setIsLoadingTickets(true)
        setIsLoadingStats(true)
        const [tickets, stats] = await Promise.all([
          adminAPI.getSupportTickets(1, 50, filterStatus !== "all" ? filterStatus : undefined, filterPriority !== "all" ? filterPriority : undefined).catch(err => { setTicketsError(err); return null }),
          adminAPI.getSupportStatistics().catch(() => null)
        ])
        if (tickets) setTicketsData(tickets)
        if (stats) setStatisticsData(stats)
      } finally {
        setIsLoadingTickets(false)
        setIsLoadingStats(false)
      }
    }
    loadData()
  }, [hasAccess, filterStatus, filterPriority])

  // Subscribe to real-time support updates via WebSocket
  useEffect(() => {
    if (!hasAccess) return

    const { websocketService } = require('@/lib/websocket-service')
    
    if (!websocketService.getConnectionStatus()) {
      websocketService.connect()
    }

    // Reload when notifications indicate ticket changes
    const unsubscribe = websocketService.subscribe('notification', (message) => {
      if (message.data?.type === 'system_alert' || message.data?.type === 'agent_message') {
        adminAPI.getSupportTickets(1, 50, filterStatus !== "all" ? filterStatus : undefined, filterPriority !== "all" ? filterPriority : undefined).then(setTicketsData).catch(setTicketsError)
        adminAPI.getSupportStatistics().then(setStatisticsData).catch(() => {})
      }
    })

    return () => unsubscribe()
  }, [hasAccess, filterStatus, filterPriority])

  const refetchTickets = async () => {
    try {
      const data = await adminAPI.getSupportTickets(1, 50, filterStatus !== "all" ? filterStatus : undefined, filterPriority !== "all" ? filterPriority : undefined)
      setTicketsData(data)
    } catch (err) {
      setTicketsError(err)
    }
  }

  useEffect(() => {
    if (ticketsData?.tickets) {
      setTickets(ticketsData.tickets.map((ticket: any) => ({
        id: ticket.ticket_id || ticket.id,
        subject: ticket.subject,
        user: ticket.user_email || ticket.user || 'Unknown',
        priority: ticket.priority || 'medium',
        status: ticket.status || 'open',
        created: ticket.created_at || ticket.timestamp,
        category: ticket.category || 'general',
        assigned_to: ticket.assigned_to
      })))
    }
  }, [ticketsData])

  useEffect(() => {
    if (ticketsError) {
      setError(ticketsError.message || "Failed to load tickets")
    } else {
      setError(null)
    }
  }, [ticketsError])

  useEffect(() => {
    setIsLoading(isLoadingTickets || isLoadingStats)
  }, [isLoadingTickets, isLoadingStats])

  const handleCreateTicket = async (subject: string, description: string, priority: string, category: string) => {
    try {
      await adminAPI.createSupportTicket(subject, description, priority, category)
      await refetchTickets()
    } catch (err: any) {
      setError(err.message || "Failed to create ticket")
    }
  }

  const handleViewTicket = (ticketId: string) => {
    // Navigate to ticket details
    console.log("View ticket:", ticketId)
  }

  const handleUpdateStatus = async (ticketId: string, status: string) => {
    try {
      await adminAPI.updateTicketStatus(ticketId, status)
      await refetchTickets()
    } catch (err: any) {
      setError(err.message || "Failed to update ticket status")
    }
  }

  const filteredTickets = tickets.filter(ticket => {
    const matchesSearch = ticket.subject.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         ticket.user.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesPriority = filterPriority === "all" || ticket.priority === filterPriority
    const matchesStatus = filterStatus === "all" || ticket.status === filterStatus
    
    return matchesSearch && matchesPriority && matchesStatus
  })

  if (!hasAccess) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <HelpCircle className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">Access Denied</h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              You don't have permission to access support management.
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
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Support Management</h1>
            <p className="text-gray-600 dark:text-gray-400">Manage customer support tickets</p>
          </div>
          <Button onClick={handleCreateTicket}>
            <Plus className="h-4 w-4 mr-2" />
            New Ticket
          </Button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Tickets</CardTitle>
              <HelpCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">156</div>
              <p className="text-xs text-muted-foreground">
                This month
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Open</CardTitle>
              <AlertTriangle className="h-4 w-4 text-yellow-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-yellow-600">23</div>
              <p className="text-xs text-muted-foreground">
                Pending resolution
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">In Progress</CardTitle>
              <Clock className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">8</div>
              <p className="text-xs text-muted-foreground">
                Being worked on
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Resolved</CardTitle>
              <CheckCircle className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">125</div>
              <p className="text-xs text-muted-foreground">
                Successfully closed
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg">
          {[
            { id: "tickets", name: "Tickets", icon: MessageSquare },
            { id: "knowledge", name: "Knowledge Base", icon: HelpCircle },
            { id: "analytics", name: "Analytics", icon: AlertCircle }
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
        {activeTab === "tickets" && (
          <Card>
            <CardHeader>
              <CardTitle>Support Tickets</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Filters */}
                <div className="flex flex-col sm:flex-row gap-4 mb-6">
                  <div className="flex-1">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                      <Input
                        placeholder="Search tickets..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-10 dark:bg-gray-800 dark:border-gray-600"
                      />
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <select
                      value={filterPriority}
                      onChange={(e) => setFilterPriority(e.target.value)}
                      className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-green-500 dark:bg-gray-800 dark:border-gray-600"
                    >
                      <option value="all">All Priorities</option>
                      <option value="high">High</option>
                      <option value="medium">Medium</option>
                      <option value="low">Low</option>
                    </select>
                    <select
                      value={filterStatus}
                      onChange={(e) => setFilterStatus(e.target.value)}
                      className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-green-500 dark:bg-gray-800 dark:border-gray-600"
                    >
                      <option value="all">All Status</option>
                      <option value="open">Open</option>
                      <option value="in_progress">In Progress</option>
                      <option value="resolved">Resolved</option>
                    </select>
                  </div>
                </div>

                {/* Tickets List */}
                <div className="space-y-4">
                  {filteredTickets.map((ticket) => (
                    <div key={ticket.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
                      <div className="flex items-center space-x-4">
                        <div>
                          <h3 className="font-medium text-gray-900 dark:text-white">{ticket.subject}</h3>
                          <p className="text-sm text-gray-500">
                            {ticket.id} • {ticket.user} • {ticket.created} • {ticket.category}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className={
                          ticket.priority === 'high' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300' :
                          ticket.priority === 'medium' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300' :
                          'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
                        }>
                          {ticket.priority}
                        </Badge>
                        <Badge className={
                          ticket.status === 'open' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300' :
                          ticket.status === 'in_progress' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300' :
                          'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
                        }>
                          {ticket.status}
                        </Badge>
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => handleViewTicket(ticket.id)}
                        >
                          <Eye className="h-4 w-4 mr-1" />
                          View
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {activeTab === "knowledge" && (
          <Card>
            <CardHeader>
              <CardTitle>Knowledge Base</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  { id: "1", title: "Getting Started Guide", category: "Onboarding", views: 234, last_updated: "2 days ago" },
                  { id: "2", title: "Payment Troubleshooting", category: "Billing", views: 156, last_updated: "1 week ago" },
                  { id: "3", title: "API Documentation", category: "Technical", views: 89, last_updated: "3 days ago" },
                  { id: "4", title: "Account Settings", category: "User Guide", views: 67, last_updated: "5 days ago" }
                ].map((article) => (
                  <div key={article.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
                    <div>
                      <h3 className="font-medium text-gray-900 dark:text-white">{article.title}</h3>
                      <p className="text-sm text-gray-500">{article.category} • {article.views} views • Updated {article.last_updated}</p>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm">Edit</Button>
                      <Button variant="outline" size="sm">View</Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {activeTab === "analytics" && (
          <Card>
            <CardHeader>
              <CardTitle>Support Analytics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <h4 className="font-medium mb-2">Average Response Time</h4>
                  <div className="text-2xl font-bold text-blue-600">2.3 hours</div>
                  <p className="text-sm text-gray-500">Last 30 days</p>
                </div>
                <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <h4 className="font-medium mb-2">Resolution Rate</h4>
                  <div className="text-2xl font-bold text-green-600">94.2%</div>
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
