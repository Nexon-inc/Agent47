"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { 
  X, 
  Save, 
  TrendingUp,
  Target,
  Calendar,
  CheckCircle
} from "lucide-react"
import { Goal, UpdateGoalProgressData } from "@/lib/api-client"
import { useGoalsStore } from "@/lib/stores/goals-store"

interface GoalProgressModalProps {
  goal: Goal
  isOpen: boolean
  onClose: () => void
  onProgressUpdated: () => void
}

export default function GoalProgressModal({ goal, isOpen, onClose, onProgressUpdated }: GoalProgressModalProps) {
  const [progressUpdates, setProgressUpdates] = useState<Record<string, number>>({})
  const [notes, setNotes] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  const { updateGoalProgress, fetchGoalProgress, goalProgress } = useGoalsStore()

  useEffect(() => {
    if (isOpen && goal) {
      fetchGoalProgress(goal.id)
      const initialUpdates: Record<string, number> = {}
      goal.metrics.forEach(metric => {
        initialUpdates[metric.name] = metric.current_value
      })
      setProgressUpdates(initialUpdates)
    }
  }, [isOpen, goal, fetchGoalProgress])

  const handleSubmit = async () => {
    setIsSubmitting(true)
    try {
      const updates = Object.entries(progressUpdates)
      for (const [metricName, currentValue] of updates) {
        await updateGoalProgress(goal.id, {
          metric_name: metricName,
          current_value: currentValue,
          notes: notes
        })
      }
      onProgressUpdated()
    } catch (error) {
      console.error("Failed to update progress:", error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleMetricUpdate = (metricName: string, value: number) => {
    setProgressUpdates(prev => ({
      ...prev,
      [metricName]: value
    }))
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Update Goal Progress</h2>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="space-y-6">
          {/* Goal Info */}
          <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <h3 className="font-medium text-gray-900 dark:text-white mb-2">{goal.name}</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">{goal.description}</p>
            <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
              <div className="flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                <span>Due: {new Date(goal.end_date).toLocaleDateString()}</span>
              </div>
              <div className="flex items-center gap-1">
                <Target className="h-4 w-4" />
                <span>{goal.days_remaining} days left</span>
              </div>
            </div>
          </div>

          {/* Overall Progress */}
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

          {/* Metrics Updates */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Update Metrics
            </label>
            <div className="space-y-4">
              {goal.metrics.map((metric, index) => {
                const currentValue = progressUpdates[metric.name] || metric.current_value
                const progressPercentage = metric.target_value > 0 ? (currentValue / metric.target_value) * 100 : 0
                const isCompleted = currentValue >= metric.target_value

                return (
                  <div key={index} className="p-4 border border-gray-200 rounded-lg">
                    <div className="flex justify-between items-center mb-3">
                      <div>
                        <h4 className="font-medium text-gray-900 dark:text-white">{metric.name}</h4>
                        <p className="text-sm text-gray-500">
                          Target: {metric.target_value} {metric.unit}
                        </p>
                      </div>
                      {isCompleted && (
                        <Badge className="bg-green-100 text-green-800">
                          <CheckCircle className="h-3 w-3 mr-1" />
                          Completed
                        </Badge>
                      )}
                    </div>
                    
                    <div className="space-y-3">
                      <div className="flex items-center gap-3">
                        <label className="text-sm font-medium text-gray-700 dark:text-gray-300 min-w-[80px]">
                          Current Value:
                        </label>
                        <Input
                          type="number"
                          value={currentValue}
                          onChange={(e) => handleMetricUpdate(metric.name, parseFloat(e.target.value) || 0)}
                          className="w-32"
                          min="0"
                          step="0.01"
                        />
                        <span className="text-sm text-gray-500">{metric.unit}</span>
                      </div>
                      
                      <div className="space-y-1">
                        <div className="flex justify-between text-sm">
                          <span>{progressPercentage.toFixed(1)}%</span>
                          <span>{currentValue} / {metric.target_value}</span>
                        </div>
                        <Progress value={Math.min(100, progressPercentage)} className="h-2" />
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Update Notes (Optional)
            </label>
            <Textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add notes about this progress update..."
              rows={3}
            />
          </div>

          {/* Recent Progress History */}
          {goalProgress.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Recent Progress History
              </label>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {goalProgress.slice(0, 5).map((progress, index) => (
                  <div key={index} className="p-3 bg-gray-50 dark:bg-gray-700 rounded-md">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-medium text-sm">{progress.metric_name}</p>
                        <p className="text-sm text-gray-500">
                          Updated to {progress.current_value} on {new Date(progress.timestamp).toLocaleDateString()}
                        </p>
                        {progress.notes && (
                          <p className="text-sm text-gray-600 mt-1">{progress.notes}</p>
                        )}
                      </div>
                      <span className="text-xs text-gray-400">
                        {new Date(progress.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-6 border-t">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button 
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="bg-green-600 hover:bg-green-700"
            >
              {isSubmitting ? "Updating..." : "Update Progress"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
