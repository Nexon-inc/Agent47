import React from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { RefreshCw, Pause, CheckCircle2, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'

interface TaskItem {
    id: string
    title: string
    eta?: string
}

interface WorkloadData {
    inProgress: TaskItem[]
    awaitingApproval: TaskItem[]
    completedToday: {
        count: number
        items: string[]
    }
}

interface TaskQueueSidebarProps {
    agentName: string
    workload: WorkloadData
    onReviewApproval?: (taskId: string) => void
    onViewAll?: () => void
    className?: string
}

export function TaskQueueSidebar({
    agentName,
    workload,
    onReviewApproval,
    onViewAll,
    className
}: TaskQueueSidebarProps) {
    return (
        <div className={cn(
            "w-80 border-l bg-slate-50 p-4 overflow-y-auto",
            className
        )}>
            <h3 className="font-bold mb-4 text-slate-900">
                {agentName}'s Current Workload
            </h3>

            {/* In Progress Section */}
            {workload.inProgress.length > 0 && (
                <div className="mb-6">
                    <h4 className="text-sm font-bold mb-2 flex items-center text-slate-700">
                        <RefreshCw className="h-4 w-4 mr-2 text-blue-500" />
                        In Progress ({workload.inProgress.length})
                    </h4>
                    <div className="space-y-3">
                        {workload.inProgress.map((task) => (
                            <div
                                key={task.id}
                                className="bg-white p-3 rounded-lg border border-slate-200 shadow-sm"
                            >
                                <p className="text-sm font-medium text-slate-900">{task.title}</p>
                                {task.eta && (
                                    <p className="text-xs text-slate-500 mt-1">ETA: {task.eta}</p>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Awaiting Approval Section */}
            {workload.awaitingApproval.length > 0 && (
                <div className="mb-6">
                    <h4 className="text-sm font-bold mb-2 flex items-center text-slate-700">
                        <Pause className="h-4 w-4 mr-2 text-orange-500" />
                        Awaiting Approval ({workload.awaitingApproval.length})
                    </h4>
                    <div className="space-y-3">
                        {workload.awaitingApproval.map((task) => (
                            <div
                                key={task.id}
                                className="bg-white p-3 rounded-lg border border-orange-200 shadow-sm"
                            >
                                <p className="text-sm font-medium text-slate-900">{task.title}</p>
                                <Button
                                    size="sm"
                                    variant="outline"
                                    className="mt-2 w-full text-xs border-orange-300 text-orange-700 hover:bg-orange-50"
                                    onClick={() => onReviewApproval?.(task.id)}
                                >
                                    Review & Approve →
                                </Button>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Completed Today Section */}
            {workload.completedToday.count > 0 && (
                <div>
                    <h4 className="text-sm font-bold mb-2 flex items-center text-slate-700">
                        <CheckCircle2 className="h-4 w-4 mr-2 text-green-500" />
                        Completed Today ({workload.completedToday.count})
                    </h4>
                    <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-sm">
                        <ul className="text-xs space-y-1 text-slate-600">
                            {workload.completedToday.items.slice(0, 3).map((item, idx) => (
                                <li key={idx}>• {item}</li>
                            ))}
                        </ul>
                        {workload.completedToday.items.length > 3 && (
                            <Button
                                size="sm"
                                variant="link"
                                className="mt-2 p-0 h-auto text-xs text-green-600 hover:text-green-700"
                                onClick={onViewAll}
                            >
                                View All ({workload.completedToday.count}) →
                            </Button>
                        )}
                    </div>
                </div>
            )}

            {/* Empty State */}
            {workload.inProgress.length === 0 &&
                workload.awaitingApproval.length === 0 &&
                workload.completedToday.count === 0 && (
                    <div className="text-center py-8">
                        <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-3">
                            <CheckCircle2 className="h-8 w-8 text-slate-300" />
                        </div>
                        <p className="text-sm font-medium text-slate-600">All caught up!</p>
                        <p className="text-xs text-slate-500 mt-1">
                            {agentName} is ready for new tasks
                        </p>
                    </div>
                )}
        </div>
    )
}
