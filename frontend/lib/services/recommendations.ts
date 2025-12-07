import { OnboardingData } from '@/lib/api-client'

export interface Recommendation {
  id: string
  title: string
  description: string
  category: 'tutorial' | 'workflow' | 'integration'
  priority: 'high' | 'medium' | 'low'
  reason: string
}

export class RecommendationService {
  // Generate personalized recommendations based on onboarding data
  static generateRecommendations(onboardingData: OnboardingData): Recommendation[] {
    const recommendations: Recommendation[] = []

    // Tutorial recommendations based on role and industry
    const tutorialRecommendations = this.getTutorialRecommendations(onboardingData)
    recommendations.push(...tutorialRecommendations)

    // Workflow recommendations based on goals
    const workflowRecommendations = this.getWorkflowRecommendations(onboardingData)
    recommendations.push(...workflowRecommendations)

    // Integration recommendations based on social platforms
    const integrationRecommendations = this.getIntegrationRecommendations(onboardingData)
    recommendations.push(...integrationRecommendations)

    return recommendations.sort((a, b) => {
      const priorityOrder = { high: 3, medium: 2, low: 1 }
      return priorityOrder[b.priority] - priorityOrder[a.priority]
    })
  }

  private static getTutorialRecommendations(onboardingData: OnboardingData): Recommendation[] {
    const recommendations: Recommendation[] = []
    const { profile } = onboardingData

    // Role-based tutorials
    switch (profile.role) {
      case 'influencer':
        recommendations.push({
          id: 'tut-influencer-1',
          title: 'Content Creation Mastery',
          description: 'Learn how to create engaging content that drives engagement',
          category: 'tutorial',
          priority: 'high',
          reason: 'Based on your influencer role'
        })
        break
      case 'small_business':
        recommendations.push({
          id: 'tut-business-1',
          title: 'Business Growth Strategies',
          description: 'Essential strategies for growing your small business',
          category: 'tutorial',
          priority: 'high',
          reason: 'Based on your small business role'
        })
        break
      case 'startup':
        recommendations.push({
          id: 'tut-startup-1',
          title: 'Startup Scaling Guide',
          description: 'How to scale your startup efficiently',
          category: 'tutorial',
          priority: 'high',
          reason: 'Based on your startup role'
        })
        break
      case 'enterprise':
        recommendations.push({
          id: 'tut-enterprise-1',
          title: 'Enterprise Integration',
          description: 'Advanced enterprise features and integrations',
          category: 'tutorial',
          priority: 'high',
          reason: 'Based on your enterprise role'
        })
        break
    }

    // Industry-based tutorials
    switch (profile.industry) {
      case 'technology':
        recommendations.push({
          id: 'tut-tech-1',
          title: 'Tech Industry Best Practices',
          description: 'Industry-specific strategies for technology companies',
          category: 'tutorial',
          priority: 'medium',
          reason: 'Based on your technology industry'
        })
        break
      case 'healthcare':
        recommendations.push({
          id: 'tut-healthcare-1',
          title: 'Healthcare Compliance',
          description: 'Understanding healthcare regulations and compliance',
          category: 'tutorial',
          priority: 'medium',
          reason: 'Based on your healthcare industry'
        })
        break
      case 'retail':
        recommendations.push({
          id: 'tut-retail-1',
          title: 'Retail Optimization',
          description: 'Optimize your retail operations and customer experience',
          category: 'tutorial',
          priority: 'medium',
          reason: 'Based on your retail industry'
        })
        break
    }

    return recommendations
  }

  private static getWorkflowRecommendations(onboardingData: OnboardingData): Recommendation[] {
    const recommendations: Recommendation[] = []
    const { profile } = onboardingData

    // Goal-based workflows
    if (profile.goals.includes('grow_audience')) {
      recommendations.push({
        id: 'workflow-audience-1',
        title: 'Audience Growth Workflow',
        description: 'Automated workflow to grow your audience systematically',
        category: 'workflow',
        priority: 'high',
        reason: 'Based on your goal to grow audience'
      })
    }

    if (profile.goals.includes('customer_support')) {
      recommendations.push({
        id: 'workflow-support-1',
        title: 'Customer Support Automation',
        description: 'Streamline customer support with automated responses',
        category: 'workflow',
        priority: 'high',
        reason: 'Based on your goal to improve customer support'
      })
    }

    if (profile.goals.includes('content_creation')) {
      recommendations.push({
        id: 'workflow-content-1',
        title: 'Content Creation Pipeline',
        description: 'Automated content creation and publishing workflow',
        category: 'workflow',
        priority: 'medium',
        reason: 'Based on your goal to create content'
      })
    }

    if (profile.goals.includes('lead_generation')) {
      recommendations.push({
        id: 'workflow-leads-1',
        title: 'Lead Generation Funnel',
        description: 'Automated lead generation and nurturing workflow',
        category: 'workflow',
        priority: 'high',
        reason: 'Based on your goal to generate leads'
      })
    }

    return recommendations
  }

  private static getIntegrationRecommendations(onboardingData: OnboardingData): Recommendation[] {
    const recommendations: Recommendation[] = []
    const { social } = onboardingData

    // Social platform integrations
    if (social.connectedPlatforms.includes('instagram')) {
      recommendations.push({
        id: 'integration-instagram-1',
        title: 'Instagram Integration',
        description: 'Connect and automate your Instagram presence',
        category: 'integration',
        priority: 'high',
        reason: 'Based on your Instagram connection'
      })
    }

    if (social.connectedPlatforms.includes('twitter')) {
      recommendations.push({
        id: 'integration-twitter-1',
        title: 'Twitter Integration',
        description: 'Automate your Twitter engagement and posting',
        category: 'integration',
        priority: 'high',
        reason: 'Based on your Twitter connection'
      })
    }

    if (social.connectedPlatforms.includes('linkedin')) {
      recommendations.push({
        id: 'integration-linkedin-1',
        title: 'LinkedIn Integration',
        description: 'Professional networking automation',
        category: 'integration',
        priority: 'medium',
        reason: 'Based on your LinkedIn connection'
      })
    }

    if (social.connectedPlatforms.includes('youtube')) {
      recommendations.push({
        id: 'integration-youtube-1',
        title: 'YouTube Integration',
        description: 'Video content management and optimization',
        category: 'integration',
        priority: 'medium',
        reason: 'Based on your YouTube connection'
      })
    }

    return recommendations
  }

  // Get A/B test group for user
  static getABTestGroup(userId: number): string {
    // Simple hash-based A/B test assignment
    const hash = this.hashCode(userId.toString())
    return hash % 2 === 0 ? 'A' : 'B'
  }

  // Simple hash function
  private static hashCode(str: string): number {
    let hash = 0
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i)
      hash = ((hash << 5) - hash) + char
      hash = hash & hash // Convert to 32-bit integer
    }
    return Math.abs(hash)
  }

  // Get onboarding flow based on A/B test group
  static getOnboardingFlow(abTestGroup: string): any {
    if (abTestGroup === 'A') {
      return {
        steps: ['welcome', 'profile', 'social', 'tutorials', 'workflow'],
        showProgressBar: true,
        showSkipOptions: true,
        estimatedTime: '5 minutes'
      }
    } else {
      return {
        steps: ['welcome', 'profile', 'social', 'workflow', 'tutorials'],
        showProgressBar: false,
        showSkipOptions: false,
        estimatedTime: '3 minutes'
      }
    }
  }
}
