/**
 * Tests for Dashboard Components
 */
import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useAuthStore } from '@/lib/stores/auth-store'
import { useAgentStore } from '@/lib/stores/agent-store'

// Mock the stores
jest.mock('@/lib/stores/auth-store')
jest.mock('@/lib/stores/agent-store')
const mockUseAuthStore = useAuthStore as jest.MockedFunction<typeof useAuthStore>
const mockUseAgentStore = useAgentStore as jest.MockedFunction<typeof useAgentStore>

describe('Dashboard Components', () => {
  const mockUser = {
    id: 1,
    email: 'test@example.com',
    username: 'testuser',
    full_name: 'Test User',
    is_active: true,
    is_verified: true,
    subscription_tier: 'pro'
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('AgentSelector Component', () => {
    it('renders all available agents', () => {
      mockUseAuthStore.mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      mockUseAgentStore.mockReturnValue({
        selectedAgent: null,
        setSelectedAgent: jest.fn(),
        agents: ['aria', 'clara', 'eric', 'jackie', 'joe', 'purity', 'shakes'],
        loadAgents: jest.fn(),
      })

      const { AgentSelector } = require('@/components/dashboard/agent-selector')
      render(<AgentSelector />)

      expect(screen.getByText('Aria')).toBeInTheDocument()
      expect(screen.getByText('Clara')).toBeInTheDocument()
      expect(screen.getByText('Eric')).toBeInTheDocument()
      expect(screen.getByText('Jackie')).toBeInTheDocument()
      expect(screen.getByText('Joe')).toBeInTheDocument()
      expect(screen.getByText('Purity')).toBeInTheDocument()
      expect(screen.getByText('Shakes')).toBeInTheDocument()
    })

    it('handles agent selection', async () => {
      const mockSetSelectedAgent = jest.fn()
      
      mockUseAuthStore.mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      mockUseAgentStore.mockReturnValue({
        selectedAgent: null,
        setSelectedAgent: mockSetSelectedAgent,
        agents: ['aria', 'clara', 'eric'],
        loadAgents: jest.fn(),
      })

      const { AgentSelector } = require('@/components/dashboard/agent-selector')
      render(<AgentSelector />)

      const ariaButton = screen.getByText('Aria')
      fireEvent.click(ariaButton)

      await waitFor(() => {
        expect(mockSetSelectedAgent).toHaveBeenCalledWith('aria')
      })
    })

    it('shows selected agent state', () => {
      mockUseAuthStore.mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      mockUseAgentStore.mockReturnValue({
        selectedAgent: 'aria',
        setSelectedAgent: jest.fn(),
        agents: ['aria', 'clara', 'eric'],
        loadAgents: jest.fn(),
      })

      const { AgentSelector } = require('@/components/dashboard/agent-selector')
      render(<AgentSelector />)

      const ariaButton = screen.getByText('Aria')
      expect(ariaButton).toHaveClass('selected')
    })
  })

  describe('AgentDashboard Component', () => {
    it('renders Aria dashboard when Aria is selected', () => {
      mockUseAuthStore.mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      mockUseAgentStore.mockReturnValue({
        selectedAgent: 'aria',
        setSelectedAgent: jest.fn(),
        agents: ['aria', 'clara', 'eric'],
        loadAgents: jest.fn(),
      })

      const { AgentDashboard } = require('@/components/dashboard/agent-dashboard')
      render(<AgentDashboard />)

      expect(screen.getByText('Social Media Management')).toBeInTheDocument()
      expect(screen.getByText('Content Generation')).toBeInTheDocument()
      expect(screen.getByText('Analytics')).toBeInTheDocument()
    })

    it('renders Clara dashboard when Clara is selected', () => {
      mockUseAuthStore.mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      mockUseAgentStore.mockReturnValue({
        selectedAgent: 'clara',
        setSelectedAgent: jest.fn(),
        agents: ['aria', 'clara', 'eric'],
        loadAgents: jest.fn(),
      })

      const { AgentDashboard } = require('@/components/dashboard/agent-dashboard')
      render(<AgentDashboard />)

      expect(screen.getByText('Customer Support')).toBeInTheDocument()
      expect(screen.getByText('Chat Management')).toBeInTheDocument()
      expect(screen.getByText('Knowledge Base')).toBeInTheDocument()
    })

    it('renders Eric dashboard when Eric is selected', () => {
      mockUseAuthStore.mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      mockUseAgentStore.mockReturnValue({
        selectedAgent: 'eric',
        setSelectedAgent: jest.fn(),
        agents: ['aria', 'clara', 'eric'],
        loadAgents: jest.fn(),
      })

      const { AgentDashboard } = require('@/components/dashboard/agent-dashboard')
      render(<AgentDashboard />)

      expect(screen.getByText('Sales & Marketing')).toBeInTheDocument()
      expect(screen.getByText('Lead Management')).toBeInTheDocument()
      expect(screen.getByText('Campaigns')).toBeInTheDocument()
    })

    it('renders Jackie dashboard when Jackie is selected', () => {
      mockUseAuthStore.mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      mockUseAgentStore.mockReturnValue({
        selectedAgent: 'jackie',
        setSelectedAgent: jest.fn(),
        agents: ['aria', 'clara', 'eric', 'jackie'],
        loadAgents: jest.fn(),
      })

      const { AgentDashboard } = require('@/components/dashboard/agent-dashboard')
      render(<AgentDashboard />)

      expect(screen.getByText('Development & Code')).toBeInTheDocument()
      expect(screen.getByText('Code Generation')).toBeInTheDocument()
      expect(screen.getByText('Architecture')).toBeInTheDocument()
    })

    it('renders Joe dashboard when Joe is selected', () => {
      mockUseAuthStore.mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      mockUseAgentStore.mockReturnValue({
        selectedAgent: 'joe',
        setSelectedAgent: jest.fn(),
        agents: ['aria', 'clara', 'eric', 'joe'],
        loadAgents: jest.fn(),
      })

      const { AgentDashboard } = require('@/components/dashboard/agent-dashboard')
      render(<AgentDashboard />)

      expect(screen.getByText('Research & Analytics')).toBeInTheDocument()
      expect(screen.getByText('Market Research')).toBeInTheDocument()
      expect(screen.getByText('Data Analysis')).toBeInTheDocument()
    })

    it('renders Purity dashboard when Purity is selected', () => {
      mockUseAuthStore.mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      mockUseAgentStore.mockReturnValue({
        selectedAgent: 'purity',
        setSelectedAgent: jest.fn(),
        agents: ['aria', 'clara', 'eric', 'purity'],
        loadAgents: jest.fn(),
      })

      const { AgentDashboard } = require('@/components/dashboard/agent-dashboard')
      render(<AgentDashboard />)

      expect(screen.getByText('Business Strategy')).toBeInTheDocument()
      expect(screen.getByText('Business Ideas')).toBeInTheDocument()
      expect(screen.getByText('Financial Planning')).toBeInTheDocument()
    })

    it('renders Shakes dashboard when Shakes is selected', () => {
      mockUseAuthStore.mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      mockUseAgentStore.mockReturnValue({
        selectedAgent: 'shakes',
        setSelectedAgent: jest.fn(),
        agents: ['aria', 'clara', 'eric', 'shakes'],
        loadAgents: jest.fn(),
      })

      const { AgentDashboard } = require('@/components/dashboard/agent-dashboard')
      render(<AgentDashboard />)

      expect(screen.getByText('Content & Marketing')).toBeInTheDocument()
      expect(screen.getByText('Content Creation')).toBeInTheDocument()
      expect(screen.getByText('SEO Optimization')).toBeInTheDocument()
    })

    it('shows no agent selected state', () => {
      mockUseAuthStore.mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      mockUseAgentStore.mockReturnValue({
        selectedAgent: null,
        setSelectedAgent: jest.fn(),
        agents: ['aria', 'clara', 'eric'],
        loadAgents: jest.fn(),
      })

      const { AgentDashboard } = require('@/components/dashboard/agent-dashboard')
      render(<AgentDashboard />)

      expect(screen.getByText('Select an Agent')).toBeInTheDocument()
      expect(screen.getByText('Choose an AI agent to get started')).toBeInTheDocument()
    })
  })

  describe('AgentChat Component', () => {
    it('renders chat interface for selected agent', () => {
      mockUseAuthStore.mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      mockUseAgentStore.mockReturnValue({
        selectedAgent: 'aria',
        setSelectedAgent: jest.fn(),
        agents: ['aria', 'clara', 'eric'],
        loadAgents: jest.fn(),
      })

      const { AgentChat } = require('@/components/dashboard/agent-chat')
      render(<AgentChat />)

      expect(screen.getByText('Chat with Aria')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Type your message...')).toBeInTheDocument()
      expect(screen.getByText('Send')).toBeInTheDocument()
    })

    it('handles message sending', async () => {
      mockUseAuthStore.mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      mockUseAgentStore.mockReturnValue({
        selectedAgent: 'aria',
        setSelectedAgent: jest.fn(),
        agents: ['aria', 'clara', 'eric'],
        loadAgents: jest.fn(),
      })

      const { AgentChat } = require('@/components/dashboard/agent-chat')
      render(<AgentChat />)

      const messageInput = screen.getByPlaceholderText('Type your message...')
      const sendButton = screen.getByText('Send')

      fireEvent.change(messageInput, { target: { value: 'Hello Aria!' } })
      fireEvent.click(sendButton)

      await waitFor(() => {
        expect(screen.getByText('Hello Aria!')).toBeInTheDocument()
      })
    })

    it('shows typing indicator', async () => {
      mockUseAuthStore.mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      mockUseAgentStore.mockReturnValue({
        selectedAgent: 'aria',
        setSelectedAgent: jest.fn(),
        agents: ['aria', 'clara', 'eric'],
        loadAgents: jest.fn(),
      })

      const { AgentChat } = require('@/components/dashboard/agent-chat')
      render(<AgentChat />)

      const messageInput = screen.getByPlaceholderText('Type your message...')
      const sendButton = screen.getByText('Send')

      fireEvent.change(messageInput, { target: { value: 'Hello Aria!' } })
      fireEvent.click(sendButton)

      await waitFor(() => {
        expect(screen.getByText('Aria is typing...')).toBeInTheDocument()
      })
    })
  })

  describe('AgentAnalytics Component', () => {
    it('renders analytics dashboard', () => {
      mockUseAuthStore.mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      mockUseAgentStore.mockReturnValue({
        selectedAgent: 'aria',
        setSelectedAgent: jest.fn(),
        agents: ['aria', 'clara', 'eric'],
        loadAgents: jest.fn(),
      })

      const { AgentAnalytics } = require('@/components/dashboard/agent-analytics')
      render(<AgentAnalytics />)

      expect(screen.getByText('Analytics Dashboard')).toBeInTheDocument()
      expect(screen.getByText('Usage Statistics')).toBeInTheDocument()
      expect(screen.getByText('Performance Metrics')).toBeInTheDocument()
    })

    it('displays usage statistics', () => {
      mockUseAuthStore.mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      mockUseAgentStore.mockReturnValue({
        selectedAgent: 'aria',
        setSelectedAgent: jest.fn(),
        agents: ['aria', 'clara', 'eric'],
        loadAgents: jest.fn(),
      })

      const { AgentAnalytics } = require('@/components/dashboard/agent-analytics')
      render(<AgentAnalytics />)

      expect(screen.getByText('Total Requests')).toBeInTheDocument()
      expect(screen.getByText('Success Rate')).toBeInTheDocument()
      expect(screen.getByText('Average Response Time')).toBeInTheDocument()
    })

    it('shows performance metrics', () => {
      mockUseAuthStore.mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      mockUseAgentStore.mockReturnValue({
        selectedAgent: 'aria',
        setSelectedAgent: jest.fn(),
        agents: ['aria', 'clara', 'eric'],
        loadAgents: jest.fn(),
      })

      const { AgentAnalytics } = require('@/components/dashboard/agent-analytics')
      render(<AgentAnalytics />)

      expect(screen.getByText('Response Time Trends')).toBeInTheDocument()
      expect(screen.getByText('Error Rate Trends')).toBeInTheDocument()
      expect(screen.getByText('Usage Patterns')).toBeInTheDocument()
    })
  })

  describe('AgentSettings Component', () => {
    it('renders agent settings', () => {
      mockUseAuthStore.mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      mockUseAgentStore.mockReturnValue({
        selectedAgent: 'aria',
        setSelectedAgent: jest.fn(),
        agents: ['aria', 'clara', 'eric'],
        loadAgents: jest.fn(),
      })

      const { AgentSettings } = require('@/components/dashboard/agent-settings')
      render(<AgentSettings />)

      expect(screen.getByText('Agent Settings')).toBeInTheDocument()
      expect(screen.getByText('General Settings')).toBeInTheDocument()
      expect(screen.getByText('Advanced Settings')).toBeInTheDocument()
    })

    it('handles setting changes', async () => {
      mockUseAuthStore.mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      mockUseAgentStore.mockReturnValue({
        selectedAgent: 'aria',
        setSelectedAgent: jest.fn(),
        agents: ['aria', 'clara', 'eric'],
        loadAgents: jest.fn(),
      })

      const { AgentSettings } = require('@/components/dashboard/agent-settings')
      render(<AgentSettings />)

      const autoResponseToggle = screen.getByLabelText('Auto Response')
      fireEvent.click(autoResponseToggle)

      await waitFor(() => {
        expect(autoResponseToggle).toBeChecked()
      })
    })

    it('saves settings', async () => {
      mockUseAuthStore.mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      mockUseAgentStore.mockReturnValue({
        selectedAgent: 'aria',
        setSelectedAgent: jest.fn(),
        agents: ['aria', 'clara', 'eric'],
        loadAgents: jest.fn(),
      })

      const { AgentSettings } = require('@/components/dashboard/agent-settings')
      render(<AgentSettings />)

      const saveButton = screen.getByText('Save Settings')
      fireEvent.click(saveButton)

      await waitFor(() => {
        expect(screen.getByText('Settings saved successfully')).toBeInTheDocument()
      })
    })
  })
})
