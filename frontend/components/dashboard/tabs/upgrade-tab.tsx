"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { Check, Crown, Zap, Shield, ArrowRight, Loader2, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { useUserStore } from "@/lib/stores/user-store"
import { apiClient } from "@/lib/api-client"
import { cn } from "@/lib/utils"

export default function UpgradeTab() {
    const { userPlan, refreshProfile } = useUserStore()
    const [isLoading, setIsLoading] = useState(false)
    const [billingPeriod, setBillingPeriod] = useState<"monthly" | "yearly">("monthly")
    const [error, setError] = useState<string | null>(null)

    const plans = [
        {
            id: "starter",
            name: "Starter",
            tier: "starter",
            price: billingPeriod === "monthly" ? 49 : 529,
            description: "Perfect for solopreneurs starting their first team.",
            features: [
                "Hire 3 Specialized AI Employees",
                "14-Day Free Trial",
                "Full Platform & Tool Access",
                "Unlimited Tasks for your Agents",
                "Email Support (24h response)",
            ],
            color: "from-green-400 to-green-600",
            recommended: userPlan === "free",
        },
        {
            id: "pro",
            name: "Pro",
            tier: "pro",
            price: billingPeriod === "monthly" ? 149 : 1609,
            description: "Your comprehensive 24/7 digital workforce.",
            features: [
                "Hire All 7 AI Employees",
                "Inter-Employee Communication",
                "Team Strategic Briefing",
                "Unlimited Multi-Agent Workflows",
                "Priority Support (12h response)",
            ],
            color: "from-green-500 to-green-700",
            recommended: userPlan === "starter",
        },
    ]

    // Filter plans to only show upgrades
    const upgradePlans = plans.filter(plan => {
        if (userPlan === "free") return true
        if (userPlan === "starter") return plan.tier === "pro"
        return false
    })

    const handleUpgrade = async (tier: string) => {
        setIsLoading(true)
        setError(null)
        try {
            const response = await apiClient.createSubscription(tier, "paystack", billingPeriod)
            if (response && response.authorization_url) {
                window.location.href = response.authorization_url
            } else {
                throw new Error("Failed to generate payment link. Please try again.")
            }
        } catch (err: any) {
            console.error("Upgrade error:", err)
            setError(err.message || "Something went wrong. Please try again.")
            setIsLoading(false)
        }
    }

    if (userPlan === "pro") {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6">
                <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mb-6">
                    <Crown className="w-10 h-10 text-green-600" />
                </div>
                <h2 className="text-3xl font-bold text-gray-900 mb-2">You're on the Pro Plan!</h2>
                <p className="text-gray-600 max-w-md mx-auto mb-8">
                    You already have access to all features and agents. Thank you for being a Pro user!
                </p>
                <Button onClick={() => window.location.href = "/dashboard?tab=home"}>
                    Back to Dashboard
                </Button>
            </div>
        )
    }

    return (
        <div className="p-6 max-w-6xl mx-auto">
            <div className="text-center mb-10">
                <h1 className="text-3xl font-bold text-gray-900 mb-4">Upgrade Your Experience</h1>
                <p className="text-gray-600 max-w-2xl mx-auto">
                    Scale your business with more agents and advanced features. Choose the plan that's right for you.
                </p>

                {/* Billing Toggle */}
                <div className="flex items-center justify-center mt-8 gap-4">
                    <span className={cn("text-sm font-medium", billingPeriod === "monthly" ? "text-gray-900" : "text-gray-500")}>
                        Monthly
                    </span>
                    <button
                        onClick={() => setBillingPeriod(billingPeriod === "monthly" ? "yearly" : "monthly")}
                        className={cn(
                            "relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2",
                            billingPeriod === "yearly" ? "bg-green-600" : "bg-gray-200"
                        )}
                    >
                        <span
                            className={cn(
                                "inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-200",
                                billingPeriod === "yearly" ? "translate-x-6" : "translate-x-1"
                            )}
                        />
                    </button>
                    <span className={cn("text-sm font-medium", billingPeriod === "yearly" ? "text-gray-900" : "text-gray-500")}>
                        Yearly <span className="text-green-600 font-bold">(Save 10%)</span>
                    </span>
                </div>
            </div>

            {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-8 text-center">
                    {error}
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 justify-center max-w-4xl mx-auto">
                {upgradePlans.map((plan) => (
                    <Card
                        key={plan.id}
                        className={cn(
                            "relative flex flex-col transition-all duration-300 hover:shadow-2xl border-2",
                            plan.recommended ? "border-green-500 shadow-green-100" : "border-gray-100"
                        )}
                    >
                        {plan.recommended && (
                            <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-green-500 text-white px-4 py-1 rounded-full text-xs font-bold tracking-wider">
                                RECOMMENDED
                            </div>
                        )}

                        <CardHeader className="text-center pb-2">
                            <CardTitle className="text-2xl font-bold">{plan.name}</CardTitle>
                            <CardDescription>{plan.description}</CardDescription>
                        </CardHeader>

                        <CardContent className="flex-grow pt-4">
                            <div className="text-center mb-6">
                                <span className="text-4xl font-bold">${plan.price}</span>
                                <span className="text-gray-500 ml-1 font-medium">/{billingPeriod === "monthly" ? "mo" : "yr"}</span>
                            </div>

                            <ul className="space-y-3">
                                {plan.features.map((feature, idx) => (
                                    <li key={idx} className="flex items-start text-sm text-gray-700">
                                        <Check className="w-5 h-5 text-green-500 mr-2 shrink-0" />
                                        <span>{feature}</span>
                                    </li>
                                ))}
                            </ul>
                        </CardContent>

                        <CardFooter className="pt-6">
                            <Button
                                onClick={() => handleUpgrade(plan.tier)}
                                disabled={isLoading}
                                className={cn(
                                    "w-full py-6 text-lg font-bold transition-all",
                                    plan.recommended ? "bg-green-600 hover:bg-green-700" : "bg-gray-900 hover:bg-black"
                                )}
                            >
                                {isLoading ? (
                                    <>
                                        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                                        Processing...
                                    </>
                                ) : (
                                    <>
                                        Upgrade to {plan.name}
                                        <ArrowRight className="ml-2 h-5 w-5" />
                                    </>
                                )}
                            </Button>
                        </CardFooter>
                    </Card>
                ))}
            </div>

            <div className="mt-16 bg-slate-50 rounded-2xl p-8 border border-slate-100">
                <div className="grid md:grid-cols-3 gap-8 text-center">
                    <div className="space-y-3">
                        <div className="w-12 h-12 bg-white rounded-full shadow-sm flex items-center justify-center mx-auto">
                            <Shield className="w-6 h-6 text-indigo-600" />
                        </div>
                        <h4 className="font-bold">Secure Payment</h4>
                        <p className="text-sm text-gray-500">Fast and secure payments processed via Paystack.</p>
                    </div>
                    <div className="space-y-3">
                        <div className="w-12 h-12 bg-white rounded-full shadow-sm flex items-center justify-center mx-auto">
                            <Zap className="w-6 h-6 text-amber-500" />
                        </div>
                        <h4 className="font-bold">Instant Activation</h4>
                        <p className="text-sm text-gray-500">Get access to your new features immediately after payment.</p>
                    </div>
                    <div className="space-y-3">
                        <div className="w-12 h-12 bg-white rounded-full shadow-sm flex items-center justify-center mx-auto">
                            <Sparkles className="w-6 h-6 text-emerald-500" />
                        </div>
                        <h4 className="font-bold">Priority Support</h4>
                        <p className="text-sm text-gray-500">Jump the queue with our dedicated premium support team.</p>
                    </div>
                </div>
            </div>
        </div>
    )
}
