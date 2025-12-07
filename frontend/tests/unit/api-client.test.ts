import { apiClient } from '@/lib/api-client';

// Mock Supabase
jest.mock('@supabase/supabase-js', () => ({
  createClient: jest.fn(() => ({
    auth: {
      signUp: jest.fn(),
      signInWithPassword: jest.fn(),
      signOut: jest.fn(),
      resetPasswordForEmail: jest.fn(),
      updateUser: jest.fn(),
      getUser: jest.fn(),
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

describe('API Client', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
  });

  describe('Authentication', () => {
    it('should signup with Supabase when available', async () => {
      const mockSupabase = {
        auth: {
          signUp: jest.fn().mockResolvedValue({
            data: {
              user: { id: '123', email: 'test@example.com' },
              session: { access_token: 'token', refresh_token: 'refresh' }
            },
            error: null
          })
        }
      };

      // Mock the dynamic import
      jest.doMock('@supabase/supabase-js', () => ({
        createClient: jest.fn(() => mockSupabase)
      }));

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

      const result = await apiClient.signup(signupData);

      expect(result).toHaveProperty('access_token');
      expect(result).toHaveProperty('refresh_token');
      expect(result).toHaveProperty('user');
      expect(result.user.email).toBe('test@example.com');
    });

    it('should login with Supabase when available', async () => {
      const mockSupabase = {
        auth: {
          signInWithPassword: jest.fn().mockResolvedValue({
            data: {
              user: { id: '123', email: 'test@example.com' },
              session: { access_token: 'token', refresh_token: 'refresh' }
            },
            error: null
          })
        }
      };

      jest.doMock('@supabase/supabase-js', () => ({
        createClient: jest.fn(() => mockSupabase)
      }));

      const loginData = {
        email: 'test@example.com',
        password: 'password123'
      };

      const result = await apiClient.login(loginData);

      expect(result).toHaveProperty('access_token');
      expect(result).toHaveProperty('refresh_token');
      expect(result).toHaveProperty('user');
    });

    it('should logout with Supabase when available', async () => {
      const mockSupabase = {
        auth: {
          signOut: jest.fn().mockResolvedValue({ error: null })
        }
      };

      jest.doMock('@supabase/supabase-js', () => ({
        createClient: jest.fn(() => mockSupabase)
      }));

      await apiClient.logout();

      expect(mockSupabase.auth.signOut).toHaveBeenCalled();
    });

    it('should fallback to API-only mode when Supabase is not available', async () => {
      // Mock fetch for API fallback
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          access_token: 'api-token',
          refresh_token: 'api-refresh',
          user: { id: 1, email: 'test@example.com' }
        })
      });

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

      const result = await apiClient.signup(signupData);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/signup'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(signupData)
        })
      );
    });
  });

  describe('Token Management', () => {
    it('should save tokens to localStorage and cookies', () => {
      const tokens = {
        access_token: 'access-token',
        refresh_token: 'refresh-token',
        token_type: 'bearer',
        expires_in: 3600,
        user: { id: 1, email: 'test@example.com' }
      };

      // Access private method through any
      (apiClient as any).saveTokensToStorage(tokens);

      expect(localStorageMock.setItem).toHaveBeenCalledWith('access_token', 'access-token');
      expect(localStorageMock.setItem).toHaveBeenCalledWith('refresh_token', 'refresh-token');
      expect(localStorageMock.setItem).toHaveBeenCalledWith('user', JSON.stringify(tokens.user));
    });

    it('should clear tokens from localStorage and cookies', () => {
      (apiClient as any).clearTokensFromStorage();

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('refresh_token');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('user');
    });

    it('should check if user is authenticated', () => {
      localStorageMock.getItem.mockReturnValue('token');
      (apiClient as any).loadTokensFromStorage();

      expect(apiClient.isAuthenticated()).toBe(true);
    });
  });

  describe('HTTP Requests', () => {
    it('should make authenticated requests with Bearer token', async () => {
      localStorageMock.getItem.mockReturnValue('test-token');
      (apiClient as any).loadTokensFromStorage();

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ data: 'test' })
      });

      await (apiClient as any).makeRequest('/test');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/test'),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token',
            'x-access-token': 'test-token'
          })
        })
      );
    });

    it('should handle 401 errors by refreshing token', async () => {
      localStorageMock.getItem.mockReturnValue('test-token');
      (apiClient as any).loadTokensFromStorage();

      // Mock refresh token method
      const refreshSpy = jest.spyOn(apiClient, 'refreshAccessToken').mockResolvedValue(true);

      // First call returns 401, second call succeeds
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          status: 401,
          ok: false
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ data: 'test' })
        });

      await (apiClient as any).makeRequest('/test');

      expect(refreshSpy).toHaveBeenCalled();
    });
  });

  describe('User Management', () => {
    it('should get current user from Supabase when available', async () => {
      const mockSupabase = {
        auth: {
          getUser: jest.fn().mockResolvedValue({
            data: {
              user: { id: '123', email: 'test@example.com' }
            },
            error: null
          })
        }
      };

      jest.doMock('@supabase/supabase-js', () => ({
        createClient: jest.fn(() => mockSupabase)
      }));

      const user = await apiClient.getCurrentUser();

      expect(user).toHaveProperty('id');
      expect(user).toHaveProperty('email');
    });

    it('should get current user from storage', () => {
      const mockUser = { id: 1, email: 'test@example.com' };
      localStorageMock.getItem.mockReturnValue(JSON.stringify(mockUser));

      const user = apiClient.getCurrentUserFromStorage();

      expect(user).toEqual(mockUser);
    });
  });

  describe('Password Management', () => {
    it('should reset password with Supabase when available', async () => {
      const mockSupabase = {
        auth: {
          resetPasswordForEmail: jest.fn().mockResolvedValue({ error: null })
        }
      };

      jest.doMock('@supabase/supabase-js', () => ({
        createClient: jest.fn(() => mockSupabase)
      }));

      const result = await apiClient.resetPasswordRequest({ email: 'test@example.com' });

      expect(result).toEqual({ message: 'Password reset email sent successfully' });
      expect(mockSupabase.auth.resetPasswordForEmail).toHaveBeenCalledWith(
        'test@example.com',
        expect.objectContaining({
          redirectTo: expect.stringContaining('/auth/reset-password')
        })
      );
    });

    it('should change password with Supabase when available', async () => {
      const mockSupabase = {
        auth: {
          updateUser: jest.fn().mockResolvedValue({ error: null })
        }
      };

      jest.doMock('@supabase/supabase-js', () => ({
        createClient: jest.fn(() => mockSupabase)
      }));

      const result = await apiClient.changePassword({
        current_password: 'old',
        new_password: 'new'
      });

      expect(result).toEqual({ message: 'Password updated successfully' });
      expect(mockSupabase.auth.updateUser).toHaveBeenCalledWith({
        password: 'new'
      });
    });
  });
});
