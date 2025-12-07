"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { 
  CreditCard, 
  DollarSign, 
  TrendingUp, 
  Calendar,
  Download,
  Eye,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  BarChart3,
  Settings,
  Loader2,
  Users,
  Database,
  MessageCircle,
  ImageIcon,
  Zap,
  Shield
} from "lucide-react"
import { useBillingStore } from "@/lib/stores/billing-store"
import { useAuthStore } from "@/lib/stores/auth-store"
import { apiClient } from "@/lib/api-client"

export default function UserBillingPage() {
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCancelModal, setShowCancelModal] = useState(false)
  const [showUpgradeModal, setShowUpgradeModal] = useState(false)
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null)
  
  const { 
    subscription, 
    paymentHistory, 
    usage, 
    billingPlans,
    fetchSubscription, 
    fetchPaymentHistory, 
    fetchUsage,
    fetchBillingPlans,
    cancelSubscription 
  } = useBillingStore()
  
  const { user } = useAuthStore()

  useEffect(() => {
    const loadBillingData = async () => {
      setIsLoading(true)
      setError(null)
      
      try {
        await Promise.all([
          fetchSubscription(true),
          fetchPaymentHistory(),
          fetchUsage(),
          fetchBillingPlans(true)
        ])
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load billing data')
      } finally {
        setIsLoading(false)
      }
    }
    
    loadBillingData()
  }, [fetchSubscription, fetchPaymentHistory, fetchUsage, fetchBillingPlans])

  const handleCancelSubscription = async () => {
    try {
      await cancelSubscription('User requested cancellation')
      setShowCancelModal(false)
    } catch (error) {
      console.error('Failed to cancel subscription:', error)
    }
  }

  const handleUpgrade = async (planTier: string) => {
    try {
      const response = await apiClient.createSubscription(planTier, 'paystack')
      if (response.payment_url) {
        window.location.href = response.payment_url
      }
    } catch (error) {
      console.error('Failed to upgrade subscription:', error)
    }
  }

  const getUsagePercentage = (current: number, limit: number | null) => {
    if (!limit) return 0
    return Math.min((current / limit) * 100, 100)
  }

  const getUsageColor = (percentage: number) => {
    if (percentage >= 90) return 'text-red-600'
    if (percentage >= 75) return 'text-yellow-600'
    return 'text-green-600'
  }

  const getFeatureIcon = (feature: string) => {
    switch (feature.toLowerCase()) {
      case 'agents':
        return <Users className="w-4 h-4" />
      case 'analytics':
        return <BarChart3 className="w-4 h-4" />
      case 'integrations':
        return <Database className="w-4 h-4" />
      case 'support':
        return <MessageCircle className="w-4 h-4" />
      case 'team':
        return <Users className="w-4 h-4" />
      case 'image generation':
        return <ImageIcon className="w-4 h-4" />
      case 'ai generation':
        return <Zap className="w-4 h-4" />
      case 'white label':
        return <Shield className="w-4 h-4" />
      default:
        return <CheckCircle className="w-4 h-4" />
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
          <p className="text-gray-500">Loading billing information...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <XCircle className="w-8 h-8 text-red-500 mx-auto mb-4" />
          <p className="text-red-500">Error: {error}</p>
          <Button onClick={() => window.location.reload()} className="mt-4">
            Retry
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Billing & Subscription</h1>
          <p className="text-gray-500 dark:text-gray-400">Manage your subscription and billing information</p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" onClick={() => window.location.href = '/pricing'}>
            <Settings className="w-4 h-4 mr-2" />
            Manage Plan
          </Button>
          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            Download Invoices
          </Button>
        </div>
      </div>

      {/* Current Subscription */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <CreditCard className="w-5 h-5 mr-2" />
            Current Subscription
          </CardTitle>
        </CardHeader>
        <CardContent>
          {subscription ? (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 p-6 rounded-lg">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white capitalize">
                    {subscription.tier} Plan
                  </h3>
                  <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                    ${subscription.price_usd}/month
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {subscription.plan_name}
                  </p>
                </div>
                
                <div className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 p-6 rounded-lg">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Status</h3>
                  <Badge variant={subscription.status === 'active' ? 'default' : 'secondary'} className="mt-2">
                    {subscription.status}
                  </Badge>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                    {subscription.auto_renew ? 'Auto-renewal enabled' : 'Auto-renewal disabled'}
                  </p>
                </div>
                
                <div className="bg-gradient-to-r from-purple-50 to-violet-50 dark:from-purple-900/20 dark:to-violet-900/20 p-6 rounded-lg">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Billing Cycle</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Started: {new Date(subscription.start_date).toLocaleDateString()}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Next: {new Date(subscription.end_date).toLocaleDateString()}
                  </p>
                </div>
              </div>
              
              <div className="flex space-x-4">
                <Button 
                  onClick={() => window.location.href = '/pricing'}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  Change Plan
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => setShowCancelModal(true)}
                  className="text-red-600 hover:text-red-700"
                >
                  Cancel Subscription
                </Button>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <CreditCard className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                No Active Subscription
              </h3>
              <p className="text-gray-500 dark:text-gray-400 mb-4">
                You don't have an active subscription. Choose a plan to get started.
              </p>
              <Button onClick={() => window.location.href = '/pricing'}>
                Choose Plan
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Usage Analytics */}
      {usage && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <BarChart3 className="w-5 h-5 mr-2" />
              Usage This Month
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">API Calls</span>
                  <span className={`text-sm font-medium ${getUsageColor(getUsagePercentage(usage.api_calls_count, subscription?.features?.api_rate_limits?.requests_per_hour || 1000))}`}>
                    {usage.api_calls_count.toLocaleString()}
                  </span>
                </div>
                <Progress 
                  value={getUsagePercentage(usage.api_calls_count, subscription?.features?.api_rate_limits?.requests_per_hour || 1000)} 
                  className="h-2"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Limit: {(subscription?.features?.api_rate_limits?.requests_per_hour || 1000).toLocaleString()}/hour
                </p>
              </div>
              
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Storage</span>
                  <span className={`text-sm font-medium ${getUsageColor(getUsagePercentage(usage.storage_used_mb, subscription?.features?.storage_limit_mb || 1000))}`}>
                    {usage.storage_used_mb.toFixed(1)} MB
                  </span>
                </div>
                <Progress 
                  value={getUsagePercentage(usage.storage_used_mb, subscription?.features?.storage_limit_mb || 1000)} 
                  className="h-2"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Limit: {(subscription?.features?.storage_limit_mb || 1000).toLocaleString()} MB
                </p>
              </div>
              
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Agents</span>
                  <span className="text-sm font-medium text-green-600">
                    {usage.agent_usage?.active_agents || 0} active
                  </span>
                </div>
                <Progress 
                  value={getUsagePercentage(usage.agent_usage?.active_agents || 0, subscription?.features?.agents?.max_count || 3)} 
                  className="h-2"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Limit: {subscription?.features?.agents?.max_count || 3} agents
                </p>
              </div>
            </div>
            
            {getUsagePercentage(usage.api_calls_count, subscription?.features?.api_rate_limits?.requests_per_hour || 1000) >= 75 && (
              <div className="mt-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                <div className="flex items-center">
                  <AlertTriangle className="w-5 h-5 text-yellow-600 mr-2" />
                  <p className="text-sm text-yellow-800 dark:text-yellow-200">
                    You're approaching your usage limits. Consider upgrading your plan for more capacity.
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Payment History */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Calendar className="w-5 h-5 mr-2" />
            Payment History
          </CardTitle>
        </CardHeader>
        <CardContent>
          {paymentHistory.length > 0 ? (
            <div className="space-y-4">
              {paymentHistory.map((payment) => (
                <div
                  key={payment.id}
                  className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  <div className="flex items-center space-x-4">
                    <div className="w-10 h-10 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center">
                      <CreditCard className="w-5 h-5 text-gray-500 dark:text-gray-400" />
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white">
                        ${payment.amount_usd.toFixed(2)} {payment.currency}
                      </h4>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {new Date(payment.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <Badge variant={payment.status === 'successful' ? 'default' : 'secondary'}>
                      {payment.status}
                    </Badge>
                    <span className="text-sm text-gray-500 dark:text-gray-400 capitalize">
                      {payment.payment_method}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500 dark:text-gray-400">No payment history available.</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Cancel Subscription Modal */}
      {showCancelModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Cancel Subscription
            </h3>
            <p className="text-gray-600 dark:text-gray-300 mb-6">
              Are you sure you want to cancel your subscription? You'll lose access to premium features at the end of your current billing period.
            </p>
            <div className="flex space-x-4">
              <Button 
                variant="outline" 
                onClick={() => setShowCancelModal(false)}
              >
                Keep Subscription
              </Button>
              <Button 
                variant="destructive"
                onClick={handleCancelSubscription}
              >
                Cancel Subscription
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
