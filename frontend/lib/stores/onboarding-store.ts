import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { apiClient, OnboardingData, OnboardingResponse } from '@/lib/api-client'

interface OnboardingState {
  // Progress tracking
  currentStep: number
  progress: number
  isCompleted: boolean
  onboardingData: OnboardingData | null
  
  // A/B Testing (kept minimal)
  abTestGroup: string | null
  
  // Loading states
  isLoading: boolean
  error: string | null
  
  // Actions
  setCurrentStep: (step: number) => void
  setProgress: (progress: number) => void
  setOnboardingData: (data: OnboardingData) => void
  saveOnboardingData: () => Promise<void>
  loadOnboardingData: () => Promise<void>
  updateOnboardingData: (data: Partial<OnboardingData>) => void
  setABTestGroup: (group: string) => void
  setRecommendations: (recommendations: any) => void
  resetOnboarding: () => void
  clearError: () => void
}

export const useOnboardingStore = create<OnboardingState>()(
  persist(
    (set, get) => ({
      // Initial state
      currentStep: 1,
      progress: 0,
      isCompleted: false,
      onboardingData: null,
      abTestGroup: null,
      
      isLoading: false,
      error: null,

      // Actions
      setCurrentStep: (step: number) => {
        const totalSteps = 4
        const progress = Math.round((step / totalSteps) * 100)
        set({ currentStep: step, progress })
      },

      setProgress: (progress: number) => {
        set({ progress })
      },

      setOnboardingData: (data: OnboardingData) => {
        set({ onboardingData: data })
      },

      saveOnboardingData: async () => {
        const { onboardingData } = get()
        if (!onboardingData) return

        set({ isLoading: true, error: null })
        
        try {
          const response = await apiClient.saveOnboardingData(onboardingData)
          if (response.success) {
            set({ isCompleted: true, progress: 100 })
          }
        } catch (error) {
          set({ error: error instanceof Error ? error.message : 'Failed to save onboarding data' })
        } finally {
          set({ isLoading: false })
        }
      },

      loadOnboardingData: async () => {
        set({ isLoading: true, error: null })
        
        try {
          const response = await apiClient.getOnboardingData()
          if (response.success && response.onboarding_data) {
            set({ 
              onboardingData: response.onboarding_data,
              isCompleted: true,
              progress: 100
            })
          }
        } catch (error) {
          // If no onboarding data exists, that's fine - user hasn't completed onboarding
          console.log('No existing onboarding data found')
        } finally {
          set({ isLoading: false })
        }
      },

      updateOnboardingData: (data: Partial<OnboardingData>) => {
        const { onboardingData } = get()
        if (onboardingData) {
          const updatedData = { ...onboardingData, ...data }
          set({ onboardingData: updatedData })
        }
      },

      setABTestGroup: (group: string) => {
        set({ abTestGroup: group })
      },

      setRecommendations: (_recommendations: any) => {},

      resetOnboarding: () => {
        set({
          currentStep: 1,
          progress: 0,
          isCompleted: false,
          onboardingData: null,
          
          error: null
        })
      },

      clearError: () => {
        set({ error: null })
      }
    }),
    {
      name: 'onboarding-storage',
      partialize: (state) => ({
        currentStep: state.currentStep,
        progress: state.progress,
        isCompleted: state.isCompleted,
        onboardingData: state.onboardingData,
        abTestGroup: state.abTestGroup
      })
    }
  )
)
