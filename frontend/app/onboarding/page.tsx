"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useAuthStore } from "@/lib/stores/auth-store"
import {
  FileText,
  BarChart3,
  DollarSign,
  ChevronLeft,
  ChevronRight,
  Check,
  ArrowRight,
  Zap,
  Users,
  Target,
  Headphones
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

// Types
type Step = "welcome" | "personal" | "business" | "brand" | "strategic" | "complete"

interface ProfileData {
  full_name: string
  role: string
  experience_level: string
  business_name: string
  industry: string
  business_size: string
  business_stage: string
  brand_voice: string
  target_audience: string
  core_values: string
  goals: string[]
  otherGoal?: string
  top_priority: string
  deadline_focus: string
}

// Constants
const STEPS: Step[] = ["welcome", "personal", "business", "brand", "strategic", "complete"]
const STEP_LABELS = {
  welcome: "Start",
  personal: "Personal",
  business: "Business",
  brand: "Brand",
  strategic: "Strategic",
  complete: "Finish",
}

const ROLES = [
  { value: "founder", label: "Founder / Owner", description: "Steering the ship and high-level strategy" },
  { value: "marketing", label: "Marketing Lead", description: "Focusing on growth and brand presence" },
  { value: "operations", label: "Operations Manager", description: "Scaling efficiency and internal systems" },
  { value: "sales", label: "Sales Executive", description: "Driving revenue and client acquisition" },
  { value: "product", label: "Product Manager", description: "Building and refining the core offering" },
  { value: "other", label: "Specialized Professional", description: "Expert in a specific niche" },
]

const INDUSTRIES = [
  { value: "ecom", label: "E-commerce & Retail" },
  { value: "saas", label: "SaaS & Technology" },
  { value: "agency", label: "Agency & Services" },
  { value: "content", label: "Content Creation" },
  { value: "realestate", label: "Real Estate" },
  { value: "healthcare", label: "Health & Wellness" },
  { value: "education", label: "Education" },
  { value: "other", label: "Other Industry" },
]

const GOAL_OPTIONS = [
  { value: "growth", label: "Rapid Growth", description: "Acquire users at scale", icon: Target },
  { value: "automation", label: "Process Automation", description: "Remove repetitive tasks", icon: Zap },
  { value: "content", label: "Content Output", description: "High-quality market presence", icon: FileText },
  { value: "retention", label: "Customer Joy", description: "Automate support & CRM", icon: Headphones },
  { value: "roi", label: "Maximum ROI", description: "Reduce overhead costs", icon: DollarSign },
  { value: "insights", label: "Data Intelligence", description: "Behavioral analytics", icon: BarChart3 },
]

// Default values
const defaultProfile: ProfileData = {
  full_name: "",
  role: "",
  experience_level: "intermediate",
  business_name: "",
  industry: "",
  business_size: "",
  business_stage: "",
  brand_voice: "",
  target_audience: "",
  core_values: "",
  goals: [],
  otherGoal: "",
  top_priority: "",
  deadline_focus: "medium",
}

export default function OnboardingPage() {
  const router = useRouter()
  const [currentStep, setCurrentStep] = useState<Step>("welcome")
  const [profile, setProfile] = useState<ProfileData>(defaultProfile)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [isLoading, setIsLoading] = useState(false)
  const [isScrolled, setIsScrolled] = useState(false)
  const [apiClient, setApiClient] = useState<any>(null)

  // Calculate completion percentage for the current step
  const calculateStepCompletion = (): number => {
    switch (currentStep) {
      case "welcome": return 100
      case "personal":
        let pComp = 0
        if (profile.full_name) pComp += 50
        if (profile.role) pComp += 50
        return Math.min(100, pComp)
      case "business":
        let bComp = 0
        if (profile.business_name) bComp += 50
        if (profile.industry) bComp += 50
        return Math.min(100, bComp)
      case "brand":
        let rComp = 0
        if (profile.brand_voice) rComp += 50
        if (profile.target_audience) rComp += 50
        return Math.min(100, rComp)
      case "strategic":
        let sComp = 0
        if (profile.goals.length > 0) sComp += 50
        if (profile.top_priority) sComp += 50
        return Math.min(100, sComp)
      case "complete": return 100
      default: return 0
    }
  }

  // Check if the current step is complete
  const isCurrentStepComplete = (): boolean => {
    switch (currentStep) {
      case "welcome": return true
      case "personal": return !!profile.full_name && !!profile.role
      case "business": return !!profile.business_name && !!profile.industry
      case "brand": return !!profile.brand_voice && !!profile.target_audience
      case "strategic": return profile.goals.length > 0 && !!profile.top_priority
      case "complete": return true
      default: return false
    }
  }

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 10)
    window.addEventListener("scroll", handleScroll)
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  useEffect(() => {
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
      completeOnboarding()
    }
  }

  const goToPreviousStep = () => {
    const currentIndex = STEPS.indexOf(currentStep)
    if (currentIndex > 0) {
      goToStep(STEPS[currentIndex - 1])
    }
  }

  const skipOnboarding = () => {
    setIsLoading(true)
    setTimeout(() => router.push("/pricing"), 300)
  }

  const completeOnboarding = async () => {
    setIsLoading(true)
    try {
      const { user, isAuthenticated, refreshUser } = useAuthStore.getState()
      const onboardingPayload = {
        profile: {
          ...profile,
          email: user?.email || '',
          username: user?.username || '',
        }
      }

      localStorage.setItem('onboarding-data', JSON.stringify(onboardingPayload))

      if (isAuthenticated && apiClient) {
        try {
          await apiClient.saveOnboardingData(onboardingPayload)
          await refreshUser()
        } catch (apiError) {
          console.error("Failed to save to backend:", apiError)
        }
      }

      router.push("/pricing")
    } catch (error) {
      console.error("Failed to complete onboarding:", error)
      router.push("/pricing")
    } finally {
      setIsLoading(false)
    }
  }

  const validateCurrentStep = (): boolean => {
    const newErrors: Record<string, string> = {}
    switch (currentStep) {
      case "personal":
        if (!profile.full_name) newErrors.full_name = "Full name is required"
        if (!profile.role) newErrors.role = "Please select your role"
        break
      case "business":
        if (!profile.business_name) newErrors.business_name = "Business name is required"
        if (!profile.industry) newErrors.industry = "Please select your industry"
        break
      case "brand":
        if (!profile.brand_voice) newErrors.brand_voice = "Please describe your brand voice"
        if (!profile.target_audience) newErrors.target_audience = "Please describe your audience"
        break
      case "strategic":
        if (profile.goals.length === 0) newErrors.goals = "Select at least one goal"
        if (!profile.top_priority) newErrors.top_priority = "Define your top priority"
        break
    }
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setProfile(prev => ({ ...prev, [name]: value }))
    if (errors[name]) setErrors(prev => {
      const { [name]: _, ...rest } = prev
      return rest
    })
  }

  const handleSelect = (name: string, value: string) => {
    setProfile(prev => ({ ...prev, [name]: value }))
    if (errors[name]) setErrors(prev => {
      const { [name]: _, ...rest } = prev
      return rest
    })
  }

  const toggleGoal = (goal: string) => {
    setProfile(prev => ({
      ...prev,
      goals: prev.goals.includes(goal)
        ? prev.goals.filter(g => g !== goal)
        : [...prev.goals, goal]
    }))
    if (errors.goals) setErrors(prev => {
      const { goals: _, ...rest } = prev
      return rest
    })
  }

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
          <h2 className="text-sm font-medium text-slate-500 uppercase tracking-widest">
            PHASE {currentIndex + 1}
          </h2>
          <span className="text-sm font-bold text-slate-900">{Math.round(totalProgress)}%</span>
        </div>

        <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden border border-slate-200">
          <div
            className="h-full bg-green-500 transition-all duration-500 ease-in-out shadow-[0_0_15px_rgba(34,197,94,0.4)]"
            style={{ width: `${totalProgress}%` }}
          />
        </div>

        <div className="hidden md:flex justify-between mt-3 px-1">
          {STEPS.map((step, index) => (
            <div
              key={step}
              className={cn(
                "text-[10px] font-black uppercase tracking-widest transition-colors",
                index <= currentIndex ? "text-green-600" : "text-slate-300",
              )}
            >
              {STEP_LABELS[step]}
            </div>
          ))}
        </div>
      </div>
    )
  }

  const renderStepContent = () => {
    switch (currentStep) {
      case "welcome": return renderWelcomeStep()
      case "personal": return renderPersonalStep()
      case "business": return renderBusinessStep()
      case "brand": return renderBrandStep()
      case "strategic": return renderStrategicStep()
      case "complete": return renderCompleteStep()
      default: return null
    }
  }

  const renderWelcomeStep = () => {
    return (
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} className="text-center py-6">
        <div className="inline-block px-4 py-1 bg-green-100 text-green-700 rounded-full text-[10px] font-black tracking-widest mb-6 uppercase">
          Onboarding Protocol v2.0
        </div>
        <h1 className="text-5xl font-black text-slate-900 mb-6 tracking-tight leading-[1.1]">The AI Briefing</h1>
        <p className="text-xl text-slate-500 mb-12 max-w-2xl mx-auto leading-relaxed font-medium">
          In 3 minutes, we'll brief your new 24/7 AI workforce on your brand identity and strategic objectives.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
          <div className="p-8 bg-slate-50/50 rounded-3xl border border-slate-100 transition-all hover:shadow-xl hover:-translate-y-1">
            <Users className="h-12 w-12 text-green-500 mx-auto mb-6" />
            <h3 className="font-black text-slate-900 mb-3 text-lg uppercase tracking-tight">Identity</h3>
            <p className="text-sm text-slate-500 leading-relaxed">Customize tone and audience targeting.</p>
          </div>
          <div className="p-8 bg-slate-50/50 rounded-3xl border border-slate-100 transition-all hover:shadow-xl hover:-translate-y-1">
            <Target className="h-12 w-12 text-green-500 mx-auto mb-6" />
            <h3 className="font-black text-slate-900 mb-3 text-lg uppercase tracking-tight">Strategy</h3>
            <p className="text-sm text-slate-500 leading-relaxed">Set key objectives and measurable KPIs.</p>
          </div>
          <div className="p-8 bg-slate-50/50 rounded-3xl border border-slate-100 transition-all hover:shadow-xl hover:-translate-y-1">
            <Zap className="h-12 w-12 text-green-500 mx-auto mb-6" />
            <h3 className="font-black text-slate-900 mb-3 text-lg uppercase tracking-tight">Deploy</h3>
            <p className="text-sm text-slate-500 leading-relaxed">Live in your existing stack instantly.</p>
          </div>
        </div>

        <Button size="lg" onClick={goToNextStep} className="bg-green-500 hover:bg-green-600 text-white px-12 h-20 text-xl rounded-full shadow-2xl hover:shadow-green-200/50 transition-all font-black group">
          START BRIEFING
          <ArrowRight className="ml-3 h-6 w-6 group-hover:translate-x-2 transition-transform" />
        </Button>
      </motion.div>
    )
  }

  const renderPersonalStep = () => {
    return (
      <motion.div initial={{ opacity: 0, x: 50 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -50 }} className="py-2">
        <h2 className="text-4xl font-black text-slate-900 mb-2 tracking-tight uppercase">Leader Profile</h2>
        <p className="text-slate-500 mb-12 font-medium">Who will your AI employees be reporting to?</p>

        <div className="space-y-10">
          <div className="group">
            <Label className="text-slate-900 font-black mb-4 block text-xs uppercase tracking-widest group-focus-within:text-green-600 transition-colors">Admin Full Name</Label>
            <Input
              name="full_name"
              value={profile.full_name}
              onChange={handleChange}
              placeholder="e.g. John Doe"
              className={cn("h-16 text-xl bg-slate-50/50 border-0 border-b-4 rounded-none focus:border-green-500 transition-all px-0", errors.full_name ? "border-red-500" : "border-slate-100")}
            />
            {errors.full_name && <p className="text-red-500 text-xs mt-3 font-bold uppercase tracking-tighter">{errors.full_name}</p>}
          </div>

          <div>
            <Label className="text-slate-900 font-black mb-6 block text-xs uppercase tracking-widest">Primary Leadership Role</Label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {ROLES.map(role => (
                <button
                  key={role.value}
                  onClick={() => handleSelect('role', role.value)}
                  className={cn(
                    "p-6 text-left rounded-3xl border-2 transition-all relative group",
                    profile.role === role.value
                      ? "border-green-500 bg-green-50/50"
                      : "border-slate-100 hover:border-slate-300 bg-slate-50/30"
                  )}
                >
                  <p className="font-black text-slate-900 mb-1 uppercase tracking-tight text-sm">{role.label}</p>
                  <p className="text-[10px] text-slate-400 font-bold leading-normal uppercase">{role.description}</p>
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-16 flex justify-between items-center">
          <Button variant="ghost" onClick={goToPreviousStep} className="font-black text-[10px] uppercase tracking-widest text-slate-400 hover:text-slate-900">
            <ChevronLeft className="mr-2 h-4 w-4" />
            Previous
          </Button>
          <Button onClick={goToNextStep} className="bg-slate-900 hover:bg-slate-800 text-white px-10 h-16 rounded-full font-black uppercase tracking-widest shadow-xl" disabled={!isCurrentStepComplete()}>
            Next Phase
            <ChevronRight className="ml-2 h-4 w-4" />
          </Button>
        </div>
      </motion.div>
    )
  }

  const renderBusinessStep = () => {
    return (
      <motion.div initial={{ opacity: 0, x: 50 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -50 }} className="py-2">
        <h2 className="text-4xl font-black text-slate-900 mb-2 tracking-tight uppercase">Corporate Intel</h2>
        <p className="text-slate-500 mb-12 font-medium">Domain and structural parameters.</p>

        <div className="space-y-10">
          <div className="group">
            <Label className="text-slate-900 font-black mb-4 block text-xs uppercase tracking-widest">Registered Business Name</Label>
            <Input
              name="business_name"
              value={profile.business_name}
              onChange={handleChange}
              placeholder="e.g. Acme Industries"
              className={cn("h-16 text-xl bg-slate-50/50 border-0 border-b-4 rounded-none focus:border-green-500 transition-all px-0", errors.business_name ? "border-red-500" : "border-slate-100")}
            />
            {errors.business_name && <p className="text-red-500 text-xs mt-3 font-bold uppercase tracking-tighter">{errors.business_name}</p>}
          </div>

          <div>
            <Label className="text-slate-900 font-black mb-4 block text-xs uppercase tracking-widest">Industry Classification</Label>
            <Select value={profile.industry} onValueChange={(v: string) => handleSelect('industry', v)}>
              <SelectTrigger className="h-16 text-lg border-2 border-slate-100 bg-slate-50/50 rounded-3xl px-6 font-bold">
                <SelectValue placeholder="Select industry" />
              </SelectTrigger>
              <SelectContent>
                {INDUSTRIES.map(ind => (
                  <SelectItem key={ind.value} value={ind.value} className="font-bold">{ind.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <Label className="text-slate-900 font-black mb-4 block text-xs uppercase tracking-widest">Workforce Size</Label>
              <Select value={profile.business_size} onValueChange={(v: string) => handleSelect('business_size', v)}>
                <SelectTrigger className="h-16 border-2 border-slate-100 bg-slate-50/50 rounded-3xl px-6 font-bold">
                  <SelectValue placeholder="Personnel" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="solo" className="font-bold">Solo (1)</SelectItem>
                  <SelectItem value="small" className="font-bold">Boutique (2-10)</SelectItem>
                  <SelectItem value="medium" className="font-bold">Growth (11-50)</SelectItem>
                  <SelectItem value="large" className="font-bold">Enterprise (50+)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-slate-900 font-black mb-4 block text-xs uppercase tracking-widest">Market Stage</Label>
              <Select value={profile.business_stage} onValueChange={(v: string) => handleSelect('business_stage', v)}>
                <SelectTrigger className="h-16 border-2 border-slate-100 bg-slate-50/50 rounded-3xl px-6 font-bold">
                  <SelectValue placeholder="Revenue status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="launch" className="font-bold">Stealth / Launch</SelectItem>
                  <SelectItem value="growth" className="font-bold">Revenue Generating</SelectItem>
                  <SelectItem value="scale" className="font-bold">Scaling Ops</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        <div className="mt-16 flex justify-between items-center">
          <Button variant="ghost" onClick={goToPreviousStep} className="font-black text-[10px] uppercase tracking-widest text-slate-400 hover:text-slate-900">
            <ChevronLeft className="mr-2 h-4 w-4" />
            Previous
          </Button>
          <Button onClick={goToNextStep} className="bg-slate-900 hover:bg-slate-800 text-white px-10 h-16 rounded-full font-black uppercase tracking-widest shadow-xl" disabled={!isCurrentStepComplete()}>
            Next Phase
            <ChevronRight className="ml-2 h-4 w-4" />
          </Button>
        </div>
      </motion.div>
    )
  }

  const renderBrandStep = () => {
    return (
      <motion.div initial={{ opacity: 0, x: 50 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -50 }} className="py-2">
        <h2 className="text-4xl font-black text-slate-900 mb-2 tracking-tight uppercase">Voice Matrix</h2>
        <p className="text-slate-500 mb-12 font-medium">Calibrate employee communication style.</p>

        <div className="space-y-10">
          <div>
            <Label className="text-slate-900 font-black mb-4 block text-xs uppercase tracking-widest">Brand Tone & Persona</Label>
            <textarea
              name="brand_voice"
              value={profile.brand_voice}
              onChange={handleChange as any}
              placeholder="e.g. Aggressive marketing tone, clinical technical precision, or empathetic support..."
              className={cn("w-full min-h-[140px] p-6 text-lg bg-slate-50/50 border-2 rounded-3xl focus:bg-white focus:border-green-500 focus:ring-4 focus:ring-green-500/10 transition-all outline-none resize-none font-medium", errors.brand_voice ? "border-red-500" : "border-slate-100")}
            />
            {errors.brand_voice && <p className="text-red-500 text-xs mt-3 font-bold uppercase tracking-tighter">{errors.brand_voice}</p>}
          </div>

          <div>
            <Label className="text-slate-900 font-black mb-4 block text-xs uppercase tracking-widest">Target Demographic</Label>
            <Input
              name="target_audience"
              value={profile.target_audience}
              onChange={handleChange}
              placeholder="e.g. High-net-worth investors, or millennial houseplant owners"
              className={cn("h-16 text-xl bg-slate-50/50 border-0 border-b-4 rounded-none focus:border-green-500 transition-all px-0", errors.target_audience ? "border-red-500" : "border-slate-100")}
            />
            {errors.target_audience && <p className="text-red-500 text-xs mt-3 font-bold uppercase tracking-tighter">{errors.target_audience}</p>}
          </div>

          <div>
            <Label className="text-slate-900 font-black mb-4 block text-xs uppercase tracking-widest">Company Core Values</Label>
            <Input
              name="core_values"
              value={profile.core_values}
              onChange={handleChange}
              placeholder="e.g. Radical Transparency, Absolute Speed"
              className="h-16 text-lg border-2 border-slate-100 bg-slate-50/50 rounded-3xl px-6 font-bold transition-all"
            />
          </div>
        </div>

        <div className="mt-16 flex justify-between items-center">
          <Button variant="ghost" onClick={goToPreviousStep} className="font-black text-[10px] uppercase tracking-widest text-slate-400 hover:text-slate-900">
            <ChevronLeft className="mr-2 h-4 w-4" />
            Previous
          </Button>
          <Button onClick={goToNextStep} className="bg-slate-900 hover:bg-slate-800 text-white px-10 h-16 rounded-full font-black uppercase tracking-widest shadow-xl" disabled={!isCurrentStepComplete()}>
            Next Phase
            <ChevronRight className="ml-2 h-4 w-4" />
          </Button>
        </div>
      </motion.div>
    )
  }

  const renderStrategicStep = () => {
    return (
      <motion.div initial={{ opacity: 0, x: 50 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -50 }} className="py-2">
        <h2 className="text-4xl font-black text-slate-900 mb-2 tracking-tight uppercase">Mission Brief</h2>
        <p className="text-slate-500 mb-12 font-medium">Strategic priorities for your AI team.</p>

        <div className="space-y-10">
          <div>
            <Label className="text-slate-900 font-black mb-6 block text-xs uppercase tracking-widest font-black">Strategic Objectives</Label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {GOAL_OPTIONS.map(goal => (
                <button
                  key={goal.value}
                  onClick={() => toggleGoal(goal.value)}
                  className={cn(
                    "p-6 text-left rounded-3xl border-2 transition-all flex items-start space-x-4",
                    profile.goals.includes(goal.value)
                      ? "border-green-500 bg-green-50/50"
                      : "border-slate-100 hover:border-slate-300 bg-slate-50/30"
                  )}
                >
                  <div className={cn("p-2 rounded-xl mt-1", profile.goals.includes(goal.value) ? "bg-green-500 text-white" : "bg-white text-slate-300 border shadow-sm")}>
                    <goal.icon className="h-5 w-5" />
                  </div>
                  <div>
                    <h4 className="font-black text-slate-900 uppercase tracking-tight text-sm">{goal.label}</h4>
                    <p className="text-[10px] text-slate-400 font-bold leading-tight uppercase mt-1">{goal.description}</p>
                  </div>
                </button>
              ))}
            </div>
            {errors.goals && <p className="text-red-500 text-xs mt-3 font-bold uppercase tracking-tighter">{errors.goals}</p>}
          </div>

          <div>
            <Label className="text-slate-900 font-black mb-4 block text-xs uppercase tracking-widest">Immediate Critical Priority</Label>
            <Input
              name="top_priority"
              value={profile.top_priority}
              onChange={handleChange}
              placeholder="e.g. Slash support ticket volume by 40%"
              className={cn("h-16 text-xl bg-slate-50/50 border-0 border-b-4 rounded-none focus:border-green-500 transition-all px-0 font-medium", errors.top_priority ? "border-red-500" : "border-slate-100")}
            />
            {errors.top_priority && <p className="text-red-500 text-xs mt-3 font-bold uppercase tracking-tighter">{errors.top_priority}</p>}
          </div>
        </div>

        <div className="mt-16 flex justify-between items-center">
          <Button variant="ghost" onClick={goToPreviousStep} className="font-black text-[10px] uppercase tracking-widest text-slate-400 hover:text-slate-900">
            <ChevronLeft className="mr-2 h-4 w-4" />
            Previous
          </Button>
          <Button onClick={goToNextStep} className="bg-slate-900 hover:bg-slate-800 text-white px-10 h-16 rounded-full font-black uppercase tracking-widest shadow-xl" disabled={!isCurrentStepComplete()}>
            Finalize Brief
            <Check className="ml-3 h-5 w-5" />
          </Button>
        </div>
      </motion.div>
    )
  }

  const renderCompleteStep = () => {
    return (
      <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="text-center py-10">
        <div className="mb-12 relative flex justify-center">
          <div className="w-28 h-28 bg-green-500 rounded-full flex items-center justify-center relative z-10 shadow-2xl">
            <Check className="w-14 h-14 text-white" />
          </div>
          <motion.div
            initial={{ scale: 0.5, opacity: 0 }}
            animate={{ scale: 1.8, opacity: 0 }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeOut" }}
            className="absolute inset-x-0 top-0 mx-auto w-28 h-28 border-4 border-green-500 rounded-full"
          />
        </div>

        <h1 className="text-4xl font-black text-slate-900 mb-4 tracking-tight uppercase">Briefing Logged</h1>
        <p className="text-xl text-slate-500 mb-12 max-w-lg mx-auto leading-relaxed font-medium">
          Strategic profiles have been uploaded to memory banks. Deployment sequence ready.
        </p>

        <div className="bg-slate-900 rounded-[40px] p-10 mb-16 space-y-6 max-w-xl mx-auto text-left shadow-2xl overflow-hidden relative group">
          <div className="absolute top-0 right-0 p-4">
            <div className="h-1 w-20 bg-green-500/20 rounded-full overflow-hidden">
              <motion.div animate={{ x: [-80, 80] }} transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }} className="h-full w-10 bg-green-500" />
            </div>
          </div>
          <div className="flex items-center space-x-5">
            <div className="h-3 w-3 rounded-full bg-green-500 animate-pulse" />
            <p className="text-xs text-white/70 font-black uppercase tracking-widest">Calibrating ARIA (PR Director)</p>
          </div>
          <div className="flex items-center space-x-5">
            <div className="h-3 w-3 rounded-full bg-green-500 animate-pulse delay-75" />
            <p className="text-xs text-white/70 font-black uppercase tracking-widest">Syncing SHAKES (Creative Lead)</p>
          </div>
          <div className="flex items-center space-x-5">
            <div className="h-3 w-3 rounded-full bg-green-500 animate-pulse delay-150" />
            <p className="text-xs text-white/70 font-black uppercase tracking-widest">Initializing Eric (Sales Core)</p>
          </div>
        </div>

        <Button onClick={completeOnboarding} className="bg-green-500 hover:bg-green-600 text-white px-16 h-20 text-xl font-black rounded-full shadow-2xl hover:shadow-green-200/50 transition-all flex items-center justify-center mx-auto uppercase tracking-widest group">
          {isLoading ? (
            <div className="flex items-center space-x-4">
              <div className="animate-spin h-6 w-6 border-4 border-white border-t-transparent rounded-full" />
              <span>Deploying...</span>
            </div>
          ) : (
            <>
              Deploy Workforce
              <ArrowRight className="ml-3 h-6 w-6 group-hover:translate-x-2 transition-transform" />
            </>
          )}
        </Button>
      </motion.div>
    )
  }

  return (
    <div className="min-h-screen bg-white flex flex-col font-sans selection:bg-green-100 selection:text-green-900">
      {/* Header */}
      <header className={cn("sticky top-0 h-20 bg-white/80 backdrop-blur-xl z-50 transition-all border-b border-transparent px-6", isScrolled ? "border-slate-100 shadow-[0_1px_3px_rgba(0,0,0,0.02)]" : "")}>
        <div className="container mx-auto h-full flex items-center justify-between">
          <Link href="/" className="flex items-center group">
            <span className="text-slate-900 font-black text-3xl tracking-tighter uppercase">
              Agent<span className="text-green-500 group-hover:animate-pulse">47</span>
            </span>
          </Link>

          <Button variant="ghost" size="sm" onClick={skipOnboarding} disabled={isLoading} className="text-slate-400 font-black uppercase tracking-widest text-[10px] hover:text-slate-900 hover:bg-slate-50 rounded-full px-6">
            {isLoading ? "Redirecting..." : "Skip Protocol"}
          </Button>
        </div>
      </header>

      {/* Progress */}
      <div className="pt-10 pb-6">{renderProgressBar()}</div>

      {/* Content */}
      <main className="container mx-auto px-6 pb-24 flex-grow flex items-center justify-center">
        <div className="w-full max-w-4xl bg-white rounded-[60px] border border-slate-50 p-4 md:p-12 shadow-[0_0_100px_rgba(0,0,0,0.02)]">
          <AnimatePresence mode="wait">{renderStepContent()}</AnimatePresence>
        </div>
      </main>

      {/* Security Footer */}
      <footer className="py-8 bg-slate-50">
        <div className="container mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Nexonic Industries Protocol</p>
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-2">
              <div className="h-1.5 w-1.5 rounded-full bg-green-500" />
              <p className="text-[10px] font-black uppercase text-slate-500">Encrypted Channel</p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
