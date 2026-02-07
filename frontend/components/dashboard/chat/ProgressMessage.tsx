import React from 'react'
import { CheckCircle2, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface TaskItem {
    id: string
    label: string
    status: 'completed' | 'in-progress' | 'pending'
}

interface ProgressMessageProps {
    title: string
    currentStep: number
    totalSteps: number
    tasks: TaskItem[]
    eta?: string
    className?: string
}

export function ProgressMessage({
    title,
    currentStep,
    totalSteps,
    tasks,
    eta,
    className
}: ProgressMessageProps) {
    const progressPercentage = (currentStep / totalSteps) * 100

    return (
        <div className={cn("p-6 bg-white border rounded-2xl shadow-sm", className)}>
            <p className="font-medium mb-4">{title}</p>

            {/* Progress Bar */}
            <div className="mb-4">
                <div className="flex items-center justify-between text-xs mb-1">
                    <span className="font-medium">⚙️ Progress:</span>
                    <span className="text-slate-600">{currentStep}/{totalSteps} completed</span>
                </div>
                <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                    <div
                        className="h-full bg-green-500 transition-all duration-500 ease-out"
                        style={{ width: `${progressPercentage}%` }}
                    />
                </div>
            </div>

            {/* Task Checklist */}
            <div className="space-y-2 text-sm">
                {tasks.map((task) => (
                    <div
                        key={task.id}
                        className={cn(
                            "flex items-center space-x-2",
                            task.status === 'completed' && 'text-green-600',
                            task.status === 'in-progress' && 'text-blue-600',
                            task.status === 'pending' && 'text-slate-400'
                        )}
                    >
                        {task.status === 'completed' && (
                            <CheckCircle2 className="h-4 w-4 flex-shrink-0" />
                        )}
                        {task.status === 'in-progress' && (
                            <Loader2 className="h-4 w-4 animate-spin flex-shrink-0" />
                        )}
                        {task.status === 'pending' && (
                            <div className="h-4 w-4 rounded-full border-2 border-slate-300 flex-shrink-0" />
                        )}
                        <span>{task.label}</span>
                    </div>
                ))}
            </div>

            {/* ETA */}
            {eta && (
                <p className="text-xs text-slate-500 mt-4 font-medium">
                    ⏱️ ETA: {eta}
                </p>
            )}
        </div>
    )
}
