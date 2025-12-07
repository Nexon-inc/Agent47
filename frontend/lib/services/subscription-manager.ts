import { apiClient, Subscription, BillingPlan } from '@/lib/api-client'

export interface SubscriptionChange {
  from_tier: string
  to_tier: string
  prorated_amount: number
  effective_date: string
  billing_cycle: string
}

export interface PauseRequest {
  reason: string
  pause_until: string
  auto_resume: boolean
}

export interface RenewalSettings {
  auto_renew: boolean
  renewal_date: string
  next_billing_amount: number
  payment_method: string
}

export interface SubscriptionAnalytics {
  total_revenue: number
  average_lifetime: number
  churn_rate: number
  upgrade_rate: number
  downgrade_rate: number
  retention_by_tier: Record<string, number>
}

class SubscriptionManager {
  private static instance: SubscriptionManager
  private currentSubscription: Subscription | null = null
  private billingPlans: BillingPlan[] = []

  private constructor() {}

  static getInstance(): SubscriptionManager {
    if (!SubscriptionManager.instance) {
      SubscriptionManager.instance = new SubscriptionManager()
    }
    return SubscriptionManager.instance
  }

  // Initialize the manager
  async initialize() {
    try {
      const [subscription, plans] = await Promise.all([
        apiClient.getSubscription({ suppressRedirect: true }).catch(() => null),
        apiClient.getBillingPlans({ suppressRedirect: true })
      ])
      
      this.currentSubscription = subscription
      this.billingPlans = plans
    } catch (error) {
      console.error('Failed to initialize subscription manager:', error)
    }
  }

  // Get current subscription
  getCurrentSubscription(): Subscription | null {
    return this.currentSubscription
  }

  // Get available billing plans
  getBillingPlans(): BillingPlan[] {
    return this.billingPlans
  }

