import { useEffect, useRef, useState, useCallback } from 'react'

interface UseWebSocketOptions {
  url: string
  onMessage?: (data: any) => void
  onError?: (error: Event) => void
  onOpen?: () => void
  onClose?: () => void
  reconnect?: boolean
  reconnectInterval?: number
  maxReconnectAttempts?: number
  token?: string | null
}

export function useWebSocket({
  url,
  onMessage,
  onError,
  onOpen,
  onClose,
  reconnect = true,
  reconnectInterval = 3000,
  maxReconnectAttempts = 10,
  token
}: UseWebSocketOptions) {
  const [isConnected, setIsConnected] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected')
  const [lastMessage, setLastMessage] = useState<any>(null)
  const [reconnectAttempts, setReconnectAttempts] = useState(0)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const shouldReconnectRef = useRef(true)
  const reconnectAttemptsRef = useRef(0)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    // Check max reconnect attempts
    if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
      console.warn(`WebSocket: Max reconnect attempts (${maxReconnectAttempts}) reached`)
      setConnectionStatus('error')
      shouldReconnectRef.current = false
      return
    }

    try {
      setConnectionStatus('connecting')
      const wsUrl = token ? `${url}?token=${token}` : url
      const ws = new WebSocket(wsUrl)
      
      ws.onopen = () => {
        setIsConnected(true)
        setConnectionStatus('connected')
        reconnectAttemptsRef.current = 0
        setReconnectAttempts(0)
        onOpen?.()
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          setLastMessage(data)
          onMessage?.(data)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
          // Try to handle non-JSON messages
          if (event.data) {
            setLastMessage({ raw: event.data })
            onMessage?.({ raw: event.data })
          }
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        setConnectionStatus('error')
        onError?.(error)
      }

      ws.onclose = (event) => {
        setIsConnected(false)
        setConnectionStatus('disconnected')
        onClose?.()

        // Only reconnect if it wasn't a normal closure and we should reconnect
        if (shouldReconnectRef.current && reconnect && event.code !== 1000) {
          reconnectAttemptsRef.current += 1
          setReconnectAttempts(reconnectAttemptsRef.current)
          
          // Exponential backoff: increase delay with each attempt
          const delay = Math.min(reconnectInterval * Math.pow(2, reconnectAttemptsRef.current - 1), 30000)
          
          reconnectTimeoutRef.current = setTimeout(() => {
            if (shouldReconnectRef.current) {
              connect()
            }
          }, delay)
        } else if (event.code === 1000) {
          // Normal closure, don't reconnect
          shouldReconnectRef.current = false
        }
      }

      wsRef.current = ws
    } catch (error) {
      console.error('Failed to create WebSocket:', error)
      setConnectionStatus('error')
      reconnectAttemptsRef.current += 1
      setReconnectAttempts(reconnectAttemptsRef.current)
      
      if (shouldReconnectRef.current && reconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
        reconnectTimeoutRef.current = setTimeout(() => {
          connect()
        }, reconnectInterval)
      }
    }
  }, [url, token, onMessage, onError, onOpen, onClose, reconnect, reconnectInterval, maxReconnectAttempts])

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect')
      wsRef.current = null
    }
    setIsConnected(false)
    setConnectionStatus('disconnected')
  }, [])

  const sendMessage = useCallback((data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify(data))
        return true
      } catch (error) {
        console.error('Failed to send WebSocket message:', error)
        return false
      }
    } else {
      console.warn('WebSocket is not connected. Current state:', wsRef.current?.readyState)
      return false
    }
  }, [])

  const manualReconnect = useCallback(() => {
    reconnectAttemptsRef.current = 0
    setReconnectAttempts(0)
    shouldReconnectRef.current = true
    disconnect()
    setTimeout(() => {
      connect()
    }, 1000)
  }, [connect, disconnect])

  useEffect(() => {
    connect()
    return () => {
      disconnect()
    }
  }, [connect, disconnect])

  return {
    isConnected,
    connectionStatus,
    lastMessage,
    sendMessage,
    disconnect,
    reconnect: manualReconnect,
    reconnectAttempts
  }
}

