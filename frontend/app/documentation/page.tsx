"use client"

import { motion } from "framer-motion"
import Link from "next/link"
import { ArrowLeft, BookOpen, Code, Rocket, Zap, Globe, Webhook, Terminal, FileText } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import Header from "@/components/header"
import Footer from "@/components/footer"

export default function DocumentationPage() {
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
              <BookOpen className="w-3 h-3 mr-1" />
              Coming in Phase 2 (Alpha)
            </Badge>
            <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">Documentation & API</h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Comprehensive documentation, API references, and developer tools will be available in Q4 2025 as part of
              our Phase 2 (Alpha) release.
            </p>
          </motion.div>

          {/* Timeline Badge */}
          <motion.div
            className="bg-gradient-to-r from-green-400 to-green-600 rounded-2xl p-8 text-white text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <Rocket className="w-12 h-12 mx-auto mb-4" />
            <h2 className="text-3xl font-bold mb-2">Launch Target: Q4 2025</h2>
            <p className="text-white/90 text-lg">
              Full API access and documentation will be available in Phase 2 (Alpha)
            </p>
          </motion.div>

          {/* What's Coming */}
          <motion.div
            className="bg-white rounded-2xl p-8 shadow-xl border border-gray-200 mb-12"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <h2 className="text-3xl font-bold text-gray-900 mb-8">What's Coming</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[
                {
                  title: "REST API",
                  description: "Full REST API access to all Agent47 features and AI agents",
                  icon: Code,
                  color: "from-blue-500 to-cyan-500",
                },
                {
                  title: "SDKs",
                  description: "Official SDKs for Python, JavaScript, Go, and more",
                  icon: Terminal,
                  color: "from-green-500 to-emerald-500",
                },
                {
                  title: "API Reference",
                  description: "Complete API reference with interactive examples",
                  icon: FileText,
                  color: "from-purple-500 to-pink-500",
                },
                {
                  title: "Integration Guides",
                  description: "Step-by-step guides for popular platforms and tools",
                  icon: BookOpen,
                  color: "from-orange-500 to-red-500",
                },
                {
                  title: "Webhooks",
                  description: "Real-time event notifications via webhooks",
                  icon: Webhook,
                  color: "from-indigo-500 to-purple-500",
                },
                {
                  title: "API Playground",
                  description: "Test API endpoints directly in your browser",
                  icon: Zap,
                  color: "from-yellow-500 to-orange-500",
                },
              ].map((feature, i) => (
                <div
                  key={i}
                  className="p-6 bg-gray-50 rounded-xl border border-gray-200"
                >
                  <div
                    className={`w-12 h-12 rounded-xl bg-gradient-to-r ${feature.color} flex items-center justify-center mb-4`}
                  >
                    <feature.icon className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
                  <p className="text-sm text-gray-600">{feature.description}</p>
                </div>
              ))}
            </div>
          </motion.div>

          {/* API Preview */}
          <motion.div
            className="bg-white rounded-2xl p-8 shadow-xl border border-gray-200 mb-12"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            <h2 className="text-3xl font-bold text-gray-900 mb-6">API Preview</h2>
            <p className="text-gray-700 mb-6">
              Get a sneak peek at how our API will work. Here's an example of sending a task to an AI agent:
            </p>
            <div className="bg-gray-900 rounded-xl p-6 overflow-x-auto">
              <pre className="text-sm text-gray-100">
                <code>{`// Initialize the Agent47 SDK
import { Agent47 } from '@agent47/sdk'

const agent47 = new Agent47({
  apiKey: process.env.AGENT47_API_KEY
})

// Send a task to Aria (Social Media Agent)
const response = await agent47.agents.aria.chat({
  message: "Create a week's worth of Instagram posts about AI automation",
  options: {
    tone: "professional",
    includeHashtags: true,
    includeImages: true
  }
})

console.log(response.content)
// Output: Generated posts with images and hashtags

// Access analytics
const analytics = await agent47.analytics.get({
  agentId: "aria",
  period: "last_7_days"
})

console.log(analytics.totalTasks) // 127
console.log(analytics.successRate) // 98.4%`}</code>
              </pre>
            </div>
          </motion.div>

          {/* Early Access */}
          <motion.div
            className="bg-gradient-to-r from-green-400 to-green-600 rounded-2xl p-12 text-center text-white"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5 }}
          >
            <Globe className="w-16 h-16 mx-auto mb-6" />
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Get Early Access</h2>
            <p className="text-xl mb-8 text-white/90 max-w-2xl mx-auto">
              Sign up to be notified when our API and documentation are available. Early access users will get priority
              access and exclusive benefits.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Button asChild size="lg" className="bg-white text-green-600 hover:bg-gray-100">
                <Link href="/contact">
                  Contact Us for Early Access
                  <ArrowLeft className="ml-2 w-5 h-5 rotate-180" />
                </Link>
              </Button>
              <Button
                asChild
                size="lg"
                variant="outline"
                className="bg-transparent border-white text-white hover:bg-white/10"
              >
                <Link href="/roadmap">View Full Roadmap</Link>
              </Button>
            </div>
          </motion.div>
        </div>
      </section>

      <Footer />
    </main>
  )
}
