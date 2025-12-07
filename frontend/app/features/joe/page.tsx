import {
  ArrowLeft,
  Search,
  Database,
  FileText,
  Globe,
  BarChart3,
  TrendingUp,
  Users,
  Zap,
  Target,
  AlertCircle,
  BookOpen,
} from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export default function JoeFeaturesPage() {
  const featureCategories = [
    {
      title: "Data Collection & Sources",
      icon: Database,
      color: "from-blue-500 to-cyan-500",
      features: [
        {
          name: "Data Collection from Free APIs",
          description:
            "Fetches data from Wikipedia, Google Custom Search, and YouTube Data APIs for comprehensive research.",
        },
        {
          name: "Web Scraping for Structured Data",
          description:
            "Extracts structured data from websites efficiently using advanced scraping tools like ScrapeGraphAI or FireCrawl.",
        },
        {
          name: "Document Processing (PDFs, DOCX)",
          description:
            "Parses and extracts information from various document formats, including PDFs and DOCX files, using PyPDF2 and python-docx.",
        },
        {
          name: "Custom Data Source Integration",
          description: "Connect and integrate with custom data sources for specialized research needs.",
        },
        {
          name: "Google Drive Upload Integration",
          description:
            "Seamlessly exports and uploads generated research outputs directly to your Google Drive for easy access and sharing.",
        },
      ],
    },
    {
      title: "Market Research & Analysis",
      icon: TrendingUp,
      color: "from-green-500 to-emerald-500",
      features: [
        {
          name: "Market Trend Analysis",
          description: "Real-time trend monitoring and analysis using Google Trends and Brandwatch.",
        },
        {
          name: "Niche Market Discovery",
          description: "Identify untapped markets and opportunities with low competition.",
        },
        {
          name: "Trend Forecasting",
          description: "Predictive trend analysis to stay ahead of market changes.",
        },
        {
          name: "Geo-Specific Research",
          description: "Location-based market insights for targeted regional analysis.",
        },
        {
          name: "Market Opportunity Scoring",
          description: "Evaluate and score market opportunities based on multiple factors.",
        },
      ],
    },
    {
      title: "Competitor Intelligence",
      icon: Target,
      color: "from-purple-500 to-pink-500",
      features: [
        {
          name: "Competitor Analysis",
          description: "Comprehensive competitor intelligence gathering via SEMrush and SimilarWeb APIs.",
        },
        {
          name: "Competitor Benchmarking",
          description: "Performance comparison analysis against industry competitors.",
        },
        {
          name: "Competitor Ad Tracking",
          description: "Automated competitor ad tracking via Facebook Ads Library.",
        },
        {
          name: "Social Proof Analyzer",
          description: "Analyze competitor social proof and marketing strategies.",
        },
      ],
    },
    {
      title: "Content Analysis & NLP",
      icon: FileText,
      color: "from-orange-500 to-red-500",
      features: [
        {
          name: "Advanced NLP for Summarization",
          description:
            "Leverages Hugging Face Transformers (LLaMA, MarianMT) for summarizing content, extracting entities, and performing translations.",
        },
        {
          name: "Research Summarizer",
          description: "AI-powered research summaries for quick insights.",
        },
        {
          name: "Sentiment Tracking",
          description: "Brand and product sentiment monitoring with NLP and Pinecone.",
        },
        {
          name: "Keyword Research",
          description: "SEO and content keyword analysis using Ahrefs API.",
        },
      ],
    },
    {
      title: "Reporting & Export",
      icon: BookOpen,
      color: "from-indigo-500 to-violet-500",
      features: [
        {
          name: "Customizable Report Generation",
          description:
            "Generates research reports in multiple formats (DOCX, PDF, JSON, Markdown) with user-defined templates for tailored outputs.",
        },
        {
          name: "Industry Reports",
          description: "Automated industry intelligence reports with comprehensive insights.",
        },
        {
          name: "Data Export",
          description: "Multi-format data export capabilities (CSV, PDF, branded reports).",
        },
        {
          name: "Data Visualization",
          description: "Interactive charts and dashboards with Tableau integration.",
        },
      ],
    },
    {
      title: "Consumer & Audience Insights",
      icon: Users,
      color: "from-pink-500 to-rose-500",
      features: [
        {
          name: "Consumer Behavior",
          description: "User behavior pattern analysis via Brandwatch and SurveyMonkey.",
        },
        {
          name: "Customer Persona",
          description: "Detailed customer profiling and persona building.",
        },
        {
          name: "Social Media Listening",
          description: "Cross-platform social media monitoring using Hootsuite Insights.",
        },
        {
          name: "Survey Creation",
          description: "Automated survey generation via Typeform integration.",
        },
      ],
    },
    {
      title: "Real-Time Monitoring",
      icon: AlertCircle,
      color: "from-red-500 to-pink-500",
      features: [
        {
          name: "Real-Time Updates via WebSockets",
          description: "Streams research progress and results in real-time, keeping you informed throughout the process.",
        },
        {
          name: "News Monitoring",
          description: "Real-time news tracking and analysis via Google News API.",
        },
        {
          name: "Trend Alerts",
          description: "Real-time trend notifications via Slack integration.",
        },
        {
          name: "Patent Tracking",
          description: "IP and innovation monitoring via Google Patents API.",
        },
      ],
    },
    {
      title: "Advanced AI Features",
      icon: Zap,
      color: "from-yellow-500 to-orange-500",
      features: [
        {
          name: "Personalization through Fine-Tuned LLMs",
          description:
            "Fine-tunes Large Language Models on your specific data for highly personalized and relevant research outputs.",
        },
        {
          name: "AI-Powered Research Ideation",
          description: "Generate research ideas and hypotheses using AI assistance.",
        },
        {
          name: "AI-Assisted Hypothesis Testing",
          description: "Test research hypotheses with AI-powered analysis.",
        },
        {
          name: "Custom Research Queries",
          description: "Personalized research queries with GPT-4-turbo for specific needs.",
        },
      ],
    },
    {
      title: "Global & Accessibility",
      icon: Globe,
      color: "from-cyan-500 to-blue-500",
      features: [
        {
          name: "Multilingual Content Support",
          description: "Processes and generates research content in multiple languages, expanding your global reach.",
        },
        {
          name: "Multi-Language Research",
          description: "Global market insights with translation APIs.",
        },
        {
          name: "Accessibility Features",
          description: "Ensure research outputs are accessible and screen-reader compatible.",
        },
      ],
    },
    {
      title: "Automation & Workflow",
      icon: Zap,
      color: "from-gray-600 to-gray-800",
      features: [
        {
          name: "Research Automation Scheduler",
          description: "Schedule and automate recurring research tasks.",
        },
        {
          name: "Collaborative Research Workflows",
          description: "Team collaboration via Notion integration for shared research projects.",
        },
        {
          name: "Historical Data Analysis",
          description: "Analyze historical trends and patterns for long-term insights.",
        },
        {
          name: "Cross-Platform Data Integration",
          description: "Integrate data from multiple platforms for unified research insights.",
        },
      ],
    },
    {
      title: "Compliance & Ethics",
      icon: AlertCircle,
      color: "from-teal-500 to-emerald-500",
      features: [
        {
          name: "Compliance Checker",
          description: "Regulatory compliance validation for GDPR and other standards.",
        },
        {
          name: "Ethical Research Guidelines",
          description: "Ensure research follows ethical guidelines and best practices.",
        },
      ],
    },
    {
      title: "User Experience",
      icon: BarChart3,
      color: "from-violet-500 to-purple-500",
      features: [
        {
          name: "Onboarding Wizard",
          description: "Step-by-step setup guide for new users.",
        },
        {
          name: "Mobile Research Dashboard",
          description: "Monitor and manage research on the go with mobile access.",
        },
        {
          name: "Voice-Activated Research Queries",
          description: "Conduct research using voice commands via Google Assistant.",
        },
        {
          name: "Research Performance Analytics",
          description: "Track and analyze research performance and effectiveness.",
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
                Back to Features
              </Button>
            </Link>
          </div>

          <div className="text-center max-w-3xl mx-auto">
            <div className="flex items-center justify-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-r from-sky-400 to-cyan-500 flex items-center justify-center">
                <Search className="h-6 w-6 text-white" />
              </div>
              <h1 className="text-4xl font-bold text-gray-900">Joe Features</h1>
            </div>
            <p className="text-xl text-gray-600 mb-8">
              Comprehensive research and data analysis platform with AI-powered market research, competitor analysis,
              trend tracking, and automated report generation across multiple sources and platforms.
            </p>

            <div className="flex flex-wrap justify-center gap-4 mb-8">
              <Badge variant="secondary" className="px-4 py-2 text-sm">
                Market Research
              </Badge>
              <Badge variant="secondary" className="px-4 py-2 text-sm">
                Competitor Analysis
              </Badge>
              <Badge variant="secondary" className="px-4 py-2 text-sm">
                AI-Powered Insights
              </Badge>
              <Badge variant="secondary" className="px-4 py-2 text-sm">
                Real-Time Monitoring
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

        {/* CTA Section */}
        <div className="mt-16 text-center">
          <div className="bg-gradient-to-r from-sky-400 to-cyan-500 rounded-2xl p-8 text-white">
            <h3 className="text-2xl font-bold mb-4">Ready to Automate Your Research?</h3>
            <p className="text-sky-100 mb-6 max-w-2xl mx-auto">
              Start leveraging Joe's powerful research capabilities to save time and gain deeper insights with
              AI-powered automation.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/auth?tab=signup">
                <Button size="lg" className="bg-white text-cyan-600 hover:bg-gray-100">
                  Get Started with Joe
                </Button>
              </Link>
              <Link href="/pricing">
                <Button size="lg" variant="outline" className="border-white text-white hover:bg-white/10">
                  View Pricing Plans
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
