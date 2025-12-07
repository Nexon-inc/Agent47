'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Input } from '@/components/ui/input'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
import { adminAPI } from '@/lib/services/admin-api'
import { useAdminStore } from '@/lib/stores/admin-store'
import { usePolling } from '@/lib/hooks/use-polling'
import { 
  Activity, 
  Server, 
  Zap, 
  CheckCircle, 
  XCircle, 
  Clock,
  Settings,
  RefreshCw,
  Plus,
  Search,
  Wifi,
  Database,
  MessageSquare,
  BarChart3
} from 'lucide-react'

interface ServiceConfig {
  id: string
  agent_id: string
  service_name: string
  service_type: string
  endpoint: string
  protocol: string
  health_check_url: string
  status: 'online' | 'offline' | 'error' | 'maintenance'
  response_time_ms: number
  last_health_check: string
  error_count: number
  timeout_seconds: number
  retry_attempts: number
  rate_limit: number
}

interface Communication {
  id: string
  sender_agent_id: string
  receiver_agent_id: string
  message_type: string
  protocol: string
  status: 'pending' | 'sent' | 'failed' | 'delivered'
  timestamp: string
  retry_count: number
  content: string
}

interface IntegrationMetrics {
  total_services: number
  online_services: number
  total_communications: number
  successful_communications: number
  avg_response_time: number
  error_rate: number
}

