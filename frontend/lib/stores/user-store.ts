import { create } from "zustand"

type UserPlan = "free" | "starter" | "pro"

interface UserState {
  userPlan: UserPlan
  setUserPlan: (plan: UserPlan) => void
}

export const useUserStore = create<UserState>((set) => ({
  userPlan: "free",
  setUserPlan: (plan) => set({ userPlan: plan }),
}))
