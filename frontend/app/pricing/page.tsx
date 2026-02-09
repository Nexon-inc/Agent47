"use client"

import type React from "react"

import { useState, useEffect } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Check, X, ChevronRight, ArrowLeft, CreditCard, Shield, Info, Loader2, AlertCircle, Lock } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { cn } from "@/lib/utils"
import { apiClient, BillingPlan } from "@/lib/api-client"
import { useBillingStore } from "@/lib/stores/billing-store"

// Types
type PricingTier = "free" | "starter" | "pro"
type BillingPeriod = "monthly" | "yearly"
type PaymentStep = "select" | "payment" | "processing" | "success" | "error"

interface PricingPlan {
  name: string
  price: number
  yearlyPrice: number
  period: string
  description: string
  color: string
  features: string[]
  recommended?: boolean
  agents: number | string
  support: string
  integrations: string
  teamMembers?: string
}

interface ComparisonFeature {
  name: string
  free: boolean | string
  starter: boolean | string
  pro: boolean | string
}

// Constants
const PRICING_PLANS: Record<PricingTier, PricingPlan> = {
  free: {
    name: "Free",
    price: 0,
    yearlyPrice: 0,
    period: "month",
    description: "Perfect for trying out our AI employees",
    color: "from-green-400 to-green-600",
    agents: 1,
    support: "Community support only",
    integrations: "Basic integrations",
    features: [
      "1 AI Employee (your choice)",
      "14-day full access trial",
      "Then limited to 5 actions/day",
      "Basic functionality",
      "No inter-personnel communication",
      "Basic Content Creation",
      "Basic Analytics",
      "Community Support",
    ],
  },
  starter: {
    name: "Starter",
    price: 24.99,
    yearlyPrice: 269.89, // 10% discount: (24.99 * 12) * 0.9
    period: "month",
    description: "Perfect for freelancers and small teams",
    color: "from-green-400 to-green-600",
    recommended: true,
    agents: 4,
    support: "Email support (24h response)",
    integrations: "5 platforms",
    features: [
      "4 AI Employees (Purity excluded)",
      "Full employee features",
      "Basic analytics",
      "Advanced Content Creation",
      "Workflow Automation",
      "Lead Generation Tools",
      "Customer Support Automation",
      "Market Research Insights",
      "Custom Integrations (5 platforms)",
      "Email Support (24h response)",
    ],
  },
  pro: {
    name: "Pro",
    price: 79.0,
    yearlyPrice: 853.20, // 10% discount: (79 * 12) * 0.9
    period: "month",
    description: "For agencies and growing businesses",
    color: "from-green-500 to-green-700",
    agents: "Full team (7 employees)",
    support: "Priority support (12h response)",
    integrations: "Unlimited",
    teamMembers: "Up to 5 team members",
    features: [
      "Full AI Team Available",
      "Inter-employee communication",
      "Advanced analytics",
      "Advanced Content Creation",
      "Team Collaboration (5 members)",
      "CRM Integration",
      "Advanced SEO Tools",
      "Email Marketing Automation",
      "Social Media Advertising",
      "Business Intelligence",
      "Unlimited Custom Integrations",
      "Priority Support (12h response)",
    ],
  },
}

const COMPARISON_FEATURES: ComparisonFeature[] = [
  {
    name: "Number of team members",
    free: 1,
    starter: "4 (Purity excluded)",
    pro: "Full team (7 employees)",
  },
  {
    name: "Personnel Communication",
    free: false,
    starter: false,
    pro: true,
  },
  {
    name: "Team Collaboration",
    free: false,
    starter: false,
    pro: "Up to 5 members",
  },
  {
    name: "Custom Integrations",
    free: "Basic",
    starter: "5 platforms",
    pro: "Unlimited",
  },
  {
    name: "Support",
    free: "Community only",
    starter: "Email (24h)",
    pro: "Priority (12h)",
  },
  {
    name: "Analytics",
    free: "Basic",
    starter: "Basic",
    pro: "Advanced",
  },
  {
    name: "Trial Period",
    free: "14 days full access",
    starter: false,
    pro: false,
  },
]

