"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Globe, Twitter, Instagram, Facebook, Linkedin, Plus, AlertCircle } from "lucide-react"

export default function SocialMediaTab() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Social Media Platforms</h1>
          <p className="text-gray-500">Connect and manage your social media accounts</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Globe className="mr-2 h-5 w-5" />
            Connected Platforms
          </CardTitle>
          <CardDescription>No social media platforms connected</CardDescription>
        </CardHeader>
        <CardContent className="text-center py-8">
          <div className="mx-auto w-16 h-16 bg-gray-100  rounded-full flex items-center justify-center mb-4">
            <AlertCircle className="h-8 w-8 text-gray-500" />
          </div>
          <h3 className="text-lg font-medium mb-2">No Platforms Connected</h3>
          <p className="text-sm text-gray-500 mb-6 max-w-md mx-auto">
            Connect your social media platforms to enable Agent47 to manage your social media presence.
          </p>
          <Button className="bg-green-500 hover:bg-green-600">
            <Plus className="mr-2 h-4 w-4" /> Connect Platforms
          </Button>
        </CardContent>
      </Card>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center text-base">
              <Twitter className="mr-2 h-5 w-5 text-[#1DA1F2]" />
              Twitter
            </CardTitle>
          </CardHeader>
          <CardContent className="text-center py-4">
            <p className="text-sm text-gray-500 mb-4">Not connected</p>
            <Button size="sm" variant="outline">
              Connect
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center text-base">
              <Instagram className="mr-2 h-5 w-5 text-[#E1306C]" />
              Instagram
            </CardTitle>
          </CardHeader>
          <CardContent className="text-center py-4">
            <p className="text-sm text-gray-500 mb-4">Not connected</p>
            <Button size="sm" variant="outline">
              Connect
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center text-base">
              <Facebook className="mr-2 h-5 w-5 text-[#1877F2]" />
              Facebook
            </CardTitle>
          </CardHeader>
          <CardContent className="text-center py-4">
            <p className="text-sm text-gray-500 mb-4">Not connected</p>
            <Button size="sm" variant="outline">
              Connect
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center text-base">
              <Linkedin className="mr-2 h-5 w-5 text-[#0A66C2]" />
              LinkedIn
            </CardTitle>
          </CardHeader>
          <CardContent className="text-center py-4">
            <p className="text-sm text-gray-500 mb-4">Not connected</p>
            <Button size="sm" variant="outline">
              Connect
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
