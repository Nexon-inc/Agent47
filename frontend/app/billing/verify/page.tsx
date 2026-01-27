"use client"

import { useEffect, useState } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import { Loader2, CheckCircle2, XCircle, ArrowRight } from "lucide-react"
import Link from "next/link"
import { apiClient } from "@/lib/api-client"

export default function VerifyPaymentPage() {
    const searchParams = useSearchParams()
    const router = useRouter()
    const [status, setStatus] = useState<"loading" | "success" | "error">("loading")
    const [message, setMessage] = useState("Verifying your payment...")

    useEffect(() => {
        const reference = searchParams.get("reference") || searchParams.get("trxref")

        if (!reference) {
            setStatus("error")
            setMessage("No payment reference found. Please contact support if you believe this is an error.")
            return
        }

        const verify = async () => {
            try {
                const result = await apiClient.verifyPayment(reference)
                if (result.status === "active" || result.status === "success" || result.success) {
                    setStatus("success")
                    setMessage("Payment verified successfully! Redirecting to dashboard...")
                    setTimeout(() => {
                        router.push("/dashboard")
                    }, 2000)
                } else {
                    setStatus("error")
                    setMessage(result.message || "Payment verification failed. Please try again.")
                }
            } catch (err: any) {
                console.error("Verification error:", err)
                setStatus("error")
                setMessage(err.message || "An error occurred while verifying your payment.")
            }
        }

        verify()
    }, [searchParams, router])

    return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
            <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center">
                {status === "loading" && (
                    <div className="space-y-4">
                        <Loader2 className="h-12 w-12 text-green-600 animate-spin mx-auto" />
                        <h1 className="text-2xl font-bold text-gray-900">Verifying Payment</h1>
                        <p className="text-gray-600">{message}</p>
                    </div>
                )}

                {status === "success" && (
                    <div className="space-y-4">
                        <CheckCircle2 className="h-12 w-12 text-green-500 mx-auto" />
                        <h1 className="text-2xl font-bold text-gray-900">Success!</h1>
                        <p className="text-gray-600">{message}</p>
                        <Link
                            href="/dashboard"
                            className="inline-flex items-center px-6 py-3 bg-green-600 text-white font-semibold rounded-xl hover:bg-green-700 transition-colors"
                        >
                            Go to Dashboard
                            <ArrowRight className="ml-2 h-5 w-5" />
                        </Link>
                    </div>
                )}

                {status === "error" && (
                    <div className="space-y-4">
                        <XCircle className="h-12 w-12 text-red-500 mx-auto" />
                        <h1 className="text-2xl font-bold text-gray-900">Verification Failed</h1>
                        <p className="text-gray-600">{message}</p>
                        <div className="flex flex-col gap-3">
                            <button
                                onClick={() => window.location.reload()}
                                className="px-6 py-3 bg-gray-900 text-white font-semibold rounded-xl hover:bg-gray-800 transition-colors"
                            >
                                Try Again
                            </button>
                            <Link
                                href="/pricing"
                                className="text-green-600 font-medium hover:underline"
                            >
                                Back to Pricing
                            </Link>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
