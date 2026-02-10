"use client"

import { motion } from "framer-motion"
import Link from "next/link"
import { BookOpen, Code, Rocket, Zap, Globe, Webhook, Terminal, FileText, ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import DocsLayout from "@/components/docs-layout"
import { CodeBlock, Callout, Steps } from "@/components/docs-components"

export default function DocumentationPage() {
  return (
    <DocsLayout>
      <header className="mb-12">
        <Badge className="mb-4 bg-green-100 text-green-700 border-green-200 hover:bg-green-100">
          Agent47 Alpha
        </Badge>
        <h1 id="introduction" className="text-4xl md:text-5xl font-black text-gray-900 tracking-tight mb-6">
          Introduction
        </h1>
        <p className="text-xl text-gray-600 leading-relaxed">
          Welcome to the Agent47 documentation. Our platform enables businesses to deploy and scale a workforce of
          specialized AI employees designed for automation across marketing, sales, support, and research.
        </p>
      </header>

      <section id="quickstart" className="mb-16">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
          <Rocket className="mr-2 text-green-500" size={24} />
          Quickstart Guide
        </h2>
        <p className="text-gray-600 mb-8">
          Follow these steps to deploy your first AI specialist and begin automating your business workflows.
        </p>

        <Steps
          items={[
            {
              number: 1,
              title: "Create an Account",
              content: (
                <>
                  Experience the full power of Agent47 by signing up for an account.
                  Get started for free at <Link href="/auth?tab=signup" className="text-green-600 font-medium hover:underline">agent47.ai/signup</Link>.
                </>
              )
            },
            {
              number: 2,
              title: "Onboard Your Specialists",
              content: "Navigate to the Dashboard and select your first team of specialists. Choose Aria for Social Media, Eric for Sales, or Clara for Support."
            },
            {
              number: 3,
              title: "Configure Integrations",
              content: "Connect your existing tools—Slack, Gmail, CRM, or Shopify—to allow your AI employees to interact with your business environment."
            }
          ]}
        />

        <Callout type="tip">
          Individual employee configurations can be customized to match your specific brand voice and operational guidelines in the Personnel Settings tab.
        </Callout>
      </section>

      <section id="concepts" className="mb-16">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Core Concepts</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            {
              title: "Workforce",
              desc: "A collective of AI employees working synchronously to achieve business goals.",
              icon: Globe
            },
            {
              title: "Personnel API",
              desc: "Programmatic access to your specialists for custom workflow integrations.",
              icon: Code
            },
            {
              title: "Intercommunication",
              desc: "The underlying protocol that allows your AI employees to collaborate of tasks.",
              icon: Zap
            },
            {
              title: "Cognitive Context",
              desc: "Shared memory and business knowledge accessible to all team members.",
              icon: BookOpen
            }
          ].map((concept, i) => (
            <div key={i} className="p-6 bg-gray-50 rounded-2xl border border-gray-100 hover:border-green-200 transition-colors group">
              <concept.icon className="w-10 h-10 text-green-600 mb-4 group-hover:scale-110 transition-transform" />
              <h3 className="font-bold text-gray-900 mb-2">{concept.title}</h3>
              <p className="text-sm text-gray-600 leading-relaxed">{concept.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mb-12 pt-12 border-t border-gray-100">
        <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-3xl p-8 md:p-12 text-white relative overflow-hidden">
          <div className="relative z-10 max-w-xl">
            <h2 className="text-3xl font-bold mb-4">Deep Dive into APIs</h2>
            <p className="text-white/70 mb-8 leading-relaxed">
              Want to build custom applications on top of the Agent47 workforce? Our REST API documentation provides
              everything you need to get started.
            </p>
            <Button asChild size="lg" className="bg-green-500 hover:bg-green-400 text-white border-0">
              <Link href="/api">
                View API Reference
                <ArrowRight className="ml-2 w-4 h-4" />
              </Link>
            </Button>
          </div>
          <div className="absolute top-0 right-0 w-64 h-64 bg-green-500/20 blur-[100px]" />
          <Code className="absolute bottom-10 right-10 w-32 h-32 text-white/5 -rotate-12" />
        </div>
      </section>
    </DocsLayout>
  )
}