export default function IntegrationAdminPage() {
  const [services, setServices] = useState<ServiceConfig[]>([])
  const [communications, setCommunications] = useState<Communication[]>([])
  const [metrics, setMetrics] = useState<IntegrationMetrics>({
    total_services: 0,
    online_services: 0,
    total_communications: 0,
    successful_communications: 0,
    avg_response_time: 0,
    error_rate: 0
  })
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')

  const { currentAdmin } = useAdminStore()
  const hasAccess = currentAdmin?.permissions?.includes("super_admin") || 
                    currentAdmin?.permissions?.includes("system_admin")

  const [overviewData, setOverviewData] = useState<any>(null)
  const [isLoadingOverview, setIsLoadingOverview] = useState(true)
  const [overviewError, setOverviewError] = useState<any>(null)

  // Load initial data
  useEffect(() => {
    if (!hasAccess) return
    
    const loadData = async () => {
      try {
        setIsLoadingOverview(true)
        const data = await adminAPI.getIntegrationsOverview()
        setOverviewData(data)
      } catch (err) {
        setOverviewError(err)
      } finally {
        setIsLoadingOverview(false)
      }
    }
    loadData()
  }, [hasAccess])

  // Subscribe to real-time integration updates via WebSocket
  useEffect(() => {
    if (!hasAccess) return

    const { websocketService } = require('@/lib/websocket-service')
    
    if (!websocketService.getConnectionStatus()) {
      websocketService.connect()
    }

    const unsubscribe = websocketService.subscribe('notification', (message) => {
      if (message.data?.type === 'integration_error' || message.data?.type === 'platform_update') {
        adminAPI.getIntegrationsOverview().then(setOverviewData).catch(setOverviewError)
      }
    })

    return () => unsubscribe()
  }, [hasAccess])

  useEffect(() => {
    setLoading(isLoadingOverview)
  }, [isLoadingOverview])

  useEffect(() => {
    if (overviewData) {
      // Map overview data to services format if available
      if (overviewData.services) {
        setServices(overviewData.services)
      }
      if (overviewData.communications) {
        setCommunications(overviewData.communications)
      }
      if (overviewData.metrics) {
        setMetrics(overviewData.metrics)
      }
    }
  }, [overviewData])

  useEffect(() => {
    if (overviewData) {
      if (overviewData.services && Array.isArray(overviewData.services)) {
        setServices(overviewData.services)
      }
      if (overviewData.communications && Array.isArray(overviewData.communications)) {
        setCommunications(overviewData.communications)
      }
      if (overviewData.metrics) {
        setMetrics(overviewData.metrics)
      } else if (overviewData.services && overviewData.communications) {
        // Calculate metrics from real data
        const calculatedMetrics: IntegrationMetrics = {
          total_services: overviewData.services.length,
          online_services: overviewData.services.filter((s: any) => s.status === 'online').length,
          total_communications: overviewData.communications.length,
          successful_communications: overviewData.communications.filter((c: any) => c.status === 'delivered').length,
          avg_response_time: overviewData.services.length > 0 
            ? overviewData.services.reduce((sum: number, s: any) => sum + (s.response_time_ms || 0), 0) / overviewData.services.length 
            : 0,
          error_rate: overviewData.communications.length > 0
            ? (overviewData.communications.filter((c: any) => c.status === 'failed').length / overviewData.communications.length) * 100
            : 0
        }
        setMetrics(calculatedMetrics)
      }
    }
  }, [overviewData])

  const filteredServices = services.filter(service => {
    const matchesSearch = service.service_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         service.service_type.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = statusFilter === 'all' || service.status === statusFilter
    return matchesSearch && matchesStatus
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'bg-green-500'
      case 'error': return 'bg-red-500'
      case 'offline': return 'bg-gray-500'
      case 'maintenance': return 'bg-blue-500'
      default: return 'bg-gray-500'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online': return <CheckCircle className="h-4 w-4" />
      case 'error': return <XCircle className="h-4 w-4" />
      case 'offline': return <XCircle className="h-4 w-4" />
      case 'maintenance': return <Settings className="h-4 w-4" />
      default: return <XCircle className="h-4 w-4" />
    }
  }

  const getProtocolIcon = (protocol: string) => {
    switch (protocol) {
      case 'http': return <Wifi className="h-4 w-4" />
      case 'kafka': return <MessageSquare className="h-4 w-4" />
      case 'redis': return <Database className="h-4 w-4" />
      default: return <Server className="h-4 w-4" />
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Integration Management</h1>
          <p className="text-muted-foreground">
            Monitor service integrations, communication protocols, and health status
          </p>
        </div>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Add Service
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Services</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.total_services}</div>
            <p className="text-xs text-muted-foreground">
              {metrics.online_services} online
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Communications</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.total_communications}</div>
            <p className="text-xs text-muted-foreground">
              {metrics.successful_communications} successful
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.avg_response_time.toFixed(0)}ms</div>
            <p className="text-xs text-muted-foreground">
              Across all services
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Error Rate</CardTitle>
            <XCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.error_rate.toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">
              Communication failures
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="services" className="space-y-4">
        <TabsList>
          <TabsTrigger value="services">Services</TabsTrigger>
          <TabsTrigger value="communications">Communications</TabsTrigger>
          <TabsTrigger value="protocols">Protocols</TabsTrigger>
          <TabsTrigger value="health">Health Monitoring</TabsTrigger>
        </TabsList>

        {/* Services Tab */}
        <TabsContent value="services" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Service Configurations</CardTitle>
                  <CardDescription>Monitor service endpoints and health status</CardDescription>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="relative">
                    <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search services..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10 w-64"
                    />
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {filteredServices.map(service => (
                  <div key={service.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-4">
                      <div className={`w-3 h-3 rounded-full ${getStatusColor(service.status)}`} />
                      <div>
                        <div className="flex items-center space-x-2">
                          {getStatusIcon(service.status)}
                          <h3 className="font-medium">{service.service_name}</h3>
                          <Badge variant="outline">{service.service_type}</Badge>
                          <Badge variant={service.status === 'online' ? 'default' : 'destructive'}>
                            {service.status}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">{service.endpoint}</p>
                        <div className="flex items-center space-x-4 mt-2">
                          <span className="text-sm">Protocol: {service.protocol}</span>
                          <span className="text-sm">Timeout: {service.timeout_seconds}s</span>
                          <span className="text-sm">Rate Limit: {service.rate_limit}/min</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="text-right">
                      <p className="text-sm font-medium">{service.response_time_ms}ms</p>
                      <p className="text-xs text-muted-foreground">
                        Last check: {new Date(service.last_health_check).toLocaleTimeString()}
                      </p>
                      {service.error_count > 0 && (
                        <p className="text-xs text-red-500">{service.error_count} errors</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Communications Tab */}
        <TabsContent value="communications" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Communication Logs</CardTitle>
              <CardDescription>Monitor inter-agent communications and message delivery</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {communications.map(comm => (
                  <div key={comm.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-4">
                      <div className={`w-3 h-3 rounded-full ${getStatusColor(comm.status)}`} />
                      <div>
                        <div className="flex items-center space-x-2">
                          {getProtocolIcon(comm.protocol)}
                          <h3 className="font-medium">{comm.message_type}</h3>
                          <Badge variant="outline">{comm.protocol}</Badge>
                          <Badge variant={comm.status === 'delivered' ? 'default' : 'destructive'}>
                            {comm.status}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">{comm.content}</p>
                        <p className="text-xs text-muted-foreground">
                          {comm.sender_agent_id} → {comm.receiver_agent_id} • {new Date(comm.timestamp).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    
                    <div className="text-right">
                      {comm.retry_count > 0 && (
                        <p className="text-xs text-orange-500">{comm.retry_count} retries</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Protocols Tab */}
        <TabsContent value="protocols" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>HTTP Protocol</CardTitle>
                <CardDescription>RESTful API communications</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Active Services</span>
                    <span className="text-sm font-medium">8</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Avg Response Time</span>
                    <span className="text-sm font-medium">245ms</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Success Rate</span>
                    <span className="text-sm font-medium">98.5%</span>
                  </div>
                  <Progress value={98.5} className="h-2" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Kafka Protocol</CardTitle>
                <CardDescription>Event-driven messaging</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Active Topics</span>
                    <span className="text-sm font-medium">12</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Messages/sec</span>
                    <span className="text-sm font-medium">1,245</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Success Rate</span>
                    <span className="text-sm font-medium">99.2%</span>
                  </div>
                  <Progress value={99.2} className="h-2" />
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Health Monitoring Tab */}
        <TabsContent value="health" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Health Monitoring</CardTitle>
              <CardDescription>Real-time health checks and performance metrics</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {services.map(service => (
                  <div key={service.id} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(service.status)}
                        <span className="font-medium">{service.service_name}</span>
                        <Badge variant={service.status === 'online' ? 'default' : 'destructive'}>
                          {service.status}
                        </Badge>
                      </div>
                      <span className="text-sm text-muted-foreground">
                        {service.response_time_ms}ms
                      </span>
                    </div>
                    <div className="flex space-x-2">
                      <Progress 
                        value={service.status === 'online' ? 100 : 0} 
                        className="flex-1 h-2" 
                      />
                      <Progress 
                        value={Math.min((service.response_time_ms / 1000) * 100, 100)} 
                        className="flex-1 h-2" 
                      />
                    </div>
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>Health</span>
                      <span>Performance</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
