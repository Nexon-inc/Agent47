"use client"

import { useState, useEffect } from "react"
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts"
import { Download, Filter, RefreshCw, Loader2, TrendingUp, TrendingDown } from "lucide-react"
import { cn } from "@/lib/utils"
import { useUserStore } from "@/lib/stores/user-store"
import { useAuthStore } from "@/lib/stores/auth-store"
import { apiClient } from "@/lib/api-client"
import { Skeleton } from "@/components/ui/skeleton"

// Types
type AgentId = "aria" | "jackie" | "shakes" | "clara" | "eric" | "all"
type Period = "7" | "30" | "90"
type Metric = "engagement" | "response" | "roi" | "usage"

interface AnalyticsSummary {
  total_tasks: number
  completed_tasks: number
  success_rate: number
  average_response_time: number
  total_engagement: number
  roi_percentage: number
  user_satisfaction: number
  period_start: string
  period_end: string
  agent_breakdown: Record<string, any>
}

interface ChartDataPoint {
  date: string
  value: number
  agent_id?: string
  metadata?: any
}

interface UsageDistribution {
  name: string
  value: number
  percentage: number
  color: string
}

interface DetailedData {
  id: string
  task: string
  agent: string
  engagement: string
  response_time: string
  roi: string
  satisfaction: string
  date: string
  status: string
}

