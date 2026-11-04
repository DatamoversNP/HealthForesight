/**
 * Frontend logging utility.
 * - Never logs secrets (password, tokens, Authorization).
 * - In production builds, API success logs are quiet (method/url/status/duration only).
 * - Avoids dumping large response bodies into console / localStorage.
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

const SENSITIVE_KEY_RE =
  /^(password|passwd|pwd|secret|token|access_token|refresh_token|id_token|authorization|api[_-]?key|client_secret|jwt)$/i

const isProdBuild = Boolean(import.meta.env?.PROD)

function redactValue(key: string, value: unknown): unknown {
  if (SENSITIVE_KEY_RE.test(key)) return '[REDACTED]'
  return value
}

/** Deep-redact sensitive keys; truncate huge strings/arrays for logging. */
export function sanitizeForLog(input: unknown, depth = 0): unknown {
  if (input == null) return input
  if (depth > 4) return '[max-depth]'

  if (typeof input === 'string') {
    // Axios may pass already-stringified JSON bodies
    const trimmed = input.trim()
    if (
      (trimmed.startsWith('{') && trimmed.endsWith('}')) ||
      (trimmed.startsWith('[') && trimmed.endsWith(']'))
    ) {
      try {
        return JSON.stringify(sanitizeForLog(JSON.parse(trimmed), depth + 1))
      } catch {
        return input.length > 300 ? `${input.slice(0, 300)}…[truncated]` : input
      }
    }
    return input.length > 300 ? `${input.slice(0, 300)}…[truncated]` : input
  }

  if (typeof input !== 'object') return input

  if (Array.isArray(input)) {
    if (input.length > 20) {
      return {
        _type: 'array',
        length: input.length,
        sample: input.slice(0, 3).map((v) => sanitizeForLog(v, depth + 1)),
      }
    }
    return input.map((v) => sanitizeForLog(v, depth + 1))
  }

  const out: Record<string, unknown> = {}
  for (const [k, v] of Object.entries(input as Record<string, unknown>)) {
    out[k] = redactValue(k, sanitizeForLog(v, depth + 1))
  }
  return out
}

class Logger {
  private logs: LogEntry[] = []
  private maxLogs = 100
  private enableConsole = true
  private enableStorage = true
  private enableRemote = false
  private storageQuotaExceeded = false
  /** In production, skip debug + routine successful API body dumps. */
  private quietSuccessInProd = isProdBuild

  constructor() {
    this.loadLogs()
    setInterval(() => this.saveLogs(), 5000)
    window.addEventListener('beforeunload', () => this.saveLogs())
  }

