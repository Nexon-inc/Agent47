import { apiClient } from './api-client'

export interface CommunicationTemplate {
  id: string
  name: string
  type: 'email' | 'sms' | 'notification'
  subject?: string
  content: string
  variables: string[]
  triggers: string[]
  active: boolean
}

export interface UserEvent {
  type: 'signup' | 'login' | 'payment' | 'subscription_change' | 'password_reset' | 'support_ticket'
  user_id: string
  user_email: string
  data: Record<string, any>
  timestamp: string
}

export interface AutomatedMessage {
  id: string
  template_id: string
  user_id: string
  user_email: string
  type: 'email' | 'sms' | 'notification'
  subject?: string
  content: string
  status: 'pending' | 'sent' | 'failed'
  sent_at?: string
  created_at: string
}

class AutomatedCommunication {
  private templates: CommunicationTemplate[] = []
  private eventHandlers: Map<string, ((event: UserEvent) => void)[]> = new Map()

  constructor() {
    this.initializeTemplates()
    this.setupEventHandlers()
  }

  private initializeTemplates() {
    this.templates = [
      {
        id: 'welcome-email',
        name: 'Welcome Email',
        type: 'email',
        subject: 'Welcome to Agent47!',
        content: 'Hi {{name}}, welcome to Agent47! We\'re excited to have you on board.',
        variables: ['name'],
        triggers: ['signup'],
        active: true
      },
      {
        id: 'payment-confirmation',
        name: 'Payment Confirmation',
        type: 'email',
        subject: 'Payment Confirmed - Agent47',
        content: 'Hi {{name}}, your payment of ${{amount}} has been confirmed. Thank you!',
        variables: ['name', 'amount'],
        triggers: ['payment'],
        active: true
      },
      {
        id: 'password-reset',
        name: 'Password Reset',
        type: 'email',
        subject: 'Password Reset Request - Agent47',
        content: 'Hi {{name}}, you requested a password reset. Click here: {{reset_link}}',
        variables: ['name', 'reset_link'],
        triggers: ['password_reset'],
        active: true
      },
      {
        id: 'subscription-upgrade',
        name: 'Subscription Upgrade',
        type: 'email',
        subject: 'Subscription Upgraded - Agent47',
        content: 'Hi {{name}}, your subscription has been upgraded to {{plan}}. Enjoy the new features!',
        variables: ['name', 'plan'],
        triggers: ['subscription_change'],
        active: true
      },
      {
        id: 'support-ticket-created',
        name: 'Support Ticket Created',
        type: 'email',
        subject: 'Support Ticket #{{ticket_id}} Created',
        content: 'Hi {{name}}, your support ticket has been created. We\'ll get back to you soon.',
        variables: ['name', 'ticket_id'],
        triggers: ['support_ticket'],
        active: true
      }
    ]
  }

  private setupEventHandlers() {
    // Handle signup events
    this.on('signup', async (event) => {
      await this.sendWelcomeEmail(event)
    })

    // Handle payment events
    this.on('payment', async (event) => {
      await this.sendPaymentConfirmation(event)
    })

    // Handle password reset events
    this.on('password_reset', async (event) => {
      await this.sendPasswordResetEmail(event)
    })

    // Handle subscription changes
    this.on('subscription_change', async (event) => {
      await this.sendSubscriptionUpdate(event)
    })

    // Handle support ticket creation
    this.on('support_ticket', async (event) => {
      await this.sendSupportTicketConfirmation(event)
    })
  }

