import { apiClient } from '@/lib/api-client'
import usageTracker, { UsageMetrics, UsageAlert } from './usage-tracker'
import subscriptionManager, { SubscriptionAnalytics } from './subscription-manager'
import financialReporter, { FinancialReport } from './financial-reporter'

export interface ComprehensiveAnalytics {
  usage: {
    metrics: UsageMetrics | null
    alerts: UsageAlert[]
    trends: any[]
    health_score: number
  }
  subscriptions: {
    analytics: SubscriptionAnalytics | null
    current_subscription: any
    billing_plans: any[]
    recommendations: string[]
  }
  financial: {
    report: FinancialReport | null
    revenue_forecast: number[]
    key_metrics: {
      mrr: number
      arr: number
      churn_rate: number
      clv: number
      payback_period: number
    }
  }
  insights: {
    business_health: 'excellent' | 'good' | 'warning' | 'critical'
    top_concerns: string[]
    opportunities: string[]
    recommendations: string[]
  }
  last_updated: string
}

export interface RealTimeMetrics {
  active_users: number
  api_calls_per_minute: number
  revenue_today: number
  new_subscriptions_today: number
  churn_risk_users: number
  system_health: 'healthy' | 'warning' | 'critical'
}

class AnalyticsIntegration {
  private static instance: AnalyticsIntegration
  private updateInterval: number | null = null
  private listeners: ((analytics: ComprehensiveAnalytics) => void)[] = []
  private realTimeListeners: ((metrics: RealTimeMetrics) => void)[] = []

  private constructor() {}

  static getInstance(): AnalyticsIntegration {
    if (!AnalyticsIntegration.instance) {
      AnalyticsIntegration.instance = new AnalyticsIntegration()
    }
    return AnalyticsIntegration.instance
  }

  // Initialize the analytics integration
  async initialize(): Promise<void> {
    try {
      // Initialize all services
      await Promise.all([
        usageTracker.refresh(),
        subscriptionManager.initialize(),
        financialReporter.generateReport('monthly')
      ])

      // Start real-time monitoring
      this.startRealTimeMonitoring()

      console.log('Analytics integration initialized successfully')
    } catch (error) {
      console.error('Failed to initialize analytics integration:', error)
      throw error
    }
  }

  // Get comprehensive analytics data
  async getComprehensiveAnalytics(): Promise<ComprehensiveAnalytics> {
    try {
      // Fetch data from all services
      const [usageMetrics, usageAlerts, subscriptionAnalytics, financialReport, revenueForecast] = await Promise.all([
        Promise.resolve(usageTracker.getCurrentUsage()),
        Promise.resolve(usageTracker.getAlerts()),
        subscriptionManager.getAnalytics(),
        financialReporter.generateReport('monthly'),
        financialReporter.getRevenueForecast(12)
      ])

      // Generate insights
      const insights = this.generateInsights({
        usageMetrics,
        usageAlerts,
        subscriptionAnalytics,
        financialReport
      })

      const analytics: ComprehensiveAnalytics = {
        usage: {
          metrics: usageMetrics,
          alerts: usageAlerts,
          trends: this.generateUsageTrends(),
          health_score: this.calculateUsageHealthScore(usageMetrics, usageAlerts)
        },
        subscriptions: {
          analytics: subscriptionAnalytics,
          current_subscription: subscriptionManager.getCurrentSubscription(),
          billing_plans: subscriptionManager.getBillingPlans(),
          recommendations: this.generateSubscriptionRecommendations(subscriptionAnalytics)
        },
        financial: {
          report: financialReport,
          revenue_forecast: revenueForecast,
          key_metrics: {
            mrr: financialReport?.revenue.monthly_recurring_revenue || 0,
            arr: financialReport?.revenue.annual_recurring_revenue || 0,
            churn_rate: financialReport?.churn.overall_churn_rate || 0,
            clv: financialReport?.clv.average_clv || 0,
            payback_period: financialReport?.clv.payback_period || 0
          }
        },
        insights,
        last_updated: new Date().toISOString()
      }

      return analytics
    } catch (error) {
      console.error('Failed to get comprehensive analytics:', error)
      throw error
    }
  }