export default function AnalyticsTab() {
  const { userPlan } = useUserStore()
  const { user } = useAuthStore()
  const [selectedAgent, setSelectedAgent] = useState<AgentId>("all")
  const [selectedPeriod, setSelectedPeriod] = useState<Period>(userPlan === "Free" ? "7" : "30")
  const [selectedMetric, setSelectedMetric] = useState<Metric>("engagement")

  // Data states
  const [analyticsSummary, setAnalyticsSummary] = useState<AnalyticsSummary | null>(null)
  const [chartData, setChartData] = useState<ChartDataPoint[]>([])
  const [usageData, setUsageData] = useState<UsageDistribution[]>([])
  const [tableData, setTableData] = useState<DetailedData[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  // Colors for charts
  const COLORS = ["#FF6B1A", "#FF1493", "#9370DB", "#3CB371", "#FFD700", "#3B82F6", "#6366F1"]

  // Load analytics data
  useEffect(() => {
    loadAnalyticsData()
  }, [selectedAgent, selectedPeriod, selectedMetric])

  // Subscribe to real-time analytics updates via WebSocket
  useEffect(() => {
    const { websocketService } = require('@/lib/websocket-service')
    
    if (!websocketService.getConnectionStatus()) {
      websocketService.connect()
    }

    // Reload analytics when tasks are completed or updated
    const unsubscribe = websocketService.subscribe('task_update', () => {
      loadAnalyticsData()
    })

    return () => unsubscribe()
  }, [selectedAgent, selectedPeriod, selectedMetric])

  const loadAnalyticsData = async () => {
    try {
      setIsLoading(true)
      setIsRefreshing(true)
      
      const periodDays = parseInt(selectedPeriod)
      
      // Load all analytics data in parallel
      const [summaryResponse, chartResponse, usageResponse, detailedResponse] = await Promise.all([
        apiClient.get(`/api/analytics/summary?period_days=${periodDays}&agent_id=${selectedAgent === "all" ? "" : selectedAgent}`),
        apiClient.get(`/api/analytics/chart-data?metric_type=${selectedMetric}&period_days=${periodDays}&agent_id=${selectedAgent === "all" ? "" : selectedAgent}&group_by=day`),
        apiClient.get(`/api/analytics/usage-distribution?period_days=${periodDays}`),
        apiClient.get(`/api/analytics/detailed-data?period_days=${periodDays}&agent_id=${selectedAgent === "all" ? "" : selectedAgent}&limit=50`)
      ])
      
      setAnalyticsSummary(summaryResponse.data)
      setChartData(chartResponse.data)
      setUsageData(usageResponse.data)
      setTableData(detailedResponse.data)
      setLastUpdated(new Date())
      
    } catch (error) {
      console.error("Failed to load analytics data:", error)
      // Generate fallback data
      generateFallbackData()
    } finally {
      setIsLoading(false)
      setIsRefreshing(false)
    }
  }

  const generateFallbackData = () => {
    // Set empty data when API is not available
    setChartData([])
    setUsageData([])
    setTableData([])
    setLastUpdated(new Date())
  }

  const handleRefresh = () => {
    loadAnalyticsData()
  }

  const handleExport = async () => {
    try {
      const periodDays = parseInt(selectedPeriod)
      const response = await apiClient.get(`/api/analytics/export?period_days=${periodDays}&format=csv`)
      
      // Create and download CSV file
      const blob = new Blob([response.data.csv_data], { type: 'text/csv' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `analytics-export-${new Date().toISOString().split('T')[0]}.csv`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error("Failed to export data:", error)
    }
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-[#4B0082]  mb-4">Analytics</h1>
        <p className="text-gray-600  mb-6">
          Track performance metrics for your agents.
          {userPlan === "Free"
            ? " Free tier shows 7-day trends."
            : userPlan === "Starter"
              ? " Starter plan shows 30-day trends."
              : " Pro plan shows 90-day trends and advanced metrics."}
              {lastUpdated && (
                <span className="ml-2 text-sm text-gray-500">
                  Last updated: {lastUpdated.toLocaleTimeString()}
                </span>
              )}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${isRefreshing ? "animate-spin" : ""}`} />
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white  rounded-xl shadow-sm border border-gray-200  p-4 mb-6">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[150px]">
            <label htmlFor="agent" className="block text-sm font-medium text-gray-700  mb-1">
              Agent
            </label>
            <select
              id="agent"
              value={selectedAgent}
              onChange={(e) => setSelectedAgent(e.target.value as AgentId)}
              className="w-full h-10 px-3 rounded-lg border border-gray-300  bg-white  text-gray-900  focus:outline-none focus:ring-2 focus:ring-[#1E90FF]"
            >
              <option value="all">All Agents</option>
              <option value="aria">Aria</option>
              <option value="clara">Clara</option>
              <option value="jackie">Jackie</option>
              <option value="shakes">Shakes</option>
              <option value="eric">Eric</option>
            </select>
          </div>

          <div className="flex-1 min-w-[150px]">
            <label htmlFor="period" className="block text-sm font-medium text-gray-700  mb-1">
              Time Period
            </label>
            <select
              id="period"
              value={selectedPeriod}
              onChange={(e) => setSelectedPeriod(e.target.value as Period)}
              className="w-full h-10 px-3 rounded-lg border border-gray-300  bg-white  text-gray-900  focus:outline-none focus:ring-2 focus:ring-[#1E90FF]"
              disabled={userPlan === "Free"}
            >
              <option value="7">Last 7 Days</option>
              <option value="30" disabled={userPlan === "Free"}>
                Last 30 Days
              </option>
              <option value="90" disabled={userPlan === "Free" || userPlan === "Starter"}>
                Last 90 Days
              </option>
            </select>
          </div>

          <div className="flex-1 min-w-[150px]">
            <label htmlFor="metric" className="block text-sm font-medium text-gray-700  mb-1">
              Metric
            </label>
            <select
              id="metric"
              value={selectedMetric}
              onChange={(e) => setSelectedMetric(e.target.value as Metric)}
              className="w-full h-10 px-3 rounded-lg border border-gray-300  bg-white  text-gray-900  focus:outline-none focus:ring-2 focus:ring-[#1E90FF]"
            >
              <option value="engagement">Engagement</option>
              <option value="response">Response Time</option>
              <option value="roi">ROI</option>
              <option value="usage">Usage</option>
            </select>
          </div>

          {userPlan === "Pro" && (
            <div className="flex items-end">
              <button className="h-10 px-4 flex items-center justify-center rounded-lg border border-gray-300  text-gray-700  hover:bg-gray-50 :bg-gray-700 transition-colors">
                <Filter className="w-4 h-4 mr-2" />
                Advanced Filters
              </button>
            </div>
          )}

          <div className="flex items-end ml-auto">
            <button
              onClick={handleExport}
              className={cn(
                "h-10 px-4 flex items-center justify-center rounded-lg transition-colors",
                userPlan === "Free"
                  ? "bg-gray-100  text-gray-400  cursor-not-allowed"
                  : "bg-[#1E90FF] text-white hover:bg-[#1E90FF]/90",
              )}
              disabled={userPlan === "Free" || isLoading}
            >
              <Download className="w-4 h-4 mr-2" />
              Export
            </button>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Engagement Line Chart */}
        <div className="bg-white  rounded-xl shadow-sm border border-gray-200  p-4">
          <h2 className="text-lg font-semibold text-gray-900  mb-4">
            {selectedMetric === "engagement"
              ? "Engagement Metrics"
              : selectedMetric === "response"
                ? "Response Time"
                : selectedMetric === "roi"
                  ? "Return on Investment"
                  : "Usage Metrics"}
          </h2>
          <div className="h-80">
            {isLoading ? (
              <div className="h-full flex flex-col justify-center space-y-4 p-4">
                <Skeleton className="h-4 w-48" />
                <Skeleton className="h-64 w-full" />
                <div className="flex gap-2">
                  <Skeleton className="h-3 w-16" />
                  <Skeleton className="h-3 w-16" />
                  <Skeleton className="h-3 w-16" />
                </div>
              </div>
            ) : chartData.length === 0 ? (
              <div className="flex items-center justify-center h-full text-gray-500">
                <div className="text-center">
                  <p className="text-lg font-medium">No data available</p>
                  <p className="text-sm">Connect your agents to see analytics</p>
                </div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                  <XAxis dataKey="date" stroke="#718096" />
                  <YAxis stroke="#718096" />
                  <Tooltip />
                  <Legend />
                  {selectedAgent === "all" ? (
                    <>
                      <Line type="monotone" dataKey="aria" stroke="#FF6B1A" strokeWidth={2} dot={{ r: 4 }} />
                      <Line type="monotone" dataKey="clara" stroke="#FF1493" strokeWidth={2} dot={{ r: 4 }} />
                      <Line type="monotone" dataKey="jackie" stroke="#9370DB" strokeWidth={2} dot={{ r: 4 }} />
                      <Line type="monotone" dataKey="shakes" stroke="#3CB371" strokeWidth={2} dot={{ r: 4 }} />
                      <Line type="monotone" dataKey="eric" stroke="#FFD700" strokeWidth={2} dot={{ r: 4 }} />
                      <Line type="monotone" dataKey="joe" stroke="#3B82F6" strokeWidth={2} dot={{ r: 4 }} />
                      <Line type="monotone" dataKey="purity" stroke="#6366F1" strokeWidth={2} dot={{ r: 4 }} />
                    </>
                  ) : (
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke={
                        selectedAgent === "aria"
                          ? "#FF6B1A"
                          : selectedAgent === "clara"
                            ? "#FF1493"
                            : selectedAgent === "jackie"
                              ? "#9370DB"
                              : selectedAgent === "shakes"
                                ? "#3CB371"
                                : selectedAgent === "eric"
                                  ? "#FFD700"
                                  : selectedAgent === "joe"
                                    ? "#3B82F6"
                                    : "#6366F1"
                      }
                      strokeWidth={2}
                      dot={{ r: 4 }}
                    />
                  )}
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* ROI Bar Chart */}
        <div className="bg-white  rounded-xl shadow-sm border border-gray-200  p-4">
          <h2 className="text-lg font-semibold text-gray-900  mb-4">
            {selectedMetric === "engagement"
              ? "Engagement by Week"
              : selectedMetric === "response"
                ? "Average Response Time"
                : selectedMetric === "roi"
                  ? "ROI by Week"
                  : "Agent Distribution"}
          </h2>
          <div className="h-80">
            {isLoading ? (
              <div className="h-full flex flex-col justify-center space-y-4 p-4">
                <Skeleton className="h-4 w-48" />
                {selectedMetric === "usage" ? (
                  <div className="flex items-center justify-center">
                    <Skeleton className="h-48 w-48 rounded-full" />
                  </div>
                ) : (
                  <Skeleton className="h-64 w-full" />
                )}
                <div className="flex gap-2 justify-center">
                  <Skeleton className="h-3 w-16" />
                  <Skeleton className="h-3 w-16" />
                </div>
              </div>
            ) : (selectedMetric === "usage" ? usageData : chartData).length === 0 ? (
              <div className="flex items-center justify-center h-full text-gray-500">
                <div className="text-center">
                  <p className="text-lg font-medium">No data available</p>
                  <p className="text-sm">Connect your agents to see analytics</p>
                </div>
              </div>
            ) : selectedMetric === "usage" ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={usageData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  >
                    {usageData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color || COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                  <XAxis dataKey="date" stroke="#718096" />
                  <YAxis stroke="#718096" />
                  <Tooltip />
                  <Legend />
                  {selectedAgent === "all" ? (
                    <>
                      <Bar dataKey="aria" fill="#FF6B1A" />
                      <Bar dataKey="clara" fill="#FF1493" />
                      <Bar dataKey="jackie" fill="#9370DB" />
                      <Bar dataKey="shakes" fill="#3CB371" />
                      <Bar dataKey="eric" fill="#FFD700" />
                      <Bar dataKey="joe" fill="#3B82F6" />
                      <Bar dataKey="purity" fill="#6366F1" />
                    </>
                  ) : (
                    <Bar
                      dataKey="value"
                      fill={
                        selectedAgent === "aria"
                          ? "#FF6B1A"
                          : selectedAgent === "clara"
                            ? "#FF1493"
                            : selectedAgent === "jackie"
                              ? "#9370DB"
                              : selectedAgent === "shakes"
                                ? "#3CB371"
                                : selectedAgent === "eric"
                                  ? "#FFD700"
                                  : selectedAgent === "joe"
                                    ? "#3B82F6"
                                    : "#6366F1"
                      }
                    />
                  )}
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      {/* Data Table */}
      <div className="bg-white  rounded-xl shadow-sm border border-gray-200  overflow-hidden">
        <div className="p-4 border-b border-gray-200  flex justify-between items-center">
          <h2 className="text-lg font-semibold text-gray-900 ">Detailed Data</h2>
          {userPlan !== "Free" && (
            <button className="text-[#1E90FF] hover:text-[#00FF88] transition-colors text-sm flex items-center">
              <Download className="w-4 h-4 mr-1" />
              Export CSV
            </button>
          )}
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 ">
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500  uppercase tracking-wider">
                  Task
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500  uppercase tracking-wider">
                  Agent
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500  uppercase tracking-wider">
                  Metrics
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500  uppercase tracking-wider">
                  Performance
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500  uppercase tracking-wider">
                  Date
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 ">
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center">
                    <div className="flex items-center justify-center">
                      <Loader2 className="w-6 h-6 animate-spin mr-2 text-green-500" />
                      <span className="text-gray-500">Loading data...</span>
                    </div>
                  </td>
                </tr>
              ) : tableData.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                    No data available
                  </td>
                </tr>
              ) : (
                tableData.map((row) => (
                  <tr key={row.id} className="hover:bg-gray-50 :bg-gray-700">
                    <td className="px-4 py-3 text-sm text-gray-900 ">{row.task}</td>
                    <td className="px-4 py-3 text-sm text-gray-900 ">{row.agent}</td>
                    <td className="px-4 py-3 text-sm text-gray-900 ">
                      <div className="space-y-1">
                        <div>Engagement: {row.engagement}</div>
                        <div>Response: {row.response_time}</div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900 ">
                      <div className="space-y-1">
                        <div>ROI: {row.roi}</div>
                        <div>Satisfaction: {row.satisfaction}</div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500 ">
                      <div className="flex items-center gap-2">
                        <span>{row.date}</span>
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          row.status === "completed" 
                            ? "bg-green-100 text-green-800" 
                            : "bg-red-100 text-red-800"
                        }`}>
                          {row.status}
                        </span>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {userPlan === "Free" && (
          <div className="p-4 bg-gray-50  text-center">
            <p className="text-sm text-gray-500 ">Upgrade to see more data and export options</p>
            <a
              href="/pricing"
              className="inline-block mt-2 text-[#1E90FF] hover:text-[#00FF88] transition-colors text-sm font-medium"
            >
              Upgrade Now
            </a>
          </div>
        )}
      </div>
    </div>
  )
}
