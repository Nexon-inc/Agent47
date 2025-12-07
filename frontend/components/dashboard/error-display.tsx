"use client"

import { AlertCircle, RefreshCw, AlertTriangle, XCircle, Info } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface ErrorDisplayProps {
  error: Error | string | null
  title?: string
  description?: string
  onRetry?: () => void
  variant?: "default" | "destructive" | "warning" | "info"
  className?: string
}

export default function ErrorDisplay({
  error,
  title,
  description,
  onRetry,
  variant = "destructive",
  className,
}: ErrorDisplayProps) {
  if (!error) return null

  const errorMessage = typeof error === "string" ? error : error?.message || "An error occurred"
  
  const variants = {
    default: {
      icon: AlertCircle,
      bgColor: "bg-gray-50 dark:bg-gray-800",
      borderColor: "border-gray-200 dark:border-gray-700",
      textColor: "text-gray-900 dark:text-white",
      iconColor: "text-gray-500",
    },
    destructive: {
      icon: XCircle,
      bgColor: "bg-red-50 dark:bg-red-900/20",
      borderColor: "border-red-200 dark:border-red-800",
      textColor: "text-red-900 dark:text-red-100",
      iconColor: "text-red-600 dark:text-red-400",
    },
    warning: {
      icon: AlertTriangle,
      bgColor: "bg-yellow-50 dark:bg-yellow-900/20",
      borderColor: "border-yellow-200 dark:border-yellow-800",
      textColor: "text-yellow-900 dark:text-yellow-100",
      iconColor: "text-yellow-600 dark:text-yellow-400",
    },
    info: {
      icon: Info,
      bgColor: "bg-blue-50 dark:bg-blue-900/20",
      borderColor: "border-blue-200 dark:border-blue-800",
      textColor: "text-blue-900 dark:text-blue-100",
      iconColor: "text-blue-600 dark:text-blue-400",
    },
  }

  const variantConfig = variants[variant]
  const Icon = variantConfig.icon

  // Map common error messages to user-friendly text
  const getUserFriendlyMessage = (msg: string): string => {
    const lowerMsg = msg.toLowerCase()
    
    if (lowerMsg.includes("network") || lowerMsg.includes("fetch")) {
      return "Unable to connect to the server. Please check your internet connection."
    }
    if (lowerMsg.includes("404") || lowerMsg.includes("not found")) {
      return "The requested resource was not found."
    }
    if (lowerMsg.includes("403") || lowerMsg.includes("forbidden")) {
      return "You don't have permission to access this resource."
    }
    if (lowerMsg.includes("401") || lowerMsg.includes("unauthorized")) {
      return "Please sign in to access this resource."
    }
    if (lowerMsg.includes("500") || lowerMsg.includes("server error")) {
      return "Something went wrong on our end. Please try again later."
    }
    if (lowerMsg.includes("timeout")) {
      return "The request took too long. Please try again."
    }
    
    return msg
  }

  const friendlyMessage = getUserFriendlyMessage(errorMessage)

  return (
    <Card className={cn("border", variantConfig.borderColor, variantConfig.bgColor, className)}>
      <CardContent className="p-6">
        <div className="flex items-start space-x-4">
          <Icon className={cn("w-6 h-6 flex-shrink-0 mt-0.5", variantConfig.iconColor)} />
          <div className="flex-1 min-w-0">
            <h3 className={cn("text-lg font-semibold mb-1", variantConfig.textColor)}>
              {title || "Error"}
            </h3>
            <p className={cn("text-sm mb-4", variantConfig.textColor)}>
              {description || friendlyMessage}
            </p>
            {onRetry && (
              <Button
                variant="outline"
                size="sm"
                onClick={onRetry}
                className="mt-2"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Try Again
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

