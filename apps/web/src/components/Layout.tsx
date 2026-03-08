import React from 'react'
import { Outlet, useNavigate } from 'react-router-dom'
import {
  AppBar,
  Toolbar,
  Typography,
  Drawer,
  Divider,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Box,
  Container,
  IconButton,
  Menu,
  MenuItem,
  Avatar,
} from '@mui/material'
import {
  Dashboard as DashboardIcon,
  Policy as PolicyIcon,
  CloudUpload as UploadIcon,
  Analytics as AnalyticsIcon,
  Assessment as AssessmentIcon,
  FileDownload as ExportIcon,
  Gavel as DecisionIcon,
  Timeline as LineageIcon,
  Description as SpecsIcon,
  Schema as SchemaIcon,
  Psychology as WhatIfIcon,
  SettingsEthernet as PipelineIcon,
  AdminPanelSettings as AdminIcon,
  MonitorHeart as MonitoringIcon,
  VerifiedUser as QualityIcon,
  FolderOpen as ExplorerIcon,
  TrendingUp as TrendingIcon,
  CompareArrows as CompareIcon,
  Psychology as PsychologyIcon,
  Schedule as ScheduleIcon,
  Notifications as NotificationsIcon,
  DataObject as DataObjectIcon,
  Storage as StorageIcon,
  AccountCircle,
  Logout,
  HelpOutline as HelpIcon,
  Flag as FlagIcon,
  PlayArrow as PlayArrowIcon,
  History as HistoryIcon,
  StackedBarChart as PolicyImpactIcon,
} from '@mui/icons-material'
import { useAuth } from '../contexts/AuthContext'
import { useTour } from '../contexts/TourContext'
import RoleSwitcher from './rbac/RoleSwitcher'
import ToursMenu from './tour/ToursMenu'
import ConversationalAIButton from './conversational-ai/ConversationalAIButton'

const drawerWidth = 260

// HealthForesight Navigation – order and groups match attached spec
const menuGroups: { text: string; icon: React.ReactNode; path: string }[][] = [
  [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
    { text: 'Policy Verdicts', icon: <PolicyImpactIcon />, path: '/policy-verdicts' },
    { text: 'Policies', icon: <PolicyIcon />, path: '/policies' },
    { text: 'Policy Impact & Guidance', icon: <PolicyImpactIcon />, path: '/predicted-impacts' },
  ],
  [
    { text: 'Objectives Health', icon: <FlagIcon />, path: '/objectives-health' },
    { text: 'Baseline Analysis', icon: <TrendingIcon />, path: '/baseline-analysis' },
    { text: 'Observation Analysis', icon: <CompareIcon />, path: '/observation-analysis' },
    { text: 'Observation Run History', icon: <HistoryIcon />, path: '/observation-run-history' },
    { text: 'Predicted Impacts', icon: <PsychologyIcon />, path: '/predicted-impacts' },
    { text: 'What-If Scenarios', icon: <WhatIfIcon />, path: '/whatif' },
    { text: 'Scorecards', icon: <AssessmentIcon />, path: '/scorecards' },
  ],
  [
    { text: 'Cohorts', icon: <DataObjectIcon />, path: '/cohorts' },
    { text: 'Analyses', icon: <AnalyticsIcon />, path: '/analyses' },
  ],
  [
    { text: 'Data & Ingestion', icon: <UploadIcon />, path: '/ingestions' },
    { text: 'Data Model', icon: <SchemaIcon />, path: '/data-model' },
    { text: 'Pipelines', icon: <PipelineIcon />, path: '/pipelines' },
    { text: 'Pipeline Monitoring', icon: <MonitoringIcon />, path: '/pipeline-monitoring' },
    { text: 'Run Workflow', icon: <PlayArrowIcon />, path: '/run-workflow' },
    { text: 'Data Quality', icon: <QualityIcon />, path: '/data-quality' },
    { text: 'Data Explorer', icon: <ExplorerIcon />, path: '/data-explorer' },
  ],
  [
    { text: 'Exports', icon: <ExportIcon />, path: '/exports' },
    { text: 'Schedules', icon: <ScheduleIcon />, path: '/schedules' },
    { text: 'Notifications', icon: <NotificationsIcon />, path: '/notifications' },
  ],
  [
    { text: 'Decisions', icon: <DecisionIcon />, path: '/decisions' },
    { text: 'Lineage', icon: <LineageIcon />, path: '/lineage' },
    { text: 'Documentation', icon: <SpecsIcon />, path: '/documentation' },
    { text: 'Product Manual', icon: <SpecsIcon />, path: '/product-manual' },
    { text: 'QA Testing', icon: <HelpIcon />, path: '/qa-testing' },
    { text: 'Database Viewer', icon: <StorageIcon />, path: '/database-viewer' },
    { text: 'Audit Log', icon: <HistoryIcon />, path: '/audit-log' },
    { text: 'Admin', icon: <AdminIcon />, path: '/admin' },
  ],
]

