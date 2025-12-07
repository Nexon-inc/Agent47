import { create } from 'zustand'
import { apiClient, Goal, GoalProgress, GoalActivity, GoalTemplate, CreateGoalData, UpdateGoalData, UpdateGoalProgressData, GoalsResponse, GoalAnalytics } from '@/lib/api-client'

interface GoalsState {
  goals: Goal[]
  templates: GoalTemplate[]
  analytics: GoalAnalytics | null
  selectedGoal: Goal | null
  goalProgress: GoalProgress[]
  goalActivities: GoalActivity[]
  isLoading: boolean
  error: string | null
  total: number
  active_goals: number
  completed_goals: number
  overdue_goals: number
}

interface GoalsActions {
  fetchGoals: (page?: number, limit?: number, status?: string) => Promise<void>
  fetchGoalById: (id: string) => Promise<void>
  createGoal: (data: CreateGoalData) => Promise<Goal | null>
  updateGoal: (id: string, data: UpdateGoalData) => Promise<Goal | null>
  updateGoalProgress: (goalId: string, data: UpdateGoalProgressData) => Promise<Goal | null>
  fetchGoalProgress: (goalId: string) => Promise<void>
  fetchGoalActivities: (goalId: string) => Promise<void>
  fetchTemplates: () => Promise<void>
  fetchAnalytics: () => Promise<void>
  setSelectedGoal: (goal: Goal | null) => void
  clearError: () => void
  clearGoals: () => void
}

type GoalsStore = GoalsState & GoalsActions

export const useGoalsStore = create<GoalsStore>((set, get) => ({
  goals: [],
  templates: [],
  analytics: null,
  selectedGoal: null,
  goalProgress: [],
  goalActivities: [],
  isLoading: false,
  error: null,
  total: 0,
  active_goals: 0,
  completed_goals: 0,
  overdue_goals: 0,

  fetchGoals: async (page = 1, limit = 10, status?: string) => {
    set({ isLoading: true, error: null })
    try {
      const response = await apiClient.getGoals(page, limit, status)
      set({
        goals: response.goals,
        total: response.total,
        active_goals: response.active_goals,
        completed_goals: response.completed_goals,
        overdue_goals: response.overdue_goals,
        isLoading: false
      })
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to fetch goals',
        isLoading: false 
      })
    }
  },

  fetchGoalById: async (id: string) => {
    set({ isLoading: true, error: null })
    try {
      const goal = await apiClient.getGoalById(id)
      set({ selectedGoal: goal, isLoading: false })
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to fetch goal',
        isLoading: false 
      })
    }
  },

  createGoal: async (data: CreateGoalData) => {
    set({ isLoading: true, error: null })
    try {
      const goal = await apiClient.createGoal(data)
      const { goals } = get()
      set({ 
        goals: [goal, ...goals],
        isLoading: false 
      })
      return goal
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to create goal',
        isLoading: false 
      })
      return null
    }
  },

  updateGoal: async (id: string, data: UpdateGoalData) => {
    set({ isLoading: true, error: null })
    try {
      const updatedGoal = await apiClient.updateGoal(id, data)
      const { goals } = get()
      const updatedGoals = goals.map(goal => 
        goal.id === id ? updatedGoal : goal
      )
      set({ 
        goals: updatedGoals,
        selectedGoal: updatedGoal,
        isLoading: false 
      })
      return updatedGoal
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to update goal',
        isLoading: false 
      })
      return null
    }
  },

  updateGoalProgress: async (goalId: string, data: UpdateGoalProgressData) => {
    set({ isLoading: true, error: null })
    try {
      const updatedGoal = await apiClient.updateGoalProgress(goalId, data)
      const { goals } = get()
      const updatedGoals = goals.map(goal => 
        goal.id === goalId ? updatedGoal : goal
      )
      set({ 
        goals: updatedGoals,
        selectedGoal: updatedGoal,
        isLoading: false 
      })
      return updatedGoal
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to update goal progress',
        isLoading: false 
      })
      return null
    }
  },

  fetchGoalProgress: async (goalId: string) => {
    set({ isLoading: true, error: null })
    try {
      const progress = await apiClient.getGoalProgress(goalId)
      set({ goalProgress: progress, isLoading: false })
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to fetch goal progress',
        isLoading: false 
      })
    }
  },

  fetchGoalActivities: async (goalId: string) => {
    set({ isLoading: true, error: null })
    try {
      const activities = await apiClient.getGoalActivities(goalId)
      set({ goalActivities: activities, isLoading: false })
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to fetch goal activities',
        isLoading: false 
      })
    }
  },

  fetchTemplates: async () => {
    set({ isLoading: true, error: null })
    try {
      const templates = await apiClient.getGoalTemplates()
      set({ templates, isLoading: false })
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to fetch templates',
        isLoading: false 
      })
    }
  },

  fetchAnalytics: async () => {
    set({ isLoading: true, error: null })
    try {
      const analytics = await apiClient.getGoalAnalytics()
      set({ analytics, isLoading: false })
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to fetch analytics',
        isLoading: false 
      })
    }
  },

  setSelectedGoal: (goal: Goal | null) => {
    set({ selectedGoal: goal })
  },

  clearError: () => {
    set({ error: null })
  },

  clearGoals: () => {
    set({ 
      goals: [],
      selectedGoal: null,
      goalProgress: [],
      goalActivities: [],
      total: 0,
      active_goals: 0,
      completed_goals: 0,
      overdue_goals: 0
    })
  }
}))
