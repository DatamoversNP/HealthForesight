/**
 * usePermissions Hook - Check user permissions
 */
import { useState, useEffect, useCallback } from 'react'
import { useRole } from '../contexts/RoleContext'
import { apiClient } from '../lib/api'

interface PermissionCheck {
  resource: string
  action: string
  resourceId?: string
}

export function usePermissions() {
  const { permissions, hasPermission: hasPermissionFromContext } = useRole()
  const [permissionCache, setPermissionCache] = useState<Map<string, boolean>>(new Map())

  const checkPermission = useCallback(
    async (resource: string, action: string, resourceId?: string): Promise<boolean> => {
      const cacheKey = `${resource}:${action}:${resourceId || ''}`
      
      // Check cache first
      if (permissionCache.has(cacheKey)) {
        return permissionCache.get(cacheKey)!
      }

      // Check from context
      const hasPerm = await hasPermissionFromContext(resource, action, resourceId)
      
      // Update cache
      setPermissionCache((prev) => new Map(prev).set(cacheKey, hasPerm))
      
      return hasPerm
    },
    [hasPermissionFromContext, permissionCache]
  )

  const hasPermissionSync = useCallback(
    (resource: string, action: string): boolean => {
      // Quick sync check based on permissions list
      const perm = permissions.find((p) => p.resource === resource)
      return perm?.actions?.includes(action) || false
    },
    [permissions]
  )

  const clearCache = useCallback(() => {
    setPermissionCache(new Map())
  }, [])

  return {
    checkPermission,
    hasPermissionSync,
    permissions,
    clearCache,
  }
}