export default function Layout() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const { state: tourState } = useTour()
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null)
  const [toursAnchorEl, setToursAnchorEl] = React.useState<null | HTMLElement>(null)
  
  // Account for tour panel drawer width when tour is active
  const tourPanelWidth = tourState.isRunning ? 420 : 0
  
  // Provide fallback for user in case it's null
  const displayName = user?.email || user?.name || 'User'

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleMenuClose = () => {
    setAnchorEl(null)
  }

  const handleToursMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setToursAnchorEl(event.currentTarget)
  }

  const handleToursMenuClose = () => {
    setToursAnchorEl(null)
  }

  const handleLogout = () => {
    handleMenuClose()
    logout()
  }

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}
      >
        <Toolbar>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexGrow: 1 }}>
            {/* HealthForesight Logo/Brand */}
            <Box 
              sx={{ display: 'flex', alignItems: 'center', gap: 1.5, cursor: 'pointer' }}
              onClick={() => navigate('/')}
            >
              {/* Logo Icon */}
              <Box
                component="img"
                src="/healthforesight-logo-icon.svg"
                alt="HealthForesight"
                sx={{
                  height: 48,
                  width: 48,
                  backgroundColor: '#FFFFFF',
                  borderRadius: '8px',
                  padding: '8px',
                  boxSizing: 'border-box',
                  boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
                }}
              />
              {/* Wordmark */}
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
                <Typography
                  variant="h6"
                  component="div"
                  sx={{
                    fontFamily: 'IBM Plex Sans, Inter, sans-serif',
                    fontWeight: 600,
                    fontSize: '1.25rem',
                    letterSpacing: '-0.01em',
                    lineHeight: 1.2,
                    color: '#FFFFFF',
                  }}
                >
                  Health<span style={{ color: '#5EEAD4' }}>Foresight</span>
                </Typography>
                <Typography
                  variant="caption"
                  sx={{
                    fontSize: '0.7rem',
                    opacity: 0.85,
                    display: { xs: 'none', md: 'block' },
                    color: 'rgba(255, 255, 255, 0.9)',
                    letterSpacing: '0.05em',
                    fontWeight: 500,
                  }}
                >
                  by DataMovers
                </Typography>
              </Box>
            </Box>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <RoleSwitcher />
            <IconButton 
              onClick={handleToursMenuOpen} 
              color="inherit" 
              size="small"
              title="Product Tours"
              sx={{
                '&:hover': {
                  bgcolor: 'rgba(255, 255, 255, 0.1)',
                },
              }}
            >
              <HelpIcon />
            </IconButton>
            <Typography
              variant="body2"
              sx={{
                display: { xs: 'none', sm: 'block' },
                color: 'rgba(255, 255, 255, 0.9)',
              }}
            >
              {displayName}
            </Typography>
            <IconButton onClick={handleMenuOpen} color="inherit" size="small">
              <AccountCircle />
            </IconButton>
            <Menu
              anchorEl={anchorEl}
              open={Boolean(anchorEl)}
              onClose={handleMenuClose}
            >
              <MenuItem onClick={handleLogout}>
                <ListItemIcon>
                  <Logout fontSize="small" />
                </ListItemIcon>
                Logout
              </MenuItem>
            </Menu>
            <ToursMenu
              anchorEl={toursAnchorEl}
              open={Boolean(toursAnchorEl)}
              onClose={handleToursMenuClose}
            />
          </Box>
        </Toolbar>
      </AppBar>
      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
          },
        }}
      >
        <Toolbar />
        <Box sx={{ overflow: 'auto' }}>
          <List>
            {menuGroups.map((group, groupIndex) => (
              <React.Fragment key={groupIndex}>
                {groupIndex > 0 && <Divider sx={{ my: 0.5 }} />}
                {group.map((item) => (
                  <ListItem key={item.text} disablePadding>
                    <ListItemButton onClick={() => navigate(item.path)}>
                      <ListItemIcon>{item.icon}</ListItemIcon>
                      <ListItemText primary={item.text} />
                    </ListItemButton>
                  </ListItem>
                ))}
              </React.Fragment>
            ))}
          </List>
        </Box>
      </Drawer>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          bgcolor: 'background.default',
          p: 3,
          marginLeft: `${tourPanelWidth}px`,
          transition: 'margin-left 0.3s ease',
        }}
      >
        <Toolbar />
        <Container maxWidth="xl">
          <Outlet />
        </Container>
      </Box>
      
      {/* Conversational AI Floating Button */}
      <ConversationalAIButton />
    </Box>
  )
}

