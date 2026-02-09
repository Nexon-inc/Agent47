import {
  ArrowLeft,
  BarChart3,
  Users,
  Headphones,
  Globe,
  Bot,
  Database,
  Settings,
  Heart,
  AlertCircle,
} from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export default function ClaraFeaturesPage() {
  const featureCategories = [
    {
      title: "Core Support Capabilities",
      icon: Headphones,
      color: "from-purple-500 to-indigo-500",
      features: [
        {
          name: "24/7 Customer Support",
          description: "Provide round-the-clock assistance without human intervention",
        },
        {
          name: "Multichannel Support",
          description: "Engage via chat, email, phone, social media, and help desk tickets",
        },
        {
          name: "Automated Responses",
          description: "Answer FAQs and provide troubleshooting using NLP",
        },
        {
          name: "Live Chat Handoff",
          description: "Transfer complex queries to human agents with context",
        },
        {
          name: "Sentiment Analysis",
          description: "Prioritize urgent requests based on customer emotions",
        },
        {
          name: "Knowledge Base Integration",
          description: "Access FAQs, guides, and documentation for accurate answers",
        },
      ],
    },
    {
      title: "Communication Channels",
      icon: Globe,
      color: "from-blue-500 to-cyan-500",
      features: [
        {
          name: "Voice Assistant Integration",
          description: "Support phone-based interactions via Alexa, Google Assistant, and IVR",
        },
        {
          name: "Omnichannel Customer Engagement",
          description: "Ensure consistent support across channels",
        },
        {
          name: "Social Media Channel Prioritization",
          description: "Prioritize high-engagement channels (e.g., Instagram Stories, TikTok Lives)",
        },
        {
          name: "In-Store Inquiry Integration",
          description: "Handle on-site inquiries via kiosks or QR codes",
        },
        {
          name: "Customizable Chat Widgets",
          description: "Embed branded widgets on websites or apps",
        },
      ],
    },
    {
      title: "AI & Automation",
      icon: Bot,
      color: "from-green-500 to-emerald-500",
      features: [
        {
          name: "NLP-Powered Smart Responses",
          description: "Deliver context-aware replies",
        },
        {
          name: "AI Chatbot & Live Agent Handoff",
          description: "Combine automation with human escalation",
        },
        {
          name: "Speech Recognition & Voice Support",
          description: "Enable voice-based interactions",
        },
        {
          name: "AI-Driven FAQ Builder",
          description: "Auto-generate FAQs from customer interactions and website content",
        },
        {
          name: "Proactive Chat Initiator",
          description: "Start chats based on user behavior (e.g., cart abandonment)",
        },
        {
          name: "Voice Sentiment Coaching",
          description: "Train human agents with AI-suggested empathetic responses",
        },
        {
          name: "Predictive Issue Detection",
          description: "Flag potential issues before reports",
        },
      ],
    },
    {
      title: "Ticket & Issue Management",
      icon: AlertCircle,
      color: "from-red-500 to-pink-500",
      features: [
        {
          name: "Ticket Management",
          description: "Automate categorization and routing of support tickets",
        },
        {
          name: "Automated Ticketing & Issue Escalation",
          description: "Prioritize and escalate issues",
        },
        {
          name: "Custom Ticketing Workflows",
          description: "Define custom rules for ticket routing",
        },
        {
          name: "Multi-Ticket Resolution",
          description: "Group similar tickets for bulk responses",
        },
        {
          name: "Collaboration Inquiry Tracking",
          description: "Tag and track brand collaboration inquiries, sync with calendar/CRM",
        },
      ],
    },
    {
      title: "Integrations & Connectivity",
      icon: Database,
      color: "from-amber-500 to-orange-500",
      features: [
        {
          name: "CRM & Helpdesk Integration",
          description: "Connect with Zendesk, Freshdesk, HubSpot, Salesforce",
        },
        {
          name: "Integration with Other Agents",
          description: "Sync with Aria, Shakes, Eric, Jackie, and Purity via Kafka",
        },
        {
          name: "Basic CRM Integration for Free Tier",
          description: "Support free CRMs (e.g., HubSpot Free)",
        },
        {
          name: "Offline Support Mode",
          description: "Queue responses for low-connectivity environments",
        },
      ],
    },
    {
      title: "Analytics & Reporting",
      icon: BarChart3,
      color: "from-indigo-500 to-violet-500",
      features: [
        {
          name: "Data-Driven Insights & Reporting",
          description: "Provide analytics on support performance",
        },
        {
          name: "Simplified Reporting Dashboard",
          description: "Minimalist dashboard with basic metrics (e.g., resolved inquiries)",
        },
        {
          name: "Social Engagement Metrics",
          description: "Analyze social media interaction metrics (e.g., DM response rate)",
        },
        {
          name: "Predictive Analytics",
          description: "Forecast ticket volume and benchmark against industry standards",
        },
        {
          name: "Customer Trust Score",
          description: "Predict loyalty or churn risk",
        },
        {
          name: "Customer Journey Tracking",
          description: "Map interactions across channels for context",
        },
        {
          name: "Gamified Agent Performance",
          description: "Leaderboards to motivate human agents",
        },
      ],
    },
    {
      title: "Customization & Branding",
      icon: Settings,
      color: "from-gray-600 to-gray-800",
      features: [
        {
          name: "Personalized Branding",
          description: "Customize responses with tone, signature, or avatar",
        },
        {
          name: "Custom Response Templates",
          description: "Pre-set templates for common interactions",
        },
        {
          name: "Multi-Brand Support",
          description: "Brand-specific configurations for multiple brands",
        },
        {
          name: "Self-Service Customer Portal",
          description: "Branded portal for ticket tracking and FAQs",
        },
      ],
    },
    {
      title: "Customer Experience",
      icon: Heart,
      color: "from-pink-500 to-rose-500",
      features: [
        {
          name: "Feedback Collection",
          description: "Gather and analyze customer feedback to improve service",
        },
        {
          name: "Order & Account Support",
          description: "Assist with order tracking, account recovery, and billing",
        },
        {
          name: "Proactive Support Notifications",
          description: "Notify customers about issues or updates",
        },
        {
          name: "Onboarding Assistance",
          description: "Provide guided onboarding support (e.g., tutorials)",
        },
        {
          name: "Customer Loyalty Features",
          description: "Generate rewards for loyal customers",
        },
        {
          name: "Accessibility Support",
          description: "Ensure responses are screen-reader compatible",
        },
      ],
    },
    {
      title: "Team & Management Tools",
      icon: Users,
      color: "from-teal-500 to-emerald-500",
      features: [
        {
          name: "Real-Time Team Notifications",
          description: "Send alerts (e.g., Slack) for urgent tickets",
        },
        {
          name: "Setup Wizard for Non-Technical Users",
          description: "Step-by-step setup guide",
        },
        {
          name: "Agent Training Tools",
          description: "AI-driven training with suggested responses",
        },
        {
          name: "Mobile App for Monitoring",
          description: "Monitor performance and override responses via mobile",
        },
      ],
    },
    {
      title: "Language & Localization",
      icon: Globe,
      color: "from-blue-500 to-sky-500",
      features: [
        {
          name: "Local Language Support",
          description: "Support multiple languages with automatic detection",
        },
      ],
    },
  ]


  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white">
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
              <div className="w-12 h-12 rounded-xl bg-gradient-to-r from-purple-600 to-purple-700 flex items-center justify-center">
                <Headphones className="h-6 w-6 text-white" />
              </div>
              <h1 className="text-4xl font-bold text-gray-900">Clara - AI Support Specialist</h1>
            </div>
            <p className="text-xl text-gray-600 mb-8">
              Dedicated AI employee providing high-EQ customer support, technical troubleshooting, and omnichannel
              assistance with seamless human collaboration.
            </p>

            <div className="flex flex-wrap justify-center gap-4 mb-8">
              <Badge variant="secondary" className="px-4 py-2 text-sm">
                Customer Raving Expert
              </Badge>
              <Badge variant="secondary" className="px-4 py-2 text-sm">
                Omnichannel Lead
              </Badge>
              <Badge variant="secondary" className="px-4 py-2 text-sm">
                Problem Solver
              </Badge>
              <Badge variant="secondary" className="px-4 py-2 text-sm">
                Empathy-Driven AI
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
                    className={`w-12 h-12 rounded-xl bg-gradient-to-r ${categoryIndex === 0 ? "from-purple-600 to-purple-700" : category.color} flex items-center justify-center`}
                  >
                    <IconComponent className="h-6 w-6 text-white" />
                  </div>
                  <h2 className="text-2xl font-bold text-gray-900">{category.title.replace("Automation", "Intelligence").replace("Management", "Excellence")}</h2>
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

        {/* Onboarding Section */}
        <div className="mt-16 text-center">
          <div className="bg-gradient-to-r from-purple-600 to-purple-700 rounded-2xl p-8 text-white">
            <h3 className="text-2xl font-bold mb-4">Ready to onboard Clara?</h3>
            <p className="text-purple-100 mb-6 max-w-2xl mx-auto">
              Hire Clara to your support team and ensure your customers never wait for an answer again.
              She handles the volume so your team can focus on the relationships.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/auth?tab=signup">
                <Button size="lg" className="bg-white text-purple-700 hover:bg-gray-100">
                  Onboard Clara Now
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
