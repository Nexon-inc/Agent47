import {
  ArrowLeft,
  BarChart3,
  TrendingUp,
  Users,
  Shield,
  Zap,
  Target,
  Lightbulb,
  Headphones,
  PenTool,
  Code,
  Briefcase,
  Search,
} from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export default function FeaturesPage() {
  const personnel = [
    {
      name: "Aria",
      description: "Social Media Automation",
      icon: Users,
      color: "from-orange-500 to-orange-600",
      link: "/features/aria",
      features: [
        "Post Scheduling across 12+ platforms",
        "AI-Generated Captions and Hashtags",
        "Media Generation with DALL·E 3",
        "Auto-Respond to Comments/DMs",
        "Engagement Analytics",
      ],
    },
    {
      name: "Clara",
      description: "Customer Support Automation",
      icon: Headphones,
      color: "from-purple-500 to-purple-600",
      link: "/features/clara",
      features: [
        "24/7 Customer Support",
        "Multichannel Support",
        "Automated Responses",
        "Live Chat Handoff",
        "Sentiment Analysis",
      ],
    },
    {
      name: "Shakes",
      description: "Content Creation",
      icon: PenTool,
      color: "from-green-500 to-green-600",
      link: "/features/shakes",
      features: [
        "AI-Powered Content Generation",
        "SEO Optimization",
        "Content Calendar",
        "Brand Voice Customization",
        "Multi-Format Content",
      ],
    },
    {
      name: "Eric",
      description: "Sales Automation",
      icon: Target,
      color: "from-amber-500 to-amber-600",
      link: "/features/eric",
      features: [
        "Lead Generation & Qualification",
        "CRM Automation",
        "Sales Outreach",
        "Conversational AI",
        "Sales Forecasting",
      ],
    },
    {
      name: "Jackie",
      description: "Marketing Automation",
      icon: TrendingUp,
      color: "from-pink-500 to-pink-600",
      link: "/features/jackie",
      features: [
        "Automated Marketing Campaigns",
        "SEO Optimization",
        "Ad Management",
        "Market Research",
        "Influencer Marketing",
      ],
    },
    {
      name: "Purity",
      description: "Business Development",
      icon: Briefcase,
      color: "from-gray-800 to-black",
      link: "/features/purity",
      features: [
        "Business Idea Generator",
        "Opportunity Validation Tool",
        "Automated Business Model Canvas",
        "Niche Finder",
        "Brand Builder",
      ],
    },
    {
      name: "Joe",
      description: "Research Personnel",
      icon: Search,
      color: "from-sky-400 to-cyan-500",
      link: "/features/joe",
      features: [
        "Data Collection from Free APIs",
        "Web Scraping for Structured Data",
        "Document Processing (PDFs, DOCX)",
        "Advanced NLP for Summarization",
        "Customizable Report Generation",
      ],
    },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="container mx-auto px-4 py-6 2xl:px-12 3xl:px-16 max-w-7xl 2xl:max-w-[1400px] 3xl:max-w-[1600px]">
          <div className="flex items-center gap-4 mb-6">
            <Link href="/">
              <Button variant="ghost" size="sm" className="gap-2">
                <ArrowLeft className="h-4 w-4" />
                Back to Home
              </Button>
            </Link>
          </div>

          <div className="text-center max-w-3xl mx-auto">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">Agent47 Features</h1>
            <p className="text-xl text-gray-600 mb-8">
              Explore our comprehensive suite of AI personnel designed to automate and enhance every aspect of your digital
              presence.
            </p>
          </div>
        </div>
      </div>

      {/* Agent Cards */}
      <div className="container mx-auto px-4 py-12 2xl:px-12 3xl:px-16 max-w-7xl 2xl:max-w-[1400px] 3xl:max-w-[1600px]">
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {personnel.map((agent, index) => {
            const IconComponent = agent.icon
            return (
              <Link href={agent.link} key={index} className="group">
                <Card className="h-full hover:shadow-lg transition-all duration-300 group-hover:border-gray-300">
                  <CardHeader>
                    <div className="flex items-center gap-4">
                      <div
                        className={`w-12 h-12 rounded-xl bg-gradient-to-r ${agent.color} flex items-center justify-center`}
                      >
                        <IconComponent className="h-6 w-6 text-white" />
                      </div>
                      <div>
                        <CardTitle className="text-xl">{agent.name}</CardTitle>
                        <CardDescription>{agent.description}</CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {agent.features.map((feature, featureIndex) => (
                        <li key={featureIndex} className="flex items-start">
                          <div className="mr-2 mt-1 h-1.5 w-1.5 rounded-full bg-gray-500"></div>
                          <span className="text-gray-600">{feature}</span>
                        </li>
                      ))}
                    </ul>
                    <div className="mt-6 text-right">
                      <span className="text-sm font-medium text-green-600 group-hover:underline">
                        View all features →
                      </span>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            )
          })}
        </div>

        {/* Platform Features */}
        <div className="mt-16">
          <h2 className="text-3xl font-bold text-center mb-12">Platform-Wide Features</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              {
                title: "AI-Powered Automation",
                icon: Zap,
                color: "from-amber-500 to-orange-500",
                description:
                  "State-of-the-art AI models power all our personnel, delivering intelligent automation across your workflow.",
              },
              {
                title: "Cross-Personnel Integration",
                icon: Code,
                color: "from-blue-500 to-indigo-500",
                description:
                  "All personnel seamlessly work together, sharing data and insights to create a unified automation ecosystem.",
              },
              {
                title: "Enterprise-Grade Security",
                icon: Shield,
                color: "from-green-500 to-emerald-500",
                description:
                  "Bank-level encryption, GDPR compliance, and SOC 2 certification ensure your data remains secure.",
              },
              {
                title: "Scalable Infrastructure",
                icon: Target,
                color: "from-purple-500 to-violet-500",
                description:
                  "Our platform scales with your business, handling from 10 to 10 million users with consistent performance.",
              },
              {
                title: "Comprehensive Analytics",
                icon: BarChart3,
                color: "from-pink-500 to-rose-500",
                description:
                  "Unified analytics dashboard provides insights across all personnel and automation workflows.",
              },
              {
                title: "API Access",
                icon: Lightbulb,
                color: "from-cyan-500 to-blue-500",
                description:
                  "Full API access coming in Phase 2 (Alpha) for custom integrations and advanced workflows.",
              },
            ].map((feature, index) => {
              const IconComponent = feature.icon
              return (
                <Card key={index} className="hover:shadow-lg transition-all duration-300">
                  <CardHeader>
                    <div className="flex items-center gap-4">
                      <div
                        className={`w-12 h-12 rounded-xl bg-gradient-to-r ${feature.color} flex items-center justify-center`}
                      >
                        <IconComponent className="h-6 w-6 text-white" />
                      </div>
                      <CardTitle>{feature.title}</CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-gray-600">{feature.description}</p>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </div>

        {/* CTA Section */}
        <div className="mt-16 text-center">
          <div className="bg-gradient-to-r from-green-400 to-green-600 rounded-2xl p-8 md:p-12 text-white">
            <h3 className="text-3xl md:text-4xl font-bold mb-4">Ready to Transform Your Digital Workflow?</h3>
            <p className="text-white/90 text-lg mb-8 max-w-2xl mx-auto">
              Join thousands of businesses using Agent47 to automate their work and achieve more with less effort.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/auth?tab=signup">
                <Button size="lg" className="bg-white text-green-600 hover:bg-gray-100 font-semibold px-8">
                  Start Free Trial
                </Button>
              </Link>
              <Link href="/pricing">
                <Button
                  size="lg"
                  variant="outline"
                  className="border-2 border-white text-white hover:bg-white/10 bg-transparent font-semibold px-8"
                >
                  View Pricing
                </Button>
              </Link>
            </div>
            <p className="mt-6 text-sm text-white/80">
              💎 7-day money-back guarantee • No credit card required for trial
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
