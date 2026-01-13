"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { AlertCircle, ArrowLeft } from "lucide-react"

export default function AdminSignupPage() {
  const router = useRouter()

  useEffect(() => {
    // Force dark mode
    document.documentElement.classList.add("dark")
    
    // Check if already logged in
    const token = localStorage.getItem("admin_token")
    if (token) {
      router.push("/admin")
    }
  }, [router])

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center relative overflow-hidden">
      <div className="relative z-10 w-full max-w-md px-4">
        <div className="bg-gray-900/90 backdrop-blur-sm border border-gray-800 rounded-2xl p-8 shadow-2xl">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">Agent47 Admin</h1>
            <p className="text-gray-400">Admin Account Registration</p>
          </div>

          <div className="mb-6 p-4 bg-blue-900/20 border border-blue-800 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-blue-400 text-sm font-medium mb-1">Admin accounts are invitation-only</p>
              <p className="text-gray-400 text-xs">
                Admin accounts must be created by an existing administrator. If you need admin access, please contact your system administrator.
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <p className="text-gray-400 text-sm text-center">
              For regular user accounts, please use the standard signup page.
            </p>

            <Link
              href="/auth"
              className="w-full py-3 bg-green-600 hover:bg-green-700 text-white font-semibold rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              Go to User Signup
            </Link>

            <Link
              href="/admin/login"
              className="w-full py-3 bg-gray-800 hover:bg-gray-700 text-white font-semibold rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Admin Login
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

