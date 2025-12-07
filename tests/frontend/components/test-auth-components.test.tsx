/**
 * Tests for Authentication Components
 */
import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useAuthStore } from '@/lib/stores/auth-store'

// Mock the auth store
jest.mock('@/lib/stores/auth-store')
const mockUseAuthStore = useAuthStore as jest.MockedFunction<typeof useAuthStore>

describe('Authentication Components', () => {
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

  describe('LoginForm Component', () => {
    it('renders login form fields', () => {
      mockUseAuthStore.mockReturnValue({
        user: null,
        isAuthenticated: false,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      const { LoginForm } = require('@/components/auth/login-form')
      render(<LoginForm />)

      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
      expect(screen.getByText('Sign In')).toBeInTheDocument()
      expect(screen.getByText('Forgot Password?')).toBeInTheDocument()
    })

    it('handles form submission', async () => {
      const mockLogin = jest.fn()
      mockUseAuthStore.mockReturnValue({
        user: null,
        isAuthenticated: false,
        login: mockLogin,
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      const { LoginForm } = require('@/components/auth/login-form')
      render(<LoginForm />)

      const emailInput = screen.getByLabelText(/email/i)
      const passwordInput = screen.getByLabelText(/password/i)
      const submitButton = screen.getByText('Sign In')

      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'password123' } })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'password123'
        })
      })
    })

    it('shows validation errors', async () => {
      mockUseAuthStore.mockReturnValue({
        user: null,
        isAuthenticated: false,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      const { LoginForm } = require('@/components/auth/login-form')
      render(<LoginForm />)

      const submitButton = screen.getByText('Sign In')
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/email is required/i)).toBeInTheDocument()
        expect(screen.getByText(/password is required/i)).toBeInTheDocument()
      })
    })

    it('handles login errors', async () => {
      const mockLogin = jest.fn().mockRejectedValue(new Error('Invalid credentials'))
      mockUseAuthStore.mockReturnValue({
        user: null,
        isAuthenticated: false,
        login: mockLogin,
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      const { LoginForm } = require('@/components/auth/login-form')
      render(<LoginForm />)

      const emailInput = screen.getByLabelText(/email/i)
      const passwordInput = screen.getByLabelText(/password/i)
      const submitButton = screen.getByText('Sign In')

      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument()
      })
    })
  })

  describe('SignupForm Component', () => {
    it('renders signup form fields', () => {
      mockUseAuthStore.mockReturnValue({
        user: null,
        isAuthenticated: false,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      const { SignupForm } = require('@/components/auth/signup-form')
      render(<SignupForm />)

      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/full name/i)).toBeInTheDocument()
      expect(screen.getByText('Create Account')).toBeInTheDocument()
    })

    it('handles form submission', async () => {
      const mockRegister = jest.fn()
      mockUseAuthStore.mockReturnValue({
        user: null,
        isAuthenticated: false,
        login: jest.fn(),
        logout: jest.fn(),
        register: mockRegister,
        updateProfile: jest.fn(),
      })

      const { SignupForm } = require('@/components/auth/signup-form')
      render(<SignupForm />)

      const emailInput = screen.getByLabelText(/email/i)
      const passwordInput = screen.getByLabelText(/password/i)
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i)
      const fullNameInput = screen.getByLabelText(/full name/i)
      const submitButton = screen.getByText('Create Account')

      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'password123' } })
      fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } })
      fireEvent.change(fullNameInput, { target: { value: 'Test User' } })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(mockRegister).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'password123',
          full_name: 'Test User'
        })
      })
    })

    it('validates password confirmation', async () => {
      mockUseAuthStore.mockReturnValue({
        user: null,
        isAuthenticated: false,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      const { SignupForm } = require('@/components/auth/signup-form')
      render(<SignupForm />)

      const passwordInput = screen.getByLabelText(/password/i)
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i)
      const submitButton = screen.getByText('Create Account')

      fireEvent.change(passwordInput, { target: { value: 'password123' } })
      fireEvent.change(confirmPasswordInput, { target: { value: 'differentpassword' } })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument()
      })
    })

    it('validates email format', async () => {
      mockUseAuthStore.mockReturnValue({
        user: null,
        isAuthenticated: false,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      const { SignupForm } = require('@/components/auth/signup-form')
      render(<SignupForm />)

      const emailInput = screen.getByLabelText(/email/i)
      const submitButton = screen.getByText('Create Account')

      fireEvent.change(emailInput, { target: { value: 'invalid-email' } })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/invalid email format/i)).toBeInTheDocument()
      })
    })
  })

  describe('ForgotPasswordForm Component', () => {
    it('renders forgot password form', () => {
      mockUseAuthStore.mockReturnValue({
        user: null,
        isAuthenticated: false,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      const { ForgotPasswordForm } = require('@/components/auth/forgot-password-form')
      render(<ForgotPasswordForm />)

      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      expect(screen.getByText('Send Reset Link')).toBeInTheDocument()
      expect(screen.getByText('Back to Login')).toBeInTheDocument()
    })

    it('handles password reset request', async () => {
      mockUseAuthStore.mockReturnValue({
        user: null,
        isAuthenticated: false,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      const { ForgotPasswordForm } = require('@/components/auth/forgot-password-form')
      render(<ForgotPasswordForm />)

      const emailInput = screen.getByLabelText(/email/i)
      const submitButton = screen.getByText('Send Reset Link')

      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/reset link sent/i)).toBeInTheDocument()
      })
    })
  })

  describe('ResetPasswordForm Component', () => {
    it('renders reset password form', () => {
      mockUseAuthStore.mockReturnValue({
        user: null,
        isAuthenticated: false,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      const { ResetPasswordForm } = require('@/components/auth/reset-password-form')
      render(<ResetPasswordForm token="reset-token-123" />)

      expect(screen.getByLabelText(/new password/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/confirm new password/i)).toBeInTheDocument()
      expect(screen.getByText('Reset Password')).toBeInTheDocument()
    })

    it('handles password reset', async () => {
      mockUseAuthStore.mockReturnValue({
        user: null,
        isAuthenticated: false,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      const { ResetPasswordForm } = require('@/components/auth/reset-password-form')
      render(<ResetPasswordForm token="reset-token-123" />)

      const newPasswordInput = screen.getByLabelText(/new password/i)
      const confirmPasswordInput = screen.getByLabelText(/confirm new password/i)
      const submitButton = screen.getByText('Reset Password')

      fireEvent.change(newPasswordInput, { target: { value: 'newpassword123' } })
      fireEvent.change(confirmPasswordInput, { target: { value: 'newpassword123' } })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/password reset successfully/i)).toBeInTheDocument()
      })
    })
  })

  describe('UserProfile Component', () => {
    it('renders user profile for authenticated user', () => {
      mockUseAuthStore.mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      const { UserProfile } = require('@/components/auth/user-profile')
      render(<UserProfile />)

      expect(screen.getByText('Test User')).toBeInTheDocument()
      expect(screen.getByText('test@example.com')).toBeInTheDocument()
      expect(screen.getByText('PRO')).toBeInTheDocument()
    })

    it('handles profile updates', async () => {
      const mockUpdateProfile = jest.fn()
      mockUseAuthStore.mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: mockUpdateProfile,
      })

      const { UserProfile } = require('@/components/auth/user-profile')
      render(<UserProfile />)

      const editButton = screen.getByText('Edit Profile')
      fireEvent.click(editButton)

      const fullNameInput = screen.getByLabelText(/full name/i)
      fireEvent.change(fullNameInput, { target: { value: 'Updated Name' } })

      const saveButton = screen.getByText('Save Changes')
      fireEvent.click(saveButton)

      await waitFor(() => {
        expect(mockUpdateProfile).toHaveBeenCalledWith({
          full_name: 'Updated Name'
        })
      })
    })

    it('handles logout', async () => {
      const mockLogout = jest.fn()
      mockUseAuthStore.mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        login: jest.fn(),
        logout: mockLogout,
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      const { UserProfile } = require('@/components/auth/user-profile')
      render(<UserProfile />)

      const logoutButton = screen.getByText('Logout')
      fireEvent.click(logoutButton)

      await waitFor(() => {
        expect(mockLogout).toHaveBeenCalledTimes(1)
      })
    })
  })

  describe('AuthGuard Component', () => {
    it('renders children for authenticated users', () => {
      mockUseAuthStore.mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      const { AuthGuard } = require('@/components/auth/auth-guard')
      render(
        <AuthGuard>
          <div>Protected Content</div>
        </AuthGuard>
      )

      expect(screen.getByText('Protected Content')).toBeInTheDocument()
    })

    it('redirects unauthenticated users', () => {
      mockUseAuthStore.mockReturnValue({
        user: null,
        isAuthenticated: false,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      const { AuthGuard } = require('@/components/auth/auth-guard')
      render(
        <AuthGuard>
          <div>Protected Content</div>
        </AuthGuard>
      )

      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
      expect(screen.getByText('Please log in to access this page')).toBeInTheDocument()
    })

    it('shows loading state', () => {
      mockUseAuthStore.mockReturnValue({
        user: null,
        isAuthenticated: false,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      const { AuthGuard } = require('@/components/auth/auth-guard')
      render(
        <AuthGuard loading={<div>Loading...</div>}>
          <div>Protected Content</div>
        </AuthGuard>
      )

      expect(screen.getByText('Loading...')).toBeInTheDocument()
    })
  })

  describe('SubscriptionStatus Component', () => {
    it('renders subscription status for pro user', () => {
      mockUseAuthStore.mockReturnValue({
        user: { ...mockUser, subscription_tier: 'pro' },
        isAuthenticated: true,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      const { SubscriptionStatus } = require('@/components/auth/subscription-status')
      render(<SubscriptionStatus />)

      expect(screen.getByText('Pro Plan')).toBeInTheDocument()
      expect(screen.getByText('Active')).toBeInTheDocument()
    })

    it('renders subscription status for starter user', () => {
      mockUseAuthStore.mockReturnValue({
        user: { ...mockUser, subscription_tier: 'starter' },
        isAuthenticated: true,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      const { SubscriptionStatus } = require('@/components/auth/subscription-status')
      render(<SubscriptionStatus />)

      expect(screen.getByText('Starter Plan')).toBeInTheDocument()
      expect(screen.getByText('Active')).toBeInTheDocument()
    })

    it('renders subscription status for free user', () => {
      mockUseAuthStore.mockReturnValue({
        user: { ...mockUser, subscription_tier: 'free' },
        isAuthenticated: true,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      const { SubscriptionStatus } = require('@/components/auth/subscription-status')
      render(<SubscriptionStatus />)

      expect(screen.getByText('Free Plan')).toBeInTheDocument()
      expect(screen.getByText('Active')).toBeInTheDocument()
    })

    it('shows upgrade button for free users', () => {
      mockUseAuthStore.mockReturnValue({
        user: { ...mockUser, subscription_tier: 'free' },
        isAuthenticated: true,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
        updateProfile: jest.fn(),
      })

      const { SubscriptionStatus } = require('@/components/auth/subscription-status')
      render(<SubscriptionStatus />)

      expect(screen.getByText('Upgrade')).toBeInTheDocument()
    })
  })
})
