import { create } from "zustand"
import { adminAPI, AdminUser } from "@/lib/services/admin-api"

interface AdminState {
  // Admin data
  currentAdmin: AdminUser | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  
  // Actions
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  fetchCurrentAdmin: () => Promise<void>
  clearError: () => void
}

export const useAdminStore = create<AdminState>((set, get) => ({
  // Initial state
  currentAdmin: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  // Login
  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null })
    
    try {
      const response = await adminAPI.login(email, password)
      set({ 
        currentAdmin: response.admin_user,
        isAuthenticated: true,
        isLoading: false 
      })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Login failed'
      set({ error: errorMessage, isLoading: false, isAuthenticated: false })
      throw error
    }
  },

  // Logout
  logout: async () => {
    try {
      await adminAPI.logout()
    } finally {
      set({ 
        currentAdmin: null,
        isAuthenticated: false,
        error: null
      })
    }
  },

  // Fetch current admin
  fetchCurrentAdmin: async () => {
    set({ isLoading: true, error: null })
    
    try {
      const admin = await adminAPI.getCurrentAdmin()
      set({ 
        currentAdmin: admin,
        isAuthenticated: true,
        isLoading: false 
      })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch admin'
      set({ 
        error: errorMessage, 
        isLoading: false,
        isAuthenticated: false,
        currentAdmin: null
      })
    }
  },

  // Clear error
  clearError: () => {
    set({ error: null })
  }
}))
