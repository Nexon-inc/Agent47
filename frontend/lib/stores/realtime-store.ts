import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'

export interface SystemStatus {
  servers: {
    [key: string]: {
      status: 'online' | 'offline' | 'warning'
      cpu: number
      memory: number
      disk: number
      uptime: number
    }
  }
  database: {
    status: 'healthy' | 'warning' | 'error'
    connections: number
    queries_per_second: number
  }
  alerts: {
    critical: number
    warning: number
    info: number
  }
}

export interface Notification {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  title: string
  message: string
  timestamp: string
  read: boolean
  action_url?: string
}

export interface RealTimeMetrics {
  active_users: number
  total_requests: number
  error_rate: number
  response_time: number
}

interface RealTimeState {
  // Connection status
  isConnected: boolean
  connectionStatus: 'connected' | 'disconnected' | 'connecting'
  
  // System status
  systemStatus: SystemStatus | null
  
  // Notifications
  notifications: Notification[]
  unreadCount: number
  
  // Real-time metrics
  metrics: RealTimeMetrics | null
  
  // Live data
  liveAlerts: any[]
  liveUsers: any[]
  livePayments: any[]
  
  // Actions
  connect: () => void
  disconnect: () => void
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => void
  markNotificationAsRead: (id: string) => void
  markAllNotificationsAsRead: () => void
  removeNotification: (id: string) => void
  updateSystemStatus: (status: SystemStatus) => void
  updateMetrics: (metrics: RealTimeMetrics) => void
  addLiveAlert: (alert: any) => void
  addLiveUser: (user: any) => void
  addLivePayment: (payment: any) => void
  clearLiveData: () => void
}

