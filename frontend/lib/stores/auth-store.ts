import { create } from "zustand"
import { persist } from "zustand/middleware"
import { apiClient, User, AuthTokens, SignupData, LoginData, PasswordResetData } from "@/lib/api-client"

// Use the shared Supabase client from api-client
const getSupabaseClient = async () => {
  return await apiClient.getCurrentSession();
};

interface AuthState {
  // User state
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  session: any | null
  
  // Actions
  signup: (data: SignupData) => Promise<boolean>
  login: (data: LoginData) => Promise<boolean>
  logout: () => Promise<void>
  resetPassword: (data: PasswordResetData) => Promise<boolean>
  refreshUser: () => Promise<void>
  clearError: () => void
  
  // Initialize auth state from storage
  initialize: () => Promise<void>
  
  // Force refresh auth state
  forceRefresh: () => Promise<void>
  
  // Supabase session management
  initializeSupabase: () => Promise<void>
  handleAuthStateChange: (event: string, session: any) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      session: null,

      // Initialize auth state from storage
      initialize: async () => {
        const user = apiClient.getCurrentUserFromStorage()
        const isAuthenticated = apiClient.isAuthenticated()
        
        set({
          user,
          isAuthenticated,
          isLoading: false,
          error: null
        })
        
        // If we have tokens but no user data, try to refresh from backend
        if (isAuthenticated && !user) {
          try {
            const freshUser = await apiClient.getCurrentUser()
            set({ user: freshUser })
          } catch (error) {
            console.error('Failed to refresh user during initialization:', error)
            // If refresh fails, clear auth state
            set({ user: null, isAuthenticated: false })
          }
        }
      },

      // Signup action
      signup: async (data: SignupData) => {
        set({ isLoading: true, error: null })
        
        try {
          const tokens = await apiClient.signup(data)
          
          // Wait for tokens to be saved before updating state
          // Check if user is admin based on tier or email whitelist
          const isAdmin = tokens.user.tier === 'pro' || tokens.user.is_admin === true
          
          set({
            user: { ...tokens.user, is_admin: isAdmin },
            isAuthenticated: true,
            isLoading: false,
            error: null
          })
          
          // Add a small delay to ensure localStorage is updated
          await new Promise(resolve => setTimeout(resolve, 100))
          
          // Fetch fresh user data from backend to ensure we have complete profile
          try {
            const freshUser = await apiClient.getCurrentUser()
            if (freshUser && freshUser.id) {
              set({ user: { ...freshUser, is_admin: isAdmin } })
            }
          } catch (err) {
            console.warn('Failed to fetch fresh user data after signup:', err)
            // Continue with the user data we have from signup response
          }
          
          return true
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Signup failed'
          set({
            isLoading: false,
            error: errorMessage
          })
          return false
        }
      },

      // Login action
      login: async (data: LoginData) => {
        set({ isLoading: true, error: null })
        
        try {
          const tokens = await apiClient.login(data)
          
          // Check if user is admin based on tier or email whitelist
          const isAdmin = tokens.user.tier === 'pro' || tokens.user.is_admin === true
          
          set({
            user: { ...tokens.user, is_admin: isAdmin },
            isAuthenticated: true,
            isLoading: false,
            error: null
          })
          
          // Fetch fresh user data from backend to ensure we have complete profile
          try {
            const freshUser = await apiClient.getCurrentUser()
            if (freshUser && freshUser.id) {
              set({ user: { ...freshUser, is_admin: isAdmin } })
            }
          } catch (err) {
            console.warn('Failed to fetch fresh user data after login:', err)
            // Continue with the user data we have from login response
          }
          
          return true
        } catch (error) {
          console.error('Login error:', error)
          const errorMessage = error instanceof Error ? error.message : 'Login failed'
          set({
            isLoading: false,
            error: errorMessage
          })
          return false
        }
      },

      // Logout action
      logout: async () => {
        set({ isLoading: true })
        
        try {
          await apiClient.logout()
        } catch (error) {
          console.warn('Logout error:', error)
        } finally {
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null
          })
        }
      },

      // Reset password action
      resetPassword: async (data: PasswordResetData) => {
        set({ isLoading: true, error: null })
        
        try {
          await apiClient.resetPasswordRequest(data)
          set({ isLoading: false })
          return true
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Password reset failed'
          set({
            isLoading: false,
            error: errorMessage
          })
          return false
        }
      },

      // Refresh user data
      refreshUser: async () => {
        // Check if we have tokens, not just isAuthenticated flag
        const hasTokens = apiClient.isAuthenticated()
        if (!hasTokens) return
        
        try {
          const user = await apiClient.getCurrentUser()
          set({ user, isAuthenticated: true })
        } catch (error) {
          console.error('Failed to refresh user:', error)
          // If refresh fails, user might be logged out
          if (error instanceof Error && error.message.includes('401')) {
            get().logout()
          }
        }
      },

      // Clear error
      clearError: () => {
        set({ error: null })
      },

      // Force refresh auth state
      forceRefresh: async () => {
        const hasTokens = apiClient.isAuthenticated()
        if (!hasTokens) {
          set({ user: null, isAuthenticated: false })
          return
        }
        
        try {
          const user = await apiClient.getCurrentUser()
          set({ user, isAuthenticated: true })
        } catch (error) {
          console.error('Failed to force refresh user:', error)
          set({ user: null, isAuthenticated: false })
        }
      },

      // Initialize auth state from storage
      initializeSupabase: async () => {
        if (typeof window !== 'undefined') {
          // Check if user is already authenticated from storage
          const storedUser = localStorage.getItem('user');
          const accessToken = localStorage.getItem('access_token');
          
          if (storedUser && accessToken) {
            try {
              const user = JSON.parse(storedUser);
              set({ 
                user,
                isAuthenticated: true,
                session: { access_token: accessToken }
              });
            } catch (error) {
              console.error('Failed to parse stored user:', error);
              // Clear invalid storage
              localStorage.removeItem('user');
              localStorage.removeItem('access_token');
              localStorage.removeItem('refresh_token');
            }
          }
        }
      },

      // Handle Supabase auth state changes
      handleAuthStateChange: (event: string, session: any) => {
        console.log('Auth state changed:', event, session);
        
        if (event === 'SIGNED_IN' && session) {
          set({ 
            session,
            isAuthenticated: true,
            error: null 
          });
          
          // Get user profile
          apiClient.getCurrentUser()
            .then(user => set({ user }))
            .catch(error => console.error('Failed to get user profile:', error));
        } else if (event === 'SIGNED_OUT') {
          set({ 
            user: null,
            isAuthenticated: false,
            session: null,
            error: null 
          });
        } else if (event === 'TOKEN_REFRESHED' && session) {
          set({ session });
        }
      }
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        session: state.session
      })
    }
  )
)
