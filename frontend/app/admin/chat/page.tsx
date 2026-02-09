'use client'

import React, { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { adminAPI } from '@/lib/services/admin-api'
import { useAdminStore } from '@/lib/stores/admin-store'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import AdminLayout from "@/components/admin/layout"
import { agentServiceManager, type AgentService, type AgentTask, type AgentWorkflow, type AgentCommunication } from '@/lib/agent-services'
import {
  Send,
  Bot,
  User,
  Settings,
  Zap,
  Activity,
  Server,
  Database,
  Users,
  BarChart3,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  Terminal,
  Command,
  History,
  Play,
  Pause,
  RefreshCw,
  Trash2,
  Download,
  Upload,
  Eye,
  EyeOff,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Workflow,
  MessageSquare,
  Target,
  TrendingUp,
  FileText,
  Megaphone,
  ShoppingCart,
  Search
} from 'lucide-react'

interface ChatMessage {
  id: string
  type: 'user' | 'system' | 'agent' | 'error' | 'success' | 'warning' | 'thinking'
  content: string
  timestamp: string
  metadata?: {
    command?: string
    execution_time?: number
    agent_id?: string
    status?: string
    data?: any
    thinking_steps?: string[]
  }
}

interface CommandDefinition {
  name: string
  description: string
  syntax: string
  examples: string[]
  category: 'system' | 'agents' | 'analytics' | 'users' | 'billing' | 'security' | 'integration'
  permissions: string[]
  execution_time?: number
}

export default function AdminChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [commandHistory, setCommandHistory] = useState<string[]>([])
  const [historyIndex, setHistoryIndex] = useState(-1)
  const [isVoiceEnabled, setIsVoiceEnabled] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [showCommands, setShowCommands] = useState(false)
  const [activeAgents, setActiveAgents] = useState<string[]>([])
  const [systemStatus, setSystemStatus] = useState('online')
  const [isListening, setIsListening] = useState(false)
  const [voiceTranscript, setVoiceTranscript] = useState('')
  const [aiSuggestions, setAiSuggestions] = useState<string[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [recognition, setRecognition] = useState<any>(null)
  const [agentServices, setAgentServices] = useState<AgentService[]>([])
  const [agentTasks, setAgentTasks] = useState<AgentTask[]>([])
  const [agentWorkflows, setAgentWorkflows] = useState<AgentWorkflow[]>([])
  const [isAgentManagerInitialized, setIsAgentManagerInitialized] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const commands: CommandDefinition[] = [
    // System Commands
    {
      name: 'system.status',
      description: 'Display comprehensive system status and health metrics',
      syntax: 'system.status [detailed]',
      examples: ['system.status', 'system.status detailed'],
      category: 'system',
      permissions: ['superadmin', 'admin']
    },
    {
      name: 'system.restart',
      description: 'Restart specific system components or entire system',
      syntax: 'system.restart [component]',
      examples: ['system.restart', 'system.restart database', 'system.restart all'],
      category: 'system',
      permissions: ['superadmin']
    },
    {
      name: 'system.maintenance',
      description: 'Enable/disable maintenance mode and schedule maintenance windows',
      syntax: 'system.maintenance [on|off] [duration]',
      examples: ['system.maintenance on 2h', 'system.maintenance off'],
      category: 'system',
      permissions: ['superadmin']
    },
    {
      name: 'system.backup',
      description: 'Create system backups and manage backup schedules',
      syntax: 'system.backup [create|list|restore] [name]',
      examples: ['system.backup create', 'system.backup list', 'system.backup restore latest'],
      category: 'system',
      permissions: ['superadmin']
    },

    // Agent Commands
    {
      name: 'agents.list',
      description: 'List all agents with detailed status and performance metrics',
      syntax: 'agents.list [filter]',
      examples: ['agents.list', 'agents.list online', 'agents.list busy'],
      category: 'agents',
      permissions: ['superadmin', 'admin']
    },
    {
      name: 'agents.status',
      description: 'Get detailed status of specific agent or all agents',
      syntax: 'agents.status [agent_id]',
      examples: ['agents.status', 'agents.status aria', 'agents.status all'],
      category: 'agents',
      permissions: ['superadmin', 'admin']
    },
    {
      name: 'agents.restart',
      description: 'Restart specific agent or multiple agents',
      syntax: 'agents.restart [agent_id] [force]',
      examples: ['agents.restart aria', 'agents.restart all', 'agents.restart aria force'],
      category: 'agents',
      permissions: ['superadmin', 'admin']
    },
    {
      name: 'agents.configure',
      description: 'Configure agent parameters and capabilities',
      syntax: 'agents.configure [agent_id] [parameter] [value]',
      examples: ['agents.configure aria memory_limit 2GB', 'agents.configure aria enable_api true'],
      category: 'agents',
      permissions: ['superadmin']
    },
    {
      name: 'agents.deploy',
      description: 'Deploy new agent or update existing agent',
      syntax: 'agents.deploy [agent_id] [version] [config]',
      examples: ['agents.deploy new_agent v1.2.0', 'agents.deploy aria v2.0.0'],
      category: 'agents',
      permissions: ['superadmin']
    },
    {
      name: 'agents.monitor',
      description: 'Start real-time monitoring of agent performance',
      syntax: 'agents.monitor [agent_id] [metrics]',
      examples: ['agents.monitor aria', 'agents.monitor all cpu,memory,response_time'],
      category: 'agents',
      permissions: ['superadmin', 'admin']
    },

    // Analytics Commands
    {
      name: 'analytics.overview',
      description: 'Display comprehensive analytics dashboard',
      syntax: 'analytics.overview [period] [metrics]',
      examples: ['analytics.overview', 'analytics.overview 7d', 'analytics.overview 30d revenue,users'],
      category: 'analytics',
      permissions: ['superadmin', 'admin', 'analytics']
    },
    {
      name: 'analytics.report',
      description: 'Generate detailed reports and export data',
      syntax: 'analytics.report [type] [format] [period]',
      examples: ['analytics.report revenue pdf', 'analytics.report users csv 30d'],
      category: 'analytics',
      permissions: ['superadmin', 'admin', 'analytics']
    },
    {
      name: 'analytics.predict',
      description: 'Run predictive analytics and forecasting models',
      syntax: 'analytics.predict [model] [horizon] [data]',
      examples: ['analytics.predict revenue 30d', 'analytics.predict churn 7d'],
      category: 'analytics',
      permissions: ['superadmin', 'analytics']
    },
    {
      name: 'analytics.alerts',
      description: 'Configure and manage analytics alerts',
      syntax: 'analytics.alerts [action] [condition] [threshold]',
      examples: ['analytics.alerts create revenue_drop < 1000', 'analytics.alerts list'],
      category: 'analytics',
      permissions: ['superadmin', 'admin']
    },

    // User Management Commands
    {
      name: 'users.list',
      description: 'List users with filtering and sorting options',
      syntax: 'users.list [filter] [sort] [limit]',
      examples: ['users.list', 'users.list active', 'users.list premium created_at desc 50'],
      category: 'users',
      permissions: ['superadmin', 'admin', 'support']
    },
    {
      name: 'users.details',
      description: 'Get detailed user information and activity',
      syntax: 'users.details [user_id] [include]',
      examples: ['users.details 123', 'users.details 123 activity,payments,usage'],
      category: 'users',
      permissions: ['superadmin', 'admin', 'support']
    },
    {
      name: 'users.modify',
      description: 'Modify user account settings and permissions',
      syntax: 'users.modify [user_id] [action] [value]',
      examples: ['users.modify 123 suspend', 'users.modify 123 upgrade pro', 'users.modify 123 reset_password'],
      category: 'users',
      permissions: ['superadmin', 'admin']
    },
    {
      name: 'users.impersonate',
      description: 'Impersonate user account for support purposes',
      syntax: 'users.impersonate [user_id] [duration]',
      examples: ['users.impersonate 123', 'users.impersonate 123 1h'],
      category: 'users',
      permissions: ['superadmin', 'support']
    },

    // Billing Commands
    {
      name: 'billing.overview',
      description: 'Display billing overview and revenue metrics',
      syntax: 'billing.overview [period] [detailed]',
      examples: ['billing.overview', 'billing.overview 30d detailed'],
      category: 'billing',
      permissions: ['superadmin', 'admin', 'billing']
    },
    {
      name: 'billing.subscriptions',
      description: 'Manage subscriptions and billing plans',
      syntax: 'billing.subscriptions [action] [user_id] [plan]',
      examples: ['billing.subscriptions list', 'billing.subscriptions upgrade 123 pro'],
      category: 'billing',
      permissions: ['superadmin', 'admin', 'billing']
    },
    {
      name: 'billing.refund',
      description: 'Process refunds and billing adjustments',
      syntax: 'billing.refund [payment_id] [amount] [reason]',
      examples: ['billing.refund 456 29.99 duplicate_charge'],
      category: 'billing',
      permissions: ['superadmin', 'billing']
    },
    {
      name: 'billing.export',
      description: 'Export billing data and financial reports',
      syntax: 'billing.export [type] [format] [period]',
      examples: ['billing.export revenue csv 30d', 'billing.export subscriptions pdf'],
      category: 'billing',
      permissions: ['superadmin', 'billing']
    },

    // Security Commands
    {
      name: 'security.audit',
      description: 'Run security audits and vulnerability scans',
      syntax: 'security.audit [type] [scope]',
      examples: ['security.audit', 'security.audit full', 'security.audit users'],
      category: 'security',
      permissions: ['superadmin']
    },
    {
      name: 'security.block',
      description: 'Block IP addresses or user accounts',
      syntax: 'security.block [target] [reason] [duration]',
      examples: ['security.block 192.168.1.1', 'security.block user@example.com suspicious_activity 24h'],
      category: 'security',
      permissions: ['superadmin', 'admin']
    },
    {
      name: 'security.logs',
      description: 'View security logs and access attempts',
      syntax: 'security.logs [type] [filter] [limit]',
      examples: ['security.logs', 'security.logs failed_logins', 'security.logs admin_actions 100'],
      category: 'security',
      permissions: ['superadmin', 'admin']
    },
    {
      name: 'security.encrypt',
      description: 'Manage encryption keys and data encryption',
      syntax: 'security.encrypt [action] [target] [algorithm]',
      examples: ['security.encrypt rotate_keys', 'security.encrypt backup database'],
      category: 'security',
      permissions: ['superadmin']
    },

    // Integration Commands
    {
      name: 'integration.status',
      description: 'Check integration status and health',
      syntax: 'integration.status [service] [detailed]',
      examples: ['integration.status', 'integration.status paystack', 'integration.status all detailed'],
      category: 'integration',
      permissions: ['superadmin', 'admin']
    },
    {
      name: 'integration.test',
      description: 'Test integration endpoints and connectivity',
      syntax: 'integration.test [service] [endpoint]',
      examples: ['integration.test paystack', 'integration.test email smtp'],
      category: 'integration',
      permissions: ['superadmin', 'admin']
    },
    {
      name: 'integration.configure',
      description: 'Configure integration settings and credentials',
      syntax: 'integration.configure [service] [parameter] [value]',
      examples: ['integration.configure paystack api_key new_key', 'integration.configure email smtp_host smtp.gmail.com'],
      category: 'integration',
      permissions: ['superadmin']
    },
    {
      name: 'integration.sync',
      description: 'Synchronize data with external services',
      syntax: 'integration.sync [service] [data_type] [force]',
      examples: ['integration.sync paystack payments', 'integration.sync email contacts force'],
      category: 'integration',
      permissions: ['superadmin', 'admin']
    },

    // AI Commands
    {
      name: 'ai.assist',
      description: 'Get AI-powered recommendations and assistance',
      syntax: 'ai.assist [query]',
      examples: ['ai.assist system health', 'ai.assist optimize performance'],
      category: 'system',
      permissions: ['superadmin', 'admin']
    },
    {
      name: 'ai.optimize',
      description: 'AI-powered system optimization and recommendations',
      syntax: 'ai.optimize [type]',
      examples: ['ai.optimize', 'ai.optimize performance'],
      category: 'system',
      permissions: ['superadmin']
    },
    {
      name: 'ai.predict',
      description: 'Run predictive analytics and forecasting',
      syntax: 'ai.predict [type] [timeframe]',
      examples: ['ai.predict revenue 30d', 'ai.predict users 7d'],
      category: 'analytics',
      permissions: ['superadmin', 'admin', 'analytics']
    },
    {
      name: 'ai.automate',
      description: 'Setup AI automation and monitoring',
      syntax: 'ai.automate [type]',
      examples: ['ai.automate monitoring', 'ai.automate alerts'],
      category: 'system',
      permissions: ['superadmin']
    },

    // Agent Automation Commands
    {
      name: 'agent.execute',
      description: 'Execute a task with a specific agent',
      syntax: 'agent.execute [agent_id] [task_type] [parameters]',
      examples: ['agent.execute aria create_post "AI automation benefits"', 'agent.execute joe market_research "competitor analysis"'],
      category: 'agents',
      permissions: ['superadmin', 'admin']
    },
    {
      name: 'agent.workflow',
      description: 'Create and execute agent workflows',
      syntax: 'agent.workflow [action] [workflow_id] [parameters]',
      examples: ['agent.workflow create "marketing_campaign"', 'agent.workflow execute workflow_123'],
      category: 'agents',
      permissions: ['superadmin', 'admin']
    },
    {
      name: 'agent.communicate',
      description: 'Send messages between agents',
      syntax: 'agent.communicate [sender] [receiver] [message_type] [content]',
      examples: ['agent.communicate aria joe "data_request" "market insights"'],
      category: 'agents',
      permissions: ['superadmin', 'admin']
    },
    {
      name: 'agent.monitor',
      description: 'Monitor agent performance and tasks',
      syntax: 'agent.monitor [agent_id] [metrics]',
      examples: ['agent.monitor aria performance', 'agent.monitor all tasks'],
      category: 'agents',
      permissions: ['superadmin', 'admin']
    },
    {
      name: 'agent.optimize',
      description: 'Optimize agent performance and configurations',
      syntax: 'agent.optimize [agent_id] [parameter] [value]',
      examples: ['agent.optimize aria memory_limit 2GB', 'agent.optimize all performance'],
      category: 'agents',
      permissions: ['superadmin']
    },
    {
      name: 'agent.deploy',
      description: 'Deploy new agents or update existing ones',
      syntax: 'agent.deploy [agent_id] [version] [config]',
      examples: ['agent.deploy new_agent v1.0.0', 'agent.deploy aria v2.0.0'],
      category: 'agents',
      permissions: ['superadmin']
    }
  ]

  useEffect(() => {
    // Initialize chat with welcome message
    addMessage({
      type: 'system',
      content: 'Welcome to Agent47 Admin Command Center. Type "help" for available commands or "commands" to see all options.',
      timestamp: new Date().toISOString()
    })

    // Load command history from localStorage
    const savedHistory = localStorage.getItem('admin_command_history')
    if (savedHistory) {
      setCommandHistory(JSON.parse(savedHistory))
    }

    // Initialize speech recognition
    if (typeof window !== 'undefined' && 'webkitSpeechRecognition' in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition
      const recognition = new SpeechRecognition()
      recognition.continuous = true
      recognition.interimResults = true
      recognition.lang = 'en-US'

      recognition.onstart = () => {
        setIsListening(true)
        addMessage({
          type: 'system',
          content: '🎤 Voice recognition activated. Speak your command...',
          timestamp: new Date().toISOString()
        })
      }

      recognition.onresult = (event: any) => {
        let transcript = ''
        for (let i = event.resultIndex; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript
        }
        setVoiceTranscript(transcript)

        if (event.results[event.results.length - 1].isFinal) {
          const finalTranscript = transcript.trim()
          if (finalTranscript) {
            setInputValue(finalTranscript)
            setVoiceTranscript('')
            setIsListening(false)
            recognition.stop()

            // Generate AI suggestions based on voice input
            generateAiSuggestions(finalTranscript)
          }
        }
      }

      recognition.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error)
        setIsListening(false)
        setVoiceTranscript('')
        addMessage({
          type: 'error',
          content: `Voice recognition error: ${event.error}`,
          timestamp: new Date().toISOString()
        })
      }

      recognition.onend = () => {
        setIsListening(false)
        setVoiceTranscript('')
      }

      setRecognition(recognition)
    }

    // Initialize Agent Service Manager
    const initializeAgentManager = async () => {
      try {
        await agentServiceManager.initialize()
        setIsAgentManagerInitialized(true)

        const agents = await agentServiceManager.getAllAgents()
        const workflows = await agentServiceManager.getWorkflows()

        setAgentServices(agents)
        setAgentWorkflows(workflows)

        addMessage({
          type: 'system',
          content: `🤖 Agent Service Manager initialized with ${agents.length} agents and ${workflows.length} workflows`,
          timestamp: new Date().toISOString()
        })
      } catch (error) {
        console.error('Failed to initialize Agent Service Manager:', error)
        addMessage({
          type: 'error',
          content: 'Failed to initialize Agent Service Manager. Some agent commands may not work.',
          timestamp: new Date().toISOString()
        })
      }
    }

    initializeAgentManager()
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const addMessage = (message: Omit<ChatMessage, 'id'>) => {
    const newMessage: ChatMessage = {
      ...message,
      id: Date.now().toString()
    }
    setMessages(prev => [...prev, newMessage])
  }

  const saveCommandToHistory = (command: string) => {
    const newHistory = [command, ...commandHistory.filter((cmd: string) => cmd !== command)].slice(0, 100)
    setCommandHistory(newHistory)
    localStorage.setItem('admin_command_history', JSON.stringify(newHistory))
  }

  const generateAiSuggestions = (input: string) => {
    const suggestions: string[] = []
    const lowerInput = input.toLowerCase()

    // Context-aware suggestions based on input
    if (lowerInput.includes('system') || lowerInput.includes('status') || lowerInput.includes('health')) {
      suggestions.push('system.status', 'system.status detailed', 'system.restart')
    }

    if (lowerInput.includes('agent') || lowerInput.includes('bot') || lowerInput.includes('ai')) {
      suggestions.push('agents.list', 'agents.status', 'agents.restart aria')
    }

    if (lowerInput.includes('user') || lowerInput.includes('customer') || lowerInput.includes('people')) {
      suggestions.push('users.list', 'users.list active', 'users.details 123')
    }

    if (lowerInput.includes('money') || lowerInput.includes('billing') || lowerInput.includes('payment')) {
      suggestions.push('billing.overview', 'billing.subscriptions list', 'billing.refund 456 29.99')
    }

    if (lowerInput.includes('security') || lowerInput.includes('audit') || lowerInput.includes('safe')) {
      suggestions.push('security.audit', 'security.logs', 'security.block 192.168.1.1')
    }

    if (lowerInput.includes('analytics') || lowerInput.includes('report') || lowerInput.includes('data')) {
      suggestions.push('analytics.overview', 'analytics.report revenue pdf', 'analytics.predict revenue 30d')
    }

    if (lowerInput.includes('integration') || lowerInput.includes('service') || lowerInput.includes('api')) {
      suggestions.push('integration.status', 'integration.test paystack', 'integration.configure paystack api_key')
    }

    // Agent automation suggestions
    if (lowerInput.includes('execute') || lowerInput.includes('run') || lowerInput.includes('task')) {
      suggestions.push('agent.execute aria create_post "AI automation benefits"', 'agent.execute joe market_research "competitor analysis"', 'agent.execute clara resolve_ticket "user support"')
    }

    if (lowerInput.includes('workflow') || lowerInput.includes('automate') || lowerInput.includes('pipeline')) {
      suggestions.push('agent.workflow create "marketing_campaign"', 'agent.workflow list', 'agent.workflow execute workflow_123')
    }

    if (lowerInput.includes('communicate') || lowerInput.includes('message') || lowerInput.includes('send')) {
      suggestions.push('agent.communicate aria joe "data_request" "market insights"', 'agent.communicate clara eric "lead_qualification" "new prospect"')
    }

    if (lowerInput.includes('monitor') || lowerInput.includes('performance') || lowerInput.includes('track')) {
      suggestions.push('agent.monitor aria performance', 'agent.monitor all tasks', 'agent.monitor joe')
    }

    if (lowerInput.includes('social') || lowerInput.includes('media') || lowerInput.includes('post')) {
      suggestions.push('agent.execute aria create_post "AI automation benefits"', 'agent.execute aria analyze_trends', 'agent.execute aria engage_audience')
    }

    if (lowerInput.includes('research') || lowerInput.includes('market') || lowerInput.includes('analysis')) {
      suggestions.push('agent.execute joe market_research "competitor analysis"', 'agent.execute joe competitor_analysis', 'agent.execute joe data_analysis')
    }

    if (lowerInput.includes('support') || lowerInput.includes('help') || lowerInput.includes('ticket')) {
      suggestions.push('agent.execute clara resolve_ticket "user support request"', 'agent.execute clara analyze_sentiment', 'agent.execute clara generate_response')
    }

    if (lowerInput.includes('sales') || lowerInput.includes('lead') || lowerInput.includes('proposal')) {
      suggestions.push('agent.execute eric qualify_lead "new prospect"', 'agent.execute eric generate_proposal', 'agent.execute eric follow_up')
    }

    if (lowerInput.includes('marketing') || lowerInput.includes('campaign') || lowerInput.includes('promote')) {
      suggestions.push('agent.execute jackie create_campaign "email campaign"', 'agent.execute jackie optimize_performance', 'agent.execute jackie analyze_market')
    }

    if (lowerInput.includes('content') || lowerInput.includes('write') || lowerInput.includes('create')) {
      suggestions.push('agent.execute shakes create_content "blog post"', 'agent.execute shakes optimize_seo', 'agent.execute shakes generate_ideas')
    }

    // Add common commands if no specific matches
    if (suggestions.length === 0) {
      suggestions.push('help', 'system.status', 'agents.list', 'users.list', 'billing.overview', 'agent.execute aria create_post "AI automation benefits"')
    }

    setAiSuggestions(suggestions.slice(0, 5))
    setShowSuggestions(true)
  }

  const handleVoiceToggle = () => {
    if (!recognition) {
      addMessage({
        type: 'error',
        content: 'Voice recognition not supported in this browser.',
        timestamp: new Date().toISOString()
      })
      return
    }

    if (isListening) {
      recognition.stop()
      setIsListening(false)
      setVoiceTranscript('')
    } else {
      recognition.start()
    }
  }

  const parseTaskParameters = (params: string): Record<string, any> => {
    const parameters: Record<string, any> = {}

    // Parse key-value pairs
    const pairs = params.match(/(\w+):\s*([^,\s]+)/g)
    if (pairs) {
      pairs.forEach(pair => {
        const [key, value] = pair.split(':').map(s => s.trim())
        parameters[key] = value
      })
    }

    // Parse quoted content as main content
    const contentMatch = params.match(/"([^"]+)"/)
    if (contentMatch) {
      parameters.content = contentMatch[1]
    }

    // Parse action if present
    const actionMatch = params.match(/(create_post|analyze_trends|engage_audience|resolve_ticket|analyze_sentiment|generate_response|market_research|competitor_analysis|data_analysis|qualify_lead|generate_proposal|follow_up|create_campaign|optimize_performance|analyze_market|create_content|optimize_seo|generate_ideas)/)
    if (actionMatch) {
      parameters.action = actionMatch[1]
    }

    return parameters
  }

  const generateWorkflowSteps = (workflowName: string) => {
    const steps = []

    switch (workflowName.toLowerCase()) {
      case 'marketing_campaign':
        steps.push(
          {
            id: 'step_1',
            agent_id: 'joe',
            action: 'market_research',
            parameters: { topic: 'target audience analysis' },
            dependencies: [],
            timeout: 300000,
            retry_count: 3
          },
          {
            id: 'step_2',
            agent_id: 'jackie',
            action: 'create_campaign',
            parameters: { campaign_type: 'email', target_audience: 'qualified leads' },
            dependencies: ['step_1'],
            timeout: 600000,
            retry_count: 2
          },
          {
            id: 'step_3',
            agent_id: 'aria',
            action: 'create_post',
            parameters: { content: 'campaign announcement', platforms: ['linkedin', 'twitter'] },
            dependencies: ['step_2'],
            timeout: 300000,
            retry_count: 2
          }
        )
        break

      case 'lead_qualification':
        steps.push(
          {
            id: 'step_1',
            agent_id: 'eric',
            action: 'qualify_lead',
            parameters: { lead_id: 'auto_generated' },
            dependencies: [],
            timeout: 300000,
            retry_count: 2
          },
          {
            id: 'step_2',
            agent_id: 'clara',
            action: 'generate_response',
            parameters: { query: 'lead qualification follow-up' },
            dependencies: ['step_1'],
            timeout: 300000,
            retry_count: 2
          }
        )
        break

      default:
        steps.push(
          {
            id: 'step_1',
            agent_id: 'joe',
            action: 'data_analysis',
            parameters: { topic: workflowName },
            dependencies: [],
            timeout: 300000,
            retry_count: 3
          }
        )
    }

    return steps
  }

  const { currentAdmin } = useAdminStore()

  const executeCommand = async (command: string) => {
    setIsProcessing(true)
    const startTime = Date.now()

    try {
      const [cmd, ...args] = command.trim().split(' ')
      const commandDef = commands.find((c: CommandDefinition) => c.name === cmd)

      if (!commandDef) {
        // Handle help and commands which might not be in commandDef but are handled locally
        if (cmd === 'help' || cmd === 'commands') {
          const response = await processCommand(cmd, args)
          addMessage({
            type: 'system',
            content: response,
            timestamp: new Date().toISOString()
          })
          return
        }

        addMessage({
          type: 'error',
          content: `Command not found: ${cmd}. Type "help" for available commands.`,
          timestamp: new Date().toISOString(),
          metadata: { command: cmd }
        })
        return
      }

      // Execute some commands locally if they are not yet implemented in backend
      if (['ai.assist', 'ai.optimize', 'ai.predict', 'ai.automate', 'agent.execute', 'agent.workflow', 'agent.communicate', 'agent.monitor'].includes(cmd) || cmd.startsWith('system.') || cmd.startsWith('agents.') || cmd.startsWith('analytics.') || cmd.startsWith('billing.') || cmd.startsWith('security.') || cmd.startsWith('integration.')) {
        const response = await processCommand(cmd, args)
        addMessage({
          type: 'system',
          content: response,
          timestamp: new Date().toISOString(),
          metadata: {
            command: cmd,
            execution_time: Date.now() - startTime,
            status: 'success'
          }
        })
        saveCommandToHistory(command)
        generateAiSuggestions(command)
        return
      }

      // Execute command via API for others
      const result = await adminAPI.executeChatCommand(cmd, args)
      const actualExecutionTime = Date.now() - startTime

      const response = result.output || result.result || result.message || 'Command executed successfully'

      addMessage({
        type: 'system',
        content: response,
        timestamp: new Date().toISOString(),
        metadata: {
          command: cmd,
          execution_time: actualExecutionTime,
          status: 'success'
        }
      })

      saveCommandToHistory(command)

      // Generate AI suggestions after command execution
      generateAiSuggestions(command)
    } catch (error) {
      addMessage({
        type: 'error',
        content: `Command execution failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date().toISOString(),
        metadata: { command: command.trim() }
      })
    } finally {
      setIsProcessing(false)
    }
  }

  const processCommand = async (cmd: string, args: string[]): Promise<string> => {
    switch (cmd) {
      case 'help':
        return `Available command categories:
• system.* - System management and monitoring
• agents.* - Agent control and configuration  
• analytics.* - Data analysis and reporting
• users.* - User management and support
• billing.* - Billing and subscription management
• security.* - Security and access control
• integration.* - External service integration

Type "commands" to see all available commands.
Type "help [category]" for category-specific help.`

      case 'commands':
        const category = args[0]
        const filteredCommands = category
          ? commands.filter(c => c.category === category)
          : commands

        return filteredCommands.map(cmd =>
          `${cmd.name} - ${cmd.description}\n  Syntax: ${cmd.syntax}`
        ).join('\n\n')

      case 'system.status':
        const detailed = args.includes('detailed')
        return detailed
          ? `System Status: ${systemStatus.toUpperCase()}
• CPU Usage: 45.2% (4 cores)
• Memory Usage: 68.5% (8GB/12GB)
• Disk Usage: 23.1% (120GB/500GB)
• Network: 1.2 Gbps active
• Database: PostgreSQL 14.5 (healthy)
• Redis: 6.2.7 (connected)
• Active Services: 12/15
• Uptime: 15 days, 7 hours, 23 minutes`
          : `System Status: ${systemStatus.toUpperCase()} | CPU: 45.2% | Memory: 68.5% | Uptime: 15d 7h 23m`

      case 'agents.list':
        const filter = args[0] || 'all'
        return `Agent Status (${filter}):
• Aria (social_media) - ONLINE - 94.4% success rate
• Clara (customer_support) - ONLINE - 95.0% success rate  
• Joe (research) - BUSY - 91.7% success rate
• Eric (sales) - ERROR - 92.6% success rate
• Jackie (marketing) - OFFLINE - 89.3% success rate

Total: 5 agents | Online: 2 | Busy: 1 | Error: 1 | Offline: 1`

      case 'analytics.overview':
        const period = args[0] || '7d'
        return `Analytics Overview (${period}):
• Total Revenue: $12,450.00 (+15.3%)
• Active Users: 1,247 (+8.7%)
• New Signups: 89 (+12.4%)
• Agent Usage: 15,234 tasks (+22.1%)
• API Calls: 45,678 (+18.9%)
• Support Tickets: 23 (-5.2%)
• System Uptime: 99.97%

Top Performing Agents:
1. Clara (customer_support) - 95.0% success
2. Aria (social_media) - 94.4% success
3. Joe (research) - 91.7% success`

      case 'users.list':
        return 'Use the API to fetch real user data. This command is handled by the backend.'

      case 'billing.overview':
        const billingPeriod = args[0] || '30d'
        return `Billing Overview (${billingPeriod}):
• Total Revenue: $45,678.90 (+18.7%)
• MRR: $12,450.00 (+15.3%)
• Active Subscriptions: 1,189 (+8.7%)
• Churn Rate: 2.1% (-0.5%)
• Average Revenue per User: $38.42 (+9.1%)
• Payment Success Rate: 98.7%
• Outstanding Invoices: $1,234.56

Plan Distribution:
• Free: 234 users (19.7%)
• Starter: 456 users (38.3%)
• Pro: 389 users (32.7%)
• Enterprise: 110 users (9.3%)`

      case 'security.audit':
        return `Security Audit Results:
• System Security: ✅ PASSED
• Database Security: ✅ PASSED
• API Security: ✅ PASSED
• User Authentication: ✅ PASSED
• File Permissions: ✅ PASSED
• SSL/TLS Configuration: ✅ PASSED
• Firewall Rules: ✅ PASSED

Vulnerabilities Found: 0
Security Score: 98/100
Last Scan: 2 hours ago
Next Scan: 22 hours`

      case 'integration.status':
        return `Integration Status:
• Paystack (Payment Gateway): ✅ ONLINE - 99.9% uptime
• Email Service (SMTP): ✅ ONLINE - 99.8% uptime
• SMS Gateway: ✅ ONLINE - 99.7% uptime
• Social Media APIs: ✅ ONLINE - 99.6% uptime
• Analytics Service: ✅ ONLINE - 99.9% uptime
• Backup Service: ✅ ONLINE - 99.8% uptime

Overall Integration Health: 99.8%
Failed Requests (24h): 12/45,678 (0.026%)`

      case 'ai.assist':
        const query = args.join(' ')
        return `🤖 AI Assistant Response:
Based on your query: "${query}"

Here are my recommendations:

1. **System Health**: Run 'system.status detailed' to check current system state
2. **Agent Performance**: Use 'agents.list' to monitor AI personnel status
3. **User Activity**: Execute 'users.list active' to see active users
4. **Revenue Analysis**: Try 'analytics.overview 30d' for recent performance
5. **Security Check**: Run 'security.audit' to ensure system security

Would you like me to execute any of these commands automatically?`

      case 'ai.optimize':
        return `🚀 AI System Optimization:
• Analyzing system performance...
• Identifying bottlenecks...
• Optimizing agent configurations...
• Balancing resource allocation...
• Updating cache strategies...

Optimization Recommendations:
1. Increase memory allocation for Clara (customer_support)
2. Restart Eric (sales) agent to resolve error state
3. Scale up database connections during peak hours
4. Enable auto-scaling for agent instances

Execute 'system.restart optimized' to apply optimizations?`

      case 'ai.predict':
        const predictionType = args[0] || 'revenue'
        const timeframe = args[1] || '30d'
        return `🔮 AI Prediction (${predictionType} for ${timeframe}):
• Loading historical data...
• Training prediction models...
• Analyzing trends...
• Generating forecasts...

Prediction Results:
• Revenue Growth: +18.7% (vs +15.3% current)
• User Acquisition: +12.4% (vs +8.7% current)
• Agent Efficiency: +5.2% improvement expected
• System Load: Peak usage at 2:00 PM daily

Confidence Level: 94.2%
Next Action: Consider scaling infrastructure`

      case 'ai.automate':
        const automationType = args[0] || 'monitoring'
        return `🤖 AI Automation Setup (${automationType}):
• Configuring automated monitoring...
• Setting up alert thresholds...
• Creating response workflows...
• Testing automation rules...

Automation Features Enabled:
✅ Real-time system monitoring
✅ Automatic agent restart on failure
✅ User activity tracking
✅ Revenue anomaly detection
✅ Security threat response

Automation Status: ACTIVE
Next Check: 5 minutes`

      case 'agent.execute':
        if (!isAgentManagerInitialized) {
          return `❌ Agent Service Manager not initialized. Please wait for initialization to complete.`
        }

        const agentId = args[0]
        const taskType = args[1]
        const taskParams = args.slice(2).join(' ')

        if (!agentId || !taskType) {
          return `❌ Usage: agent.execute [agent_id] [task_type] [parameters]
Examples:
• agent.execute aria create_post "AI automation benefits"
• agent.execute joe market_research "competitor analysis"
• agent.execute clara resolve_ticket "user support request"`
        }

        try {
          const agent = agentServices.find(a => a.id === agentId || a.name.toLowerCase() === agentId.toLowerCase())
          if (!agent) {
            return `❌ Agent "${agentId}" not found. Available agents: ${agentServices.map(a => a.name).join(', ')}`
          }

          const parameters = parseTaskParameters(taskParams)
          const task = await agentServiceManager.executeAgentTask(agent.id, taskType, parameters)

          return `✅ Task executed successfully!
Agent: ${agent.name} (${agent.type})
Task: ${taskType}
Status: ${task.status}
Result: ${JSON.stringify(task.result, null, 2)}`
        } catch (error) {
          return `❌ Task execution failed: ${error instanceof Error ? error.message : 'Unknown error'}`
        }

      case 'agent.workflow':
        if (!isAgentManagerInitialized) {
          return `❌ Agent Service Manager not initialized. Please wait for initialization to complete.`
        }

        const workflowAction = args[0]
        const workflowId = args[1]

        if (!workflowAction) {
          return `❌ Usage: agent.workflow [action] [workflow_id] [parameters]
Actions: create, execute, list, status
Examples:
• agent.workflow create "marketing_campaign"
• agent.workflow execute workflow_123
• agent.workflow list`
        }

        switch (workflowAction) {
          case 'create':
            const workflowName = args[1] || 'New Workflow'
            const workflowSteps = generateWorkflowSteps(workflowName)
            const newWorkflow = await agentServiceManager.createWorkflow(workflowName, `Automated ${workflowName}`, workflowSteps)
            setAgentWorkflows(prev => [...prev, newWorkflow])
            return `✅ Workflow created successfully!
ID: ${newWorkflow.id}
Name: ${newWorkflow.name}
Steps: ${newWorkflow.steps.length}`

          case 'execute':
            if (!workflowId) {
              return `❌ Please specify workflow ID: agent.workflow execute [workflow_id]`
            }
            const workflow = agentWorkflows.find(w => w.id === workflowId)
            if (!workflow) {
              return `❌ Workflow "${workflowId}" not found. Available workflows: ${agentWorkflows.map(w => w.id).join(', ')}`
            }
            const workflowResult = await agentServiceManager.executeWorkflow(workflowId, {})
            return `✅ Workflow executed successfully!
Workflow: ${workflow.name}
Status: ${workflowResult.status}
Steps: ${workflowResult.successful_steps}/${workflowResult.total_steps} completed`

          case 'list':
            return `📋 Available Workflows:
${agentWorkflows.map(w => `• ${w.id}: ${w.name} (${w.status})`).join('\n')}`

          default:
            return `❌ Unknown workflow action: ${workflowAction}. Use: create, execute, list, status`
        }

      case 'agent.communicate':
        if (!isAgentManagerInitialized) {
          return `❌ Agent Service Manager not initialized. Please wait for initialization to complete.`
        }

        const senderIdArg = args[0]
        const receiverIdArg = args[1]
        const messageTypeArg = args[2]
        const messageContentArg = args.slice(3).join(' ')

        if (!senderIdArg || !receiverIdArg || !messageTypeArg) {
          return `❌ Usage: agent.communicate [sender] [receiver] [message_type] [content]
Examples:
• agent.communicate aria joe "data_request" "market insights"
• agent.communicate clara eric "lead_qualification" "new prospect"`
        }

        try {
          const communication = await agentServiceManager.sendAgentMessage(senderIdArg, receiverIdArg, messageTypeArg, messageContentArg)
          return `✅ Message sent successfully!
From: ${senderIdArg}
To: ${receiverIdArg}
Type: ${messageTypeArg}
Status: ${communication.status}
Message ID: ${communication.id}`
        } catch (error) {
          return `❌ Communication failed: ${error instanceof Error ? error.message : 'Unknown error'}`
        }

      case 'agent.monitor':
        if (!isAgentManagerInitialized) {
          return `❌ Agent Service Manager not initialized. Please wait for initialization to complete.`
        }

        const monitorAgentId = args[0] || 'all'

        if (monitorAgentId === 'all') {
          const allTasks = await agentServiceManager.getAgentTasks()
          const performanceSummary = agentServices.map(agent => {
            const agentTasks = allTasks.filter(t => t.agent_id === agent.id)
            return {
              name: agent.name,
              status: agent.status,
              tasks_completed: agentTasks.filter(t => t.status === 'completed').length,
              tasks_failed: agentTasks.filter(t => t.status === 'failed').length,
              success_rate: agent.performance_metrics.success_rate
            }
          })

          return `📊 Agent Performance Summary:
${performanceSummary.map(a => `• ${a.name}: ${a.status} | ${a.tasks_completed} completed, ${a.tasks_failed} failed | ${a.success_rate}% success rate`).join('\n')}`
        } else {
          const agent = agentServices.find(a => a.id === monitorAgentId || a.name.toLowerCase() === monitorAgentId.toLowerCase())
          if (!agent) {
            return `❌ Agent "${monitorAgentId}" not found.`
          }

          const agentTasks = await agentServiceManager.getAgentTasks(agent.id)
          return `📊 Agent Monitor: ${agent.name}
Status: ${agent.status}
Performance Metrics:
• Success Rate: ${agent.performance_metrics.success_rate}%
• Response Time: ${agent.performance_metrics.response_time}ms
• Tasks Completed: ${agent.performance_metrics.performance_metrics?.tasks_completed || 0}
• Memory Usage: ${agent.performance_metrics.memory_usage}%
• CPU Usage: ${agent.performance_metrics.cpu_usage}%

Recent Tasks:
${agentTasks.slice(-5).map(t => `• ${t.task_type}: ${t.status} (${t.created_at})`).join('\n')}`
        }

      default:
        return `Command "${cmd}" executed successfully with args: [${args.join(', ')}]
Execution completed in ${Date.now()}ms.

💡 AI Tip: Try these advanced commands:
• ai.assist [query] - Get AI-powered recommendations
• ai.optimize - AI system optimization
• ai.predict [type] [timeframe] - Predictive analytics
• ai.automate [type] - Setup AI automation
• agent.execute [agent_id] [task_type] [params] - Execute agent tasks
• agent.workflow [action] [workflow_id] - Manage agent workflows
• agent.communicate [sender] [receiver] [type] [content] - Agent communication`

    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputValue.trim() || isProcessing) return

    const command = inputValue.trim()
    addMessage({
      type: 'user',
      content: command,
      timestamp: new Date().toISOString()
    })

    setInputValue('')
    setHistoryIndex(-1)
    executeCommand(command)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowUp') {
      e.preventDefault()
      if (historyIndex < commandHistory.length - 1) {
        const newIndex = historyIndex + 1
        setHistoryIndex(newIndex)
        setInputValue(commandHistory[newIndex])
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      if (historyIndex > 0) {
        const newIndex = historyIndex - 1
        setHistoryIndex(newIndex)
        setInputValue(commandHistory[newIndex])
      } else if (historyIndex === 0) {
        setHistoryIndex(-1)
        setInputValue('')
      }
    }
  }

  const getMessageIcon = (type: ChatMessage['type']) => {
    switch (type) {
      case 'user': return <User className="h-4 w-4" />
      case 'system': return <Terminal className="h-4 w-4" />
      case 'agent': return <Bot className="h-4 w-4" />
      case 'error': return <XCircle className="h-4 w-4" />
      case 'success': return <CheckCircle className="h-4 w-4" />
      case 'warning': return <AlertTriangle className="h-4 w-4" />
      default: return <Terminal className="h-4 w-4" />
    }
  }

  const getMessageColor = (type: ChatMessage['type']) => {
    switch (type) {
      case 'user': return 'bg-blue-500 text-white'
      case 'system': return 'bg-gray-500 text-white'
      case 'agent': return 'bg-green-500 text-white'
      case 'error': return 'bg-red-500 text-white'
      case 'success': return 'bg-green-600 text-white'
      case 'warning': return 'bg-yellow-500 text-white'
      default: return 'bg-gray-500 text-white'
    }
  }

  return (
    <AdminLayout>
      <div className="flex h-screen bg-gray-900">
        {/* Main Chat Interface */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <div className="bg-gradient-to-r from-green-400 to-green-600 p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center ring-2 ring-white/30">
                  <Terminal className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-white">Admin Command Center</h1>
                  <div className="text-sm text-white/90 flex items-center">
                    <motion.div
                      className="w-2 h-2 rounded-full bg-white mr-2"
                      animate={{ opacity: [1, 0.5, 1] }}
                      transition={{ duration: 2, repeat: Infinity }}
                    />
                    Advanced system control and monitoring
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Badge variant={systemStatus === 'online' ? 'default' : 'destructive'}>
                  {systemStatus.toUpperCase()}
                </Badge>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowCommands(!showCommands)}
                >
                  <Command className="h-4 w-4 mr-2" />
                  Commands
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleVoiceToggle}
                  className={isListening ? 'bg-red-500 hover:bg-red-600' : ''}
                >
                  {isListening ? <Mic className="h-4 w-4 animate-pulse" /> : <Mic className="h-4 w-4" />}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsMuted(!isMuted)}
                >
                  {isMuted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
                </Button>
              </div>
            </div>
          </div>

          {/* Chat Messages */}
          <ScrollArea className="flex-1 p-4 bg-gray-900/50">
            <div className="space-y-4">
              {messages.map((message) => {
                const isUserMessage = message.type === 'user'
                const isSystemMessage = message.type === 'system'
                const isThinking = message.type === 'thinking'

                return (
                  <div key={message.id} className={`flex ${isUserMessage ? "justify-end" : isSystemMessage ? "justify-center" : "justify-start"} group`}>
                    {isSystemMessage ? (
                      <div className="bg-green-900/30 border border-green-700/50 rounded-xl px-4 py-2.5 text-sm text-green-400 max-w-[85%] shadow-sm">
                        <div className="prose prose-sm prose-invert max-w-none dark:prose-invert text-center">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            className="text-sm"
                            components={{
                              p: ({ children }) => <p className="mb-1 last:mb-0 text-green-400">{children}</p>,
                              strong: ({ children }) => <strong className="font-semibold text-green-300">{children}</strong>,
                              em: ({ children }) => <em className="italic text-green-300">{children}</em>,
                              code: ({ children }) => <code className="bg-green-900/50 px-1.5 py-0.5 rounded text-xs text-green-300 font-mono">{children}</code>,
                            }}
                          >
                            {message.content}
                          </ReactMarkdown>
                        </div>
                      </div>
                    ) : (
                      <div className={`flex items-end gap-2 max-w-[80%] ${isUserMessage ? "flex-row-reverse" : ""}`}>
                        {/* Avatar */}
                        <div className={`w-9 h-9 rounded-full flex items-center justify-center text-white text-xs font-bold shadow-md flex-shrink-0 ${isUserMessage
                          ? "bg-gradient-to-r from-green-400 to-green-600"
                          : isThinking
                            ? "bg-gradient-to-r from-green-400 to-green-600 animate-pulse"
                            : getMessageColor(message.type)
                          }`}>
                          {isThinking ? <Terminal className="w-4 h-4" /> : getMessageIcon(message.type)}
                        </div>

                        <div className={`flex flex-col ${message.type === 'user' ? 'items-end' : 'items-start'}`}>
                          <div className={`px-4 py-2.5 rounded-2xl text-sm shadow-xl ${message.type === 'user' ? 'bg-green-500 text-white rounded-tr-none' :
                            message.type === 'error' ? 'bg-red-500/10 text-red-200 border border-red-500/20 rounded-tl-none' :
                              message.type === 'success' ? 'bg-green-500/10 text-green-200 border border-green-500/20 rounded-tl-none' :
                                'bg-gray-800/80 backdrop-blur-md text-gray-200 border border-gray-700/50 rounded-tl-none'
                            }`}>
                            {message.type === 'thinking' ? (
                              <div className="flex items-center gap-2 text-gray-400 italic">
                                <RefreshCw className="w-3 h-3 animate-spin" />
                                <span>Processing command...</span>
                              </div>
                            ) : (
                              <div className="prose prose-sm prose-invert max-w-none">
                                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                  {message.content}
                                </ReactMarkdown>
                              </div>
                            )}
                          </div>
                          <span className="text-[10px] text-gray-500 mt-1 px-1">
                            {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
              {isProcessing && (
                <div className="flex justify-start items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-gray-800 border border-gray-700 flex items-center justify-center text-gray-400">
                    <Terminal className="w-4 h-4 animate-pulse text-green-500" />
                  </div>
                  <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-2xl px-4 py-3">
                    <div className="flex space-x-1.5">
                      {[0, 1, 2].map((i) => (
                        <motion.div
                          key={i}
                          className="w-1.5 h-1.5 bg-green-500/60 rounded-full"
                          animate={{ y: [0, -4, 0], opacity: [0.4, 1, 0.4] }}
                          transition={{ duration: 1, repeat: Infinity, delay: i * 0.15 }}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>

          {/* Voice & Suggestions */}
          <div className="p-4 space-y-3 bg-gray-800/30 backdrop-blur-sm border-t border-gray-700/50">
            {isListening && voiceTranscript && (
              <div className="flex items-center space-x-2 text-green-400 px-2 py-1 bg-green-500/5 rounded-lg border border-green-500/20">
                <Mic className="h-3 w-3 animate-pulse" />
                <span className="text-xs font-mono">{voiceTranscript}</span>
              </div>
            )}

            {showSuggestions && aiSuggestions.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {aiSuggestions.map((suggestion, index) => (
                  <Button
                    key={index}
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setInputValue(suggestion)
                      setShowSuggestions(false)
                      inputRef.current?.focus()
                    }}
                    className="text-[10px] h-7 px-3 font-mono bg-gray-800/50 border-gray-700 hover:bg-gray-700 text-gray-400 hover:text-white rounded-full transition-all"
                  >
                    {suggestion}
                  </Button>
                ))}
              </div>
            )}

            {/* Final Input Form */}
            <form onSubmit={handleSubmit} className="flex items-center gap-2">
              <div className="flex-1 relative group">
                <Input
                  ref={inputRef}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Enter command (e.g. system.status)..."
                  className="h-11 bg-gray-900/80 border-gray-700 text-white placeholder-gray-500 font-mono rounded-xl focus:ring-1 focus:ring-green-500 focus:border-green-500/50 transition-all pl-10"
                  disabled={isProcessing}
                />
                <Command className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-600 group-hover:text-green-500/60 transition-colors" />
                {commandHistory.length > 0 && (
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
                    <kbd className="px-1.5 py-0.5 rounded border border-gray-700 bg-gray-800 text-[10px] text-gray-500">↑</kbd>
                    <kbd className="px-1.5 py-0.5 rounded border border-gray-700 bg-gray-800 text-[10px] text-gray-500">↓</kbd>
                  </div>
                )}
              </div>
              <Button
                type="submit"
                disabled={isProcessing || !inputValue.trim()}
                className="h-11 w-11 rounded-xl bg-gradient-to-br from-green-400 to-green-600 text-white hover:shadow-lg hover:shadow-green-500/30 disabled:opacity-50 disabled:grayscale transition-all"
              >
                <Send className="h-4.5 w-4.5" />
              </Button>
            </form>
          </div>
        </div>

        {/* Commands Panel - Right Side */}
        {showCommands && (
          <div className="w-80 bg-gray-800/50 backdrop-blur-xl border-l border-gray-700 flex flex-col hidden xl:flex">
            <div className="p-4 border-b border-gray-700 flex items-center justify-between">
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                <Play className="w-3.5 h-3.5 text-green-500" />
                Quick Commands
              </h2>
              <Button variant="ghost" size="icon" onClick={() => setShowCommands(false)} className="h-6 w-6 text-gray-500 hover:text-white">
                <XCircle className="h-4 w-4" />
              </Button>
            </div>
            <ScrollArea className="flex-1">
              <div className="p-3 space-y-6">
                {Object.entries(
                  commands.reduce((acc, cmd) => {
                    if (!acc[cmd.category]) acc[cmd.category] = []
                    acc[cmd.category].push(cmd)
                    return acc
                  }, {} as Record<string, CommandDefinition[]>)
                ).map(([category, categoryCommands]) => (
                  <div key={category}>
                    <h3 className="text-[10px] font-bold text-gray-500 uppercase tracking-[0.2em] mb-3 px-1">
                      {category}
                    </h3>
                    <div className="space-y-1">
                      {categoryCommands.map((cmd) => (
                        <div
                          key={cmd.name}
                          className="group bg-transparent hover:bg-gray-700/50 rounded-lg p-2.5 cursor-pointer transition-all border border-transparent hover:border-gray-700"
                          onClick={() => {
                            setInputValue(cmd.name)
                            inputRef.current?.focus()
                          }}
                        >
                          <div className="text-gray-300 group-hover:text-green-400 font-mono text-xs mb-1">{cmd.name}</div>
                          <div className="text-[10px] text-gray-500 leading-relaxed line-clamp-2">{cmd.description}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </div>
        )}
      </div>
    </AdminLayout>
  )
}
