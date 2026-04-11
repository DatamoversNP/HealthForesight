/**
 * Authentication Context
 */
import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiClient } from '../lib/api'

// Import WebSocket client - wrap usage in try/catch to handle gracefully
import { wsClient } from '../lib/websocket'

interface User {
  id: string
  email: string
  name?: string
  roles: string[]
  tenant_id: string
}

interface AuthContextType {
  user: User | null
  loading: boolean
  error: string | null
  apiUnavailable: boolean
  clearApiUnavailable: () => void
  login: (token: string) => Promise<void>
  logout: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [apiUnavailable, setApiUnavailable] = useState(false)
  const navigate = useNavigate() // Now safe - BrowserRouter wraps AuthProvider

  const loadUser = async (opts?: { sessionOnly?: boolean }): Promise<User | null> => {
    if (!apiClient.getToken()) {
      setUser(null)
      setLoading(false)
      return null
    }
    const sessionOnly = opts?.sessionOnly ?? false
    try {
      const userData = (sessionOnly
        ? await apiClient.getMeSessionVerify(12000)
        : await apiClient.getMe()) as any
      if (userData) {
        const u: User = {
          id: userData.id,
          email: userData.email,
          name: userData.full_name ?? userData.name,
          roles: userData.roles ?? [],
          tenant_id: userData.tenant_id,
        }
        setUser(u)
        setApiUnavailable(false)
        return u
      }
      setUser(null)
      return null
    } catch (error: any) {
      if (error?.status === 401) {
        apiClient.setToken(null)
        setUser(null)
      } else if (
        error?.code === 'ERR_NETWORK' ||
        error?.code === 'ECONNABORTED' ||
        error?.status === 0
      ) {
        setApiUnavailable(true)
        setUser(null)
        if (sessionOnly) {
          apiClient.setToken(null)
        }
      } else {
        setUser(null)
      }
      return null
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // Clear any legacy dev/mock token so getToken() returns null and we show login
    const t = apiClient.getToken()
    if (!t) {
      setUser(null)
      setLoading(false)
      return
    }
    if (apiClient.isAccessTokenExpired()) {
      apiClient.setToken(null)
      setUser(null)
      setLoading(false)
      return
    }
    loadUser({ sessionOnly: true }).catch(() => setLoading(false))
  }, [])

  const clearApiUnavailable = () => setApiUnavailable(false)

  const login = async (token: string) => {
    apiClient.setToken(token)
    const u = await loadUser({ sessionOnly: false })
    if (u && apiClient.getToken()) {
      if (typeof wsClient !== 'undefined' && wsClient) {
        try {
          wsClient.connect(token)
        } catch (wsError) {
          console.warn('WebSocket connection failed:', wsError)
        }
      }
      navigate('/')
    }
  }

  const logout = () => {
    apiClient.setToken(null)
    if (typeof wsClient !== 'undefined' && wsClient) {
      try {
        wsClient.disconnect()
      } catch (wsError) {
        console.warn('WebSocket disconnect failed:', wsError)
      }
    }
    setUser(null)
    setError(null)
    navigate('/login')
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        error,
        apiUnavailable,
        clearApiUnavailable,
        login,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    return {
      user: null,
      isAuthenticated: false,
      loading: false,
      error: null,
      apiUnavailable: false,
      clearApiUnavailable: () => {},
      login: async () => {},
      logout: () => {},
    }
  }
  return context
}

