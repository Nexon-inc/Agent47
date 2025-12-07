/**
 * Tests for Header component
 */
import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { Header } from '@/components/header'
import { useAuthStore } from '@/lib/stores/auth-store'

// Mock the auth store
jest.mock('@/lib/stores/auth-store')
const mockUseAuthStore = useAuthStore as jest.MockedFunction<typeof useAuthStore>

describe('Header Component', () => {
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

  it('renders header with logo and navigation', () => {
    mockUseAuthStore.mockReturnValue({
      user: null,
      isAuthenticated: false,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      updateProfile: jest.fn(),
    })

    render(<Header />)
    
    expect(screen.getByText('Agent47')).toBeInTheDocument()
    expect(screen.getByText('Features')).toBeInTheDocument()
    expect(screen.getByText('Pricing')).toBeInTheDocument()
    expect(screen.getByText('Documentation')).toBeInTheDocument()
  })

  it('shows login and signup buttons when user is not authenticated', () => {
    mockUseAuthStore.mockReturnValue({
      user: null,
      isAuthenticated: false,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      updateProfile: jest.fn(),
    })

    render(<Header />)
    
    expect(screen.getByText('Login')).toBeInTheDocument()
    expect(screen.getByText('Sign Up')).toBeInTheDocument()
  })

  it('shows user menu when user is authenticated', () => {
    mockUseAuthStore.mockReturnValue({
      user: mockUser,
      isAuthenticated: true,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      updateProfile: jest.fn(),
    })

    render(<Header />)
    
    expect(screen.getByText('Test User')).toBeInTheDocument()
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Logout')).toBeInTheDocument()
  })

  it('opens mobile menu when hamburger button is clicked', () => {
    mockUseAuthStore.mockReturnValue({
      user: null,
      isAuthenticated: false,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      updateProfile: jest.fn(),
    })

    render(<Header />)
    
    const hamburgerButton = screen.getByRole('button', { name: /menu/i })
    fireEvent.click(hamburgerButton)
    
    expect(screen.getByText('Features')).toBeVisible()
  })

  it('calls logout when logout button is clicked', async () => {
    const mockLogout = jest.fn()
    mockUseAuthStore.mockReturnValue({
      user: mockUser,
      isAuthenticated: true,
      login: jest.fn(),
      logout: mockLogout,
      register: jest.fn(),
      updateProfile: jest.fn(),
    })

    render(<Header />)
    
    const logoutButton = screen.getByText('Logout')
    fireEvent.click(logoutButton)
    
    await waitFor(() => {
      expect(mockLogout).toHaveBeenCalledTimes(1)
    })
  })

  it('shows subscription tier badge for pro users', () => {
    mockUseAuthStore.mockReturnValue({
      user: { ...mockUser, subscription_tier: 'pro' },
      isAuthenticated: true,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      updateProfile: jest.fn(),
    })

    render(<Header />)
    
    expect(screen.getByText('PRO')).toBeInTheDocument()
  })

  it('shows subscription tier badge for starter users', () => {
    mockUseAuthStore.mockReturnValue({
      user: { ...mockUser, subscription_tier: 'starter' },
      isAuthenticated: true,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      updateProfile: jest.fn(),
    })

    render(<Header />)
    
    expect(screen.getByText('STARTER')).toBeInTheDocument()
  })

  it('navigates to dashboard when dashboard link is clicked', () => {
    mockUseAuthStore.mockReturnValue({
      user: mockUser,
      isAuthenticated: true,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      updateProfile: jest.fn(),
    })

    render(<Header />)
    
    const dashboardLink = screen.getByText('Dashboard')
    expect(dashboardLink.closest('a')).toHaveAttribute('href', '/dashboard')
  })

  it('navigates to pricing when pricing link is clicked', () => {
    mockUseAuthStore.mockReturnValue({
      user: null,
      isAuthenticated: false,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      updateProfile: jest.fn(),
    })

    render(<Header />)
    
    const pricingLink = screen.getByText('Pricing')
    expect(pricingLink.closest('a')).toHaveAttribute('href', '/pricing')
  })

  it('navigates to features when features link is clicked', () => {
    mockUseAuthStore.mockReturnValue({
      user: null,
      isAuthenticated: false,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      updateProfile: jest.fn(),
    })

    render(<Header />)
    
    const featuresLink = screen.getByText('Features')
    expect(featuresLink.closest('a')).toHaveAttribute('href', '/features')
  })

  it('navigates to documentation when documentation link is clicked', () => {
    mockUseAuthStore.mockReturnValue({
      user: null,
      isAuthenticated: false,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      updateProfile: jest.fn(),
    })

    render(<Header />)
    
    const docsLink = screen.getByText('Documentation')
    expect(docsLink.closest('a')).toHaveAttribute('href', '/documentation')
  })

  it('shows user avatar when user is authenticated', () => {
    mockUseAuthStore.mockReturnValue({
      user: mockUser,
      isAuthenticated: true,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      updateProfile: jest.fn(),
    })

    render(<Header />)
    
    const avatar = screen.getByRole('img', { name: /avatar/i })
    expect(avatar).toBeInTheDocument()
  })

  it('handles responsive design correctly', () => {
    mockUseAuthStore.mockReturnValue({
      user: null,
      isAuthenticated: false,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      updateProfile: jest.fn(),
    })

    render(<Header />)
    
    // Check that mobile menu button exists
    expect(screen.getByRole('button', { name: /menu/i })).toBeInTheDocument()
    
    // Check that desktop navigation exists
    expect(screen.getByText('Features')).toBeInTheDocument()
  })
})
