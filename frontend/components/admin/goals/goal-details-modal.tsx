"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { 
  X, 
  Edit, 
  Save, 
  Calendar,
  Users,
  Target,
  TrendingUp,
  CheckCircle,
  Clock
} from "lucide-react"
import { Goal, UpdateGoalData } from "@/lib/api-client"
import { useGoalsStore } from "@/lib/stores/goals-store"

interface GoalDetailsModalProps {
  goal: Goal
  isOpen: boolean
  onClose: () => void
  onGoalUpdated: () => void
}

export default function GoalDetailsModal({ goal, isOpen, onClose, onGoalUpdated }: GoalDetailsModalProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editedGoal, setEditedGoal] = useState<UpdateGoalData>({
    name: goal.name,
    description: goal.description,
    status: goal.status,
    priority: goal.priority,
    end_date: goal.end_date.split('T')[0],
    budget: goal.budget
  })
  const [isSubmitting, setIsSubmitting] = useState(false)

  const { updateGoal } = useGoalsStore()

  const handleSave = async () => {
    setIsSubmitting(true)
    try {
      const updatedGoal = await updateGoal(goal.id, editedGoal)
      if (updatedGoal) {
        setIsEditing(false)
        onGoalUpdated()
      }
    } catch (error) {
      console.error("Failed to update goal:", error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active": return "bg-green-100 text-green-800"
      case "completed": return "bg-blue-100 text-blue-800"
      case "paused": return "bg-yellow-100 text-yellow-800"
      case "failed": return "bg-red-100 text-red-800"
      default: return "bg-gray-100 text-gray-800"
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Goal Details</h2>
          <div className="flex gap-2">
            {!isEditing && (
              <Button variant="outline" size="sm" onClick={() => setIsEditing(true)}>
                <Edit className="h-4 w-4 mr-2" />
                Edit
              </Button>
            )}
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div className="space-y-6">
          {/* Basic Information */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Goal Name
            </label>
            {isEditing ? (
              <Input
                value={editedGoal.name}
                onChange={(e) => setEditedGoal(prev => ({ ...prev, name: e.target.value }))}
              />
            ) : (
              <p className="text-gray-900 dark:text-white font-medium">{goal.name}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Description
            </label>
            {isEditing ? (
              <Textarea
                value={editedGoal.description}
                onChange={(e) => setEditedGoal(prev => ({ ...prev, description: e.target.value }))}
                rows={3}
              />
            ) : (
              <p className="text-gray-600 dark:text-gray-400">{goal.description}</p>
            )}
          </div>

          {/* Status and Progress */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Status
              </label>
              {isEditing ? (
                <select
                  value={editedGoal.status}
                  onChange={(e) => setEditedGoal(prev => ({ ...prev, status: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="draft">Draft</option>
                  <option value="active">Active</option>
                  <option value="paused">Paused</option>
                  <option value="completed">Completed</option>
                  <option value="failed">Failed</option>
                </select>
              ) : (
                <Badge className={getStatusColor(goal.status)}>{goal.status}</Badge>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Overall Progress
              </label>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>{goal.overall_progress.toFixed(1)}%</span>
                  <span>{goal.is_completed ? "Completed" : "In Progress"}</span>
                </div>
                <Progress value={goal.overall_progress} className="h-2" />
              </div>
            </div>
          </div>

          {/* Metrics */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Metrics
            </label>
            <div className="space-y-3">
              {goal.metrics.map((metric, index) => (
                <div key={index} className="p-3 border border-gray-200 rounded-md">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-medium">{metric.name}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-500">
                        {metric.current_value} / {metric.target_value} {metric.unit}
                      </span>
                      {metric.is_primary && <Badge variant="default">Primary</Badge>}
                    </div>
                  </div>
                  <div className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span>{metric.progress_percentage.toFixed(1)}%</span>
                      <span>Weight: {metric.weight}</span>
                    </div>
                    <Progress value={metric.progress_percentage} className="h-2" />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Timeline and Agents */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Timeline
              </label>
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  <span>Start: {new Date(goal.start_date).toLocaleDateString()}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  <span>End: {new Date(goal.end_date).toLocaleDateString()}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  <span>{goal.days_remaining} days remaining</span>
                </div>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Assigned Agents
              </label>
              <div className="flex flex-wrap gap-2">
                {goal.assigned_agents.map((agent, index) => (
                  <Badge key={index} variant="secondary">
                    <Users className="h-3 w-3 mr-1" />
                    {agent}
                  </Badge>
                ))}
              </div>
            </div>
          </div>

          {/* Tags */}
          {goal.tags.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Tags
              </label>
              <div className="flex flex-wrap gap-2">
                {goal.tags.map((tag, index) => (
                  <Badge key={index} variant="outline">{tag}</Badge>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          {isEditing && (
            <div className="flex justify-end gap-3 pt-6 border-t">
              <Button variant="outline" onClick={() => setIsEditing(false)}>
                Cancel
              </Button>
              <Button 
                onClick={handleSave}
                disabled={isSubmitting}
                className="bg-green-600 hover:bg-green-700"
              >
                {isSubmitting ? "Saving..." : "Save Changes"}
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
