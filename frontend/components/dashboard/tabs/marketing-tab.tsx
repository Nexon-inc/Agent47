"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Megaphone, Mail, BarChart2, Plus, AlertCircle } from "lucide-react"

export default function MarketingTab() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Marketing Platforms</h1>
          <p className="text-gray-500">Connect and manage your marketing tools</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Megaphone className="mr-2 h-5 w-5" />
            Connected Marketing Platforms
          </CardTitle>
          <CardDescription>No marketing platforms connected</CardDescription>
        </CardHeader>
        <CardContent className="text-center py-8">
          <div className="mx-auto w-16 h-16 bg-gray-100  rounded-full flex items-center justify-center mb-4">
            <AlertCircle className="h-8 w-8 text-gray-500" />
          </div>
          <h3 className="text-lg font-medium mb-2">No Platforms Connected</h3>
          <p className="text-sm text-gray-500 mb-6 max-w-md mx-auto">
            Connect your marketing platforms to enable Agent47 to optimize your marketing campaigns.
          </p>
          <Button className="bg-green-500 hover:bg-green-600">
            <Plus className="mr-2 h-4 w-4" /> Connect Platforms
          </Button>
        </CardContent>
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Mail className="mr-2 h-5 w-5" />
              Email Marketing
            </CardTitle>
            <CardDescription>No email platforms connected</CardDescription>
          </CardHeader>
          <CardContent className="text-center py-6">
            <p className="text-sm text-gray-500 mb-4">
              Connect your email marketing platforms like Mailchimp, SendGrid, or HubSpot.
            </p>
            <Button className="bg-green-500 hover:bg-green-600">
              <Plus className="mr-2 h-4 w-4" /> Connect Email Platform
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <BarChart2 className="mr-2 h-5 w-5" />
              Analytics Platforms
            </CardTitle>
            <CardDescription>No analytics platforms connected</CardDescription>
          </CardHeader>
          <CardContent className="text-center py-6">
            <p className="text-sm text-gray-500 mb-4">
              Connect your analytics platforms like Google Analytics or Adobe Analytics.
            </p>
            <Button className="bg-green-500 hover:bg-green-600">
              <Plus className="mr-2 h-4 w-4" /> Connect Analytics Platform
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