  // Get real-time metrics
  async getRealTimeMetrics(): Promise<RealTimeMetrics> {
    try {
      const [revenueData, subscriptionsData] = await Promise.all([
        apiClient.getAdminRevenue(),
        apiClient.getAdminSubscriptions()
      ])

      const usageMetrics = usageTracker.getCurrentUsage()
      const alerts = usageTracker.getAlerts()

      // Calculate real-time metrics
      const activeUsers = subscriptionsData.filter(sub => sub.status === 'active').length
      const apiCallsPerMinute = usageMetrics ? Math.floor(usageMetrics.api_calls_count / 1440) : 0 // Daily calls / minutes
      const revenueToday = revenueData.daily_revenue || 0
      const newSubscriptionsToday = subscriptionsData.filter(sub => {
        const subDate = new Date(sub.created_at)
        const today = new Date()
        return subDate.toDateString() === today.toDateString()
      }).length

      // Calculate churn risk users
      const churnRiskUsers = subscriptionsData.filter(sub => {
        const healthScore = financialReporter.calculateCustomerHealthScore(sub)
        return healthScore < 50
      }).length

      // Determine system health
      const systemHealth = this.determineSystemHealth(alerts, usageMetrics)

      const metrics: RealTimeMetrics = {
        active_users: activeUsers,
        api_calls_per_minute: apiCallsPerMinute,
        revenue_today: revenueToday,
        new_subscriptions_today: newSubscriptionsToday,
        churn_risk_users: churnRiskUsers,
        system_health: systemHealth
      }

      return metrics
    } catch (error) {
      console.error('Failed to get real-time metrics:', error)
      throw error
    }
  }

  // Generate business insights
  private generateInsights(data: {
    usageMetrics: UsageMetrics | null
    usageAlerts: UsageAlert[]
    subscriptionAnalytics: SubscriptionAnalytics | null
    financialReport: FinancialReport | null
  }): ComprehensiveAnalytics['insights'] {
    const { usageMetrics, usageAlerts, subscriptionAnalytics, financialReport } = data

    const topConcerns: string[] = []
    const opportunities: string[] = []
    const recommendations: string[] = []

    // Analyze usage concerns
    if (usageAlerts.length > 0) {
      topConcerns.push(`${usageAlerts.length} usage alerts require attention`)
    }

    if (usageMetrics && usageMetrics.api_calls_count > 8000) {
      topConcerns.push('API usage approaching limits')
    }

    // Analyze subscription concerns
    if (subscriptionAnalytics) {
      if (subscriptionAnalytics.churn_rate > 0.1) {
        topConcerns.push('High churn rate detected')
      }
      if (subscriptionAnalytics.upgrade_rate < 0.05) {
        opportunities.push('Low upgrade rate - consider upselling campaigns')
      }
    }

    // Analyze financial concerns
    if (financialReport) {
      if (financialReport.churn.overall_churn_rate > 0.08) {
        topConcerns.push('Churn rate above industry average')
      }
      if (financialReport.revenue.revenue_growth_rate < 0.05) {
        topConcerns.push('Revenue growth below target')
      }
      if (financialReport.clv.payback_period > 12) {
        topConcerns.push('Long customer payback period')
      }
    }

    // Generate recommendations
    if (topConcerns.length > 0) {
      recommendations.push('Address critical usage and churn issues immediately')
    }
    if (opportunities.length > 0) {
      recommendations.push('Implement targeted upselling and retention campaigns')
    }
    recommendations.push('Monitor system health and usage patterns closely')
    recommendations.push('Review pricing strategy and customer segmentation')

    // Determine business health
    const businessHealth = this.determineBusinessHealth(topConcerns, opportunities)

    return {
      business_health: businessHealth,
      top_concerns: topConcerns,
      opportunities: opportunities,
      recommendations: recommendations
    }
  }

  // Determine business health
  private determineBusinessHealth(concerns: string[], opportunities: string[]): 'excellent' | 'good' | 'warning' | 'critical' {
    if (concerns.length === 0 && opportunities.length > 0) return 'excellent'
    if (concerns.length <= 1) return 'good'
    if (concerns.length <= 3) return 'warning'
    return 'critical'
  }

  // Determine system health
  private determineSystemHealth(alerts: UsageAlert[], usageMetrics: UsageMetrics | null): 'healthy' | 'warning' | 'critical' {
    if (alerts.length === 0) return 'healthy'
    if (alerts.length <= 2) return 'warning'
    return 'critical'
  }

