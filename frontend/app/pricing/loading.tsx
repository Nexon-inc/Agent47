export default function Loading() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-white">
      <div className="flex flex-col items-center">
        <div className="w-16 h-16 border-4 border-t-green-600 border-green-500/30 rounded-full animate-spin"></div>
        <p className="mt-4 text-lg text-green-600 font-medium">Loading pricing options...</p>
      </div>
    </div>
  )
}
