/**
 * Comprehensive frontend logging utility
 */
interface LogEntry {
  timestamp: string
  level: 'debug' | 'info' | 'warn' | 'error'
  category: string
  message: string
  data?: any
  error?: {
    name: string
    message: string
    stack?: string
  }
  userAgent?: string
  url?: string
}

class Logger {
  private logs: LogEntry[] = []
  private maxLogs = 100  // Reduced from 1000 to prevent localStorage quota issues
  private enableConsole = true
  private enableStorage = true
  private enableRemote = false
  private storageQuotaExceeded = false  // Track if we've hit quota limit

  constructor() {
    // Load existing logs from localStorage
    this.loadLogs()
    
    // Save logs periodically
    setInterval(() => this.saveLogs(), 5000)
    
    // Save logs before page unload
    window.addEventListener('beforeunload', () => this.saveLogs())
  }

  private loadLogs(): void {
    if (!this.enableStorage) return
    
    try {
      const stored = localStorage.getItem('uepi_logs')
      if (stored) {
        this.logs = JSON.parse(stored)
        // Keep only recent logs
        if (this.logs.length > this.maxLogs) {
          this.logs = this.logs.slice(-this.maxLogs)
        }
      }
    } catch (e) {
      console.warn('Failed to load logs from storage:', e)
    }
  }

  private saveLogs(): void {
    if (!this.enableStorage || this.storageQuotaExceeded) return
    
    try {
      // Keep only recent logs (aggressive trimming to prevent quota issues)
      if (this.logs.length > this.maxLogs) {
        // Keep only the most recent logs
        this.logs = this.logs.slice(-this.maxLogs)
      }
      
      // Truncate large data objects to prevent quota issues
      const logsToSave = this.logs.map(log => {
        const logCopy = { ...log }
        // Truncate large data objects
        if (logCopy.data && typeof logCopy.data === 'object') {
          const dataStr = JSON.stringify(logCopy.data)
          if (dataStr.length > 1000) {
            logCopy.data = { ...logCopy.data, _truncated: true, _originalSize: dataStr.length }
            // Remove large nested objects
            if (logCopy.data.requestData) logCopy.data.requestData = '[truncated]'
            if (logCopy.data.responseData) logCopy.data.responseData = '[truncated]'
          }
        }
        return logCopy
      })
      
      const logsJson = JSON.stringify(logsToSave)
      
      // Check size before saving (localStorage limit is ~5-10MB)
      if (logsJson.length > 2 * 1024 * 1024) {  // 2MB threshold
        // Too large, keep only errors and recent logs
        const errorLogs = this.logs.filter(log => log.level === 'error').slice(-20)
        const recentLogs = this.logs.slice(-50)
        const combined = [...new Set([...errorLogs, ...recentLogs])].slice(-50)
        localStorage.setItem('uepi_logs', JSON.stringify(combined))
      } else {
        localStorage.setItem('uepi_logs', logsJson)
      }
    } catch (e: any) {
      // If quota exceeded, disable storage and keep only in-memory logs
      if (e.name === 'QuotaExceededError' || e.message?.includes('quota')) {
        this.storageQuotaExceeded = true
        this.enableStorage = false
        // Clear old logs and keep only recent ones in memory
        this.logs = this.logs.slice(-50)
        console.warn('localStorage quota exceeded. Logging will continue in memory only.')
      } else {
        console.warn('Failed to save logs to storage:', e)
      }
    }
  }

  private addLog(level: LogEntry['level'], category: string, message: string, data?: any, error?: Error): void {
    // Truncate large data objects to prevent memory issues
    let truncatedData = data
    if (data && typeof data === 'object') {
      const dataStr = JSON.stringify(data)
      if (dataStr.length > 500) {
        // Keep only essential fields for large objects
        truncatedData = {
          ...data,
          _truncated: true,
          _originalSize: dataStr.length
        }
        // Remove large nested objects
        if (truncatedData.requestData) truncatedData.requestData = '[truncated]'
        if (truncatedData.responseData) truncatedData.responseData = '[truncated]'
      }
    }
    
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      category,
      message,
      data: truncatedData,
      userAgent: navigator.userAgent,
      url: window.location.href,
    }

    if (error) {
      entry.error = {
        name: error.name,
        message: error.message,
        stack: error.stack,
      }
    }

    this.logs.push(entry)

    // Console logging
    if (this.enableConsole) {
      const consoleMethod = console[level] || console.log
      const prefix = `[${category}]`
      if (error) {
        consoleMethod(prefix, message, data, error)
      } else if (data) {
        consoleMethod(prefix, message, data)
      } else {
        consoleMethod(prefix, message)
      }
    }

    // Remote logging (if enabled)
    if (this.enableRemote && level === 'error') {
      this.sendToRemote(entry)
    }
  }

  private async sendToRemote(entry: LogEntry): Promise<void> {
    try {
      // Send to API endpoint if available
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
      await fetch(`${apiUrl}/logs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(entry),
      }).catch(() => {
        // Silently fail - don't log logging errors
      })
    } catch (e) {
      // Silently fail
    }
  }

  debug(category: string, message: string, data?: any): void {
    this.addLog('debug', category, message, data)
  }

  info(category: string, message: string, data?: any): void {
    this.addLog('info', category, message, data)
  }

  warn(category: string, message: string, data?: any): void {
    this.addLog('warn', category, message, data)
  }

  error(category: string, message: string, error?: Error, data?: any): void {
    this.addLog('error', category, message, data, error)
  }

  // API call logging
  logApiCall(method: string, url: string, status: number, duration: number, requestData?: any, responseData?: any, error?: Error): void {
    this.info('API', `${method} ${url} -> ${status} (${duration}ms)`, {
      method,
      url,
      status,
      duration,
      requestData,
      responseData,
      error: error ? { name: error.name, message: error.message } : undefined,
    })
  }

  // User action logging
  logAction(action: string, details?: any): void {
    this.info('ACTION', action, details)
  }

  // Get all logs
  getLogs(level?: LogEntry['level'], category?: string, limit?: number): LogEntry[] {
    let filtered = this.logs

    if (level) {
      filtered = filtered.filter(log => log.level === level)
    }

    if (category) {
      filtered = filtered.filter(log => log.category === category)
    }

    if (limit) {
      filtered = filtered.slice(-limit)
    }

    return filtered
  }

  // Export logs
  exportLogs(): string {
    return JSON.stringify(this.logs, null, 2)
  }

  // Clear logs
  clearLogs(): void {
    this.logs = []
    if (this.enableStorage) {
      localStorage.removeItem('uepi_logs')
    }
  }
}

// Create singleton instance
export const logger = new Logger()

// Export for use in components
export default logger

