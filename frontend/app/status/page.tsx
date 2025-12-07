import { ArrowLeft } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"

export default function StatusPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white flex flex-col items-center justify-center text-center p-8 max-w-7xl mx-auto 2xl:max-w-[1400px] 3xl:max-w-[1600px]">
      <div className="absolute top-4 left-4">
        <Link href="/">
          <Button variant="ghost" size="sm" className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back to Home
          </Button>
        </Link>
      </div>
      <h1 className="text-5xl font-bold text-gray-900 mb-4">System Status</h1>
      <p className="text-xl text-gray-600 mb-8 max-w-2xl">
        All systems operational. For detailed status updates and incident reports, please check back later.
      </p>
      <Link href="/">
        <Button className="bg-gradient-to-r from-green-400 to-green-600 hover:from-green-500 hover:to-green-700 text-white">Go to Homepage</Button>
      </Link>
    </div>
  )
}
