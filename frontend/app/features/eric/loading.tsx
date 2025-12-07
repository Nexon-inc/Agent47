import { Skeleton } from "@/components/ui/skeleton"

export default function Loading() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white">
      {/* Header Skeleton */}
      <div className="bg-white border-b">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center gap-4 mb-6">
            <Skeleton className="h-9 w-32" />
          </div>

          <div className="text-center max-w-3xl mx-auto">
            <div className="flex items-center justify-center gap-3 mb-4">
              <Skeleton className="h-12 w-12 rounded-xl" />
              <Skeleton className="h-12 w-48" />
            </div>
            <Skeleton className="h-6 w-full max-w-lg mx-auto mb-8" />

            <div className="flex flex-wrap justify-center gap-4 mb-8">
              {Array(4)
                .fill(0)
                .map((_, index) => (
                  <Skeleton key={index} className="h-8 w-32" />
                ))}
            </div>
          </div>
        </div>
      </div>

      {/* Features Grid Skeleton */}
      <div className="container mx-auto px-4 py-12">
        <div className="grid gap-8">
          {Array(12)
            .fill(0)
            .map((_, categoryIndex) => (
              <div key={categoryIndex} className="space-y-6">
                <div className="flex items-center gap-4">
                  <Skeleton className="h-12 w-12 rounded-xl" />
                  <Skeleton className="h-8 w-64" />
                </div>

                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {Array(3)
                    .fill(0)
                    .map((_, featureIndex) => (
                      <div key={featureIndex} className="border rounded-lg p-6 space-y-4">
                        <div className="flex items-start justify-between">
                          <Skeleton className="h-6 w-48" />
                          <Skeleton className="h-6 w-20" />
                        </div>
                        <Skeleton className="h-16 w-full" />
                      </div>
                    ))}
                </div>
              </div>
            ))}
        </div>

        {/* CTA Section Skeleton */}
        <div className="mt-16">
          <div className="rounded-2xl p-8 bg-gray-100">
            <Skeleton className="h-8 w-80 mx-auto mb-4" />
            <Skeleton className="h-4 w-full max-w-2xl mx-auto mb-6" />
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Skeleton className="h-12 w-36 mx-auto sm:mx-0" />
              <Skeleton className="h-12 w-36 mx-auto sm:mx-0" />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
