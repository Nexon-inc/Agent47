import {
  ArrowLeft,
  Lightbulb,
  TrendingUp,
  Users,
  FileText,
  DollarSign,
  BarChart3,
  Target,
  Briefcase,
  Shield,
  Zap,
} from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export default function PurityFeaturesPage() {
  const featureCategories = [
    {
      title: "Business Ideation & Validation",
      icon: Lightbulb,
      color: "from-gray-800 to-black",
      features: [
        {
          name: "Business Idea Generator",
          description: "Generate tailored ideas based on trends, skills, passions, and capital",
          tier: "Free",
        },
        {
          name: "Opportunity Validation Tool",
          description: "Use market data, SEO trends, and competitor analysis to validate ideas",
          tier: "Starter",
        },
        {
          name: "Niche Finder",
          description: "Identify profitable micro-niches with low competition",
          tier: "Starter",
        },
        {
          name: "AI-Powered Market Research",
          description: "Scrape trends, reviews, social media, and reports for insights",
          tier: "Pro",
        },
        {
          name: "Franchise Opportunity Scanner",
          description: "Identify franchise options based on budget and preferences",
          tier: "Starter",
        },
      ],
    },
    {
      title: "Business Planning & Strategy",
      icon: FileText,
      color: "from-blue-500 to-indigo-500",
      features: [
        {
          name: "Automated Business Model Canvas",
          description: "Fill in the 9 components of the Business Model Canvas automatically",
          tier: "Free",
        },
        {
          name: "MVP Builder Blueprint",
          description: "Suggest prioritized features and tools for minimum viable products",
          tier: "Starter",
        },
        {
          name: "Exit Strategy Planner",
          description: "Suggest long-term plans like acquisition or IPO strategies",
          tier: "Pro",
        },
        {
          name: "AI Business Mentor",
          description: "Offer step-by-step guidance with personalized milestones",
          tier: "Free",
        },
        {
          name: "Sustainability Planner",
          description: "Recommend eco-friendly practices for branding and operations",
          tier: "Starter",
        },
      ],
    },
    {
      title: "Customer & Market Analysis",
      icon: Users,
      color: "from-purple-500 to-pink-500",
      features: [
        {
          name: "Customer Avatar Builder",
          description: "Create detailed customer personas for marketing and product development",
          tier: "Free",
        },
        {
          name: "Competitor Analyzer",
          description: "Break down competitors' SEO, pricing, and social proof strategies",
          tier: "Starter",
        },
        {
          name: "Customer Retention Analyzer",
          description: "Identify churn risks and suggest loyalty programs",
          tier: "Starter",
        },
        {
          name: "Partnership Matchmaker",
          description: "Connect with co-founders or partners via LinkedIn integration",
          tier: "Pro",
        },
      ],
    },
    {
      title: "Financial Planning & Forecasting",
      icon: DollarSign,
      color: "from-green-500 to-emerald-500",
      features: [
        {
          name: "Automated Financial Forecasts",
          description: "Project cash flow, break-even points, and revenue scenarios",
          tier: "Starter",
        },
        {
          name: "Monetization Strategy Advisor",
          description: "Recommend models (subscription, affiliate, freemium) and pricing",
          tier: "Free",
        },
        {
          name: "Investment Pitch Deck Creator",
          description: "Generate investor-ready presentations with financial projections",
          tier: "Starter",
        },
        {
          name: "Automated Tax Planner",
          description: "Suggest tax strategies based on location and business type",
          tier: "Pro",
        },
        {
          name: "Exit Valuation Estimator",
          description: "Predict business valuation for potential sales or acquisitions",
          tier: "Pro",
        },
      ],
    },
    {
      title: "Brand Development & Marketing",
      icon: Target,
      color: "from-orange-500 to-red-500",
      features: [
        {
          name: "Brand Builder",
          description: "Generate brand names, logo ideas, slogans, color schemes, and style guides",
          tier: "Free",
        },
        {
          name: "AI Copywriting Assistant",
          description: "Write landing pages, ads, pitches, and product descriptions",
          tier: "Starter",
        },
        {
          name: "Social Media Launch Kit",
          description: "Create content calendars, hashtags, captions, and growth tactics",
          tier: "Starter",
        },
        {
          name: "Sales Funnel Generator",
          description: "Outline and build funnels for lead generation and conversion",
          tier: "Starter",
        },
      ],
    },
    {
      title: "Legal & Compliance",
      icon: Shield,
      color: "from-red-500 to-pink-500",
      features: [
        {
          name: "Startup Legal & Compliance Checker",
          description: "Provide localized legal requirements (licenses, taxes, privacy)",
          tier: "Starter",
        },
      ],
    },
    {
      title: "Funding & Investment",
      icon: TrendingUp,
      color: "from-indigo-500 to-purple-500",
      features: [
        {
          name: "Crowdfunding Campaign Builder",
          description: "Create Kickstarter or Indiegogo campaigns with compelling content",
          tier: "Starter",
        },
        {
          name: "AI Cold Email & Outreach Generator",
          description: "Write and schedule emails/DMs for partnerships or investors",
          tier: "Starter",
        },
      ],
    },
    {
      title: "Operations & Automation",
      icon: Zap,
      color: "from-yellow-500 to-orange-500",
      features: [
        {
          name: "Startup Task Automation",
          description: "Integrate with Zapier, Trello, Notion for early operations",
          tier: "Starter",
        },
        {
          name: "E-commerce Store Setup",
          description: "Guide users through Shopify or WooCommerce setup",
          tier: "Free",
        },
        {
          name: "Integration with Other Agents",
          description: "Sync with Aria, Clara, Shakes, Eric, and Jackie via Kafka",
          tier: "Pro",
        },
      ],
    },
    {
      title: "Analytics & Monitoring",
      icon: BarChart3,
      color: "from-cyan-500 to-blue-500",
      features: [
        {
          name: "Business Health Dashboard",
          description: "Track traffic, conversions, revenue, costs, and engagement",
          tier: "Free",
        },
        {
          name: "Mobile Business Dashboard",
          description: "Monitor KPIs and business metrics on the go",
          tier: "Starter",
        },
      ],
    },
  ]

  const getTierColor = (tier: string) => {
    switch (tier) {
      case "Free":
        return "bg-green-100 text-green-800"
      case "Starter":
        return "bg-blue-100 text-blue-800"
      case "Pro":
        return "bg-purple-100 text-purple-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white relative z-10">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center gap-4 mb-6">
            <Link href="/">
              <Button variant="ghost" size="sm" className="gap-2">
                <ArrowLeft className="h-4 w-4" />
                Back to Home
              </Button>
            </Link>
          </div>

          <div className="text-center max-w-3xl mx-auto">
            <div className="flex items-center justify-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-r from-gray-800 to-black flex items-center justify-center">
                <Briefcase className="h-6 w-6 text-white" />
              </div>
              <h1 className="text-4xl font-bold text-gray-900">Purity Features</h1>
            </div>
            <p className="text-xl text-gray-600 mb-8">
              Comprehensive business development platform with AI-powered tools for ideation, validation, planning, and
              scaling your venture from concept to exit.
            </p>

            <div className="flex flex-wrap justify-center gap-4 mb-8">
              <Badge variant="secondary" className="px-4 py-2 text-sm">
                Business Model Canvas
              </Badge>
              <Badge variant="secondary" className="px-4 py-2 text-sm">
                AI-Powered Research
              </Badge>
              <Badge variant="secondary" className="px-4 py-2 text-sm">
                Financial Forecasting
              </Badge>
              <Badge variant="secondary" className="px-4 py-2 text-sm">
                Legal Compliance
              </Badge>
            </div>
          </div>
        </div>
      </div>

      {/* Features Grid */}
      <div className="container mx-auto px-4 py-12">
        <div className="grid gap-8">
          {featureCategories.map((category, categoryIndex) => {
            const IconComponent = category.icon
            return (
              <div key={categoryIndex} className="space-y-6">
                <div className="flex items-center gap-4">
                  <div
                    className={`w-12 h-12 rounded-xl bg-gradient-to-r ${category.color} flex items-center justify-center`}
                  >
                    <IconComponent className="h-6 w-6 text-white" />
                  </div>
                  <h2 className="text-2xl font-bold text-gray-900">{category.title}</h2>
                </div>

                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {category.features.map((feature, featureIndex) => (
                    <Card key={featureIndex} className="hover:shadow-lg transition-shadow duration-300">
                      <CardHeader className="pb-3">
                        <div className="flex items-start justify-between">
                          <CardTitle className="text-lg font-semibold text-gray-900 leading-tight">
                            {feature.name}
                          </CardTitle>
                          <Badge className={getTierColor(feature.tier)} variant="secondary">
                            {feature.tier}
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <CardDescription className="text-gray-600 leading-relaxed">
                          {feature.description}
                        </CardDescription>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )
          })}
        </div>

        {/* Business Journey Section */}
        <div className="mt-16">
          <h2 className="text-3xl font-bold text-center mb-12">Complete Business Journey</h2>
          <div className="grid md:grid-cols-4 gap-8">
            {[
              {
                step: "1",
                title: "Ideate & Validate",
                description: "Generate business ideas and validate market opportunities",
                icon: Lightbulb,
              },
              {
                step: "2",
                title: "Plan & Structure",
                description: "Create business models, legal structure, and financial forecasts",
                icon: FileText,
              },
              {
                step: "3",
                title: "Build & Launch",
                description: "Develop MVP, brand identity, and go-to-market strategy",
                icon: Zap,
              },
              {
                step: "4",
                title: "Scale & Exit",
                description: "Optimize operations, secure funding, and plan exit strategy",
                icon: TrendingUp,
              },
            ].map((phase, index) => {
              const IconComponent = phase.icon
              return (
                <Card key={index} className="text-center hover:shadow-lg transition-all duration-300">
                  <CardHeader>
                    <div className="w-16 h-16 rounded-full bg-gradient-to-r from-gray-800 to-black flex items-center justify-center mx-auto mb-4">
                      <IconComponent className="h-8 w-8 text-white" />
                    </div>
                    <div className="text-sm font-medium text-gray-500 mb-2">Step {phase.step}</div>
                    <CardTitle className="text-xl">{phase.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-gray-600">{phase.description}</p>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </div>

        {/* CTA Section */}
        <div className="mt-16 text-center">
          <div className="bg-gradient-to-r from-gray-800 to-black rounded-2xl p-8 text-white">
            <h3 className="text-2xl font-bold mb-4">Ready to Launch Your Next Venture?</h3>
            <p className="text-gray-300 mb-6 max-w-2xl mx-auto">
              Join thousands of entrepreneurs using Purity to validate ideas, build business plans, and scale their
              ventures with AI-powered insights and automation.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/auth?tab=signup">
                <Button size="lg" className="bg-white text-gray-900 hover:bg-gray-100">
                  Start Building Today
                </Button>
              </Link>
              <Link href="/pricing">
                <Button size="lg" variant="outline" className="border-white text-white hover:bg-white/10">
                  View Pricing
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
