/**
 * Role Context - Manages current persona/role view
 */
import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useAuth } from './AuthContext'
import { apiClient } from '../lib/api'

export type PersonaRole = 'EXECUTIVE' | 'POLICY_OWNER' | 'ANALYST' | 'OPS_CLINICAL'

interface RoleContextType {
  currentPersona: PersonaRole | null
  setCurrentPersona: (persona: PersonaRole | null) => void
  availablePersonas: PersonaRole[]
  userRoles: any[]
  permissions: any[]
  loading: boolean
  hasPermission: (resource: string, action: string, resourceId?: string) => Promise<boolean>
}

const RoleContext = createContext<RoleContextType | undefined>(undefined)

export function RoleProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth() // Now safe - useAuth returns defaults if context unavailable
  const [currentPersona, setCurrentPersonaState] = useState<PersonaRole | null>(null)
  const [availablePersonas, setAvailablePersonas] = useState<PersonaRole[]>([])
  const [userRoles, setUserRoles] = useState<any[]>([])
  const [permissions, setPermissions] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  // Load user roles and determine available personas
  useEffect(() => {
    if (!user) {
      setLoading(false)
      return
    }

    const loadRoleData = async () => {
      try {
        setLoading(true)
        
        // Map user roles from auth context to personas
        // This works with the demo user's roles: ["POLICY_ADMIN", "UM_LEADER"]
        const roleToPersonaMap: Record<string, PersonaRole> = {
          'POLICY_ADMIN': 'POLICY_OWNER',
          'UM_LEADER': 'POLICY_OWNER',
          'EXEC_VIEWER': 'EXECUTIVE',
          'ACTUARIAL': 'ANALYST',
          'STRATEGY': 'ANALYST',
          'COMPLIANCE': 'OPS_CLINICAL',
          'admin': 'POLICY_OWNER', // File storage mode
        }

        // Use roles from user object immediately (fast path)
        let roles: any[] = []
        let perms: any[] = []
        
        if (user.roles && Array.isArray(user.roles)) {
          // Convert user roles to role assignments format
          roles = user.roles.map((roleName: string) => ({
            role_name: roleName,
            role_id: roleName, // Use role name as ID for now
          }))
        }
        
        // Set immediately for fast UI rendering
        setUserRoles(roles)
        setPermissions(perms)
        
        // Try to get roles from RBAC API in background (non-blocking)
        try {
          const [rolesResult, permsResult] = await Promise.all([
            apiClient.getUserRoles(user.id),
            apiClient.getUserPermissions(user.id)
          ])
          // API returns { user_id, role_names: string[] }; normalize to [{ role_name, role_id }]
          if (rolesResult?.role_names && Array.isArray(rolesResult.role_names) && rolesResult.role_names.length > 0) {
            setUserRoles(rolesResult.role_names.map((roleName: string) => ({ role_name: roleName, role_id: roleName })))
          } else if (rolesResult && Array.isArray(rolesResult) && rolesResult.length > 0) {
            setUserRoles(rolesResult)
          }
          if (permsResult && Array.isArray(permsResult) && permsResult.length > 0) {
            setPermissions(permsResult)
          }
        } catch (apiError: any) {
          // Silently fail - we already have roles from user object
        }

        // Determine available personas from roles
        const personas = new Set<PersonaRole>()
        
        // Check role assignments from API
        roles.forEach((roleAssignment: any) => {
          const roleName = roleAssignment.role_name || roleAssignment.role_id || ''
          const persona = roleToPersonaMap[roleName]
          if (persona) {
            personas.add(persona)
          }
        })

        // Also check user.roles directly (from auth context
        if (user.roles && Array.isArray(user.roles)) {
          user.roles.forEach((roleName: string) => {
            const persona = roleToPersonaMap[roleName]
            if (persona) {
              personas.add(persona)
            }
          })
        }

        // For demo purposes, ALWAYS show all personas regardless of user roles
        // This allows users to explore all different views
        const allPersonas: PersonaRole[] = ['EXECUTIVE', 'POLICY_OWNER', 'ANALYST', 'OPS_CLINICAL']
        allPersonas.forEach(p => personas.add(p))
        
        const finalPersonas = Array.from(personas).sort()
        console.log('RoleContext: User roles:', user.roles, 'API roles:', roles, 'Final available personas:', finalPersonas)
        setAvailablePersonas(finalPersonas)

        // Set default persona if none selected
        if (!currentPersona && personas.size > 0) {
          // Check for persisted persona first
          const persisted = localStorage.getItem('current_persona') as PersonaRole | null
          if (persisted && personas.has(persisted)) {
            setCurrentPersonaState(persisted)
          } else {
            setCurrentPersonaState(Array.from(personas)[0])
          }
        }
      } catch (error) {
        console.error('Failed to load role data:', error)
        // Default to all personas for demo
        setAvailablePersonas(['EXECUTIVE', 'POLICY_OWNER', 'ANALYST', 'OPS_CLINICAL'])
        const persisted = localStorage.getItem('current_persona') as PersonaRole | null
        setCurrentPersonaState(persisted || 'EXECUTIVE')
      } finally {
        setLoading(false)
      }
    }

    loadRoleData()
  }, [user])

  const setCurrentPersona = (persona: PersonaRole | null) => {
    console.log('RoleContext: Setting persona to:', persona)
    setCurrentPersonaState(persona)
    // Persist to localStorage
    if (persona) {
      localStorage.setItem('current_persona', persona)
    } else {
      localStorage.removeItem('current_persona')
    }
  }

  // Load persisted persona on mount (moved logic to loadRoleData to avoid race condition)

  const hasPermission = async (resource: string, action: string, resourceId?: string): Promise<boolean> => {
    try {
      const result = await apiClient.checkPermission(resource, action, resourceId)
      return result.has_permission || false
    } catch (error) {
      console.error('Permission check failed:', error)
      return false
    }
  }

  return (
    <RoleContext.Provider
      value={{
        currentPersona,
        setCurrentPersona,
        availablePersonas,
        userRoles,
        permissions,
        loading,
        hasPermission,
      }}
    >
      {children}
    </RoleContext.Provider>
  )
}

export function useRole() {
  const context = useContext(RoleContext)
  if (context === undefined) {
    // Return a safe default instead of throwing
    // This allows components to render even if provider isn't available yet
    return {
      currentPersona: null,
      setCurrentPersona: () => {},
      availablePersonas: [],
      userRoles: [],
      permissions: [],
      loading: true,
      hasPermission: async () => false,
    }
  }
  return context
}

