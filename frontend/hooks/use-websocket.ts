/**
 * React hook for WebSocket subscriptions
 * Makes it easy to subscribe to WebSocket messages in any component
 */

import { useEffect, useRef, useState } from 'react'
import { websocketService, WebSocketMessageType, WebSocketMessage } from '@/lib/websocket-service'

/**
 * Hook to subscribe to WebSocket messages
 * @param messageType - Type of message to subscribe to
 * @param handler - Callback function to handle messages
 * @param deps - Optional dependency array (like useEffect)
 */
export function useWebSocket(
  messageType: WebSocketMessageType,
  handler: (message: WebSocketMessage) => void,
  deps: any[] = []
) {
  const handlerRef = useRef(handler)

  // Update handler ref when it changes
  useEffect(() => {
    handlerRef.current = handler
  }, [handler])

  useEffect(() => {
    // Ensure WebSocket is connected
    if (!websocketService.getConnectionStatus()) {
      websocketService.connect()
    }

    // Subscribe to messages
    const unsubscribe = websocketService.subscribe(messageType, (message) => {
      handlerRef.current(message)
    })

    // Cleanup on unmount
    return () => {
      unsubscribe()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messageType, ...deps])
}

/**
 * Hook to monitor WebSocket connection status
 * @returns Connection status (true if connected, false otherwise)
 */
export function useWebSocketConnection(): boolean {
  const [connected, setConnected] = useState(websocketService.getConnectionStatus())

  useEffect(() => {
    // Ensure WebSocket is connected
    if (!websocketService.getConnectionStatus()) {
      websocketService.connect()
    }

    // Subscribe to connection changes
    const unsubscribe = websocketService.onConnectionChange((isConnected) => {
      setConnected(isConnected)
    })

    return () => {
      unsubscribe()
    }
  }, [])

  return connected
}

