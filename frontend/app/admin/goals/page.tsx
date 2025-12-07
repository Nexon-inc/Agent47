"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { 
  Target, 
  Search, 
  Filter, 
  Plus, 
  Eye, 
  Edit, 
  TrendingUp,
  Calendar,
  Users,
  CheckCircle,
  Clock,
  AlertTriangle,
  BarChart3,
  Activity
} from "lucide-react"
import { useGoalsStore } from "@/lib/stores/goals-store"
import { useAdminStore } from "@/lib/stores/admin-store"
import AdminLayout from "@/components/admin/layout"
import { Goal, GoalStatus, GoalPriority, GoalType } from "@/lib/api-client"
import CreateGoalModal from "@/components/admin/goals/create-goal-modal"
import GoalDetailsModal from "@/components/admin/goals/goal-details-modal"
import GoalProgressModal from "@/components/admin/goals/goal-progress-modal"
import GoalAnalytics from "@/components/admin/goals/goal-analytics"

export default function AdminGoalsPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [filterStatus, setFilterStatus] = useState<string>("all")
  const [filterPriority, setFilterPriority] = useState<string>("all")
  const [filterType, setFilterType] = useState<string>("all")
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showDetailsModal, setShowDetailsModal] = useState(false)
  const [showProgressModal, setShowProgressModal] = useState(false)
  const [selectedGoal, setSelectedGoal] = useState<Goal | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  
  const { 
    goals, 
    analytics, 
    isLoading, 
    error, 
    total, 
    active_goals, 
    completed_goals, 
    overdue_goals, 
    fetchGoals, 
    fetchAnalytics
  } = useGoalsStore()
  const { currentAdmin } = useAdminStore()

  const hasAccess = currentAdmin?.permissions?.includes("super_admin") || 
                    currentAdmin?.permissions?.includes("system_admin")

  useEffect(() => {
    if (hasAccess) {
      fetchGoals(currentPage, 10, filterStatus !== "all" ? filterStatus : undefined)
      fetchAnalytics()
    }
  }, [hasAccess, currentPage, filterStatus, fetchGoals, fetchAnalytics])

  const filteredGoals = goals.filter(goal => {
    const matchesSearch = 
      goal.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      goal.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      goal.assigned_agents.some(agent => agent.toLowerCase().includes(searchQuery.toLowerCase()))
    
    const matchesPriority = filterPriority === "all" || goal.priority === filterPriority
    const matchesType = filterType === "all" || goal.goal_type === filterType

    return matchesSearch && matchesPriority && matchesType
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active": return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300"
      case "completed": return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300"
      case "paused": return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300"
      case "failed": return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300"
      case "draft": return "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300"
      default: return "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300"
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "critical": return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300"
      case "high": return "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300"
      case "medium": return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300"
      case "low": return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300"
      default: return "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300"
    }
  }

  const handleViewGoal = (goal: Goal) => {
    setSelectedGoal(goal)
    setShowDetailsModal(true)
  }

  const handleUpdateProgress = (goal: Goal) => {
    setSelectedGoal(goal)
    setShowProgressModal(true)
  }

  const handleCreateGoal = () => {
    setShowCreateModal(true)
  }

  const handleGoalCreated = () => {
    setShowCreateModal(false)
    fetchGoals(currentPage, 10, filterStatus !== "all" ? filterStatus : undefined)
    fetchAnalytics()
  }

  const handleProgressUpdated = () => {
    setShowProgressModal(false)
    fetchGoals(currentPage, 10, filterStatus !== "all" ? filterStatus : undefined)
    fetchAnalytics()
  }

  if (!hasAccess) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Target className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">Access Denied</h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              You don't have permission to access the goals management.
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
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Goals Management</h1>
            <p className="text-gray-600 dark:text-gray-400">Manage and track agent goals and objectives</p>
          </div>
          <Button onClick={handleCreateGoal} className="bg-green-600 hover:bg-green-700">
            <Plus className="h-4 w-4 mr-2" />
            Create Goal
          </Button>
        </div>

        {/* Analytics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Goals</CardTitle>
              <Target className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{total}</div>
              <p className="text-xs text-muted-foreground">
                {active_goals} active, {completed_goals} completed
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Goals</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{active_goals}</div>
              <p className="text-xs text-muted-foreground">
                Currently in progress
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Completed Goals</CardTitle>
              <CheckCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">{completed_goals}</div>
              <p className="text-xs text-muted-foreground">
                Successfully achieved
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Overdue Goals</CardTitle>
              <AlertTriangle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">{overdue_goals}</div>
              <p className="text-xs text-muted-foreground">
                Past deadline
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Filters and Search */}
        <Card>
          <CardHeader>
            <CardTitle>Goals</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col sm:flex-row gap-4 mb-6">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                  <Input
                    placeholder="Search goals..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
              <div className="flex gap-2">
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                >
                  <option value="all">All Status</option>
                  <option value="active">Active</option>
                  <option value="completed">Completed</option>
                  <option value="paused">Paused</option>
                  <option value="failed">Failed</option>
                  <option value="draft">Draft</option>
                </select>
                <select
                  value={filterPriority}
                  onChange={(e) => setFilterPriority(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                >
                  <option value="all">All Priorities</option>
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
                <select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                >
                  <option value="all">All Types</option>
                  <option value="user_acquisition">User Acquisition</option>
                  <option value="revenue_generation">Revenue Generation</option>
                  <option value="customer_satisfaction">Customer Satisfaction</option>
                  <option value="operational_efficiency">Operational Efficiency</option>
                  <option value="market_expansion">Market Expansion</option>
                  <option value="product_development">Product Development</option>
                  <option value="custom">Custom</option>
                </select>
              </div>
            </div>

            {/* Goals List */}
            {isLoading ? (
              <div className="flex items-center justify-center h-32">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
              </div>
            ) : error ? (
              <div className="text-center text-red-600 py-8">{error}</div>
            ) : filteredGoals.length === 0 ? (
              <div className="text-center py-8">
                <Target className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No goals found</h3>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  Get started by creating a new goal.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {filteredGoals.map((goal) => (
                  <Card key={goal.id} className="hover:shadow-md transition-shadow">
                    <CardContent className="p-6">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                              {goal.name}
                            </h3>
                            <Badge className={getStatusColor(goal.status)}>
                              {goal.status}
                            </Badge>
                            <Badge className={getPriorityColor(goal.priority)}>
                              {goal.priority}
                            </Badge>
                          </div>
                          <p className="text-gray-600 dark:text-gray-400 mb-3">
                            {goal.description}
                          </p>
                          <div className="flex items-center gap-6 text-sm text-gray-500 dark:text-gray-400 mb-3">
                            <div className="flex items-center gap-1">
                              <Calendar className="h-4 w-4" />
                              <span>Due: {new Date(goal.end_date).toLocaleDateString()}</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <Users className="h-4 w-4" />
                              <span>{goal.assigned_agents.length} agents</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <Clock className="h-4 w-4" />
                              <span>{goal.days_remaining} days left</span>
                            </div>
                          </div>
                          <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                              <span>Overall Progress</span>
                              <span>{goal.overall_progress.toFixed(1)}%</span>
                            </div>
                            <Progress value={goal.overall_progress} className="h-2" />
                          </div>
                        </div>
                        <div className="flex gap-2 ml-4">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleViewGoal(goal)}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleUpdateProgress(goal)}
                          >
                            <TrendingUp className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Analytics Section */}
        {analytics && <GoalAnalytics analytics={analytics} />}

        {/* Modals */}
        {showCreateModal && (
          <CreateGoalModal
            isOpen={showCreateModal}
            onClose={() => setShowCreateModal(false)}
            onGoalCreated={handleGoalCreated}
          />
        )}

        {showDetailsModal && selectedGoal && (
          <GoalDetailsModal
            goal={selectedGoal}
            isOpen={showDetailsModal}
            onClose={() => setShowDetailsModal(false)}
            onGoalUpdated={() => {
              setShowDetailsModal(false)
              fetchGoals(currentPage, 10, filterStatus !== "all" ? filterStatus : undefined)
              fetchAnalytics()
            }}
          />
        )}

        {showProgressModal && selectedGoal && (
          <GoalProgressModal
            goal={selectedGoal}
            isOpen={showProgressModal}
            onClose={() => setShowProgressModal(false)}
            onProgressUpdated={handleProgressUpdated}
          />
        )}
      </div>
    </AdminLayout>
  )
}
