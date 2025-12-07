"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { 
  CreditCard, 
  ArrowUp, 
  ArrowDown, 
  X,
  CheckCircle,
  AlertTriangle,
  Info,
  Calendar,
  Zap,
  Users,
  Database,
  Shield,
  BarChart3,
  MessageCircle,
  ImageIcon
} from "lucide-react"
import { useBillingStore } from "@/lib/stores/billing-store"
import { apiClient } from "@/lib/api-client"

interface SubscriptionManagerProps {
  className?: string
}

export default function SubscriptionManager({ className }: SubscriptionManagerProps) {
  const { subscription, billingPlans, isLoading, fetchSubscription, createSubscription, cancelSubscription } = useBillingStore()
  const [showUpgradeModal, setShowUpgradeModal] = useState(false)
  const [showDowngradeModal, setShowDowngradeModal] = useState(false)
  const [showCancelModal, setShowCancelModal] = useState(false)
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)

  const currentPlan = billingPlans.find(plan => plan.tier === subscription?.tier)
  const availablePlans = billingPlans.filter(plan => plan.tier !== subscription?.tier)

  const handleUpgrade = async (newTier: string) => {
    setIsProcessing(true)
    try {
      if (newTier === "free") {
        // For free tier, no payment required. Suppress redirect for background flow.
        await createSubscription(newTier, "free", true)
        setShowUpgradeModal(false)
        try {
          const cookieExpires = new Date(Date.now() + 24 * 60 * 60 * 1000).toUTCString()
          document.cookie = `user_tier=free; path=/; expires=${cookieExpires}; SameSite=Lax`
        } catch (e) {
          console.warn('Could not set user_tier cookie locally', e)
        }
        window.location.href = "/dashboard"
      } else {
        await createSubscription(newTier, "paystack")
        setShowUpgradeModal(false)
        // Redirect to payment or show success
        window.location.href = "/pricing"
      }
    } catch (error) {
      console.error("Upgrade failed:", error)
    } finally {
      setIsProcessing(false)
    }
  }

  const handleDowngrade = async (newTier: string) => {
    setIsProcessing(true)
    try {
      if (newTier === "free") {
        // For free tier, no payment required. Suppress redirect for background flow.
        await createSubscription(newTier, "free", true)
        setShowDowngradeModal(false)
        try {
          const cookieExpires = new Date(Date.now() + 24 * 60 * 60 * 1000).toUTCString()
          document.cookie = `user_tier=free; path=/; expires=${cookieExpires}; SameSite=Lax`
        } catch (e) {
          console.warn('Could not set user_tier cookie locally', e)
        }
        window.location.href = "/dashboard"
      } else {
        await createSubscription(newTier, "paystack")
        setShowDowngradeModal(false)
        // Redirect to payment or show success
        window.location.href = "/pricing"
      }
    } catch (error) {
      console.error("Downgrade failed:", error)
    } finally {
      setIsProcessing(false)
    }
  }

  const handleCancel = async () => {
    setIsProcessing(true)
    try {
      await cancelSubscription("User requested cancellation")
      setShowCancelModal(false)
      // Show success message
    } catch (error) {
      console.error("Cancellation failed:", error)
    } finally {
      setIsProcessing(false)
    }
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

  const renderCurrentPlan = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CreditCard className="w-5 h-5" />
          Current Plan
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="animate-pulse space-y-4">
            <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded"></div>
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
          </div>
        ) : subscription ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white capitalize">
                  {subscription.tier} Plan
                </h3>
                <p className="text-gray-500 dark:text-gray-400">
                  ${subscription.price_usd}/month
                </p>
              </div>
              <Badge variant={subscription.status === 'active' ? 'default' : 'secondary'}>
                {subscription.status}
              </Badge>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-500 dark:text-gray-400">Next billing date</span>
                <span className="text-gray-900 dark:text-white">
                  {new Date(subscription.end_date).toLocaleDateString()}
                </span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-500 dark:text-gray-400">Auto-renewal</span>
                <span className={`${subscription.auto_renew ? 'text-green-600' : 'text-red-600'}`}>
                  {subscription.auto_renew ? 'Enabled' : 'Disabled'}
                </span>
              </div>
            </div>

            <div className="flex space-x-2">
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => setShowUpgradeModal(true)}
                disabled={subscription.tier === 'pro'}
              >
                <ArrowUp className="w-4 h-4 mr-1" />
                Upgrade
              </Button>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => setShowDowngradeModal(true)}
                disabled={subscription.tier === 'free'}
              >
                <ArrowDown className="w-4 h-4 mr-1" />
                Downgrade
              </Button>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => setShowCancelModal(true)}
                className="text-red-600 hover:text-red-700"
              >
                <X className="w-4 h-4 mr-1" />
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <div className="text-center py-6">
            <CreditCard className="w-12 h-12 text-gray-400 mx-auto mb-2" />
            <p className="text-gray-500 dark:text-gray-400">No active subscription</p>
            <Button className="mt-2" onClick={() => window.location.href = "/pricing"}>
              Choose Plan
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )

  const renderPlanComparison = () => (
    <Card>
      <CardHeader>
        <CardTitle>Plan Comparison</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <th className="text-left py-3 px-4 font-medium text-gray-900 dark:text-white">Feature</th>
                <th className="text-center py-3 px-4 font-medium text-gray-900 dark:text-white">Free</th>
                <th className="text-center py-3 px-4 font-medium text-gray-900 dark:text-white">Starter</th>
                <th className="text-center py-3 px-4 font-medium text-gray-900 dark:text-white">Pro</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              <tr>
                <td className="py-3 px-4 text-sm text-gray-500 dark:text-gray-400">Price</td>
                <td className="py-3 px-4 text-center text-sm font-medium">$0</td>
                <td className="py-3 px-4 text-center text-sm font-medium">$24.99</td>
                <td className="py-3 px-4 text-center text-sm font-medium">$79</td>
              </tr>
              <tr>
                <td className="py-3 px-4 text-sm text-gray-500 dark:text-gray-400">API Calls</td>
                <td className="py-3 px-4 text-center text-sm">1,000/month</td>
                <td className="py-3 px-4 text-center text-sm">10,000/month</td>
                <td className="py-3 px-4 text-center text-sm">Unlimited</td>
              </tr>
              <tr>
                <td className="py-3 px-4 text-sm text-gray-500 dark:text-gray-400">Agents</td>
                <td className="py-3 px-4 text-center text-sm">1</td>
                <td className="py-3 px-4 text-center text-sm">3</td>
                <td className="py-3 px-4 text-center text-sm">Unlimited</td>
              </tr>
              <tr>
                <td className="py-3 px-4 text-sm text-gray-500 dark:text-gray-400">Storage</td>
                <td className="py-3 px-4 text-center text-sm">100 MB</td>
                <td className="py-3 px-4 text-center text-sm">1 GB</td>
                <td className="py-3 px-4 text-center text-sm">10 GB</td>
              </tr>
              <tr>
                <td className="py-3 px-4 text-sm text-gray-500 dark:text-gray-400">Support</td>
                <td className="py-3 px-4 text-center text-sm">Community</td>
                <td className="py-3 px-4 text-center text-sm">Email</td>
                <td className="py-3 px-4 text-center text-sm">Priority</td>
              </tr>
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )

  const renderUpgradeModal = () => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Upgrade Plan</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <p className="text-gray-600 dark:text-gray-400">
              Choose a plan to upgrade to:
            </p>
            <div className="space-y-2">
              {availablePlans
                .filter(plan => plan.tier !== 'free')
                .map(plan => (
                  <div
                    key={plan.tier}
                    className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                      selectedPlan === plan.tier
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                    }`}
                    onClick={() => setSelectedPlan(plan.tier)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-medium text-gray-900 dark:text-white capitalize">
                          {plan.tier} Plan
                        </h4>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          ${plan.price_usd}/month
                        </p>
                      </div>
                      {selectedPlan === plan.tier && (
                        <CheckCircle className="w-5 h-5 text-blue-600" />
                      )}
                    </div>
                  </div>
                ))}
            </div>
            <div className="flex space-x-2">
              <Button 
                variant="outline" 
                className="flex-1"
                onClick={() => setShowUpgradeModal(false)}
              >
                Cancel
              </Button>
              <Button 
                className="flex-1"
                disabled={!selectedPlan || isProcessing}
                onClick={() => selectedPlan && handleUpgrade(selectedPlan)}
              >
                {isProcessing ? 'Processing...' : 'Upgrade'}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderDowngradeModal = () => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Downgrade Plan</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center space-x-2 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-yellow-600" />
              <div>
                <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                  Downgrade Warning
                </p>
                <p className="text-xs text-yellow-600 dark:text-yellow-300">
                  You may lose access to some features when downgrading
                </p>
              </div>
            </div>
            <p className="text-gray-600 dark:text-gray-400">
              Choose a plan to downgrade to:
            </p>
            <div className="space-y-2">
              {availablePlans
                .filter(plan => plan.tier !== 'pro')
                .map(plan => (
                  <div
                    key={plan.tier}
                    className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                      selectedPlan === plan.tier
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                    }`}
                    onClick={() => setSelectedPlan(plan.tier)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-medium text-gray-900 dark:text-white capitalize">
                          {plan.tier} Plan
                        </h4>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          ${plan.price_usd}/month
                        </p>
                      </div>
                      {selectedPlan === plan.tier && (
                        <CheckCircle className="w-5 h-5 text-blue-600" />
                      )}
                    </div>
                  </div>
                ))}
            </div>
            <div className="flex space-x-2">
              <Button 
                variant="outline" 
                className="flex-1"
                onClick={() => setShowDowngradeModal(false)}
              >
                Cancel
              </Button>
              <Button 
                variant="outline"
                className="flex-1"
                disabled={!selectedPlan || isProcessing}
                onClick={() => selectedPlan && handleDowngrade(selectedPlan)}
              >
                {isProcessing ? 'Processing...' : 'Downgrade'}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderCancelModal = () => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Cancel Subscription</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center space-x-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-red-600" />
              <div>
                <p className="text-sm font-medium text-red-800 dark:text-red-200">
                  Cancellation Warning
                </p>
                <p className="text-xs text-red-600 dark:text-red-300">
                  You will lose access to all premium features immediately
                </p>
              </div>
            </div>
            <p className="text-gray-600 dark:text-gray-400">
              Are you sure you want to cancel your subscription? This action cannot be undone.
            </p>
            <div className="flex space-x-2">
              <Button 
                variant="outline" 
                className="flex-1"
                onClick={() => setShowCancelModal(false)}
              >
                Keep Subscription
              </Button>
              <Button 
                variant="destructive"
                className="flex-1"
                disabled={isProcessing}
                onClick={handleCancel}
              >
                {isProcessing ? 'Cancelling...' : 'Cancel Subscription'}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  return (
    <div className={`space-y-6 ${className}`}>
      {renderCurrentPlan()}
      {renderPlanComparison()}
      
      {showUpgradeModal && renderUpgradeModal()}
      {showDowngradeModal && renderDowngradeModal()}
      {showCancelModal && renderCancelModal()}
    </div>
  )
}
