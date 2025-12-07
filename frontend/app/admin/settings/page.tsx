"use client"

import { useState, useEffect } from "react"
import AdminLayout from "@/components/admin/layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { adminAPI } from "@/lib/services/admin-api"
import { useAdminStore } from "@/lib/stores/admin-store"
import { Settings, Save, RefreshCw, AlertCircle, CheckCircle } from "lucide-react"
import EmptyState from "@/components/admin/empty-state"

export default function SettingsPage() {
  const { currentAdmin } = useAdminStore()
  const [settings, setSettings] = useState<Record<string, any>>({})
  const [editedSettings, setEditedSettings] = useState<Record<string, any>>({})
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const hasAccess = currentAdmin?.permissions?.includes("super_admin") || 
                    currentAdmin?.permissions?.includes("system_admin")

  useEffect(() => {
    if (hasAccess) {
      fetchSettings()
    }
  }, [hasAccess])

  const fetchSettings = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await adminAPI.getSettings()
      if (data && typeof data === 'object') {
        setSettings(data)
        setEditedSettings({})
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load settings")
    } finally {
      setIsLoading(false)
    }
  }

  const handleSettingChange = (key: string, value: any) => {
    setEditedSettings({ ...editedSettings, [key]: value })
  }

  const handleSave = async () => {
    setIsSaving(true)
    setError(null)
    setSuccess(null)
    try {
      const updates = Object.entries(editedSettings)
      for (const [key, value] of updates) {
        await adminAPI.updateSetting(key, value, `Updated by ${currentAdmin?.email}`)
      }
      setSuccess(`Successfully updated ${updates.length} setting(s)`)
      setEditedSettings({})
      await fetchSettings()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save settings")
    } finally {
      setIsSaving(false)
    }
  }

  if (!hasAccess) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Settings className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-white">Access Denied</h3>
            <p className="mt-1 text-sm text-gray-500">You don't have permission to access settings.</p>
          </div>
        </div>
      </AdminLayout>
    )
  }

  if (isLoading) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <RefreshCw className="h-8 w-8 text-gray-400 animate-spin mx-auto mb-2" />
            <p className="text-gray-400">Loading settings...</p>
          </div>
        </div>
      </AdminLayout>
    )
  }

  if (error && Object.keys(settings).length === 0) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-red-400" />
            <h3 className="mt-2 text-sm font-medium text-white">Error Loading Settings</h3>
            <p className="mt-1 text-sm text-gray-500">{error}</p>
            <Button onClick={fetchSettings} className="mt-4">
              Retry
            </Button>
          </div>
        </div>
      </AdminLayout>
    )
  }

  const settingsEntries = Object.entries(settings)
  const hasChanges = Object.keys(editedSettings).length > 0

  return (
    <AdminLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Settings</h1>
          <p className="text-gray-400">System-wide configuration settings</p>
        </div>
          <div className="flex gap-2">
            <Button
              onClick={fetchSettings}
              disabled={isLoading}
              className="bg-gray-800 hover:bg-gray-700"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            {hasChanges && (
              <Button
                onClick={handleSave}
                disabled={isSaving}
                className="bg-green-600 hover:bg-green-700"
              >
                <Save className={`w-4 h-4 mr-2 ${isSaving ? 'animate-spin' : ''}`} />
                Save Changes
              </Button>
            )}
          </div>
        </div>

        {error && (
          <div className="bg-red-900/20 border border-red-800 text-red-400 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {success && (
          <div className="bg-green-900/20 border border-green-800 text-green-400 px-4 py-3 rounded-lg flex items-center gap-2">
            <CheckCircle className="w-4 h-4" />
            {success}
          </div>
        )}

        {settingsEntries.length === 0 ? (
          <EmptyState
            icon={Settings}
            title="No Settings Available"
            description="System settings will appear here once configured."
          />
        ) : (
          <div className="space-y-4">
            {settingsEntries.map(([key, value]) => {
              const editedValue = editedSettings[key] !== undefined ? editedSettings[key] : value
              return (
                <Card key={key} className="bg-gray-900/50 border-gray-800">
                  <CardHeader>
                    <CardTitle className="text-white text-sm font-medium">
                      {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Input
                      value={typeof editedValue === 'object' ? JSON.stringify(editedValue) : String(editedValue || '')}
                      onChange={(e) => {
                        let newValue: any = e.target.value
                        // Try to parse as JSON if it looks like JSON
                        if (e.target.value.startsWith('{') || e.target.value.startsWith('[')) {
                          try {
                            newValue = JSON.parse(e.target.value)
                          } catch {
                            // Keep as string if parsing fails
                          }
                        }
                        // Try to parse as number if it's a number
                        if (!isNaN(Number(newValue)) && newValue !== '') {
                          newValue = Number(newValue)
                        }
                        handleSettingChange(key, newValue)
                      }}
                      className="bg-gray-800 border-gray-700 text-white"
                    />
                    {editedSettings[key] !== undefined && (
                      <p className="text-xs text-green-400 mt-1">Modified</p>
                    )}
                  </CardContent>
        </Card>
              )
            })}
          </div>
        )}
      </div>
    </AdminLayout>
  )
}

