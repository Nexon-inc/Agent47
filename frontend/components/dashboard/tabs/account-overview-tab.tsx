"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Switch } from "@/components/ui/switch"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  User,
  Bell,
  Activity,
  Edit,
  Save,
  X,
  Upload,
  RefreshCw,
  Loader2,
  Settings,
  Bot,
  Crown,
  CheckCircle2,
} from "lucide-react"
import { apiClient } from "@/lib/api-client"
import { useAuthStore } from "@/lib/stores/auth-store"
import { useUserStore } from "@/lib/stores/user-store"
import AgentSelectionModal from "@/components/dashboard/agent-selection-modal"
import { Skeleton } from "@/components/ui/skeleton"

interface AccountData {
  profile: {
    fullName: string
    nickname: string
    company: string
    jobTitle: string
    location: string
    website: string
    timezone: string
    language: string
    bio: string
  }
  business: {
    role: string
    industry: string
    businessName: string
    businessWebsite: string
    businessSize: string
    businessStage: string
    primaryGoals: string[]
    mainPurpose: string
  }
  account: {
    email: string
    status: string
    emailVerified: boolean
    accountCreated: string
    lastLogin: string
    subscriptionTier: string
  }
  preferences: {
    notifications: {
      email: boolean
      push: boolean
      sms: boolean
    }
    privacy: {
      profileVisibility: string
      dataSharing: boolean
    }
  }
}

