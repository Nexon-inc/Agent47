import { useAuthStore } from '@/lib/stores/auth-store'

export interface WebSocketMessage {
  type: string
  data: any
  timestamp: string
  user_id?: string
}

class WebSocketClient {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private messageHandlers: Map<string, ((data: any) => void)[]> = new Map()
  private connectionStatus: 'connected' | 'disconnected' | 'connecting' = 'disconnected'

  public connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve()
        return
      }

      const { user } = useAuthStore.getState()
      if (!user?.access_token) {
        reject(new Error('No authentication token available'))
        return
      }

      this.connectionStatus = 'connecting'
      
      const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws'
      this.ws = new WebSocket(`${wsUrl}?token=${user.access_token}`)

      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.connectionStatus = 'connected'
        this.reconnectAttempts = 0
        resolve()
      }

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          this.handleMessage(message)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      this.ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason)
        this.connectionStatus = 'disconnected'
        
        if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect()
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        this.connectionStatus = 'disconnected'
        reject(error)
      }
    })
  }

  public disconnect() {
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect')
      this.ws = null
    }
    this.connectionStatus = 'disconnected'
  }

  private scheduleReconnect() {
    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
    
    setTimeout(() => {
      if (this.connectionStatus === 'disconnected') {
        this.connect().catch(console.error)
      }
    }, delay)
  }

  public send(message: WebSocketMessage) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket not connected, message not sent:', message)
    }
  }

  private handleMessage(message: WebSocketMessage) {
    const handlers = this.messageHandlers.get(message.type)
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(message.data)
        } catch (error) {
          console.error(`Error in message handler for type ${message.type}:`, error)
        }
      })
    }
  }

  public subscribe(messageType: string, handler: (data: any) => void) {
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, [])
    }
    this.messageHandlers.get(messageType)!.push(handler)

    return () => {
      const handlers = this.messageHandlers.get(messageType)
      if (handlers) {
        const index = handlers.indexOf(handler)
        if (index > -1) {
          handlers.splice(index, 1)
        }
      }
    }
  }

  public getConnectionStatus() {
    return this.connectionStatus
  }

  public isConnected() {
    return this.ws?.readyState === WebSocket.OPEN
  }
}

export const websocketClient = new WebSocketClient()

export const useWebSocket = () => {
  return {
    connect: () => websocketClient.connect(),
    disconnect: () => websocketClient.disconnect(),
    send: (message: WebSocketMessage) => websocketClient.send(message),
    subscribe: (messageType: string, handler: (data: any) => void) => 
      websocketClient.subscribe(messageType, handler),
    isConnected: () => websocketClient.isConnected(),
    getConnectionStatus: () => websocketClient.getConnectionStatus()
  }
}
