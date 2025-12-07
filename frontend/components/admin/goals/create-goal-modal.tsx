"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { 
  X, 
  Plus, 
  Trash2, 
  Target,
  Users,
  Tag
} from "lucide-react"
import { useGoalsStore } from "@/lib/stores/goals-store"
import { CreateGoalData } from "@/lib/api-client"

interface CreateGoalModalProps {
  isOpen: boolean
  onClose: () => void
  onGoalCreated: () => void
}

export default function CreateGoalModal({ isOpen, onClose, onGoalCreated }: CreateGoalModalProps) {
  const [formData, setFormData] = useState<CreateGoalData>({
    name: "",
    description: "",
    goal_type: "user_acquisition",
    priority: "medium",
    start_date: new Date().toISOString().split('T')[0],
    end_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    metrics: [],
    assigned_agents: [],
    tags: [],
    budget: 0
  })
  const [newMetric, setNewMetric] = useState({
    name: "",
    target_value: 0,
    unit: "",
    weight: 1.0,
    is_primary: false
  })
  const [newAgent, setNewAgent] = useState("")
  const [newTag, setNewTag] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  const { createGoal } = useGoalsStore()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.name || !formData.description || formData.metrics.length === 0) {
      return
    }

    setIsSubmitting(true)
    try {
      const goal = await createGoal(formData)
      if (goal) {
        onGoalCreated()
        resetForm()
      }
    } catch (error) {
      console.error("Failed to create goal:", error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const resetForm = () => {
    setFormData({
      name: "",
      description: "",
      goal_type: "user_acquisition",
      priority: "medium",
      start_date: new Date().toISOString().split('T')[0],
      end_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      metrics: [],
      assigned_agents: [],
      tags: [],
      budget: 0
    })
    setNewMetric({
      name: "",
      target_value: 0,
      unit: "",
      weight: 1.0,
      is_primary: false
    })
    setNewAgent("")
    setNewTag("")
  }

  const addMetric = () => {
    if (newMetric.name && newMetric.target_value > 0) {
      setFormData(prev => ({
        ...prev,
        metrics: [...prev.metrics, { ...newMetric }]
      }))
      setNewMetric({
        name: "",
        target_value: 0,
        unit: "",
        weight: 1.0,
        is_primary: false
      })
    }
  }

  const removeMetric = (index: number) => {
    setFormData(prev => ({
      ...prev,
      metrics: prev.metrics.filter((_, i) => i !== index)
    }))
  }

  const addAgent = () => {
    if (newAgent.trim() && !formData.assigned_agents.includes(newAgent.trim())) {
      setFormData(prev => ({
        ...prev,
        assigned_agents: [...prev.assigned_agents, newAgent.trim()]
      }))
      setNewAgent("")
    }
  }

  const removeAgent = (agent: string) => {
    setFormData(prev => ({
      ...prev,
      assigned_agents: prev.assigned_agents.filter(a => a !== agent)
    }))
  }

  const addTag = () => {
    if (newTag.trim() && !formData.tags.includes(newTag.trim())) {
      setFormData(prev => ({
        ...prev,
        tags: [...prev.tags, newTag.trim()]
      }))
      setNewTag("")
    }
  }

  const removeTag = (tag: string) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(t => t !== tag)
    }))
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Create New Goal</h2>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Goal Name *
              </label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="Enter goal name"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Goal Type
              </label>
              <select
                value={formData.goal_type}
                onChange={(e) => setFormData(prev => ({ ...prev, goal_type: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                <option value="user_acquisition">User Acquisition</option>
                <option value="revenue_generation">Revenue Generation</option>
                <option value="customer_satisfaction">Customer Satisfaction</option>
                <option value="operational_efficiency">Operational Efficiency</option>
                <option value="market_expansion">Market Expansion</option>
                <option value="product_development">Product Development</option>
                <option value="custom">Custom</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Description *
            </label>
            <Textarea
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              placeholder="Describe the goal and its objectives"
              rows={3}
              required
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Priority
              </label>
              <select
                value={formData.priority}
                onChange={(e) => setFormData(prev => ({ ...prev, priority: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Start Date
              </label>
              <Input
                type="date"
                value={formData.start_date}
                onChange={(e) => setFormData(prev => ({ ...prev, start_date: e.target.value }))}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                End Date
              </label>
              <Input
                type="date"
                value={formData.end_date}
                onChange={(e) => setFormData(prev => ({ ...prev, end_date: e.target.value }))}
              />
            </div>
          </div>

          {/* Metrics */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Metrics *
            </label>
            <div className="space-y-4">
              {formData.metrics.map((metric, index) => (
                <div key={index} className="flex items-center gap-2 p-3 border border-gray-200 rounded-md">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{metric.name}</span>
                      <Badge variant="secondary">{metric.target_value} {metric.unit}</Badge>
                      {metric.is_primary && <Badge variant="default">Primary</Badge>}
                    </div>
                    <div className="text-sm text-gray-500">Weight: {metric.weight}</div>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => removeMetric(index)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
              
              <div className="grid grid-cols-1 md:grid-cols-4 gap-2">
                <Input
                  placeholder="Metric name"
                  value={newMetric.name}
                  onChange={(e) => setNewMetric(prev => ({ ...prev, name: e.target.value }))}
                />
                <Input
                  type="number"
                  placeholder="Target value"
                  value={newMetric.target_value}
                  onChange={(e) => setNewMetric(prev => ({ ...prev, target_value: parseFloat(e.target.value) || 0 }))}
                />
                <Input
                  placeholder="Unit"
                  value={newMetric.unit}
                  onChange={(e) => setNewMetric(prev => ({ ...prev, unit: e.target.value }))}
                />
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={newMetric.is_primary}
                    onChange={(e) => setNewMetric(prev => ({ ...prev, is_primary: e.target.checked }))}
                    className="rounded"
                  />
                  <span className="text-sm">Primary</span>
                </div>
              </div>
              <Button type="button" onClick={addMetric} variant="outline" size="sm">
                <Plus className="h-4 w-4 mr-2" />
                Add Metric
              </Button>
            </div>
          </div>

          {/* Assigned Agents */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Assigned Agents
            </label>
            <div className="space-y-2">
              <div className="flex gap-2">
                <Input
                  placeholder="Agent name"
                  value={newAgent}
                  onChange={(e) => setNewAgent(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addAgent())}
                />
                <Button type="button" onClick={addAgent} variant="outline" size="sm">
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
              <div className="flex flex-wrap gap-2">
                {formData.assigned_agents.map((agent, index) => (
                  <Badge key={index} variant="secondary" className="flex items-center gap-1">
                    <Users className="h-3 w-3" />
                    {agent}
                    <button
                      type="button"
                      onClick={() => removeAgent(agent)}
                      className="ml-1 hover:text-red-600"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-6 border-t">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button 
              type="submit" 
              disabled={isSubmitting || !formData.name || !formData.description || formData.metrics.length === 0}
              className="bg-green-600 hover:bg-green-700"
            >
              {isSubmitting ? "Creating..." : "Create Goal"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
