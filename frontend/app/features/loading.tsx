import { Skeleton } from "@/components/ui/skeleton"

export default function Loading() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white">
      {/* Header Skeleton */}
      <div className="bg-white border-b">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center gap-4 mb-6">
            <Skeleton className="h-9 w-28" />
          </div>

          <div className="text-center max-w-3xl mx-auto">
            <Skeleton className="h-12 w-64 mx-auto mb-4" />
            <Skeleton className="h-6 w-full max-w-lg mx-auto mb-8" />
          </div>
        </div>
      </div>

      {/* Agent Cards Skeleton */}
      <div className="container mx-auto px-4 py-12">
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {Array(6)
            .fill(0)
            .map((_, index) => (
              <div key={index} className="border rounded-lg p-6 space-y-4">
                <div className="flex items-center gap-4">
                  <Skeleton className="h-12 w-12 rounded-xl" />
                  <div>
                    <Skeleton className="h-6 w-32 mb-2" />
                    <Skeleton className="h-4 w-40" />
                  </div>
                </div>
                <div className="space-y-2">
                  {Array(5)
                    .fill(0)
                    .map((_, featureIndex) => (
                      <div key={featureIndex} className="flex items-start">
                        <div className="mr-2 mt-1 h-1.5 w-1.5 rounded-full bg-gray-200"></div>
                        <Skeleton className="h-4 w-full" />
                      </div>
                    ))}
                </div>
                <div className="mt-6 text-right">
                  <Skeleton className="h-4 w-32 ml-auto" />
                </div>
              </div>
            ))}
        </div>

        {/* Platform Features Skeleton */}
        <div className="mt-16">
          <Skeleton className="h-8 w-64 mx-auto mb-12" />
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {Array(6)
              .fill(0)
              .map((_, index) => (
                <div key={index} className="border rounded-lg p-6 space-y-4">
                  <div className="flex items-center gap-4">
                    <Skeleton className="h-12 w-12 rounded-xl" />
                    <Skeleton className="h-6 w-48" />
                  </div>
                  <Skeleton className="h-20 w-full" />
                </div>
              ))}
          </div>
        </div>

        {/* CTA Section Skeleton */}
        <div className="mt-16">
          <div className="rounded-2xl p-8 bg-gray-100">
            <Skeleton className="h-8 w-96 mx-auto mb-4" />
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
