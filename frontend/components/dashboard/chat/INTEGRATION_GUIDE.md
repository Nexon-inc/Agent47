# Premium Chat UI Components - Integration Guide

This guide demonstrates how to integrate the new premium chat components into your existing chat interfaces.

## Components Created

1. **RichResponseCard** - Display analytics, reports, and structured data
2. **ProgressMessage** - Show real-time task progress with visual indicators
3. **EnhancedChatInput** - Input with slash command autocomplete
4. **EmployeeSelector** - Dropdown to switch between agents with status
5. **TaskQueueSidebar** - Display employee workload and tasks

## Integration Example for Home Tab

```tsx
import { useState } from 'react'
import {
  RichResponseCard,
  ProgressMessage,
  EnhancedChatInput,
  EmployeeSelector,
  TaskQueueSidebar,
  type Agent,
  type SlashCommand
} from '@/components/dashboard/chat'

// Define your agents with status
const agents: Agent[] = [
  {
    id: 'aria',
    name: 'Aria',
    title: 'Social Media Manager',
    description: 'Manages your social media presence',
    icon: Globe,
    color: 'bg-orange-500',
    status: 'available',
    taskCount: 2,
    isLocked: false
  },
  // ... more agents
]

// Define slash commands per agent
const getSlashCommands = (agentId: string): SlashCommand[] => {
  const commandMap = {
    aria: [
      { command: '/schedule', description: 'Schedule posts', action: () => {} },
      { command: '/analyze', description: 'Analyze performance', action: () => {} },
      { command: '/create', description: 'Create content', action: () => {} },
      { command: '/report', description: 'Generate report', action: () => {} }
    ],
    // ... commands for other agents
  }
  return commandMap[agentId] || []
}

function ChatInterface() {
  const [selectedAgent, setSelectedAgent] = useState(agents[0])
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState([])

  // Example workload data
  const workload = {
    inProgress: [
      { id: '1', title: 'Creating weekly content', eta: '2 minutes' },
      { id: '2', title: 'Analyzing competitor accounts', eta: '5 minutes' }
    ],
    awaitingApproval: [
      { id: '3', title: '7 scheduled posts ready' }
    ],
    completedToday: {
      count: 8,
      items: [
        'Responded to 47 comments',
        'Scheduled 12 posts',
        'Generated 3 reports'
      ]
    }
  }

  const handleSend = () => {
    // Send message logic
    setInput('')
  }

  return (
    <div className="flex h-screen">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header with Employee Selector */}
        <div className="border-b p-4">
          <div className="flex items-center justify-between">
            <EmployeeSelector
              agents={agents}
              selectedAgent={selectedAgent}
              onSelectAgent={setSelectedAgent}
              showTeamChat={true}
              isTeamChatLocked={false}
              onTeamChatClick={() => {}}
              onUpgradeClick={() => {}}
            />
            
            {/* Status Indicator */}
            <div className="flex items-center space-x-2">
              <div className="h-2 w-2 rounded-full bg-green-500" />
              <span className="text-xs font-medium">Available</span>
            </div>
          </div>
          
          {/* Role Description */}
          <div className="mt-2 text-xs text-slate-600">
            {selectedAgent.title} • Works 24/7 • Response: Instant
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Example: Rich Response Card */}
          <RichResponseCard
            title="INSTAGRAM PERFORMANCE REPORT"
            icon="📊"
            metrics={[
              { label: 'Total Posts', value: 42 },
              { label: 'Avg Engagement', value: '3.2%', trend: { direction: 'up', value: '0.5%' } },
              { label: 'Total Reach', value: '127K', trend: { direction: 'up', value: '23%' } },
              { label: 'New Followers', value: '+847' }
            ]}
            sections={[
              {
                title: 'Best Performing',
                icon: '🏆',
                items: [
                  'Content Type: Carousel posts (4.8% eng rate)',
                  'Best Time: 7 PM weekdays',
                  'Top Topic: Product tutorials'
                ]
              }
            ]}
            recommendations={[
              'Post more carousels (2x current volume)',
              'Schedule at 7 PM for maximum reach',
              'Add polls to Stories (increases eng 2x)',
              'Reduce text-only posts (low performance)'
            ]}
            actions={[
              { label: 'Full Report', icon: '📄', variant: 'outline', onClick: () => {} },
              { label: 'Export Data', icon: '📊', variant: 'outline', onClick: () => {} },
              { label: 'Apply Changes', icon: '🎯', variant: 'default', onClick: () => {} }
            ]}
          />

          {/* Example: Progress Message */}
          <ProgressMessage
            title="Creating 7 posts for next week..."
            currentStep={4}
            totalSteps={7}
            tasks={[
              { id: '1', label: 'Monday: Carousel about features', status: 'completed' },
              { id: '2', label: 'Tuesday: Tutorial video script', status: 'completed' },
              { id: '3', label: 'Wednesday: Customer testimonial', status: 'completed' },
              { id: '4', label: 'Thursday: Behind-the-scenes', status: 'completed' },
              { id: '5', label: 'Friday: Product showcase...', status: 'in-progress' },
              { id: '6', label: 'Saturday: Weekend engagement post...', status: 'pending' },
              { id: '7', label: 'Sunday: Week preview...', status: 'pending' }
            ]}
            eta="2 minutes"
          />
        </div>

        {/* Enhanced Input */}
        <EnhancedChatInput
          placeholder={`Type your message to ${selectedAgent.name}...`}
          value={input}
          onChange={setInput}
          onSend={handleSend}
          onFileUpload={(file) => console.log('File:', file)}
          onVoiceToggle={() => {}}
          slashCommands={getSlashCommands(selectedAgent.id)}
        />
      </div>

      {/* Task Queue Sidebar */}
      <TaskQueueSidebar
        agentName={selectedAgent.name}
        workload={workload}
        onReviewApproval={(taskId) => console.log('Review:', taskId)}
        onViewAll={() => console.log('View all')}
      />
    </div>
  )
}
```

## Quick Actions Integration

Add quick action buttons below the header:

```tsx
const quickActions = {
  aria: [
    { id: 'schedule', label: 'Schedule Posts', icon: '📅' },
    { id: 'analyze', label: 'Analyze Account', icon: '📊' },
    { id: 'create', label: 'Create Content', icon: '✍️' },
    { id: 'report', label: 'Generate Report', icon: '📈' }
  ],
  // ... actions for other agents
}

// In your header section:
<div className="px-6 py-3 flex gap-2 overflow-x-auto border-b">
  {quickActions[selectedAgent.id]?.map(action => (
    <Button
      key={action.id}
      variant="outline"
      size="sm"
      onClick={() => handleQuickAction(action.id)}
    >
      <span className="mr-1">{action.icon}</span>
      {action.label}
    </Button>
  ))}
</div>
```

## Status Indicators

Implement the 4-state status system:

```tsx
const statusConfig = {
  available: { dot: 'bg-green-500', label: 'Available', description: 'Ready to work' },
  working: { dot: 'bg-yellow-500', label: 'Working', description: 'Processing tasks' },
  'needs-attention': { dot: 'bg-red-500', label: 'Needs Attention', description: 'Awaiting approval' },
  locked: { dot: 'bg-slate-300', label: 'Locked', description: 'Upgrade to access' }
}
```

## Next Steps

1. Integrate components into `home-tab.tsx`
2. Add quick action buttons per agent
3. Implement status update logic via WebSocket
4. Create initial greeting messages
5. Build Team Chat multi-agent mode
6. Add mobile responsive layouts
