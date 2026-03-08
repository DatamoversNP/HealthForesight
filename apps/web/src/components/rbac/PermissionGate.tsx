/**
 * PermissionGate Component - Conditionally render children based on permissions
 */
import React, { useState, useEffect } from 'react'
import { Box, Alert } from '@mui/material'
import { usePermissions } from '../../hooks/usePermissions'

interface PermissionGateProps {
  resource: string
  action: string
  resourceId?: string
  children: React.ReactNode
  fallback?: React.ReactNode
  showError?: boolean
  mode?: 'hide' | 'disable' | 'error'
}

export default function PermissionGate({
  resource,
  action,
  resourceId,
  children,
  fallback,
  showError = false,
  mode = 'hide',
}: PermissionGateProps) {
  const { checkPermission, hasPermissionSync } = usePermissions()
  const [hasPermission, setHasPermission] = useState<boolean | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const check = async () => {
      setLoading(true)
      try {
        // Try sync check first
        const syncCheck = hasPermissionSync(resource, action)
        if (syncCheck) {
          setHasPermission(true)
          setLoading(false)
          return
        }

        // Fall back to async check
        const result = await checkPermission(resource, action, resourceId)
        setHasPermission(result)
      } catch (error) {
        console.error('Permission check failed:', error)
        setHasPermission(false)
      } finally {
        setLoading(false)
      }
    }

    check()
  }, [resource, action, resourceId, checkPermission, hasPermissionSync])

  if (loading) {
    return null // Or a loading spinner
  }

  if (!hasPermission) {
    if (mode === 'error' && showError) {
      return (
        <Alert severity="error" sx={{ mt: 2 }}>
          You don't have permission to {action} {resource}
        </Alert>
      )
    }
    if (fallback) {
      return <>{fallback}</>
    }
    return null
  }

  if (mode === 'disable' && React.isValidElement(children)) {
    return React.cloneElement(children, { disabled: false } as any)
  }

  return <>{children}</>
}


