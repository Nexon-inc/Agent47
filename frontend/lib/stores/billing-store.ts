import { create } from 'zustand'
import { apiClient, BillingPlan, Subscription, Payment, UsageData } from '@/lib/api-client'

interface BillingState {
  // Data
  billingPlans: BillingPlan[]
  subscription: Subscription | null
  paymentHistory: Payment[]
  usage: UsageData | null

  // Loading states
  isLoading: boolean
  error: string | null

  // Actions
  fetchBillingPlans: () => Promise<void>
  fetchSubscription: (suppressRedirect?: boolean) => Promise<void>
  fetchPaymentHistory: () => Promise<void>
  fetchUsage: () => Promise<void>
  createSubscription: (tier: string, paymentMethod: string) => Promise<any>
  cancelSubscription: (reason: string) => Promise<void>
  clearError: () => void
}

export const useBillingStore = create<BillingState>()((set, get) => ({
  // Initial state
  billingPlans: [],
  subscription: null,
  paymentHistory: [],
  usage: null,
  isLoading: false,
  error: null,

  // Actions
  fetchBillingPlans: async (suppressRedirect: boolean = false) => {
    set({ isLoading: true, error: null })
    try {
      const plans = await apiClient.getBillingPlans({ suppressRedirect })
      set({ billingPlans: plans })
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to fetch billing plans' })
    } finally {
      set({ isLoading: false })
    }
  },

  fetchSubscription: async (suppressRedirect: boolean = false) => {
    set({ isLoading: true, error: null })
    try {
      const subscription = await apiClient.getSubscription({ suppressRedirect })
      set({ subscription })
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to fetch subscription' })
    } finally {
      set({ isLoading: false })
    }
  },

  fetchPaymentHistory: async () => {
    set({ isLoading: true, error: null })
    try {
      const payments = await apiClient.getPaymentHistory()
      set({ paymentHistory: payments })
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to fetch payment history' })
    } finally {
      set({ isLoading: false })
    }
  },

  fetchUsage: async () => {
    set({ isLoading: true, error: null })
    try {
      const usage = await apiClient.getUserUsage()
      set({ usage })
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to fetch usage data' })
    } finally {
      set({ isLoading: false })
    }
  },

  createSubscription: async (tier: string, paymentMethod: string, billingPeriod: string = "monthly", suppressRedirect: boolean = false) => {
    set({ isLoading: true, error: null })
    try {
      const result = await apiClient.createSubscription(tier, paymentMethod, billingPeriod, { suppressRedirect })
      // Refresh subscription data but suppress automatic redirect behavior
      await get().fetchSubscription(true)
      return result
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to create subscription' })
      throw error
    } finally {
      set({ isLoading: false })
    }
  },

  cancelSubscription: async (reason: string) => {
    set({ isLoading: true, error: null })
    try {
      await apiClient.cancelSubscription(reason)
      // Refresh subscription data
      await get().fetchSubscription()
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to cancel subscription' })
      throw error
    } finally {
      set({ isLoading: false })
    }
  },

  clearError: () => set({ error: null })
}))
