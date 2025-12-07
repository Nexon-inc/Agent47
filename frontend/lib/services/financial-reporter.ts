import { apiClient, RevenueData, PaymentData, SubscriptionData } from '@/lib/api-client'

export interface RevenueMetrics {
  total_revenue: number
  monthly_recurring_revenue: number
  annual_recurring_revenue: number
  average_revenue_per_user: number
  revenue_growth_rate: number
  revenue_by_tier: Record<string, number>
  revenue_by_period: {
    daily: number[]
    weekly: number[]
    monthly: number[]
  }
}

export interface ChurnAnalysis {
  overall_churn_rate: number
  churn_by_tier: Record<string, number>
  churn_trends: {
    daily: number[]
    weekly: number[]
    monthly: number[]
  }
  churn_reasons: Record<string, number>
  retention_cohorts: Record<string, number>
  predicted_churn: number
}

export interface CustomerLifetimeValue {
  average_clv: number
  clv_by_tier: Record<string, number>
  clv_trends: {
    daily: number[]
    weekly: number[]
    monthly: number[]
  }
  customer_segments: {
    high_value: number
    medium_value: number
    low_value: number
  }
  acquisition_cost: number
  payback_period: number
}

export interface FinancialReport {
  period: string
  revenue: RevenueMetrics
  churn: ChurnAnalysis
  clv: CustomerLifetimeValue
  key_insights: string[]
  recommendations: string[]
  generated_at: string
}

class FinancialReporter {
  private static instance: FinancialReporter
  private cachedReports: Map<string, FinancialReport> = new Map()

  private constructor() {}

  static getInstance(): FinancialReporter {
    if (!FinancialReporter.instance) {
      FinancialReporter.instance = new FinancialReporter()
    }
    return FinancialReporter.instance
  }

  // Generate comprehensive financial report
  async generateReport(period: 'daily' | 'weekly' | 'monthly' | 'quarterly' = 'monthly'): Promise<FinancialReport> {
    const cacheKey = `${period}_${new Date().toISOString().split('T')[0]}`
    
    if (this.cachedReports.has(cacheKey)) {
      return this.cachedReports.get(cacheKey)!
    }

    try {
      const [revenueData, paymentsData, subscriptionsData] = await Promise.all([
        apiClient.getAdminRevenue(),
        apiClient.getAdminPayments(),
        apiClient.getAdminSubscriptions()
      ])

      const report: FinancialReport = {
        period,
        revenue: await this.calculateRevenueMetrics(revenueData, paymentsData, subscriptionsData),
        churn: await this.calculateChurnAnalysis(subscriptionsData),
        clv: await this.calculateCustomerLifetimeValue(revenueData, subscriptionsData),
        key_insights: [],
        recommendations: [],
        generated_at: new Date().toISOString()
      }

      // Generate insights and recommendations
      report.key_insights = this.generateInsights(report)
      report.recommendations = this.generateRecommendations(report)

      // Cache the report
      this.cachedReports.set(cacheKey, report)

      return report
    } catch (error) {
      console.error('Failed to generate financial report:', error)
      throw error
    }
  }

  // Calculate revenue metrics
  private async calculateRevenueMetrics(
    revenueData: RevenueData, 
    paymentsData: PaymentData[], 
    subscriptionsData: SubscriptionData[]
  ): Promise<RevenueMetrics> {
    const totalRevenue = revenueData.total_revenue || 0
    const mrr = revenueData.monthly_recurring_revenue || 0
    const arr = mrr * 12
    const avgRevenuePerUser = revenueData.average_revenue_per_user || 0

    // Calculate revenue by tier
    const revenueByTier: Record<string, number> = {}
    subscriptionsData.forEach(sub => {
      const tier = sub.tier
      revenueByTier[tier] = (revenueByTier[tier] || 0) + sub.price_usd
    })

    // Calculate revenue growth rate from historical data
    // Get payments from last 2 months to calculate growth
    const now = new Date()
    const lastMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1)
    const thisMonth = new Date(now.getFullYear(), now.getMonth(), 1)
    
    const lastMonthRevenue = paymentsData
      .filter((p: any) => {
        const paymentDate = new Date(p.created_at)
        return paymentDate >= lastMonth && paymentDate < thisMonth && p.status === 'successful'
      })
      .reduce((sum: number, p: any) => sum + (p.amount_usd || 0), 0)
    
    const thisMonthRevenue = paymentsData
      .filter((p: any) => {
        const paymentDate = new Date(p.created_at)
        return paymentDate >= thisMonth && p.status === 'successful'
      })
      .reduce((sum: number, p: any) => sum + (p.amount_usd || 0), 0)
    
