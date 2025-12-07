/**
 * Tests for Pricing component
 */
import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { Pricing } from '@/components/pricing'
import { useAuthStore } from '@/lib/stores/auth-store'

// Mock the auth store
jest.mock('@/lib/stores/auth-store')
const mockUseAuthStore = useAuthStore as jest.MockedFunction<typeof useAuthStore>

describe('Pricing Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders pricing section with all tiers', () => {
    mockUseAuthStore.mockReturnValue({
      user: null,
      isAuthenticated: false,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      updateProfile: jest.fn(),
    })

    render(<Pricing />)
    
    expect(screen.getByText('Free')).toBeInTheDocument()
    expect(screen.getByText('Starter')).toBeInTheDocument()
    expect(screen.getByText('Pro')).toBeInTheDocument()
  })

  it('displays correct pricing for each tier', () => {
    mockUseAuthStore.mockReturnValue({
      user: null,
      isAuthenticated: false,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      updateProfile: jest.fn(),
    })

    render(<Pricing />)
    
    expect(screen.getByText('$0')).toBeInTheDocument()
    expect(screen.getByText('$29')).toBeInTheDocument()
    expect(screen.getByText('$99')).toBeInTheDocument()
  })

  it('shows yearly pricing with discount', () => {
    mockUseAuthStore.mockReturnValue({
      user: null,
      isAuthenticated: false,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      updateProfile: jest.fn(),
    })

    render(<Pricing />)
    
    // Toggle to yearly pricing
    const yearlyToggle = screen.getByText('Yearly')
    fireEvent.click(yearlyToggle)
    
    expect(screen.getByText('$26.10')).toBeInTheDocument() // $29 * 0.9
    expect(screen.getByText('$89.10')).toBeInTheDocument() // $99 * 0.9
    expect(screen.getByText('10% off')).toBeInTheDocument()
  })

  it('displays feature lists for each tier', () => {
    mockUseAuthStore.mockReturnValue({
      user: null,
      isAuthenticated: false,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      updateProfile: jest.fn(),
    })

    render(<Pricing />)
    
    // Check for common features
    expect(screen.getAllByText(/AI Agents/i)).toHaveLength(3)
    expect(screen.getAllByText(/API Access/i)).toHaveLength(3)
    expect(screen.getAllByText(/Support/i)).toHaveLength(3)
  })

  it('shows different agent limits for each tier', () => {
    mockUseAuthStore.mockReturnValue({
      user: null,
      isAuthenticated: false,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      updateProfile: jest.fn(),
    })

    render(<Pricing />)
    
    expect(screen.getByText('1 Agent')).toBeInTheDocument()
    expect(screen.getByText('3 Agents')).toBeInTheDocument()
    expect(screen.getByText('All 7 Agents')).toBeInTheDocument()
  })

  it('displays inter-agent communication availability', () => {
    mockUseAuthStore.mockReturnValue({
      user: null,
      isAuthenticated: false,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      updateProfile: jest.fn(),
    })

    render(<Pricing />)
    
    expect(screen.getByText('Inter-Agent Communication')).toBeInTheDocument()
    expect(screen.getByText('Not Available')).toBeInTheDocument()
    expect(screen.getByText('Available')).toBeInTheDocument()
  })

  it('shows get started button for free tier', () => {
    mockUseAuthStore.mockReturnValue({
      user: null,
      isAuthenticated: false,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      updateProfile: jest.fn(),
    })

    render(<Pricing />)
    
    const freeButtons = screen.getAllByText('Get Started')
    expect(freeButtons[0]).toBeInTheDocument()
    expect(freeButtons[0].closest('a')).toHaveAttribute('href', '/auth/signup')
  })

  it('shows upgrade button for paid tiers', () => {
    mockUseAuthStore.mockReturnValue({
      user: null,
      isAuthenticated: false,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      updateProfile: jest.fn(),
    })

    render(<Pricing />)
    
    const upgradeButtons = screen.getAllByText('Upgrade')
    expect(upgradeButtons).toHaveLength(2)
    upgradeButtons.forEach(button => {
      expect(button.closest('a')).toHaveAttribute('href', '/checkout')
    })
  })

  it('highlights recommended tier', () => {
    mockUseAuthStore.mockReturnValue({
      user: null,
      isAuthenticated: false,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      updateProfile: jest.fn(),
    })

    render(<Pricing />)
    
    expect(screen.getByText('Most Popular')).toBeInTheDocument()
  })

  it('shows current plan for authenticated users', () => {
    const mockUser = {
      id: 1,
      email: 'test@example.com',
      username: 'testuser',
      full_name: 'Test User',
      is_active: true,
      is_verified: true,
      subscription_tier: 'pro'
    }

    mockUseAuthStore.mockReturnValue({
      user: mockUser,
      isAuthenticated: true,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      updateProfile: jest.fn(),
    })

    render(<Pricing />)
    
    expect(screen.getByText('Current Plan')).toBeInTheDocument()
  })

  it('handles tier switching correctly', () => {
    mockUseAuthStore.mockReturnValue({
      user: null,
      isAuthenticated: false,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      updateProfile: jest.fn(),
    })

    render(<Pricing />)
    
    // Switch to yearly
    const yearlyToggle = screen.getByText('Yearly')
    fireEvent.click(yearlyToggle)
    
    expect(screen.getByText('$26.10')).toBeInTheDocument()
    
    // Switch back to monthly
    const monthlyToggle = screen.getByText('Monthly')
    fireEvent.click(monthlyToggle)
    
    expect(screen.getByText('$29')).toBeInTheDocument()
  })

  it('displays feature comparison table', () => {
    mockUseAuthStore.mockReturnValue({
      user: null,
      isAuthenticated: false,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      updateProfile: jest.fn(),
    })

    render(<Pricing />)
    
    // Check for feature comparison
    expect(screen.getByText('Feature Comparison')).toBeInTheDocument()
    expect(screen.getByText('Free')).toBeInTheDocument()
    expect(screen.getByText('Starter')).toBeInTheDocument()
    expect(screen.getByText('Pro')).toBeInTheDocument()
  })

  it('shows FAQ section', () => {
    mockUseAuthStore.mockReturnValue({
      user: null,
      isAuthenticated: false,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      updateProfile: jest.fn(),
    })

    render(<Pricing />)
    
    expect(screen.getByText('Frequently Asked Questions')).toBeInTheDocument()
    expect(screen.getByText('Can I change my plan anytime?')).toBeInTheDocument()
  })

  it('handles FAQ accordion interactions', () => {
    mockUseAuthStore.mockReturnValue({
      user: null,
      isAuthenticated: false,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      updateProfile: jest.fn(),
    })

    render(<Pricing />)
    
    const faqQuestion = screen.getByText('Can I change my plan anytime?')
    fireEvent.click(faqQuestion)
    
    expect(screen.getByText(/Yes, you can upgrade or downgrade your plan at any time/i)).toBeInTheDocument()
  })

  it('shows enterprise contact option', () => {
    mockUseAuthStore.mockReturnValue({
      user: null,
      isAuthenticated: false,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      updateProfile: jest.fn(),
    })

    render(<Pricing />)
    
    expect(screen.getByText('Need a custom solution?')).toBeInTheDocument()
    expect(screen.getByText('Contact Sales')).toBeInTheDocument()
  })

  it('displays money-back guarantee', () => {
    mockUseAuthStore.mockReturnValue({
      user: null,
      isAuthenticated: false,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      updateProfile: jest.fn(),
    })

    render(<Pricing />)
    
    expect(screen.getByText(/30-day money-back guarantee/i)).toBeInTheDocument()
  })

  it('shows usage limits for each tier', () => {
    mockUseAuthStore.mockReturnValue({
      user: null,
      isAuthenticated: false,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      updateProfile: jest.fn(),
    })

    render(<Pricing />)
    
    expect(screen.getByText('100 requests/month')).toBeInTheDocument()
    expect(screen.getByText('1,000 requests/month')).toBeInTheDocument()
    expect(screen.getByText('Unlimited requests')).toBeInTheDocument()
  })
})
