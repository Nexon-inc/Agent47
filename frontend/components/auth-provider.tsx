"use client"

import { useEffect } from "react"
import { useAuthStore } from "@/lib/stores/auth-store"

interface AuthProviderProps {
  children: React.ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const { initialize, initializeSupabase } = useAuthStore()

  useEffect(() => {
    // Initialize auth state from storage
    initialize().catch(console.error)
    
    // Initialize Supabase client and set up auth state listener
    initializeSupabase()
  }, [initialize, initializeSupabase])

  return <>{children}</>
}
