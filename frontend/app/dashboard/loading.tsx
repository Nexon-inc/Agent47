import { Loader2 } from "lucide-react"

export default function Loading() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-white dark:bg-gray-900">
      <div className="text-center">
        <Loader2 className="h-12 w-12 animate-spin text-green-600 mx-auto" />
        <h3 className="mt-4 text-xl font-semibold text-slate-900 dark:text-white">Loading Dashboard...</h3>
        <p className="mt-2 text-gray-500 dark:text-gray-400">Please wait while we load your agents.</p>
      </div>
    </div>
  )
}
