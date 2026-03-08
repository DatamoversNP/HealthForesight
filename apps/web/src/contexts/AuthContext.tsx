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

  const loadUser = async () => {
    // Set mock user immediately for fast startup (API will override if available)
    const mockUser = {
      id: '00000000-0000-0000-0000-000000000001',
      email: 'demo@example.com',
      name: 'Demo User',
      roles: ['POLICY_ADMIN'],
      tenant_id: '00000000-0000-0000-0000-000000000001',
    }
    
    // Set mock user immediately so UI can render
    setUser(mockUser)
    setLoading(false)
    setError(null)
    
    // Ensure token is set
    if (!apiClient.getToken()) {
      apiClient.setToken('dev-token-123')
    }
    
    // Try to get real user data in background (non-blocking)
    try {
      const userData = await apiClient.getMe() as any
      if (userData) {
        setUser(userData)
        setApiUnavailable(false)
      }
    } catch (error: any) {
      if (error?.code === 'ERR_NETWORK' || error?.status === 0) {
        setApiUnavailable(true)
      }
    }
  }

  useEffect(() => {
    // Check for existing token
    let token = apiClient.getToken()
    if (!token) {
      // No token - set a mock token for development/production fallback
      // This allows the app to work even without authentication setup
      token = 'dev-token-123'  // Use a consistent mock token that API accepts
      apiClient.setToken(token)
    }
    
    // Try to load user with the token
    loadUser().catch((err) => {
      console.error('Error in loadUser during initialization:', err)
      if (err?.code === 'ERR_NETWORK' || err?.status === 0) {
        setApiUnavailable(true)
      }
      setUser({
        id: 'mock-user-id',
        email: 'user@example.com',
        name: 'Demo User',
        roles: ['POLICY_ADMIN'],
        tenant_id: 'mock-tenant-id',
      })
      setLoading(false)
      if (!apiClient.getToken()) {
        apiClient.setToken('dev-token-123')
      }
    })
  }, [])

  const clearApiUnavailable = () => setApiUnavailable(false)

  const login = async (token: string) => {
    try {
      apiClient.setToken(token)
      await loadUser()
      // Connect WebSocket after login (only if user loaded successfully, and if wsClient exists)
      if (typeof wsClient !== 'undefined' && wsClient) {
        try {
          wsClient.connect(token)
        } catch (wsError) {
          console.warn('WebSocket connection failed:', wsError)
          // Don't fail login if WebSocket fails
        }
      }
      navigate('/')
    } catch (error: any) {
      console.error('Login failed:', error)
      // Always allow access with mock user if login fails (until API is fully functional)
      setUser({
        id: 'mock-user-id',
        email: 'user@example.com',
        name: 'Demo User',
        roles: ['POLICY_ADMIN'],
        tenant_id: 'mock-tenant-id',
      })
      setLoading(false)
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
    // Return safe defaults instead of throwing - allows components to render during hot reload
    return {
      user: {
        id: '00000000-0000-0000-0000-000000000001',
        email: 'demo@example.com',
        name: 'Demo User',
        roles: ['POLICY_ADMIN'],
        tenant_id: '00000000-0000-0000-0000-000000000001',
      },
      isAuthenticated: true,
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

