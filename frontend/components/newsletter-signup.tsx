"use client"

import type React from "react"

import { useState } from "react"
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Github, Loader2, Mail, Star, Twitter } from "lucide-react"

export default function NewsletterSignup() {
  const [email, setEmail] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isSuccess, setIsSuccess] = useState(false)
  const [error, setError] = useState("")

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")

    // Basic email validation
    if (!email || !email.includes("@") || !email.includes(".")) {
      setError("Please enter a valid email address")
      return
    }

    setIsLoading(true)

    // Simulate API call
    setTimeout(() => {
      setIsLoading(false)
      setIsSuccess(true)
      setEmail("")
    }, 1500)
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-4 bg-gradient-to-br from-purple-50 to-indigo-50">
      <Card className="w-full max-w-md shadow-lg">
        <CardHeader className="flex flex-col items-center space-y-2 pt-6">
          <div className="h-16 w-16 rounded-full bg-gradient-to-r from-indigo-700 to-blue-500 flex items-center justify-center">
            <Star className="h-8 w-8 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-center">Join Our Newsletter</h2>
          <p className="text-muted-foreground text-center">
            Get the latest updates and exclusive content directly to your inbox.
          </p>
        </CardHeader>
        <CardContent className="space-y-4 pt-4">
          <div className="flex flex-col space-y-2">
            <div className="flex justify-center space-x-4">
              <Button variant="outline" className="flex items-center space-x-2 w-full">
                <Github className="h-5 w-5" />
                <span>GitHub</span>
              </Button>
              <Button variant="outline" className="flex items-center space-x-2 w-full">
                <Twitter className="h-5 w-5" />
                <span>Twitter</span>
              </Button>
            </div>
            <div className="relative flex items-center">
              <div className="flex-grow border-t border-gray-200"></div>
              <span className="mx-4 flex-shrink text-gray-400 text-sm">or continue with</span>
              <div className="flex-grow border-t border-gray-200"></div>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
                <Input
                  type="email"
                  placeholder="Email address"
                  className="pl-10"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={isLoading || isSuccess}
                />
              </div>
              {error && <p className="text-sm text-red-500">{error}</p>}
            </div>
            <Button
              type="submit"
              className="w-full bg-purple-700 hover:bg-purple-800"
              disabled={isLoading || isSuccess}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Subscribing...
                </>
              ) : isSuccess ? (
                "Subscribed!"
              ) : (
                "Subscribe"
              )}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex flex-col items-center border-t px-6 py-4">
          <p className="text-xs text-center text-gray-500">
            We respect your privacy. We'll never share your information.
          </p>
          <div className="mt-2 flex space-x-4">
            <a href="#" className="text-xs text-gray-500 hover:underline">
              Terms
            </a>
            <a href="#" className="text-xs text-gray-500 hover:underline">
              Privacy
            </a>
            <a href="#" className="text-xs text-gray-500 hover:underline">
              Help
            </a>
          </div>
        </CardFooter>
      </Card>
    </div>
  )
}
