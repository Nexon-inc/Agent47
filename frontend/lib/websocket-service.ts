/**
 * Centralized WebSocket Service
 * Provides real-time updates for all components including team chat, notifications, system status, etc.
 */

import { apiClient } from './api-client'

export type WebSocketMessageType = 
  | 'system_status'
  | 'team_chat_message'
  | 'notification'
  | 'alert'
  | 'agent_response'
  | 'task_update'
  | 'pong'

export interface WebSocketMessage {
  type: WebSocketMessageType
  data?: any
  timestamp?: string
}

type MessageHandler = (message: WebSocketMessage) => void
type ConnectionHandler = (connected: boolean) => void

class WebSocketService {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 10
  private reconnectDelay = 1000
  private reconnectTimer: NodeJS.Timeout | null = null
  private messageHandlers: Map<WebSocketMessageType, Set<MessageHandler>> = new Map()
  private connectionHandlers: Set<ConnectionHandler> = new Set()
  private isConnecting = false
  private isConnected = false
  private heartbeatInterval: NodeJS.Timeout | null = null
  private readonly heartbeatIntervalMs = 30000 // 30 seconds

  /**
   * Connect to WebSocket server
   */
  async connect(): Promise<void> {
    if (this.isConnecting || this.isConnected) {
      return
    }

    this.isConnecting = true

    try {
      const token = apiClient.getToken()
      if (!token) {
        console.warn('No authentication token available for WebSocket connection')
        this.isConnecting = false
        return
      }

      const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const wsProtocol = apiBaseUrl.startsWith('https') ? 'wss:' : 'ws:'
      const wsUrl = `${wsProtocol}//${apiBaseUrl.replace(/^https?:\/\//, '')}/api/realtime/ws?token=${encodeURIComponent(token)}`

      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.isConnected = true
        this.isConnecting = false
        this.reconnectAttempts = 0
        this.notifyConnectionHandlers(true)
        this.startHeartbeat()
      }

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          this.handleMessage(message)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        this.isConnecting = false
      }

      this.ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason)
        this.isConnected = false
        this.isConnecting = false
        this.notifyConnectionHandlers(false)
        this.stopHeartbeat()

        // Attempt to reconnect if not a clean close
        if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect()
        }
      }
    } catch (error) {
      console.error('Failed to connect WebSocket:', error)
      this.isConnecting = false
      this.scheduleReconnect()
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    this.stopHeartbeat()

    if (this.ws) {
      this.ws.close(1000, 'Client disconnect')
      this.ws = null
    }

    this.isConnected = false
    this.isConnecting = false
    this.notifyConnectionHandlers(false)
  }

  /**
   * Subscribe to messages of a specific type
   */
  subscribe(messageType: WebSocketMessageType, handler: MessageHandler): () => void {
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, new Set())
    }
    this.messageHandlers.get(messageType)!.add(handler)

    // Return unsubscribe function
    return () => {
      const handlers = this.messageHandlers.get(messageType)
      if (handlers) {
        handlers.delete(handler)
        if (handlers.size === 0) {
          this.messageHandlers.delete(messageType)
        }
      }
    }
  }

  /**
   * Subscribe to connection status changes
   */
  onConnectionChange(handler: ConnectionHandler): () => void {
    this.connectionHandlers.add(handler)
    
    // Immediately notify of current status
    handler(this.isConnected)

    // Return unsubscribe function
    return () => {
      this.connectionHandlers.delete(handler)
    }
  }

  /**
   * Send a message through WebSocket
   */
  send(message: any): void {
    if (this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(message))
      } catch (error) {
        console.error('Failed to send WebSocket message:', error)
      }
    } else {
      console.warn('WebSocket is not connected. Message not sent:', message)
    }
  }

  /**
   * Get current connection status
   */
  getConnectionStatus(): boolean {
    return this.isConnected
  }

  /**
   * Handle incoming message
   */
  private handleMessage(message: WebSocketMessage): void {
    // Notify handlers for this specific message type
    const handlers = this.messageHandlers.get(message.type)
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(message)
        } catch (error) {
          console.error(`Error in message handler for ${message.type}:`, error)
        }
      })
    }

    // Also notify handlers subscribed to 'all' messages (if we add that feature)
    // For now, we handle specific types only
  }

  /**
   * Notify all connection handlers
   */
  private notifyConnectionHandlers(connected: boolean): void {
    this.connectionHandlers.forEach(handler => {
      try {
        handler(connected)
      } catch (error) {
        console.error('Error in connection handler:', error)
      }
    })
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      return
    }

    this.reconnectAttempts++
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000)

    console.log(`Scheduling WebSocket reconnect attempt ${this.reconnectAttempts} in ${delay}ms`)

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null
      if (!this.isConnected && !this.isConnecting) {
        this.connect()
      }
    }, delay)
  }

  /**
   * Start heartbeat to keep connection alive
   */
  private startHeartbeat(): void {
    this.stopHeartbeat()
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping', timestamp: new Date().toISOString() })
      }
    }, this.heartbeatIntervalMs)
  }

  /**
   * Stop heartbeat
   */
  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }
  }
}

// Export singleton instance
export const websocketService = new WebSocketService()

// Auto-connect when module loads (in browser only)
if (typeof window !== 'undefined') {
  // Connect after a short delay to ensure auth is ready
  setTimeout(() => {
    websocketService.connect()
  }, 1000)

  // Reconnect on visibility change (when user returns to tab)
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden && !websocketService.getConnectionStatus()) {
      websocketService.connect()
    }
  })
}

