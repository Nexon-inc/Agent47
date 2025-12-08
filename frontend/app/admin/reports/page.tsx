"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { 
  TrendingUp, 
  TrendingDown, 
  Users, 
  DollarSign, 
  Activity, 
  BarChart3, 
  PieChart, 
  Download, 
  Calendar, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Loader2, 
  XCircle,
  Eye,
  Settings,
  RefreshCw
} from "lucide-react"
import { useAdminStore } from "@/lib/stores/admin-store"
import AdminLayout from "@/components/admin/layout"
import { usePolling } from "@/lib/hooks/use-polling"
import { 
  LineChart, 
  Line, 
  AreaChart, 
  Area, 
  BarChart, 
  Bar, 
  PieChart as RechartsPieChart, 
  Pie, 
  Cell, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts'
import { adminAPI } from "@/lib/services/admin-api"

export default function AdminReportsPage() {
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('30d')
  const [reportType, setReportType] = useState<'overview' | 'usage' | 'subscriptions' | 'financial'>('overview')
  
  // Usage tracking state
  const [usageMetrics, setUsageMetrics] = useState<any>(null)
  const [usageAlerts, setUsageAlerts] = useState<any[]>([])
  
  // Subscription state
  const [subscriptionAnalytics, setSubscriptionAnalytics] = useState<any>(null)
  
  // Financial state
  const [financialReport, setFinancialReport] = useState<any>(null)
  const [revenueForecast, setRevenueForecast] = useState<number[]>([])

  const { currentAdmin } = useAdminStore()

  const hasAccess = currentAdmin?.permissions?.includes("super_admin") || 
                    currentAdmin?.permissions?.includes("system_admin")

  const getDays = (range: string) => {
    switch (range) {
      case "7d": return 7
      case "30d": return 30
      case "90d": return 90
      default: return 30
    }
  }

  const [usageData, setUsageData] = useState<any>(null)
  const [subscriptionData, setSubscriptionData] = useState<any>(null)
  const [financialData, setFinancialData] = useState<any>(null)
  const [forecastData, setForecastData] = useState<any>(null)
  const [isLoadingUsage, setIsLoadingUsage] = useState(false)
  const [isLoadingSubscriptions, setIsLoadingSubscriptions] = useState(false)
  const [isLoadingFinancial, setIsLoadingFinancial] = useState(false)
  const [isLoadingForecast, setIsLoadingForecast] = useState(false)
  const [usageError, setUsageError] = useState<any>(null)
  const [subscriptionError, setSubscriptionError] = useState<any>(null)
  const [financialError, setFinancialError] = useState<any>(null)

  // Load initial data
  useEffect(() => {
    if (!hasAccess) return
    
    const loadData = async () => {
      try {
        if (reportType === 'usage') {
          setIsLoadingUsage(true)
          const data = await adminAPI.getUsageReports(getDays(timeRange))
          setUsageData(data)
        } else if (reportType === 'subscriptions') {
          setIsLoadingSubscriptions(true)
          const data = await adminAPI.getSubscriptionReports(getDays(timeRange))
          setSubscriptionData(data)
        } else if (reportType === 'financial') {
          setIsLoadingFinancial(true)
          const data = await adminAPI.getFinancialReports(getDays(timeRange))
          setFinancialData(data)
        }
        setIsLoadingForecast(true)
        const forecast = await adminAPI.getRevenueForecast(12)
        setForecastData(forecast)
      } catch (err) {
        if (reportType === 'usage') setUsageError(err)
        else if (reportType === 'subscriptions') setSubscriptionError(err)
        else if (reportType === 'financial') setFinancialError(err)
      } finally {
        setIsLoadingUsage(false)
        setIsLoadingSubscriptions(false)
        setIsLoadingFinancial(false)
        setIsLoadingForecast(false)
      }
    }
    loadData()
  }, [hasAccess, reportType, timeRange])

  // Subscribe to real-time report updates via WebSocket
  useEffect(() => {
    if (!hasAccess) return

    const { websocketService } = require('@/lib/websocket-service')
    
    if (!websocketService.getConnectionStatus()) {
      websocketService.connect()
    }

    const unsubscribe = websocketService.subscribe('notification', (message) => {
      if (message.data?.type === 'billing_reminder' || message.data?.type === 'system_update') {
        if (reportType === 'usage') {
          adminAPI.getUsageReports(getDays(timeRange)).then(setUsageData).catch(setUsageError)
        } else if (reportType === 'subscriptions') {
          adminAPI.getSubscriptionReports(getDays(timeRange)).then(setSubscriptionData).catch(setSubscriptionError)
        } else if (reportType === 'financial') {
          adminAPI.getFinancialReports(getDays(timeRange)).then(setFinancialData).catch(setFinancialError)
        }
      }
    })

    return () => unsubscribe()
  }, [hasAccess, reportType, timeRange])

  useEffect(() => {
    setIsLoading(isLoadingUsage || isLoadingSubscriptions || isLoadingFinancial || isLoadingForecast)
  }, [isLoadingUsage, isLoadingSubscriptions, isLoadingFinancial, isLoadingForecast])

  useEffect(() => {
    if (usageError || subscriptionError || financialError) {
      setError(usageError?.message || subscriptionError?.message || financialError?.message || "Failed to load reports")
    } else {
      setError(null)
    }
  }, [usageError, subscriptionError, financialError])

  useEffect(() => {
    if (usageData) {
      setUsageMetrics(usageData.usage_metrics)
      setUsageAlerts(usageData.alerts || [])
    }
    if (subscriptionData) {
      setSubscriptionAnalytics(subscriptionData)
    }
    if (financialData) {
      setFinancialReport(financialData)
    }
    if (forecastData) {
      setRevenueForecast(forecastData.forecast || [])
    }
  }, [usageData, subscriptionData, financialData, forecastData])

  const loadReportsData = async () => {
    try {
      setIsLoading(true)
      // Data is loaded via polling hooks; no manual fetch required here
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load reports data')
    } finally {
      setIsLoading(false)
    }
  }

  const getUsagePercentage = (current: number, limit: number | null) => {
    if (!limit) return 0
    return Math.min((current / limit) * 100, 100)
  }

  const getUsageColor = (percentage: number) => {
    if (percentage < 70) return 'bg-green-500'
    if (percentage < 90) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  const generateUsageData = () => {
    if (!usageMetrics) return []
    
    return [
      { name: 'API Calls', value: usageMetrics.api_calls_count, limit: 10000 },
      { name: 'Storage', value: usageMetrics.storage_used_mb, limit: 1000 },
      { name: 'Agents', value: usageMetrics.active_agents, limit: 5 },
      { name: 'Bandwidth', value: usageMetrics.bandwidth_used_mb, limit: 5000 }
    ]
  }

  const generateRevenueData = () => {
    if (!financialReport) return []
    
    return financialReport.revenue.revenue_by_period.monthly.map((value, index) => ({
      month: `Month ${index + 1}`,
      revenue: value
    }))
  }

  const generateChurnData = () => {
    if (!financialReport) return []
    
    return Object.entries(financialReport.churn.churn_by_tier).map(([tier, rate]) => ({
      tier: tier.charAt(0).toUpperCase() + tier.slice(1),
      churn: rate * 100
    }))
  }

  const generateCLVData = () => {
    if (!financialReport) return []
    
    return Object.entries(financialReport.clv.clv_by_tier).map(([tier, clv]) => ({
      tier: tier.charAt(0).toUpperCase() + tier.slice(1),
      clv: clv
    }))
  }

  if (isLoading) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
            <p className="text-gray-500 dark:text-gray-400">Loading comprehensive reports...</p>
          </div>
        </div>
      </AdminLayout>
    )
  }

  if (error) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <XCircle className="w-8 h-8 text-red-500 mx-auto mb-4" />
            <p className="text-red-500">Error loading reports: {error}</p>
            <Button onClick={loadReportsData} className="mt-4">
              <RefreshCw className="w-4 h-4 mr-2" />
              Retry
            </Button>
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
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Comprehensive Reports</h1>
            <p className="text-gray-500 dark:text-gray-400">Advanced analytics and insights across all business metrics</p>
          </div>
          <div className="flex space-x-2">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value as '7d' | '30d' | '90d')}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            >
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="90d">Last 90 days</option>
            </select>
            <Button variant="outline" onClick={loadReportsData}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
            <Button variant="outline">
              <Download className="w-4 h-4 mr-2" />
              Export All
            </Button>
          </div>
        </div>

        {/* Report Type Tabs */}
        <div className="flex space-x-1 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg">
          {[
            { id: 'overview', label: 'Overview', icon: BarChart3 },
            { id: 'usage', label: 'Usage', icon: Activity },
            { id: 'subscriptions', label: 'Subscriptions', icon: Users },
            { id: 'financial', label: 'Financial', icon: DollarSign }
          ].map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setReportType(tab.id as any)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  reportType === tab.id
                    ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            )
          })}
        </div>

        {/* Overview Report */}
        {reportType === 'overview' && (
          <div className="space-y-6">
            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
                  <DollarSign className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    ${financialReport?.revenue.total_revenue.toLocaleString() || '0'}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {financialReport?.revenue.revenue_growth_rate > 0 ? '+' : ''}
                    {financialReport?.revenue.revenue_growth_rate.toFixed(1)}% from last period
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Active Users</CardTitle>
                  <Users className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {subscriptionAnalytics?.active_subscriptions || '0'}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {subscriptionAnalytics?.subscription_growth_rate > 0 ? '+' : ''}
                    {subscriptionAnalytics?.subscription_growth_rate?.toFixed(1)}% from last period
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
                    {(financialReport?.churn.overall_churn_rate * 100).toFixed(1)}%
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Predicted: {(financialReport?.churn.predicted_churn * 100).toFixed(1)}% next month
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Avg CLV</CardTitle>
                  <TrendingUp className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    ${financialReport?.clv.average_clv.toFixed(0) || '0'}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Payback: {financialReport?.clv.payback_period.toFixed(1)} months
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Revenue Trend */}
              <Card>
                <CardHeader>
                  <CardTitle>Revenue Trend</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={generateRevenueData()}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="month" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="revenue" stroke="#8884d8" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Churn by Tier */}
              <Card>
                <CardHeader>
                  <CardTitle>Churn by Tier</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={generateChurnData()}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="tier" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="churn" fill="#ff6b6b" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>

            {/* Insights and Alerts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Key Insights */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Eye className="w-5 h-5 mr-2" />
                    Key Insights
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {financialReport?.key_insights.slice(0, 5).map((insight, index) => (
                      <div key={index} className="flex items-start space-x-2">
                        <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                        <p className="text-sm text-gray-700 dark:text-gray-300">{insight}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Usage Alerts */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <AlertTriangle className="w-5 h-5 mr-2" />
                    Usage Alerts
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {usageAlerts.length > 0 ? (
                      usageAlerts.slice(0, 5).map((alert, index) => (
                        <div key={index} className="flex items-start space-x-2">
                          <AlertTriangle className="w-4 h-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                          <div>
                            <p className="text-sm font-medium text-gray-900 dark:text-white">{alert.title}</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">{alert.message}</p>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="flex items-center space-x-2">
                        <CheckCircle className="w-4 h-4 text-green-500" />
                        <p className="text-sm text-gray-500 dark:text-gray-400">No usage alerts</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        )}

        {/* Usage Report */}
        {reportType === 'usage' && usageMetrics && (
          <div className="space-y-6">
            {/* Usage Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {generateUsageData().map((metric) => (
                <Card key={metric.name}>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">{metric.name}</CardTitle>
                    <Activity className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {metric.name === 'Storage' || metric.name === 'Bandwidth' 
                        ? `${metric.value.toFixed(1)} MB`
                        : metric.value.toLocaleString()}
                    </div>
                    <div className="mt-2">
                      <Progress 
                        value={getUsagePercentage(metric.value, metric.limit)} 
                        className="h-2"
                      />
                      <p className="text-xs text-muted-foreground mt-1">
                        {getUsagePercentage(metric.value, metric.limit).toFixed(1)}% of limit
                      </p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Usage Trends */}
            <Card>
              <CardHeader>
                <CardTitle>Usage Trends</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                  <AreaChart data={Array.from({ length: 30 }, (_, i) => ({
                    day: i + 1,
                    api_calls: Math.floor(Math.random() * 100) + 50,
                    storage: Math.floor(Math.random() * 50) + 25,
                    bandwidth: Math.floor(Math.random() * 200) + 100
                  }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="day" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Area type="monotone" dataKey="api_calls" stackId="1" stroke="#8884d8" fill="#8884d8" />
                    <Area type="monotone" dataKey="storage" stackId="1" stroke="#82ca9d" fill="#82ca9d" />
                    <Area type="monotone" dataKey="bandwidth" stackId="1" stroke="#ffc658" fill="#ffc658" />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Subscriptions Report */}
        {reportType === 'subscriptions' && (
          <div className="space-y-6">
            {/* Subscription Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Subscriptions</CardTitle>
                  <Users className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {subscriptionAnalytics?.total_subscriptions || '0'}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {subscriptionAnalytics?.new_subscriptions || '0'} new this month
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Active Subscriptions</CardTitle>
                  <CheckCircle className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {subscriptionAnalytics?.active_subscriptions || '0'}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {subscriptionAnalytics?.activation_rate?.toFixed(1) || '0'}% activation rate
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Upgrades</CardTitle>
                  <TrendingUp className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {subscriptionAnalytics?.upgrades_count || '0'}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {subscriptionAnalytics?.upgrade_rate?.toFixed(1) || '0'}% upgrade rate
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Downgrades</CardTitle>
                  <TrendingDown className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {subscriptionAnalytics?.downgrades_count || '0'}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {subscriptionAnalytics?.downgrade_rate?.toFixed(1) || '0'}% downgrade rate
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Customer Lifetime Value */}
            <Card>
              <CardHeader>
                <CardTitle>Customer Lifetime Value by Tier</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={generateCLVData()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="tier" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="clv" fill="#4ade80" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Financial Report */}
        {reportType === 'financial' && financialReport && (
          <div className="space-y-6">
            {/* Financial Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">MRR</CardTitle>
                  <DollarSign className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    ${financialReport.revenue.monthly_recurring_revenue.toLocaleString()}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    ARR: ${financialReport.revenue.annual_recurring_revenue.toLocaleString()}
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Avg Revenue/User</CardTitle>
                  <Users className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    ${financialReport.revenue.average_revenue_per_user.toFixed(2)}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {financialReport.revenue.revenue_growth_rate > 0 ? '+' : ''}
                    {financialReport.revenue.revenue_growth_rate.toFixed(1)}% growth
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Acquisition Cost</CardTitle>
                  <TrendingDown className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    ${financialReport.clv.acquisition_cost.toFixed(2)}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {financialReport.clv.payback_period.toFixed(1)} month payback
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Customer Segments</CardTitle>
                  <PieChart className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {Object.values(financialReport.clv.customer_segments).reduce((a, b) => a + b, 0)}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {financialReport.clv.customer_segments.high_value} high-value
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Revenue Forecast */}
            <Card>
              <CardHeader>
                <CardTitle>12-Month Revenue Forecast</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={revenueForecast.map((value, index) => ({
                    month: `Month ${index + 1}`,
                    forecast: value
                  }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="forecast" stroke="#10b981" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Recommendations */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Settings className="w-5 h-5 mr-2" />
                  Strategic Recommendations
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {financialReport.recommendations.slice(0, 6).map((recommendation, index) => (
                    <div key={index} className="flex items-start space-x-2">
                      <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                      <p className="text-sm text-gray-700 dark:text-gray-300">{recommendation}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </AdminLayout>
  )
}
