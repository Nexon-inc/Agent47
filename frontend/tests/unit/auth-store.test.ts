import { useAuthStore } from '@/lib/stores/auth-store';
import { apiClient } from '@/lib/api-client';

// Mock the API client
jest.mock('@/lib/api-client');

// Mock Supabase
jest.mock('@supabase/supabase-js', () => ({
  createClient: jest.fn(() => ({
    auth: {
      signUp: jest.fn(),
      signInWithPassword: jest.fn(),
      signOut: jest.fn(),
      getSession: jest.fn(),
      onAuthStateChange: jest.fn(),
      resetPasswordForEmail: jest.fn(),
      updateUser: jest.fn(),
      getUser: jest.fn()
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

describe('Auth Store', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const state = useAuthStore.getState();
      
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBeNull();
      expect(state.session).toBeNull();
    });
  });

  describe('Initialize', () => {
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

      (apiClient.getCurrentUserFromStorage as jest.Mock).mockReturnValue(mockUser);
      (apiClient.isAuthenticated as jest.Mock).mockReturnValue(true);

      useAuthStore.getState().initialize();

      const state = useAuthStore.getState();
      expect(state.user).toEqual(mockUser);
      expect(state.isAuthenticated).toBe(true);
    });

    it('should handle empty storage', () => {
      (apiClient.getCurrentUserFromStorage as jest.Mock).mockReturnValue(null);
      (apiClient.isAuthenticated as jest.Mock).mockReturnValue(false);

      useAuthStore.getState().initialize();

      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe('Signup', () => {
    it('should handle successful signup', async () => {
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

      const result = await useAuthStore.getState().signup(signupData);

      expect(result).toBe(true);
      expect(apiClient.signup).toHaveBeenCalledWith(signupData);
      
      const state = useAuthStore.getState();
      expect(state.user).toEqual(mockTokens.user);
      expect(state.isAuthenticated).toBe(true);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBeNull();
    });

    it('should handle signup errors', async () => {
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

      const result = await useAuthStore.getState().signup(signupData);

      expect(result).toBe(false);
      
      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBe('Email already exists');
    });
  });

  describe('Login', () => {
    it('should handle successful login', async () => {
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

      (apiClient.login as jest.Mock).mockResolvedValue(mockTokens);

      const loginData = {
        email: 'test@example.com',
        password: 'password123'
      };

      const result = await useAuthStore.getState().login(loginData);

      expect(result).toBe(true);
      expect(apiClient.login).toHaveBeenCalledWith(loginData);
      
      const state = useAuthStore.getState();
      expect(state.user).toEqual(mockTokens.user);
      expect(state.isAuthenticated).toBe(true);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBeNull();
    });

    it('should handle login errors', async () => {
      (apiClient.login as jest.Mock).mockRejectedValue(new Error('Invalid credentials'));

      const loginData = {
        email: 'test@example.com',
        password: 'wrongpassword'
      };

      const result = await useAuthStore.getState().login(loginData);

      expect(result).toBe(false);
      
      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBe('Invalid credentials');
    });
  });

  describe('Logout', () => {
    it('should handle successful logout', async () => {
      (apiClient.logout as jest.Mock).mockResolvedValue(undefined);

      await useAuthStore.getState().logout();

      expect(apiClient.logout).toHaveBeenCalled();
      
      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBeNull();
    });

    it('should handle logout errors gracefully', async () => {
      (apiClient.logout as jest.Mock).mockRejectedValue(new Error('Network error'));

      await useAuthStore.getState().logout();

      expect(apiClient.logout).toHaveBeenCalled();
      
      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBeNull();
    });
  });

  describe('Password Reset', () => {
    it('should handle successful password reset', async () => {
      (apiClient.resetPasswordRequest as jest.Mock).mockResolvedValue({
        message: 'Password reset email sent successfully'
      });

      const resetData = {
        email: 'test@example.com'
      };

      const result = await useAuthStore.getState().resetPassword(resetData);

      expect(result).toBe(true);
      expect(apiClient.resetPasswordRequest).toHaveBeenCalledWith(resetData);
      
      const state = useAuthStore.getState();
      expect(state.isLoading).toBe(false);
      expect(state.error).toBeNull();
    });

    it('should handle password reset errors', async () => {
      (apiClient.resetPasswordRequest as jest.Mock).mockRejectedValue(
        new Error('User not found')
      );

      const resetData = {
        email: 'nonexistent@example.com'
      };

      const result = await useAuthStore.getState().resetPassword(resetData);

      expect(result).toBe(false);
      
      const state = useAuthStore.getState();
      expect(state.isLoading).toBe(false);
      expect(state.error).toBe('User not found');
    });
  });

  describe('User Refresh', () => {
    it('should handle successful user refresh', async () => {
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

      (apiClient.getCurrentUser as jest.Mock).mockResolvedValue(mockUser);

      // Set initial authenticated state
      useAuthStore.setState({ isAuthenticated: true });

      await useAuthStore.getState().refreshUser();

      expect(apiClient.getCurrentUser).toHaveBeenCalled();
      
      const state = useAuthStore.getState();
      expect(state.user).toEqual(mockUser);
    });

    it('should handle user refresh errors', async () => {
      (apiClient.getCurrentUser as jest.Mock).mockRejectedValue(
        new Error('Unauthorized')
      );

      // Set initial authenticated state
      useAuthStore.setState({ isAuthenticated: true });

      await useAuthStore.getState().refreshUser();

      expect(apiClient.getCurrentUser).toHaveBeenCalled();
    });

    it('should not refresh user when not authenticated', async () => {
      useAuthStore.setState({ isAuthenticated: false });

      await useAuthStore.getState().refreshUser();

      expect(apiClient.getCurrentUser).not.toHaveBeenCalled();
    });
  });

  describe('Error Management', () => {
    it('should clear errors', () => {
      useAuthStore.setState({ error: 'Some error' });

      useAuthStore.getState().clearError();

      const state = useAuthStore.getState();
      expect(state.error).toBeNull();
    });
  });

  describe('Supabase Integration', () => {
    it('should initialize Supabase client', async () => {
      const mockSupabase = {
        auth: {
          getSession: jest.fn().mockResolvedValue({
            data: { session: null },
            error: null
          }),
          onAuthStateChange: jest.fn()
        }
      };

      // Mock the dynamic import
      jest.doMock('@supabase/supabase-js', () => ({
        createClient: jest.fn(() => mockSupabase)
      }));

      await useAuthStore.getState().initializeSupabase();

      expect(mockSupabase.auth.getSession).toHaveBeenCalled();
      expect(mockSupabase.auth.onAuthStateChange).toHaveBeenCalled();
    });

    it('should handle auth state changes', () => {
      const mockSession = {
        access_token: 'access-token',
        refresh_token: 'refresh-token',
        user: {
          id: '123',
          email: 'test@example.com'
        }
      };

      useAuthStore.getState().handleAuthStateChange('SIGNED_IN', mockSession);

      const state = useAuthStore.getState();
      expect(state.session).toEqual(mockSession);
      expect(state.isAuthenticated).toBe(true);
    });

    it('should handle sign out', () => {
      useAuthStore.setState({
        user: { id: 1, email: 'test@example.com' },
        isAuthenticated: true,
        session: { access_token: 'token' }
      });

      useAuthStore.getState().handleAuthStateChange('SIGNED_OUT', null);

      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(state.session).toBeNull();
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

      useAuthStore.getState().handleAuthStateChange('TOKEN_REFRESHED', mockSession);

      const state = useAuthStore.getState();
      expect(state.session).toEqual(mockSession);
    });
  });
});