  // Calculate usage health score
  private calculateUsageHealthScore(metrics: UsageMetrics | null, alerts: UsageAlert[]): number {
    if (!metrics) return 0

    let score = 100

    // Reduce score based on alerts
    score -= alerts.length * 10

    // Reduce score based on usage limits
    const apiUsagePercent = (metrics.api_calls_count / 10000) * 100
    const storageUsagePercent = (metrics.storage_used_mb / 1000) * 100

    if (apiUsagePercent > 90) score -= 20
    else if (apiUsagePercent > 70) score -= 10

    if (storageUsagePercent > 90) score -= 20
    else if (storageUsagePercent > 70) score -= 10

    return Math.max(0, score)
  }

  // Generate usage trends
  private generateUsageTrends(): any[] {
    return Array.from({ length: 30 }, (_, i) => ({
      day: i + 1,
      api_calls: Math.floor(Math.random() * 100) + 50,
      storage: Math.floor(Math.random() * 50) + 25,
      bandwidth: Math.floor(Math.random() * 200) + 100
    }))
  }

  // Generate subscription recommendations
  private generateSubscriptionRecommendations(analytics: SubscriptionAnalytics | null): string[] {
    const recommendations: string[] = []

    if (!analytics) return recommendations

    if (analytics.churn_rate > 0.1) {
      recommendations.push('Implement customer success program to reduce churn')
    }

    if (analytics.upgrade_rate < 0.05) {
      recommendations.push('Launch targeted upselling campaigns')
    }

    if (analytics.activation_rate < 0.7) {
      recommendations.push('Improve onboarding process to increase activation')
    }

    return recommendations
  }

  // Start real-time monitoring
  private startRealTimeMonitoring(): void {
    if (this.updateInterval) {
      clearInterval(this.updateInterval)
    }

    this.updateInterval = window.setInterval(async () => {
      try {
        const metrics = await this.getRealTimeMetrics()
        this.notifyRealTimeListeners(metrics)
      } catch (error) {
        console.error('Failed to update real-time metrics:', error)
      }
    }, 60000) // Update every minute
  }

  // Subscribe to analytics updates
  subscribe(callback: (analytics: ComprehensiveAnalytics) => void): () => void {
    this.listeners.push(callback)
    return () => {
      const index = this.listeners.indexOf(callback)
      if (index > -1) {
        this.listeners.splice(index, 1)
      }
    }
  }

  // Subscribe to real-time metrics updates
  subscribeToRealTime(callback: (metrics: RealTimeMetrics) => void): () => void {
    this.realTimeListeners.push(callback)
    return () => {
      const index = this.realTimeListeners.indexOf(callback)
      if (index > -1) {
        this.realTimeListeners.splice(index, 1)
      }
    }
  }

  // Notify listeners
  private notifyListeners(analytics: ComprehensiveAnalytics): void {
    this.listeners.forEach(callback => {
      try {
        callback(analytics)
      } catch (error) {
        console.error('Error in analytics listener:', error)
      }
    })
  }

  // Notify real-time listeners
  private notifyRealTimeListeners(metrics: RealTimeMetrics): void {
    this.realTimeListeners.forEach(callback => {
      try {
        callback(metrics)
      } catch (error) {
        console.error('Error in real-time listener:', error)
      }
    })
  }

  // Refresh all data
  async refresh(): Promise<void> {
    try {
      const analytics = await this.getComprehensiveAnalytics()
      this.notifyListeners(analytics)
    } catch (error) {
      console.error('Failed to refresh analytics:', error)
      throw error
    }
  }

  // Stop monitoring
  stop(): void {
    if (this.updateInterval) {
      clearInterval(this.updateInterval)
      this.updateInterval = null
    }
  }

  // Get analytics summary for dashboard
  async getDashboardSummary(): Promise<{
    total_revenue: number
    active_users: number
    churn_rate: number
    system_health: string
    alerts_count: number
  }> {
    try {
      const analytics = await this.getComprehensiveAnalytics()
      const realTimeMetrics = await this.getRealTimeMetrics()

      return {
        total_revenue: analytics.financial.key_metrics.mrr,
        active_users: realTimeMetrics.active_users,
        churn_rate: analytics.financial.key_metrics.churn_rate,
        system_health: realTimeMetrics.system_health,
        alerts_count: analytics.usage.alerts.length
      }
    } catch (error) {
      console.error('Failed to get dashboard summary:', error)
      throw error
    }
  }
}

export const analyticsIntegration = AnalyticsIntegration.getInstance()
export default analyticsIntegration
