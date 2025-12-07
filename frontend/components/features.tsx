"use client"

import React, { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  Globe,
  Headphones,
  FileText,
  BarChart3,
  DollarSign,
  X,
  Check,
  ArrowRight,
  Lightbulb,
  Search,
} from "lucide-react"

const agents = [
  {
    name: "Aria - Social Media Agent",
    icon: Globe,
    color: "bg-gradient-to-br from-green-400 to-green-600",
    lightColor: "bg-orange-50",
    textColor: "text-[#FF6B1A]",
    description: [
      "Schedule posts across platforms with AI-optimized timing.",
      "Analyze sentiment and respond to comments in real-time.",
      "Generate trending hashtags and visuals for engagement.",
      "Monitor campaigns with unified analytics dashboards.",
    ],
    stats: {
      automationRate: "92%",
      timeReduction: "4.5h",
      engagementIncrease: "37%",
    },
  },
  {
    name: "Clara - Customer Support Agent",
    icon: Headphones,
    color: "bg-gradient-to-br from-purple-400 to-purple-600",
    lightColor: "bg-purple-50",
    textColor: "text-purple-600",
    description: [
      "Handle inquiries via email, chat, and social in 50+ languages.",
      "Detect intent and personalize replies with CRM data.",
      "Escalate complex issues to humans with full context.",
      "Build dynamic FAQs from past interactions.",
    ],
    stats: {
      responseTime: "< 30s",
      resolutionRate: "78%",
      customerSatisfaction: "94%",
    },
  },
  {
    name: "Shakes - Content Creation Agent",
    icon: FileText,
    color: "bg-gradient-to-br from-green-400 to-green-600",
    lightColor: "bg-green-50",
    textColor: "text-green-600",
    description: [
      "Write SEO-optimized blogs, scripts, and whitepapers.",
      "Generate video storyboards with stock footage suggestions.",
      "Edit drafts iteratively based on your feedback.",
      "Localize content for global audiences.",
    ],
    stats: {
      contentQuality: "89%",
      creationSpeed: "5x faster",
      seoRankingImprovement: "43%",
    },
  },
  {
    name: "Jackie - Marketing Agent",
    icon: BarChart3,
    color: "bg-gradient-to-br from-pink-400 to-pink-600",
    lightColor: "bg-pink-50",
    textColor: "text-pink-600",
    description: [
      "Segment audiences with data-driven insights.",
      "Automate email, SMS, and ad campaigns with A/B tests.",
      "Track ROI across platforms like Google Ads, Meta.",
      "Analyze competitors and suggest counter-strategies.",
    ],
    stats: {
      campaignEfficiency: "3.2x",
      conversionIncrease: "28%",
      budgetOptimization: "31%",
    },
  },
  {
    name: "Eric - Sales Agent",
    icon: DollarSign,
    color: "bg-gradient-to-br from-amber-400 to-amber-600",
    lightColor: "bg-amber-50",
    textColor: "text-amber-600",
    description: [
      "Score leads with predictive models for higher conversions.",
      "Craft personalized outreach emails and follow-ups.",
      "Manage pipelines with CRM integrations (Salesforce, HubSpot).",
      "Forecast sales with 90% accuracy using AI models.",
    ],
    stats: {
      leadQualification: "47% better",
      closingRate: "36% higher",
      forecastAccuracy: "90%",
    },
  },
  {
    name: "Purity - Business Maker Agent",
    icon: Lightbulb,
    color: "bg-gradient-to-br from-gray-800 to-black",
    lightColor: "bg-gray-50",
    textColor: "text-gray-800",
    description: [
      "Generate tailored business ideas based on trends and market data.",
      "Validate opportunities with competitor analysis and SEO insights.",
      "Create automated Business Model Canvas and customer personas.",
      "Build MVP blueprints with prioritized features and tools.",
    ],
    stats: {
      ideaGeneration: "500+ ideas",
      validationAccuracy: "87%",
      timeToLaunch: "60% faster",
    },
  },
  {
    name: "Joe - Research Agent",
    icon: Search,
    color: "bg-gradient-to-br from-teal-500 to-cyan-600",
    lightColor: "bg-teal-50",
    textColor: "text-teal-600",
    description: [
      "Collect data from Wikipedia, Google Search, and YouTube APIs.",
      "Scrape websites and process PDFs with advanced NLP.",
      "Generate reports in multiple formats (PDF, DOCX, JSON, Markdown).",
      "Support multilingual research with real-time translation.",
    ],
    stats: {
      dataAccuracy: "96%",
      researchSpeed: "10x faster",
      sourcesProcessed: "1000+",
    },
  },
]

