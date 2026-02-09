"use client"

import { useState } from "react"
import Link from "next/link"
import { motion, AnimatePresence } from "framer-motion"
import { ArrowLeft, Check, ChevronDown, ChevronUp, Calendar, Target, Zap, Rocket, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import Header from "@/components/header"
import Footer from "@/components/footer"

interface Member {
  name: string
  description: string
  color: string
}

interface Phase {
  name: string
  tagline: string
  status: "current" | "upcoming" | "future"
  timeline: string
  color: string
  gradient: string
  icon: typeof Zap
  goals: string[]
  features: string[]
  personnel: Member[]
  personnelCount: number
  targetPersonnelCount?: number
}

const phases: Phase[] = [
  {
    name: "Phase 1: BETA",
    tagline: "Foundation & Testing",
    status: "current",
    timeline: "July 2025 - January 2026",
    color: "text-blue-600",
    gradient: "from-blue-600 to-cyan-400",
    icon: Zap,
    goals: [
      "Launch core AI automation platform with 7 essential personnel",
      "Build strong community and gather user feedback",
      "Establish brand presence and market positioning",
      "Test system stability and performance at scale",
      "Refine personnel collaboration and intercommunication",
      "Expand to 15 personnel by January 2026",
    ],
    features: [
      "7 Core AI Personnel (Aria, Clara, Eric, Jackie, Shakes, Joe, Purity)",
      "Aria: Social Media Automation - Post scheduling, AI captions, media generation, engagement analytics",
      "Clara: Customer Support - 24/7 support, multichannel, automated responses, sentiment analysis",
      "Eric: Sales Automation - Lead generation, CRM automation, sales outreach, forecasting",
      "Jackie: Marketing Automation - Campaign management, SEO, ad management, influencer marketing",
      "Shakes: Content Creation - AI content generation, SEO optimization, content calendar, brand voice",
      "Joe: Research Agent - Data collection, web scraping, document processing, NLP summarization",
      "Purity: Business Development - Idea generator, validation tool, business model canvas, brand builder",
      "Chat & Voice Control Interface",
      "Workforce Intercommunication System",
      "Basic Analytics Dashboard",
      "Email & Slack Integrations",
      "24/7 Customer Support",
      "Web & Mobile Apps",
      "User Feedback Portal",
      "Target: 15 Personnel by January 2026",
    ],
    personnelCount: 7,
    targetPersonnelCount: 15,
    personnel: [
      { name: "Aria", description: "Social Media Automation", color: "bg-orange-500" },
      { name: "Clara", description: "Customer Support AI", color: "bg-purple-500" },
      { name: "Eric", description: "Sales Optimization", color: "bg-blue-500" },
      { name: "Jackie", description: "Marketing Campaigns", color: "bg-pink-500" },
      { name: "Shakes", description: "Content Creation", color: "bg-green-500" },
      { name: "Joe", description: "Research & Data Analysis", color: "bg-sky-400" },
      { name: "Purity", description: "Business Strategy", color: "bg-gray-800" },
    ],
  },
  {
    name: "Phase 2: ALPHA",
    tagline: "Optimization & Expansion",
    status: "upcoming",
    timeline: "February 2026 - June 2026",
    color: "text-purple-600",
    gradient: "from-purple-600 to-rose-500",
    icon: Target,
    goals: [
      "Achieve peak automation efficiency across all workflows",
      "Launch comprehensive API and documentation",
      "Introduce custom personnel builder for enterprise clients",
      "Replace underperforming personnel with advanced alternatives",
      "Scale infrastructure for 100,000+ concurrent users",
      "Integrate advanced AI models (GPT-5, Claude 3.5)",
      "Expand to 15 specialized personnel",
    ],
    features: [
      "15 Specialized AI Personnel",
      "Custom Personnel Builder (No-Code)",
      "REST API & SDKs (Python, JavaScript, Go)",
      "Comprehensive Documentation Portal",
      "Advanced Personnel Analytics & Insights",
      "Workflow Automation Templates",
      "Multi-Language Support (50+ languages)",
      "Enterprise SSO & RBAC",
      "Advanced Security Features (SOC 2, ISO 27001)",
      "AI Model Selection (Choose your LLM)",
      "Webhook & Real-Time Events",
    ],
    personnelCount: 0,
    targetPersonnelCount: 15,
    personnel: [],
  },
  {
    name: "Phase 3: SIGMA",
    tagline: "Next-Generation Intelligence",
    status: "future",
    timeline: "July 2026 - December 2026",
    color: "text-emerald-600",
    gradient: "from-green-500 to-emerald-600",
    icon: Rocket,
    goals: [
      "Deploy AGI-adjacent personnel with reasoning capabilities",
      "Enable true autonomous decision-making",
      "Integrate quantum computing for complex problem-solving",
      "Create self-evolving personnel that improve without human input",
      "Establish Agent47 as the world's most advanced AI platform",
      "Push the boundaries of what's possible with AI automation",
      "Expand to 17 advanced specialized personnel",
    ],
    features: [
      "17 Advanced Specialized AI Personnel",
      "AGI-Adjacent Reasoning Engines",
      "Quantum Computing Integration",
      "Self-Evolving Workforce Architecture",
      "Autonomous Decision-Making Systems",
      "Neural Interface Compatibility",
      "Holographic AI Interfaces",
      "Multi-Modal AI (Text, Voice, Vision, Touch)",
      "Predictive Scenario Modeling",
      "Real-Time Language Translation (200+ languages)",
      "Cross-Platform Universal Personnel",
      "Zero-Latency Global Infrastructure",
      "Blockchain-Verified AI Actions",
    ],
    personnelCount: 0,
    targetPersonnelCount: 17,
    personnel: [],
  },
]

export default function RoadmapPage() {
  const [expandedPhase, setExpandedPhase] = useState<number | null>(0)

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      <Header />

      <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8 2xl:px-12 3xl:px-16">
        <div className="max-w-7xl mx-auto 2xl:max-w-[1400px] 3xl:max-w-[1600px]">
          {/* Back Button */}
          <Link
            href="/"
            className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-8"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Home
          </Link>

          {/* Header */}
          <motion.div
            className="text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <Badge className="mb-4 bg-gradient-to-r from-green-400 to-green-600 text-white">
              <Sparkles className="w-3 h-3 mr-1" />
              Building the Future of AI Automation
            </Badge>
            <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">Agent47 Roadmap</h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Our journey to deploy 47 specialized AI personnel across three transformative phases, revolutionizing
              automation and pushing the boundaries of artificial intelligence.
            </p>
          </motion.div>

          {/* Timeline Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
            {phases.map((phase, index) => (
              <motion.div
                key={index}
                className="bg-white rounded-2xl p-6 shadow-lg border border-gray-200"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
              >
                <div
                  className={`w-12 h-12 rounded-xl bg-gradient-to-r ${phase.gradient} flex items-center justify-center mb-4 shadow-md`}
                  style={phase.name.includes("BETA") ? {
                    background: "linear-gradient(to right, #2563eb, #22d3ee)"
                  } : undefined}
                >
                  <phase.icon className="w-6 h-6 text-white drop-shadow-sm" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-2">
                  {phase.personnelCount} {phase.targetPersonnelCount && phase.targetPersonnelCount > phase.personnelCount ? `→ ${phase.targetPersonnelCount}` : ""} Employees
                </h3>
                <p className={`text-sm font-semibold ${phase.color} mb-1`}>{phase.name.split(":")[1]}</p>
                <p className="text-sm text-gray-500">{phase.timeline}</p>
              </motion.div>
            ))}
          </div>

          {/* Phase Timeline */}
          <div className="relative">
            {/* Vertical Line */}
            <div className="absolute left-8 top-0 bottom-0 w-1 bg-gradient-to-b from-green-400 via-green-500 to-green-600"></div>

            {/* Phases */}
            <div className="space-y-12">
              {phases.map((phase, index) => (
                <motion.div
                  key={index}
                  className="relative"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.6, delay: index * 0.2 }}
                >
                  {/* Timeline Dot */}
                  <div
                    className={`absolute left-6 top-8 w-5 h-5 rounded-full bg-gradient-to-r ${phase.gradient} border-4 border-white shadow-lg z-10`}
                    style={phase.name.includes("BETA") ? {
                      background: "linear-gradient(to right, #2563eb, #22d3ee)"
                    } : undefined}
                  ></div>

                  {/* Phase Card */}
                  <div className="ml-20 bg-white rounded-2xl shadow-xl border border-gray-200 overflow-hidden">
                    {/* Header */}
                    <div
                      className={`bg-gradient-to-r ${phase.gradient} p-6 cursor-pointer shadow-lg`}
                      style={phase.name.includes("BETA") ? {
                        background: "linear-gradient(to right, #2563eb, #22d3ee)"
                      } : undefined}
                      onClick={() => setExpandedPhase(expandedPhase === index ? null : index)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                          <div className="w-12 h-12 bg-white/30 rounded-xl flex items-center justify-center backdrop-blur-sm shadow-lg">
                            <phase.icon className="w-6 h-6 text-white drop-shadow-md" />
                          </div>
                          <div>
                            <h2 className="text-2xl font-bold text-white">{phase.name}</h2>
                            <p className="text-white/90">{phase.tagline}</p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-4">
                          <Badge className="bg-white/20 text-white border-white/30">
                            {phase.status === "current"
                              ? "In Progress"
                              : phase.status === "upcoming"
                                ? "Coming Soon"
                                : "Future"}
                          </Badge>
                          {expandedPhase === index ? (
                            <ChevronUp className="w-6 h-6 text-white" />
                          ) : (
                            <ChevronDown className="w-6 h-6 text-white" />
                          )}
                        </div>
                      </div>
                      <div className="mt-4 flex items-center text-white/90">
                        <Calendar className="w-4 h-4 mr-2" />
                        <span className="text-sm">{phase.timeline}</span>
                        <span className="mx-3">•</span>
                        <span className="text-sm">
                          {phase.personnelCount} {phase.targetPersonnelCount && phase.targetPersonnelCount > phase.personnelCount ? `→ ${phase.targetPersonnelCount}` : ""} Personnel
                        </span>
                      </div>
                    </div>

                    {/* Expanded Content */}
                    <AnimatePresence>
                      {expandedPhase === index && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.3 }}
                          className="overflow-hidden"
                        >
                          <div className="p-6 space-y-6">
                            {/* Goals */}
                            <div>
                              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                                <Target className="w-5 h-5 mr-2 text-blue-500" />
                                Phase Goals
                              </h3>
                              <ul className="space-y-2">
                                {phase.goals.map((goal, i) => (
                                  <li key={i} className="flex items-start">
                                    <Check className="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                                    <span className="text-gray-700">{goal}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>

                            {/* Features */}
                            <div>
                              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                                <Sparkles className="w-5 h-5 mr-2 text-purple-500" />
                                Key Features
                              </h3>
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                {phase.features.map((feature, i) => (
                                  <div
                                    key={i}
                                    className="flex items-start p-3 bg-gray-50 rounded-lg"
                                  >
                                    <Zap className="w-4 h-4 text-yellow-500 mr-2 mt-0.5 flex-shrink-0" />
                                    <span className="text-sm text-gray-700">{feature}</span>
                                  </div>
                                ))}
                              </div>
                            </div>

                            {/* AI Personnel */}
                            {phase.personnel.length > 0 && (
                              <div>
                                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                                  <Rocket className="w-5 h-5 mr-2 text-orange-500" />
                                  AI Personnel ({phase.personnelCount}{phase.targetPersonnelCount && phase.targetPersonnelCount > phase.personnelCount ? ` → ${phase.targetPersonnelCount}` : ""})
                                </h3>
                                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                                  {phase.personnel.map((agent, i) => (
                                    <div
                                      key={i}
                                      className="flex items-center p-4 bg-gray-50 rounded-xl border border-gray-200 hover:shadow-lg transition-shadow"
                                    >
                                      <div
                                        className={`w-10 h-10 ${agent.color} rounded-full flex items-center justify-center text-white font-bold mr-3 flex-shrink-0`}
                                      >
                                        {agent.name.slice(0, 2)}
                                      </div>
                                      <div className="min-w-0">
                                        <p className="font-semibold text-gray-900 truncate">
                                          {agent.name}
                                        </p>
                                        <p className="text-xs text-gray-600 truncate">
                                          {agent.description}
                                        </p>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                            {phase.personnel.length === 0 && phase.targetPersonnelCount && (
                              <div>
                                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                                  <Rocket className="w-5 h-5 mr-2 text-orange-500" />
                                  Target: {phase.targetAgentCount} Personnel
                                </h3>
                                <p className="text-gray-600">
                                  This phase aims to expand our personnel ecosystem to {phase.targetAgentCount} specialized AI personnel, each designed to handle specific business functions and workflows.
                                </p>
                              </div>
                            )}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>

          {/* CTA Section */}
          <motion.div
            className="mt-20 bg-gradient-to-r from-green-400 to-green-600 rounded-3xl p-12 text-center text-white"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.8 }}
          >
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Ready to Join the Journey?</h2>
            <p className="text-xl mb-8 text-white/90">
              Be part of the Beta phase and help shape the future of AI automation.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Button asChild size="lg" className="bg-white text-green-600 hover:bg-gray-100">
                <Link href="/auth?tab=signup">
                  Start Free Trial
                  <ArrowLeft className="ml-2 w-5 h-5 rotate-180" />
                </Link>
              </Button>
              <Button
                asChild
                size="lg"
                variant="outline"
                className="bg-transparent border-white text-white hover:bg-white/10"
              >
                <Link href="/contact">Contact Sales</Link>
              </Button>
            </div>
          </motion.div>
        </div>
      </section>

      <Footer />
    </main>
  )
}
