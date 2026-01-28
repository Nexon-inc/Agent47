"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  Users,
  CreditCard,
  Calendar,
  Search,
  Filter,
  Download,
  Eye
} from "lucide-react"
import { useAdminStore } from "@/lib/stores/admin-store"
import { adminAPI } from "@/lib/services/admin-api"
import { Loader2, AlertCircle } from "lucide-react"
import AdminLayout from "@/components/admin/layout"

interface Subscription {
  id: string
  user_email: string
  plan: string
  status: string
  amount: number
  next_billing: string
  created_at: string
}

interface Payment {
  id: string
  user_email: string
  amount: number
  status: string
  payment_method: string
  created_at: string
}

interface RevenueData {
  total_revenue: number
  monthly_recurring_revenue: number
  annual_recurring_revenue: number
  total_subscriptions: number
  active_subscriptions: number
  average_revenue_per_user: number
  churn_rate: number
  tier_distribution: {
    free: {
      count: number
      monthly_revenue: number
      yearly_revenue: number
    }
    starter: {
      count: number
      monthly_revenue: number
      yearly_revenue: number
    }
    pro: {
      count: number
      monthly_revenue: number
      yearly_revenue: number
    }
  }
}

export default function AdminBillingPage() {
  const [activeTab, setActiveTab] = useState("overview")
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([])
  const [recentActivity, setRecentActivity] = useState<any[]>([])
  const [analytics, setAnalytics] = useState<any>(null)
  const [revenueData, setRevenueData] = useState<RevenueData | null>(null)
  const [searchQuery, setSearchQuery] = useState("")
  const [filterStatus, setFilterStatus] = useState("all")
  const [filterPlan, setFilterPlan] = useState("all")
  const [billingPeriod, setBillingPeriod] = useState<"monthly" | "yearly">("monthly")

  // Fetch billing data on component mount
  useEffect(() => {
    const fetchBillingData = async () => {
      setIsLoading(true)
      setError(null)

      try {
        const [subscriptionsData, activityData, analyticsData, revenueData] = await Promise.all([
          adminAPI.getBillingSubscriptions(),
          adminAPI.getBillingActivity(),
          adminAPI.getBillingAnalytics(),
          adminAPI.getBillingRevenue()
        ])

        setSubscriptions(subscriptionsData.subscriptions || [])
        setRecentActivity(activityData.activities || [])
        setAnalytics(analyticsData)
        setRevenueData(revenueData)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load billing data')
        console.error('Billing data fetch error:', err)
      } finally {
        setIsLoading(false)
      }
    }

    fetchBillingData()
  }, [])

  // Filter subscriptions based on search and filters
  const filteredSubscriptions = subscriptions.filter(subscription => {
    const matchesSearch = subscription.user_email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      subscription.plan.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesStatus = filterStatus === "all" || subscription.status === filterStatus
    const matchesPlan = filterPlan === "all" || subscription.plan.toLowerCase() === filterPlan.toLowerCase()

    return matchesSearch && matchesStatus && matchesPlan
  })

  const { currentAdmin } = useAdminStore()
  const { isLoading: adminLoading } = useAdminStore()

  useEffect(() => {
    if (currentAdmin) {
      // Initialize data
    }
  }, [currentAdmin])

  const handleExportData = () => {
    // Export billing data
    console.log("Exporting billing data")
  }

  if (adminLoading) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        </div>
      </AdminLayout>
    )
  }

  if (!currentAdmin) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <DollarSign className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">Access Denied</h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              You don't have permission to access billing management.
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
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Billing Management</h1>
            <p className="text-gray-600 dark:text-gray-400">Manage subscriptions and revenue</p>
          </div>
          <Button onClick={handleExportData}>
            <Download className="h-4 w-4 mr-2" />
            Export Data
          </Button>
        </div>

        {/* Billing Period Toggle */}
        <div className="flex justify-end mb-6">
          <div className="flex items-center bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
            <button
              onClick={() => setBillingPeriod("monthly")}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${billingPeriod === "monthly"
                  ? "bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm"
                  : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingPeriod("yearly")}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${billingPeriod === "yearly"
                  ? "bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm"
                  : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                }`}
            >
              Yearly
            </button>
          </div>
        </div>

        {/* Revenue Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {billingPeriod === "monthly" ? "Monthly Revenue" : "Annual Revenue"}
              </CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {isLoading ? (
                  <div className="h-8 w-20 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                ) : (
                  `$${revenueData ? (billingPeriod === "monthly" ? revenueData.monthly_recurring_revenue.toLocaleString() : revenueData.annual_recurring_revenue.toLocaleString()) : "0"}`
                )}
              </div>
              <div className="flex items-center text-sm text-green-600">
                <TrendingUp className="h-4 w-4 mr-1" />
                {isLoading ? (
                  <div className="h-4 w-12 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                ) : (
                  "+0.0%"
                )}
              </div>
              <p className="text-xs text-muted-foreground">
                vs last {billingPeriod === "monthly" ? "month" : "year"}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Subscriptions</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {isLoading ? (
                  <div className="h-8 w-16 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                ) : (
                  revenueData?.active_subscriptions.toLocaleString() || "0"
                )}
              </div>
              <div className="flex items-center text-sm text-green-600">
                <TrendingUp className="h-4 w-4 mr-1" />
                {isLoading ? (
                  <div className="h-4 w-12 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                ) : (
                  "+0.0%"
                )}
              </div>
              <p className="text-xs text-muted-foreground">
                vs last {billingPeriod === "monthly" ? "month" : "year"}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Churn Rate</CardTitle>
              <TrendingDown className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {isLoading ? (
                  <div className="h-8 w-12 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                ) : (
                  `${revenueData?.churn_rate.toFixed(1) || "0.0"}%`
                )}
              </div>
              <div className="flex items-center text-sm text-green-600">
                <TrendingDown className="h-4 w-4 mr-1" />
                {isLoading ? (
                  <div className="h-4 w-12 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                ) : (
                  "-0.0%"
                )}
              </div>
              <p className="text-xs text-muted-foreground">
                vs last {billingPeriod === "monthly" ? "month" : "year"}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Average Revenue</CardTitle>
              <CreditCard className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {isLoading ? (
                  <div className="h-8 w-16 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                ) : (
                  `$${revenueData?.average_revenue_per_user.toFixed(2) || "0.00"}`
                )}
              </div>
              <div className="flex items-center text-sm text-green-600">
                <TrendingUp className="h-4 w-4 mr-1" />
                {isLoading ? (
                  <div className="h-4 w-12 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                ) : (
                  "+0.0%"
                )}
              </div>
              <p className="text-xs text-muted-foreground">
                per user
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg">
          {[
            { id: "overview", name: "Overview", icon: DollarSign },
            { id: "subscriptions", name: "Subscriptions", icon: Users },
            { id: "payments", name: "Payments", icon: CreditCard },
            { id: "analytics", name: "Analytics", icon: TrendingUp }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === tab.id
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
        {activeTab === "overview" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Revenue Breakdown */}
            <Card>
              <CardHeader>
                <CardTitle>Revenue by Plan ({billingPeriod === "monthly" ? "Monthly" : "Yearly"})</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {isLoading ? (
                    // Loading skeleton
                    <>
                      {[1, 2, 3].map((i) => (
                        <div key={i} className="flex justify-between items-center">
                          <div className="h-4 w-20 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                          <div className="h-4 w-16 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                        </div>
                      ))}
                      <div className="pt-4 border-t">
                        <div className="flex justify-between items-center">
                          <div className="h-4 w-24 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                          <div className="h-4 w-20 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                        </div>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Free Plan</span>
                        <span className="font-medium">$0</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Starter Plan</span>
                        <span className="font-medium">
                          ${revenueData?.tier_distribution.starter[billingPeriod === "monthly" ? "monthly_revenue" : "yearly_revenue"].toLocaleString() || "0"}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Pro Plan</span>
                        <span className="font-medium">
                          ${revenueData?.tier_distribution.pro[billingPeriod === "monthly" ? "monthly_revenue" : "yearly_revenue"].toLocaleString() || "0"}
                        </span>
                      </div>
                      <div className="pt-4 border-t">
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-medium">Total Revenue</span>
                          <span className="font-bold">
                            ${billingPeriod === "monthly"
                              ? revenueData?.monthly_recurring_revenue.toLocaleString() || "0"
                              : revenueData?.annual_recurring_revenue.toLocaleString() || "0"
                            }
                          </span>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Recent Activity */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {isLoading ? (
                    <div className="flex items-center justify-center py-4">
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      <span>Loading activity...</span>
                    </div>
                  ) : recentActivity.length === 0 ? (
                    <div className="text-center py-4 text-gray-500">
                      No recent activity
                    </div>
                  ) : (
                    recentActivity.map((activity, index) => (
                      <div key={index} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                        <div>
                          <p className="font-medium text-gray-900 dark:text-white">{activity.action}</p>
                          <p className="text-sm text-gray-500">{activity.user}</p>
                        </div>
                        <div className="text-right">
                          <span className="font-medium text-gray-900 dark:text-white">{activity.amount}</span>
                          <p className="text-sm text-gray-500">{activity.time}</p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === "subscriptions" && (
          <Card>
            <CardHeader>
              <CardTitle>Subscriptions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Filters */}
                <div className="flex flex-col sm:flex-row gap-4 mb-6">
                  <div className="flex-1">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                      <Input
                        placeholder="Search subscriptions..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-10 dark:bg-gray-800 dark:border-gray-600"
                      />
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <select
                      value={filterStatus}
                      onChange={(e) => setFilterStatus(e.target.value)}
                      className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-green-500 dark:bg-gray-800 dark:border-gray-600"
                    >
                      <option value="all">All Status</option>
                      <option value="active">Active</option>
                      <option value="cancelled">Cancelled</option>
                      <option value="past_due">Past Due</option>
                    </select>
                    <select
                      value={filterPlan}
                      onChange={(e) => setFilterPlan(e.target.value)}
                      className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-green-500 dark:bg-gray-800 dark:border-gray-600"
                    >
                      <option value="all">All Plans</option>
                      <option value="free">Free</option>
                      <option value="starter">Starter</option>
                      <option value="pro">Pro</option>
                    </select>
                  </div>
                </div>

                {/* Subscriptions List */}
                <div className="space-y-4">
                  {isLoading ? (
                    <div className="flex items-center justify-center py-8">
                      <Loader2 className="h-6 w-6 animate-spin mr-2" />
                      <span>Loading subscriptions...</span>
                    </div>
                  ) : error ? (
                    <div className="flex items-center justify-center py-8 text-red-600">
                      <AlertCircle className="h-6 w-6 mr-2" />
                      <span>{error}</span>
                    </div>
                  ) : filteredSubscriptions.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      No subscriptions found
                    </div>
                  ) : (
                    filteredSubscriptions.map((subscription) => (
                      <div key={subscription.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
                        <div>
                          <h3 className="font-medium text-gray-900 dark:text-white">{subscription.user_email}</h3>
                          <p className="text-sm text-gray-500">
                            {subscription.plan} Plan • Created {subscription.created_at}
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge className={
                            subscription.status === 'active' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' :
                              subscription.status === 'cancelled' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300' :
                                'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
                          }>
                            {subscription.status}
                          </Badge>
                          <span className="font-medium">${subscription.amount}</span>
                          <Button variant="outline" size="sm">
                            <Eye className="h-4 w-4 mr-1" />
                            View
                          </Button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {activeTab === "payments" && (
          <Card>
            <CardHeader>
              <CardTitle>Payment History</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {isLoading ? (
                  // Loading skeleton
                  <>
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                        <div className="flex-1">
                          <div className="h-4 w-32 bg-gray-200 dark:bg-gray-700 rounded animate-pulse mb-2" />
                          <div className="h-3 w-48 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="h-6 w-16 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                          <div className="h-4 w-12 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                          <div className="h-3 w-20 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                        </div>
                      </div>
                    ))}
                  </>
                ) : recentActivity.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    No payment history available
                  </div>
                ) : (
                  recentActivity.map((activity, index) => (
                    <div key={index} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
                      <div>
                        <h3 className="font-medium text-gray-900 dark:text-white">{activity.user}</h3>
                        <p className="text-sm text-gray-500">{activity.action}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className={
                          activity.status === 'completed' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' :
                            activity.status === 'failed' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300' :
                              'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
                        }>
                          {activity.status || 'completed'}
                        </Badge>
                        <span className="font-medium">{activity.amount}</span>
                        <span className="text-sm text-gray-500">{activity.time}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {activeTab === "analytics" && (
          <Card>
            <CardHeader>
              <CardTitle>Billing Analytics</CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin mr-2" />
                  <span>Loading analytics...</span>
                </div>
              ) : error ? (
                <div className="flex items-center justify-center py-8 text-red-600">
                  <AlertCircle className="h-6 w-6 mr-2" />
                  <span>{error}</span>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <h4 className="font-medium mb-2">Monthly Recurring Revenue</h4>
                    <div className="text-2xl font-bold text-green-600">
                      ${analytics?.mrr?.toLocaleString() || '0'}
                    </div>
                    <p className="text-sm text-gray-500">
                      {analytics?.mrr_growth ? `+${analytics.mrr_growth}% vs last month` : 'No data available'}
                    </p>
                  </div>
                  <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <h4 className="font-medium mb-2">Customer Lifetime Value</h4>
                    <div className="text-2xl font-bold text-blue-600">
                      ${analytics?.clv?.toLocaleString() || '0'}
                    </div>
                    <p className="text-sm text-gray-500">Average per customer</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </AdminLayout>
  )
}
