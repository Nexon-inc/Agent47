"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Check, ChevronDown, ChevronUp, Calendar, Target, Zap, Rocket, Sparkles } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import DocsLayout from "@/components/docs-layout"

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
      "Scale to 15 personnel by January 2026",
    ],
    features: [
      "7 Core AI Specialists",
      "Workforce Intercommunication System",
      "Premium Documentation Portal",
      "Basic Analytics Dashboard",
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
      "Achieve peak automation efficiency",
      "Launch comprehensive API and SDKs",
      "Expand to 15 specialized personnel",
    ],
    features: [
      "Official SDKs (Python, JS, Go)",
      "Personnel API Access",
      "Advanced Workflow Templates",
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
      "Deploy AGI-adjacent reasoning engines",
      "Autonomous Decision-Making Systems",
      "Expansion to 47 elite personnel",
    ],
    features: [
      "Self-Evolving Workforce",
      "Predictive Scenario Modeling",
      "Holographic Interfaces",
    ],
    personnelCount: 0,
    targetPersonnelCount: 47,
    personnel: [],
  },
]

export default function RoadmapPage() {
  const [expandedPhase, setExpandedPhase] = useState<number | null>(0)

  return (
    <DocsLayout>
      <header className="mb-12">
        <Badge className="mb-4 bg-purple-100 text-purple-700 border-purple-200">
          The Journey to 47
        </Badge>
        <h1 className="text-4xl md:text-5xl font-black text-gray-900 tracking-tight mb-6">
          Project Roadmap
        </h1>
        <p className="text-xl text-gray-600 leading-relaxed">
          Our vision for the future of the Agent47 AI workforce across three transformative phases.
        </p>
      </header>

      <section className="space-y-12 mb-16">
        {phases.map((phase, index) => (
          <div key={index} className="bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden hover:border-green-200 transition-all">
            <div
              className={`p-6 bg-gradient-to-r ${phase.gradient} cursor-pointer group`}
              style={phase.name.includes("BETA") ? { background: "linear-gradient(to right, #2563eb, #22d3ee)" } : undefined}
              onClick={() => setExpandedPhase(expandedPhase === index ? null : index)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-white/20 rounded-2xl flex items-center justify-center backdrop-blur-md shadow-inner">
                    <phase.icon className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-white leading-none mb-1">{phase.name}</h2>
                    <p className="text-white/80 text-sm">{phase.tagline}</p>
                  </div>
                </div>
                {expandedPhase === index ? <ChevronUp className="text-white" /> : <ChevronDown className="text-white" />}
              </div>
            </div>

            <AnimatePresence>
              {expandedPhase === index && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="overflow-hidden"
                >
                  <div className="p-8 space-y-8">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                      <div>
                        <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4 flex items-center">
                          <Target size={14} className="mr-2" /> Goals
                        </h3>
                        <ul className="space-y-3">
                          {phase.goals.map((goal, i) => (
                            <li key={i} className="flex items-start text-sm text-gray-600">
                              <Check className="mr-2 text-green-500 shrink-0" size={16} />
                              {goal}
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4 flex items-center">
                          <Sparkles size={14} className="mr-2" /> Features
                        </h3>
                        <div className="grid grid-cols-1 gap-2">
                          {phase.features.map((feature, i) => (
                            <div key={i} className="bg-gray-50 px-3 py-2 rounded-lg text-xs font-medium text-gray-700 flex items-center border border-gray-100">
                              <Zap className="mr-2 text-yellow-500" size={12} />
                              {feature}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>

                    {phase.personnel.length > 0 && (
                      <div className="pt-6 border-t border-gray-100">
                        <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4">Initial Team</h3>
                        <div className="flex flex-wrap gap-3">
                          {phase.personnel.map((p, i) => (
                            <div key={i} className="flex items-center px-3 py-1.5 bg-white border border-gray-200 rounded-full text-xs font-semibold text-gray-700 shadow-sm">
                              <div className={cn("w-2 h-2 rounded-full mr-2", p.color)} />
                              {p.name}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        ))}
      </section>
    </DocsLayout>
  )
}
