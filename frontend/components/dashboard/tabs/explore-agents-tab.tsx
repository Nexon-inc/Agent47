"use client"

import type React from "react"

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Globe, Headphones, FileText, BarChart3, DollarSign, X, Check, Play, Megaphone, Lightbulb } from "lucide-react"
import { cn } from "@/lib/utils"
import { useUserStore } from "@/lib/stores/user-store"

// Types
type AgentCategory = "all" | "marketing" | "sales" | "support" | "content" | "business"
type SortOption = "popularity" | "newest" | "alphabetical"
type AgentId = "aria" | "clara" | "shakes" | "eric" | "jackie" | "purity" | "future1" | "future2"

interface Agent {
  id: AgentId
  name: string
  title: string
  description: string
  category: AgentCategory[]
  icon: React.ElementType
  color: string
  lightColor: string
  textColor: string
  features: string[]
  popularity: number
  isNew: boolean
  comingSoon: boolean
  freeEligible: boolean
}

export default function ExploreAgentsTab() {
  const { userPlan } = useUserStore()
  const [category, setCategory] = useState<AgentCategory>("all")
  const [sortBy, setSortBy] = useState<SortOption>("popularity")
  const [selectedAgent, setSelectedAgent] = useState<AgentId | null>(null)
  const [selectedAgents, setSelectedAgents] = useState<AgentId[]>(["aria"])

  // Agent data
  const agents: Agent[] = [
    {
      id: "aria",
      name: "Aria",
      title: "Social Media Agent",
      description: "Automate your social media workflow",
      category: ["marketing", "content"],
      icon: Globe,
      color: "bg-gradient-to-br from-[#FF6B1A] to-[#FF8C3E]",
      lightColor: "bg-orange-50",
      textColor: "text-[#FF6B1A]",
      features: [
        "Schedule posts across platforms",
        "Analyze sentiment and engagement",
        "Generate trending hashtags",
        "Monitor campaigns with analytics",
      ],
      popularity: 95,
      isNew: false,
      comingSoon: false,
      freeEligible: true,
    },
    {
      id: "clara",
      name: "Clara",
      title: "Customer Support Agent",
      description: "Handle inquiries and support tickets",
      category: ["support"],
      icon: Headphones,
      color: "bg-gradient-to-br from-purple-400 to-purple-600",
      lightColor: "bg-purple-50",
      textColor: "text-purple-600",
      features: [
        "Handle inquiries in 50+ languages",
        "Detect intent and personalize replies",
        "Escalate complex issues to humans",
        "Build dynamic FAQs",
      ],
      popularity: 90,
      isNew: false,
      comingSoon: false,
      freeEligible: true,
    },
    {
      id: "shakes",
      name: "Shakes",
      title: "Content Creation Agent",
      description: "Create engaging content for your audience",
      category: ["content"],
      icon: FileText,
      color: "bg-gradient-to-br from-green-400 to-green-600",
      lightColor: "bg-green-50",
      textColor: "text-green-600",
      features: [
        "Write SEO-optimized content",
        "Generate video storyboards",
        "Edit drafts based on feedback",
        "Localize content for global audiences",
      ],
      popularity: 80,
      isNew: false,
      comingSoon: false,
      freeEligible: true,
    },
    {
      id: "jackie",
      name: "Jackie",
      title: "Marketing Agent",
      description: "Optimize your marketing campaigns",
      category: ["marketing"],
      icon: Megaphone,
      color: "bg-gradient-to-br from-pink-400 to-pink-600",
      lightColor: "bg-pink-50",
      textColor: "text-pink-600",
      features: [
        "Segment audiences with data",
        "Automate email and ad campaigns",
        "Track ROI across platforms",
        "Analyze competitors",
      ],
      popularity: 85,
      isNew: false,
      comingSoon: false,
      freeEligible: true,
    },
    {
      id: "eric",
      name: "Eric",
      title: "Sales Agent",
      description: "Boost your sales and conversions",
      category: ["sales"],
      icon: DollarSign,
      color: "bg-gradient-to-br from-amber-400 to-amber-600",
      lightColor: "bg-amber-50",
      textColor: "text-amber-600",
      features: [
        "Score leads with predictive models",
        "Craft personalized outreach",
        "Manage pipelines with CRM integrations",
        "Forecast sales with 90% accuracy",
      ],
      popularity: 75,
      isNew: true,
      comingSoon: false,
      freeEligible: true,
    },
    {
      id: "purity",
      name: "Purity",
      title: "Business Maker Agent",
      description: "Launch and scale businesses with AI",
      category: ["business", "marketing"],
      icon: Lightbulb,
      color: "bg-gradient-to-br from-indigo-500 to-indigo-700",
      lightColor: "bg-indigo-50",
      textColor: "text-indigo-600",
      features: [
        "Generate tailored business ideas",
        "Validate opportunities with market data",
        "Create automated business model canvas",
        "Build customer avatars and personas",
        "AI-powered market research and insights",
        "MVP builder blueprint and monetization strategy",
      ],
      popularity: 88,
      isNew: true,
      comingSoon: false,
      freeEligible: true,
    },
    {
      id: "future1",
      name: "Agent #7",
      title: "Data Analysis Agent",
      description: "Transform your data into insights",
      category: ["marketing", "sales"],
      icon: BarChart3,
      color: "bg-gradient-to-br from-blue-400 to-blue-600",
      lightColor: "bg-blue-50",
      textColor: "text-blue-600",
      features: [
        "Analyze complex datasets",
        "Generate visual reports",
        "Identify trends and patterns",
        "Make data-driven recommendations",
      ],
      popularity: 0,
      isNew: false,
      comingSoon: true,
      freeEligible: false,
    },
    {
      id: "future2",
      name: "Agent #8",
      title: "Project Management Agent",
      description: "Keep your projects on track",
      category: ["support"],
      icon: FileText,
      color: "bg-gradient-to-br from-teal-400 to-teal-600",
      lightColor: "bg-teal-50",
      textColor: "text-teal-600",
      features: [
        "Track project milestones",
        "Assign and monitor tasks",
        "Generate progress reports",
        "Identify bottlenecks",
      ],
      popularity: 0,
      isNew: false,
      comingSoon: true,
      freeEligible: false,
    },
  ]

  // Filter and sort agents
  const filteredAgents = agents
    .filter((agent) => category === "all" || agent.category.includes(category))
    .sort((a, b) => {
      if (sortBy === "popularity") return b.popularity - a.popularity
      if (sortBy === "newest") return a.isNew ? -1 : b.isNew ? 1 : 0
      return a.name.localeCompare(b.name) // alphabetical
    })

  // Handle agent selection
  const toggleAgentSelection = (agentId: AgentId) => {
    // For free tier, only allow one agent
    if (userPlan === "free") {
      setSelectedAgents([agentId])
      return
    }

    // For other plans, allow multiple agents based on plan limits
    setSelectedAgents((prev) => {
      if (prev.includes(agentId)) {
        return prev.filter((id) => id !== agentId)
      } else {
        const maxAgents = userPlan === "starter" ? 3 : userPlan === "pro" ? 6 : 999
        if (prev.length >= maxAgents) {
          return [...prev.slice(1), agentId] // Remove oldest, add new
        }
        return [...prev, agentId]
      }
    })
  }

  // Check if agent can be added based on plan
  const canAddAgent = (agent: Agent) => {
    if (agent.comingSoon) return false
    if (selectedAgents.includes(agent.id)) return true

    if (userPlan === "free") {
      return selectedAgents.length === 0 && agent.freeEligible
    }

    const maxAgents = userPlan === "starter" ? 3 : userPlan === "pro" ? 6 : 999
    return selectedAgents.length < maxAgents
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl md:text-3xl font-extrabold text-[#4B0082]  mb-4">Explore Agents</h1>
        <p className="text-gray-600  mb-6">
          Discover AI agents to automate your workflows.
          {userPlan === "free"
            ? " Free tier allows 1 agent."
            : userPlan === "starter"
              ? " Starter plan allows 3 agents."
              : userPlan === "pro"
                ? " Pro plan allows 6 agents."
                : " Ecosystem plan allows unlimited agents."}
        </p>

        {/* Filters */}
        <div className="flex flex-wrap gap-4 mb-6">
          <div className="flex-1 min-w-[200px]">
            <label htmlFor="category" className="block text-sm font-medium text-gray-700  mb-1">
              Category
            </label>
            <select
              id="category"
              value={category}
              onChange={(e) => setCategory(e.target.value as AgentCategory)}
              className="w-full h-10 px-3 rounded-lg border border-gray-300  bg-white  text-gray-900  focus:outline-none focus:ring-2 focus:ring-[#1E90FF]"
            >
              <option value="all">All Categories</option>
              <option value="marketing">Marketing</option>
              <option value="sales">Sales</option>
              <option value="support">Customer Support</option>
              <option value="content">Content Creation</option>
              <option value="business">Business Development</option>
            </select>
          </div>

          {userPlan !== "free" && (
            <div className="flex-1 min-w-[200px]">
              <label htmlFor="sortBy" className="block text-sm font-medium text-gray-700  mb-1">
                Sort By
              </label>
              <select
                id="sortBy"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as SortOption)}
                className="w-full h-10 px-3 rounded-lg border border-gray-300  bg-white  text-gray-900  focus:outline-none focus:ring-2 focus:ring-[#1E90FF]"
              >
                <option value="popularity">Popularity</option>
                <option value="newest">Newest</option>
                <option value="alphabetical">Alphabetical</option>
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Agent Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredAgents.map((agent) => (
          <div
            key={agent.id}
            className={cn(
              "bg-white  rounded-xl shadow-sm border overflow-hidden transition-all",
              selectedAgents.includes(agent.id)
                ? "border-[#1E90FF] [#1E90FF]"
                : "border-gray-200 ",
              "hover:shadow-md",
            )}
          >
            <div className={cn("p-4", agent.color)}>
              <div className="flex justify-between items-start">
                <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
                  <agent.icon className="w-6 h-6 text-white" />
                </div>
                {agent.isNew && (
                  <span className="bg-white/20 rounded-full px-2 py-1 text-xs text-white font-medium">New</span>
                )}
                {agent.comingSoon && (
                  <span className="bg-white/20 rounded-full px-2 py-1 text-xs text-white font-medium">Coming Soon</span>
                )}
              </div>
              <h3 className="text-lg font-semibold text-white mt-3">
                {agent.name} - {agent.title}
              </h3>
              <p className="text-white/80 text-sm mt-1">{agent.description}</p>
            </div>

            <div className="p-4">
              <ul className="space-y-2 mb-4">
                {agent.features.slice(0, 3).map((feature, index) => (
                  <li key={index} className="flex items-start">
                    <Check className={cn("w-4 h-4 mr-2 mt-0.5", agent.textColor)} />
                    <span className="text-sm text-gray-600 ">{feature}</span>
                  </li>
                ))}
              </ul>

              <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-100 ">
                <button
                  onClick={() => setSelectedAgent(agent.id)}
                  className={cn("text-sm font-medium", agent.textColor)}
                >
                  Learn More
                </button>

                <button
                  onClick={() => !agent.comingSoon && toggleAgentSelection(agent.id)}
                  disabled={!canAddAgent(agent) && !selectedAgents.includes(agent.id)}
                  className={cn(
                    "px-3 py-1.5 rounded-lg text-sm font-medium transition-colors",
                    selectedAgents.includes(agent.id)
                      ? "bg-[#1E90FF]/10 text-[#1E90FF]"
                      : agent.comingSoon
                        ? "bg-gray-100  text-gray-400  cursor-not-allowed"
                        : canAddAgent(agent)
                          ? "bg-[#00FF88] text-white hover:bg-[#00FF88]/90"
                          : "bg-gray-100  text-gray-400  cursor-not-allowed",
                  )}
                >
                  {selectedAgents.includes(agent.id)
                    ? "Selected"
                    : agent.comingSoon
                      ? "Coming Soon"
                      : userPlan === "free" && selectedAgents.length > 0 && !selectedAgents.includes(agent.id)
                        ? "Upgrade to Add"
                        : "Add Agent"}
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Agent Detail Modal */}
      <AnimatePresence>
        {selectedAgent && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ type: "spring", damping: 25 }}
              className="bg-white  rounded-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              {(() => {
                const agent = agents.find((a) => a.id === selectedAgent)
                if (!agent) return null

                return (
                  <>
                    <div className={cn("p-6 relative", agent.color)}>
                      <button
                        onClick={() => setSelectedAgent(null)}
                        className="absolute top-4 right-4 text-white/80 hover:text-white"
                      >
                        <X className="w-6 h-6" />
                      </button>

                      <div className="flex items-center">
                        <div className="w-16 h-16 bg-white/20 rounded-xl flex items-center justify-center mr-4">
                          <agent.icon className="w-8 h-8 text-white" />
                        </div>
                        <div>
                          <h3 className="text-2xl font-bold text-white">
                            {agent.name} - {agent.title}
                          </h3>
                          <p className="text-white/80">{agent.description}</p>
                        </div>
                      </div>
                    </div>

                    <div className="p-6">
                      <div className="mb-6">
                        <h4 className="font-semibold text-gray-800  mb-3">Key Features</h4>
                        <ul className="space-y-2">
                          {agent.features.map((feature, index) => (
                            <li key={index} className="flex items-start">
                              <Check className={cn("w-5 h-5 mr-2 mt-0.5", agent.textColor)} />
                              <span className="text-gray-600 ">{feature}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      <div className="mb-6">
                        <h4 className="font-semibold text-gray-800  mb-3">Demo</h4>
                        <div
                          className={cn("aspect-video rounded-lg flex items-center justify-center", agent.lightColor)}
                        >
                          <button className="flex items-center justify-center w-12 h-12 rounded-full bg-white/80 text-gray-800">
                            <Play className="w-5 h-5" />
                          </button>
                        </div>
                        <p className="text-sm text-gray-500  mt-2">
                          Click to watch a demo of {agent.name} in action
                        </p>
                      </div>

                      <div className="flex justify-end">
                        <button
                          onClick={() => {
                            if (!agent.comingSoon) {
                              toggleAgentSelection(agent.id)
                            }
                            setSelectedAgent(null)
                          }}
                          disabled={!canAddAgent(agent) && !selectedAgents.includes(agent.id)}
                          className={cn(
                            "px-6 py-2 rounded-lg font-medium",
                            selectedAgents.includes(agent.id)
                              ? "bg-[#1E90FF]/10 text-[#1E90FF]"
                              : agent.comingSoon
                                ? "bg-gray-100  text-gray-400  cursor-not-allowed"
                                : canAddAgent(agent)
                                  ? "bg-[#00FF88] text-white hover:bg-[#00FF88]/90"
                                  : "bg-gray-100  text-gray-400  cursor-not-allowed",
                          )}
                        >
                          {selectedAgents.includes(agent.id)
                            ? "Agent Selected"
                            : agent.comingSoon
                              ? "Coming Soon"
                              : userPlan === "free" && selectedAgents.length > 0 && !selectedAgents.includes(agent.id)
                                ? "Upgrade to Add"
                                : "Add This Agent"}
                        </button>
                      </div>
                    </div>
                  </>
                )
              })()}
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}
