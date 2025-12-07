"use client"

import { LucideIcon } from "lucide-react"
import { Card } from "@/components/ui/card"

interface EmptyStateProps {
  icon: LucideIcon
  title: string
  description?: string
  action?: {
    label: string
    onClick: () => void
  }
}

export default function EmptyState({ icon: Icon, title, description, action }: EmptyStateProps) {
  return (
    <Card className="bg-gray-900/50 border-gray-800 p-12">
      <div className="flex flex-col items-center justify-center text-center">
        <div className="w-16 h-16 rounded-full bg-gray-800 flex items-center justify-center mb-4">
          <Icon className="w-8 h-8 text-gray-400" />
        </div>
        <h3 className="text-xl font-semibold text-white mb-2">{title}</h3>
        {description && (
          <p className="text-gray-400 max-w-md mb-6">{description}</p>
        )}
        {action && (
          <button
            onClick={action.onClick}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
          >
            {action.label}
          </button>
        )}
      </div>
    </Card>
  )
}