  private loadLogs(): void {
    if (!this.enableStorage) return
    try {
      const stored = localStorage.getItem('uepi_logs')
      if (stored) {
        this.logs = JSON.parse(stored)
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
      if (this.logs.length > this.maxLogs) {
        this.logs = this.logs.slice(-this.maxLogs)
      }

      const logsToSave = this.logs.map((log) => {
        const logCopy = { ...log }
        if (logCopy.data && typeof logCopy.data === 'object') {
          const dataStr = JSON.stringify(logCopy.data)
          if (dataStr.length > 1000) {
            logCopy.data = {
              ...logCopy.data,
              _truncated: true,
              _originalSize: dataStr.length,
              requestData: logCopy.data.requestData ? '[truncated]' : undefined,
              responseData: logCopy.data.responseData ? '[truncated]' : undefined,
            }
          }
        }
        return logCopy
      })

      const logsJson = JSON.stringify(logsToSave)
      if (logsJson.length > 2 * 1024 * 1024) {
        const errorLogs = this.logs.filter((log) => log.level === 'error').slice(-20)
        const recentLogs = this.logs.slice(-50)
        const combined = [...new Set([...errorLogs, ...recentLogs])].slice(-50)
        localStorage.setItem('uepi_logs', JSON.stringify(combined))
      } else {
        localStorage.setItem('uepi_logs', logsJson)
      }
    } catch (e: any) {
      if (e.name === 'QuotaExceededError' || e.message?.includes('quota')) {
        this.storageQuotaExceeded = true
        this.enableStorage = false
        this.logs = this.logs.slice(-50)
        console.warn('localStorage quota exceeded. Logging will continue in memory only.')
      } else {
        console.warn('Failed to save logs to storage:', e)
      }
    }
  }

  private addLog(
    level: LogEntry['level'],
    category: string,
    message: string,
    data?: any,
    error?: Error
  ): void {
    if (this.quietSuccessInProd && level === 'debug') {
      return
    }

    const safeData = data !== undefined ? sanitizeForLog(data) : undefined
    let truncatedData = safeData
    if (safeData && typeof safeData === 'object') {
      try {
        const dataStr = JSON.stringify(safeData)
        if (dataStr.length > 500) {
          truncatedData = {
            ...(safeData as object),
            _truncated: true,
            _originalSize: dataStr.length,
          } as any
          if ((truncatedData as any).requestData) (truncatedData as any).requestData = '[truncated]'
          if ((truncatedData as any).responseData) (truncatedData as any).responseData = '[truncated]'
        }
      } catch {
        truncatedData = { _unserializable: true }
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

    if (this.enableConsole) {
      const consoleMethod = console[level] || console.log
      const prefix = `[${category}]`
      if (error) {
        consoleMethod(prefix, message, truncatedData, error)
      } else if (truncatedData !== undefined) {
        consoleMethod(prefix, message, truncatedData)
      } else {
        consoleMethod(prefix, message)
      }
    }

    if (this.enableRemote && level === 'error') {
      this.sendToRemote(entry)
    }
  }

  private async sendToRemote(entry: LogEntry): Promise<void> {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
      await fetch(`${apiUrl}/logs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(entry),
      }).catch(() => {})
    } catch {
      // ignore
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

  /**
   * API call logging. Never includes raw secrets.
   * Production: successful calls log status/duration only (no bodies).
   * Dev / errors: include redacted request/response summaries.
   */
  logApiCall(
    method: string,
    url: string,
    status: number,
    duration: number,
    requestData?: any,
    responseData?: any,
    error?: Error
  ): void {
    const ok = status >= 200 && status < 400
    const payload: Record<string, unknown> = {
      method,
      url,
      status,
      duration,
    }

    const includeBodies = Boolean(error) || !ok || !this.quietSuccessInProd
    if (includeBodies) {
      payload.requestData = sanitizeForLog(requestData)
      // Never attach full response arrays/objects in prod success path; here only when includeBodies
      payload.responseData = sanitizeForLog(
        Array.isArray(responseData)
          ? { _type: 'array', length: responseData.length }
          : responseData && typeof responseData === 'object'
            ? { keys: Object.keys(responseData).slice(0, 20) }
            : responseData
      )
    }

    if (error) {
      payload.error = { name: error.name, message: error.message }
      this.warn('API', `${method} ${url} -> ${status} (${duration}ms)`, payload)
      return
    }

    if (this.quietSuccessInProd && ok) {
      // Minimal one-liner; no bodies
      this.info('API', `${method} ${url} -> ${status} (${duration}ms)`, payload)
      return
    }

    this.info('API', `${method} ${url} -> ${status} (${duration}ms)`, payload)
  }

  logAction(action: string, details?: any): void {
    this.info('ACTION', action, sanitizeForLog(details))
  }

  getLogs(level?: LogEntry['level'], category?: string, limit?: number): LogEntry[] {
    let filtered = this.logs
    if (level) filtered = filtered.filter((log) => log.level === level)
    if (category) filtered = filtered.filter((log) => log.category === category)
    if (limit) filtered = filtered.slice(-limit)
    return filtered
  }

  exportLogs(): string {
    return JSON.stringify(this.logs, null, 2)
  }

  clearLogs(): void {
    this.logs = []
    if (this.enableStorage) {
      localStorage.removeItem('uepi_logs')
    }
  }
}

export const logger = new Logger()
export default logger