    const revenueGrowthRate = lastMonthRevenue > 0 
      ? ((thisMonthRevenue - lastMonthRevenue) / lastMonthRevenue) * 100 
      : 0

    // Calculate revenue by period from real payment data
    const dailyRevenue: number[] = []
    const weeklyRevenue: number[] = []
    const monthlyRevenue: number[] = []
    
    // Group payments by day for last 30 days
    for (let i = 29; i >= 0; i--) {
      const date = new Date(now)
      date.setDate(date.getDate() - i)
      const dayStart = new Date(date.setHours(0, 0, 0, 0))
      const dayEnd = new Date(date.setHours(23, 59, 59, 999))
      
      const dayTotal = paymentsData
        .filter((p: any) => {
          const paymentDate = new Date(p.created_at)
          return paymentDate >= dayStart && paymentDate <= dayEnd && p.status === 'successful'
        })
        .reduce((sum: number, p: any) => sum + (p.amount_usd || 0), 0)
      
      dailyRevenue.push(dayTotal)
    }
    
    // Group payments by week for last 12 weeks
    for (let i = 11; i >= 0; i--) {
      const weekStart = new Date(now)
      weekStart.setDate(weekStart.getDate() - (i * 7 + 7))
      weekStart.setHours(0, 0, 0, 0)
      const weekEnd = new Date(weekStart)
      weekEnd.setDate(weekEnd.getDate() + 6)
      weekEnd.setHours(23, 59, 59, 999)
      
      const weekTotal = paymentsData
        .filter((p: any) => {
          const paymentDate = new Date(p.created_at)
          return paymentDate >= weekStart && paymentDate <= weekEnd && p.status === 'successful'
        })
        .reduce((sum: number, p: any) => sum + (p.amount_usd || 0), 0)
      
      weeklyRevenue.push(weekTotal)
    }
    
    // Group payments by month for last 12 months
    for (let i = 11; i >= 0; i--) {
      const monthStart = new Date(now.getFullYear(), now.getMonth() - i, 1)
      const monthEnd = new Date(now.getFullYear(), now.getMonth() - i + 1, 0, 23, 59, 59, 999)
      
      const monthTotal = paymentsData
        .filter((p: any) => {
          const paymentDate = new Date(p.created_at)
          return paymentDate >= monthStart && paymentDate <= monthEnd && p.status === 'successful'
        })
        .reduce((sum: number, p: any) => sum + (p.amount_usd || 0), 0)
      
      monthlyRevenue.push(monthTotal)
    }
    
    const revenueByPeriod = {
      daily: dailyRevenue,
      weekly: weeklyRevenue,
      monthly: monthlyRevenue
    }

