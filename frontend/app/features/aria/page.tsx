import {
  ArrowLeft,
  Users,
  Calendar,
  ImageIcon,
  MessageCircle,
  BarChart3,
  TrendingUp,
  Target,
  Zap,
  Globe,
} from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export default function AriaFeaturesPage() {
  const featureCategories = [
    {
      title: "Content Creation & Scheduling",
      icon: Calendar,
      color: "from-blue-500 to-cyan-500",
      features: [
        {
          name: "Post Scheduling",
          description:
            "Schedule posts across 12+ platforms (Instagram, LinkedIn, TikTok) with smart timing optimization using Buffer API",
        },
        {
          name: "AI-Generated Captions and Hashtags",
          description:
            "Generate brand-aligned captions with GPT-4-turbo and hashtags with fine-tuned LLaMA 13B, stored in Pinecone",
        },
        {
          name: "Story/Reels Templates",
          description: "Pre-designed templates for Instagram Stories and TikTok Reels using Canva API",
        },
        {
          name: "Content Remix Scheduler",
          description: "Auto-repurpose content on a set schedule across different platforms",
        },
        {
          name: "Cross-Platform Story Sync",
          description: "Auto-adapt Stories/Reels for Instagram, TikTok, Snapchat, and YouTube Shorts",
        },
      ],
    },
    {
      title: "Media Generation & Design",
      icon: ImageIcon,
      color: "from-purple-500 to-pink-500",
      features: [
        {
          name: "Media Generation",
          description: "Create images with DALL·E 3 and videos with RunwayML, stored in AWS S3",
        },
        {
          name: "AI Thumbnail Generator",
          description: "Create click-worthy thumbnails for videos automatically",
        },
        {
          name: "Voice-Generated Posts",
          description: "Convert spoken ideas into polished posts using speech-to-text and GPT-4",
        },
        {
          name: "Accessibility Features",
          description: "Auto-generate captions for videos and alt text for images",
        },
      ],
    },
    {
      title: "Engagement & Communication",
      icon: MessageCircle,
      color: "from-green-500 to-emerald-500",
      features: [
        {
          name: "Auto-Respond to Comments/DMs",
          description: "Generate context-aware responses using GPT-4 with sentiment analysis",
        },
        {
          name: "Collaboration Workflows",
          description: "Share draft posts with brands for approval via email/dashboard",
        },
        {
          name: "Influencer Collaboration Finder",
          description: "Identify and connect with micro-influencers using social listening tools",
        },
        {
          name: "Engagement Booster Prompts",
          description: "Suggest interactive elements like polls, quizzes, or CTAs",
        },
      ],
    },
    {
      title: "Analytics & Insights",
      icon: BarChart3,
      color: "from-orange-500 to-red-500",
      features: [
        {
          name: "Engagement Analytics",
          description: "Track impressions, likes, comments, and sentiment via platform APIs and Pinecone",
        },
        {
          name: "Simplified Analytics",
          description: "Local Impact metrics for non-technical users",
        },
        {
          name: "Virality Prediction Score",
          description: "Predict post performance before publishing",
        },
        {
          name: "Audience Sentiment Heatmap",
          description: "Visualize audience reactions to optimize posting strategy",
        },
        {
          name: "Custom Reporting",
          description: "Branded analytics reports using Canva API",
        },
      ],
    },
    {
      title: "Advanced Automation",
      icon: Zap,
      color: "from-indigo-500 to-purple-500",
      features: [
        {
          name: "Automated A/B Testing",
          description: "Test captions, hashtags, or visuals and auto-select the best variant",
        },
        {
          name: "Real-Time Trend Alerts",
          description: "Notify users of trending hashtags/topics with suggested posts via Brandwatch API",
        },
        {
          name: "AI-Powered Content Remix",
          description: "Repurpose one post into multiple formats (Instagram Reel to LinkedIn article)",
        },
        {
          name: "Geo-Specific Campaign Planner",
          description: "Design campaigns targeting specific regions with local insights",
        },
      ],
    },
    {
      title: "Targeting & Localization",
      icon: Target,
      color: "from-pink-500 to-rose-500",
      features: [
        {
          name: "Local Targeting",
          description: "Geotagging posts and local hashtag suggestions",
        },
        {
          name: "Account Grouping",
          description: "Organize multiple social media accounts into groups",
        },
        {
          name: "Multi-Platform Support",
          description: "Manage multiple platforms via Buffer and native APIs",
        },
      ],
    },
    {
      title: "Brand & Customization",
      icon: Users,
      color: "from-yellow-500 to-orange-500",
      features: [
        {
          name: "Brand Voice Customization",
          description: "Define brand voice (e.g., Witty, Gen-Z coded) and upload guidelines to S3",
        },
        {
          name: "Approval Workflows",
          description: "Team-based post approval with Slack/email notifications",
        },
        {
          name: "Team Collaboration",
          description: "Role-based access control (RBAC) for team members",
        },
      ],
    },
    {
      title: "Advertising & Monetization",
      icon: TrendingUp,
      color: "from-red-500 to-pink-500",
      features: [
        {
          name: "Ad Integration",
          description: "Create/monitor Instagram Ads and LinkedIn Ads campaigns",
        },
        {
          name: "Affiliate Tracking",
          description: "Track clicks/conversions from affiliate links",
        },
      ],
    },
    {
      title: "Security & Performance",
      icon: Globe,
      color: "from-gray-600 to-gray-800",
      features: [
        {
          name: "Secure Authentication",
          description: "OAuth for social media accounts, JWT for dashboard access, GDPR-compliant",
        },
        {
          name: "Scalability/Performance",
          description: "Handle 100K users, 10K posts/day, <2s latency, 99.9% uptime",
        },
        {
          name: "Integration with Other Agents",
          description: "Sync with Clara, Shakes, Eric, Jackie, and Purity via Kafka for campaigns and content",
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
              <div className="w-12 h-12 rounded-xl bg-gradient-to-r from-orange-500 to-orange-600 flex items-center justify-center">
                <Users className="h-6 w-6 text-white" />
              </div>
              <h1 className="text-4xl font-bold text-gray-900">Aria - AI Social Media Manager</h1>
            </div>
            <p className="text-xl text-gray-600 mb-8">
              Professional AI employee specializing in end-to-end social media strategy, content creation, and real-time engagement
              across 12+ platforms including Instagram, LinkedIn, TikTok, and more.
            </p>

            <div className="flex flex-wrap justify-center gap-4 mb-8">
              <Badge variant="secondary" className="px-4 py-2 text-sm">
                Multi-Platform Expert
              </Badge>
              <Badge variant="secondary" className="px-4 py-2 text-sm">
                Creative Director
              </Badge>
              <Badge variant="secondary" className="px-4 py-2 text-sm">
                Growth Strategist
              </Badge>
              <Badge variant="secondary" className="px-4 py-2 text-sm">
                24/7 Operations
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
                    className={`w-12 h-12 rounded-xl bg-gradient-to-r ${categoryIndex === 0 ? "from-orange-500 to-orange-600" : category.color} flex items-center justify-center`}
                  >
                    <IconComponent className="h-6 w-6 text-white" />
                  </div>
                  <h2 className="text-2xl font-bold text-gray-900">{category.title.replace("Features", "Skills").replace("Automation", "Operations")}</h2>
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
          <div className="bg-gradient-to-r from-orange-500 to-orange-600 rounded-2xl p-8 text-white">
            <h3 className="text-2xl font-bold mb-4">Ready to hire Aria?</h3>
            <p className="text-orange-100 mb-6 max-w-2xl mx-auto">
              Onboard Aria to your team today and let her take full ownership of your social media presence.
              She works 24/7, never misses a post, and scales with your growth.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/auth?tab=signup">
                <Button size="lg" className="bg-white text-orange-600 hover:bg-gray-100">
                  Hire Aria Now
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
