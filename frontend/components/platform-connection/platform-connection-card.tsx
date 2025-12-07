"use client"

import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  CheckCircle, 
  XCircle, 
  Clock, 
  AlertCircle, 
  ExternalLink,
  RefreshCw,
  Trash2,
  Settings
} from 'lucide-react'
import { platformOAuthService, ConnectedPlatform } from '@/lib/services/platform-oauth'
import { cn } from '@/lib/utils'

interface PlatformConnectionCardProps {
  platform: ConnectedPlatform
  onDisconnect: (platformName: string) => void
  onRefresh: (platformName: string) => void
  onReconnect: (platformName: string) => void
}

export function PlatformConnectionCard({ 
  platform, 
  onDisconnect, 
  onRefresh, 
  onReconnect 
}: PlatformConnectionCardProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [showScopes, setShowScopes] = useState(false)

  const platformInfo = platformOAuthService.getPlatformInfo(platform.platform_name)
  const statusColor = platformOAuthService.getStatusColor(platform.status)
  const formattedScopes = platformOAuthService.formatScopes(platform.scopes)

  const handleDisconnect = async () => {
    setIsLoading(true)
    try {
      await onDisconnect(platform.platform_name)
    } finally {
      setIsLoading(false)
    }
  }

  const handleRefresh = async () => {
    setIsLoading(true)
    try {
      await onRefresh(platform.platform_name)
    } finally {
      setIsLoading(false)
    }
  }

  const handleReconnect = async () => {
    setIsLoading(true)
    try {
      await onReconnect(platform.platform_name)
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusIcon = () => {
    switch (platform.status) {
      case 'active':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'expired':
        return <Clock className="h-4 w-4 text-yellow-600" />
      case 'revoked':
        return <XCircle className="h-4 w-4 text-red-600" />
      case 'invalid':
        return <AlertCircle className="h-4 w-4 text-red-600" />
      default:
        return <AlertCircle className="h-4 w-4 text-gray-600" />
    }
  }

  const getStatusText = () => {
    switch (platform.status) {
      case 'active':
        return 'Connected'
      case 'expired':
        return 'Expired'
      case 'revoked':
        return 'Revoked'
      case 'invalid':
        return 'Invalid'
      default:
        return 'Unknown'
    }
  }

  const isConnected = platform.status === 'active' && platform.is_active
  const needsRefresh = platform.status === 'expired'
  const needsReconnect = platform.status === 'revoked' || platform.status === 'invalid'

  return (
    <Card className={cn(
      "transition-all duration-200 hover:shadow-md",
      isConnected ? "border-green-200 bg-green-50/50" : "border-gray-200"
    )}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={cn(
              "flex h-10 w-10 items-center justify-center rounded-lg",
              platformInfo.bgColor
            )}>
              <span className="text-white font-semibold text-sm">
                {platform.display_name?.charAt(0) || platform.platform_name.charAt(0).toUpperCase()}
              </span>
            </div>
            <div>
              <CardTitle className="text-lg">
                {platform.display_name || platform.platform_name}
              </CardTitle>
              <CardDescription className="flex items-center space-x-2">
                {getStatusIcon()}
                <span className={statusColor}>
                  {getStatusText()}
                </span>
                {platform.workspace_name && (
                  <span className="text-gray-500">
                    • {platform.workspace_name}
                  </span>
                )}
              </CardDescription>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {isConnected && (
              <Badge variant="secondary" className="bg-green-100 text-green-800">
                Active
              </Badge>
            )}
            {needsRefresh && (
              <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">
                Needs Refresh
              </Badge>
            )}
            {needsReconnect && (
              <Badge variant="secondary" className="bg-red-100 text-red-800">
                Needs Reconnect
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <div className="space-y-4">
          {/* Platform Features */}
          {platform.supported_features && (
            <div className="flex flex-wrap gap-2">
              {Object.entries(platform.supported_features)
                .filter(([_, supported]) => supported)
                .map(([feature, _]) => (
                  <Badge key={feature} variant="outline" className="text-xs">
                    {feature.charAt(0).toUpperCase() + feature.slice(1)}
                  </Badge>
                ))}
            </div>
          )}

          {/* Scopes */}
          <div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowScopes(!showScopes)}
              className="p-0 h-auto text-sm text-gray-600 hover:text-gray-900"
            >
              {showScopes ? 'Hide' : 'Show'} permissions ({platform.scopes.length})
            </Button>
            {showScopes && (
              <div className="mt-2 space-y-1">
                {formattedScopes.map((scope, index) => (
                  <div key={index} className="text-sm text-gray-600 flex items-center space-x-2">
                    <div className="w-1 h-1 bg-gray-400 rounded-full" />
                    <span>{scope}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Connection Details */}
          <div className="text-sm text-gray-500 space-y-1">
            {platform.last_used && (
              <div>
                Last used: {new Date(platform.last_used).toLocaleDateString()}
              </div>
            )}
            {platform.expires_at && (
              <div>
                Expires: {new Date(platform.expires_at).toLocaleDateString()}
              </div>
            )}
            <div>
              Connected: {new Date(platform.created_at).toLocaleDateString()}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center space-x-2 pt-2">
            {isConnected && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRefresh}
                  disabled={isLoading}
                  className="flex items-center space-x-1"
                >
                  <RefreshCw className={cn("h-3 w-3", isLoading && "animate-spin")} />
                  <span>Refresh</span>
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleDisconnect}
                  disabled={isLoading}
                  className="flex items-center space-x-1 text-red-600 hover:text-red-700 hover:bg-red-50"
                >
                  <Trash2 className="h-3 w-3" />
                  <span>Disconnect</span>
                </Button>
              </>
            )}

            {needsRefresh && (
              <Button
                variant="default"
                size="sm"
                onClick={handleRefresh}
                disabled={isLoading}
                className="flex items-center space-x-1"
              >
                <RefreshCw className={cn("h-3 w-3", isLoading && "animate-spin")} />
                <span>Refresh Tokens</span>
              </Button>
            )}

            {needsReconnect && (
              <Button
                variant="default"
                size="sm"
                onClick={handleReconnect}
                disabled={isLoading}
                className="flex items-center space-x-1"
              >
                <ExternalLink className="h-3 w-3" />
                <span>Reconnect</span>
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