export default function AccountOverviewTab() {
  const { user, isAuthenticated, refreshUser, forceRefresh } = useAuthStore()
  const { userPlan } = useUserStore()
  const [isLoading, setIsLoading] = useState(true)
  const [isEditing, setIsEditing] = useState(false)
  const [accountData, setAccountData] = useState<AccountData | null>(null)
  const [editedData, setEditedData] = useState<AccountData | null>(null)
  const [lastUpdated, setLastUpdated] = useState<string>("")
  const [selectedAgents, setSelectedAgents] = useState<any[]>([])
  const [showAgentSelection, setShowAgentSelection] = useState(false)
  const [isLoadingAgents, setIsLoadingAgents] = useState(false)
  const [agentsLocked, setAgentsLocked] = useState(false)
  const [lockReason, setLockReason] = useState<string>("")
  const [trialEndDate, setTrialEndDate] = useState<Date | null>(null)

  // Load account data from backend
  const loadAccountData = async () => {
    try {
      setIsLoading(true)
      console.log("Loading account data...")
      
      if (isAuthenticated && user && apiClient) {
        try {
          // Try to get user data from backend
          const userData = await apiClient.getAccountData()
          console.log("Backend account data:", userData)
          
          if (userData) {
            // Handle onboarding_data - it might be null, undefined, empty object, or a proper object
            let onboardingData = userData.onboarding_data
            if (!onboardingData || (typeof onboardingData === 'object' && Object.keys(onboardingData).length === 0)) {
              // If onboarding_data is empty/null, try to construct from user fields
              onboardingData = {
                profile: {
                  full_name: userData.full_name,
                  username: userData.username,
                  email: userData.email,
                  name: userData.full_name || userData.username
                }
              }
            }
            const profileData = onboardingData?.profile || {}
            
            console.log("Raw userData:", userData)
            console.log("Raw onboarding_data:", onboardingData)
            console.log("Profile data:", profileData)
            
            // Transform backend data to match our interface (read from onboarding_data.profile)
            const transformedData: AccountData = {
              profile: {
                fullName: userData.full_name || userData.username || profileData.full_name || profileData.name || "Not set",
                nickname: userData.username || profileData.nickname || profileData.username || "Not set",
                company: profileData.business_name || profileData.company || "Not set",
                jobTitle: profileData.role || "Not set",
                location: profileData.country || profileData.location || "Not set",
                website: profileData.business_website || profileData.website || "https://yourwebsite.com",
                timezone: profileData.timezone || "UTC",
                language: profileData.language || "English",
                bio: profileData.bio || "Tell us about yourself...",
              },
              business: {
                role: profileData.role || "Not set",
                industry: profileData.industry || "Not set",
                businessName: profileData.business_name || profileData.company || "Not set",
                businessWebsite: profileData.business_website || profileData.website || "https://yourbusiness.com",
                businessSize: profileData.business_size || "Not set",
                businessStage: profileData.business_stage || "Not set",
                primaryGoals: Array.isArray(profileData.goals) ? profileData.goals : (profileData.goals ? [profileData.goals] : []),
                mainPurpose: profileData.purpose || "Not set",
              },
              account: {
                email: userData.email || "Not available",
                status: userData.is_active ? "Active" : "Inactive",
                emailVerified: userData.is_verified || false,
                accountCreated: userData.created_at ? new Date(userData.created_at).toLocaleDateString() : "Not available",
                lastLogin: userData.last_login ? new Date(userData.last_login).toLocaleDateString() : "Not available",
                subscriptionTier: userData.tier ? userData.tier.charAt(0).toUpperCase() + userData.tier.slice(1) + " Plan" : "Free Plan",
              },
              preferences: {
                notifications: {
                  email: true,
                  push: true,
                  sms: false,
                },
                privacy: {
                  profileVisibility: "public",
                  dataSharing: true,
                },
              },
            }
            
            setAccountData(transformedData)
            setEditedData(transformedData)
            setLastUpdated(new Date().toLocaleTimeString())
            console.log("Account data loaded successfully:", transformedData)
          } else {
            console.log("No user data in response")
            // Set default data if no backend data
            setDefaultData()
          }
        } catch (error) {
          console.error("Error loading account data from backend:", error)
          // Set default data if backend fails
          setDefaultData()
        }
      } else {
        console.log("User not authenticated or API client not available")
        // Set default data if not authenticated
        setDefaultData()
      }
    } catch (error) {
      console.error("Error in loadAccountData:", error)
      setDefaultData()
    } finally {
      setIsLoading(false)
    }
  }

  // Set default data when backend is not available - use user data from auth store
  const setDefaultData = () => {
    const defaultData: AccountData = {
      profile: {
        fullName: user?.full_name || user?.username || "Not set",
        nickname: user?.username || "Not set",
        company: user?.onboarding_data?.profile?.business_name || "Not set",
        jobTitle: user?.onboarding_data?.profile?.role || "Not set",
        location: user?.onboarding_data?.profile?.country || "Not set",
        website: user?.onboarding_data?.profile?.business_website || "https://yourwebsite.com",
        timezone: "UTC",
        language: "English",
        bio: "Tell us about yourself...",
      },
      business: {
        role: user?.onboarding_data?.profile?.role || "Not set",
        industry: user?.onboarding_data?.profile?.industry || "Not set",
        businessName: user?.onboarding_data?.profile?.business_name || "Not set",
        businessWebsite: user?.onboarding_data?.profile?.business_website || "https://yourbusiness.com",
        businessSize: user?.onboarding_data?.profile?.business_size || "Not set",
        businessStage: user?.onboarding_data?.profile?.business_stage || "Not set",
        primaryGoals: user?.onboarding_data?.profile?.goals || [],
        mainPurpose: user?.onboarding_data?.profile?.purpose || "Not set",
      },
      account: {
        email: user?.email || "Not available",
        status: user?.is_active ? "Active" : "Inactive",
        emailVerified: user?.is_verified || false,
        accountCreated: user?.created_at ? new Date(user.created_at).toLocaleDateString() : "Not available",
        lastLogin: user?.last_login ? new Date(user.last_login).toLocaleDateString() : "Not available",
        subscriptionTier: user?.tier || "Free Plan",
      },
      preferences: {
        notifications: {
          email: true,
          push: true,
          sms: false,
        },
        privacy: {
          profileVisibility: "public",
          dataSharing: true,
        },
      },
    }
    
    setAccountData(defaultData)
    setEditedData(defaultData)
    setLastUpdated(new Date().toLocaleTimeString())
  }

  // Calculate trial end date for free tier users
  const calculateTrialEndDate = () => {
    if (user && userPlan === "free" && user.created_at) {
      const createdDate = new Date(user.created_at)
      const trialEnd = new Date(createdDate)
      trialEnd.setDate(trialEnd.getDate() + 14)
      trialEnd.setHours(23, 59, 59, 999)
      return trialEnd
    }
    return null
  }

  // Check if agents are locked
  const checkAgentsLocked = () => {
    if (!selectedAgents || selectedAgents.length === 0) {
      setAgentsLocked(false)
      return
    }

    // Check if any agent is locked
    const hasLockedAgent = selectedAgents.some((agent: any) => agent.locked === true)
    
    if (hasLockedAgent) {
      setAgentsLocked(true)
      
      // Get lock end date from agent data (if available)
      const lockedAgent = selectedAgents.find((agent: any) => agent.locked === true)
      let lockEndDate: Date | null = null
      
      if (lockedAgent?.lock_end_date) {
        lockEndDate = new Date(lockedAgent.lock_end_date)
        setTrialEndDate(lockEndDate)
      } else {
        const trialEnd = calculateTrialEndDate()
        setTrialEndDate(trialEnd)
        lockEndDate = trialEnd
      }
      
      if (userPlan === "free") {
        if (lockEndDate && new Date() > lockEndDate) {
          setLockReason("Your 14-day free trial has ended. Agents are locked until you upgrade your plan.")
        } else {
          const endDateStr = lockEndDate ? lockEndDate.toLocaleDateString() : "soon"
          setLockReason(`Agents are locked until your trial period ends on ${endDateStr}. Upgrade now to unlock immediately.`)
        }
      } else if (userPlan === "starter" || userPlan === "pro") {
        // Starter/Pro: Monthly lock
        if (lockEndDate) {
          if (new Date() > lockEndDate) {
            setLockReason("Your 1-month lock period has ended. You can now change your agents.")
            setAgentsLocked(false) // Unlock if period has passed
          } else {
            const endDateStr = lockEndDate.toLocaleDateString()
            const maxAgents = userPlan === "starter" ? 4 : 7
            setLockReason(`Agents are locked for 1 month from selection. You selected ${selectedAgents.length} of ${maxAgents} agents. Lock ends on ${endDateStr}.`)
          }
        } else {
          setLockReason("Agents are locked for 1 month from selection date.")
        }
      } else {
        setLockReason("Agents are locked until your subscription period ends. Contact support to change agents.")
      }
    } else {
      setAgentsLocked(false)
      setLockReason("")
    }
  }

  // Load selected agents
  const loadSelectedAgents = async () => {
    try {
      setIsLoadingAgents(true)
      const agents = await apiClient.getSelectedAgents()
      setSelectedAgents(agents || [])
    } catch (error) {
      console.error("Error loading selected agents:", error)
      setSelectedAgents([])
      setAgentsLocked(false)
    } finally {
      setIsLoadingAgents(false)
    }
  }

  // Check lock status whenever selectedAgents or user changes
  useEffect(() => {
    if (selectedAgents.length > 0) {
      checkAgentsLocked()
    } else {
      setAgentsLocked(false)
    }
  }, [selectedAgents, user, userPlan])

  useEffect(() => {
    console.log("Account tab loaded, user:", user, "isAuthenticated:", isAuthenticated)
    loadAccountData()
    loadSelectedAgents()
  }, [user, isAuthenticated])

  // Subscribe to real-time account updates via WebSocket
  useEffect(() => {
    if (!isAuthenticated || !user) return

    const { websocketService } = require('@/lib/websocket-service')
    
    if (!websocketService.getConnectionStatus()) {
      websocketService.connect()
    }

    // Reload account data when profile is updated or notifications arrive
    const unsubscribe = websocketService.subscribe('notification', (message) => {
      if (message.data?.type === 'system_update' || message.data?.type === 'billing_notification') {
        loadAccountData()
      }
    })

    return () => unsubscribe()
  }, [isAuthenticated, user])

  const handleEdit = () => {
    setIsEditing(true)
    setEditedData(accountData)
  }

  const handleCancel = () => {
    setIsEditing(false)
    setEditedData(accountData)
  }

  const handleSaveProfile = async () => {
    try {
      setIsLoading(true)
      
      if (editedData && apiClient && isAuthenticated) {
        try {
          // Save to backend
          const response = await apiClient.updateOnboardingData({
            fullName: editedData.profile.fullName,
            company: editedData.profile.company,
            jobTitle: editedData.profile.jobTitle,
            location: editedData.profile.location,
            website: editedData.profile.website,
            timezone: editedData.profile.timezone,
            language: editedData.profile.language,
            bio: editedData.profile.bio,
            role: editedData.business.role,
            industry: editedData.business.industry,
            businessName: editedData.business.businessName,
            businessWebsite: editedData.business.businessWebsite,
            businessSize: editedData.business.businessSize,
            businessStage: editedData.business.businessStage,
            primaryGoals: editedData.business.primaryGoals,
            mainPurpose: editedData.business.mainPurpose,
          })
          
          console.log("Profile updated successfully:", response)
        } catch (error) {
          console.error("Error updating profile:", error)
        }
      }
      
      setAccountData(editedData)
      setIsEditing(false)
      setLastUpdated(new Date().toLocaleTimeString())
      
    } catch (error) {
      console.error("Error saving profile:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleInputChange = (section: keyof AccountData, field: string, value: any) => {
    if (editedData) {
      setEditedData({
        ...editedData,
        [section]: {
          ...editedData[section],
          [field]: value,
        },
      })
    }
  }

  const handleArrayChange = (section: keyof AccountData, field: string, value: string[]) => {
    if (editedData) {
      setEditedData({
        ...editedData,
        [section]: {
          ...editedData[section],
          [field]: value,
        },
      })
    }
  }

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin" />
          <span className="ml-2">Loading account data...</span>
        </div>
      </div>
    )
  }

  if (!accountData) {
    return (
      <div className="p-6 space-y-6">
        <div className="text-center">
          <p className="text-gray-500">No account data available</p>
          <Button onClick={loadAccountData} className="mt-4">
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Account Settings</h1>
          <p className="text-gray-600">Manage your account preferences and security settings</p>
          <p className="text-sm text-gray-500">Last updated: {lastUpdated}</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadAccountData}
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          {!isEditing && (
            <Button onClick={handleEdit} size="sm">
              <Edit className="h-4 w-4 mr-2" />
              Edit Profile
            </Button>
          )}
        </div>
      </div>

      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="account">Account</TabsTrigger>
          <TabsTrigger value="agents">Agents</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
          <TabsTrigger value="activity">Activity</TabsTrigger>
        </TabsList>

        {/* Profile Tab */}
        <TabsContent value="profile" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <User className="h-5 w-5 mr-2" />
                Profile Information
              </CardTitle>
              <CardDescription>
                Update your personal information and preferences
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {isEditing ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="fullName">Full Name *</Label>
                      <Input
                        id="fullName"
                        value={editedData?.profile.fullName || ""}
                        onChange={(e) => handleInputChange("profile", "fullName", e.target.value)}
                        placeholder="Your full name"
                      />
                    </div>
                    <div>
                      <Label htmlFor="nickname">Nickname/Username</Label>
                      <Input
                        id="nickname"
                        value={editedData?.profile.nickname || ""}
                        onChange={(e) => handleInputChange("profile", "nickname", e.target.value)}
                        placeholder="Your nickname or username"
                      />
                    </div>
                    <div>
                      <Label htmlFor="company">Current Company/Organization</Label>
                      <Input
                        id="company"
                        value={editedData?.profile.company || ""}
                        onChange={(e) => handleInputChange("profile", "company", e.target.value)}
                        placeholder="Your current company or organization"
                      />
                    </div>
                    <div>
                      <Label htmlFor="jobTitle">Job Title</Label>
                      <Input
                        id="jobTitle"
                        value={editedData?.profile.jobTitle || ""}
                        onChange={(e) => handleInputChange("profile", "jobTitle", e.target.value)}
                        placeholder="Your job title"
                      />
                    </div>
                    <div>
                      <Label htmlFor="location">Location</Label>
                      <Input
                        id="location"
                        value={editedData?.profile.location || ""}
                        onChange={(e) => handleInputChange("profile", "location", e.target.value)}
                        placeholder="Your location"
                      />
                    </div>
                    <div>
                      <Label htmlFor="website">Website</Label>
                      <Input
                        id="website"
                        value={editedData?.profile.website || ""}
                        onChange={(e) => handleInputChange("profile", "website", e.target.value)}
                        placeholder="https://yourwebsite.com"
                      />
                    </div>
                    <div>
                      <Label htmlFor="timezone">Timezone</Label>
                      <Select
                        value={editedData?.profile.timezone || "UTC"}
                        onValueChange={(value) => handleInputChange("profile", "timezone", value)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select timezone" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="UTC">UTC</SelectItem>
                          <SelectItem value="EST">Eastern Time</SelectItem>
                          <SelectItem value="PST">Pacific Time</SelectItem>
                          <SelectItem value="GMT">Greenwich Mean Time</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label htmlFor="language">Language</Label>
                      <Select
                        value={editedData?.profile.language || "English"}
                        onValueChange={(value) => handleInputChange("profile", "language", value)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select language" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="English">English</SelectItem>
                          <SelectItem value="Spanish">Spanish</SelectItem>
                          <SelectItem value="French">French</SelectItem>
                          <SelectItem value="German">German</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div>
                    <Label htmlFor="bio">Bio</Label>
                    <Textarea
                      id="bio"
                      value={editedData?.profile.bio || ""}
                      onChange={(e) => handleInputChange("profile", "bio", e.target.value)}
                      placeholder="Tell us about yourself..."
                      rows={3}
                    />
                  </div>
                  <div className="flex justify-end space-x-2">
                    <Button variant="outline" onClick={handleCancel}>
                      <X className="h-4 w-4 mr-2" />
                      Cancel
                    </Button>
                    <Button onClick={handleSaveProfile} disabled={isLoading}>
                      <Save className="h-4 w-4 mr-2" />
                      Save Changes
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label className="text-sm font-medium text-gray-500">Full Name</Label>
                      <p className="text-sm">{accountData.profile.fullName}</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-gray-500">Nickname/Username</Label>
                      <p className="text-sm">{accountData.profile.nickname}</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-gray-500">Current Company/Organization</Label>
                      <p className="text-sm">{accountData.profile.company}</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-gray-500">Job Title</Label>
                      <p className="text-sm">{accountData.profile.jobTitle}</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-gray-500">Location</Label>
                      <p className="text-sm">{accountData.profile.location}</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-gray-500">Website</Label>
                      <p className="text-sm">{accountData.profile.website}</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-gray-500">Timezone</Label>
                      <p className="text-sm">{accountData.profile.timezone}</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-gray-500">Language</Label>
                      <p className="text-sm">{accountData.profile.language}</p>
                    </div>
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-gray-500">Bio</Label>
                    <p className="text-sm">{accountData.profile.bio}</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Business Information</CardTitle>
              <CardDescription>
                Tell us about your business and goals
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {isEditing ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="role">Role *</Label>
                      <Select
                        value={editedData?.business.role || ""}
                        onValueChange={(value) => handleInputChange("business", "role", value)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select your role" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="entrepreneur">Entrepreneur</SelectItem>
                          <SelectItem value="marketer">Marketer</SelectItem>
                          <SelectItem value="developer">Developer</SelectItem>
                          <SelectItem value="designer">Designer</SelectItem>
                          <SelectItem value="manager">Manager</SelectItem>
                          <SelectItem value="other">Other</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label htmlFor="industry">Industry *</Label>
                      <Select
                        value={editedData?.business.industry || ""}
                        onValueChange={(value) => handleInputChange("business", "industry", value)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select your industry" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="technology">Technology</SelectItem>
                          <SelectItem value="healthcare">Healthcare</SelectItem>
                          <SelectItem value="finance">Finance</SelectItem>
                          <SelectItem value="education">Education</SelectItem>
                          <SelectItem value="retail">Retail</SelectItem>
                          <SelectItem value="other">Other</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label htmlFor="businessName">Business Name</Label>
                      <Input
                        id="businessName"
                        value={editedData?.business.businessName || ""}
                        onChange={(e) => handleInputChange("business", "businessName", e.target.value)}
                        placeholder="Your business name"
                      />
                    </div>
                    <div>
                      <Label htmlFor="businessWebsite">Business Website</Label>
                      <Input
                        id="businessWebsite"
                        value={editedData?.business.businessWebsite || ""}
                        onChange={(e) => handleInputChange("business", "businessWebsite", e.target.value)}
                        placeholder="https://yourbusiness.com"
                      />
                    </div>
                    <div>
                      <Label htmlFor="businessSize">Business Size</Label>
                      <Select
                        value={editedData?.business.businessSize || ""}
                        onValueChange={(value) => handleInputChange("business", "businessSize", value)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select business size" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="solo">Solo (Just me)</SelectItem>
                          <SelectItem value="small">Small (2-10 employees)</SelectItem>
                          <SelectItem value="medium">Medium (11-50 employees)</SelectItem>
                          <SelectItem value="large">Large (50+ employees)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label htmlFor="businessStage">Business Stage</Label>
                      <Select
                        value={editedData?.business.businessStage || ""}
                        onValueChange={(value) => handleInputChange("business", "businessStage", value)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select business stage" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="startup">Startup</SelectItem>
                          <SelectItem value="growth">Growth</SelectItem>
                          <SelectItem value="established">Established</SelectItem>
                          <SelectItem value="enterprise">Enterprise</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div>
                    <Label>Primary Goals</Label>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mt-2">
                      {[
                        "Grow My Audience",
                        "Improve Customer Support",
                        "Create Better Content",
                        "Boost Sales",
                        "Optimize Marketing",
                        "Automate Tasks",
                        "Increase Productivity",
                        "Enhance Analytics",
                        "Team Collaboration",
                        "Lead Generation",
                      ].map((goal) => (
                        <div key={goal} className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            id={goal}
                            checked={editedData?.business.primaryGoals.includes(goal) || false}
                            onChange={(e) => {
                              const currentGoals = editedData?.business.primaryGoals || []
                              const newGoals = e.target.checked
                                ? [...currentGoals, goal]
                                : currentGoals.filter((g) => g !== goal)
                              handleArrayChange("business", "primaryGoals", newGoals)
                            }}
                            className="rounded"
                          />
                          <Label htmlFor={goal} className="text-sm">
                            {goal}
                          </Label>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <Label htmlFor="mainPurpose">Main Purpose</Label>
                    <Textarea
                      id="mainPurpose"
                      value={editedData?.business.mainPurpose || ""}
                      onChange={(e) => handleInputChange("business", "mainPurpose", e.target.value)}
                      placeholder="What is your main purpose for using Agent47?"
                      rows={3}
                    />
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label className="text-sm font-medium text-gray-500">Role</Label>
                      <p className="text-sm">{accountData.business.role}</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-gray-500">Industry</Label>
                      <p className="text-sm">{accountData.business.industry}</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-gray-500">Business Name</Label>
                      <p className="text-sm">{accountData.business.businessName}</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-gray-500">Business Website</Label>
                      <p className="text-sm">{accountData.business.businessWebsite}</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-gray-500">Business Size</Label>
                      <p className="text-sm">{accountData.business.businessSize}</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-gray-500">Business Stage</Label>
                      <p className="text-sm">{accountData.business.businessStage}</p>
                    </div>
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-gray-500">Primary Goals</Label>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {accountData.business.primaryGoals.map((goal) => (
                        <Badge key={goal} variant="secondary">
                          {goal}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-gray-500">Main Purpose</Label>
                    <p className="text-sm">{accountData.business.mainPurpose}</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Account Tab */}
        <TabsContent value="account" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Settings className="h-5 w-5 mr-2" />
                Account Information
              </CardTitle>
              <CardDescription>
                View and manage your account details and subscription information
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {isEditing ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="email">Email Address</Label>
                      <Input
                        id="email"
                        type="email"
                        value={user?.email || ""}
                        disabled
                        className="bg-gray-50"
                      />
                      <p className="text-xs text-gray-500 mt-1">Email cannot be changed</p>
                    </div>
                    <div>
                      <Label htmlFor="username">Username</Label>
                      <Input
                        id="username"
                        value={editedData?.profile.nickname || ""}
                        onChange={(e) => handleInputChange("profile", "nickname", e.target.value)}
                        placeholder="Your username"
                      />
                    </div>
                    <div>
                      <Label htmlFor="fullName">Full Name</Label>
                      <Input
                        id="fullName"
                        value={editedData?.profile.fullName || ""}
                        onChange={(e) => handleInputChange("profile", "fullName", e.target.value)}
                        placeholder="Your full name"
                      />
                    </div>
                    <div>
                      <Label htmlFor="subscriptionTier">Subscription Tier</Label>
                      <div className="flex items-center gap-2 mt-2">
                        <Badge variant="outline" className="flex items-center gap-1">
                          {userPlan === "free" && <Crown className="w-3 h-3" />}
                          {userPlan === "starter" && <Crown className="w-3 h-3" />}
                          {userPlan === "pro" && <Crown className="w-3 h-3" />}
                          {userPlan?.toUpperCase() || "FREE"}
                        </Badge>
                        <Button variant="outline" size="sm" onClick={() => window.location.href = "/pricing"}>
                          Upgrade
                        </Button>
                      </div>
                    </div>
                  </div>
                  <div className="flex justify-end space-x-2">
                    <Button variant="outline" onClick={handleCancel}>
                      <X className="h-4 w-4 mr-2" />
                      Cancel
                    </Button>
                    <Button onClick={handleSaveProfile} disabled={isLoading}>
                      <Save className="h-4 w-4 mr-2" />
                      Save Changes
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm font-medium text-gray-500">Email Address</Label>
                    <p className="text-sm">{accountData.account.email}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-gray-500">Username</Label>
                    <p className="text-sm">{accountData.profile.nickname}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-gray-500">Full Name</Label>
                    <p className="text-sm">{accountData.profile.fullName}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-gray-500">Account Status</Label>
                    <Badge variant={accountData.account.status === "Active" ? "default" : "secondary"}>
                      {accountData.account.status}
                    </Badge>
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-gray-500">Email Verified</Label>
                    <Badge variant={accountData.account.emailVerified ? "default" : "destructive"}>
                      {accountData.account.emailVerified ? "Verified" : "Not Verified"}
                    </Badge>
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-gray-500">Account Created</Label>
                    <p className="text-sm">{accountData.account.accountCreated}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-gray-500">Last Login</Label>
                    <p className="text-sm">{accountData.account.lastLogin}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-gray-500">Subscription Tier</Label>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge variant="outline" className="flex items-center gap-1">
                        {userPlan === "free" && <Crown className="w-3 h-3" />}
                        {userPlan === "starter" && <Crown className="w-3 h-3" />}
                        {userPlan === "pro" && <Crown className="w-3 h-3" />}
                        {userPlan?.toUpperCase() || accountData.account.subscriptionTier}
                      </Badge>
                      <Button variant="outline" size="sm" onClick={() => window.location.href = "/pricing"}>
                        Upgrade
                      </Button>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Password Management</CardTitle>
              <CardDescription>
                Update your password and security settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label className="text-sm font-medium text-gray-500">Password</Label>
                <p className="text-sm text-gray-600">Last updated: Never</p>
                <Button variant="outline" size="sm">
                  Change Password
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Agents Tab */}
        <TabsContent value="agents" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Bot className="h-5 w-5 mr-2" />
                Selected Agents
              </CardTitle>
              <CardDescription>
                Manage your selected AI agents based on your {userPlan} plan
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {isLoadingAgents ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin" />
                  <span className="ml-2">Loading agents...</span>
                </div>
              ) : selectedAgents.length > 0 ? (
                <div className="space-y-4">
                  {agentsLocked && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                      <div className="flex items-start gap-3">
                        <Settings className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                        <div className="flex-1">
                          <p className="text-sm font-medium text-yellow-800">Agents Locked</p>
                          <p className="text-sm text-yellow-700 mt-1">{lockReason}</p>
                          {userPlan === "free" && trialEndDate && (
                            <p className="text-xs text-yellow-600 mt-2">
                              {new Date() > trialEndDate 
                                ? "Trial ended. Upgrade to unlock agents."
                                : `Trial ends: ${trialEndDate.toLocaleDateString()}`}
                            </p>
                          )}
                          {(userPlan === "starter" || userPlan === "pro") && trialEndDate && (
                            <p className="text-xs text-yellow-600 mt-2">
                              {new Date() > trialEndDate 
                                ? "Lock period ended. You can now change your agents."
                                : `Lock ends: ${trialEndDate.toLocaleDateString()} (1 month from selection)`}
                            </p>
                          )}
                          {userPlan === "free" && (
                            <Button 
                              onClick={() => window.location.href = "/pricing"} 
                              size="sm" 
                              className="mt-3 bg-yellow-600 hover:bg-yellow-700"
                            >
                              Upgrade Plan
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-gray-600">
                      You have {selectedAgents.length} agent{selectedAgents.length > 1 ? 's' : ''} selected
                    </p>
                    <Button 
                      onClick={() => {
                        if (!agentsLocked) {
                          setShowAgentSelection(true)
                        } else {
                          alert(lockReason + "\n\nUpgrade your plan to unlock agents.")
                        }
                      }} 
                      variant="outline" 
                      size="sm"
                      disabled={agentsLocked}
                      title={agentsLocked ? lockReason : "Change agent selection"}
                    >
                      <Edit className="h-4 w-4 mr-2" />
                      Change Selection
                    </Button>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {selectedAgents.map((agent: any) => (
                      <div
                        key={agent.agent_id}
                        className="border rounded-lg p-4 flex items-center justify-between"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                            <Bot className="w-5 h-5 text-green-600" />
                          </div>
                          <div>
                            <p className="font-medium capitalize">{agent.agent_id}</p>
                            <p className="text-xs text-gray-500">Status: {agent.status}</p>
                            {agent.locked && (
                              <p className="text-xs text-yellow-600 mt-1">🔒 Locked</p>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {agent.status === "active" && (
                            <CheckCircle2 className="w-5 h-5 text-green-500" />
                          )}
                          {agent.locked && (
                            <Settings className="w-4 h-4 text-yellow-600" />
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <Bot className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500 mb-4">No agents selected yet</p>
                  <Button 
                    onClick={() => {
                      if (!agentsLocked) {
                        setShowAgentSelection(true)
                      } else {
                        alert(lockReason)
                      }
                    }}
                    disabled={agentsLocked}
                  >
                    Select Agents
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notifications Tab */}
        <TabsContent value="notifications" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Bell className="h-5 w-5 mr-2" />
                Notification Preferences
              </CardTitle>
              <CardDescription>
                Choose how you want to be notified about updates and activities
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Email Notifications</Label>
                    <p className="text-sm text-gray-500">
                      Receive notifications via email
                    </p>
                  </div>
                  <Switch
                    checked={accountData.preferences.notifications.email}
                    onCheckedChange={(checked) =>
                      handleInputChange("preferences", "notifications", {
                        ...accountData.preferences.notifications,
                        email: checked,
                      })
                    }
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Push Notifications</Label>
                    <p className="text-sm text-gray-500">
                      Receive push notifications in your browser
                    </p>
                  </div>
                  <Switch
                    checked={accountData.preferences.notifications.push}
                    onCheckedChange={(checked) =>
                      handleInputChange("preferences", "notifications", {
                        ...accountData.preferences.notifications,
                        push: checked,
                      })
                    }
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>SMS Notifications</Label>
                    <p className="text-sm text-gray-500">
                      Receive notifications via SMS
                    </p>
                  </div>
                  <Switch
                    checked={accountData.preferences.notifications.sms}
                    onCheckedChange={(checked) =>
                      handleInputChange("preferences", "notifications", {
                        ...accountData.preferences.notifications,
                        sms: checked,
                      })
                    }
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Activity Tab */}
        <TabsContent value="activity" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Activity className="h-5 w-5 mr-2" />
                Account Activity
              </CardTitle>
              <CardDescription>
                View your recent account activity and login history
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8">
                <Activity className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">No recent activity to display</p>
                <p className="text-sm text-gray-400">
                  Your account activity will appear here once you start using the platform
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Agent Selection Modal */}
      <AgentSelectionModal
        isOpen={showAgentSelection && !agentsLocked}
        onClose={() => setShowAgentSelection(false)}
        onConfirm={() => {
          setShowAgentSelection(false)
          loadSelectedAgents()
        }}
      />
    </div>
  )
}