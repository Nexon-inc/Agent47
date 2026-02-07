import React from 'react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface MetricItem {
    label: string
    value: string | number
    trend?: {
        direction: 'up' | 'down'
        value: string
    }
}

interface Section {
    title: string
    icon: string
    items: string[]
}

interface RichResponseCardProps {
    title: string
    icon?: string
    metrics?: MetricItem[]
    sections?: Section[]
    recommendations?: string[]
    actions?: {
        label: string
        icon?: string
        variant?: 'default' | 'outline' | 'ghost'
        onClick: () => void
    }[]
    className?: string
}

export function RichResponseCard({
    title,
    icon = '📊',
    metrics,
    sections,
    recommendations,
    actions,
    className
}: RichResponseCardProps) {
    return (
        <div className={cn("p-6 bg-white border rounded-2xl shadow-sm", className)}>
            {/* Success Header */}
            <div className="flex items-center justify-between mb-4">
                <span className="text-sm font-bold text-green-600">✅ Analysis complete!</span>
            </div>

            {/* Report Card */}
            <div className="border-2 border-slate-200 rounded-xl p-6 mb-4">
                {/* Title */}
                <h3 className="text-lg font-bold mb-4 flex items-center uppercase tracking-tight">
                    {icon} {title}
                </h3>

                {/* Key Metrics Section */}
                {metrics && metrics.length > 0 && (
                    <div className="mb-6">
                        <h4 className="font-bold text-sm mb-2">📈 Key Metrics:</h4>
                        <ul className="space-y-1 text-sm">
                            {metrics.map((metric, idx) => (
                                <li key={idx}>
                                    • {metric.label}: {metric.value}
                                    {metric.trend && (
                                        <span className={cn(
                                            "ml-2",
                                            metric.trend.direction === 'up' ? 'text-green-600' : 'text-red-600'
                                        )}>
                                            ({metric.trend.direction === 'up' ? '↑' : '↓'} {metric.trend.value})
                                        </span>
                                    )}
                                </li>
                            ))}
                        </ul>
                    </div>
                )}

                {/* Dynamic Sections */}
                {sections && sections.map((section, idx) => (
                    <div key={idx} className="mb-6 last:mb-0">
                        <h4 className="font-bold text-sm mb-2">{section.icon} {section.title}:</h4>
                        <ul className="space-y-1 text-sm">
                            {section.items.map((item, itemIdx) => (
                                <li key={itemIdx}>• {item}</li>
                            ))}
                        </ul>
                    </div>
                ))}

                {/* Recommendations Section */}
                {recommendations && recommendations.length > 0 && (
                    <div>
                        <h4 className="font-bold text-sm mb-2">💡 Recommendations:</h4>
                        <ol className="space-y-1 text-sm list-decimal list-inside">
                            {recommendations.map((rec, idx) => (
                                <li key={idx}>{rec}</li>
                            ))}
                        </ol>
                    </div>
                )}
            </div>

            {/* Action Buttons */}
            {actions && actions.length > 0 && (
                <div className="flex gap-3 flex-wrap">
                    {actions.map((action, idx) => (
                        <Button
                            key={idx}
                            variant={action.variant || 'outline'}
                            size="sm"
                            onClick={action.onClick}
                            className={cn(
                                action.variant === 'default' && 'bg-green-600 hover:bg-green-700'
                            )}
                        >
                            {action.icon && <span className="mr-1">{action.icon}</span>}
                            {action.label}
                        </Button>
                    ))}
                </div>
            )}
        </div>
    )
}
