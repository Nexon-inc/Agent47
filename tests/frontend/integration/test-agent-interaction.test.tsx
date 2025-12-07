/**
 * Integration tests for agent interaction workflows
 */
import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useAgentStore } from '@/lib/stores/agent-store'
import { ariaService, claraService, ericService } from '@/lib/agent-services'
import { WebSocketClient } from '@/lib/websocket-client'

// Mock dependencies
jest.mock('@/lib/stores/agent-store')
jest.mock('@/lib/agent-services')
jest.mock('@/lib/websocket-client')

const mockUseAgentStore = useAgentStore as jest.MockedFunction<typeof useAgentStore>
const mockAriaService = ariaService as jest.Mocked<typeof ariaService>
const mockClaraService = claraService as jest.Mocked<typeof claraService>
const mockEricService = ericService as jest.Mocked<typeof ericService>
const mockWebSocketClient = WebSocketClient as jest.MockedClass<typeof WebSocketClient>

describe('Agent Interaction Integration', () => {
  const mockWebSocketInstance = {
    connect: jest.fn(),
    disconnect: jest.fn(),
    send: jest.fn(),
    on: jest.fn(),
    off: jest.fn(),
  }

  beforeEach(() => {
    jest.clearAllMocks()
    mockWebSocketClient.mockImplementation(() => mockWebSocketInstance)
  })

  describe('Aria Agent - Social Media Management', () => {
    it('completes caption generation workflow', async () => {
      mockUseAgentStore.mockReturnValue({
        selectedAgent: 'aria',
        setSelectedAgent: jest.fn(),
        agents: ['aria', 'clara', 'eric'],
        loadAgents: jest.fn(),
      })

      mockAriaService.generateCaption.mockResolvedValue({
        success: true,
        caption: '🚀 Just launched our new product! #innovation #launch #excited',
        hashtags: ['#innovation', '#launch', '#excited']
      })

      // Render Aria dashboard
      const { AriaDashboard } = require('@/app/dashboard/aria/page')
      render(<AriaDashboard />)

      // Fill out caption generation form
      fireEvent.change(screen.getByLabelText(/content/i), {
        target: { value: 'Just launched our new product!' }
      })
      fireEvent.select(screen.getByLabelText(/platform/i), {
        target: { value: 'instagram' }
      })
      fireEvent.select(screen.getByLabelText(/tone/i), {
        target: { value: 'excited' }
      })

      // Submit form
      fireEvent.click(screen.getByText('Generate Caption'))

      await waitFor(() => {
        expect(mockAriaService.generateCaption).toHaveBeenCalledWith({
          content: 'Just launched our new product!',
          platform: 'instagram',
          tone: 'excited',
          hashtags: true
        })
      })

      await waitFor(() => {
        expect(screen.getByText('🚀 Just launched our new product! #innovation #launch #excited')).toBeInTheDocument()
      })
    })

    it('handles real-time caption generation via WebSocket', async () => {
      mockUseAgentStore.mockReturnValue({
        selectedAgent: 'aria',
        setSelectedAgent: jest.fn(),
        agents: ['aria', 'clara', 'eric'],
        loadAgents: jest.fn(),
      })

      // Render Aria dashboard
      const { AriaDashboard } = require('@/app/dashboard/aria/page')
      render(<AriaDashboard />)

      // Simulate WebSocket connection
      expect(mockWebSocketInstance.connect).toHaveBeenCalled()

      // Simulate real-time caption generation
      const mockMessage = {
        type: 'caption_generated',
        data: {
          caption: 'Real-time generated caption!',
          hashtags: ['#realtime', '#ai']
        }
      }

      // Trigger WebSocket message handler
      const messageHandler = mockWebSocketInstance.on.mock.calls.find(
        call => call[0] === 'message'
      )?.[1]

      if (messageHandler) {
        messageHandler(mockMessage)
      }

      await waitFor(() => {
        expect(screen.getByText('Real-time generated caption!')).toBeInTheDocument()
      })
    })

    it('completes account analysis workflow', async () => {
      mockUseAgentStore.mockReturnValue({
        selectedAgent: 'aria',
        setSelectedAgent: jest.fn(),
        agents: ['aria', 'clara', 'eric'],
        loadAgents: jest.fn(),
      })

      mockAriaService.analyzeAccount.mockResolvedValue({
        success: true,
        analysis: {
          followers: 1000,
          engagement_rate: 0.05,
          top_posts: ['post1', 'post2', 'post3'],
          recommendations: ['Post more consistently', 'Use more hashtags']
        }
      })

      // Render Aria dashboard
      const { AriaDashboard } = require('@/app/dashboard/aria/page')
      render(<AriaDashboard />)

      // Navigate to analytics tab
      fireEvent.click(screen.getByText('Analytics'))

      // Fill out account analysis form
      fireEvent.change(screen.getByLabelText(/username/i), {
        target: { value: 'test_account' }
      })
      fireEvent.select(screen.getByLabelText(/platform/i), {
        target: { value: 'instagram' }
      })

      // Submit analysis
      fireEvent.click(screen.getByText('Analyze Account'))

      await waitFor(() => {
        expect(mockAriaService.analyzeAccount).toHaveBeenCalledWith({
          platform: 'instagram',
          username: 'test_account',
          analysis_type: 'performance'
        })
      })

      await waitFor(() => {
        expect(screen.getByText('1,000')).toBeInTheDocument() // followers
        expect(screen.getByText('5%')).toBeInTheDocument() // engagement rate
      })
    })
  })

  describe('Clara Agent - Customer Support', () => {
    it('completes customer support conversation workflow', async () => {
      mockUseAgentStore.mockReturnValue({
        selectedAgent: 'clara',
        setSelectedAgent: jest.fn(),
        agents: ['aria', 'clara', 'eric'],
        loadAgents: jest.fn(),
      })

      mockClaraService.processMessage.mockResolvedValue({
        success: true,
        response: 'I understand you need help with your account. Let me assist you with that.',
        intent: 'account_help',
        confidence: 0.95,
        suggested_actions: ['Check account status', 'Reset password']
      })

      // Render Clara dashboard
      const { ClaraDashboard } = require('@/app/dashboard/clara/page')
      render(<ClaraDashboard />)

      // Send customer message
      fireEvent.change(screen.getByLabelText(/message/i), {
        target: { value: 'I need help with my account' }
      })
      fireEvent.click(screen.getByText('Send'))

      await waitFor(() => {
        expect(mockClaraService.processMessage).toHaveBeenCalledWith({
          message: 'I need help with my account',
          context: 'customer_support'
        })
      })

      await waitFor(() => {
        expect(screen.getByText('I understand you need help with your account. Let me assist you with that.')).toBeInTheDocument()
      })
    })

    it('handles escalation to human support', async () => {
      mockUseAgentStore.mockReturnValue({
        selectedAgent: 'clara',
        setSelectedAgent: jest.fn(),
        agents: ['aria', 'clara', 'eric'],
        loadAgents: jest.fn(),
      })

      mockClaraService.escalateToHuman.mockResolvedValue({
        success: true,
        ticket_id: 'TICKET-12345',
        estimated_wait_time: '5 minutes'
      })

      // Render Clara dashboard
      const { ClaraDashboard } = require('@/app/dashboard/clara/page')
      render(<ClaraDashboard />)

      // Trigger escalation
      fireEvent.click(screen.getByText('Escalate to Human'))

      await waitFor(() => {
        expect(mockClaraService.escalateToHuman).toHaveBeenCalledWith({
          reason: 'complex_issue',
          customer_id: 'current_user'
        })
      })

      await waitFor(() => {
        expect(screen.getByText('TICKET-12345')).toBeInTheDocument()
        expect(screen.getByText('5 minutes')).toBeInTheDocument()
      })
    })
  })

  describe('Eric Agent - Sales & Marketing', () => {
    it('completes sales pitch generation workflow', async () => {
      mockUseAgentStore.mockReturnValue({
        selectedAgent: 'eric',
        setSelectedAgent: jest.fn(),
        agents: ['aria', 'clara', 'eric'],
        loadAgents: jest.fn(),
      })

      mockEricService.generateSalesPitch.mockResolvedValue({
        success: true,
        pitch: {
          subject: 'Transform Your Business with AI',
          opening: 'Hi [Name], I noticed your company is growing rapidly...',
          value_proposition: 'Our AI agents can increase your productivity by 300%',
          call_to_action: 'Schedule a demo to see how this can work for you',
          follow_up: 'I\'ll follow up in 3 days if I don\'t hear back'
        }
      })

      // Render Eric dashboard
      const { EricDashboard } = require('@/app/dashboard/eric/page')
      render(<EricDashboard />)

      // Fill out sales pitch form
      fireEvent.change(screen.getByLabelText(/lead information/i), {
        target: { value: 'Tech startup, 50 employees, looking for automation' }
      })
      fireEvent.select(screen.getByLabelText(/pitch type/i), {
        target: { value: 'cold_email' }
      })

      // Generate pitch
      fireEvent.click(screen.getByText('Generate Sales Pitch'))

      await waitFor(() => {
        expect(mockEricService.generateSalesPitch).toHaveBeenCalledWith({
          lead_info: 'Tech startup, 50 employees, looking for automation',
          pitch_type: 'cold_email',
          tone: 'professional'
        })
      })

      await waitFor(() => {
        expect(screen.getByText('Transform Your Business with AI')).toBeInTheDocument()
      })
    })

    it('completes lead analysis workflow', async () => {
      mockUseAgentStore.mockReturnValue({
        selectedAgent: 'eric',
        setSelectedAgent: jest.fn(),
        agents: ['aria', 'clara', 'eric'],
        loadAgents: jest.fn(),
      })

      mockEricService.analyzeLead.mockResolvedValue({
        success: true,
        analysis: {
          lead_score: 85,
          company_size: 'medium',
          industry: 'technology',
          pain_points: ['manual processes', 'scaling challenges'],
          recommended_approach: 'Focus on automation benefits',
          next_steps: ['Schedule demo', 'Send case studies']
        }
      })

      // Render Eric dashboard
      const { EricDashboard } = require('@/app/dashboard/eric/page')
      render(<EricDashboard />)

      // Navigate to lead analysis
      fireEvent.click(screen.getByText('Lead Analysis'))

      // Submit lead data
      fireEvent.change(screen.getByLabelText(/company name/i), {
        target: { value: 'TechCorp Inc' }
      })
      fireEvent.change(screen.getByLabelText(/website/i), {
        target: { value: 'https://techcorp.com' }
      })

      // Analyze lead
      fireEvent.click(screen.getByText('Analyze Lead'))

      await waitFor(() => {
        expect(mockEricService.analyzeLead).toHaveBeenCalledWith({
          company_name: 'TechCorp Inc',
          website: 'https://techcorp.com'
        })
      })

      await waitFor(() => {
        expect(screen.getByText('85')).toBeInTheDocument() // lead score
        expect(screen.getByText('medium')).toBeInTheDocument() // company size
      })
    })
  })

  describe('Inter-Agent Communication', () => {
    it('handles agent handoff workflow', async () => {
      mockUseAgentStore.mockReturnValue({
        selectedAgent: 'clara',
        setSelectedAgent: jest.fn(),
        agents: ['aria', 'clara', 'eric'],
        loadAgents: jest.fn(),
      })

      // Simulate Clara identifying a sales opportunity
      mockClaraService.processMessage.mockResolvedValue({
        success: true,
        response: 'I understand you\'re interested in our premium features.',
        intent: 'sales_opportunity',
        confidence: 0.90,
        suggested_handoff: 'eric'
      })

      // Render Clara dashboard
      const { ClaraDashboard } = require('@/app/dashboard/clara/page')
      render(<ClaraDashboard />)

      // Process message that triggers handoff
      fireEvent.change(screen.getByLabelText(/message/i), {
        target: { value: 'I want to upgrade to the premium plan' }
      })
      fireEvent.click(screen.getByText('Send'))

      await waitFor(() => {
        expect(screen.getByText('Transferring you to our sales specialist...')).toBeInTheDocument()
      })

      // Verify handoff to Eric
      await waitFor(() => {
        expect(mockUseAgentStore().setSelectedAgent).toHaveBeenCalledWith('eric')
      })
    })

    it('handles collaborative agent workflows', async () => {
      mockUseAgentStore.mockReturnValue({
        selectedAgent: 'aria',
        setSelectedAgent: jest.fn(),
        agents: ['aria', 'clara', 'eric'],
        loadAgents: jest.fn(),
      })

      // Simulate collaborative workflow between Aria and Eric
      mockAriaService.generateCaption.mockResolvedValue({
        success: true,
        caption: 'Check out our new product launch!',
        hashtags: ['#product', '#launch']
      })

      mockEricService.generateSalesPitch.mockResolvedValue({
        success: true,
        pitch: {
          subject: 'New Product Launch - Exclusive Early Access',
          opening: 'Hi [Name], we\'re excited to announce our new product...',
          value_proposition: 'Get early access to our revolutionary new product',
          call_to_action: 'Sign up for early access now',
          follow_up: 'Limited time offer - act fast!'
        }
      })

      // Render collaborative workflow
      const { CollaborativeWorkflow } = require('@/components/collaborative-workflow')
      render(<CollaborativeWorkflow />)

      // Start collaborative campaign
      fireEvent.click(screen.getByText('Create Collaborative Campaign'))

      await waitFor(() => {
        expect(mockAriaService.generateCaption).toHaveBeenCalled()
        expect(mockEricService.generateSalesPitch).toHaveBeenCalled()
      })

      await waitFor(() => {
        expect(screen.getByText('Campaign created successfully!')).toBeInTheDocument()
      })
    })
  })

  describe('Real-time Updates', () => {
    it('handles real-time agent status updates', async () => {
      mockUseAgentStore.mockReturnValue({
        selectedAgent: 'aria',
        setSelectedAgent: jest.fn(),
        agents: ['aria', 'clara', 'eric'],
        loadAgents: jest.fn(),
      })

      // Render agent dashboard
      const { AgentDashboard } = require('@/components/agent-dashboard')
      render(<AgentDashboard />)

      // Simulate WebSocket status update
      const statusUpdate = {
        type: 'agent_status_update',
        data: {
          agent: 'aria',
          status: 'processing',
          progress: 75,
          estimated_completion: '2 minutes'
        }
      }

      const messageHandler = mockWebSocketInstance.on.mock.calls.find(
        call => call[0] === 'message'
      )?.[1]

      if (messageHandler) {
        messageHandler(statusUpdate)
      }

      await waitFor(() => {
        expect(screen.getByText('Processing...')).toBeInTheDocument()
        expect(screen.getByText('75%')).toBeInTheDocument()
        expect(screen.getByText('2 minutes')).toBeInTheDocument()
      })
    })
  })
})
