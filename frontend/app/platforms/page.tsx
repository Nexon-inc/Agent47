"use client"

import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  Plus, 
  RefreshCw, 
  Settings, 
  AlertCircle,
  CheckCircle,
  ExternalLink,
  Loader2
} from 'lucide-react'
import { PlatformConnectionModal } from '@/components/platform-connection/platform-connection-modal'
import { PlatformConnectionCard } from '@/components/platform-connection/platform-connection-card'
import { platformOAuthService, ConnectedPlatform } from '@/lib/services/platform-oauth'
import { cn } from '@/lib/utils'

export default function PlatformsPage() {
  const [connectedPlatforms, setConnectedPlatforms] = useState<ConnectedPlatform[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isConnecting, setIsConnecting] = useState(false)
  const [showConnectModal, setShowConnectModal] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  useEffect(() => {
    loadConnectedPlatforms()
  }, [])

  const loadConnectedPlatforms = async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      const platforms = await platformOAuthService.getConnectedPlatforms()
      setConnectedPlatforms(platforms)
    } catch (err) {
      setError('Failed to load connected platforms')
      console.error('Error loading platforms:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleConnect = async (platformName: string) => {
    setIsConnecting(true)
    setError(null)
    setSuccessMessage(null)
    
    try {
      const result = await platformOAuthService.initiateConnection(platformName)
      
      if (result.success && result.auth_url) {
        // Redirect to OAuth URL
        platformOAuthService.redirectToOAuth(result.auth_url)
      } else {
        setError(result.error || 'Failed to initiate connection')
      }
    } catch (err) {
      setError('Failed to initiate connection')
      console.error('Error connecting to platform:', err)
    } finally {
      setIsConnecting(false)
    }
  }

  const handleDisconnect = async (platformName: string) => {
    try {
      const result = await platformOAuthService.disconnectPlatform(platformName)
      
      if (result.success) {
        setSuccessMessage(`Successfully disconnected from ${platformName}`)
        await loadConnectedPlatforms()
      } else {
        setError(result.error || 'Failed to disconnect platform')
      }
    } catch (err) {
      setError('Failed to disconnect platform')
      console.error('Error disconnecting platform:', err)
    }
  }

  const handleRefresh = async (platformName: string) => {
    try {
      const result = await platformOAuthService.refreshTokens(platformName)
      
      if (result.success) {
        setSuccessMessage(`Successfully refreshed tokens for ${platformName}`)
        await loadConnectedPlatforms()
      } else {
        setError(result.error || 'Failed to refresh tokens')
      }
    } catch (err) {
      setError('Failed to refresh tokens')
      console.error('Error refreshing tokens:', err)
    }
  }

  const handleReconnect = async (platformName: string) => {
    await handleConnect(platformName)
  }

  const getStats = () => {
    const total = connectedPlatforms.length
    const active = connectedPlatforms.filter(p => p.status === 'active' && p.is_active).length
    const expired = connectedPlatforms.filter(p => p.status === 'expired').length
    const needsAttention = connectedPlatforms.filter(p => 
      p.status === 'revoked' || p.status === 'invalid'
    ).length

    return { total, active, expired, needsAttention }
  }

  const stats = getStats()

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
            <p className="text-gray-600">Loading connected platforms...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Platform Connections</h1>
            <p className="text-gray-600 mt-2">
              Manage your connected platforms and enable AI agents to work with your data.
            </p>
          </div>
          <Button onClick={() => setShowConnectModal(true)} className="flex items-center space-x-2">
            <Plus className="h-4 w-4" />
            <span>Connect Platform</span>
          </Button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <div>
                  <p className="text-sm text-gray-600">Total Connected</p>
                  <p className="text-2xl font-bold">{stats.total}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <div>
                  <p className="text-sm text-gray-600">Active</p>
                  <p className="text-2xl font-bold text-green-600">{stats.active}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <RefreshCw className="h-5 w-5 text-yellow-600" />
                <div>
                  <p className="text-sm text-gray-600">Expired</p>
                  <p className="text-2xl font-bold text-yellow-600">{stats.expired}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <AlertCircle className="h-5 w-5 text-red-600" />
                <div>
                  <p className="text-sm text-gray-600">Need Attention</p>
                  <p className="text-2xl font-bold text-red-600">{stats.needsAttention}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Messages */}
        {error && (
          <div className="flex items-center space-x-2 text-red-600 bg-red-50 p-4 rounded-lg">
            <AlertCircle className="h-5 w-5" />
            <span>{error}</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setError(null)}
              className="ml-auto"
            >
              ×
            </Button>
          </div>
        )}

        {successMessage && (
          <div className="flex items-center space-x-2 text-green-600 bg-green-50 p-4 rounded-lg">
            <CheckCircle className="h-5 w-5" />
            <span>{successMessage}</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSuccessMessage(null)}
              className="ml-auto"
            >
              ×
            </Button>
          </div>
        )}

        {/* Connected Platforms */}
        {connectedPlatforms.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center">
              <ExternalLink className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <h3 className="text-lg font-semibold mb-2">No platforms connected</h3>
              <p className="text-gray-600 mb-4">
                Connect your first platform to start using AI agents with your data.
              </p>
              <Button onClick={() => setShowConnectModal(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Connect Platform
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {connectedPlatforms.map((platform) => (
              <PlatformConnectionCard
                key={platform.id}
                platform={platform}
                onDisconnect={handleDisconnect}
                onRefresh={handleRefresh}
                onReconnect={handleReconnect}
              />
            ))}
          </div>
        )}

        {/* Connect Platform Modal */}
        <PlatformConnectionModal
          isOpen={showConnectModal}
          onClose={() => setShowConnectModal(false)}
          onConnect={handleConnect}
          connectedPlatforms={connectedPlatforms.map(p => p.platform_name)}
        />
      </div>
    </div>
  )
}
