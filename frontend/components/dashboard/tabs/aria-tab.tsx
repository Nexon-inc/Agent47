"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  Twitter,
  Instagram,
  Youtube,
  Facebook,
  TrendingUp,
  Users,
  Eye,
  ChevronDown,
  Bell,
  Plus,
  ImageIcon,
  Video,
  Target,
  Search,
  Zap,
  BarChart3,
  Clock,
  Send,
  Sparkles,
  TrendingDown,
  Play,
  Pause,
  Edit,
  Copy,
  Download,
  Filter,
  RefreshCw,
} from "lucide-react"
import { cn } from "@/lib/utils"

// Mock data
const socialPlatforms = [
  { name: "Twitter", icon: Twitter, followers: "280k", color: "text-blue-400", bgColor: "bg-blue-50", connected: true },
  {
    name: "Instagram",
    icon: Instagram,
    followers: "680k",
    color: "text-pink-500",
    bgColor: "bg-pink-50",
    connected: true,
  },
  { name: "YouTube", icon: Youtube, followers: "2.3M", color: "text-red-500", bgColor: "bg-red-50", connected: true },
  {
    name: "Facebook",
    icon: Facebook,
    followers: "50k",
    color: "text-blue-600",
    bgColor: "bg-blue-50",
    connected: false,
  },
]

const competitors = [
  { name: "TechCorp", followers: "1.2M", engagement: "4.2%", trend: "up" },
  { name: "InnovateLab", followers: "890k", engagement: "3.8%", trend: "down" },
  { name: "FutureWorks", followers: "650k", engagement: "5.1%", trend: "up" },
]

const contentIdeas = [
  {
    type: "Post",
    title: "Behind the scenes: Our development process",
    engagement: "High",
    platforms: ["Instagram", "LinkedIn"],
  },
  {
    type: "Video",
    title: "5 productivity tips for remote teams",
    engagement: "Very High",
    platforms: ["YouTube", "TikTok"],
  },
  {
    type: "Story",
    title: "Quick poll: What's your favorite feature?",
    engagement: "Medium",
    platforms: ["Instagram", "Facebook"],
  },
]

const scheduledPosts = [
  {
    id: 1,
    content: "Excited to announce our new product launch! 🚀",
    platform: "Twitter",
    time: "Today 2:00 PM",
    status: "scheduled",
  },
  {
    id: 2,
    content: "Check out our latest blog post about AI trends",
    platform: "LinkedIn",
    time: "Tomorrow 9:00 AM",
    status: "scheduled",
  },
  {
    id: 3,
    content: "Behind the scenes video coming soon!",
    platform: "Instagram",
    time: "Tomorrow 3:00 PM",
    status: "draft",
  },
]