export const useRealTimeStore = create<RealTimeState>()(
  subscribeWithSelector((set, get) => ({
    // Initial state
    isConnected: false,
    connectionStatus: 'disconnected',
    systemStatus: null,
    notifications: [],
    unreadCount: 0,
    metrics: null,
    liveAlerts: [],
    liveUsers: [],
    livePayments: [],

    // Actions
    connect: () => {
      set({ connectionStatus: 'connecting' })
      
      // Use centralized WebSocket service
      const connectWebSocket = async () => {
        try {
          const { websocketService } = await import('@/lib/websocket-service')
          
          // Ensure WebSocket is connected
          if (!websocketService.getConnectionStatus()) {
            await websocketService.connect()
          }
          
          // Subscribe to system status updates
          const unsubscribeStatus = websocketService.subscribe('system_status', (message) => {
            if (message.data && message.data.components) {
              const status = message.data
              
              // Transform backend health data to frontend format
              const systemStatus: SystemStatus = {
                servers: {
                  'api-server': {
                    status: status.status === 'healthy' ? 'online' : status.status === 'degraded' ? 'warning' : 'offline',
                    cpu: 0,
                    memory: 0,
                    disk: 0,
                    uptime: 0
                  }
                },
                database: {
                  status: status.components?.supabase === 'healthy' ? 'healthy' : status.components?.supabase === 'unhealthy' ? 'error' : 'warning',
                  connections: 0,
                  queries_per_second: 0
                },
                alerts: {
                  critical: 0,
                  warning: status.status === 'degraded' ? 1 : 0,
                  info: 0
                }
              }
              
              get().updateSystemStatus(systemStatus)
              
              get().updateMetrics({
                active_users: 0,
                total_requests: 0,
                error_rate: status.status === 'unhealthy' ? 1 : 0,
                response_time: 0
              })
            }
          })
          
          // Subscribe to notifications
          const unsubscribeNotification = websocketService.subscribe('notification', (message) => {
            get().addNotification({
              type: message.data?.type || 'info',
              title: message.data?.title || 'Notification',
              message: message.data?.message || '',
              action_url: message.data?.action_url
            })
          })
          
          // Subscribe to alerts
          const unsubscribeAlert = websocketService.subscribe('alert', (message) => {
            get().addLiveAlert(message.data)
          })
          
          // Subscribe to connection status changes
          const unsubscribeConnection = websocketService.onConnectionChange((connected) => {
            set({
              isConnected: connected,
              connectionStatus: connected ? 'connected' : 'disconnected'
            })
          })
          
          // Store unsubscribe functions for cleanup
          if (typeof window !== 'undefined') {
            (window as any).__realtimeUnsubscribe = () => {
              unsubscribeStatus()
              unsubscribeNotification()
              unsubscribeAlert()
              unsubscribeConnection()
            }
          }
          
          // Update connection status
          set({
            isConnected: websocketService.getConnectionStatus(),
            connectionStatus: websocketService.getConnectionStatus() ? 'connected' : 'disconnected'
          })
          
        } catch (error) {
          console.error('WebSocket connection failed, falling back to polling:', error)
          connectPolling()
        }
      }
      
      // Fallback polling connection
      const connectPolling = () => {
        const fetchSystemStatus = async () => {
          try {
            const { apiClient } = await import('@/lib/api-client')
            const status = await apiClient.getSystemStatus()
            
            if (status && status.components) {
              const systemStatus: SystemStatus = {
                servers: {
                  'api-server': {
                    status: status.status === 'healthy' ? 'online' : status.status === 'degraded' ? 'warning' : 'offline',
                    cpu: 0,
                    memory: 0,
                    disk: 0,
                    uptime: 0
                  }
                },
                database: {
                  status: status.components.supabase === 'healthy' ? 'healthy' : status.components.supabase === 'unhealthy' ? 'error' : 'warning',
                  connections: 0,
                  queries_per_second: 0
                },
                alerts: {
                  critical: 0,
                  warning: status.status === 'degraded' ? 1 : 0,
                  info: 0
                }
              }
              
              get().updateSystemStatus(systemStatus)
              
              get().updateMetrics({
                active_users: 0,
                total_requests: 0,
                error_rate: status.status === 'unhealthy' ? 1 : 0,
                response_time: 0
              })
              
              set({ 
                isConnected: true, 
                connectionStatus: 'connected' 
              })
            }
          } catch (error) {
            console.error('Failed to fetch system status:', error)
            set({ connectionStatus: 'disconnected' })
          }
        }
        
        // Initial fetch
        fetchSystemStatus()
        
        // Poll every 30 seconds for updates
        const intervalId = setInterval(fetchSystemStatus, 30000)
        
        // Store interval ID for cleanup
        if (typeof window !== 'undefined') {
          (window as any).__realtimeInterval = intervalId
        }
      }
      
      // Try WebSocket first
      connectWebSocket()
    },

    disconnect: () => {
      // Cleanup WebSocket subscriptions
      if (typeof window !== 'undefined' && (window as any).__realtimeUnsubscribe) {
        (window as any).__realtimeUnsubscribe()
        delete (window as any).__realtimeUnsubscribe
      }
      
      // Clear polling interval (fallback)
      if (typeof window !== 'undefined' && (window as any).__realtimeInterval) {
        clearInterval((window as any).__realtimeInterval)
        delete (window as any).__realtimeInterval
      }
      
      set({ 
        isConnected: false, 
        connectionStatus: 'disconnected',
        systemStatus: null,
        metrics: null
      })
    },

    addNotification: (notification) => {
      const newNotification: Notification = {
        ...notification,
        id: Math.random().toString(36).substring(2),
        timestamp: new Date().toISOString(),
        read: false
      }

      set(state => ({
        notifications: [newNotification, ...state.notifications],
        unreadCount: state.unreadCount + 1
      }))

      // Auto-remove notifications after 10 seconds
      setTimeout(() => {
        get().removeNotification(newNotification.id)
      }, 10000)
    },

    markNotificationAsRead: (id) => {
      set(state => ({
        notifications: state.notifications.map(notification =>
          notification.id === id 
            ? { ...notification, read: true }
            : notification
        ),
        unreadCount: Math.max(0, state.unreadCount - 1)
      }))
    },

    markAllNotificationsAsRead: () => {
      set(state => ({
        notifications: state.notifications.map(notification => ({
          ...notification,
          read: true
        })),
        unreadCount: 0
      }))
    },

    removeNotification: (id) => {
      set(state => {
        const notification = state.notifications.find(n => n.id === id)
        return {
          notifications: state.notifications.filter(n => n.id !== id),
          unreadCount: notification && !notification.read 
            ? Math.max(0, state.unreadCount - 1) 
            : state.unreadCount
        }
      })
    },

    updateSystemStatus: (status) => {
      set({ systemStatus: status })
    },

    updateMetrics: (metrics) => {
      set({ metrics })
    },

    addLiveAlert: (alert) => {
      set(state => ({
        liveAlerts: [alert, ...state.liveAlerts.slice(0, 49)] // Keep last 50
      }))
    },

    addLiveUser: (user) => {
      set(state => ({
        liveUsers: [user, ...state.liveUsers.slice(0, 49)] // Keep last 50
      }))
    },

    addLivePayment: (payment) => {
      set(state => ({
        livePayments: [payment, ...state.livePayments.slice(0, 49)] // Keep last 50
      }))
    },

    clearLiveData: () => {
      set({
        liveAlerts: [],
        liveUsers: [],
        livePayments: []
      })
    }
  }))
)

// Subscribe to store changes for debugging
if (process.env.NODE_ENV === 'development') {
  useRealTimeStore.subscribe(
    (state) => state.connectionStatus,
    (status) => console.log('WebSocket status changed:', status)
  )

  useRealTimeStore.subscribe(
    (state) => state.notifications,
    (notifications) => console.log('Notifications updated:', notifications.length)
  )
}