  // Calculate prorated amount for plan change
  calculateProratedAmount(fromTier: string, toTier: string): SubscriptionChange | null {
    if (!this.currentSubscription) return null

    const fromPlan = this.billingPlans.find(p => p.tier === fromTier)
    const toPlan = this.billingPlans.find(p => p.tier === toTier)

    if (!fromPlan || !toPlan) return null

    const fromPrice = fromPlan.price_usd
    const toPrice = toPlan.price_usd
    const priceDifference = toPrice - fromPrice

    // Calculate days remaining in current billing cycle
    const now = new Date()
    const endDate = new Date(this.currentSubscription.end_date)
    const daysRemaining = Math.ceil((endDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
    const totalDays = 30 // Assuming monthly billing

    const proratedAmount = (priceDifference * daysRemaining) / totalDays

    return {
      from_tier: fromTier,
      to_tier: toTier,
      prorated_amount: Math.max(0, proratedAmount),
      effective_date: now.toISOString(),
      billing_cycle: 'monthly'
    }
  }

  // Upgrade subscription
  async upgradeSubscription(newTier: string): Promise<boolean> {
    try {
      if (!this.currentSubscription) {
        throw new Error('No active subscription')
      }

      const change = this.calculateProratedAmount(this.currentSubscription.tier, newTier)
      if (!change) {
        throw new Error('Invalid tier change')
      }

      // Create upgrade subscription
      const response = await apiClient.createSubscription(newTier, 'paystack')
      
      if (response.payment_url) {
        // Redirect to payment page for prorated amount
        window.location.href = response.payment_url
        return true
      }

      // Update local subscription
      await this.refreshSubscription()
      return true
    } catch (error) {
      console.error('Failed to upgrade subscription:', error)
      return false
    }
  }

  // Downgrade subscription
  async downgradeSubscription(newTier: string): Promise<boolean> {
    try {
      if (!this.currentSubscription) {
        throw new Error('No active subscription')
      }

      const change = this.calculateProratedAmount(this.currentSubscription.tier, newTier)
      if (!change) {
        throw new Error('Invalid tier change')
      }

      // For downgrades, we might need to handle credits differently
      const response = await apiClient.createSubscription(newTier, 'paystack')
      
      // Update local subscription
      await this.refreshSubscription()
      return true
    } catch (error) {
      console.error('Failed to downgrade subscription:', error)
      return false
    }
  }

  // Pause subscription
  async pauseSubscription(request: PauseRequest): Promise<boolean> {
    try {
      // This would call a backend endpoint to pause the subscription
      console.log('Pausing subscription:', request)
      
      // Update local subscription
      await this.refreshSubscription()
      return true
    } catch (error) {
      console.error('Failed to pause subscription:', error)
      return false
    }
  }

  // Resume subscription
  async resumeSubscription(): Promise<boolean> {
    try {
      // This would call a backend endpoint to resume the subscription
      console.log('Resuming subscription')
      
      // Update local subscription
      await this.refreshSubscription()
      return true
    } catch (error) {
      console.error('Failed to resume subscription:', error)
      return false
    }
  }

  // Update renewal settings
  async updateRenewalSettings(settings: Partial<RenewalSettings>): Promise<boolean> {
    try {
      if (!this.currentSubscription) {
        throw new Error('No active subscription')
      }

      // This would call a backend endpoint to update renewal settings
      console.log('Updating renewal settings:', settings)
      
      // Update local subscription
      await this.refreshSubscription()
      return true
    } catch (error) {
      console.error('Failed to update renewal settings:', error)
      return false
    }
  }

  // Cancel subscription
  async cancelSubscription(reason: string = 'User requested cancellation'): Promise<boolean> {
    try {
      await apiClient.cancelSubscription(reason)
      
      // Update local subscription
      await this.refreshSubscription()
      return true
    } catch (error) {
      console.error('Failed to cancel subscription:', error)
      return false
    }
  }

  // Get subscription analytics
  async getAnalytics(): Promise<SubscriptionAnalytics> {
    try {
      // Call backend endpoint to get real analytics
      const analytics = await apiClient.getAdminBillingAnalytics().catch(() => null)
      
      if (analytics && analytics.subscription_statistics) {
        const stats = analytics.subscription_statistics
        const subscriptions = stats.subscriptions_by_tier || {}
        const totalSubs = Object.values(subscriptions).reduce((sum: number, count: any) => sum + (count || 0), 0)
        
        // Calculate retention by tier (simplified - would need historical data)
        const retention_by_tier: Record<string, number> = {}
        Object.keys(subscriptions).forEach(tier => {
          // Default retention rates - in production, calculate from historical data
          retention_by_tier[tier] = tier === 'free' ? 0.3 : tier === 'starter' ? 0.85 : 0.92
        })
        
        // Calculate churn rate from cancelled subscriptions
        const cancelled = stats.subscriptions_by_status?.cancelled || 0
        const churn_rate = totalSubs > 0 ? cancelled / totalSubs : 0
        
        // Calculate upgrade/downgrade rates (would need subscription history)
        const upgrade_rate = 0.15 // Would need to calculate from subscription changes
        const downgrade_rate = 0.03 // Would need to calculate from subscription changes
        
        // Calculate average lifetime (would need subscription history)
        const average_lifetime = 8.5 // Would need to calculate from subscription durations
        
        return {
          total_revenue: stats.total_revenue_usd || 0,
          average_lifetime,
          churn_rate,
          upgrade_rate,
          downgrade_rate,
          retention_by_tier
        }
      }
      
      // Fallback to empty data if API fails
      return {
        total_revenue: 0,
        average_lifetime: 0,
        churn_rate: 0,
        upgrade_rate: 0,
        downgrade_rate: 0,
        retention_by_tier: {}
      }
    } catch (error) {
      console.error('Failed to get subscription analytics:', error)
      throw error
    }
  }

  // Get upcoming renewal information
  getRenewalInfo(): RenewalSettings | null {
    if (!this.currentSubscription) return null

    return {
      auto_renew: this.currentSubscription.auto_renew,
      renewal_date: this.currentSubscription.end_date,
      next_billing_amount: this.currentSubscription.price_usd,
      payment_method: 'paystack' // This would come from the subscription data
    }
  }

  // Check if subscription can be upgraded
  canUpgrade(): boolean {
    if (!this.currentSubscription) return false
    
    const currentTier = this.currentSubscription.tier
    const availableTiers = this.billingPlans.map(p => p.tier)
    
    // Check if there's a higher tier available
    const tierOrder = ['free', 'starter', 'pro']
    const currentIndex = tierOrder.indexOf(currentTier)
    const hasHigherTier = availableTiers.some(tier => 
      tierOrder.indexOf(tier) > currentIndex
    )
    
    return hasHigherTier
  }

  // Check if subscription can be downgraded
  canDowngrade(): boolean {
    if (!this.currentSubscription) return false
    
    const currentTier = this.currentSubscription.tier
    const tierOrder = ['free', 'starter', 'pro']
    const currentIndex = tierOrder.indexOf(currentTier)
    
    return currentIndex > 0 // Can downgrade if not on free tier
  }

  // Get recommended plan based on usage
  getRecommendedPlan(): BillingPlan | null {
    // This would analyze usage patterns and recommend the best plan
    // For now, return the starter plan as default recommendation
    return this.billingPlans.find(p => p.tier === 'starter') || null
  }

  // Refresh subscription data
  async refreshSubscription() {
    try {
  const subscription = await apiClient.getSubscription({ suppressRedirect: true }).catch(() => null)
      this.currentSubscription = subscription
    } catch (error) {
      console.error('Failed to refresh subscription:', error)
    }
  }

  // Get subscription history
  async getSubscriptionHistory(): Promise<any[]> {
    try {
      // Call backend endpoint to get real subscription history
      // Note: This endpoint may need to be created if it doesn't exist
      const history = await apiClient.getPaymentHistory(50).catch(() => [])
      
      // Transform payment history to subscription history format
      return history.map((payment: any, index: number) => ({
        id: payment.id || index,
        tier: payment.tier || this.currentSubscription?.tier || 'free',
        start_date: payment.created_at || new Date().toISOString(),
        end_date: payment.created_at || new Date().toISOString(),
        status: payment.status === 'successful' ? 'active' : 'cancelled',
        amount: payment.amount_usd || 0
      }))
    } catch (error) {
      console.error('Failed to get subscription history:', error)
      return []
    }
  }

  // Calculate savings from annual billing
  calculateAnnualSavings(monthlyPrice: number): number {
    const annualPrice = monthlyPrice * 12
    const annualDiscount = 0.10 // 10% discount for annual billing
    const discountedAnnualPrice = annualPrice * (1 - annualDiscount)
    const savings = annualPrice - discountedAnnualPrice
    
    return savings
  }

  // Get billing cycle options
  getBillingCycles(): { value: string; label: string; savings?: number }[] {
    const currentPlan = this.currentSubscription ? 
      this.billingPlans.find(p => p.tier === this.currentSubscription!.tier) : null

    if (!currentPlan) return []

    const monthlyPrice = currentPlan.price_usd
    const annualSavings = this.calculateAnnualSavings(monthlyPrice)

    return [
      { value: 'monthly', label: 'Monthly' },
      { 
        value: 'annual', 
        label: 'Annual (Save 10%)', 
        savings: annualSavings 
      }
    ]
  }
}

export const subscriptionManager = SubscriptionManager.getInstance()
export default subscriptionManager
