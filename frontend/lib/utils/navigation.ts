/**
 * Navigation utilities for optimized page transitions
 */

import { useRouter } from "next/navigation"
import { useTransition } from "react"

/**
 * Hook for optimized navigation with loading states
 */
export function useOptimizedNavigation() {
  const router = useRouter()
  const [isPending, startTransition] = useTransition()

  const navigate = (path: string) => {
    startTransition(() => {
      router.push(path)
    })
  }

  const prefetch = (path: string) => {
    router.prefetch(path)
  }

  return {
    navigate,
    prefetch,
    isPending,
  }
}

/**
 * Prefetch common routes on mount
 */
export function prefetchCommonRoutes() {
  if (typeof window === "undefined") return

  const commonRoutes = [
    "/dashboard",
    "/dashboard?tab=home",
    "/dashboard?tab=agents-overview",
    "/dashboard?tab=platforms-overview",
    "/auth",
    "/pricing",
    "/features",
  ]

  // Prefetch routes after a short delay to not block initial load
  setTimeout(() => {
    commonRoutes.forEach((route) => {
      // Use Next.js router prefetch if available
      if (window.next?.router) {
        window.next.router.prefetch(route)
      }
    })
  }, 1000)
}

