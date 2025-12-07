"use client"

import { useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Loader2, Eye, EyeOff, ExternalLink, Info } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"

interface ApiKeyDialogProps {
  isOpen: boolean
  onClose: () => void
  integration: {
    id: number | string
    name: string
    display_name: string
    description?: string
    authentication_methods?: {
      api_key?: boolean
      api_secret?: boolean
      bearer_token?: boolean
      oauth2?: boolean
    }
    api_documentation_url?: string
  }
  onConnect: (credentials: Record<string, string>) => Promise<void>
  connectionInstructions?: string
}

export default function ApiKeyDialog({
  isOpen,
  onClose,
  integration,
  onConnect,
  connectionInstructions
}: ApiKeyDialogProps) {
  const [apiKey, setApiKey] = useState("")
  const [apiSecret, setApiSecret] = useState("")
  const [bearerToken, setBearerToken] = useState("")
  const [showApiKey, setShowApiKey] = useState(false)
  const [showApiSecret, setShowApiSecret] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const authMethods = integration.authentication_methods || {}
  const needsApiKey = authMethods.api_key
  const needsApiSecret = authMethods.api_secret
  const needsBearerToken = authMethods.bearer_token

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)

    try {
      const credentials: Record<string, string> = {}
      
      if (needsApiKey && apiKey.trim()) {
        credentials.api_key = apiKey.trim()
      }
      if (needsApiSecret && apiSecret.trim()) {
        credentials.api_secret = apiSecret.trim()
      }
      if (needsBearerToken && bearerToken.trim()) {
        credentials.bearer_token = bearerToken.trim()
      }

      // Validate required fields
      if (needsApiKey && !credentials.api_key) {
        setError("API Key is required")
        setIsLoading(false)
        return
      }
      if (needsApiSecret && !credentials.api_secret) {
        setError("API Secret is required")
        setIsLoading(false)
        return
      }
      if (needsBearerToken && !credentials.bearer_token) {
        setError("Bearer Token is required")
        setIsLoading(false)
        return
      }

      await onConnect(credentials)
      
      // Reset form
      setApiKey("")
      setApiSecret("")
      setBearerToken("")
      onClose()
    } catch (err: any) {
      setError(err.message || "Failed to connect integration")
    } finally {
      setIsLoading(false)
    }
  }

  const handleClose = () => {
    if (!isLoading) {
      setApiKey("")
      setApiSecret("")
      setBearerToken("")
      setError(null)
      onClose()
    }
  }

    return (
      <Dialog open={isOpen} onOpenChange={handleClose}>
        <DialogContent className="w-[95vw] sm:max-w-[500px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Connect {integration.display_name}</DialogTitle>
          <DialogDescription>
            {integration.description || `Enter your ${integration.display_name} credentials to connect.`}
          </DialogDescription>
        </DialogHeader>

        {connectionInstructions && (
          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription className="text-sm">
              {connectionInstructions}
            </AlertDescription>
          </Alert>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {needsApiKey && (
            <div className="space-y-2">
              <Label htmlFor="api-key">API Key *</Label>
              <div className="relative">
                <Input
                  id="api-key"
                  type={showApiKey ? "text" : "password"}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Enter your API key"
                  disabled={isLoading}
                  required
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                  onClick={() => setShowApiKey(!showApiKey)}
                  disabled={isLoading}
                >
                  {showApiKey ? (
                    <EyeOff className="h-4 w-4 text-gray-500" />
                  ) : (
                    <Eye className="h-4 w-4 text-gray-500" />
                  )}
                </Button>
              </div>
            </div>
          )}

          {needsApiSecret && (
            <div className="space-y-2">
              <Label htmlFor="api-secret">API Secret *</Label>
              <div className="relative">
                <Input
                  id="api-secret"
                  type={showApiSecret ? "text" : "password"}
                  value={apiSecret}
                  onChange={(e) => setApiSecret(e.target.value)}
                  placeholder="Enter your API secret"
                  disabled={isLoading}
                  required
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                  onClick={() => setShowApiSecret(!showApiSecret)}
                  disabled={isLoading}
                >
                  {showApiSecret ? (
                    <EyeOff className="h-4 w-4 text-gray-500" />
                  ) : (
                    <Eye className="h-4 w-4 text-gray-500" />
                  )}
                </Button>
              </div>
            </div>
          )}

          {needsBearerToken && (
            <div className="space-y-2">
              <Label htmlFor="bearer-token">Bearer Token *</Label>
              <Textarea
                id="bearer-token"
                value={bearerToken}
                onChange={(e) => setBearerToken(e.target.value)}
                placeholder="Enter your bearer token"
                disabled={isLoading}
                required
                rows={3}
              />
            </div>
          )}

          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {integration.api_documentation_url && (
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Info className="h-4 w-4" />
              <span>Need help finding your credentials?</span>
              <a
                href={integration.api_documentation_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-green-600 hover:underline flex items-center gap-1"
              >
                View documentation
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>
          )}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Connecting...
                </>
              ) : (
                "Connect"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

