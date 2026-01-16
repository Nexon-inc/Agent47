"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useAuthStore } from "@/lib/stores/auth-store"
import {
  Globe,
  Headphones,
  FileText,
  BarChart3,
  DollarSign,
  ChevronLeft,
  ChevronRight,
  Check,
  Info,
  X,
  ArrowRight,
  Play,
  Instagram,
  Linkedin,
  Twitter,
  Youtube,
  Facebook,
  Video,
  ImageIcon,
  Mail,
  BarChart,
  Cloud,
  ShoppingBag,
  PieChart,
  Zap,
  Users,
  Clock,
  Target,
  Award,
  Slack,
  Github,
  Trello,
  Figma,
  BoomBox as Dropbox,
  Chrome,
  Twitch,
  Dribbble,
  SproutIcon as Spotify,
  Lightbulb,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

// Types
type Step = "welcome" | "business" | "goals" | "complete"
type Role =
  | "ceo_founder"
  | "small_business"
  | "startup"
  | "enterprise"
  | "marketing_manager"
  | "sales_manager"
  | "operations_manager"
  | "agency_owner"
  | ""
type Industry =
  | "retail"
  | "technology"
  | "healthcare"
  | "finance"
  | "education"
  | "entertainment"
  | "food"
  | "travel"
  | "other"
  | ""
type Goal =
  | "grow_audience"
  | "customer_support"
  | "content_creation"
  | "sales"
  | "marketing"
  | "automation"
  | "productivity"
  | "analytics"
  | "team_collaboration"
  | "lead_generation"
  | "brand_awareness"
  | "business_development"
  | "other"
type SocialPlatform =
  | "instagram"
  | "linkedin"
  | "twitter"
  | "youtube"
  | "facebook"
  | "tiktok"
  | "pinterest"
  | "slack"
  | "discord"
  | "mailchimp"
  | "hubspot"
  | "salesforce"
  | "shopify"
  | "wordpress"
  | "google"
  | "github"
  | "trello"
  | "figma"
  | "dropbox"
  | "chrome"
  | "twitch"
  | "dribbble"
  | "spotify"
type Tutorial = "aria" | "clara" | "shakes" | "eric" | "jackie" | "purity" | "workflows"

interface ProfileData {
  role: Role
  industry: Industry
  goals: Goal[]
  otherGoal?: string
  business_name?: string
  business_website?: string
  business_size?: string
  business_stage?: string
  purpose?: string
}

interface SocialData {
  connectedPlatforms: SocialPlatform[]
  skipSocial: boolean
}

interface TutorialData {
  watchedTutorials: Tutorial[]
  showTutorialsLater: boolean
}

interface WorkflowData {
  createdWorkflow: boolean
  selectedTemplate: string | null
  skipWorkflow: boolean
}

// Constants
const STEPS: Step[] = ["welcome", "business", "goals", "complete"]
const STEP_LABELS = {
  welcome: "Welcome",
  business: "Business Info",
  goals: "Your Goals",
  complete: "Complete",
  social: "Platforms",
  tutorials: "Tutorials",
  workflow: "First Workflow",
}

const ROLES: { value: Role; label: string; description: string }[] = [
  {
    value: "ceo_founder",
    label: "CEO/Founder",
    description: "Business leader responsible for overall strategy and growth",
  },
  {
    value: "small_business",
    label: "Small Business Owner",
    description: "Owner of a local or online business with <50 employees",
  },
  {
    value: "startup",
    label: "Startup Founder",
    description: "Founder of a growing tech company or new venture",
  },
  {
    value: "enterprise",
    label: "Enterprise Executive",
    description: "Executive in a large organization with multiple departments",
  },
  {
    value: "marketing_manager",
    label: "Marketing Manager",
    description: "Professional responsible for marketing strategy and campaigns",
  },
  {
    value: "sales_manager",
    label: "Sales Manager",
    description: "Professional focused on sales strategy and team management",
  },
  {
    value: "operations_manager",
    label: "Operations Manager",
    description: "Professional responsible for business operations and efficiency",
  },
  {
    value: "agency_owner",
    label: "Agency Owner",
    description: "Owner of a service agency working with multiple clients",
  },
]

const INDUSTRIES: { value: Industry; label: string }[] = [
  { value: "retail", label: "Retail & E-commerce" },
  { value: "technology", label: "Technology & SaaS" },
  { value: "healthcare", label: "Healthcare & Wellness" },
  { value: "finance", label: "Finance & Insurance" },
  { value: "education", label: "Education & Training" },
  { value: "entertainment", label: "Entertainment & Media" },
  { value: "food", label: "Food & Beverage" },
  { value: "travel", label: "Travel & Hospitality" },
  { value: "other", label: "Other" },
]

const GOALS: { value: Goal; label: string; description: string; icon: React.ElementType }[] = [
  {
    value: "grow_audience",
    label: "Grow My Audience",
    description: "Increase followers and engagement on social media",
    icon: Globe,
  },
  {
    value: "customer_support",
    label: "Improve Customer Support",
    description: "Automate responses and handle inquiries faster",
    icon: Headphones,
  },
  {
    value: "content_creation",
    label: "Create Better Content",
    description: "Generate engaging posts, blogs, and videos",
    icon: FileText,
  },
  {
    value: "sales",
    label: "Boost Sales",
    description: "Convert more leads and increase revenue",
    icon: DollarSign,
  },
  {
    value: "marketing",
    label: "Optimize Marketing",
    description: "Improve campaigns and track performance",
    icon: BarChart3,
  },
  {
    value: "business_development",
    label: "Launch New Business",
    description: "Generate ideas, validate opportunities, and scale",
    icon: Lightbulb,
  },
  {
    value: "automation",
    label: "Automate Workflows",
    description: "Save time with automated business processes",
    icon: Zap,
  },
  {
    value: "productivity",
    label: "Increase Productivity",
    description: "Get more done with AI assistance",
    icon: Clock,
  },
  {
    value: "analytics",
    label: "Better Analytics",
    description: "Gain insights from your data",
    icon: PieChart,
  },
  {
    value: "team_collaboration",
    label: "Team Collaboration",
    description: "Improve how your team works together",
    icon: Users,
  },
  {
    value: "lead_generation",
    label: "Generate Leads",
    description: "Find and qualify potential customers",
    icon: Target,
  },
  {
    value: "brand_awareness",
    label: "Build Brand Awareness",
    description: "Increase recognition and visibility",
    icon: Award,
  },
  {
    value: "other",
    label: "Other Goal",
    description: "Tell us what you're looking to achieve",
    icon: Info,
  },
]

const SOCIAL_PLATFORMS: { id: SocialPlatform; name: string; icon: React.ElementType; color: string }[] = [
  {
    id: "instagram",
    name: "Instagram",
    icon: Instagram,
    color: "bg-gradient-to-r from-purple-500 to-pink-500",
  },
  {
    id: "linkedin",
    name: "LinkedIn",
    icon: Linkedin,
    color: "bg-blue-600",
  },
  {
    id: "twitter",
    name: "X (Twitter)",
    icon: Twitter,
    color: "bg-black",
  },
  {
    id: "youtube",
    name: "YouTube",
    icon: Youtube,
    color: "bg-red-600",
  },
  {
    id: "facebook",
    name: "Facebook",
    icon: Facebook,
    color: "bg-blue-700",
  },
  {
    id: "tiktok",
    name: "TikTok",
    icon: Video,
    color: "bg-black",
  },
  {
    id: "pinterest",
    name: "Pinterest",
    icon: ImageIcon,
    color: "bg-red-500",
  },
  {
    id: "slack",
    name: "Slack",
    icon: Slack,
    color: "bg-purple-600",
  },
  {
    id: "discord",
    name: "Discord",
    icon: Headphones,
    color: "bg-indigo-600",
  },
  {
    id: "mailchimp",
    name: "Mailchimp",
    icon: Mail,
    color: "bg-yellow-500",
  },
  {
    id: "hubspot",
    name: "HubSpot",
    icon: BarChart,
    color: "bg-orange-500",
  },
  {
    id: "salesforce",
    name: "Salesforce",
    icon: Cloud,
    color: "bg-blue-500",
  },
  {
    id: "shopify",
    name: "Shopify",
    icon: ShoppingBag,
    color: "bg-green-600",
  },
  {
    id: "wordpress",
    name: "WordPress",
    icon: FileText,
    color: "bg-blue-700",
  },
  {
    id: "google",
    name: "Google Analytics",
    icon: PieChart,
    color: "bg-yellow-600",
  },
  {
    id: "github",
    name: "GitHub",
    icon: Github,
    color: "bg-gray-800",
  },
  {
    id: "trello",
    name: "Trello",
    icon: Trello,
    color: "bg-blue-400",
  },
  {
    id: "figma",
    name: "Figma",
    icon: Figma,
    color: "bg-purple-800",
  },
  {
    id: "dropbox",
    name: "Dropbox",
    icon: Dropbox,
    color: "bg-blue-600",
  },
  {
    id: "chrome",
    name: "Chrome",
    icon: Chrome,
    color: "bg-gradient-to-r from-red-500 via-yellow-500 to-green-500",
  },
  {
    id: "twitch",
    name: "Twitch",
    icon: Twitch,
    color: "bg-purple-700",
  },
  {
    id: "dribbble",
    name: "Dribbble",
    icon: Dribbble,
    color: "bg-pink-600",
  },
  {
    id: "spotify",
    name: "Spotify",
    icon: Spotify,
    color: "bg-green-600",
  },
]

const TUTORIALS: { id: Tutorial; title: string; duration: string; thumbnail: string; agent: string; color: string }[] =
  [
    {
      id: "aria",
      title: "Social Media Management with Aria",
      duration: "2:15",
      thumbnail: "/placeholder.svg?height=120&width=200",
      agent: "Aria",
      color: "border-blue-400",
    },
    {
      id: "clara",
      title: "Customer Support with Clara",
      duration: "1:45",
      thumbnail: "/placeholder.svg?height=120&width=200",
      agent: "Clara",
      color: "border-green-400",
    },
    {
      id: "shakes",
      title: "Content Creation with Shakes",
      duration: "3:10",
      thumbnail: "/placeholder.svg?height=120&width=200",
      agent: "Shakes",
      color: "border-purple-400",
    },
    {
      id: "eric",
      title: "Sales Automation with Eric",
      duration: "2:30",
      thumbnail: "/placeholder.svg?height=120&width=200",
      agent: "Eric",
      color: "border-red-400",
    },
    {
      id: "jackie",
      title: "Marketing Campaigns with Jackie",
      duration: "2:50",
      thumbnail: "/placeholder.svg?height=120&width=200",
      agent: "Jackie",
      color: "border-amber-400",
    },
    {
      id: "purity",
      title: "Business Development with Purity",
      duration: "3:20",
      thumbnail: "/placeholder.svg?height=120&width=200",
      agent: "Purity",
      color: "border-indigo-400",
    },
    {
      id: "workflows",
      title: "Creating Your First Workflow",
      duration: "4:20",
      thumbnail: "/placeholder.svg?height=120&width=200",
      agent: "Workflows",
      color: "border-gray-400",
    },
  ]

// Default values
const defaultProfile: ProfileData = {
  role: "",
  industry: "",
  goals: [],
  otherGoal: "",
  business_name: "",
  business_website: "",
  business_size: "",
  business_stage: "",
  purpose: "",
}

const defaultSocial: SocialData = {
  connectedPlatforms: [],
  skipSocial: false,
}

const defaultTutorials: TutorialData = {
  watchedTutorials: [],
  showTutorialsLater: false,
}

const defaultWorkflow: WorkflowData = {
  createdWorkflow: false,
  selectedTemplate: null,
  skipWorkflow: false,
}

export default function OnboardingPage() {
  const router = useRouter()
  const [currentStep, setCurrentStep] = useState<Step>("welcome")
  const [profile, setProfile] = useState<ProfileData>(defaultProfile)
  const [social, setSocial] = useState<SocialData>(defaultSocial)
  const [tutorials, setTutorials] = useState<TutorialData>(defaultTutorials)
  const [workflow, setWorkflow] = useState<WorkflowData>(defaultWorkflow)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [isLoading, setIsLoading] = useState(false)
  const [currentTutorial, setCurrentTutorial] = useState<Tutorial | null>(null)
  const [isScrolled, setIsScrolled] = useState(false)
  const [apiClient, setApiClient] = useState(null)

  // Calculate completion percentage for the current step
  const calculateStepCompletion = (): number => {
    switch (currentStep) {
      case "welcome":
        return 100 // Welcome step is always 100% complete
      case "business":
        let businessCompletion = 0
        if (profile.role) businessCompletion += 25
        if (profile.industry) businessCompletion += 25
        if (profile.business_name) businessCompletion += 25
        if (profile.country) businessCompletion += 25
        return Math.min(100, businessCompletion)
      case "goals":
        let goalsCompletion = 0
        if (profile.goals.length > 0) goalsCompletion += 50
        if (profile.goals.includes("other") ? profile.otherGoal : true) goalsCompletion += 50
        return Math.min(100, goalsCompletion)
      case "complete":
        return 100 // Complete step is always 100% complete
      default:
        return 0
    }
  }

  // Check if the current step is complete and can proceed
  const isCurrentStepComplete = (): boolean => {
    switch (currentStep) {
      case "welcome":
        return true // Welcome step is always complete
      case "business":
        return (
          !!profile.role &&
          !!profile.industry
        )
      case "goals":
        return (
          profile.goals.length > 0 &&
          (!profile.goals.includes("other") || !!profile.otherGoal)
        )
      case "complete":
        return true // Complete step is always complete
      default:
        return false
    }
  }

  // Handle scroll for header shadow
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10)
    }

    window.addEventListener("scroll", handleScroll)
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  useEffect(() => {
    // Dynamically import the ApiClient to ensure it runs only on the client-side
    import("@/lib/api-client").then((module) => {
      const client = module.apiClient
      client.initializeSupabase()
      setApiClient(client)
    })
  }, [])

  // Step navigation
  const goToStep = (step: Step) => {
    setCurrentStep(step)
    window.scrollTo({ top: 0, behavior: "smooth" })
  }

  const goToNextStep = () => {
    const currentIndex = STEPS.indexOf(currentStep)
    if (currentIndex < STEPS.length - 1) {
      if (validateCurrentStep()) {
        goToStep(STEPS[currentIndex + 1])
      }
    } else {
      // Last step - complete onboarding
      completeOnboarding()
    }
  }

  const goToPreviousStep = () => {
    const currentIndex = STEPS.indexOf(currentStep)
    if (currentIndex > 0) {
      goToStep(STEPS[currentIndex - 1])
    }
  }

  // Skip onboarding - FASTER
  const skipOnboarding = () => {
    setIsLoading(true)
    // Reduced from 1000ms to 300ms
    setTimeout(() => {
      router.push("/pricing")
    }, 300)
  }

  // Complete onboarding - FASTER
  const completeOnboarding = async () => {
    setIsLoading(true)
    try {
      // Get user data from auth store to include in onboarding data
      const { user, isAuthenticated, refreshUser } = useAuthStore.getState()
      console.log("User data from auth store:", user)
      console.log("Is authenticated:", isAuthenticated)
      
      const onboardingPayload = {
        profile: {
          ...profile,
          // Include user data from signup
          name: user?.full_name || user?.first_name + ' ' + user?.last_name || '',
          full_name: user?.full_name || user?.first_name + ' ' + user?.last_name || '',
          nickname: user?.username || '',
          username: user?.username || '',
          email: user?.email || '',
        },
        // Note: social, tutorials, and workflow data are not persisted to backend
        // User info and integrations are managed separately
      }
      
      // Save to localStorage as backup
      localStorage.setItem('onboarding-data', JSON.stringify(onboardingPayload))
      console.log("Onboarding data saved to localStorage:", onboardingPayload)
      
      // Try to save onboarding data if user is authenticated and API client is available
      if (isAuthenticated && user && apiClient) {
        try {
          await apiClient.saveOnboardingData(onboardingPayload)
          console.log("Onboarding data saved successfully to backend:", onboardingPayload)
          
          // Refresh user data to include the saved onboarding data
          try {
            await refreshUser()
            console.log("User data refreshed after onboarding save")
          } catch (refreshError) {
            console.error("Failed to refresh user data after onboarding save:", refreshError)
            // Continue anyway - user can still proceed
          }
        } catch (apiError) {
          console.error("Failed to save onboarding data to backend:", apiError)
          // Continue with redirect even if backend save fails
        }
      } else {
        console.log("User not authenticated or API client not available, data saved to localStorage only")
        console.log("Authentication status:", { isAuthenticated, hasUser: !!user, hasApiClient: !!apiClient })
      }
      
      // Redirect to pricing page
      router.push("/pricing")
    } catch (error) {
      console.error("Failed to complete onboarding:", error)
      // Still redirect to pricing page even if save fails
      router.push("/pricing")
    } finally {
      setIsLoading(false)
    }
  }

  // Validation
  const validateCurrentStep = (): boolean => {
    const newErrors: Record<string, string> = {}

    switch (currentStep) {
      case "business":
        if (!profile.role) {
          newErrors.role = "Please select your role"
        }
        if (!profile.industry) {
          newErrors.industry = "Please select your industry"
        }
        break
      case "goals":
        if (profile.goals.length === 0) {
          newErrors.goals = "Please select at least one goal"
        }
        if (profile.goals.includes("other") && !profile.otherGoal) {
          newErrors.otherGoal = "Please describe your other goal"
        }
        break
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  // Form handlers
  const handleRoleChange = (role: Role) => {
    setProfile((prev) => ({ ...prev, role }))

    // Clear error when field is filled
    if (errors.role) {
      setErrors((prev) => {
        const newErrors = { ...prev }
        delete newErrors.role
        return newErrors
      })
    }
  }

  const handleIndustryChange = (industry: Industry) => {
    setProfile((prev) => ({ ...prev, industry }))

    // Clear error when field is filled
    if (errors.industry) {
      setErrors((prev) => {
        const newErrors = { ...prev }
        delete newErrors.industry
        return newErrors
      })
    }
  }

  const handleGoalToggle = (goal: Goal) => {
    setProfile((prev) => {
      // If already selected, remove it
      if (prev.goals.includes(goal)) {
        return {
          ...prev,
          goals: prev.goals.filter((g) => g !== goal),
          // Clear otherGoal if "other" is deselected
          ...(goal === "other" ? { otherGoal: "" } : {}),
        }
      }

      // If not selected, add it
      return {
        ...prev,
        goals: [...prev.goals, goal],
      }
    })

    // Clear error when at least one goal is selected
    if (errors.goals) {
      setErrors((prev) => {
        const newErrors = { ...prev }
        delete newErrors.goals
        return newErrors
      })
    }
  }

  const handleOtherGoalChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const otherGoal = e.target.value
    setProfile((prev) => ({ ...prev, otherGoal }))

    // Clear error when field is filled
    if (errors.otherGoal && otherGoal) {
      setErrors((prev) => {
        const newErrors = { ...prev }
        delete newErrors.otherGoal
        return newErrors
      })
    }
  }

  const handleProfileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setProfile((prev) => ({ ...prev, [name]: value }))
  }

  const handleProfileSelectChange = (name: string, value: string) => {
    setProfile((prev) => ({ ...prev, [name]: value }))
  }
  const handleSocialConnect = (platform: SocialPlatform) => {
    // Toggle platform selection
    setSocial((prev) => {
      if (prev.connectedPlatforms.includes(platform)) {
        return {
          ...prev,
          connectedPlatforms: prev.connectedPlatforms.filter((p) => p !== platform),
        }
      } else {
        return {
          ...prev,
          connectedPlatforms: [...prev.connectedPlatforms, platform],
        }
      }
    })

    // Clear error when at least one platform is connected
    if (errors.social) {
      setErrors((prev) => {
        const newErrors = { ...prev }
        delete newErrors.social
        return newErrors
      })
    }
  }

  const handleSkipSocialToggle = (checked: boolean) => {
    setSocial((prev) => ({ ...prev, skipSocial: checked }))

    // Clear error if skipping
    if (checked && errors.social) {
      setErrors((prev) => {
        const newErrors = { ...prev }
        delete newErrors.social
        return newErrors
      })
    }
  }

  const handleWatchTutorial = (tutorial: Tutorial) => {
    setCurrentTutorial(tutorial)

    // In a real app, this would track that the user watched the tutorial
    if (!tutorials.watchedTutorials.includes(tutorial)) {
      setTutorials((prev) => ({
        ...prev,
        watchedTutorials: [...prev.watchedTutorials, tutorial],
      }))
    }
  }

  const handleCloseTutorial = () => {
    setCurrentTutorial(null)
  }

  const handleShowTutorialsLaterToggle = (checked: boolean) => {
    setTutorials((prev) => ({ ...prev, showTutorialsLater: checked }))
  }

  // Render progress bar
  const renderProgressBar = () => {
    const currentIndex = STEPS.indexOf(currentStep)
    const baseProgress = (currentIndex / (STEPS.length - 1)) * 100
    const stepCompletion = calculateStepCompletion()
    const stepWeight = 100 / STEPS.length
    const additionalProgress = (stepCompletion / 100) * stepWeight
    const totalProgress = baseProgress + additionalProgress

    return (
      <div className="w-full max-w-3xl mx-auto px-4 mb-8">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-sm font-medium text-gray-500">
            Step {currentIndex + 1} of {STEPS.length}
          </h2>
          <span className="text-sm font-medium text-gray-500">{Math.round(totalProgress)}% Complete</span>
        </div>

        <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-green-500 transition-all duration-500 ease-in-out"
            style={{ width: `${totalProgress}%` }}
          />
        </div>

        <div className="flex justify-between mt-2">
          {STEPS.map((step, index) => (
            <div
              key={step}
              className={cn(
                "text-xs font-medium transition-colors",
                index <= currentIndex ? "text-green-500" : "text-gray-400",
              )}
            >
              {STEP_LABELS[step]}
            </div>
          ))}
        </div>
      </div>
    )
  }

  // Render step content
  const renderStepContent = () => {
    switch (currentStep) {
      case "welcome":
        return renderWelcomeStep()
      case "business":
        return renderBusinessStep()
      case "goals":
        return renderGoalsStep()
      case "complete":
        return renderCompleteStep()
      default:
        return null
    }
  }

  // Step renderers
  const renderWelcomeStep = () => {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        className="text-center"
      >
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Welcome to Agent47</h1>
        <p className="text-lg text-gray-600 mb-6 max-w-2xl mx-auto">
          We're excited to help you automate your business operations with our AI-powered agents. 
          To provide you with the most effective automation solutions, we'll need some information about your business.
        </p>
        
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8 max-w-2xl mx-auto">
          <div className="flex items-start">
            <Info className="h-5 w-5 text-blue-600 mt-0.5 mr-3 flex-shrink-0" />
            <div className="text-left">
              <h3 className="font-medium text-blue-900 mb-2">How we use your information</h3>
              <p className="text-sm text-blue-800">
                The information you provide will be used exclusively by our AI agents to:
              </p>
              <ul className="text-sm text-blue-800 mt-2 space-y-1">
                <li>• Customize automation strategies for your specific industry and role</li>
                <li>• Generate relevant content and recommendations</li>
                <li>• Optimize workflows based on your business goals</li>
                <li>• Provide personalized insights and analytics</li>
              </ul>
              <p className="text-sm text-blue-800 mt-2">
                Your data is secure and will never be shared with third parties.
              </p>
            </div>
          </div>
        </div>

        <div className="flex justify-center">
          <Button size="lg" onClick={goToNextStep} className="bg-green-500 hover:bg-green-600 text-white px-8 py-3">
            Get Started
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </div>

        <p className="text-sm text-gray-500 mt-4">This will take about 3 minutes to complete.</p>
      </motion.div>
    )
  }

  const renderBusinessStep = () => {
    return (
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Business Information</h1>
        <p className="text-gray-600 mb-6">Tell us about your business to help our agents provide better automation solutions.</p>

        <div className="space-y-6">
          {/* Role Selection */}
          <div>
            <h2 className="text-lg font-medium text-gray-900 mb-3">What best describes your role? *</h2>

            {errors.role && <div className="text-sm text-red-500 mb-2">{errors.role}</div>}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {ROLES.map((role) => (
                <div key={role.value} className="relative">
                  <button
                    type="button"
                    onClick={() => handleRoleChange(role.value)}
                    className={cn(
                      "w-full p-4 text-left rounded-lg border transition-all",
                      profile.role === role.value
                        ? "border-green-500 bg-green-50 ring-2 ring-green-500 ring-opacity-50"
                        : "border-gray-200 hover:border-green-300",
                    )}
                  >
                    <div className="flex items-start">
                      <div
                        className={cn(
                          "w-5 h-5 rounded-full border flex items-center justify-center mr-3 mt-0.5",
                          profile.role === role.value ? "border-green-500 bg-green-500 text-white" : "border-gray-300",
                        )}
                      >
                        {profile.role === role.value && <Check className="w-3 h-3" />}
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-900">{role.label}</h3>
                        <p className="text-sm text-gray-500">{role.description}</p>
                      </div>
                    </div>
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Industry Selection */}
          <div>
            <h2 className="text-lg font-medium text-gray-900 mb-3">What industry are you in? *</h2>

            {errors.industry && <div className="text-sm text-red-500 mb-2">{errors.industry}</div>}

            <Select value={profile.industry} onValueChange={(value) => handleIndustryChange(value as Industry)}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select your industry" />
              </SelectTrigger>
              <SelectContent>
                {INDUSTRIES.map((industry) => (
                  <SelectItem key={industry.value} value={industry.value}>
                    {industry.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Business Details */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="business_name">Business Name (Optional)</Label>
              <Input
                id="business_name"
                name="business_name"
                value={profile.business_name}
                onChange={handleProfileInputChange}
                placeholder="e.g., Acme Inc."
                className="mt-1"
              />
            </div>
            <div>
              <Label htmlFor="business_website">Website URL (Optional)</Label>
              <Input
                id="business_website"
                name="business_website"
                value={profile.business_website}
                onChange={handleProfileInputChange}
                placeholder="e.g., https://www.acme.com"
                className="mt-1"
              />
            </div>
            <div>
              <Label htmlFor="business_size">Business Size (Optional)</Label>
              <Select
                value={profile.business_size}
                onValueChange={(value) => handleProfileSelectChange("business_size", value)}
              >
                <SelectTrigger className="w-full mt-1">
                  <SelectValue placeholder="Select your business size" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="solo">Solo Entrepreneur</SelectItem>
                  <SelectItem value="small">Small Business (2-10 employees)</SelectItem>
                  <SelectItem value="medium">Medium Business (11-50 employees)</SelectItem>
                  <SelectItem value="large">Large Business (51-200 employees)</SelectItem>
                  <SelectItem value="enterprise">Enterprise (200+ employees)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="business_stage">Business Stage (Optional)</Label>
              <Select
                value={profile.business_stage}
                onValueChange={(value) => handleProfileSelectChange("business_stage", value)}
              >
                <SelectTrigger className="w-full mt-1">
                  <SelectValue placeholder="Select your business stage" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="idea">Idea Stage</SelectItem>
                  <SelectItem value="startup">Startup</SelectItem>
                  <SelectItem value="growth">Growth Stage</SelectItem>
                  <SelectItem value="established">Established</SelectItem>
                  <SelectItem value="scaling">Scaling</SelectItem>
                </SelectContent>
              </Select>
            </div>
            </div>
          </div>

        <div className="mt-8 flex justify-between">
          <Button variant="outline" onClick={goToPreviousStep}>
            <ChevronLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
          <Button
            onClick={goToNextStep}
            className="bg-green-500 hover:bg-green-600 text-white px-8 py-3 text-lg"
            disabled={!isCurrentStepComplete()}
          >
            Next
            <ChevronRight className="ml-2 h-5 w-5" />
          </Button>
        </div>
      </motion.div>
    )
  }

  const renderGoalsStep = () => {
    return (
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Your Goals</h1>
        <p className="text-gray-600 mb-6">What do you want to achieve with Agent47? Select your primary goals to help our agents focus on what matters most to you.</p>

        <div className="space-y-6">
          {/* Goals Selection */}
          <div>
            <h2 className="text-lg font-medium text-gray-900 mb-3">What are your main goals? (Select up to 5) *</h2>

            {errors.goals && <div className="text-sm text-red-500 mb-2">{errors.goals}</div>}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {GOALS.map((goal) => {
                const isSelected = profile.goals.includes(goal.value)
                const isDisabled = profile.goals.length >= 5 && !isSelected

                return (
                  <div key={goal.value}>
                    <button
                      type="button"
                      onClick={() => handleGoalToggle(goal.value)}
                      disabled={isDisabled}
                      className={cn(
                        "w-full p-4 text-left rounded-lg border transition-all",
                        isSelected ? "border-green-500 bg-green-50" : "border-gray-200 hover:border-green-300",
                        isDisabled && "opacity-50 cursor-not-allowed hover:border-gray-200",
                      )}
                    >
                      <div className="flex items-start">
                        <div
                          className={cn(
                            "w-10 h-10 rounded-lg flex items-center justify-center mr-3",
                            isSelected ? "bg-green-500 text-white" : "bg-gray-100 text-gray-500",
                          )}
                        >
                          <goal.icon className="w-5 h-5" />
                        </div>
                        <div>
                          <div className="flex items-center">
                            <h3 className="font-medium text-gray-900">{goal.label}</h3>
                            {isSelected && <Check className="w-4 h-4 text-green-500 ml-2" />}
                          </div>
                          <p className="text-sm text-gray-500 mt-1">{goal.description}</p>
                        </div>
                      </div>
                    </button>
                  </div>
                )
              })}
            </div>

            {/* Other Goal Input */}
            {profile.goals.includes("other") && (
              <div className="mt-4">
                <Label htmlFor="otherGoal">Tell us more about your goal</Label>
                <Input
                  id="otherGoal"
                  value={profile.otherGoal}
                  onChange={handleOtherGoalChange}
                  placeholder="e.g., Automate my email marketing"
                  className={cn("mt-1", errors.otherGoal && "border-red-500 focus-visible:ring-red-500")}
                />
                {errors.otherGoal && <div className="text-sm text-red-500 mt-1">{errors.otherGoal}</div>}
              </div>
            )}
          </div>

          {/* Purpose Input */}
          <div>
            <Label htmlFor="purpose">Main Purpose (Optional)</Label>
            <Input
              id="purpose"
              name="purpose"
              value={profile.purpose}
              onChange={handleProfileInputChange}
              placeholder="e.g., To automate marketing tasks and improve customer engagement"
              className="mt-1"
            />
            <p className="text-sm text-gray-500 mt-1">Describe how you plan to use Agent47 in your business.</p>
          </div>
        </div>

        <div className="mt-8 flex justify-between">
          <Button variant="outline" onClick={goToPreviousStep}>
            <ChevronLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
          <Button
            onClick={goToNextStep}
            className="bg-green-500 hover:bg-green-600 text-white px-8 py-3 text-lg"
            disabled={!isCurrentStepComplete()}
          >
            Next
            <ChevronRight className="ml-2 h-5 w-5" />
          </Button>
        </div>
      </motion.div>
    )
  }

  const renderCompleteStep = () => {
    return (
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}>
        <div className="text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <Check className="w-8 h-8 text-green-600" />
          </div>
          
        <h1 className="text-2xl font-bold text-gray-900 mb-2">You're All Set!</h1>
          <p className="text-gray-600 mb-8 max-w-2xl mx-auto">
            Thank you for providing your business information. Our AI agents now have everything they need to help automate your workflows and provide personalized solutions.
          </p>

          <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-8 max-w-2xl mx-auto">
            <h3 className="font-medium text-green-900 mb-3">What happens next?</h3>
            <ul className="text-sm text-green-800 space-y-2 text-left">
              <li>• Your profile has been saved and our agents are ready to assist you</li>
              <li>• You'll be redirected to choose your subscription plan</li>
              <li>• Once subscribed, you can start using all 7 AI agents immediately</li>
              <li>• Our agents will use your information to provide tailored automation strategies</li>
            </ul>
                    </div>

          <Button onClick={completeOnboarding} className="bg-green-500 hover:bg-green-600 text-white px-8 py-3 text-lg">
            {isLoading ? (
              <div className="flex items-center">
                <div className="animate-spin mr-2 h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                Completing...
              </div>
            ) : (
              <>
                Complete Setup
                <ArrowRight className="ml-2 h-5 w-5" />
              </>
            )}
          </Button>
        </div>
      </motion.div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex flex-col">
      {/* Header */}
      <header className={cn("sticky top-0 h-16 bg-white z-50 transition-shadow", isScrolled ? "shadow-sm" : "")}>
        <div className="container mx-auto px-4 h-full flex items-center justify-between">
          <Link href="/" className="flex items-center">
            <span className="text-slate-900 font-extrabold text-2xl">
              Agent<span className="text-green-500">47</span>
            </span>
          </Link>

          <Button variant="ghost" size="sm" onClick={skipOnboarding} disabled={isLoading} className="text-gray-600">
            {isLoading ? "Skipping..." : "Skip"}
          </Button>
        </div>
      </header>

      {/* Progress Bar */}
      <div className="pt-6 pb-4">{renderProgressBar()}</div>

      {/* Main Content */}
      <main className="container mx-auto px-4 pb-20 flex-grow">
        <Card className="max-w-3xl mx-auto">
          <CardContent className="pt-6">
            <AnimatePresence mode="wait">{renderStepContent()}</AnimatePresence>
          </CardContent>
        </Card>
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-white py-3 text-sm text-center">Powered by Nexonic Industries</footer>
    </div>
  )
}
