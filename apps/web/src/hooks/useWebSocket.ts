/**
 * React Hook for WebSocket Updates
 */
import { useEffect, useRef } from 'react'
import { wsClient, WS_EVENTS } from '../lib/websocket'
import { apiClient } from '../lib/api'

export function useWebSocketUpdates(
  event: string,
  callback: (data: any) => void,
  enabled: boolean = true
) {
  const callbackRef = useRef(callback)

  useEffect(() => {
    callbackRef.current = callback
  }, [callback])

  useEffect(() => {
    if (!enabled) return

    // Connect if not already connected
    const token = apiClient.getToken()
    if (!wsClient.isConnected()) {
      wsClient.connect(token || undefined)
    }

    // Register listener
    const unsubscribe = wsClient.on(event, (data) => {
      callbackRef.current(data)
    })

    return () => {
      unsubscribe()
    }
  }, [event, enabled])
}

// Specific hooks for common use cases
export function useIngestionUpdates(ingestionId: string | null, onUpdate: (data: any) => void) {
  useWebSocketUpdates(
    WS_EVENTS.INGESTION_STATUS,
    (data) => {
      if (data.ingestion_id === ingestionId) {
        onUpdate(data)
      }
    },
    !!ingestionId
  )
}

export function useAnalysisUpdates(analysisId: string | null, onUpdate: (data: any) => void) {
  useWebSocketUpdates(
    WS_EVENTS.ANALYSIS_STATUS,
    (data) => {
      if (data.analysis_id === analysisId) {
        onUpdate(data)
      }
    },
    !!analysisId
  )
}

export function useExportUpdates(exportId: string | null, onUpdate: (data: any) => void) {
  useWebSocketUpdates(
    WS_EVENTS.EXPORT_STATUS,
    (data) => {
      if (data.export_id === exportId) {
        onUpdate(data)
      }
    },
    !!exportId
  )
}

