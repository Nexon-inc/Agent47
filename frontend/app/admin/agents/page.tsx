'use client'

import { useState, useEffect, useRef } from 'react'
import AdminLayout from '@/components/admin/layout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Input } from '@/components/ui/input'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
import { useAdminStore } from '@/lib/stores/admin-store'
import { adminAPI } from '@/lib/services/admin-api'
import { 
  Activity, 
  Users, 
  Server, 
  Zap, 
  CheckCircle, 
  XCircle, 
  Clock,
  Settings,
  Play,
  Pause,
  RefreshCw,
  Plus,
  Search,
  MessageSquare,
  Send,
  Bot
} from 'lucide-react'

interface Agent {
  id: string
  name: string
  type: string
  status: 'online' | 'offline' | 'busy' | 'error' | 'maintenance'
  capabilities: string[]
  metrics: {
    total_tasks: number
    completed_tasks: number
    failed_tasks: number
    success_rate: number
    active_tasks: number
    avg_response_time: number
    memory_usage: number
    cpu_usage: number
  }
  last_activity: string
  version: string
  description: string
  is_active: boolean
}

export default function AgentsAdminPage() {
  const { currentAdmin } = useAdminStore()
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')

  // Check permissions
  const hasAccess = currentAdmin?.permissions?.includes("super_admin") || 
                    currentAdmin?.permissions?.includes("system_admin")

  const fetchData = async () => {
    if (!hasAccess) return
    
    setLoading(true)
    try {
      const response = await adminAPI.getAgents()
      if (response && response.agents) {
        const formattedAgents: Agent[] = response.agents.map((agent: any) => ({
          id: agent.id || agent.name,
          name: agent.name,
          type: agent.type || agent.agent_type || 'general',
          status: agent.status || (agent.is_active ? 'online' : 'offline'),
          capabilities: agent.capabilities || [],
          metrics: {
            total_tasks: agent.metrics?.total_tasks || 0,
            completed_tasks: agent.metrics?.completed_tasks || 0,
            failed_tasks: agent.metrics?.failed_tasks || 0,
            success_rate: agent.metrics?.success_rate || 0,
            active_tasks: agent.metrics?.active_tasks || 0,
            avg_response_time: agent.metrics?.avg_response_time || 0,
            memory_usage: agent.metrics?.memory_usage || 0,
            cpu_usage: agent.metrics?.cpu_usage || 0
          },
          last_activity: agent.last_activity || new Date().toISOString(),
          version: agent.version || '1.0.0',
          description: agent.description || '',
          is_active: agent.is_active !== false
        }))
        setAgents(formattedAgents)
      } else {
        setAgents([])
      }
    } catch (error) {
      console.error('Failed to fetch agents data:', error)
      setAgents([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [hasAccess])

  // Subscribe to real-time agent updates via WebSocket
  useEffect(() => {
    if (!hasAccess) return

    const { websocketService } = require('@/lib/websocket-service')
    
    if (!websocketService.getConnectionStatus()) {
      websocketService.connect()
    }

    // Reload agents when task updates or agent responses occur
    const unsubscribeTask = websocketService.subscribe('task_update', () => {
      fetchData()
    })

    const unsubscribeAgent = websocketService.subscribe('agent_response', () => {
      fetchData()
    })

    // Also reload on system status updates
    const unsubscribeSystem = websocketService.subscribe('system_status', () => {
      fetchData()
    })

    return () => {
      unsubscribeTask()
      unsubscribeAgent()
      unsubscribeSystem()
    }
  }, [hasAccess])

  const filteredAgents = agents.filter(agent => {
    const matchesSearch = agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         agent.type.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = statusFilter === 'all' || agent.status === statusFilter
    return matchesSearch && matchesStatus
  })

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online': return <CheckCircle className="h-4 w-4" />
      case 'busy': return <Clock className="h-4 w-4" />
      case 'error': return <XCircle className="h-4 w-4" />
      case 'offline': return <XCircle className="h-4 w-4" />
      case 'maintenance': return <Settings className="h-4 w-4" />
      default: return <XCircle className="h-4 w-4" />
    }
  }

  const totalAgents = agents.length
  const onlineAgents = agents.filter(a => a.status === 'online').length
  const errorAgents = agents.filter(a => a.status === 'error').length
  const totalTasks = agents.reduce((sum, agent) => sum + agent.metrics.total_tasks, 0)
  const avgSuccessRate = agents.length > 0 
    ? agents.reduce((sum, agent) => sum + agent.metrics.success_rate, 0) / agents.length 
    : 0

  if (!hasAccess) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Activity className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-white">Access Denied</h3>
            <p className="mt-1 text-sm text-gray-500">You don't have permission to access agents.</p>
          </div>
        </div>
      </AdminLayout>
    )
  }

  if (loading) {
    return (
      <AdminLayout>
      <div className="flex items-center justify-center h-64">
          <div className="text-gray-400">Loading agents...</div>
      </div>
      </AdminLayout>
    )
  }

  return (
    <AdminLayout>
    <div className="space-y-6">
      {/* Header */}
        <div>
        <h1 className="text-3xl font-bold text-white mb-2">Agent Management</h1>
        <p className="text-gray-400">Monitor and manage your AI agents</p>
      </div>

      <Tabs defaultValue="agents" className="w-full">
        <TabsList className="bg-gray-900/50 border-gray-800">
          <TabsTrigger value="agents" className="data-[state=active]:bg-gray-800 data-[state=active]:text-white text-gray-400">
            <Activity className="h-4 w-4 mr-2" />
            Agents
          </TabsTrigger>
          <TabsTrigger value="chat" className="data-[state=active]:bg-gray-800 data-[state=active]:text-white text-gray-400">
            <MessageSquare className="h-4 w-4 mr-2" />
            Chat with Agents
          </TabsTrigger>
        </TabsList>

        <TabsContent value="agents" className="space-y-6">
      {/* Stats Cards */}
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            <Card className="bg-gray-900/50 border-gray-800 p-6 hover:border-green-500/50 transition-colors">
              <div className="flex items-center justify-between mb-4">
                <Bot className="w-8 h-8 text-green-500" />
                <span className="text-sm text-gray-400">Total</span>
              </div>
              <div className="text-3xl font-bold text-white">{totalAgents}</div>
              <div className="text-sm text-gray-400 mt-2">{onlineAgents} online, {errorAgents} errors</div>
        </Card>
        
            <Card className="bg-gray-900/50 border-gray-800 p-6 hover:border-green-500/50 transition-colors">
              <div className="flex items-center justify-between mb-4">
                <Activity className="w-8 h-8 text-green-500" />
                <span className="text-sm text-gray-400">Tasks</span>
              </div>
              <div className="text-3xl font-bold text-white">{totalTasks}</div>
              <div className="text-sm text-gray-400 mt-2">{avgSuccessRate.toFixed(1)}% success rate</div>
        </Card>
        
            <Card className="bg-gray-900/50 border-gray-800 p-6 hover:border-blue-500/50 transition-colors">
              <div className="flex items-center justify-between mb-4">
                <Server className="w-8 h-8 text-blue-500" />
                <span className="text-sm text-gray-400">Services</span>
              </div>
              <div className="text-3xl font-bold text-white">{agents.filter(a => a.status === 'online').length}</div>
              <div className="text-sm text-gray-400 mt-2">Active services</div>
        </Card>
        
            <Card className="bg-gray-900/50 border-gray-800 p-6 hover:border-yellow-500/50 transition-colors">
              <div className="flex items-center justify-between mb-4">
                <Zap className="w-8 h-8 text-yellow-500" />
                <span className="text-sm text-gray-400">Performance</span>
              </div>
              <div className="text-3xl font-bold text-white">{avgSuccessRate.toFixed(0)}%</div>
              <div className="text-sm text-gray-400 mt-2">Average success rate</div>
        </Card>
      </div>

      {/* Agents List */}
          <Card className="bg-gray-900/50 border-gray-800">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
                  <CardTitle className="text-white">Agent Status</CardTitle>
                  <CardDescription className="text-gray-400">Monitor and manage your AI agents</CardDescription>
            </div>
            <div className="flex items-center space-x-4">
              <div className="relative">
                    <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search agents..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10 w-64 bg-gray-800 border-gray-700 text-white"
                />
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
                {filteredAgents.length === 0 ? (
                  <div className="text-center py-12">
                    <Bot className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-gray-300 mb-2">No agents found</h3>
                    <p className="text-gray-500">No agents match your search criteria</p>
                  </div>
                ) : (
                  filteredAgents.map(agent => (
                    <div key={agent.id} className="flex items-center justify-between p-4 border border-gray-800 rounded-lg bg-gray-800/50 hover:bg-gray-800 transition-colors">
                <div className="flex items-center space-x-4">
                  <div className={`w-3 h-3 rounded-full ${getStatusColor(agent.status)}`} />
                  <div>
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(agent.status)}
                            <h3 className="font-medium text-white">{agent.name}</h3>
                            <Badge variant="outline" className="border-gray-700 text-gray-300">{agent.type}</Badge>
                      <Badge variant={agent.status === 'online' ? 'default' : 'destructive'}>
                        {agent.status}
                      </Badge>
                    </div>
                          <p className="text-sm text-gray-400">{agent.description}</p>
                          <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                            <span>Tasks: {agent.metrics.total_tasks}</span>
                            <span>Success: {agent.metrics.success_rate}%</span>
                            <span>Response: {agent.metrics.avg_response_time}ms</span>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                        <Button variant="outline" size="sm" className="border-gray-700 text-gray-300 hover:bg-gray-700">
                    <Settings className="h-4 w-4 mr-2" />
                    Configure
                  </Button>
                        <Button 
                          variant="outline" 
                          size="sm" 
                          className="border-gray-700 text-gray-300 hover:bg-gray-700"
                          onClick={async () => {
                            try {
                              await adminAPI.restartAgent(agent.name)
                            } catch (error) {
                              console.error('Failed to restart agent:', error)
                            }
                          }}
                        >
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Restart
                  </Button>
                </div>
              </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="chat" className="space-y-6">
          <AgentChatInterface agents={agents} />
        </TabsContent>
      </Tabs>
      </div>
    </AdminLayout>
  )
}

// Helper functions for status
const getStatusColor = (status: string) => {
  switch (status) {
    case 'online': return 'bg-green-500'
    case 'busy': return 'bg-yellow-500'
    case 'error': return 'bg-red-500'
    case 'offline': return 'bg-gray-500'
    case 'maintenance': return 'bg-blue-500'
    default: return 'bg-gray-500'
  }
}

// Agent Chat Interface Component
function AgentChatInterface({ agents }: { agents: Agent[] }) {
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)
  const [messages, setMessages] = useState<Array<{id: string, type: 'user' | 'agent' | 'system', content: string, timestamp: Date, agentId?: string, imageUrl?: string}>>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { currentAdmin } = useAdminStore()
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !selectedAgent || isLoading) return

    const userMessage = {
      id: Date.now().toString(),
      type: 'user' as const,
      content: inputMessage,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)

    try {
      const sessionId = `admin_${currentAdmin?.user_id || 'admin'}_${selectedAgent.id}_${Date.now()}`
      const endpoint = `${API_BASE_URL}/api/agents/${selectedAgent.id}/${selectedAgent.id}-chat/message`
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
        },
        body: JSON.stringify({
          message: userMessage.content,
          session_id: sessionId
        })
      })

      if (response.ok) {
        const data = await response.json()
        if (data.success && data.data) {
          // Add thinking steps if available
          if (data.data.thinking_steps && Array.isArray(data.data.thinking_steps)) {
            data.data.thinking_steps.forEach((step: string, index: number) => {
              setMessages(prev => [...prev, {
                id: `thinking-${Date.now()}-${index}`,
                type: 'system',
                content: `💭 ${step}`,
                timestamp: new Date(),
                agentId: selectedAgent.id
              }])
            })
          }

          // Extract image URL if present
          const imageUrl = data.data.image_url || data.image_url

          // Add agent response
          const agentMessage = {
            id: (Date.now() + 1).toString(),
            type: 'agent' as const,
            content: data.data.response || data.data.message || 'No response received',
            timestamp: new Date(),
            agentId: selectedAgent.id,
            imageUrl: imageUrl  // Include image URL if present
          }
          setMessages(prev => [...prev, agentMessage])
        } else {
          throw new Error(data.message || 'Failed to get response')
        }
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
    } catch (error) {
      console.error('Failed to send message:', error)
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        type: 'system' as const,
        content: `❌ Error: ${error instanceof Error ? error.message : 'Failed to send message'}`,
        timestamp: new Date(),
        agentId: selectedAgent.id
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Agent List */}
      <Card className="bg-gray-900/50 border-gray-800 lg:col-span-1">
        <CardHeader>
          <CardTitle className="text-white">Select Agent</CardTitle>
          <CardDescription className="text-gray-400">Choose an agent to chat with</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 max-h-[600px] overflow-y-auto scrollbar-hide">
            {agents.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <Bot className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>No agents available</p>
              </div>
            ) : (
              agents.map(agent => (
                <button
                  key={agent.id}
                  onClick={() => {
                    setSelectedAgent(agent)
                    setMessages([])
                  }}
                  className={`w-full p-3 rounded-lg border transition-colors text-left ${
                    selectedAgent?.id === agent.id
                      ? 'bg-green-600/20 border-green-500 text-white'
                      : 'bg-gray-800/50 border-gray-700 text-gray-300 hover:bg-gray-800'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-3 h-3 rounded-full ${getStatusColor(agent.status)}`} />
                    <div className="flex-1">
                      <div className="font-medium">{agent.name}</div>
                      <div className="text-xs text-gray-400">{agent.type}</div>
                    </div>
                    {agent.status === 'online' && (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    )}
                  </div>
                </button>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {/* Chat Interface */}
      <Card className="bg-gray-900/50 border-gray-800 lg:col-span-2 flex flex-col">
        <CardHeader>
          <CardTitle className="text-white">
            {selectedAgent ? `Chat with ${selectedAgent.name}` : 'Select an agent to start chatting'}
          </CardTitle>
          {selectedAgent && (
            <CardDescription className="text-gray-400">
              {selectedAgent.description}
            </CardDescription>
          )}
        </CardHeader>
        <CardContent className="flex-1 flex flex-col min-h-[600px]">
          {selectedAgent ? (
            <>
              {/* Messages */}
              <div className="flex-1 overflow-y-auto space-y-4 mb-4 scrollbar-hide">
                {messages.length === 0 ? (
                  <div className="text-center py-12 text-gray-400">
                    <MessageSquare className="w-12 h-12 mx-auto mb-2 opacity-50" />
                    <p>Start a conversation with {selectedAgent.name}</p>
                  </div>
                ) : (
                  messages.map(msg => (
                    <div
                      key={msg.id}
                      className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[80%] rounded-lg px-4 py-2 ${
                          msg.type === 'user'
                            ? 'bg-green-600 text-white'
                            : msg.type === 'system'
                            ? 'bg-gray-800 text-gray-300 border border-gray-700'
                            : 'bg-gray-800 text-white'
                        }`}
                      >
                        {msg.type === 'system' && msg.content.includes('💭') ? (
                          <div className="text-sm">{msg.content}</div>
                        ) : (
                          <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
                        )}
                        
                        {/* Display generated images */}
                        {msg.imageUrl && (
                          <div className="mt-3 rounded-lg overflow-hidden border border-gray-600 max-w-md">
                            <img
                              src={msg.imageUrl}
                              alt="Generated image"
                              className="w-full h-auto"
                              onError={(e) => {
                                // Fallback to link if image fails to load
                                e.currentTarget.style.display = 'none'
                                const link = e.currentTarget.nextElementSibling as HTMLElement
                                if (link) link.style.display = 'block'
                              }}
                            />
                            <a
                              href={msg.imageUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="hidden text-green-400 hover:text-green-300 flex items-center space-x-2 p-2 bg-gray-700 text-sm"
                            >
                              <span>View Image</span>
                            </a>
                          </div>
                        )}
                        
                        <div className="text-xs opacity-70 mt-1">
                          {msg.timestamp.toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  ))
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <div className="flex gap-2 border-t border-gray-800 pt-4">
                <Input
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
                  placeholder="Type your message..."
                  className="flex-1 bg-gray-800 border-gray-700 text-white"
                  disabled={isLoading}
                />
                <Button
                  onClick={handleSendMessage}
                  disabled={!inputMessage.trim() || isLoading}
                  className="bg-green-600 hover:bg-green-700"
                >
                  {isLoading ? (
                    <RefreshCw className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center text-gray-400">
                <MessageSquare className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p>Select an agent from the list to start chatting</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
