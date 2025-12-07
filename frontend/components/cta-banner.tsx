"use client"

import { motion } from "framer-motion"
import { ArrowRight } from "lucide-react"
import Link from "next/link"

export default function CtaBanner() {
  return (
    <section className="py-16 relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-r from-green-400 to-green-600 -z-10"></div>
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10">
        <div className="absolute top-[20%] -right-[10%] w-[40%] h-[40%] rounded-full bg-white/5 blur-3xl"></div>
        <div className="absolute -bottom-[10%] -left-[10%] w-[40%] h-[40%] rounded-full bg-white/5 blur-3xl"></div>
      </div>

      <div className="container mx-auto px-4 2xl:px-12 3xl:px-16 max-w-7xl 2xl:max-w-[1400px] 3xl:max-w-[1600px]">
        <motion.div
          className="max-w-4xl mx-auto text-center text-white"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          <h2 className="text-3xl md:text-4xl font-bold mb-6">Ready to Transform Your Workflow?</h2>
          <p className="text-lg md:text-xl text-white/80 mb-8 max-w-2xl mx-auto">
            Join thousands of businesses saving 47+ hours per week with our AI agents. Start free, scale as you grow.
          </p>

          <div className="flex flex-col sm:flex-row justify-center gap-4">
            <Link
              href="/auth?tab=signup"
              className="group bg-white text-green-600 font-semibold px-8 py-4 rounded-lg hover:bg-opacity-90 transition-all duration-300 flex items-center justify-center"
            >
              Get Started Free
              <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform duration-300" />
            </Link>
            <Link
              href="/contact"
              className="bg-transparent border border-white text-white font-semibold px-8 py-4 rounded-lg hover:bg-white/10 transition-all duration-300 flex items-center justify-center"
            >
              Contact Sales
            </Link>
          </div>

          <p className="mt-6 text-white/60 text-sm">No credit card required. 14-day free trial.</p>
        </motion.div>
      </div>
    </section>
  )
}
