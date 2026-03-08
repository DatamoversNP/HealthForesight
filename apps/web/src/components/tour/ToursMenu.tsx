import React from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Typography,
  Box,
} from '@mui/material'
import {
  Dashboard as DashboardIcon,
  Policy as PolicyIcon,
  Build as BuildIcon,
  FolderOpen as WorkspaceIcon,
  Analytics as AnalyticsIcon,
  Psychology as WhatIfIcon,
  CloudUpload as UploadIcon,
  HelpOutline as HelpIcon,
} from '@mui/icons-material'
import { useTour } from '../../contexts/TourContext'
import { TourModule } from '../../contexts/TourContext'

interface ToursMenuProps {
  anchorEl: HTMLElement | null
  open: boolean
  onClose: () => void
}

const tourMenuItems: Array<{
  module: TourModule
  label: string
  icon: React.ReactNode
  description: string
  path: string
}> = [
  {
    module: 'dashboard',
    label: 'Dashboard Tour',
    icon: <DashboardIcon />,
    description: 'Overview of the executive dashboard',
    path: '/',
  },
  {
    module: 'policies',
    label: 'Policy Catalog Tour',
    icon: <PolicyIcon />,
    description: 'Navigate and manage policies',
    path: '/policies',
  },
  {
    module: 'policy-builder',
    label: 'Policy Builder Tour',
    icon: <BuildIcon />,
    description: 'Create and configure policies',
    path: '/policies/builder',
  },
  {
    module: 'policy-workspace',
    label: 'Policy Workspace Tour',
    icon: <WorkspaceIcon />,
    description: 'Manage policy lifecycle and versions',
    path: '/policies', // Will need to navigate to a specific policy workspace
  },
  {
    module: 'analysis-workspace',
    label: 'Analysis Workspace Tour',
    icon: <AnalyticsIcon />,
    description: 'Analyze policy impact and results',
    path: '/analyses',
  },
  {
    module: 'whatif',
    label: 'What-If Analysis Tour',
    icon: <WhatIfIcon />,
    description: 'Run scenarios and compare outcomes',
    path: '/whatif',
  },
  {
    module: 'ingestions',
    label: 'Data Ingestion Tour',
    icon: <UploadIcon />,
    description: 'Upload and manage data ingestion',
    path: '/ingestions',
  },
]

export default function ToursMenu({ anchorEl, open, onClose }: ToursMenuProps) {
  const { startTour, hasCompletedTour } = useTour()
  const navigate = useNavigate()
  const location = useLocation()

  const handleTourSelect = (module: TourModule, path: string) => {
    onClose()
    
    // Navigate to the page if not already there
    if (location.pathname !== path && !location.pathname.startsWith(path)) {
      navigate(path)
      // Wait longer for navigation and page load before starting tour
      // This ensures all elements are rendered
      setTimeout(() => {
        startTour(module)
      }, 1500)
    } else {
      // Already on the page, wait a bit for elements to be ready
      setTimeout(() => {
        startTour(module)
      }, 500)
    }
  }

  return (
    <Menu
      anchorEl={anchorEl}
      open={open}
      onClose={onClose}
      anchorOrigin={{
        vertical: 'bottom',
        horizontal: 'right',
      }}
      transformOrigin={{
        vertical: 'top',
        horizontal: 'right',
      }}
      PaperProps={{
        sx: {
          minWidth: 320,
          maxWidth: 400,
          mt: 1,
        },
      }}
    >
      <Box sx={{ px: 2, py: 1.5, bgcolor: 'primary.main', color: 'primary.contrastText' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <HelpIcon />
          <Typography variant="subtitle1" fontWeight={600}>
            Product Tours
          </Typography>
        </Box>
        <Typography variant="caption" sx={{ opacity: 0.9, mt: 0.5, display: 'block' }}>
          Interactive guides to help you master the platform
        </Typography>
      </Box>
      <Divider />
      {tourMenuItems.map((item, index) => {
        const completed = hasCompletedTour(item.module)
        return (
          <MenuItem
            key={item.module}
            onClick={() => handleTourSelect(item.module, item.path)}
            sx={{
              py: 1.5,
              px: 2,
              '&:hover': {
                bgcolor: 'action.hover',
              },
            }}
          >
            <ListItemIcon sx={{ minWidth: 40, color: completed ? 'success.main' : 'primary.main' }}>
              {item.icon}
            </ListItemIcon>
            <ListItemText
              primary={
                <Box component="span" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography component="span" variant="body2" fontWeight={500}>
                    {item.label}
                  </Typography>
                  {completed && (
                    <Typography
                      component="span"
                      variant="caption"
                      sx={{
                        bgcolor: 'success.light',
                        color: 'success.contrastText',
                        px: 0.75,
                        py: 0.25,
                        borderRadius: 1,
                        fontSize: '0.65rem',
                        fontWeight: 600,
                      }}
                    >
                      ✓ Done
                    </Typography>
                  )}
                </Box>
              }
              secondary={item.description}
              secondaryTypographyProps={{
                variant: 'caption',
                color: 'text.secondary',
                component: 'span',
              }}
            />
          </MenuItem>
        )
      })}
      <Divider />
      <Box sx={{ px: 2, py: 1 }}>
        <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic' }}>
          💡 Tip: Tours are also available via the ❓ help icon on each page
        </Typography>
      </Box>
    </Menu>
  )
}

