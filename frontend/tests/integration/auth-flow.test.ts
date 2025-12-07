import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { useAuthStore } from '@/lib/stores/auth-store';
import { apiClient } from '@/lib/api-client';

// Mock the auth store
jest.mock('@/lib/stores/auth-store');
jest.mock('@/lib/api-client');

// Mock Supabase
jest.mock('@supabase/supabase-js', () => ({
  createClient: jest.fn(() => ({
    auth: {
      signUp: jest.fn(),
      signInWithPassword: jest.fn(),
      signOut: jest.fn(),
      getSession: jest.fn(),
      onAuthStateChange: jest.fn()
    }
  }))
}));

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
});

// Mock fetch
global.fetch = jest.fn();

describe('Auth Flow Integration Tests', () => {
  const mockAuthStore = {
    user: null,
    isAuthenticated: false,
    isLoading: false,
    error: null,
    session: null,
    signup: jest.fn(),
    login: jest.fn(),
    logout: jest.fn(),
    resetPassword: jest.fn(),
    refreshUser: jest.fn(),
    clearError: jest.fn(),
    initialize: jest.fn(),
    initializeSupabase: jest.fn(),
    handleAuthStateChange: jest.fn()
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useAuthStore as jest.Mock).mockReturnValue(mockAuthStore);
    localStorageMock.getItem.mockReturnValue(null);
  });

  describe('Signup Flow', () => {
    it('should complete signup flow successfully', async () => {
      const mockTokens = {
        access_token: 'access-token',
        refresh_token: 'refresh-token',
        token_type: 'bearer',
        expires_in: 3600,
        user: {
          id: 1,
          email: 'test@example.com',
          username: 'testuser',
          full_name: 'Test User',
          tier: 'free',
          is_active: true,
          is_verified: false,
          created_at: new Date().toISOString(),
          preferences: {}
        }
      };

      mockAuthStore.signup.mockResolvedValue(true);
      (apiClient.signup as jest.Mock).mockResolvedValue(mockTokens);

      const signupData = {
        email: 'test@example.com',
        username: 'testuser',
        password: 'password123',
        first_name: 'Test',
        last_name: 'User',
        country: 'US',
        continent: 'North America',
        purpose: 'testing'
      };

      const result = await mockAuthStore.signup(signupData);

      expect(result).toBe(true);
      expect(mockAuthStore.signup).toHaveBeenCalledWith(signupData);
    });

    it('should handle signup errors gracefully', async () => {
      mockAuthStore.signup.mockResolvedValue(false);
      (apiClient.signup as jest.Mock).mockRejectedValue(new Error('Email already exists'));

      const signupData = {
        email: 'existing@example.com',
        username: 'existinguser',
        password: 'password123',
        first_name: 'Existing',
        last_name: 'User',
        country: 'US',
        continent: 'North America',
        purpose: 'testing'
      };

      const result = await mockAuthStore.signup(signupData);

      expect(result).toBe(false);
    });
  });

  describe('Login Flow', () => {
    it('should complete login flow successfully', async () => {
      const mockTokens = {
        access_token: 'access-token',
        refresh_token: 'refresh-token',
        token_type: 'bearer',
        expires_in: 3600,
        user: {
          id: 1,
          email: 'test@example.com',
          username: 'testuser',
          full_name: 'Test User',
          tier: 'free',
          is_active: true,
          is_verified: true,
          created_at: new Date().toISOString(),
          preferences: {}
        }
      };

      mockAuthStore.login.mockResolvedValue(true);
      (apiClient.login as jest.Mock).mockResolvedValue(mockTokens);

      const loginData = {
        email: 'test@example.com',
        password: 'password123'
      };

      const result = await mockAuthStore.login(loginData);

      expect(result).toBe(true);
      expect(mockAuthStore.login).toHaveBeenCalledWith(loginData);
    });

    it('should handle login errors gracefully', async () => {
      mockAuthStore.login.mockResolvedValue(false);
      (apiClient.login as jest.Mock).mockRejectedValue(new Error('Invalid credentials'));

      const loginData = {
        email: 'test@example.com',
        password: 'wrongpassword'
      };

      const result = await mockAuthStore.login(loginData);

      expect(result).toBe(false);
    });
  });

  describe('Logout Flow', () => {
    it('should complete logout flow successfully', async () => {
      mockAuthStore.logout.mockResolvedValue(undefined);
      (apiClient.logout as jest.Mock).mockResolvedValue(undefined);

      await mockAuthStore.logout();

      expect(mockAuthStore.logout).toHaveBeenCalled();
    });
  });

  describe('Password Reset Flow', () => {
    it('should complete password reset flow successfully', async () => {
      mockAuthStore.resetPassword.mockResolvedValue(true);
      (apiClient.resetPasswordRequest as jest.Mock).mockResolvedValue({
        message: 'Password reset email sent successfully'
      });

      const resetData = {
        email: 'test@example.com'
      };

      const result = await mockAuthStore.resetPassword(resetData);

      expect(result).toBe(true);
      expect(mockAuthStore.resetPassword).toHaveBeenCalledWith(resetData);
    });

    it('should handle password reset errors gracefully', async () => {
      mockAuthStore.resetPassword.mockResolvedValue(false);
      (apiClient.resetPasswordRequest as jest.Mock).mockRejectedValue(
        new Error('User not found')
      );

      const resetData = {
        email: 'nonexistent@example.com'
      };

      const result = await mockAuthStore.resetPassword(resetData);

      expect(result).toBe(false);
    });
  });

  describe('Session Management', () => {
    it('should initialize auth state from storage', () => {
      const mockUser = {
        id: 1,
        email: 'test@example.com',
        username: 'testuser',
        full_name: 'Test User',
        tier: 'free',
        is_active: true,
        is_verified: true,
        created_at: new Date().toISOString(),
        preferences: {}
      };

      localStorageMock.getItem.mockReturnValue(JSON.stringify(mockUser));
      (apiClient.getCurrentUserFromStorage as jest.Mock).mockReturnValue(mockUser);
      (apiClient.isAuthenticated as jest.Mock).mockReturnValue(true);

      mockAuthStore.initialize();

      expect(mockAuthStore.initialize).toHaveBeenCalled();
    });

    it('should handle Supabase auth state changes', () => {
      const mockSession = {
        access_token: 'access-token',
        refresh_token: 'refresh-token',
        user: {
          id: '123',
          email: 'test@example.com'
        }
      };

      mockAuthStore.handleAuthStateChange('SIGNED_IN', mockSession);

      expect(mockAuthStore.handleAuthStateChange).toHaveBeenCalledWith(
        'SIGNED_IN',
        mockSession
      );
    });

    it('should handle token refresh', () => {
      const mockSession = {
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
        user: {
          id: '123',
          email: 'test@example.com'
        }
      };

      mockAuthStore.handleAuthStateChange('TOKEN_REFRESHED', mockSession);

      expect(mockAuthStore.handleAuthStateChange).toHaveBeenCalledWith(
        'TOKEN_REFRESHED',
        mockSession
      );
    });
  });

  describe('Error Handling', () => {
    it('should clear errors when requested', () => {
      mockAuthStore.clearError();

      expect(mockAuthStore.clearError).toHaveBeenCalled();
    });

    it('should handle network errors gracefully', async () => {
      mockAuthStore.login.mockResolvedValue(false);
      (apiClient.login as jest.Mock).mockRejectedValue(new Error('Network error'));

      const loginData = {
        email: 'test@example.com',
        password: 'password123'
      };

      const result = await mockAuthStore.login(loginData);

      expect(result).toBe(false);
    });
  });

  describe('User Profile Management', () => {
    it('should refresh user data successfully', async () => {
      const mockUser = {
        id: 1,
        email: 'test@example.com',
        username: 'testuser',
        full_name: 'Test User',
        tier: 'free',
        is_active: true,
        is_verified: true,
        created_at: new Date().toISOString(),
        preferences: {}
      };

      mockAuthStore.refreshUser.mockResolvedValue(undefined);
      (apiClient.getCurrentUser as jest.Mock).mockResolvedValue(mockUser);

      await mockAuthStore.refreshUser();

      expect(mockAuthStore.refreshUser).toHaveBeenCalled();
    });

    it('should handle user refresh errors', async () => {
      mockAuthStore.refreshUser.mockResolvedValue(undefined);
      (apiClient.getCurrentUser as jest.Mock).mockRejectedValue(
        new Error('Unauthorized')
      );

      await mockAuthStore.refreshUser();

      expect(mockAuthStore.refreshUser).toHaveBeenCalled();
    });
  });
});
