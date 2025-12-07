import { useEffect, useRef, useState } from 'react'

interface UsePollingOptions<T> {
  fetchFn: () => Promise<T>
  interval?: number
  enabled?: boolean
  onError?: (error: Error) => void
}

export function usePolling<T>({
  fetchFn,
  interval = 5000,
  enabled = true,
  onError
}: UsePollingOptions<T>) {
  const [data, setData] = useState<T | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  const fetchData = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const result = await fetchFn()
      setData(result)
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error')
      setError(error)
      onError?.(error)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (enabled) {
      // Fetch immediately
      fetchData()

      // Set up polling
      intervalRef.current = setInterval(() => {
        fetchData()
      }, interval)

      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current)
        }
      }
    }
  }, [enabled, interval, fetchFn])

  return { data, isLoading, error, refetch: fetchData }
}

