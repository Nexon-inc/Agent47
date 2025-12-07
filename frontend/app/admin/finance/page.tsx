"use client"

import { useState, useEffect } from "react"
import AdminLayout from "@/components/admin/layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { adminAPI } from "@/lib/services/admin-api"
import { useAdminStore } from "@/lib/stores/admin-store"
import { usePolling } from "@/lib/hooks/use-polling"
import { CreditCard, TrendingUp, DollarSign, Activity, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"

export default function FinancePage() {
  const { currentAdmin } = useAdminStore()
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const hasAccess = currentAdmin?.permissions?.includes("super_admin") || 
                    currentAdmin?.permissions?.includes("system_admin")

  const [overviewData, setOverviewData] = useState<any>(null)
  const [transactionsData, setTransactionsData] = useState<any>(null)
  const [statisticsData, setStatisticsData] = useState<any>(null)
  const [isLoadingOverview, setIsLoadingOverview] = useState(true)
  const [isLoadingTransactions, setIsLoadingTransactions] = useState(true)
  const [isLoadingStatistics, setIsLoadingStatistics] = useState(true)
  const [overviewError, setOverviewError] = useState<any>(null)
  const [transactionsError, setTransactionsError] = useState<any>(null)
  const [statisticsError, setStatisticsError] = useState<any>(null)

  // Load initial data
  useEffect(() => {
    if (!hasAccess) return
    
    const loadData = async () => {
      try {
        setIsLoadingOverview(true)
        setIsLoadingTransactions(true)
        setIsLoadingStatistics(true)
        const [overview, transactions, statistics] = await Promise.all([
          adminAPI.getFinanceOverview().catch(err => { setOverviewError(err); return null }),
          adminAPI.getFinanceTransactions(1, 20).catch(err => { setTransactionsError(err); return null }),
          adminAPI.getFinanceStatistics().catch(err => { setStatisticsError(err); return null })
        ])
        if (overview) setOverviewData(overview)
        if (transactions) setTransactionsData(transactions)
        if (statistics) setStatisticsData(statistics)
      } finally {
        setIsLoadingOverview(false)
        setIsLoadingTransactions(false)
        setIsLoadingStatistics(false)
      }
    }
    loadData()
  }, [hasAccess])

  // Subscribe to real-time finance updates via WebSocket
  useEffect(() => {
    if (!hasAccess) return

    const { websocketService } = require('@/lib/websocket-service')
    
    if (!websocketService.getConnectionStatus()) {
      websocketService.connect()
    }

    // Reload finance data when billing notifications arrive
    const unsubscribe = websocketService.subscribe('notification', (message) => {
      if (message.data?.type === 'billing_reminder' || message.data?.type === 'system_update') {
        adminAPI.getFinanceOverview().then(setOverviewData).catch(setOverviewError)
        adminAPI.getFinanceTransactions(1, 20).then(setTransactionsData).catch(setTransactionsError)
        adminAPI.getFinanceStatistics().then(setStatisticsData).catch(setStatisticsError)
      }
    })

    return () => unsubscribe()
  }, [hasAccess])

  const refetchOverview = async () => {
    try {
      const data = await adminAPI.getFinanceOverview()
      setOverviewData(data)
    } catch (err) {
      setOverviewError(err)
    }
  }

  const refetchTransactions = async () => {
    try {
      const data = await adminAPI.getFinanceTransactions(1, 20)
      setTransactionsData(data)
    } catch (err) {
      setTransactionsError(err)
    }
  }

  const refetchStatistics = async () => {
    try {
      const data = await adminAPI.getFinanceStatistics()
      setStatisticsData(data)
    } catch (err) {
      setStatisticsError(err)
    }
  }

  useEffect(() => {
    setIsLoading(isLoadingOverview || isLoadingTransactions || isLoadingStatistics)
  }, [isLoadingOverview, isLoadingTransactions, isLoadingStatistics])

  useEffect(() => {
    if (overviewError || transactionsError || statisticsError) {
      setError(overviewError?.message || transactionsError?.message || statisticsError?.message || "Failed to load finance data")
    } else {
      setError(null)
    }
  }, [overviewError, transactionsError, statisticsError])

  const refreshData = () => {
    refetchOverview()
    refetchTransactions()
    refetchStatistics()
  }

  if (isLoading) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-400">Loading...</div>
        </div>
      </AdminLayout>
    )
  }

  if (!hasAccess) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <CreditCard className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-white">Access Denied</h3>
            <p className="mt-1 text-sm text-gray-500">You don't have permission to access finance.</p>
          </div>
        </div>
      </AdminLayout>
    )
  }

  if (error) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-red-400">{error}</div>
        </div>
      </AdminLayout>
    )
  }

  if (!hasAccess) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <CreditCard className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-white">Access Denied</h3>
            <p className="mt-1 text-sm text-gray-500">You don't have permission to access finance.</p>
          </div>
        </div>
      </AdminLayout>
    )
  }

  if (isLoading) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
        </div>
      </AdminLayout>
    )
  }

  if (error) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-red-400">{error}</div>
        </div>
      </AdminLayout>
    )
  }

  return (
    <AdminLayout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Finance</h1>
            <p className="text-gray-400">Financial management and reporting</p>
          </div>
          <Button onClick={refreshData} disabled={isLoading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {/* Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                ${overviewData?.total_revenue?.toLocaleString() || '0.00'}
              </div>
              <p className="text-xs text-muted-foreground">All time</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Monthly Revenue</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                ${overviewData?.monthly_revenue?.toLocaleString() || '0.00'}
              </div>
              <p className="text-xs text-muted-foreground">This month</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Subscriptions</CardTitle>
              <CreditCard className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {overviewData?.active_subscriptions || 0}
              </div>
              <p className="text-xs text-muted-foreground">Currently active</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Pending Transactions</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {overviewData?.pending_transactions || 0}
              </div>
              <p className="text-xs text-muted-foreground">Awaiting processing</p>
            </CardContent>
          </Card>
        </div>

        {/* Recent Transactions */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Transactions</CardTitle>
          </CardHeader>
          <CardContent>
            {transactionsData?.transactions?.length > 0 ? (
              <div className="space-y-4">
                {transactionsData.transactions.map((transaction: any) => (
                  <div key={transaction.id || transaction.transaction_id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <div className="font-medium">{transaction.description || transaction.type}</div>
                      <div className="text-sm text-muted-foreground">
                        {new Date(transaction.timestamp || transaction.created_at).toLocaleString()}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`font-bold ${transaction.amount >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        ${Math.abs(transaction.amount || 0).toLocaleString()}
                      </div>
                      <div className="text-sm text-muted-foreground">{transaction.status || 'completed'}</div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">No transactions found</div>
            )}
          </CardContent>
        </Card>

        {/* Statistics */}
        {statisticsData && (
          <Card>
            <CardHeader>
              <CardTitle>Financial Statistics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <div className="text-sm text-muted-foreground">Average Transaction</div>
                  <div className="text-2xl font-bold">
                    ${statisticsData.average_transaction?.toLocaleString() || '0.00'}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Total Transactions</div>
                  <div className="text-2xl font-bold">
                    {statisticsData.total_transactions || 0}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Success Rate</div>
                  <div className="text-2xl font-bold">
                    {statisticsData.success_rate?.toFixed(1) || '0.0'}%
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Refund Rate</div>
                  <div className="text-2xl font-bold">
                    {statisticsData.refund_rate?.toFixed(1) || '0.0'}%
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </AdminLayout>
  )
}

