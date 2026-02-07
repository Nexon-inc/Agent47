import React from 'react'
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ChevronDown, Crown, Lock } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface Agent {
    id: string
    name: string
    title: string
    description: string
    icon: React.ComponentType<{ className?: string }> | string
    color: string
    status: 'available' | 'working' | 'needs-attention' | 'locked'
    taskCount?: number
    isLocked?: boolean
    requiredTier?: string
}

interface EmployeeSelectorProps {
    agents: Agent[]
    selectedAgent: Agent
    onSelectAgent: (agent: Agent) => void
    showTeamChat?: boolean
    isTeamChatLocked?: boolean
    onTeamChatClick?: () => void
    onUpgradeClick?: () => void
    className?: string
}

const statusConfig = {
    available: { dot: 'bg-green-500', label: 'Available' },
    working: { dot: 'bg-yellow-500', label: 'Working' },
    'needs-attention': { dot: 'bg-red-500', label: 'Needs Attention' },
    locked: { dot: 'bg-slate-300', label: 'Locked' }
}

export function EmployeeSelector({
    agents,
    selectedAgent,
    onSelectAgent,
    showTeamChat = false,
    isTeamChatLocked = false,
    onTeamChatClick,
    onUpgradeClick,
    className
}: EmployeeSelectorProps) {
    const activeAgents = agents.filter(a => !a.isLocked)
    const lockedAgents = agents.filter(a => a.isLocked)
    const statusInfo = statusConfig[selectedAgent.status]

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button
                    variant="ghost"
                    className={cn(
                        "flex items-center space-x-2 hover:bg-slate-50 px-4 py-2 h-auto",
                        className
                    )}
                >
                    <span className="text-sm font-medium text-slate-600">💬 Chat with:</span>
                    <span className="font-bold text-lg">{selectedAgent.name}</span>
                    <ChevronDown className="h-4 w-4 text-slate-400" />
                </Button>
            </DropdownMenuTrigger>

            <DropdownMenuContent align="start" className="w-80">
                {/* Active Employees Section */}
                <DropdownMenuLabel className="text-xs uppercase tracking-wider text-slate-500">
                    Active Employees
                </DropdownMenuLabel>

                {activeAgents.map((agent) => {
                    const agentStatus = statusConfig[agent.status]
                    const isSelected = agent.id === selectedAgent.id

                    return (
                        <DropdownMenuItem
                            key={agent.id}
                            onClick={() => onSelectAgent(agent)}
                            className={cn(
                                "flex items-start space-x-3 p-3 cursor-pointer",
                                isSelected && "bg-slate-50"
                            )}
                        >
                            {/* Status Dot */}
                            <div className="flex items-center pt-1">
                                <div className={cn("h-2 w-2 rounded-full", agentStatus.dot)} />
                            </div>

                            {/* Agent Info */}
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center justify-between mb-1">
                                    <span className="font-bold text-sm">{agent.name}</span>
                                    {agent.taskCount !== undefined && agent.taskCount > 0 && (
                                        <Badge variant="secondary" className="text-xs">
                                            {agent.taskCount} {agent.taskCount === 1 ? 'task' : 'tasks'}
                                        </Badge>
                                    )}
                                </div>
                                <p className="text-xs text-slate-600">{agent.title}</p>
                                {agent.status === 'working' && agent.taskCount && (
                                    <p className="text-xs text-blue-600 mt-1">
                                        Working: {agent.taskCount} {agent.taskCount === 1 ? 'task' : 'tasks'}
                                    </p>
                                )}
                            </div>
                        </DropdownMenuItem>
                    )
                })}

                {/* Locked Employees Section */}
                {lockedAgents.length > 0 && (
                    <>
                        <DropdownMenuSeparator />
                        <DropdownMenuLabel className="text-xs uppercase tracking-wider text-slate-500">
                            Upgrade to Unlock
                        </DropdownMenuLabel>

                        {lockedAgents.map((agent) => (
                            <DropdownMenuItem
                                key={agent.id}
                                onClick={onUpgradeClick}
                                className="flex items-start space-x-3 p-3 cursor-pointer opacity-60 hover:opacity-100"
                            >
                                {/* Locked Icon */}
                                <div className="flex items-center pt-1">
                                    <Lock className="h-3 w-3 text-slate-400" />
                                </div>

                                {/* Agent Info */}
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center justify-between mb-1">
                                        <span className="font-bold text-sm">{agent.name}</span>
                                        {agent.requiredTier && (
                                            <Badge variant="outline" className="text-xs">
                                                {agent.requiredTier}
                                            </Badge>
                                        )}
                                    </div>
                                    <p className="text-xs text-slate-600">{agent.title}</p>
                                    <Button
                                        size="sm"
                                        variant="link"
                                        className="h-auto p-0 text-xs text-green-600 mt-1"
                                        onClick={(e) => {
                                            e.stopPropagation()
                                            onUpgradeClick?.()
                                        }}
                                    >
                                        Upgrade to Chat →
                                    </Button>
                                </div>
                            </DropdownMenuItem>
                        ))}
                    </>
                )}

                {/* Team Chat Option */}
                {showTeamChat && (
                    <>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                            onClick={isTeamChatLocked ? onUpgradeClick : onTeamChatClick}
                            className={cn(
                                "flex items-start space-x-3 p-3 cursor-pointer",
                                isTeamChatLocked && "opacity-60 hover:opacity-100"
                            )}
                        >
                            <div className="flex items-center pt-1">
                                <Crown className={cn(
                                    "h-4 w-4",
                                    isTeamChatLocked ? "text-slate-400" : "text-yellow-500"
                                )} />
                            </div>

                            <div className="flex-1">
                                <div className="flex items-center justify-between mb-1">
                                    <span className="font-bold text-sm">💬 Team Chat (All 7)</span>
                                </div>
                                <p className="text-xs text-slate-600">
                                    {isTeamChatLocked
                                        ? 'Collaborate with all employees at once'
                                        : 'All employees working together'}
                                </p>
                                {isTeamChatLocked && (
                                    <Button
                                        size="sm"
                                        variant="link"
                                        className="h-auto p-0 text-xs text-green-600 mt-1"
                                        onClick={(e) => {
                                            e.stopPropagation()
                                            onUpgradeClick?.()
                                        }}
                                    >
                                        Pro Feature - Upgrade →
                                    </Button>
                                )}
                            </div>
                        </DropdownMenuItem>
                    </>
                )}
            </DropdownMenuContent>
        </DropdownMenu>
    )
}