export default function PricingPage() {
  const router = useRouter()
  const [selectedTier, setSelectedTier] = useState<PricingTier | null>(null)
  const [billingPeriod, setBillingPeriod] = useState<BillingPeriod>("monthly")
  const [paymentStep, setPaymentStep] = useState<PaymentStep>("select")
  const [showComparison, setShowComparison] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  // Use billing store data directly so UI reflects backend plans/subscription
  const billingPlans = useBillingStore(state => state.billingPlans)
  const currentSubscription = useBillingStore(state => state.subscription)
  const { fetchBillingPlans, fetchSubscription } = useBillingStore()

  // Fetch pricing plans from backend (suppress redirects to avoid reload loops)
  useEffect(() => {
    const loadPricingData = async () => {
      setLoading(true)
      setError(null)

      try {
        await fetchBillingPlans(true)
        await fetchSubscription(true)
        // subscription is read from store via `currentSubscription`
        // billing plans are populated into store via fetchBillingPlans
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load pricing data')
        console.error('Pricing data fetch error:', err)
      } finally {
        setLoading(false)
      }
    }

    loadPricingData()
  }, [fetchBillingPlans, fetchSubscription])

  // Form state
  const [cardNumber, setCardNumber] = useState("")
  const [cardExpiry, setCardExpiry] = useState("")
  const [cardCvv, setCvv] = useState("")
  const [cardName, setCardName] = useState("")

  // Format card number with spaces
  const formatCardNumber = (value: string) => {
    const v = value.replace(/\s+/g, "").replace(/[^0-9]/gi, "")
    const matches = v.match(/\d{4,16}/g)
    const match = (matches && matches[0]) || ""
    const parts = []

    for (let i = 0; i < match.length; i += 4) {
      parts.push(match.substring(i, i + 4))
    }

    if (parts.length) {
      return parts.join(" ")
    } else {
      return value
    }
  }

  // Format card expiry date
  const formatExpiryDate = (value: string) => {
    const v = value.replace(/\s+/g, "").replace(/[^0-9]/gi, "")

    if (v.length >= 3) {
      return `${v.substring(0, 2)}/${v.substring(2, 4)}`
    }

    return value
  }

  // Handle tier selection
  const handleSelectTier = async (tier: PricingTier) => {
    try {
      setSelectedTier(tier)
      setError(null)

      if (tier === "free") {
        // Start local 14-day trial immediately and redirect user to dashboard.
        const expiresAt = new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString()
        try {
          localStorage.setItem('free_trial_expires_at', expiresAt)
        } catch (e) {
          console.warn('Could not persist free trial expiry locally', e)
        }

        // Fire-and-forget backend subscription creation so server record exists if possible
        apiClient.createSubscription("free", "paystack", "monthly", { suppressRedirect: true }).catch((err) => {
          console.warn('Background free subscription creation failed:', err)
        })

        // Set a short-lived cookie so Next.js middleware allows immediate navigation to /dashboard
        try {
          const cookieExpires = new Date(Date.now() + 24 * 60 * 60 * 1000).toUTCString()
          document.cookie = `user_tier=free; path=/; expires=${cookieExpires}; SameSite=Lax`
        } catch (e) {
          console.warn('Could not set user_tier cookie locally', e)
        }

        // Show success state briefly then redirect
        setPaymentStep("success")
        setTimeout(() => {
          // Set flag to show agent selection modal after entering dashboard
          sessionStorage.setItem('from-pricing', 'true')
          window.location.href = "/dashboard"
        }, 800)
      } else {
        // For paid tiers, call backend to get Paystack authorization URL
        setPaymentStep("payment") // Show processing state

        try {
          // Trigger subscription creation which returns authorization_url
          const result = await useBillingStore.getState().createSubscription(tier, "paystack")

          if (result?.authorization_url) {
            // Redirect to Paystack checkout page
            window.location.href = result.authorization_url
          } else {
            console.error("No authorization_url in response:", result)
            setError("Failed to generate payment link. Please try again.")
            setPaymentStep("error")
          }
        } catch (err: any) {
          console.error("Failed to create subscription:", err)
          setError(err?.message || "Failed to initiate payment. Please try again.")
          setPaymentStep("error")
        }
      }
    } catch (err: any) {
      console.error("Error in handleSelectTier:", err)
      setError(err?.message || "Failed to process tier selection. Please try again.")
      setSelectedTier(null)
    }
  }

  // realPlans are populated from the billing store; no duplicate unsuppressed fetch here

  // Handle payment submission
  const handlePaymentSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    try {
      // Check authentication first
      if (!apiClient.isAuthenticated()) {
        setError("You must be logged in to complete a payment. Please log in and try again.")
        setPaymentStep("error")
        return
      }

      // Basic validation
      if (!cardNumber || !cardExpiry || !cardCvv || !cardName) {
        setError("Please fill in all fields")
        return
      }

      const cleanCardNumber = cardNumber.replace(/\s/g, "")
      if (cleanCardNumber.length < 16) {
        setError("Please enter a valid card number (16+ digits)")
        return
      }

      if (cardExpiry.length < 5) {
        setError("Please enter a valid expiry date (MM/YY)")
        return
      }

      if (cardCvv.length < 3) {
        setError("Please enter a valid CVV (3-4 digits)")
        return
      }

      if (cardName.trim().length < 2) {
        setError("Please enter a valid name on card")
        return
      }

      if (!selectedTier || selectedTier === "free") {
        setError("No tier selected. Please select a plan first.")
        return
      }

      setPaymentStep("processing")

      try {
        // Create subscription with Paystack
        console.log("Creating subscription for tier:", selectedTier, "period:", billingPeriod)

        const response = await apiClient.createSubscription(
          selectedTier,
          "paystack",
          billingPeriod,
          { suppressRedirect: true }
        )

        console.log("Subscription response:", response)

        if (response?.payment_url) {
          // Redirect to Paystack payment page
          console.log("Redirecting to Paystack:", response.payment_url)
          window.location.href = response.payment_url
        } else if (response?.status === "active") {
          // Subscription created successfully without payment needed
          setPaymentStep("success")
          // Redirect to dashboard after a short delay
          setTimeout(() => {
            sessionStorage.setItem('from-pricing', 'true')
            window.location.href = "/dashboard"
          }, 2000)
        } else {
          // Unexpected response format
          setError("Unexpected response from server. Please contact support if this continues.")
          setPaymentStep("error")
        }
      } catch (apiError) {
        console.error("API Error creating subscription:", apiError)
        let errorMessage = 'Subscription creation failed'

        if (apiError instanceof Error) {
          errorMessage = apiError.message
          // Handle specific error messages
          if (errorMessage.includes('already has an active subscription')) {
            errorMessage = 'You already have an active subscription. Please contact support to upgrade.'
          } else if (errorMessage.includes('not found')) {
            errorMessage = 'User account not found. Please log in again.'
          }
        }

        setError(errorMessage)
        setPaymentStep("error")
      }
    } catch (error) {
      console.error("Payment submission error:", error)
      setError(error instanceof Error ? error.message : 'Payment processing failed. Please try again.')
      setPaymentStep("error")
    }
  }

  // Reset payment flow
  const resetPayment = () => {
    setPaymentStep("select")
    setSelectedTier(null)
    setError(null)
  }

  // Retry payment after error
  const retryPayment = () => {
    setPaymentStep("payment")
    setError(null)
  }

  return (
    <div className="min-h-screen bg-white flex flex-col relative z-10">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="container mx-auto px-4 py-4 2xl:px-12 3xl:px-16 max-w-7xl 2xl:max-w-[1400px] 3xl:max-w-[1600px] flex items-center justify-between">
          <Link href="/" className="flex items-center">
            <span className="text-slate-900 font-extrabold text-2xl">
              Agent<span className="text-green-500">47</span>
            </span>
          </Link>

          <Link href="/onboarding" className="text-green-600 hover:text-green-700 transition-colors flex items-center">
            <ArrowLeft className="w-4 h-4 mr-1" />
            Back to Onboarding
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-grow">
        {/* Hero Section */}
        <section className="py-12 bg-gradient-to-b from-gray-50 to-white">
          <div className="container mx-auto px-4 2xl:px-12 3xl:px-16 max-w-7xl 2xl:max-w-[1400px] 3xl:max-w-[1600px]">
            <div className="text-center max-w-3xl mx-auto">
              <h1 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">Hire Your Digital Workforce</h1>
              <p className="text-lg text-gray-600 mb-8">
                Select the plan that best fits your needs. All plans include access to our powerful AI employees.
              </p>

              {/* Billing Period Toggle */}
              <div className="flex items-center justify-center mb-8">
                <span className={`mr-3 ${billingPeriod === "monthly" ? "text-green-600 font-semibold" : "text-gray-500"}`}>
                  Monthly
                </span>
                <button
                  onClick={() => setBillingPeriod(billingPeriod === "monthly" ? "yearly" : "monthly")}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${billingPeriod === "yearly" ? "bg-green-600" : "bg-gray-300"
                    }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${billingPeriod === "yearly" ? "translate-x-6" : "translate-x-1"
                      }`}
                  />
                </button>
                <span className={`ml-3 ${billingPeriod === "yearly" ? "text-green-600 font-semibold" : "text-gray-500"}`}>
                  Yearly
                </span>
                {billingPeriod === "yearly" && (
                  <span className="ml-2 bg-green-100 text-green-800 text-xs font-medium px-2 py-1 rounded-full">
                    Save 10%
                  </span>
                )}
              </div>
            </div>
          </div>
        </section>

        {/* Pricing Cards Section */}
        <section className="py-12">
          <div className="container mx-auto px-4 2xl:px-12 3xl:px-16 max-w-7xl 2xl:max-w-[1400px] 3xl:max-w-[1600px]">
            <AnimatePresence mode="wait">
              {paymentStep === "select" && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto"
                >
                  {billingPlans.length > 0 ? (
                    billingPlans.map((plan) => {
                      const tier = plan.tier.toLowerCase() as PricingTier
                      const isCurrentPlan = currentSubscription?.tier === plan.tier
                      const isUpgrade = currentSubscription &&
                        (plan.tier === 'pro' && currentSubscription.tier === 'starter') ||
                        (plan.tier === 'starter' && currentSubscription.tier === 'free')
                      const isDowngrade = currentSubscription &&
                        (plan.tier === 'starter' && currentSubscription.tier === 'pro') ||
                        (plan.tier === 'free' && currentSubscription.tier === 'starter')

                      return (
                        <motion.div
                          key={tier}
                          whileHover={{ scale: 1.02 }}
                          className={cn(
                            "bg-white rounded-xl overflow-hidden shadow-lg border",
                            plan.recommended ? "border-[#10B981]" : "border-gray-200",
                            plan.recommended ? "md:-mt-4" : "",
                          )}
                        >
                          {plan.recommended && (
                            <div className="bg-[#10B981] text-white text-center py-2 font-medium">Recommended</div>
                          )}

                          <div className={cn("p-6 text-white bg-gradient-to-r",
                            plan.tier === 'free' ? "from-green-400 to-green-600" :
                              plan.tier === 'starter' ? "from-green-400 to-green-600" :
                                plan.tier === 'pro' ? "from-green-500 to-green-700" :
                                  "from-green-400 to-green-600"
                          )}>
                            <h3 className="text-2xl font-bold mb-2">{plan.name}</h3>
                            <div className="flex items-baseline">
                              <span className="text-3xl font-bold">${plan.price_usd}</span>
                              <span className="ml-2 opacity-80">/{plan.billing_cycle}</span>
                            </div>
                            <p className="mt-2 opacity-90">{plan.description}</p>
                            {isCurrentPlan && (
                              <div className="mt-2 bg-white/20 rounded px-2 py-1 text-sm">
                                Current Plan
                              </div>
                            )}
                          </div>

                          <div className="p-6">
                            <ul className="space-y-3 mb-8">
                              {plan.features?.agents && (
                                <li className="flex items-start">
                                  <Check className="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                                  <span>
                                    {plan.features.agents.max_count ?
                                      `${plan.features.agents.max_count} AI employees` :
                                      'Full AI workforce'
                                    }
                                  </span>
                                </li>
                              )}
                              {plan.features?.api_access && (
                                <li className="flex items-start">
                                  <Check className="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                                  <span>
                                    {plan.features.api_rate_limits ?
                                      `${plan.features.api_rate_limits.requests_per_minute} requests/min` :
                                      'API access'
                                    }
                                  </span>
                                </li>
                              )}
                              {plan.features?.storage_limit_mb && (
                                <li className="flex items-start">
                                  <Check className="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                                  <span>
                                    {plan.features.storage_limit_mb} MB storage
                                  </span>
                                </li>
                              )}
                              {plan.features?.support && (
                                <li className="flex items-start">
                                  <Check className="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                                  <span className="capitalize">
                                    {plan.features.support.replace('_', ' ')} support
                                  </span>
                                </li>
                              )}
                              {plan.features?.custom_integrations && (
                                <li className="flex items-start">
                                  <Check className="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                                  <span>Custom integrations</span>
                                </li>
                              )}
                              {plan.features?.advanced_analytics && (
                                <li className="flex items-start">
                                  <Check className="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                                  <span>Advanced analytics</span>
                                </li>
                              )}
                            </ul>

                            <button
                              onClick={() => handleSelectTier(tier)}
                              disabled={isCurrentPlan || loading}
                              className={cn(
                                "w-full py-3 rounded-lg font-medium transition-colors",
                                isCurrentPlan
                                  ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                                  : tier === "free"
                                    ? "bg-green-500 text-white hover:bg-green-600"
                                    : "bg-green-600 text-white hover:bg-green-700",
                              )}
                            >
                              {loading ? (
                                <Loader2 className="w-4 h-4 animate-spin mx-auto" />
                              ) : isCurrentPlan ? (
                                "Current Plan"
                              ) : isUpgrade ? (
                                "Upgrade"
                              ) : isDowngrade ? (
                                "Downgrade"
                              ) : tier === "free" ? (
                                "Get Started Free"
                              ) : (
                                "Choose Plan"
                              )}
                            </button>
                          </div>
                        </motion.div>
                      )
                    })) : (
                    // Fallback to static plans while loading
                    (Object.keys(PRICING_PLANS) as PricingTier[]).map((tier) => {
                      const plan = PRICING_PLANS[tier]
                      return (
                        <motion.div
                          key={tier}
                          whileHover={{ scale: 1.03, y: -5 }}
                          className={cn(
                            "bg-white rounded-2xl overflow-hidden shadow-xl border-2 transition-all duration-300",
                            plan.recommended ? "border-green-500 shadow-green-100" : "border-gray-200 hover:border-gray-300",
                            plan.recommended ? "md:-mt-4 md:mb-4" : "",
                          )}
                        >
                          {plan.recommended && (
                            <div className="bg-gradient-to-r from-green-500 to-green-600 text-white text-center py-2.5 font-bold text-sm tracking-wide">
                              ⭐ MOST POPULAR
                            </div>
                          )}

                          <div className={cn("relative p-8 text-white bg-gradient-to-br overflow-hidden", plan.color)}>
                            <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16 blur-2xl"></div>
                            <div className="relative z-10">
                              <h3 className="text-3xl font-extrabold mb-3">{plan.name}</h3>
                              <div className="flex items-baseline mb-2">
                                <span className="text-5xl font-black">
                                  ${billingPeriod === "yearly" ? plan.yearlyPrice : plan.price}
                                </span>
                                <span className="ml-2 text-xl opacity-90">
                                  /{billingPeriod === "yearly" ? "year" : plan.period}
                                </span>
                              </div>
                              {billingPeriod === "yearly" && plan.price > 0 && (
                                <div className="text-sm opacity-90 mt-2 bg-white/20 px-3 py-1 rounded-full inline-block">
                                  ${(plan.yearlyPrice / 12).toFixed(2)}/month billed yearly
                                </div>
                              )}
                              <p className="mt-4 text-lg opacity-95 font-medium">{plan.description}</p>
                            </div>
                          </div>

                          <div className="p-8">
                            <ul className="space-y-4 mb-8">
                              {plan.features.map((feature, index) => (
                                <li key={index} className="flex items-start">
                                  <div className="flex-shrink-0 w-6 h-6 bg-green-100 rounded-full flex items-center justify-center mr-3 mt-0.5">
                                    <Check className="w-4 h-4 text-green-600" />
                                  </div>
                                  <span className="text-gray-700 font-medium">{feature}</span>
                                </li>
                              ))}
                            </ul>

                            <button
                              onClick={() => handleSelectTier(tier)}
                              disabled={loading}
                              className={cn(
                                "w-full py-4 rounded-xl font-bold text-lg transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-105",
                                "bg-gradient-to-r from-green-500 to-green-600 text-white hover:from-green-600 hover:to-green-700",
                                loading && "opacity-70 cursor-not-allowed hover:scale-100"
                              )}
                            >
                              {loading ? (
                                <Loader2 className="w-5 h-5 animate-spin mx-auto" />
                              ) : tier === "free" ? (
                                "Get Started Free"
                              ) : (
                                "Choose Plan"
                              )}
                            </button>
                          </div>
                        </motion.div>
                      )
                    })
                  )}
                </motion.div>
              )}

              {paymentStep === "payment" && selectedTier && PRICING_PLANS[selectedTier] && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="max-w-4xl mx-auto"
                >
                  <div className="bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden">
                    {/* Header Section */}
                    <div className={cn("relative p-8 text-white bg-gradient-to-br", PRICING_PLANS[selectedTier].color)}>
                      <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -mr-32 -mt-32 blur-3xl"></div>
                      <div className="relative z-10">
                        <button
                          onClick={resetPayment}
                          className="mb-4 text-white/80 hover:text-white transition-colors flex items-center text-sm"
                        >
                          <ArrowLeft className="w-4 h-4 mr-1" />
                          Back to Plans
                        </button>
                        <h3 className="text-3xl font-bold mb-2">{PRICING_PLANS[selectedTier].name} Plan</h3>
                        <div className="flex items-baseline mb-2">
                          <span className="text-5xl font-extrabold">
                            ${billingPeriod === "yearly" ? PRICING_PLANS[selectedTier].yearlyPrice : PRICING_PLANS[selectedTier].price}
                          </span>
                          <span className="ml-3 text-xl opacity-90">
                            /{billingPeriod === "yearly" ? "year" : PRICING_PLANS[selectedTier].period}
                          </span>
                        </div>
                        {billingPeriod === "yearly" && PRICING_PLANS[selectedTier].price > 0 && (
                          <div className="text-sm opacity-90 mt-2">
                            ${(PRICING_PLANS[selectedTier].yearlyPrice / 12).toFixed(2)}/month billed yearly
                            <span className="ml-2 bg-white/20 px-2 py-1 rounded-full text-xs font-medium">
                              Save 10%
                            </span>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="p-8 md:p-10">
                      <div className="grid md:grid-cols-2 gap-8">
                        {/* Order Summary */}
                        <div className="space-y-6">
                          <div>
                            <h4 className="text-xl font-bold text-gray-900 mb-4">Order Summary</h4>
                            <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-6 border border-gray-200">
                              <div className="space-y-4">
                                <div className="flex justify-between items-center pb-4 border-b border-gray-200">
                                  <span className="font-semibold text-gray-900">{PRICING_PLANS[selectedTier].name} Plan</span>
                                  <span className="font-bold text-lg text-gray-900">
                                    ${billingPeriod === "yearly" ? PRICING_PLANS[selectedTier].yearlyPrice : PRICING_PLANS[selectedTier].price}
                                  </span>
                                </div>

                                <div className="space-y-2">
                                  <div className="flex items-start text-sm text-gray-600">
                                    <Check className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                                    <span>{PRICING_PLANS[selectedTier].agents} Personnel</span>
                                  </div>
                                  <div className="flex items-start text-sm text-gray-600">
                                    <Check className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                                    <span>{PRICING_PLANS[selectedTier].support}</span>
                                  </div>
                                  <div className="flex items-start text-sm text-gray-600">
                                    <Check className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                                    <span>{PRICING_PLANS[selectedTier].integrations} Integrations</span>
                                  </div>
                                </div>

                                <div className="pt-4 border-t border-gray-200">
                                  <div className="flex justify-between items-center mb-2">
                                    <span className="text-sm text-gray-600">Billing Period</span>
                                    <span className="text-sm font-medium text-gray-900 capitalize">{billingPeriod}</span>
                                  </div>
                                  <div className="flex justify-between items-center">
                                    <span className="text-lg font-semibold text-gray-900">Total</span>
                                    <span className="text-2xl font-bold text-gray-900">
                                      ${billingPeriod === "yearly" ? PRICING_PLANS[selectedTier].yearlyPrice : PRICING_PLANS[selectedTier].price}
                                      <span className="text-sm font-normal text-gray-600 ml-1">
                                        /{billingPeriod === "yearly" ? "year" : "month"}
                                      </span>
                                    </span>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>

                          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
                            <div className="flex items-start">
                              <Shield className="w-5 h-5 text-blue-600 mr-3 flex-shrink-0 mt-0.5" />
                              <div className="text-sm text-blue-900">
                                <p className="font-semibold mb-1">Secure Payment</p>
                                <p className="text-blue-700">Your payment is processed securely by Paystack. We never store your card details.</p>
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Payment Form */}
                        <div>
                          <h4 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
                            <CreditCard className="w-6 h-6 mr-2 text-green-600" />
                            Payment Details
                          </h4>

                          <form onSubmit={handlePaymentSubmit} className="space-y-5">
                            <div>
                              <label htmlFor="cardNumber" className="block text-sm font-semibold text-gray-700 mb-2">
                                Card Number
                              </label>
                              <div className="relative">
                                <input
                                  type="text"
                                  id="cardNumber"
                                  value={cardNumber}
                                  onChange={(e) => setCardNumber(formatCardNumber(e.target.value))}
                                  placeholder="1234 5678 9012 3456"
                                  maxLength={19}
                                  className="w-full h-12 px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all bg-gray-50 focus:bg-white text-gray-900 font-medium"
                                  required
                                />
                                <CreditCard className="absolute right-4 top-3.5 w-5 h-5 text-gray-400" />
                              </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <label htmlFor="cardExpiry" className="block text-sm font-semibold text-gray-700 mb-2">
                                  Expiry Date
                                </label>
                                <input
                                  type="text"
                                  id="cardExpiry"
                                  value={cardExpiry}
                                  onChange={(e) => setCardExpiry(formatExpiryDate(e.target.value))}
                                  placeholder="MM/YY"
                                  maxLength={5}
                                  className="w-full h-12 px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all bg-gray-50 focus:bg-white text-gray-900 font-medium"
                                  required
                                />
                              </div>

                              <div>
                                <label htmlFor="cardCvv" className="block text-sm font-semibold text-gray-700 mb-2">
                                  CVV
                                </label>
                                <input
                                  type="text"
                                  id="cardCvv"
                                  value={cardCvv}
                                  onChange={(e) => setCvv(e.target.value.replace(/\D/g, "").slice(0, 4))}
                                  placeholder="123"
                                  maxLength={4}
                                  className="w-full h-12 px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all bg-gray-50 focus:bg-white text-gray-900 font-medium"
                                  required
                                />
                              </div>
                            </div>

                            <div>
                              <label htmlFor="cardName" className="block text-sm font-semibold text-gray-700 mb-2">
                                Name on Card
                              </label>
                              <input
                                type="text"
                                id="cardName"
                                value={cardName}
                                onChange={(e) => setCardName(e.target.value)}
                                placeholder="John Doe"
                                className="w-full h-12 px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all bg-gray-50 focus:bg-white text-gray-900 font-medium"
                                required
                              />
                            </div>

                            {error && (
                              <motion.div
                                initial={{ opacity: 0, y: -10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="bg-red-50 border-2 border-red-200 text-red-700 px-4 py-3 rounded-xl flex items-start"
                              >
                                <AlertCircle className="w-5 h-5 mr-2 flex-shrink-0 mt-0.5" />
                                <span className="text-sm font-medium">{error}</span>
                              </motion.div>
                            )}

                            <button
                              type="submit"
                              className="w-full h-14 bg-gradient-to-r from-green-500 to-green-600 text-white font-bold text-lg rounded-xl hover:from-green-600 hover:to-green-700 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-[1.02] flex items-center justify-center group"
                            >
                              <span>Complete Payment</span>
                              <ChevronRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
                            </button>

                            <div className="flex items-center justify-center text-xs text-gray-500 pt-2">
                              <Lock className="w-4 h-4 mr-1" />
                              Secured by Paystack • SSL Encrypted
                            </div>
                          </form>
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}

              {paymentStep === "processing" && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="max-w-md mx-auto text-center py-12"
                >
                  <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-8">
                    <div className="w-16 h-16 border-4 border-t-[#3B82F6] border-gray-200 rounded-full animate-spin mx-auto mb-6"></div>
                    <h3 className="text-xl font-semibold mb-2">Processing Your Payment</h3>
                    <p className="text-gray-600">Please wait while we process your payment...</p>
                  </div>
                </motion.div>
              )}

              {paymentStep === "success" && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0 }}
                  className="max-w-md mx-auto text-center py-12"
                >
                  <div className="bg-white rounded-xl shadow-lg border border-green-200 p-8">
                    <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                      <Check className="w-8 h-8 text-green-600" />
                    </div>
                    <h3 className="text-xl font-semibold mb-2">Payment Successful!</h3>
                    <p className="text-gray-600 mb-6">
                      {selectedTier === "free"
                        ? "Your free plan has been activated. Enjoy your 14-day trial!"
                        : selectedTier === "starter"
                          ? "Your starter plan has been activated."
                          : "Your payment has been processed successfully."}
                    </p>
                    <p className="text-gray-600">Redirecting you to the dashboard...</p>
                  </div>
                </motion.div>
              )}

              {paymentStep === "error" && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0 }}
                  className="max-w-md mx-auto text-center py-12"
                >
                  <div className="bg-white rounded-xl shadow-lg border border-red-200 p-8">
                    <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
                      <X className="w-8 h-8 text-red-600" />
                    </div>
                    <h3 className="text-xl font-semibold mb-2">Payment Failed</h3>
                    <p className="text-gray-600 mb-6">
                      {error || "There was an issue processing your payment. Please try again."}
                    </p>
                    <button
                      onClick={retryPayment}
                      className="bg-[#3B82F6] text-white py-2 px-6 rounded-lg font-medium hover:bg-[#2563EB] transition-colors"
                    >
                      Try Again
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Comparison Toggle */}
            {paymentStep === "select" && (
              <div className="text-center mt-12">
                <button
                  onClick={() => setShowComparison(!showComparison)}
                  className="text-[#3B82F6] hover:text-[#2563EB] transition-colors font-medium"
                >
                  {showComparison ? "Hide Detailed Comparison" : "Show Detailed Comparison"}
                </button>
              </div>
            )}
          </div>
        </section>

        {/* Comparison Table */}
        <AnimatePresence>
          {showComparison && paymentStep === "select" && (
            <motion.section
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="py-8 bg-gray-50 overflow-hidden"
            >
              <div className="container mx-auto px-4 2xl:px-12 3xl:px-16 max-w-7xl 2xl:max-w-[1400px] 3xl:max-w-[1600px]">
                <h2 className="text-2xl font-bold text-center mb-8 text-slate-900">Plan Comparison</h2>

                {/* Desktop Comparison Table */}
                <div className="hidden md:block max-w-5xl mx-auto overflow-hidden rounded-xl border border-gray-200">
                  <table className="w-full bg-white">
                    <thead>
                      <tr className="bg-gray-50">
                        <th className="py-4 px-6 text-left text-gray-600 font-medium">Feature</th>
                        <th className="py-4 px-6 text-center text-gray-600 font-medium">Free</th>
                        <th className="py-4 px-6 text-center text-gray-600 font-medium">Starter</th>
                        <th className="py-4 px-6 text-center text-gray-600 font-medium">Pro</th>
                      </tr>
                    </thead>
                    <tbody>
                      {COMPARISON_FEATURES.map((feature, index) => (
                        <tr key={index}>
                          <td className="py-4 px-6 border-t border-gray-200">{feature.name}</td>
                          <td className="py-4 px-6 text-center border-t border-gray-200">
                            {typeof feature.free === "boolean" ? (
                              feature.free ? (
                                <Check className="w-5 h-5 text-green-500 mx-auto" />
                              ) : (
                                <X className="w-5 h-5 text-gray-300 mx-auto" />
                              )
                            ) : (
                              feature.free
                            )}
                          </td>
                          <td className="py-4 px-6 text-center border-t border-gray-200">
                            {typeof feature.starter === "boolean" ? (
                              feature.starter ? (
                                <Check className="w-5 h-5 text-green-500 mx-auto" />
                              ) : (
                                <X className="w-5 h-5 text-gray-300 mx-auto" />
                              )
                            ) : (
                              feature.starter
                            )}
                          </td>
                          <td className="py-4 px-6 text-center border-t border-gray-200">
                            {typeof feature.pro === "boolean" ? (
                              feature.pro ? (
                                <Check className="w-5 h-5 text-green-500 mx-auto" />
                              ) : (
                                <X className="w-5 h-5 text-gray-300 mx-auto" />
                              )
                            ) : (
                              feature.pro
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Mobile Comparison Cards */}
                <div className="md:hidden space-y-6">
                  {(Object.keys(PRICING_PLANS) as PricingTier[]).map((tier) => (
                    <div key={tier} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                      <div className={cn("p-4 text-white bg-gradient-to-r", PRICING_PLANS[tier].color)}>
                        <h3 className="text-xl font-bold">{PRICING_PLANS[tier].name}</h3>
                      </div>
                      <div className="p-4">
                        <ul className="space-y-3">
                          {COMPARISON_FEATURES.map((feature, index) => (
                            <li key={index} className="flex items-center justify-between">
                              <span className="text-gray-700">{feature.name}</span>
                              <span className="ml-4">
                                {typeof feature[tier] === "boolean" ? (
                                  feature[tier] ? (
                                    <Check className="w-5 h-5 text-green-500" />
                                  ) : (
                                    <X className="w-5 h-5 text-gray-300" />
                                  )
                                ) : (
                                  <span className="font-medium">{feature[tier]}</span>
                                )}
                              </span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </motion.section>
          )}
        </AnimatePresence>

        {/* FAQ Section */}
        {paymentStep === "select" && (
          <section className="py-16">
            <div className="container mx-auto px-4 2xl:px-12 3xl:px-16 max-w-7xl 2xl:max-w-[1400px] 3xl:max-w-[1600px]">
              <div className="max-w-3xl mx-auto">
                <h2 className="text-2xl font-bold text-center mb-8 text-slate-900">Frequently Asked Questions</h2>

                <div className="space-y-4">
                  {[
                    {
                      question: "What happens after the Free tier's 14 days?",
                      answer:
                        "After the 14-day trial period, your account will automatically switch to a limited mode where you can use up to 5 actions per day. You'll still have access to your dashboard and data, but with restricted functionality. You can upgrade to a paid plan at any time to restore full access.",
                    },
                    {
                      question: "Can I switch agents later?",
                      answer:
                        "Yes! Starter and Pro plans allow you to swap agents monthly. You can manage your agent selection from your dashboard at any time, and changes will take effect at the start of your next billing cycle.",
                    },
                    {
                      question: "How does Paystack work?",
                      answer:
                        "Paystack is our secure payment processor that supports credit/debit cards, bank transfers, and mobile money options. Your payment information is never stored on our servers. Paystack uses industry-standard encryption to ensure your financial data remains safe.",
                    },
                    {
                      question: "Can I cancel anytime?",
                      answer:
                        "Yes, you can cancel your subscription at any time from your account dashboard with no cancellation fees. Your plan will remain active until the end of your current billing cycle, after which you'll be downgraded to the limited Free tier.",
                    },
                  ].map((faq, index) => (
                    <details key={index} className="bg-white rounded-lg border border-gray-200 overflow-hidden group">
                      <summary className="flex justify-between items-center p-4 cursor-pointer font-medium">
                        {faq.question}
                        <span className="transition-transform group-open:rotate-180">
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="24"
                            height="24"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            className="w-5 h-5"
                          >
                            <polyline points="6 9 12 15 18 9"></polyline>
                          </svg>
                        </span>
                      </summary>
                      <div className="p-4 pt-0 text-gray-600">{faq.answer}</div>
                    </details>
                  ))}
                </div>
              </div>
            </div>
          </section>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-[#1F2937] text-white py-6">
        <div className="container mx-auto px-4 text-center">
          <p className="text-sm">
            Powered by{" "}
            <a
              href="https://nexonic.industries"
              target="_blank"
              rel="noopener noreferrer"
              className="text-green-500 hover:underline"
            >
              Nexonic Industries
            </a>
          </p>
        </div>
      </footer>
    </div>
  )
}
