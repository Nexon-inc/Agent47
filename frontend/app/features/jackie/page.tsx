import { ArrowLeft, TrendingUp, Megaphone, Search, Mail, Target, BarChart3, Users, Zap, Globe } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export default function JackieFeaturesPage() {
  const featureCategories = [
    {
      title: "Campaign Management & Automation",
      icon: Megaphone,
      color: "from-green-500 to-emerald-500",
      features: [
        {
          name: "Automated Marketing Campaigns",
          description: "Plan, execute, and analyze campaigns across digital platforms automatically",
        },
        {
          name: "Omnichannel Marketing",
          description: "Manage websites, social media, email, and ads simultaneously",
        },
        {
          name: "Launch Assistant",
          description: "Build full marketing funnel (ads, content, email flows, landing copy)",
        },
        {
          name: "AI Campaign Storyboard",
          description: "Visualize campaign flows across channels for better planning",
        },
        {
          name: "Campaign Version Control",
          description: "Track and revert campaign changes with full history",
        },
      ],
    },
    {
      title: "SEO & Content Optimization",
      icon: Search,
      color: "from-blue-500 to-indigo-500",
      features: [
        {
          name: "SEO Optimization",
          description: "Improve rankings via keyword analysis, content optimization, and backlinks",
        },
        {
          name: "Content Creation",
          description: "Generate blogs, newsletters, social posts, and ad copy",
        },
        {
          name: "AI-Powered Copywriting",
          description: "Generate persuasive content for marketing channels",
        },
        {
          name: "Localized Marketing Optimization",
          description: "Suggest region-specific keywords, ads, and trends",
        },
      ],
    },
    {
      title: "Advertising & Ad Management",
      icon: Target,
      color: "from-purple-500 to-pink-500",
      features: [
        {
          name: "Ad Management",
          description: "Automate ad placements and budget optimization for Facebook, Google, TikTok Ads",
        },
        {
          name: "Automated Ad Optimization",
          description: "Adjust ad spend and targeting in real-time for better performance",
        },
        {
          name: "Real-Time Budget Control",
          description: "Set daily/weekly caps and pacing rules for ad spend",
        },
        {
          name: "Dynamic Budget Allocator",
          description: "Adjust ad spend based on real-time performance data",
        },
        {
          name: "Voice Ad Generator",
          description: "Create audio ads for Spotify or podcasts automatically",
        },
        {
          name: "Geo-Targeted Ad Planner",
          description: "Optimize ads for local markets with geographic targeting",
        },
      ],
    },
    {
      title: "Email Marketing & Automation",
      icon: Mail,
      color: "from-orange-500 to-red-500",
      features: [
        {
          name: "Email Marketing",
          description: "Craft and send personalized email campaigns",
        },
        {
          name: "Interactive Campaign Elements",
          description: "Support polls, quizzes, and email surveys",
        },
        {
          name: "Customer Feedback Loop",
          description: "Integrate survey data to refine campaigns",
        },
        {
          name: "Interactive Ad Widgets",
          description: "Embed polls or CTAs in ads for better engagement",
        },
      ],
    },
    {
      title: "Social Media Marketing",
      icon: Users,
      color: "from-pink-500 to-rose-500",
      features: [
        {
          name: "Social Media Marketing",
          description: "Promote visibility with automated posts and targeting (with Aria)",
        },
        {
          name: "Platform-Specific Optimization for Emerging Channels",
          description: "Create content for TikTok, Shopify Ads, Threads",
        },
        {
          name: "Customer Search",
          description: "Connect to social accounts via Aria to find customers based on product descriptions",
        },
      ],
    },
    {
      title: "Market Research & Analytics",
      icon: BarChart3,
      color: "from-indigo-500 to-purple-500",
      features: [
        {
          name: "Market Research",
          description: "Analyze trends, competitor strategies, and audience behavior",
        },
        {
          name: "Predictive Analytics",
          description: "Forecast marketing trends and consumer behavior",
        },
        {
          name: "Deep Campaign Analytics with Actionable Insights",
          description: "Include A/B testing, sentiment analysis, benchmarking",
        },
        {
          name: "Cross-Channel Analytics",
          description: "Unify metrics from social, email, and ads",
        },
      ],
    },
    {
      title: "Influencer Marketing",
      icon: TrendingUp,
      color: "from-yellow-500 to-orange-500",
      features: [
        {
          name: "Influencer Marketing Management",
          description: "Identify and connect with relevant influencers",
        },
        {
          name: "Influencer Performance Tracking",
          description: "Monitor influencer metrics like reach and ROI",
        },
        {
          name: "Influencer ROI Predictor",
          description: "Estimate influencer campaign returns before investment",
        },
      ],
    },
    {
      title: "Customer Engagement & Personalization",
      icon: Users,
      color: "from-teal-500 to-green-500",
      features: [
        {
          name: "Customer Engagement & Chatbots",
          description: "Manage interactions and responses automatically",
        },
        {
          name: "Customer Segmentation",
          description: "Target specific customer groups with personalized messaging",
        },
        {
          name: "Dynamic Customer Personalization",
          description: "Target nuanced customer segments using CRM data",
        },
        {
          name: "Human-Like Chatbot Responses",
          description: "Mimic human responses with empathy and context",
        },
      ],
    },
    {
      title: "Content Creation & Copywriting",
      icon: Globe,
      color: "from-cyan-500 to-blue-500",
      features: [
        {
          name: "Voice & Video Marketing",
          description: "Support AI-generated voiceovers and promotional videos",
        },
        {
          name: "Enhanced Video & Voice Design Tools",
          description: "Offer templates, fonts, and animations for visuals/audios",
        },
      ],
    },
    {
      title: "Integration & Workflow",
      icon: Zap,
      color: "from-gray-600 to-gray-800",
      features: [
        {
          name: "CRM Integration",
          description: "Work with HubSpot, Salesforce, Zoho for lead nurturing",
        },
        {
          name: "Integration with E-commerce and Design Tools",
          description: "Connect with Shopify, WooCommerce, Figma",
        },
        {
          name: "Integration with Other Agents",
          description: "Sync with Aria, Clara, Shakes, Eric, and Purity via Kafka",
        },
        {
          name: "Campaign Collaboration Tools",
          description: "Enable team review, comments, and version control",
        },
      ],
    },
    {
      title: "Analytics & Performance",
      icon: BarChart3,
      color: "from-emerald-500 to-teal-500",
      features: [
        {
          name: "Data Analytics & Reporting",
          description: "Provide insights on campaign performance and ROI",
        },
        {
          name: "A/B Testing Automation",
          description: "Run experiments to optimize strategies automatically",
        },
        {
          name: "Campaign Performance Forecasting",
          description: "Predict engagement before launching campaigns",
        },
        {
          name: "AI-Powered Campaign Ideation",
          description: "Suggest ideas based on trends and competitors",
        },
      ],
    },
    {
      title: "Localization & Accessibility",
      icon: Globe,
      color: "from-rose-500 to-pink-500",
      features: [
        {
          name: "Multi-Language Campaign Creation",
          description: "Generate campaigns in native languages with cultural adaptation",
        },
        {
          name: "Accessibility Optimization",
          description: "Generate alt text and ensure screen-reader compatibility",
        },
        {
          name: "Ethical Campaign Guidelines",
          description: "Flag misleading claims and suggest inclusive language",
        },
        {
          name: "Ethical Ad Scanner",
          description: "Flag non-compliant or misleading ad copy",
        },
      ],
    },
    {
      title: "Advanced AI Features",
      icon: Zap,
      color: "from-violet-500 to-purple-500",
      features: [
        {
          name: "Advanced Brand Voice Customization",
          description: "Define tone (e.g., playful, eco-conscious) via samples",
        },
        {
          name: "Campaign Calendar Integration",
          description: "Visualize and edit schedules with drag-and-drop",
        },
        {
          name: "Mobile Campaign Management",
          description: "Allow campaign management via mobile app",
        },
        {
          name: "Streamlined Onboarding Experience",
          description: "Guide setup with interactive wizard and tutorials",
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
              <div className="w-12 h-12 rounded-xl bg-gradient-to-r from-pink-500 to-pink-600 flex items-center justify-center">
                <TrendingUp className="h-6 w-6 text-white" />
              </div>
              <h1 className="text-4xl font-bold text-gray-900">Jackie - AI Marketing Director</h1>
            </div>
            <p className="text-xl text-gray-600 mb-8">
              Visionary AI marketing executive specialized in full-funnel campaign strategy,
              cross-channel ad optimization, and data-driven brand growth.
            </p>

            <div className="flex flex-wrap justify-center gap-4 mb-8">
              <Badge variant="secondary" className="px-4 py-2 text-sm">
                Growth Director
              </Badge>
              <Badge variant="secondary" className="px-4 py-2 text-sm">
                Ad Spend Optimizer
              </Badge>
              <Badge variant="secondary" className="px-4 py-2 text-sm">
                Campaign Strategist
              </Badge>
              <Badge variant="secondary" className="px-4 py-2 text-sm">
                Marketing Visionary
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

        {/* Hiring Section */}
        <div className="mt-16 text-center">
          <div className="bg-gradient-to-r from-pink-500 to-pink-600 rounded-2xl p-8 text-white">
            <h3 className="text-2xl font-bold mb-4">Ready to hire Jackie?</h3>
            <p className="text-pink-100 mb-6 max-w-2xl mx-auto">
              Bring Jackie onto your marketing team and transform your brand's reach.
              She manages the complexity of modern marketing while you focus on the vision.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/auth?tab=signup">
                <Button size="lg" className="bg-white text-pink-600 hover:bg-gray-100">
                  Hire Jackie Now
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