  public on(eventType: string, handler: (event: UserEvent) => void) {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, [])
    }
    this.eventHandlers.get(eventType)!.push(handler)
  }

  public emit(event: UserEvent) {
    const handlers = this.eventHandlers.get(event.type)
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(event)
        } catch (error) {
          console.error(`Error handling event ${event.type}:`, error)
        }
      })
    }
  }

  private async sendWelcomeEmail(event: UserEvent) {
    const template = this.templates.find(t => t.id === 'welcome-email')
    if (!template) return

    const content = this.replaceVariables(template.content, {
      name: event.data.name || 'User'
    })

    await this.sendMessage({
      template_id: template.id,
      user_id: event.user_id,
      user_email: event.user_email,
      type: 'email',
      subject: template.subject,
      content
    })
  }

  private async sendPaymentConfirmation(event: UserEvent) {
    const template = this.templates.find(t => t.id === 'payment-confirmation')
    if (!template) return

    const content = this.replaceVariables(template.content, {
      name: event.data.name || 'User',
      amount: event.data.amount || '0'
    })

    await this.sendMessage({
      template_id: template.id,
      user_id: event.user_id,
      user_email: event.user_email,
      type: 'email',
      subject: template.subject,
      content
    })
  }

  private async sendPasswordResetEmail(event: UserEvent) {
    const template = this.templates.find(t => t.id === 'password-reset')
    if (!template) return

    const content = this.replaceVariables(template.content, {
      name: event.data.name || 'User',
      reset_link: event.data.reset_link || '#'
    })

    await this.sendMessage({
      template_id: template.id,
      user_id: event.user_id,
      user_email: event.user_email,
      type: 'email',
      subject: template.subject,
      content
    })
  }

  private async sendSubscriptionUpdate(event: UserEvent) {
    const template = this.templates.find(t => t.id === 'subscription-upgrade')
    if (!template) return

    const content = this.replaceVariables(template.content, {
      name: event.data.name || 'User',
      plan: event.data.plan || 'Premium'
    })

    await this.sendMessage({
      template_id: template.id,
      user_id: event.user_id,
      user_email: event.user_email,
      type: 'email',
      subject: template.subject,
      content
    })
  }

  private async sendSupportTicketConfirmation(event: UserEvent) {
    const template = this.templates.find(t => t.id === 'support-ticket-created')
    if (!template) return

    const content = this.replaceVariables(template.content, {
      name: event.data.name || 'User',
      ticket_id: event.data.ticket_id || 'T-000'
    })

    await this.sendMessage({
      template_id: template.id,
      user_id: event.user_id,
      user_email: event.user_email,
      type: 'email',
      subject: template.subject,
      content
    })
  }

  private replaceVariables(content: string, variables: Record<string, string>): string {
    let result = content
    Object.entries(variables).forEach(([key, value]) => {
      result = result.replace(new RegExp(`{{${key}}}`, 'g'), value)
    })
    return result
  }

  private async sendMessage(message: Omit<AutomatedMessage, 'id' | 'status' | 'created_at'>) {
    try {
      // Call real API to send message
      const { apiClient } = await import('@/lib/api-client')
      
      // Determine sender and receiver from message metadata
      const senderId = message.metadata?.sender_agent_id || 'system'
      const receiverId = message.metadata?.receiver_agent_id || message.recipient
      const messageType = message.metadata?.message_type || 'automated'
      
      // Send via agent communication API
      const success = await apiClient.sendAgentMessage(
        senderId,
        receiverId,
        messageType,
        message.content,
        message.metadata
      )
      
      if (success) {
        const automatedMessage: AutomatedMessage = {
          ...message,
          id: Math.random().toString(36).substring(2),
          status: 'sent',
          sent_at: new Date().toISOString(),
          created_at: new Date().toISOString()
        }
        
        // Add to history
        this.messageHistory.push(automatedMessage)
        
        console.log('Message sent successfully:', automatedMessage)
        return automatedMessage
      } else {
        throw new Error('Failed to send message via API')
      }
    } catch (error) {
      console.error('Failed to send automated message:', error)
      throw error
    }
  }

  public getTemplates(): CommunicationTemplate[] {
    return this.templates
  }

  public addTemplate(template: Omit<CommunicationTemplate, 'id'>): CommunicationTemplate {
    const newTemplate: CommunicationTemplate = {
      ...template,
      id: Math.random().toString(36).substring(2)
    }
    this.templates.push(newTemplate)
    return newTemplate
  }

  public updateTemplate(id: string, updates: Partial<CommunicationTemplate>): CommunicationTemplate | null {
    const index = this.templates.findIndex(t => t.id === id)
    if (index === -1) return null

    this.templates[index] = { ...this.templates[index], ...updates }
    return this.templates[index]
  }

  public deleteTemplate(id: string): boolean {
    const index = this.templates.findIndex(t => t.id === id)
    if (index === -1) return false

    this.templates.splice(index, 1)
    return true
  }

  public triggerEvent(event: UserEvent) {
    this.emit(event)
  }
}

// Create singleton instance
export const automatedCommunication = new AutomatedCommunication()

// Export types for use in components
export type { CommunicationTemplate, UserEvent, AutomatedMessage }
