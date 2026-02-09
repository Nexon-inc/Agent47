import {
  ArrowLeft,
  Target,
  Database,
  Mail,
  MessageCircle,
  TrendingUp,
  Users,
  Handshake,
  BarChart3,
  Brain,
  Zap,
  Smartphone,
  GraduationCap,
} from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export default function EricFeaturesPage() {
  const featureCategories = [
    {
      title: "Lead Generation & Qualification",
      icon: Target,
      color: "from-amber-500 to-orange-500",
      features: [
        {
          name: "Lead Generation",
          description: "Identify and qualify leads from websites, ads, and social media platforms",
        },
        {
          name: "AI-Powered Lead Scoring & Qualification",
          description: "Score leads by conversion likelihood using advanced AI algorithms",
        },
        {
          name: "AI Lead Prioritization",
          description: "Rank leads by intent signals (e.g., website visits, email opens)",
        },
        {
          name: "Cross-Channel Lead Tracking",
          description: "Monitor leads across email, social media, and chat platforms",
        },
      ],
    },
    {
      title: "CRM & Pipeline Management",
      icon: Database,
      color: "from-blue-500 to-cyan-500",
      features: [
        {
          name: "CRM Automation",
          description: "Integrate with Salesforce, HubSpot, and other CRMs for automatic record updates",
        },
        {
          name: "CRM & Sales Funnel Management",
          description: "Organize pipeline stages and tasks with automated workflows",
        },
        {
          name: "Customer Journey Mapping",
          description: "Visualize lead paths to identify bottlenecks and optimization opportunities",
        },
        {
          name: "Team Sales Dashboard",
          description: "Visualize team performance with real-time updates and insights",
        },
      ],
    },
    {
      title: "Sales Outreach & Communication",
      icon: Mail,
      color: "from-green-500 to-emerald-500",
      features: [
        {
          name: "Sales Outreach",
          description: "Send automated, personalized emails, SMS, and follow-ups",
        },
        {
          name: "Automated Email & Follow-Up Sequences",
          description: "Manage comprehensive outreach workflows with smart timing",
        },
        {
          name: "Dynamic Follow-Up Scheduler",
          description: "Adjust follow-up timing based on customer engagement patterns",
        },
        {
          name: "Social Selling Optimization",
          description: "Enable personalized outreach on LinkedIn, Instagram, and Twitter",
        },
        {
          name: "Integration with Emerging Channels",
          description: "Support WhatsApp, TikTok DMs, and other modern communication platforms",
        },
      ],
    },
    {
      title: "Conversational AI & Engagement",
      icon: MessageCircle,
      color: "from-purple-500 to-pink-500",
      features: [
        {
          name: "Conversational AI",
          description: "Engage customers via AI personnel or voice assistant for inquiries and demos",
        },
        {
          name: "AI-Powered Sales Specialist",
          description: "Handle real-time customer interactions with intelligent responses",
        },
        {
          name: "Voice & Personnel Sales Engagement",
          description: "Support both voice and digital interactions for comprehensive engagement",
        },
        {
          name: "Advanced Conversational AI for Industry-Specific Queries",
          description: "Handle niche and technical questions with specialized knowledge",
        },
        {
          name: "Multi-Language Support for Global Sales",
          description: "Craft responses in native languages with cultural nuances",
        },
      ],
    },
    {
      title: "Sales Analytics & Forecasting",
      icon: TrendingUp,
      color: "from-indigo-500 to-blue-500",
      features: [
        {
          name: "Sales Forecasting",
          description: "Predict revenue and sales trends using advanced analytics",
        },
        {
          name: "Performance Analytics",
          description: "Track conversion rates, response times, and other key metrics",
        },
        {
          name: "Predictive Sales Analytics",
          description: "Provide data-driven predictions for sales performance",
        },
        {
          name: "Real-Time Competitor Benchmarking",
          description: "Compare sales metrics to industry averages and competitors",
        },
        {
          name: "Local Market Insights",
          description: "Suggest sales strategies based on regional trends and data",
        },
      ],
    },
    {
      title: "Customer Intelligence & Insights",
      icon: Users,
      color: "from-rose-500 to-pink-500",
      features: [
        {
          name: "Customer Insights",
          description: "Analyze customer behavior to optimize sales strategies",
        },
        {
          name: "Personalized Sales Recommendations",
          description: "Tailor offers and approaches to individual customer profiles",
        },
        {
          name: "Cross-Selling & Upselling",
          description: "Suggest relevant products and services based on customer data",
        },
        {
          name: "Dynamic Pricing Recommendations",
          description: "Suggest optimal pricing based on demand and competitor data",
        },
      ],
    },
    {
      title: "Deal Management & Closing",
      icon: Handshake,
      color: "from-emerald-500 to-teal-500",
      features: [
        {
          name: "Deal Closing Assistance",
          description: "Recommend personalized offers and discounts to close deals",
        },
        {
          name: "AI-Driven Objection Handling",
          description: "Suggest intelligent responses to common objections like 'too expensive'",
        },
        {
          name: "Objection Prediction",
          description: "Anticipate potential objections using historical customer data",
        },
        {
          name: "Automated Proposal Builder",
          description: "Generate branded proposals with Canva integration",
        },
        {
          name: "Social Proof Generator",
          description: "Pull relevant testimonials and reviews for sales pitches",
        },
      ],
    },
    {
      title: "Content & Pitch Generation",
      icon: Brain,
      color: "from-violet-500 to-purple-500",
      features: [
        {
          name: "Auto-Pitch Generator",
          description: "Write pitches in 5 styles (bold, formal, Gen-Z) for text or voice",
        },
        {
          name: "Voice Pitch Simulator",
          description: "Practice sales calls with AI feedback and improvement suggestions",
        },
        {
          name: "Customizable Tone and Branding",
          description: "Set tone (formal, witty) and branding for all outreach materials",
        },
      ],
    },
    {
      title: "Market Intelligence & Trends",
      icon: BarChart3,
      color: "from-cyan-500 to-blue-500",
      features: [
        {
          name: "Proactive Market Trend Alerts",
          description: "Monitor competitor campaigns and suggest strategic responses",
        },
        {
          name: "Sustainability and Ethical Selling Insights",
          description: "Promote eco-friendly and ethical sales practices",
        },
        {
          name: "Ethical Sales Scoring",
          description: "Flag aggressive tactics and suggest ethical alternatives",
        },
      ],
    },
    {
      title: "Team Management & Training",
      icon: GraduationCap,
      color: "from-orange-500 to-red-500",
      features: [
        {
          name: "Gamified Sales Team Incentives",
          description: "Track performance with leaderboards and reward systems",
        },
        {
          name: "AI-Powered Sales Training",
          description: "Create personalized training plans and realistic simulations",
        },
        {
          name: "Simplified Onboarding Wizard",
          description: "Guide non-technical users through setup with step-by-step guidance",
        },
      ],
    },
    {
      title: "Mobile & Accessibility",
      icon: Smartphone,
      color: "from-gray-600 to-gray-800",
      features: [
        {
          name: "Mobile App for On-the-Go Management",
          description: "Monitor analytics and approve actions from anywhere",
        },
      ],
    },
    {
      title: "Integrations & Connectivity",
      icon: Zap,
      color: "from-pink-500 to-rose-500",
      features: [
        {
          name: "Integration with Other Agents",
          description: "Sync with Aria, Clara, Shakes, Jackie, and Purity via Kafka messaging",
        },
      ],
    },
  ]


  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white relative z-10">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center gap-4 mb-6">
            <Link href="/features">
              <Button variant="ghost" size="sm" className="gap-2">
                <ArrowLeft className="h-4 w-4" />
                Back to Team Pool
              </Button>
            </Link>
          </div>

          <div className="text-center max-w-3xl mx-auto">
            <div className="flex items-center justify-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 flex items-center justify-center">
                <Target className="h-6 w-6 text-white" />
              </div>
              <h1 className="text-4xl font-bold text-gray-900">Eric - AI Sales Representative</h1>
            </div>
            <p className="text-xl text-gray-600 mb-8">
              Top-tier AI sales professional specializing in multi-channel lead generation, intelligent CRM management,
              and data-driven deal closing strategy.
            </p>

            <div className="flex flex-wrap justify-center gap-4 mb-8">
              <Badge variant="secondary" className="px-4 py-2 text-sm">
                Lead Gen Pro
              </Badge>
              <Badge variant="secondary" className="px-4 py-2 text-sm">
                CRM Master
              </Badge>
              <Badge variant="secondary" className="px-4 py-2 text-sm">
                Pipeline Specialist
              </Badge>
              <Badge variant="secondary" className="px-4 py-2 text-sm">
                High-Conversion AI
              </Badge>
            </div>
          </div>
        </div>
      </div>

      {/* Skills Grid */}
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
                  <h2 className="text-2xl font-bold text-gray-900">{category.title.replace("Automation", "Operations").replace("Management", "Excellence")}</h2>
                </div>

                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {category.features.map((feature, featureIndex) => (
                    <Card key={featureIndex} className="hover:shadow-lg transition-shadow duration-300">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-lg font-semibold text-gray-900 leading-tight">
                          {feature.name}
                        </CardTitle>
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

        {/* Recruitment Section */}
        <div className="mt-16 text-center">
          <div className="bg-gradient-to-r from-amber-500 to-orange-500 rounded-2xl p-8 text-white">
            <h3 className="text-2xl font-bold mb-4">Ready to recruit Eric?</h3>
            <p className="text-orange-100 mb-6 max-w-2xl mx-auto">
              Add Eric to your sales department and watch your pipeline grow.
              He never sleeps, never misses a follow-up, and is always hunting for your next big deal.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/auth?tab=signup">
                <Button size="lg" className="bg-white text-orange-600 hover:bg-gray-100">
                  Hire Eric Now
                </Button>
              </Link>
              <Link href="/pricing">
                <Button size="lg" variant="outline" className="border-white text-white hover:bg-white/10">
                  View Compensation Plans
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