export default function Features() {
  const [selectedAgent, setSelectedAgent] = useState<number | null>(null)
  const [activeTab, setActiveTab] = useState<number>(0)

  return (
      <section id="features" className="py-24 bg-white relative overflow-hidden">
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
              Meet Your AI Workforce
            </span>
          </h2>
          <p className="text-xl text-gray-600 max-w-[800px] mx-auto">
            Our agents specialize in automating your toughest tasks—pick one or mix them all.
          </p>
        </motion.div>

        {/* Agent Tabs */}
        <div className="flex flex-wrap justify-center gap-4 mb-12">
          {agents.map((agent, index) => (
            <motion.button
              key={index}
              className={`px-6 py-3 rounded-full font-medium text-sm md:text-base transition-all duration-300 ${
                activeTab === index
                  ? `${agent.color} text-white shadow-lg`
                  : `bg-white/90 ${agent.textColor} hover:bg-opacity-100 hover:shadow border border-gray-200`
              }`}
              onClick={() => setActiveTab(index)}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
            >
              <div className="flex items-center">
                <agent.icon className="w-5 h-5 mr-2" />
                {agent.name.split(" - ")[0]}
              </div>
            </motion.button>
          ))}
        </div>

        {/* Active Agent Content */}
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.5 }}
            className="max-w-6xl mx-auto 2xl:max-w-[1400px] 3xl:max-w-[1600px]"
          >
            <div className="bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100">
              <div className={`${agents[activeTab].color} px-8 py-6 text-white`}>
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center">
                  <div className="flex items-center mb-4 md:mb-0">
                    <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center mr-4">
                      {React.createElement(agents[activeTab].icon, { size: 24 })}
                    </div>
                    <div>
                      <h3 className="text-2xl font-bold">{agents[activeTab].name}</h3>
                      <p className="text-white/80">
                        Automate your {agents[activeTab].name.split(" - ")[1].toLowerCase()} tasks
                      </p>
                    </div>
                  </div>
                  <button
                    className="px-6 py-2 bg-white/20 hover:bg-white/30 rounded-lg text-white font-medium transition-colors flex items-center"
                    onClick={() => setSelectedAgent(activeTab)}
                  >
                    Learn More <ArrowRight className="ml-2 w-4 h-4" />
                  </button>
                </div>
              </div>

              <div className="p-8">
                <div className="grid md:grid-cols-2 gap-8">
                  <div>
                    <h4 className="text-lg font-semibold text-gray-800 mb-4">Key Capabilities</h4>
                    <ul className="space-y-3">
                      {agents[activeTab].description.map((item, i) => (
                        <li key={i} className="flex items-start">
                          <Check className={`w-5 h-5 ${agents[activeTab].textColor} mr-3 mt-0.5`} />
                          <span className="text-gray-700">{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <h4 className="text-lg font-semibold text-gray-800 mb-4">Performance Metrics</h4>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                      {Object.entries(agents[activeTab].stats).map(([key, value], i) => (
                        <div key={i} className={`${agents[activeTab].lightColor} rounded-xl p-4`}>
                          <div className={`text-sm ${agents[activeTab].textColor} mb-1`}>
                            {key.replace(/([A-Z])/g, " $1").replace(/^./, (str) => str.toUpperCase())}
                          </div>
                          <div className="text-2xl font-bold text-gray-800">{value}</div>
                        </div>
                      ))}
                    </div>

                    <div className="mt-6 pt-6 border-t border-gray-100">
                      <div className="flex justify-between items-center">
                        <div className="text-gray-500">Average time saved per week</div>
                        <div className="text-xl font-bold text-green-600">9.5 hours</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </AnimatePresence>

        {/* Agent Modal */}
        <AnimatePresence>
          {selectedAgent !== null && (
            <motion.div
              className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 backdrop-blur-sm"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSelectedAgent(null)}
            >
              <motion.div
                className="bg-white rounded-2xl max-w-4xl w-full max-h-[80vh] overflow-y-auto"
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                transition={{ type: "spring", damping: 25 }}
                onClick={(e) => e.stopPropagation()}
              >
                <div className={`${agents[selectedAgent].color} p-8 text-white relative`}>
                  <button
                    onClick={() => setSelectedAgent(null)}
                    className="absolute top-4 right-4 text-white hover:text-white/80 transition-colors"
                    aria-label="Close modal"
                  >
                    <X size={24} />
                  </button>

                  <div className="flex items-center mb-6">
                    <div className="w-16 h-16 bg-white/20 rounded-xl flex items-center justify-center mr-6">
                      {React.createElement(agents[selectedAgent].icon, { size: 32 })}
                    </div>
                    <div>
                      <h3 className="text-3xl font-bold">{agents[selectedAgent].name}</h3>
                      <p className="text-white/80 text-lg">Advanced AI automation for your workflow</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    {Object.entries(agents[selectedAgent].stats).map(([key, value], i) => (
                      <div key={i} className="bg-white/10 rounded-xl p-4">
                        <div className="text-white/80 text-sm mb-1">
                          {key.replace(/([A-Z])/g, " $1").replace(/^./, (str) => str.toUpperCase())}
                        </div>
                        <div className="text-xl font-bold">{value}</div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="p-8">
                  <div className="grid md:grid-cols-2 gap-8">
                    <div>
                      <h4 className="text-xl font-semibold text-gray-800 mb-4">All Capabilities</h4>
                      <ul className="space-y-4">
                        {agents[selectedAgent].description.map((item, i) => (
                          <li key={i} className="flex items-start">
                            <Check className={`w-5 h-5 ${agents[selectedAgent].textColor} mr-3 mt-0.5 flex-shrink-0`} />
                            <span className="text-gray-700">{item}</span>
                          </li>
                        ))}
                      </ul>

                      <div className="mt-8">
                        <h4 className="text-xl font-semibold text-gray-800 mb-4">Integration Options</h4>
                        <div className="grid grid-cols-2 gap-3">
                          {["Slack", "Gmail", "Zapier", "Salesforce", "HubSpot", "Notion"].map((item, i) => (
                            <div key={i} className="flex items-center">
                              <div className="w-8 h-8 bg-gray-200 rounded-md mr-2"></div>
                              <span className="text-gray-700">{item}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div>
                      <h4 className="text-xl font-semibold text-gray-800 mb-4">How It Works</h4>
                      <div className="space-y-6">
                        {[
                          {
                            title: "Connect Your Tools",
                            desc: `${agents[selectedAgent].name.split(" - ")[0]} integrates with your existing platforms to access necessary data.`,
                          },
                          {
                            title: "Configure Workflows",
                            desc: "Set up automation rules and preferences through our intuitive dashboard.",
                          },
                          {
                            title: "Monitor & Optimize",
                            desc: "Track performance metrics and fine-tune your agent's behavior for optimal results.",
                          },
                        ].map((step, i) => (
                          <div key={i} className="flex">
                            <div
                              className={`w-8 h-8 ${agents[selectedAgent].color} rounded-full flex items-center justify-center text-white font-bold mr-4 flex-shrink-0`}
                            >
                              {i + 1}
                            </div>
                            <div>
                              <h5 className="font-semibold text-gray-800">{step.title}</h5>
                              <p className="text-gray-600">{step.desc}</p>
                            </div>
                          </div>
                        ))}
                      </div>

                      <div className="mt-8 p-6 bg-gray-50 rounded-xl">
                        <h4 className="text-lg font-semibold text-gray-800 mb-3">Customer Success Story</h4>
                        <p className="text-gray-600 italic mb-4">
                          "{agents[selectedAgent].name.split(" - ")[0]} helped us reduce our{" "}
                          {agents[selectedAgent].name.split(" - ")[1].toLowerCase()} workload by 73% while improving
                          quality. It's been a game-changer for our team."
                        </p>
                        <div className="flex items-center">
                          <div className="w-10 h-10 bg-gray-300 rounded-full mr-3"></div>
                          <div>
                            <div className="font-medium text-gray-800">Sarah Johnson</div>
                            <div className="text-sm text-gray-500">Director at TechFlow</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-8 pt-6 border-t border-gray-100 flex justify-end">
                    <button
                      className={`${agents[selectedAgent].color} text-white font-semibold px-6 py-3 rounded-lg transition-all duration-300 hover:shadow-lg`}
                      onClick={() => setSelectedAgent(null)}
                    >
                      Got it
                    </button>
                  </div>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </section>
  )
}
