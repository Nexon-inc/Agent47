"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { Check, X, ArrowRight, Loader2, AlertCircle } from "lucide-react"
import Link from "next/link"
import { BillingPlan } from "@/lib/api-client"

interface PricingProps {
  plans?: BillingPlan[]
  isLoading?: boolean
  error?: string | null
}

const defaultPlans = [
  {
    name: "Free",
    description: "Perfect for trying out Agent47.",
    monthlyPrice: 0,
    yearlyPrice: 0,
    features: [
      { included: true, text: "1 Agent (user chooses)" },
      { included: true, text: "14-day full access trial" },
      { included: true, text: "Then limited to 5 actions/day" },
      { included: true, text: "Basic Content Creation" },
      { included: true, text: "Community Support" },
    ],
    cta: "Get Started Free",
    badge: null,
    color: "from-green-400 to-green-600",
    popular: false,
    moneyBack: null,
  },
  {
    name: "Starter",
    description: "Perfect for freelancers and small teams.",
    monthlyPrice: 24.99,
  yearlyPrice: 269.89, // 10% discount: (24.99 * 12) * 0.9
    features: [
      { included: true, text: "4 Agents (Purity excluded)" },
      { included: true, text: "Full agent features" },
      { included: true, text: "Basic analytics" },
      { included: true, text: "Custom Integrations (5 platforms)" },
      { included: true, text: "Email Support (24h response)" },
    ],
    cta: "Choose Plan",
    badge: "Most Popular",
    color: "from-green-400 to-green-600",
    popular: true,
    moneyBack: "7-day money-back guarantee",
  },
  {
    name: "Pro",
    description: "For agencies and growing businesses.",
  monthlyPrice: 79.0,
  yearlyPrice: 853.20, // 10% discount: (79 * 12) * 0.9
    features: [
      { included: true, text: "All 7 Agents Available" },
      { included: true, text: "Inter-agent communication" },
      { included: true, text: "Advanced analytics" },
      { included: true, text: "Team Collaboration (5 members)" },
      { included: true, text: "Priority Support (12h response)" },
    ],
    cta: "Choose Plan",
    badge: null,
    color: "from-green-500 to-green-700",
    popular: false,
    moneyBack: "7-day money-back guarantee",
  },
]

