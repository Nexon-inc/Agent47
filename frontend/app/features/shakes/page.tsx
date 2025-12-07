import {
  ArrowLeft,
  PenTool,
  FileText,
  Search,
  Video,
  Globe,
  Palette,
  BarChart3,
  Users,
  Smartphone,
  Zap,
} from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export default function ShakesFeaturesPage() {
  const featureCategories = [
    {
      title: "Content Writing & Generation",
      icon: FileText,
      color: "from-pink-500 to-rose-500",
      features: [
        {
          name: "Blog & Article Writing",
          description: "Generate well-researched long-form articles with AI assistance",
        },
        {
          name: "Social Media Content",
          description: "Create captions, tweets, LinkedIn posts, and Instagram descriptions",
        },
        {
          name: "AI-Powered Content Generation",
          description: "Produce high-quality drafts across all content formats",
        },
        {
          name: "Human-Like Content Refinement",
          description: "Add idioms, storytelling, and cultural references for authenticity",
        },
        {
          name: "Interactive Content Creation",
          description: "Support polls, quizzes, and Q&A podcast scripts",
        },
      ],
    },
    {
      title: "SEO & Optimization",
      icon: Search,
      color: "from-green-500 to-emerald-500",
      features: [
        {
          name: "SEO Optimization",
          description: "Embed keywords for higher search rankings naturally",
        },
        {
          name: "SEO Optimization & Keyword Integration",
          description: "Embed keywords naturally for readability and ranking",
        },
        {
          name: "Localized SEO Optimization",
          description: "Suggest region-specific keywords and trends",
        },
        {
          name: "Content Performance Forecasting",
          description: "Predict engagement and SEO performance before publishing",
        },
      ],
    },
    {
      title: "Video & Media Creation",
      icon: Video,
      color: "from-purple-500 to-indigo-500",
      features: [
        {
          name: "Video & Podcast Scripting",
          description: "Develop compelling video scripts and podcast outlines",
        },
        {
          name: "Video & Image Generation",
          description: "Create promotional videos and images with AI tools",
        },
        {
          name: "AI Storyboard Generator",
          description: "Create visual storyboards for videos or campaigns",
        },
        {
          name: "AI Thumbnail Generator",
          description: "Create click-worthy thumbnails for videos automatically",
        },
        {
          name: "Voiceover Integration",
          description: "Generate AI voiceovers in multiple accents and languages",
        },
      ],
    },
    {
      title: "Marketing & Advertising",
      icon: BarChart3,
      color: "from-orange-500 to-red-500",
      features: [
        {
          name: "Ad Copywriting",
          description: "Craft high-converting ad copy for Google Ads, Facebook Ads, and more",
        },
        {
          name: "Email & Newsletter Writing",
          description: "Generate engaging email sequences for marketing campaigns",
        },
        {
          name: "Website & Landing Page Content",
          description: "Provide optimized text for web pages and landing pages",
        },
        {
          name: "Ad Copy & Marketing Content Generation",
          description: "Create product descriptions and compelling CTAs",
        },
      ],
    },
    {
      title: "Content Management & Scheduling",
      icon: Globe,
      color: "from-blue-500 to-cyan-500",
      features: [
        {
          name: "Content Repurposing",
          description: "Transform content into different formats for broader reach",
        },
        {
          name: "Social Media Content Automation",
          description: "Schedule posts via integration with Buffer and other platforms",
        },
        {
          name: "Content Calendar Integration",
          description: "Visualize and edit schedules with drag-and-drop functionality",
        },
        {
          name: "Content Remix Scheduler",
          description: "Auto-repurpose content on a set schedule across platforms",
        },
        {
          name: "Content Version Control",
          description: "Track and revert changes in collaborative projects",
        },
      ],
    },
    {
      title: "Brand Voice & Customization",
      icon: Palette,
      color: "from-indigo-500 to-purple-500",
      features: [
        {
          name: "Grammar & Tone Refinement",
          description: "Polish drafts for grammar and tone consistency",
        },
        {
          name: "Advanced Brand Voice Customization",
          description: "Define tone (e.g., witty, sustainable) via sample content",
        },
        {
          name: "Dynamic Content Personalization",
          description: "Target specific customer segments using CRM data",
        },
        {
          name: "Content Sentiment Analyzer",
          description: "Ensure content aligns with desired emotional impact",
        },
      ],
    },
    {
      title: "Analytics & Performance",
      icon: BarChart3,
      color: "from-yellow-500 to-orange-500",
      features: [
        {
          name: "Plagiarism Detection & Originality Checking",
          description: "Ensure content is unique and original",
        },
        {
          name: "Deep Performance Analytics",
          description: "Provide A/B testing, sentiment analysis, and competitor benchmarking",
        },
        {
          name: "Content DNA",
          description: "Visual heatmap of top-performing themes, keywords, or tones per platform",
        },
        {
          name: "Trend-Based Content Planner",
          description: "Suggest content based on real-time trends and data",
        },
      ],
    },
    {
      title: "Collaboration & Workflow",
      icon: Users,
      color: "from-teal-500 to-green-500",
      features: [
        {
          name: "Content Collaboration Tools",
          description: "Enable team review, comments, and version control",
        },
        {
          name: "AI-Powered Content Ideation",
          description: "Suggest ideas based on trends and competitor analysis",
        },
        {
          name: "Interactive Content Widgets",
          description: "Embed quizzes or polls in blogs and emails",
        },
      ],
    },
    {
      title: "Platform Integration",
      icon: Zap,
      color: "from-gray-600 to-gray-800",
      features: [
        {
          name: "Integration with Scheduling & Marketing Tools",
          description: "Connect with Buffer, Mailchimp, HubSpot, and other platforms",
        },
        {
          name: "Integration with Design and CMS Tools",
          description: "Connect with WordPress, Shopify, Figma for seamless workflow",
        },
        {
          name: "Integration with Other Agents",
          description: "Sync with Aria, Clara, Eric, Jackie, and Purity via Kafka",
        },
      ],
    },
    {
      title: "Accessibility & Compliance",
      icon: Smartphone,
      color: "from-emerald-500 to-teal-500",
      features: [
        {
          name: "Accessibility Optimization",
          description: "Generate alt text and ensure screen-reader compatibility",
        },
        {
          name: "Accessibility Checker",
          description: "Ensure content meets WCAG standards for accessibility",
        },
        {
          name: "Ethical Content Guidelines",
          description: "Flag misleading claims and suggest inclusive language",
        },
      ],
    },
    {
      title: "Localization & Multi-Language",
      icon: Globe,
      color: "from-rose-500 to-pink-500",
      features: [
        {
          name: "Multi-Language Content Creation",
          description: "Generate content in native languages with cultural adaptation",
        },
        {
          name: "Automated Content Localization",
          description: "Adapt content for regional dialects and slang automatically",
        },
        {
          name: "Platform-Specific Optimization for Emerging Channels",
          description: "Create content for TikTok, Threads, Snapchat, and other new platforms",
        },
      ],
    },
    {
      title: "Advanced AI Features",
      icon: Zap,
      color: "from-violet-500 to-purple-500",
      features: [
        {
          name: "Enhanced Video & Image Design Tools",
          description: "Offer templates, fonts, and animations for visuals",
        },
        {
          name: "Mobile Content Preview and Editing",
          description: "Allow content management via mobile app",
        },
        {
          name: "Streamlined Onboarding Experience",
          description: "Guide setup with interactive wizard and tutorials",
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
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center gap-4 mb-6">
            <Link href="/features">
              <Button variant="ghost" size="sm" className="gap-2">
                <ArrowLeft className="h-4 w-4" />
                Back to Features
              </Button>
            </Link>
          </div>

          <div className="text-center max-w-3xl mx-auto">
            <div className="flex items-center justify-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-r from-green-500 to-green-600 flex items-center justify-center">
                <PenTool className="h-6 w-6 text-white" />
              </div>
              <h1 className="text-4xl font-bold text-gray-900">Shakes Features</h1>
            </div>
            <p className="text-xl text-gray-600 mb-8">
              Comprehensive content creation platform with AI-powered writing, SEO optimization, video scripting, and
              multi-format content generation for all your marketing needs.
            </p>

            <div className="flex flex-wrap justify-center gap-4 mb-8">
              <Badge variant="secondary" className="px-4 py-2 text-sm">
                AI Content Generation
              </Badge>
              <Badge variant="secondary" className="px-4 py-2 text-sm">
                SEO Optimization
              </Badge>
              <Badge variant="secondary" className="px-4 py-2 text-sm">
                Multi-Format Content
              </Badge>
              <Badge variant="secondary" className="px-4 py-2 text-sm">
                Brand Voice Customization
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
                    className={`w-12 h-12 rounded-xl bg-gradient-to-r ${categoryIndex === 0 ? "from-green-500 to-green-600" : category.color} flex items-center justify-center`}
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

        {/* CTA Section */}
        <div className="mt-16 text-center">
          <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-2xl p-8 text-white">
            <h3 className="text-2xl font-bold mb-4">Ready to Transform Your Content Creation?</h3>
            <p className="text-green-100 mb-6 max-w-2xl mx-auto">
              Join thousands of content creators and marketers using Shakes to streamline their content workflow and
              create engaging, high-quality content at scale.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/auth?tab=signup">
                <Button size="lg" className="bg-white text-green-600 hover:bg-gray-100">
                  Start Creating Today
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