export default function AriaTab() {
  const [activeTab, setActiveTab] = useState("overview")
  const [postContent, setPostContent] = useState("")
  const [selectedPlatforms, setSelectedPlatforms] = useState([])
  const [campaignName, setCampaignName] = useState("")
  const [adBudget, setAdBudget] = useState("")
  const [isGenerating, setIsGenerating] = useState(false)

  const generateContent = async (type) => {
    setIsGenerating(true)
    // Simulate AI generation
    setTimeout(() => {
      if (type === "post") {
        setPostContent(
          "🚀 Exciting news! We're revolutionizing the way teams collaborate with AI. Our latest update brings intelligent automation to your workflow. What's your biggest productivity challenge? Let us know in the comments! #AI #Productivity #Innovation",
        )
      }
      setIsGenerating(false)
    }, 2000)
  }

  const Calendar = () => {
    const currentDate = new Date()
    const currentMonth = currentDate.getMonth()
    const currentYear = currentDate.getFullYear()
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate()
    const firstDayOfMonth = new Date(currentYear, currentMonth, 1).getDay()

    const monthNames = [
      "January",
      "February",
      "March",
      "April",
      "May",
      "June",
      "July",
      "August",
      "September",
      "October",
      "November",
      "December",
    ]

    const days = []
    for (let i = 0; i < firstDayOfMonth; i++) {
      days.push(<div key={`empty-${i}`} className="w-8 h-8"></div>)
    }

    for (let day = 1; day <= daysInMonth; day++) {
      const isToday = day === currentDate.getDate()
      const hasPost = [5, 12, 18, 25].includes(day)
      days.push(
        <div
          key={day}
          className={cn(
            "w-8 h-8 flex items-center justify-center text-sm rounded-lg cursor-pointer hover:bg-purple-100 relative",
            isToday ? "bg-purple-500 text-white" : "text-gray-700 hover:text-purple-600",
          )}
        >
          {day}
          {hasPost && <div className="absolute -top-1 -right-1 w-2 h-2 bg-green-400 rounded-full"></div>}
        </div>,
      )
    }

    return (
      <div className="bg-white rounded-xl p-4 shadow-sm border">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-800">
            {monthNames[currentMonth]} {currentYear}
          </h3>
          <Button size="sm" variant="outline">
            <Plus className="w-4 h-4 mr-1" />
            Schedule
          </Button>
        </div>
        <div className="grid grid-cols-7 gap-1 mb-2">
          {["S", "M", "T", "W", "T", "F", "S"].map((day) => (
            <div key={day} className="w-8 h-8 flex items-center justify-center text-xs font-medium text-gray-500">
              {day}
            </div>
          ))}
        </div>
        <div className="grid grid-cols-7 gap-1">{days}</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-orange-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl flex items-center justify-center">
              <Users className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Aria - AI Social Media Specialist</h1>
              <p className="text-gray-600">AI-powered content strategy and social media management</p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <span>LAST 15 DAYS</span>
              <ChevronDown className="w-4 h-4" />
            </div>
            <div className="flex items-center space-x-2">
              <Bell className="w-5 h-5 text-gray-400" />
              <Badge variant="destructive" className="text-xs">
                2 NEW UPDATES
              </Badge>
              <Bell className="w-5 h-5 text-gray-400" />
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="mt-6">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full grid-cols-6">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="create">Create</TabsTrigger>
              <TabsTrigger value="schedule">Schedule</TabsTrigger>
              <TabsTrigger value="analytics">Analytics</TabsTrigger>
              <TabsTrigger value="competitors">Competitors</TabsTrigger>
              <TabsTrigger value="campaigns">Campaigns</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
      </div>

      <div className="p-6">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              {/* Main Content */}
              <div className="lg:col-span-3 space-y-6">
                {/* Quick Actions */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <Button
                    className="h-20 flex-col bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600"
                    onClick={() => setActiveTab("create")}
                  >
                    <Sparkles className="w-6 h-6 mb-2" />
                    Generate Post
                  </Button>
                  <Button
                    className="h-20 flex-col bg-gradient-to-r from-green-500 to-teal-500 hover:from-green-600 hover:to-teal-600"
                    onClick={() => setActiveTab("campaigns")}
                  >
                    <Target className="w-6 h-6 mb-2" />
                    Create Ad
                  </Button>
                  <Button
                    className="h-20 flex-col bg-gradient-to-r from-red-500 to-pink-500 hover:from-red-600 hover:to-pink-600"
                    onClick={() => setActiveTab("create")}
                  >
                    <Video className="w-6 h-6 mb-2" />
                    Make Video
                  </Button>
                  <Button
                    className="h-20 flex-col bg-gradient-to-r from-orange-500 to-yellow-500 hover:from-orange-600 hover:to-yellow-600"
                    onClick={() => setActiveTab("analytics")}
                  >
                    <BarChart3 className="w-6 h-6 mb-2" />
                    View Analytics
                  </Button>
                </div>

                {/* Social Platform Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {socialPlatforms.map((platform, index) => (
                    <Card
                      key={index}
                      className="bg-white border-0 shadow-sm hover:shadow-md transition-shadow cursor-pointer"
                    >
                      <CardContent className="p-6 text-center">
                        <div
                          className={cn(
                            "w-12 h-12 rounded-xl flex items-center justify-center mx-auto mb-3",
                            platform.bgColor,
                          )}
                        >
                          <platform.icon className={cn("w-6 h-6", platform.color)} />
                        </div>
                        <div className="text-2xl font-bold text-gray-900 mb-1">{platform.followers}</div>
                        <div className="text-sm text-gray-500 mb-2">{platform.name}</div>
                        <Badge variant={platform.connected ? "default" : "secondary"} className="text-xs">
                          {platform.connected ? "Connected" : "Connect"}
                        </Badge>
                      </CardContent>
                    </Card>
                  ))}
                </div>

                {/* Recent Posts Performance */}
                <Card className="bg-white border-0 shadow-sm">
                  <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle className="text-lg font-semibold">Recent Posts Performance</CardTitle>
                    <Button variant="outline" size="sm">
                      <RefreshCw className="w-4 h-4 mr-2" />
                      Refresh
                    </Button>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {[
                        {
                          content: "Our AI revolution is here! 🚀",
                          platform: "Twitter",
                          likes: 1247,
                          shares: 89,
                          comments: 156,
                          time: "2 hours ago",
                        },
                        {
                          content: "Behind the scenes: How we build...",
                          platform: "Instagram",
                          likes: 2341,
                          shares: 234,
                          comments: 89,
                          time: "5 hours ago",
                        },
                        {
                          content: "5 productivity tips that changed...",
                          platform: "LinkedIn",
                          likes: 892,
                          shares: 156,
                          comments: 67,
                          time: "1 day ago",
                        },
                      ].map((post, index) => (
                        <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                          <div className="flex-1">
                            <p className="font-medium text-gray-900 mb-1">{post.content}</p>
                            <div className="flex items-center space-x-4 text-sm text-gray-500">
                              <span>{post.platform}</span>
                              <span>❤️ {post.likes}</span>
                              <span>🔄 {post.shares}</span>
                              <span>💬 {post.comments}</span>
                              <span>{post.time}</span>
                            </div>
                          </div>
                          <div className="flex space-x-2">
                            <Button size="sm" variant="ghost">
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button size="sm" variant="ghost">
                              <BarChart3 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Right Sidebar */}
              <div className="space-y-6">
                <Calendar />

                {/* Content Ideas */}
                <Card className="bg-white border-0 shadow-sm">
                  <CardHeader>
                    <CardTitle className="text-lg font-semibold flex items-center">
                      <Sparkles className="w-5 h-5 mr-2" />
                      AI Content Ideas
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {contentIdeas.map((idea, index) => (
                      <div key={index} className="p-3 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <Badge variant="outline">{idea.type}</Badge>
                          <Badge
                            variant={
                              idea.engagement === "Very High"
                                ? "default"
                                : idea.engagement === "High"
                                  ? "secondary"
                                  : "outline"
                            }
                          >
                            {idea.engagement}
                          </Badge>
                        </div>
                        <p className="text-sm font-medium text-gray-900 mb-2">{idea.title}</p>
                        <div className="flex flex-wrap gap-1">
                          {idea.platforms.map((platform) => (
                            <Badge key={platform} variant="outline" className="text-xs">
                              {platform}
                            </Badge>
                          ))}
                        </div>
                        <Button size="sm" className="w-full mt-2" onClick={() => setActiveTab("create")}>
                          <Zap className="w-3 h-3 mr-1" />
                          Generate
                        </Button>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>

          {/* Create Tab */}
          <TabsContent value="create" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Sparkles className="w-5 h-5 mr-2" />
                    AI Content Specialist
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Content Type</label>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="Select content type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="post">Social Media Post</SelectItem>
                        <SelectItem value="story">Instagram Story</SelectItem>
                        <SelectItem value="video">Video Script</SelectItem>
                        <SelectItem value="ad">Advertisement</SelectItem>
                        <SelectItem value="thread">Twitter Thread</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Topic/Keywords</label>
                    <Input placeholder="e.g., AI productivity, team collaboration, product launch" />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Tone</label>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="Select tone" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="professional">Professional</SelectItem>
                        <SelectItem value="casual">Casual</SelectItem>
                        <SelectItem value="excited">Excited</SelectItem>
                        <SelectItem value="informative">Informative</SelectItem>
                        <SelectItem value="humorous">Humorous</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Target Platforms</label>
                    <div className="grid grid-cols-2 gap-2">
                      {socialPlatforms.map((platform) => (
                        <Button
                          key={platform.name}
                          variant={selectedPlatforms.includes(platform.name) ? "default" : "outline"}
                          size="sm"
                          onClick={() => {
                            setSelectedPlatforms((prev) =>
                              prev.includes(platform.name)
                                ? prev.filter((p) => p !== platform.name)
                                : [...prev, platform.name],
                            )
                          }}
                        >
                          <platform.icon className="w-4 h-4 mr-2" />
                          {platform.name}
                        </Button>
                      ))}
                    </div>
                  </div>

                  <Button className="w-full" onClick={() => generateContent("post")} disabled={isGenerating}>
                    {isGenerating ? (
                      <>
                        <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4 mr-2" />
                        Generate Content
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Generated Content</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Textarea
                    value={postContent}
                    onChange={(e) => setPostContent(e.target.value)}
                    placeholder="Generated content will appear here..."
                    rows={8}
                  />

                  {postContent && (
                    <div className="space-y-2">
                      <div className="flex space-x-2">
                        <Button size="sm" variant="outline">
                          <Copy className="w-4 h-4 mr-2" />
                          Copy
                        </Button>
                        <Button size="sm" variant="outline">
                          <Edit className="w-4 h-4 mr-2" />
                          Edit
                        </Button>
                        <Button size="sm" variant="outline">
                          <RefreshCw className="w-4 h-4 mr-2" />
                          Regenerate
                        </Button>
                      </div>

                      <div className="flex space-x-2">
                        <Button size="sm" className="flex-1">
                          <Send className="w-4 h-4 mr-2" />
                          Post Now
                        </Button>
                        <Button size="sm" variant="outline" className="flex-1" onClick={() => setActiveTab("schedule")}>
                          <Clock className="w-4 h-4 mr-2" />
                          Schedule
                        </Button>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Image/Video Generation */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <ImageIcon className="w-5 h-5 mr-2" />
                    AI Image Generator
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Input placeholder="Describe the image you want to create..." />
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Image style" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="realistic">Realistic</SelectItem>
                      <SelectItem value="cartoon">Cartoon</SelectItem>
                      <SelectItem value="abstract">Abstract</SelectItem>
                      <SelectItem value="minimalist">Minimalist</SelectItem>
                    </SelectContent>
                  </Select>
                  <Button className="w-full">
                    <ImageIcon className="w-4 h-4 mr-2" />
                    Generate Image
                  </Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Video className="w-5 h-5 mr-2" />
                    Video Script Generator
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Input placeholder="Video topic or theme..." />
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Video length" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="15s">15 seconds (TikTok/Reels)</SelectItem>
                      <SelectItem value="30s">30 seconds</SelectItem>
                      <SelectItem value="60s">1 minute</SelectItem>
                      <SelectItem value="3m">3 minutes</SelectItem>
                    </SelectContent>
                  </Select>
                  <Button className="w-full">
                    <Video className="w-4 h-4 mr-2" />
                    Generate Script
                  </Button>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Schedule Tab */}
          <TabsContent value="schedule" className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold">Content Schedule</h2>
              <Dialog>
                <DialogTrigger asChild>
                  <Button>
                    <Plus className="w-4 h-4 mr-2" />
                    Schedule Post
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Schedule New Post</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4">
                    <Textarea placeholder="What's on your mind?" />
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium mb-2">Date</label>
                        <Input type="date" />
                      </div>
                      <div>
                        <label className="block text-sm font-medium mb-2">Time</label>
                        <Input type="time" />
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">Platforms</label>
                      <div className="grid grid-cols-2 gap-2">
                        {socialPlatforms.map((platform) => (
                          <Button key={platform.name} variant="outline" size="sm">
                            <platform.icon className="w-4 h-4 mr-2" />
                            {platform.name}
                          </Button>
                        ))}
                      </div>
                    </div>
                    <Button className="w-full">Schedule Post</Button>
                  </div>
                </DialogContent>
              </Dialog>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <Card>
                  <CardHeader>
                    <CardTitle>Scheduled Posts</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {scheduledPosts.map((post) => (
                        <div key={post.id} className="flex items-center justify-between p-4 border rounded-lg">
                          <div className="flex-1">
                            <p className="font-medium text-gray-900 mb-1">{post.content}</p>
                            <div className="flex items-center space-x-4 text-sm text-gray-500">
                              <span>{post.platform}</span>
                              <span>{post.time}</span>
                              <Badge variant={post.status === "scheduled" ? "default" : "secondary"}>
                                {post.status}
                              </Badge>
                            </div>
                          </div>
                          <div className="flex space-x-2">
                            <Button size="sm" variant="ghost">
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button size="sm" variant="ghost">
                              <Pause className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>

              <div>
                <Calendar />
              </div>
            </div>
          </TabsContent>

          {/* Analytics Tab */}
          <TabsContent value="analytics" className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold">Analytics Dashboard</h2>
              <div className="flex space-x-2">
                <Button variant="outline" size="sm">
                  <Filter className="w-4 h-4 mr-2" />
                  Filter
                </Button>
                <Button variant="outline" size="sm">
                  <Download className="w-4 h-4 mr-2" />
                  Export
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">Total Reach</p>
                      <p className="text-2xl font-bold">2.4M</p>
                    </div>
                    <TrendingUp className="w-8 h-8 text-green-500" />
                  </div>
                  <p className="text-xs text-green-600 mt-2">+12% from last month</p>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">Engagement Rate</p>
                      <p className="text-2xl font-bold">4.2%</p>
                    </div>
                    <Users className="w-8 h-8 text-blue-500" />
                  </div>
                  <p className="text-xs text-green-600 mt-2">+0.8% from last month</p>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">New Followers</p>
                      <p className="text-2xl font-bold">1,247</p>
                    </div>
                    <Users className="w-8 h-8 text-purple-500" />
                  </div>
                  <p className="text-xs text-green-600 mt-2">+156 this week</p>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">Click-through Rate</p>
                      <p className="text-2xl font-bold">3.8%</p>
                    </div>
                    <Eye className="w-8 h-8 text-orange-500" />
                  </div>
                  <p className="text-xs text-red-600 mt-2">-0.2% from last month</p>
                </CardContent>
              </Card>
            </div>

            {/* Best Performing Posts */}
            <Card>
              <CardHeader>
                <CardTitle>Best Performing Posts</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {[
                    {
                      content: "AI is transforming how we work...",
                      platform: "LinkedIn",
                      engagement: "8.2%",
                      reach: "45.2K",
                    },
                    {
                      content: "Behind the scenes of our latest...",
                      platform: "Instagram",
                      engagement: "6.8%",
                      reach: "32.1K",
                    },
                    {
                      content: "5 productivity hacks that...",
                      platform: "Twitter",
                      engagement: "5.4%",
                      reach: "28.9K",
                    },
                  ].map((post, index) => (
                    <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                      <div className="flex-1">
                        <p className="font-medium text-gray-900 mb-1">{post.content}</p>
                        <p className="text-sm text-gray-500">{post.platform}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-medium text-gray-900">{post.engagement}</p>
                        <p className="text-sm text-gray-500">{post.reach} reach</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Competitors Tab */}
          <TabsContent value="competitors" className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold">Competitor Analysis</h2>
              <Button>
                <Plus className="w-4 h-4 mr-2" />
                Add Competitor
              </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {competitors.map((competitor, index) => (
                <Card key={index}>
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      {competitor.name}
                      <Badge variant={competitor.trend === "up" ? "default" : "destructive"}>
                        {competitor.trend === "up" ? (
                          <TrendingUp className="w-3 h-3" />
                        ) : (
                          <TrendingDown className="w-3 h-3" />
                        )}
                      </Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <p className="text-sm text-gray-600">Followers</p>
                        <p className="text-xl font-bold">{competitor.followers}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Avg. Engagement</p>
                        <p className="text-xl font-bold">{competitor.engagement}</p>
                      </div>
                      <Button variant="outline" className="w-full">
                        <Search className="w-4 h-4 mr-2" />
                        Analyze
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Competitor Insights */}
            <Card>
              <CardHeader>
                <CardTitle>Competitive Insights</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-4 bg-blue-50 rounded-lg">
                    <h4 className="font-medium text-blue-900 mb-2">📈 Trending Content Types</h4>
                    <p className="text-sm text-blue-800">
                      Video content is performing 40% better than static posts across your competitors.
                    </p>
                  </div>
                  <div className="p-4 bg-green-50 rounded-lg">
                    <h4 className="font-medium text-green-900 mb-2">⏰ Optimal Posting Times</h4>
                    <p className="text-sm text-green-800">
                      Your competitors see highest engagement between 2-4 PM on weekdays.
                    </p>
                  </div>
                  <div className="p-4 bg-purple-50 rounded-lg">
                    <h4 className="font-medium text-purple-900 mb-2">🏷️ Popular Hashtags</h4>
                    <p className="text-sm text-purple-800">
                      #Innovation, #TechTrends, and #FutureOfWork are trending in your industry.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Campaigns Tab */}
          <TabsContent value="campaigns" className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold">Ad Campaigns</h2>
              <Dialog>
                <DialogTrigger asChild>
                  <Button>
                    <Plus className="w-4 h-4 mr-2" />
                    Create Campaign
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-2xl">
                  <DialogHeader>
                    <DialogTitle>Create New Ad Campaign</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">Campaign Name</label>
                      <Input
                        placeholder="e.g., Product Launch Q1 2024"
                        value={campaignName}
                        onChange={(e) => setCampaignName(e.target.value)}
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium mb-2">Campaign Objective</label>
                        <Select>
                          <SelectTrigger>
                            <SelectValue placeholder="Select objective" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="awareness">Brand Awareness</SelectItem>
                            <SelectItem value="traffic">Website Traffic</SelectItem>
                            <SelectItem value="leads">Lead Generation</SelectItem>
                            <SelectItem value="sales">Sales</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium mb-2">Budget</label>
                        <Input placeholder="$500" value={adBudget} onChange={(e) => setAdBudget(e.target.value)} />
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">Target Audience</label>
                      <Textarea placeholder="Describe your target audience..." />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">Ad Platforms</label>
                      <div className="grid grid-cols-2 gap-2">
                        {socialPlatforms.map((platform) => (
                          <Button key={platform.name} variant="outline" size="sm">
                            <platform.icon className="w-4 h-4 mr-2" />
                            {platform.name} Ads
                          </Button>
                        ))}
                      </div>
                    </div>
                    <Button className="w-full">
                      <Target className="w-4 h-4 mr-2" />
                      Create Campaign
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>
            </div>

            {/* Active Campaigns */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[
                {
                  name: "Product Launch Q1",
                  status: "Active",
                  budget: "$1,200",
                  spent: "$847",
                  ctr: "3.2%",
                  conversions: 47,
                },
                {
                  name: "Brand Awareness",
                  status: "Active",
                  budget: "$800",
                  spent: "$623",
                  ctr: "2.8%",
                  conversions: 23,
                },
                { name: "Holiday Sale", status: "Paused", budget: "$500", spent: "$500", ctr: "4.1%", conversions: 89 },
              ].map((campaign, index) => (
                <Card key={index}>
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      {campaign.name}
                      <Badge variant={campaign.status === "Active" ? "default" : "secondary"}>{campaign.status}</Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Budget</span>
                        <span className="font-medium">{campaign.budget}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Spent</span>
                        <span className="font-medium">{campaign.spent}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">CTR</span>
                        <span className="font-medium">{campaign.ctr}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Conversions</span>
                        <span className="font-medium">{campaign.conversions}</span>
                      </div>
                      <div className="flex space-x-2 pt-2">
                        <Button size="sm" variant="outline" className="flex-1">
                          <Edit className="w-3 h-3 mr-1" />
                          Edit
                        </Button>
                        <Button size="sm" variant="outline" className="flex-1">
                          {campaign.status === "Active" ? (
                            <Pause className="w-3 h-3 mr-1" />
                          ) : (
                            <Play className="w-3 h-3 mr-1" />
                          )}
                          {campaign.status === "Active" ? "Pause" : "Resume"}
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
