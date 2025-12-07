"use client"

import { motion } from "framer-motion"
import { ClipboardCheck, Users, BarChart, ArrowRight } from "lucide-react"
import Link from "next/link"

const steps = [
  {
    title: "1. Sign Up Free",
    description: "Create an account in 30 seconds—no credit card needed.",
    icon: ClipboardCheck,
    color: "from-green-400 to-green-600",
  },
  {
    title: "2. Choose Your Agents",
    description: "Select the AI agents that match your workflow needs.",
    icon: Users,
    color: "from-purple-400 to-purple-600",
  },
  {
    title: "3. Monitor Results",
    description: "Track performance and ROI in your personalized dashboard.",
    icon: BarChart,
    color: "from-green-400 to-green-600",
  },
]

export default function HowItWorks() {
  return (
    <section className="py-24 bg-[#FFF8F0] relative overflow-hidden">
      {/* Background Elements */}
      <div className="absolute inset-0 bg-[#FFF1E5] skew-y-3 -z-10"></div>

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
              Get Started in 3 Simple Steps
            </span>
          </h2>
          <p className="text-xl text-gray-600 max-w-[800px] mx-auto">
            From sign-up to automation, Agent47 is built for speed.
          </p>
        </motion.div>

        <div className="max-w-6xl mx-auto 2xl:max-w-[1400px] 3xl:max-w-[1600px]">
          <div className="grid md:grid-cols-3 gap-8 mb-16 relative">
            {/* Connecting Line */}
            <div className="hidden md:block absolute top-1/3 left-0 w-full h-0.5 bg-gradient-to-r from-green-400 to-green-600 -z-10"></div>

            {steps.map((step, index) => (
              <motion.div
                key={index}
                className="bg-white rounded-2xl shadow-xl overflow-hidden relative z-10"
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.2 }}
              >
                <div className={`bg-gradient-to-r ${step.color} p-6 text-white`}>
                  <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center mb-4">
                    <step.icon className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="text-xl font-bold">{step.title}</h3>
                </div>
                <div className="p-6">
                  <p className="text-gray-600">{step.description}</p>

                  <div className="mt-6 pt-6 border-t border-gray-100">
                    <div className="flex justify-between items-center">
                      <div className="text-sm text-gray-500">Time required</div>
                      <div className="text-sm font-bold text-green-600">
                        {index === 0 ? "30 seconds" : index === 1 ? "2 minutes" : "Ongoing"}
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          <motion.div
            className="text-center"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.6 }}
          >
            <Link
              href="/auth"
              className="group inline-flex items-center bg-gradient-to-r from-green-400 to-green-600 text-white font-semibold px-8 py-4 rounded-lg hover:shadow-lg hover:shadow-green-500/30 transition-all duration-300"
            >
              Try It Now
              <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform duration-300" />
            </Link>

            <p className="mt-6 text-gray-500">No credit card required. Free trial for 14 days.</p>
          </motion.div>
        </div>
      </div>
    </section>
  )
}
