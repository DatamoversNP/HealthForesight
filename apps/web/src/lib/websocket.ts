/**
 * WebSocket Client for Real-time Updates
 */
import { io, Socket } from 'socket.io-client'

/** Socket.IO expects http(s) origin; derive from VITE_API_URL when VITE_WS_URL is unset. */
function getSocketIoServerUrl(): string {
  const explicit = import.meta.env.VITE_WS_URL as string | undefined
  if (explicit?.trim()) {
    return explicit
      .trim()
      .replace(/^wss:\/\//, 'https://')
      .replace(/^ws:\/\//, 'http://')
  }
  const api = import.meta.env.VITE_API_URL as string | undefined
  if (api) {
    try {
      const u = new URL(api)
      return `${u.protocol}//${u.host}`
    } catch {
      /* ignore */
    }
  }
  if (typeof window !== 'undefined') {
    const host = window.location.hostname.toLowerCase()
    if (host.endsWith('.azurewebsites.net') && !host.startsWith('healthforesight-api')) {
      return window.location.origin
    }
    if (host.includes('azurestaticapps.net')) {
      return 'https://healthforesight-api.azurewebsites.net'
    }
  }
  return 'http://localhost:8000'
}

/** API has no Socket.IO server today; production builds skip connecting unless explicitly enabled. */
function shouldConnectWebSocket(): boolean {
  const flag = import.meta.env.VITE_ENABLE_WEBSOCKET as string | undefined
  if (flag === 'false') return false
  if (flag === 'true') return true
  if (import.meta.env.PROD) return false
  return true
}

class WebSocketClient {
  private socket: Socket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private listeners: Map<string, Set<(data: any) => void>> = new Map()

  connect(token?: string) {
    if (this.socket?.connected) {
      return
    }

    if (!shouldConnectWebSocket()) {
      return
    }

    const wsUrl = getSocketIoServerUrl()
    
    this.socket = io(wsUrl, {
      auth: token ? { token } : undefined,
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: this.maxReconnectAttempts,
    })

    this.socket.on('connect', () => {
      console.log('WebSocket connected')
      this.reconnectAttempts = 0
    })

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason)
      if (reason === 'io server disconnect') {
        // Server disconnected, reconnect manually
        this.socket?.connect()
      }
    })

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error)
      this.reconnectAttempts++
      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        console.error('Max reconnection attempts reached')
      }
    })

    // Forward all events to registered listeners
    this.socket.onAny((event, data) => {
      const listeners = this.listeners.get(event)
      if (listeners) {
        listeners.forEach((listener) => listener(data))
      }
    })
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
    this.listeners.clear()
  }

  on(event: string, callback: (data: any) => void) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set())
    }
    this.listeners.get(event)!.add(callback)

    // If socket is connected, also register with socket.io
    if (this.socket?.connected) {
      this.socket.on(event, callback)
    }

    // Return unsubscribe function
    return () => {
      this.off(event, callback)
    }
  }

  off(event: string, callback: (data: any) => void) {
    const listeners = this.listeners.get(event)
    if (listeners) {
      listeners.delete(callback)
    }

    if (this.socket) {
      this.socket.off(event, callback)
    }
  }

  emit(event: string, data: any) {
    if (this.socket?.connected) {
      this.socket.emit(event, data)
    } else {
      console.warn('WebSocket not connected, cannot emit:', event)
    }
  }

  isConnected(): boolean {
    return this.socket?.connected || false
  }
}

// Singleton instance
export const wsClient = new WebSocketClient()

// Event types
export const WS_EVENTS = {
  INGESTION_STATUS: 'ingestion:status',
  INGESTION_COMPLETE: 'ingestion:complete',
  INGESTION_ERROR: 'ingestion:error',
  ANALYSIS_STATUS: 'analysis:status',
  ANALYSIS_COMPLETE: 'analysis:complete',
  ANALYSIS_ERROR: 'analysis:error',
  EXPORT_STATUS: 'export:status',
  EXPORT_COMPLETE: 'export:complete',
  EXPORT_ERROR: 'export:error',
  SCORECARD_UPDATE: 'scorecard:update',
  DECISION_UPDATE: 'decision:update',
} as const