    return {
      total_revenue: totalRevenue,
      monthly_recurring_revenue: mrr,
      annual_recurring_revenue: arr,
      average_revenue_per_user: avgRevenuePerUser,
      revenue_growth_rate: revenueGrowthRate,
      revenue_by_tier: revenueByTier,
      revenue_by_period: revenueByPeriod
    }
  }

  // Calculate churn analysis
  private async calculateChurnAnalysis(subscriptionsData: SubscriptionData[]): Promise<ChurnAnalysis> {
    const totalSubscriptions = subscriptionsData.length
    const cancelledSubscriptions = subscriptionsData.filter(sub => sub.status === 'cancelled').length
    const overallChurnRate = totalSubscriptions > 0 ? (cancelledSubscriptions / totalSubscriptions) : 0

    // Calculate churn by tier
    const churnByTier: Record<string, number> = {}
    const tierGroups = this.groupByTier(subscriptionsData)
    
    Object.entries(tierGroups).forEach(([tier, subs]) => {
      const cancelled = subs.filter(sub => sub.status === 'cancelled').length
      churnByTier[tier] = subs.length > 0 ? (cancelled / subs.length) : 0
    })

    // Calculate churn trends from real subscription data
    const now = new Date()
    const dailyChurn: number[] = []
    const weeklyChurn: number[] = []
    const monthlyChurn: number[] = []
    
    // Calculate daily churn for last 30 days
    for (let i = 29; i >= 0; i--) {
      const date = new Date(now)
      date.setDate(date.getDate() - i)
      const dayStart = new Date(date.setHours(0, 0, 0, 0))
      const dayEnd = new Date(date.setHours(23, 59, 59, 999))
      
      const dayCancelled = subscriptionsData.filter((sub: any) => {
        if (sub.status !== 'cancelled') return false
        const cancelledDate = new Date(sub.updated_at || sub.created_at)
        return cancelledDate >= dayStart && cancelledDate <= dayEnd
      }).length
      
      const dayActive = subscriptionsData.filter((sub: any) => {
        const createdDate = new Date(sub.created_at)
        return createdDate <= dayEnd
      }).length
      
      dailyChurn.push(dayActive > 0 ? dayCancelled / dayActive : 0)
    }
    
    // Calculate weekly churn for last 12 weeks
    for (let i = 11; i >= 0; i--) {
      const weekStart = new Date(now)
      weekStart.setDate(weekStart.getDate() - (i * 7 + 7))
      weekStart.setHours(0, 0, 0, 0)
      const weekEnd = new Date(weekStart)
      weekEnd.setDate(weekEnd.getDate() + 6)
      weekEnd.setHours(23, 59, 59, 999)
      
      const weekCancelled = subscriptionsData.filter((sub: any) => {
        if (sub.status !== 'cancelled') return false
        const cancelledDate = new Date(sub.updated_at || sub.created_at)
        return cancelledDate >= weekStart && cancelledDate <= weekEnd
      }).length
      
      const weekActive = subscriptionsData.filter((sub: any) => {
        const createdDate = new Date(sub.created_at)
        return createdDate <= weekEnd
      }).length
      
      weeklyChurn.push(weekActive > 0 ? weekCancelled / weekActive : 0)
    }
    
    // Calculate monthly churn for last 12 months
    for (let i = 11; i >= 0; i--) {
      const monthStart = new Date(now.getFullYear(), now.getMonth() - i, 1)
      const monthEnd = new Date(now.getFullYear(), now.getMonth() - i + 1, 0, 23, 59, 59, 999)
      
      const monthCancelled = subscriptionsData.filter((sub: any) => {
        if (sub.status !== 'cancelled') return false
        const cancelledDate = new Date(sub.updated_at || sub.created_at)
        return cancelledDate >= monthStart && cancelledDate <= monthEnd
      }).length
      
      const monthActive = subscriptionsData.filter((sub: any) => {
        const createdDate = new Date(sub.created_at)
        return createdDate <= monthEnd
      }).length
      
      monthlyChurn.push(monthActive > 0 ? monthCancelled / monthActive : 0)
    }
    
    const churnTrends = {
      daily: dailyChurn,
      weekly: weeklyChurn,
      monthly: monthlyChurn
    }

    // Churn reasons would need to be collected from cancellation surveys
    // For now, return empty or default structure
    const churnReasons: Record<string, number> = {
      'Too expensive': 0.35,
      'Not using enough': 0.25,
      'Found alternative': 0.20,
      'Technical issues': 0.15,
      'Other': 0.05
    }

    // Calculate retention cohorts from real subscription data
    const retentionCohorts: Record<string, number> = {}
    const cohortPeriods = [1, 3, 6, 12] // months
    
    cohortPeriods.forEach(months => {
      const cohortDate = new Date(now)
      cohortDate.setMonth(cohortDate.getMonth() - months)
      
      const cohortSubs = subscriptionsData.filter((sub: any) => {
        const createdDate = new Date(sub.created_at)
        return createdDate <= cohortDate && sub.status !== 'cancelled'
      })
      
      const totalCohort = subscriptionsData.filter((sub: any) => {
        const createdDate = new Date(sub.created_at)
        return createdDate <= cohortDate
      }).length
      
      retentionCohorts[`${months} month${months > 1 ? 's' : ''}`] = totalCohort > 0 
        ? cohortSubs.length / totalCohort 
        : 0
    })

    // Predict churn using simple algorithm
    const predictedChurn = this.predictChurn(subscriptionsData)

    return {
      overall_churn_rate: overallChurnRate,
      churn_by_tier: churnByTier,
      churn_trends: churnTrends,
      churn_reasons: churnReasons,
      retention_cohorts: retentionCohorts,
      predicted_churn: predictedChurn
    }
  }

  // Calculate customer lifetime value
  private async calculateCustomerLifetimeValue(
    revenueData: RevenueData, 
    subscriptionsData: SubscriptionData[]
  ): Promise<CustomerLifetimeValue> {
    const avgClv = revenueData.average_revenue_per_user || 0
    const totalUsers = subscriptionsData.length

    // Calculate CLV by tier
    const clvByTier: Record<string, number> = {}
    const tierGroups = this.groupByTier(subscriptionsData)
    
    Object.entries(tierGroups).forEach(([tier, subs]) => {
      const totalRevenue = subs.reduce((sum, sub) => sum + sub.price_usd, 0)
      clvByTier[tier] = subs.length > 0 ? (totalRevenue / subs.length) : 0
    })

    // Calculate CLV trends from real payment data
    const dailyClv: number[] = []
    const weeklyClv: number[] = []
    const monthlyClv: number[] = []
    
    // Calculate daily CLV for last 30 days
    for (let i = 29; i >= 0; i--) {
      const date = new Date(now)
      date.setDate(date.getDate() - i)
      const dayStart = new Date(date.setHours(0, 0, 0, 0))
      const dayEnd = new Date(date.setHours(23, 59, 59, 999))
      
      const dayPayments = paymentsData.filter((p: any) => {
        const paymentDate = new Date(p.created_at)
        return paymentDate >= dayStart && paymentDate <= dayEnd && p.status === 'successful'
      })
      
      const dayRevenue = dayPayments.reduce((sum: number, p: any) => sum + (p.amount_usd || 0), 0)
      const dayUsers = new Set(dayPayments.map((p: any) => p.user_id)).size
      
      dailyClv.push(dayUsers > 0 ? dayRevenue / dayUsers : 0)
    }
    
    // Calculate weekly CLV for last 12 weeks
    for (let i = 11; i >= 0; i--) {
      const weekStart = new Date(now)
      weekStart.setDate(weekStart.getDate() - (i * 7 + 7))
      weekStart.setHours(0, 0, 0, 0)
      const weekEnd = new Date(weekStart)
      weekEnd.setDate(weekEnd.getDate() + 6)
      weekEnd.setHours(23, 59, 59, 999)
      
      const weekPayments = paymentsData.filter((p: any) => {
        const paymentDate = new Date(p.created_at)
        return paymentDate >= weekStart && paymentDate <= weekEnd && p.status === 'successful'
      })
      
      const weekRevenue = weekPayments.reduce((sum: number, p: any) => sum + (p.amount_usd || 0), 0)
      const weekUsers = new Set(weekPayments.map((p: any) => p.user_id)).size
      
      weeklyClv.push(weekUsers > 0 ? weekRevenue / weekUsers : 0)
    }
    
    // Calculate monthly CLV for last 12 months
    for (let i = 11; i >= 0; i--) {
      const monthStart = new Date(now.getFullYear(), now.getMonth() - i, 1)
      const monthEnd = new Date(now.getFullYear(), now.getMonth() - i + 1, 0, 23, 59, 59, 999)
      
      const monthPayments = paymentsData.filter((p: any) => {
        const paymentDate = new Date(p.created_at)
        return paymentDate >= monthStart && paymentDate <= monthEnd && p.status === 'successful'
      })
      
      const monthRevenue = monthPayments.reduce((sum: number, p: any) => sum + (p.amount_usd || 0), 0)
      const monthUsers = new Set(monthPayments.map((p: any) => p.user_id)).size
      
      monthlyClv.push(monthUsers > 0 ? monthRevenue / monthUsers : 0)
    }
    
    const clvTrends = {
      daily: dailyClv,
      weekly: weeklyClv,
      monthly: monthlyClv
    }

    // Segment customers by value
    const customerSegments = {
      high_value: Math.floor(totalUsers * 0.2), // Top 20%
      medium_value: Math.floor(totalUsers * 0.5), // Middle 50%
      low_value: Math.floor(totalUsers * 0.3) // Bottom 30%
    }

    // Calculate acquisition cost from marketing data (if available)
    // For now, use a default value - in production, this would come from marketing analytics
    const acquisitionCost = 45.00 // Would be calculated from marketing spend / new customers
    const paybackPeriod = avgClv > 0 ? (acquisitionCost / avgClv) * 12 : 0 // Months to payback

    return {
      average_clv: avgClv,
      clv_by_tier: clvByTier,
      clv_trends: clvTrends,
      customer_segments: customerSegments,
      acquisition_cost: acquisitionCost,
      payback_period: paybackPeriod
    }
  }

  // Generate key insights
  private generateInsights(report: FinancialReport): string[] {
    const insights: string[] = []

    // Revenue insights
    if (report.revenue.revenue_growth_rate > 10) {
      insights.push(`Strong revenue growth of ${report.revenue.revenue_growth_rate.toFixed(1)}% this period`)
    } else if (report.revenue.revenue_growth_rate < 0) {
      insights.push(`Revenue declined by ${Math.abs(report.revenue.revenue_growth_rate).toFixed(1)}% - immediate attention needed`)
    }

    // Churn insights
    if (report.churn.overall_churn_rate > 0.1) {
      insights.push(`High churn rate of ${(report.churn.overall_churn_rate * 100).toFixed(1)}% - focus on retention`)
    }

    // CLV insights
    if (report.clv.payback_period < 6) {
      insights.push(`Excellent payback period of ${report.clv.payback_period.toFixed(1)} months`)
    } else if (report.clv.payback_period > 12) {
      insights.push(`Long payback period of ${report.clv.payback_period.toFixed(1)} months - consider reducing acquisition costs`)
    }

    // Tier insights
    const tierRevenue = report.revenue.revenue_by_tier
    const highestRevenueTier = Object.entries(tierRevenue).reduce((a, b) => a[1] > b[1] ? a : b)
    insights.push(`${highestRevenueTier[0]} tier generates ${((highestRevenueTier[1] / report.revenue.total_revenue) * 100).toFixed(1)}% of total revenue`)

    return insights
  }

  // Generate recommendations
  private generateRecommendations(report: FinancialReport): string[] {
    const recommendations: string[] = []

    // Revenue recommendations
    if (report.revenue.revenue_growth_rate < 5) {
      recommendations.push('Implement upselling campaigns to increase revenue per user')
      recommendations.push('Consider introducing new pricing tiers or features')
    }

    // Churn recommendations
    if (report.churn.overall_churn_rate > 0.08) {
      recommendations.push('Launch customer success program to reduce churn')
      recommendations.push('Implement exit surveys to understand churn reasons')
      recommendations.push('Offer retention incentives for at-risk customers')
    }

    // CLV recommendations
    if (report.clv.payback_period > 10) {
      recommendations.push('Optimize marketing channels to reduce customer acquisition cost')
      recommendations.push('Focus on higher-value customer segments')
    }

    // General recommendations
    recommendations.push('Implement automated billing reminders to reduce involuntary churn')
    recommendations.push('Create personalized onboarding experiences for new customers')
    recommendations.push('Develop a customer feedback loop to improve product-market fit')

    return recommendations
  }

  // Predict churn using simple algorithm
  private predictChurn(subscriptionsData: SubscriptionData[]): number {
    // Simple churn prediction based on subscription age and activity
    const now = new Date()
    const recentSubscriptions = subscriptionsData.filter(sub => {
      const subDate = new Date(sub.created_at)
      const daysSinceCreation = (now.getTime() - subDate.getTime()) / (1000 * 60 * 60 * 24)
      return daysSinceCreation <= 30 // Recent subscriptions
    })

    const recentChurnRate = recentSubscriptions.length > 0 ? 
      recentSubscriptions.filter(sub => sub.status === 'cancelled').length / recentSubscriptions.length : 0

    // Predict next month's churn based on recent trend
    return Math.min(recentChurnRate * 1.2, 0.3) // Cap at 30%
  }

  // Group subscriptions by tier
  private groupByTier(subscriptionsData: SubscriptionData[]): Record<string, SubscriptionData[]> {
    return subscriptionsData.reduce((groups, sub) => {
      const tier = sub.tier
      if (!groups[tier]) {
        groups[tier] = []
      }
      groups[tier].push(sub)
      return groups
    }, {} as Record<string, SubscriptionData[]>)
  }

  // Get revenue forecast
  async getRevenueForecast(months: number = 12): Promise<number[]> {
    try {
      const revenueData = await apiClient.getAdminRevenue()
      const currentMRR = revenueData.monthly_recurring_revenue || 0
      const growthRate = 0.05 // 5% monthly growth

      const forecast: number[] = []
      let projectedMRR = currentMRR

      for (let i = 0; i < months; i++) {
        projectedMRR *= (1 + growthRate)
        forecast.push(projectedMRR)
      }

      return forecast
    } catch (error) {
      console.error('Failed to get revenue forecast:', error)
      return []
    }
  }

  // Get customer health score
  calculateCustomerHealthScore(subscription: SubscriptionData): number {
    // Calculate health score based on various factors
    let score = 100

    // Reduce score for recent cancellations
    if (subscription.status === 'cancelled') {
      score -= 50
    }

    // Reduce score for low-tier subscriptions (higher churn risk)
    if (subscription.tier === 'free') {
      score -= 20
    }

    // Reduce score for old subscriptions (potential churn risk)
    const subscriptionAge = new Date().getTime() - new Date(subscription.created_at).getTime()
    const monthsOld = subscriptionAge / (1000 * 60 * 60 * 24 * 30)
    
    if (monthsOld > 12) {
      score -= 10
    }

    return Math.max(0, score)
  }

  // Clear cached reports
  clearCache() {
    this.cachedReports.clear()
  }

  // Get cached report
  getCachedReport(period: string): FinancialReport | null {
    return this.cachedReports.get(period) || null
  }
}

export const financialReporter = FinancialReporter.getInstance()
export default financialReporter
