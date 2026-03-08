/**
 * Role Switcher Component - Allows users to switch between persona views
 */
import React, { useState } from 'react'
import {
  Box,
  Button,
  Menu,
  MenuItem,
  Typography,
  Chip,
  Tooltip,
  CircularProgress,
} from '@mui/material'
import {
  Person as PersonIcon,
  Business as ExecutiveIcon,
  Policy as PolicyIcon,
  Analytics as AnalystIcon,
  LocalHospital as ClinicalIcon,
} from '@mui/icons-material'
import { useRole, PersonaRole } from '../../contexts/RoleContext'
import { useNavigate } from 'react-router-dom'

const personaConfig: Record<PersonaRole, { label: string; icon: React.ReactElement; description: string }> = {
  EXECUTIVE: {
    label: 'Executive',
    icon: <ExecutiveIcon />,
    description: 'CFO/Actuary/CMO view: outcomes, risk, confidence',
  },
  POLICY_OWNER: {
    label: 'Policy Owner',
    icon: <PolicyIcon />,
    description: 'Policy lifecycle, assumptions, approvals',
  },
  ANALYST: {
    label: 'Analyst',
    icon: <AnalystIcon />,
    description: 'Methods, cohorts, diagnostics, sensitivity',
  },
  OPS_CLINICAL: {
    label: 'Ops/Clinical',
    icon: <ClinicalIcon />,
    description: 'Behavioral signals, complaints, access impact',
  },
}

export default function RoleSwitcher() {
  // ALL HOOKS MUST BE CALLED FIRST, BEFORE ANY CONDITIONAL RETURNS
  // This ensures consistent hook order across renders
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const navigate = useNavigate()
  
  // useRole now returns safe defaults if provider isn't available
  const { currentPersona, setCurrentPersona, availablePersonas, loading } = useRole()

  if (loading) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <CircularProgress size={16} sx={{ color: 'white' }} />
      </Box>
    )
  }

  // Suppress debug logs in production - only log if there's an actual issue
  if (process.env.NODE_ENV === 'development' && availablePersonas && availablePersonas.length > 0) {
    // Only log when we have personas (successful load)
  }

  if (!availablePersonas || availablePersonas.length === 0) {
    // Don't log warning - this is expected during initial load
    return null
  }

  // If no current persona but we have available personas, use first one for display
  // (RoleContext should set it, but this is a fallback)
  const displayPersona = currentPersona || availablePersonas[0]
  
  if (!displayPersona) {
    return null
  }

  const currentConfig = personaConfig[displayPersona]
  const open = Boolean(anchorEl)

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleClose = () => {
    setAnchorEl(null)
  }

  const handlePersonaSelect = (persona: PersonaRole) => {
    console.log('RoleSwitcher: User selected persona:', persona)
    setCurrentPersona(persona)
    handleClose()
    
    // Navigate to persona-specific dashboard using React Router
    const personaRoutes: Record<PersonaRole, string> = {
      EXECUTIVE: '/dashboard/executive',
      POLICY_OWNER: '/dashboard/policy-owner',
      ANALYST: '/dashboard/analyst',
      OPS_CLINICAL: '/dashboard/ops-clinical',
    }
    const route = personaRoutes[persona]
    if (route) {
      console.log('RoleSwitcher: Navigating to:', route)
      navigate(route)
    }
  }

  return (
    <Box>
      <Tooltip title={`Current view: ${currentConfig.label}`}>
        <Button
          onClick={handleClick}
          startIcon={currentConfig.icon}
          endIcon={<PersonIcon />}
          sx={{
            color: 'white',
            textTransform: 'none',
            minWidth: 'auto',
            px: 1.5,
            '&:hover': {
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
            },
          }}
        >
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', mr: 1 }}>
            <Typography variant="caption" sx={{ fontSize: '0.7rem', lineHeight: 1 }}>
              View
            </Typography>
            <Typography variant="body2" sx={{ fontSize: '0.875rem', fontWeight: 500 }}>
              {currentConfig.label}
            </Typography>
          </Box>
        </Button>
      </Tooltip>
      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
      >
        {availablePersonas.map((persona) => {
          const config = personaConfig[persona]
          const isSelected = persona === displayPersona
          return (
            <MenuItem
              key={persona}
              onClick={() => handlePersonaSelect(persona)}
              selected={isSelected}
              sx={{
                minWidth: 200,
                py: 1.5,
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, width: '100%' }}>
                <Box sx={{ color: isSelected ? 'primary.main' : 'text.secondary' }}>
                  {config.icon}
                </Box>
                <Box sx={{ flexGrow: 1 }}>
                  <Typography variant="body2" sx={{ fontWeight: isSelected ? 600 : 400 }}>
                    {config.label}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                    {config.description}
                  </Typography>
                </Box>
                {isSelected && (
                  <Chip
                    label="Active"
                    size="small"
                    color="primary"
                    sx={{ height: 20, fontSize: '0.65rem' }}
                  />
                )}
              </Box>
            </MenuItem>
          )
        })}
      </Menu>
    </Box>
  )
}

