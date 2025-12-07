"use client"

import React, { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { 
  Search, 
  ExternalLink, 
  CheckCircle, 
  AlertCircle,
  Loader2,
  Globe,
  BarChart,
  Mail,
  ShoppingBag,
  MessageSquare
} from 'lucide-react'
import { platformOAuthService, PlatformConfig } from '@/lib/services/platform-oauth'
import { cn } from '@/lib/utils'

interface PlatformConnectionModalProps {
  isOpen: boolean
  onClose: () => void
  onConnect: (platformName: string) => void
  connectedPlatforms: string[]
}

export function PlatformConnectionModal({ 
  isOpen, 
  onClose, 
  onConnect, 
  connectedPlatforms 
}: PlatformConnectionModalProps) {
  const [platforms, setPlatforms] = useState<PlatformConfig[]>([])
  const [filteredPlatforms, setFilteredPlatforms] = useState<PlatformConfig[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedType, setSelectedType] = useState<string>('all')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen) {
      loadPlatforms()
    }
  }, [isOpen])

  useEffect(() => {
    filterPlatforms()
  }, [platforms, searchQuery, selectedType])

  const loadPlatforms = async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      const availablePlatforms = await platformOAuthService.getAvailablePlatforms()
      setPlatforms(availablePlatforms)
    } catch (err) {
      setError('Failed to load available platforms')
      console.error('Error loading platforms:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const filterPlatforms = () => {
    let filtered = platforms

    // Filter by search query
    if (searchQuery) {
      filtered = filtered.filter(platform =>
        platform.display_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        platform.description.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }

    // Filter by platform type
    if (selectedType !== 'all') {
      filtered = filtered.filter(platform => platform.platform_type === selectedType)
    }

    setFilteredPlatforms(filtered)
  }

  const handleConnect = async (platformName: string) => {
    try {
      await onConnect(platformName)
      onClose()
    } catch (err) {
      console.error('Error connecting to platform:', err)
    }
  }

  const getPlatformIcon = (platformType: string) => {
    switch (platformType) {
      case 'social_media':
        return <Globe className="h-5 w-5" />
      case 'business':
        return <BarChart className="h-5 w-5" />
      case 'communication':
        return <MessageSquare className="h-5 w-5" />
      case 'ecommerce':
        return <ShoppingBag className="h-5 w-5" />
      default:
        return <Globe className="h-5 w-5" />
    }
  }

  const getPlatformTypeColor = (platformType: string) => {
    switch (platformType) {
      case 'social_media':
        return 'bg-blue-100 text-blue-800'
      case 'business':
        return 'bg-green-100 text-green-800'
      case 'communication':
        return 'bg-purple-100 text-purple-800'
      case 'ecommerce':
        return 'bg-orange-100 text-orange-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const platformTypes = [
    { value: 'all', label: 'All Platforms' },
    { value: 'social_media', label: 'Social Media' },
    { value: 'business', label: 'Business' },
    { value: 'communication', label: 'Communication' },
    { value: 'ecommerce', label: 'E-commerce' }
  ]

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle>Connect Platform</DialogTitle>
          <DialogDescription>
            Connect your accounts to enable AI agents to work with your data and automate tasks.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Search and Filters */}
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  placeholder="Search platforms..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="flex gap-2">
              {platformTypes.map((type) => (
                <Button
                  key={type.value}
                  variant={selectedType === type.value ? "default" : "outline"}
                  size="sm"
                  onClick={() => setSelectedType(type.value)}
                >
                  {type.label}
                </Button>
              ))}
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="flex items-center space-x-2 text-red-600 bg-red-50 p-3 rounded-lg">
              <AlertCircle className="h-4 w-4" />
              <span>{error}</span>
            </div>
          )}

          {/* Loading State */}
          {isLoading && (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin" />
              <span className="ml-2">Loading platforms...</span>
            </div>
          )}

          {/* Platforms Grid */}
          {!isLoading && !error && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-96 overflow-y-auto">
              {filteredPlatforms.map((platform) => {
                const isConnected = connectedPlatforms.includes(platform.name)
                const platformInfo = platformOAuthService.getPlatformInfo(platform.name)

                return (
                  <div
                    key={platform.name}
                    className={cn(
                      "border rounded-lg p-4 transition-all duration-200 hover:shadow-md",
                      isConnected 
                        ? "border-green-200 bg-green-50/50" 
                        : "border-gray-200 hover:border-gray-300"
                    )}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        <div className={cn(
                          "flex h-10 w-10 items-center justify-center rounded-lg",
                          platformInfo.bgColor
                        )}>
                          <span className="text-white font-semibold text-sm">
                            {platform.display_name.charAt(0)}
                          </span>
                        </div>
                        <div>
                          <h3 className="font-semibold text-lg">{platform.display_name}</h3>
                          <p className="text-sm text-gray-600">{platform.description}</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Badge className={getPlatformTypeColor(platform.platform_type)}>
                          {getPlatformIcon(platform.platform_type)}
                          <span className="ml-1 capitalize">
                            {platform.platform_type.replace('_', ' ')}
                          </span>
                        </Badge>
                        {isConnected && (
                          <Badge variant="secondary" className="bg-green-100 text-green-800">
                            <CheckCircle className="h-3 w-3 mr-1" />
                            Connected
                          </Badge>
                        )}
                      </div>
                    </div>

                    {/* Features */}
                    <div className="mb-3">
                      <div className="flex flex-wrap gap-1">
                        {Object.entries(platform.supported_features)
                          .filter(([_, supported]) => supported)
                          .map(([feature, _]) => (
                            <Badge key={feature} variant="outline" className="text-xs">
                              {feature.charAt(0).toUpperCase() + feature.slice(1)}
                            </Badge>
                          ))}
                      </div>
                    </div>

                    {/* Scopes Preview */}
                    <div className="mb-3">
                      <div className="text-sm text-gray-600">
                        <span className="font-medium">Permissions:</span> {platform.scopes.length} requested
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {platform.scopes.slice(0, 3).join(', ')}
                        {platform.scopes.length > 3 && ` and ${platform.scopes.length - 3} more...`}
                      </div>
                    </div>

                    {/* Connect Button */}
                    <Button
                      onClick={() => handleConnect(platform.name)}
                      disabled={isConnected}
                      className={cn(
                        "w-full",
                        isConnected && "opacity-50 cursor-not-allowed"
                      )}
                    >
                      {isConnected ? (
                        <>
                          <CheckCircle className="h-4 w-4 mr-2" />
                          Connected
                        </>
                      ) : (
                        <>
                          <ExternalLink className="h-4 w-4 mr-2" />
                          Connect
                        </>
                      )}
                    </Button>
                  </div>
                )
              })}
            </div>
          )}

          {/* No Results */}
          {!isLoading && !error && filteredPlatforms.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <Globe className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>No platforms found matching your criteria.</p>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
