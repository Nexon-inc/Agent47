import { apiClient, UsageData } from '@/lib/api-client'

export interface UsageMetrics {
  api_calls_count: number
  storage_used_mb: number
  active_agents: number
  agent_usage: Record<string, any>
  bandwidth_used_mb: number
  database_queries: number
  file_uploads: number
  integrations_used: string[]
}

export interface UsageAlert {
  type: 'warning' | 'critical' | 'limit_reached'
  message: string
  metric: string
  current: number
  limit: number
  percentage: number
}

export interface UsageReport {
  daily: UsageMetrics
  weekly: UsageMetrics
  monthly: UsageMetrics
  alerts: UsageAlert[]
  trends: {
    api_calls_trend: number
    storage_trend: number
    agent_usage_trend: number
  }
}

class UsageTracker {
  private static instance: UsageTracker
  private currentUsage: UsageMetrics | null = null
  private alerts: UsageAlert[] = []
  private updateInterval: number | null = null
  private listeners: ((usage: UsageMetrics) => void)[] = []
  private alertListeners: ((alerts: UsageAlert[]) => void)[] = []

  private constructor() {
    this.startTracking()
  }

  static getInstance(): UsageTracker {
    if (!UsageTracker.instance) {
      UsageTracker.instance = new UsageTracker()
    }
    return UsageTracker.instance
  }

  // Start real-time usage tracking
  private startTracking() {
    // Update usage every 5 minutes
    this.updateInterval = setInterval(() => {
      this.updateUsage()
    }, 5 * 60 * 1000)

    // Initial update
    this.updateUsage()
  }

  // Update current usage from API
  private async updateUsage() {
    try {
      const usageData = await apiClient.getUserUsage()
      this.currentUsage = this.transformUsageData(usageData)
      this.checkAlerts()
      this.notifyListeners()
    } catch (error) {
      console.error('Failed to update usage:', error)
    }
  }

  // Transform API usage data to internal format
  private transformUsageData(usageData: UsageData): UsageMetrics {
    return {
      api_calls_count: usageData.api_calls_count,
      storage_used_mb: usageData.storage_used_mb,
      active_agents: usageData.agent_usage?.active_agents || 0,
      agent_usage: usageData.agent_usage || {},
      bandwidth_used_mb: usageData.agent_usage?.bandwidth_used_mb || 0,
      database_queries: usageData.agent_usage?.database_queries || 0,
      file_uploads: usageData.agent_usage?.file_uploads || 0,
      integrations_used: usageData.agent_usage?.integrations_used || []
    }
  }

  // Check for usage alerts
  private checkAlerts() {
    if (!this.currentUsage) return

    this.alerts = []
    const subscription = this.getCurrentSubscription()

    if (!subscription) return

    // API calls alert
    const apiLimit = subscription.features?.api_rate_limits?.requests_per_hour || 1000
    const apiPercentage = (this.currentUsage.api_calls_count / apiLimit) * 100
    
    if (apiPercentage >= 90) {
      this.alerts.push({
        type: 'critical',
        message: 'API call limit nearly reached',
        metric: 'api_calls',
        current: this.currentUsage.api_calls_count,
        limit: apiLimit,
        percentage: apiPercentage
      })
    } else if (apiPercentage >= 75) {
      this.alerts.push({
        type: 'warning',
        message: 'API usage is high',
        metric: 'api_calls',
        current: this.currentUsage.api_calls_count,
        limit: apiLimit,
        percentage: apiPercentage
      })
    }

    // Storage alert
    const storageLimit = subscription.features?.storage_limit_mb || 1000
    const storagePercentage = (this.currentUsage.storage_used_mb / storageLimit) * 100
    
    if (storagePercentage >= 90) {
      this.alerts.push({
        type: 'critical',
        message: 'Storage limit nearly reached',
        metric: 'storage',
        current: this.currentUsage.storage_used_mb,
        limit: storageLimit,
        percentage: storagePercentage
      })
    } else if (storagePercentage >= 75) {
      this.alerts.push({
        type: 'warning',
        message: 'Storage usage is high',
        metric: 'storage',
        current: this.currentUsage.storage_used_mb,
        limit: storageLimit,
        percentage: storagePercentage
      })
    }

    // Agent usage alert
    const agentLimit = subscription.features?.agents?.max_count || 3
    const agentPercentage = (this.currentUsage.active_agents / agentLimit) * 100
    
    if (agentPercentage >= 90) {
      this.alerts.push({
        type: 'critical',
        message: 'Agent limit nearly reached',
        metric: 'agents',
        current: this.currentUsage.active_agents,
        limit: agentLimit,
        percentage: agentPercentage
      })
    }

    this.notifyAlertListeners()
  }

