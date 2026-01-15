"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import Link from "next/link"
import { ArrowLeft, Check, CreditCard, Lock, Loader2, AlertCircle, ChevronRight } from "lucide-react"
import { cn } from "@/lib/utils"
import { useBillingStore } from "@/lib/stores/billing-store"
import { BillingPlan } from "@/lib/api-client"

// Types
type PlanTier = "free" | "starter" | "pro"
type PricingPeriod = "monthly" | "yearly"

// Constants
const PLANS: Record<
  PlanTier,
  {
    name: string
    description: string
    monthlyPrice: number
    yearlyPrice: number
  }
> = {
  free: {
    name: "Free",
    description: "Perfect for trying out Agent47.",
    monthlyPrice: 0,
    yearlyPrice: 0,
  },
  starter: {
    name: "Starter",
    description: "Perfect for freelancers and small teams.",
    monthlyPrice: 24.99,
    yearlyPrice: 269.89,
  },
  pro: {
    name: "Pro",
    description: "For agencies and growing businesses.",
    monthlyPrice: 79.0,
    yearlyPrice: 853.20,
  },
}

export default function CheckoutPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [planTier, setPlanTier] = useState<PlanTier>("free")
  const [pricingPeriod, setPricingPeriod] = useState<PricingPeriod>("monthly")
  const [isLoading, setIsLoading] = useState(false)
  const [isLoadingPlans, setIsLoadingPlans] = useState(true)
  const [plansError, setPlansError] = useState<string | null>(null)
  const [billingPlans, setBillingPlans] = useState<BillingPlan[]>([])
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    cardNumber: "",
    expiry: "",
    cvc: "",
  })

  const { fetchBillingPlans } = useBillingStore()

  // Fetch billing plans from backend
  useEffect(() => {
    const loadBillingPlans = async () => {
      setIsLoadingPlans(true)
      setPlansError(null)
      
      try {
        const plans = await fetchBillingPlans()
        setBillingPlans(plans || [])
      } catch (err) {
        setPlansError(err instanceof Error ? err.message : 'Failed to load billing plans')
        console.error('Billing plans fetch error:', err)
      } finally {
        setIsLoadingPlans(false)
      }
    }

    loadBillingPlans()
  }, [fetchBillingPlans])

  // Get plan and period from URL
  useEffect(() => {
    const plan = searchParams.get("plan") as PlanTier
    const period = searchParams.get("period") as PricingPeriod

    if (plan) {
      setPlanTier(plan)
    }

    if (period && (period === "monthly" || period === "yearly")) {
      setPricingPeriod(period)
    }
  }, [searchParams])

  // Get current plan data
  const currentPlan = billingPlans.find(plan => plan.tier === planTier) || PLANS[planTier]
  
  // Calculate price
  const price = pricingPeriod === "monthly" 
    ? (currentPlan?.price_usd || PLANS[planTier].monthlyPrice)
    : (currentPlan?.yearly_price_usd || PLANS[planTier].yearlyPrice)

  // Handle form input change
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      if (planTier === "free") {
        // Start a local 24-hour free trial immediately and redirect. Call backend in background.
        const expiresAt = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
        try { localStorage.setItem('free_trial_expires_at', expiresAt) } catch (e) { console.warn('Could not persist free trial expiry locally', e) }

        // Fire-and-forget backend subscription creation
        fetch('/api/v1/subscriptions/create', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          },
          body: JSON.stringify({
            plan_tier: planTier,
            billing_period: pricingPeriod,
            customer_email: formData.email,
            customer_name: formData.name
          })
  }).catch((err) => console.warn('Background create subscription failed', err))

        // Redirect to dashboard
        window.location.href = '/dashboard'
      } else {
        // Call backend to create payment session with Paystack
        const response = await fetch('/api/v1/payments/create-session', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          },
          body: JSON.stringify({
            plan_tier: planTier,
            billing_period: pricingPeriod,
            amount: price,
            customer_email: formData.email,
            customer_name: formData.name
          })
        })

        if (!response.ok) {
          throw new Error('Failed to create payment session')
        }

        const data = await response.json()
        
        if (data.payment_url) {
          // Redirect to Paystack payment page
          window.location.href = data.payment_url
        } else {
          throw new Error('No payment URL received')
        }
      }
    } catch (error) {
      console.error('Payment error:', error)
      alert('Payment failed. Please try again.')
      setIsLoading(false)
    }
  }

  if (isLoadingPlans) {
    return (
      <div className="min-h-screen bg-gray-50 pt-20 pb-10">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-center justify-center py-16">
              <Loader2 className="h-8 w-8 animate-spin mr-3" />
              <span className="text-lg">Loading checkout...</span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (plansError) {
    return (
      <div className="min-h-screen bg-gray-50 pt-20 pb-10">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-center justify-center py-16 text-red-600">
              <AlertCircle className="h-8 w-8 mr-3" />
              <span className="text-lg">{plansError}</span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50 pt-12 pb-16">
      <div className="container mx-auto px-4">
        <div className="max-w-5xl mx-auto">
          <Link href="/pricing" className="inline-flex items-center text-green-600 hover:text-green-700 mb-8 font-medium transition-colors group">
            <ArrowLeft className="w-4 h-4 mr-2 group-hover:-translate-x-1 transition-transform" />
            Back to Pricing
          </Link>

          <div className="bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden">
            {/* Header Section */}
            <div className="relative bg-gradient-to-br from-green-500 via-green-600 to-green-700 p-8 md:p-10 text-white overflow-hidden">
              <div className="absolute top-0 right-0 w-96 h-96 bg-white/10 rounded-full -mr-48 -mt-48 blur-3xl"></div>
              <div className="absolute bottom-0 left-0 w-72 h-72 bg-white/5 rounded-full -ml-36 -mb-36 blur-3xl"></div>
              <div className="relative z-10">
                <h1 className="text-3xl md:text-4xl font-extrabold mb-3">Complete Your Purchase</h1>
                <p className="text-lg text-white/90">You're just one step away from unlocking Agent47's full potential.</p>
              </div>
            </div>

            <div className="p-6 md:p-10">
              <div className="grid md:grid-cols-2 gap-8 lg:gap-12">
                {/* Order Summary */}
                <div className="space-y-6">
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-6">Order Summary</h2>

                    <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl p-6 border-2 border-gray-200 shadow-sm">
                      <div className="space-y-5">
                        <div className="flex justify-between items-center pb-4 border-b-2 border-gray-200">
                          <div>
                            <span className="text-xl font-bold text-gray-900">{currentPlan?.name || PLANS[planTier].name} Plan</span>
                            <p className="text-sm text-gray-600 mt-1">{currentPlan?.description || PLANS[planTier].description}</p>
                          </div>
                          <div className="text-right">
                            <span className="text-2xl font-extrabold text-gray-900">
                              {planTier === "free" ? "Free" : `$${pricingPeriod === "monthly"
                                ? (currentPlan?.price_usd || PLANS[planTier].monthlyPrice)
                                : ((currentPlan?.yearly_price_usd || PLANS[planTier].yearlyPrice) / 12).toFixed(0)}`}
                            </span>
                            {planTier !== "free" && (
                              <span className="text-sm text-gray-600 block">/{pricingPeriod === "monthly" ? "month" : "month"}</span>
                            )}
                          </div>
                        </div>

                        <div className="space-y-3">
                          <div className="flex items-center text-gray-700">
                            <div className="w-2 h-2 bg-green-500 rounded-full mr-3"></div>
                            <span className="font-medium">Cancel anytime from your dashboard</span>
                          </div>
                          <div className="flex items-center text-gray-700">
                            <div className="w-2 h-2 bg-green-500 rounded-full mr-3"></div>
                            <span className="font-medium">Instant access to all features</span>
                          </div>
                          <div className="flex items-center text-gray-700">
                            <div className="w-2 h-2 bg-green-500 rounded-full mr-3"></div>
                            <span className="font-medium">24/7 support via email and chat</span>
                          </div>
                        </div>

                        <div className="pt-4 border-t-2 border-gray-200">
                          <div className="flex justify-between items-center mb-3">
                            <span className="text-sm font-medium text-gray-600">Billing Period</span>
                            <span className="text-sm font-bold text-gray-900 capitalize">{pricingPeriod}</span>
                          </div>
                          <div className="flex justify-between items-center pt-3 border-t border-gray-300">
                            <span className="text-lg font-bold text-gray-900">Total Amount</span>
                            <div className="text-right">
                              <span className="text-3xl font-extrabold text-gray-900">
                                {planTier === "free" ? "Free" : `$${price}`}
                              </span>
                              {planTier !== "free" && (
                                <span className="text-sm text-gray-600 block">
                                  {pricingPeriod === "yearly" ? "per year" : "per month"}
                                </span>
                              )}
                            </div>
                          </div>
                          {pricingPeriod === "yearly" && planTier !== "free" && (
                            <div className="mt-3 text-sm font-semibold text-green-600 text-right">
                              💰 You save ${(PLANS[planTier].monthlyPrice * 12 - PLANS[planTier].yearlyPrice).toFixed(0)} with annual billing
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="bg-blue-50 border-2 border-blue-200 rounded-xl p-5">
                    <div className="flex items-start">
                      <Lock className="w-6 h-6 text-blue-600 mr-3 flex-shrink-0 mt-0.5" />
                      <div className="text-sm">
                        <p className="font-bold text-blue-900 mb-1">Secure Payment</p>
                        <p className="text-blue-700">Your payment is processed securely by Paystack. We never store your card details.</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Payment Form */}
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                    <CreditCard className="w-6 h-6 mr-2 text-green-600" />
                    Payment Details
                  </h2>

                  <form onSubmit={handleSubmit} className="space-y-5">
                    <div>
                      <label htmlFor="name" className="block text-sm font-bold text-gray-700 mb-2">
                        Cardholder Name
                      </label>
                      <input
                        type="text"
                        id="name"
                        name="name"
                        value={formData.name}
                        onChange={handleChange}
                        required
                        className="w-full h-12 px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all bg-gray-50 focus:bg-white text-gray-900 font-medium"
                        placeholder="John Doe"
                      />
                    </div>

                    <div>
                      <label htmlFor="email" className="block text-sm font-bold text-gray-700 mb-2">
                        Email Address
                      </label>
                      <input
                        type="email"
                        id="email"
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                        required
                        className="w-full h-12 px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all bg-gray-50 focus:bg-white text-gray-900 font-medium"
                        placeholder="john@example.com"
                      />
                    </div>

                    <div>
                      <label htmlFor="cardNumber" className="block text-sm font-bold text-gray-700 mb-2">
                        Card Number
                      </label>
                      <div className="relative">
                        <input
                          type="text"
                          id="cardNumber"
                          name="cardNumber"
                          value={formData.cardNumber}
                          onChange={handleChange}
                          required
                          className="w-full h-12 px-4 py-3 pl-12 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all bg-gray-50 focus:bg-white text-gray-900 font-medium"
                          placeholder="4242 4242 4242 4242"
                        />
                        <CreditCard className="absolute left-4 top-3.5 w-5 h-5 text-gray-400" />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label htmlFor="expiry" className="block text-sm font-bold text-gray-700 mb-2">
                          Expiry Date
                        </label>
                        <input
                          type="text"
                          id="expiry"
                          name="expiry"
                          value={formData.expiry}
                          onChange={handleChange}
                          required
                          className="w-full h-12 px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all bg-gray-50 focus:bg-white text-gray-900 font-medium"
                          placeholder="MM/YY"
                        />
                      </div>

                      <div>
                        <label htmlFor="cvc" className="block text-sm font-bold text-gray-700 mb-2">
                          CVC
                        </label>
                        <input
                          type="text"
                          id="cvc"
                          name="cvc"
                          value={formData.cvc}
                          onChange={handleChange}
                          required
                          className="w-full h-12 px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all bg-gray-50 focus:bg-white text-gray-900 font-medium"
                          placeholder="123"
                        />
                      </div>
                    </div>

                    <div className="pt-4">
                      <button
                        type="submit"
                        disabled={isLoading}
                        className={cn(
                          "w-full h-14 bg-gradient-to-r from-green-500 to-green-600 text-white font-bold text-lg rounded-xl transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-[1.02] flex items-center justify-center group",
                          isLoading ? "opacity-70 cursor-not-allowed" : "hover:from-green-600 hover:to-green-700",
                        )}
                      >
                        {isLoading ? (
                          <>
                            <svg
                              className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                              xmlns="http://www.w3.org/2000/svg"
                              fill="none"
                              viewBox="0 0 24 24"
                            >
                              <circle
                                className="opacity-25"
                                cx="12"
                                cy="12"
                                r="10"
                                stroke="currentColor"
                                strokeWidth="4"
                              ></circle>
                              <path
                                className="opacity-75"
                                fill="currentColor"
                                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                              ></path>
                            </svg>
                            Processing Payment...
                          </>
                        ) : (
                          <>
                            {planTier === "free" ? "Get Started Free" : "Complete Purchase"}
                            <ChevronRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
                          </>
                        )}
                      </button>
                    </div>

                    <div className="text-center text-xs text-gray-500 flex items-center justify-center pt-2">
                      <Lock className="w-4 h-4 mr-1" />
                      Secured by Paystack • SSL Encrypted
                    </div>
                  </form>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
