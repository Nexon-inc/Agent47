"use client"

import type React from "react"

import { useState, useEffect } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Check, X, ChevronRight, ArrowLeft, CreditCard, Shield, Info, Loader2, AlertCircle } from "lucide-react"
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
    description: "Perfect for trying out Agent47",
    color: "from-green-400 to-green-600",
    agents: 1,
    support: "Community support only",
    integrations: "Basic integrations",
    features: [
      "1 Agent (user chooses)",
      "14-day full access trial",
      "Then limited to 5 actions/day",
      "Basic functionality",
      "No inter-agent communication",
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
      "4 Agents (Purity excluded)",
      "Full agent features",
      "Basic analytics",
      "Advanced Content Creation",
      "Social Media Automation",
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
    agents: "All 7 agents",
    support: "Priority support (12h response)",
    integrations: "Unlimited",
    teamMembers: "Up to 5 team members",
    features: [
      "All 7 Agents Available",
      "Inter-agent communication",
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
    name: "Number of agents",
    free: 1,
    starter: "4 (Purity excluded)",
    pro: "All 7 agents",
  },
  {
    name: "Agent Communication",
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
  const [realPlans, setRealPlans] = useState<BillingPlan[]>([])
  const [currentSubscription, setCurrentSubscription] = useState<any>(null)
  
  const { fetchBillingPlans, fetchSubscription } = useBillingStore()

  // Fetch pricing plans from backend (suppress redirects to avoid reload loops)
  useEffect(() => {
    const loadPricingData = async () => {
      setLoading(true)
      setError(null)

      try {
        await fetchBillingPlans(true)
        const subscriptionData = await fetchSubscription(true)
        setCurrentSubscription(subscriptionData)
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
    setSelectedTier(tier)

    if (tier === "free") {
      // Start local 14-day trial immediately and redirect user to dashboard.
      const expiresAt = new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString()
      try {
        localStorage.setItem('free_trial_expires_at', expiresAt)
      } catch (e) {
        console.warn('Could not persist free trial expiry locally', e)
      }

      // Fire-and-forget backend subscription creation so server record exists if possible
      apiClient.createSubscription("free", "paystack", { suppressRedirect: true }).catch((err) => {
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
      setPaymentStep("payment")
    }
  }

  // realPlans are populated from the billing store; no duplicate unsuppressed fetch here

  // Handle payment submission
  const handlePaymentSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    // Basic validation
    if (!cardNumber.trim() || !cardExpiry.trim() || !cardCvv.trim() || !cardName.trim()) {
      setError("Please fill in all fields")
      return
    }

    if (cardNumber.replace(/\s/g, "").length < 16) {
      setError("Please enter a valid card number")
      return
    }

    if (cardExpiry.length < 5) {
      setError("Please enter a valid expiry date (MM/YY)")
      return
    }

    if (cardCvv.length < 3) {
      setError("Please enter a valid CVV")
      return
    }

    setPaymentStep("processing")

    try {
      if (!selectedTier || selectedTier === "free") {
        throw new Error("No tier selected")
      }

      // Create subscription with Paystack
      const response = await apiClient.createSubscription(selectedTier, "paystack", billingPeriod, { suppressRedirect: true })
      
      if (response.payment_url) {
        // Redirect to Paystack payment page
        window.location.href = response.payment_url
      } else {
        setPaymentStep("success")
        // Redirect to dashboard after a short delay
        setTimeout(() => {
          // Set flag to show agent selection modal after entering dashboard
          sessionStorage.setItem('from-pricing', 'true')
          window.location.href = "/dashboard"
        }, 2000)
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Payment failed')
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
              <h1 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">Choose Your Agent47 Plan</h1>
              <p className="text-lg text-gray-600 mb-8">
                Select the plan that best fits your needs. All plans include access to our powerful AI agents.
              </p>
              
              {/* Billing Period Toggle */}
              <div className="flex items-center justify-center mb-8">
                <span className={`mr-3 ${billingPeriod === "monthly" ? "text-green-600 font-semibold" : "text-gray-500"}`}>
                  Monthly
                </span>
                <button
                  onClick={() => setBillingPeriod(billingPeriod === "monthly" ? "yearly" : "monthly")}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    billingPeriod === "yearly" ? "bg-green-600" : "bg-gray-300"
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      billingPeriod === "yearly" ? "translate-x-6" : "translate-x-1"
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
                  {realPlans.length > 0 ? (
                    realPlans.map((plan) => {
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
                                    `${plan.features.agents.max_count} agents` : 
                                    'Unlimited agents'
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

                        <div className={cn("p-6 text-white bg-gradient-to-r", plan.color)}>
                          <h3 className="text-2xl font-bold mb-2">{plan.name}</h3>
                          <div className="flex items-baseline">
                            <span className="text-3xl font-bold">
                              ${billingPeriod === "yearly" ? plan.yearlyPrice : plan.price}
                            </span>
                            <span className="ml-2 opacity-80">
                              /{billingPeriod === "yearly" ? "year" : plan.period}
                            </span>
                          </div>
                          {billingPeriod === "yearly" && plan.price > 0 && (
                            <div className="text-sm opacity-80 mt-1">
                              ${(plan.yearlyPrice / 12).toFixed(2)}/month billed yearly
                            </div>
                          )}
                          <p className="mt-2 opacity-90">{plan.description}</p>
                        </div>

                        <div className="p-6">
                          <ul className="space-y-3 mb-8">
                            {plan.features.map((feature, index) => (
                              <li key={index} className="flex items-start">
                                <Check className="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                                <span>{feature}</span>
                              </li>
                            ))}
                          </ul>

                          <button
                            onClick={() => handleSelectTier(tier)}
                              disabled={loading}
                            className={cn(
                              "w-full py-3 rounded-lg font-medium transition-colors",
                              tier === "free"
                                ? "bg-green-500 text-white hover:bg-green-600"
                                : "bg-[#3B82F6] text-white hover:bg-[#2563EB]",
                            )}
                          >
                            {loading ? (
                              <Loader2 className="w-4 h-4 animate-spin mx-auto" />
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

              {paymentStep === "payment" && selectedTier && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="max-w-2xl mx-auto"
                >
                  <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
                    <div className={cn("p-6 text-white bg-gradient-to-r", PRICING_PLANS[selectedTier].color)}>
                      <h3 className="text-2xl font-bold mb-2">{PRICING_PLANS[selectedTier].name} Plan</h3>
                      <div className="flex items-baseline">
                        <span className="text-3xl font-bold">
                          ${billingPeriod === "yearly" ? PRICING_PLANS[selectedTier].yearlyPrice : PRICING_PLANS[selectedTier].price}
                        </span>
                        <span className="ml-2 opacity-80">
                          /{billingPeriod === "yearly" ? "year" : PRICING_PLANS[selectedTier].period}
                        </span>
                      </div>
                      {billingPeriod === "yearly" && PRICING_PLANS[selectedTier].price > 0 && (
                        <div className="text-sm opacity-80 mt-1">
                          ${(PRICING_PLANS[selectedTier].yearlyPrice / 12).toFixed(2)}/month billed yearly
                        </div>
                      )}
                    </div>

                    <div className="p-6">
                      <h4 className="text-lg font-semibold mb-4 flex items-center">
                        <CreditCard className="w-5 h-5 mr-2" />
                        Payment Details
                      </h4>

                      <form onSubmit={handlePaymentSubmit}>
                        <div className="space-y-4">
                          <div>
                            <label htmlFor="cardNumber" className="block text-sm font-medium text-gray-700 mb-1">
                              Card Number
                            </label>
                            <input
                              type="text"
                              id="cardNumber"
                              value={cardNumber}
                              onChange={(e) => setCardNumber(formatCardNumber(e.target.value))}
                              placeholder="1234 5678 9012 3456"
                              maxLength={19}
                              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#3B82F6] focus:border-transparent"
                              required
                            />
                          </div>

                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <label htmlFor="cardExpiry" className="block text-sm font-medium text-gray-700 mb-1">
                                Expiry Date
                              </label>
                              <input
                                type="text"
                                id="cardExpiry"
                                value={cardExpiry}
                                onChange={(e) => setCardExpiry(formatExpiryDate(e.target.value))}
                                placeholder="MM/YY"
                                maxLength={5}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#3B82F6] focus:border-transparent"
                                required
                              />
                            </div>

                            <div>
                              <label htmlFor="cardCvv" className="block text-sm font-medium text-gray-700 mb-1">
                                CVV
                              </label>
                              <input
                                type="text"
                                id="cardCvv"
                                value={cardCvv}
                                onChange={(e) => setCvv(e.target.value.replace(/\D/g, "").slice(0, 4))}
                                placeholder="123"
                                maxLength={4}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#3B82F6] focus:border-transparent"
                                required
                              />
                            </div>
                          </div>

                          <div>
                            <label htmlFor="cardName" className="block text-sm font-medium text-gray-700 mb-1">
                              Name on Card
                            </label>
                            <input
                              type="text"
                              id="cardName"
                              value={cardName}
                              onChange={(e) => setCardName(e.target.value)}
                              placeholder="John Doe"
                              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#3B82F6] focus:border-transparent"
                              required
                            />
                          </div>

                          {error && (
                            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md flex items-start">
                              <Info className="w-5 h-5 mr-2 flex-shrink-0" />
                              <span>{error}</span>
                            </div>
                          )}

                          <div className="flex items-center justify-between pt-4">
                            <button
                              type="button"
                              onClick={resetPayment}
                              className="text-gray-600 hover:text-gray-800 transition-colors"
                            >
                              Go Back
                            </button>

                            <button
                              type="submit"
                              className="bg-[#3B82F6] text-white py-2 px-6 rounded-lg font-medium hover:bg-[#2563EB] transition-colors flex items-center"
                            >
                              Pay Now
                              <ChevronRight className="ml-1 w-4 h-4" />
                            </button>
                          </div>

                          <div className="flex items-center justify-center mt-6 text-sm text-gray-500">
                            <Shield className="w-4 h-4 mr-1" />
                            Secure payment powered by Paystack
                          </div>
                        </div>
                      </form>
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