  // Get current subscription (mock - in real app, get from store)
  private getCurrentSubscription() {
    // This would typically come from the billing store
    return {
      features: {
        api_rate_limits: { requests_per_hour: 1000 },
        storage_limit_mb: 1000,
        agents: { max_count: 3 }
      }
    }
  }

  // Get current usage
  getCurrentUsage(): UsageMetrics | null {
    return this.currentUsage
  }

  // Get current alerts
  getAlerts(): UsageAlert[] {
    return this.alerts
  }

  // Get usage percentage for a metric
  getUsagePercentage(metric: keyof UsageMetrics): number {
    if (!this.currentUsage) return 0

    const subscription = this.getCurrentSubscription()
    if (!subscription) return 0

    switch (metric) {
      case 'api_calls_count':
        const apiLimit = subscription.features?.api_rate_limits?.requests_per_hour || 1000
        return (this.currentUsage.api_calls_count / apiLimit) * 100
      
      case 'storage_used_mb':
        const storageLimit = subscription.features?.storage_limit_mb || 1000
        return (this.currentUsage.storage_used_mb / storageLimit) * 100
      
      case 'active_agents':
        const agentLimit = subscription.features?.agents?.max_count || 3
        return (this.currentUsage.active_agents / agentLimit) * 100
      
      default:
        return 0
    }
  }

  // Generate usage report
  async generateReport(): Promise<UsageReport> {
    const currentUsage = this.getCurrentUsage()
    
    if (!currentUsage) {
      throw new Error('No usage data available')
    }

    // In a real app, this would fetch historical data from the API
    const daily = { ...currentUsage }
    const weekly = { ...currentUsage }
    const monthly = { ...currentUsage }

    return {
      daily,
      weekly,
      monthly,
      alerts: this.alerts,
      trends: {
        api_calls_trend: 5.2, // Mock trend data
        storage_trend: -2.1,
        agent_usage_trend: 12.5
      }
    }
  }

  // Track a specific usage event
  async trackEvent(event: string, data: any) {
    try {
      // In a real app, this would send usage events to the backend
      console.log('Usage event:', event, data)
      
      // Update local usage immediately for responsive UI
      if (this.currentUsage) {
        switch (event) {
          case 'api_call':
            this.currentUsage.api_calls_count++
            break
          case 'file_upload':
            this.currentUsage.file_uploads++
            this.currentUsage.storage_used_mb += data.size_mb || 0
            break
          case 'agent_created':
            this.currentUsage.active_agents++
            break
        }
        
        this.checkAlerts()
        this.notifyListeners()
      }
    } catch (error) {
      console.error('Failed to track usage event:', error)
    }
  }

  // Subscribe to usage updates
  subscribe(callback: (usage: UsageMetrics) => void) {
    this.listeners.push(callback)
    
    // Return unsubscribe function
    return () => {
      const index = this.listeners.indexOf(callback)
      if (index > -1) {
        this.listeners.splice(index, 1)
      }
    }
  }

  // Subscribe to alert updates
  subscribeToAlerts(callback: (alerts: UsageAlert[]) => void) {
    this.alertListeners.push(callback)
    
    // Return unsubscribe function
    return () => {
      const index = this.alertListeners.indexOf(callback)
      if (index > -1) {
        this.alertListeners.splice(index, 1)
      }
    }
  }

  // Notify listeners of usage updates
  private notifyListeners() {
    if (this.currentUsage) {
      this.listeners.forEach(callback => callback(this.currentUsage!))
    }
  }

  // Notify listeners of alert updates
  private notifyAlertListeners() {
    this.alertListeners.forEach(callback => callback(this.alerts))
  }

  // Stop tracking
  stop() {
    if (this.updateInterval) {
      clearInterval(this.updateInterval)
      this.updateInterval = null
    }
  }

  // Force refresh usage data
  async refresh() {
    await this.updateUsage()
  }
}

export const usageTracker = UsageTracker.getInstance()
export default usageTracker