export default function Pricing({ plans = defaultPlans, isLoading = false, error = null }: PricingProps) {
  const [yearly, setYearly] = useState(false)

  if (isLoading) {
    return (
      <section id="pricing" className="py-24 bg-[#FFF8F0] relative overflow-hidden">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-center py-16">
            <Loader2 className="h-8 w-8 animate-spin mr-3" />
            <span className="text-lg">Loading pricing plans...</span>
          </div>
        </div>
      </section>
    )
  }

  if (error) {
    return (
      <section id="pricing" className="py-24 bg-[#FFF8F0] relative overflow-hidden">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-center py-16 text-red-600">
            <AlertCircle className="h-8 w-8 mr-3" />
            <span className="text-lg">{error}</span>
          </div>
        </div>
      </section>
    )
  }

  return (
      <section id="pricing" className="py-24 bg-[#FFF8F0] relative overflow-hidden">
      {/* Background Elements */}
      <div className="absolute top-0 right-0 w-1/3 h-1/3 bg-gradient-to-bl from-green-400/5 to-transparent rounded-full blur-3xl -z-10"></div>
      <div className="absolute bottom-0 left-0 w-1/3 h-1/3 bg-gradient-to-tr from-green-400/5 to-transparent rounded-full blur-3xl -z-10"></div>

      <div className="container mx-auto px-4 2xl:px-12 3xl:px-16 max-w-7xl 2xl:max-w-[1400px] 3xl:max-w-[1600px]">
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          <h2 className="text-3xl md:text-5xl font-extrabold mb-6">
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-green-600">
              Plans for Every Workflow
            </span>
          </h2>
          <p className="text-xl text-gray-600 max-w-[800px] mx-auto">
            Start free, scale with your needs—no hidden fees.
          </p>
        </motion.div>

        <div className="flex justify-center items-center mb-12">
          <span className={`mr-3 ${!yearly ? "font-semibold text-green-600" : "text-gray-600"}`}>Monthly</span>
          <button
            className="relative inline-flex h-6 w-11 items-center rounded-full"
            onClick={() => setYearly(!yearly)}
            aria-checked={yearly}
            aria-label="Monthly or yearly pricing"
            role="switch"
          >
            <span
              className={`absolute inset-0 rounded-full ${yearly ? "bg-gradient-to-r from-green-400 to-green-600" : "bg-gray-300"} transition-colors`}
            />
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white shadow-lg transition-transform ${
                yearly ? "translate-x-6" : "translate-x-1"
              }`}
            />
          </button>
          <span className={`ml-3 flex items-center ${yearly ? "font-semibold text-green-600" : "text-gray-600"}`}>
            Yearly
            {yearly && (
              <span className="ml-2 bg-gradient-to-r from-green-400 to-green-600 text-white text-xs px-2 py-1 rounded-full">
                Save 10%
              </span>
            )}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto 2xl:max-w-[1400px] 3xl:max-w-[1600px]">
          {plans.map((plan, index) => (
            <motion.div
              key={index}
              className={`bg-white rounded-2xl shadow-xl overflow-hidden relative border ${
                plan.popular ? "border-green-500" : "border-gray-200"
              } ${plan.popular ? "md:-mt-4 md:mb-4" : ""}`}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
            >
              {plan.badge && (
                <div className="absolute top-0 right-0 bg-gradient-to-r from-green-400 to-green-600 text-white text-xs font-semibold px-4 py-1 rounded-bl-lg">
                  {plan.badge}
                </div>
              )}

              <div className={`bg-gradient-to-r ${plan.color} p-8 text-white`}>
                <h3 className="text-2xl font-bold mb-2">{plan.name}</h3>
                <p className="text-white/80 mb-4">{plan.description}</p>
                <div className="flex items-baseline">
                  <span className="text-4xl font-bold">
                    {plan.monthlyPrice === 0 ? "Free" : `$${yearly ? (plan.yearlyPrice / 12).toFixed(2) : plan.monthlyPrice}`}
                  </span>
                  {plan.monthlyPrice > 0 && (
                    <span className="text-white/80 ml-2">/mo{yearly && ", billed annually"}</span>
                  )}
                </div>
                {plan.trial && <span className="block text-sm text-white/80 mt-1">for {plan.trial}</span>}
                {plan.moneyBack && <span className="block text-sm text-white/80 mt-1">{plan.moneyBack}</span>}
              </div>

              <div className="p-8">
                <ul className="space-y-4 mb-8">
                  {plan.features.map((feature, i) => (
                    <li key={i} className="flex items-start">
                      {feature.included ? (
                        <Check className="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
                      ) : (
                        <X className="w-5 h-5 text-gray-300 mr-3 flex-shrink-0" />
                      )}
                      <span className={feature.included ? "text-gray-700" : "text-gray-400"}>{feature.text}</span>
                    </li>
                  ))}
                </ul>

                <Link
                  href="/signup"
                  className={`w-full block text-center py-3 px-4 rounded-lg font-semibold transition-all duration-300 flex items-center justify-center ${
                    plan.monthlyPrice === 0
                      ? "bg-gradient-to-r from-[#10B981] to-[#34D399] text-white hover:shadow-lg hover:shadow-[#10B981]/20"
                      : plan.popular
                      ? "bg-gradient-to-r from-green-400 to-green-600 text-white hover:shadow-lg hover:shadow-green-500/20"
                      : "bg-gradient-to-r from-gray-200 to-gray-300 text-gray-800 hover:from-gray-300 hover:to-gray-400"
                  }`}
                >
                  {plan.cta}
                  <ArrowRight className="ml-2 w-4 h-4" />
                </Link>
              </div>

              {plan.popular && (
                <div className="absolute -bottom-px left-0 right-0 h-1 bg-gradient-to-r from-green-400 to-green-600"></div>
              )}
            </motion.div>
          ))}
        </div>

      </div>
    </section>
  )
}
