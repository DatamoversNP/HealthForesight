/**
 * Marketing Website Layout
 * Enterprise-grade navigation and structure for public-facing site
 */
import React, { useState, useEffect } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Container,
  useScrollTrigger,
  Slide,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  useMediaQuery,
  useTheme,
} from '@mui/material'
import { Menu as MenuIcon, Close as CloseIcon } from '@mui/icons-material'
import { healthForesightColors } from '../../theme/healthForesightTheme'

interface Props {
  children?: React.ReactElement
}

function HideOnScroll(props: Props) {
  const { children } = props
  const trigger = useScrollTrigger()

  if (!children) {
    return <div />
  }

  return (
    <Slide appear={false} direction="down" in={!trigger}>
      {children}
    </Slide>
  )
}

const navigationItems = [
  { label: 'Platform', path: '/platform' },
  { label: 'Solutions', path: '/solutions' },
  { label: 'How It Works', path: '/how-it-works' },
  { label: 'Who It\'s For', path: '/who-its-for' },
  { label: 'Insights', path: '/insights' },
  { label: 'Company', path: '/company' },
]

export default function MarketingLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const [scrolled, setScrolled] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20)
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const handleMobileMenuToggle = () => {
    setMobileMenuOpen(!mobileMenuOpen)
  }

  const handleNavigation = (path: string) => {
    navigate(path)
    setMobileMenuOpen(false)
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <HideOnScroll>
        <AppBar
          position="sticky"
          elevation={scrolled ? 2 : 0}
          sx={{
            backgroundColor: '#FFFFFF',
            borderBottom: `1px solid ${healthForesightColors.neutral.light}`,
            transition: 'all 0.3s ease',
          }}
        >
          <Toolbar 
            sx={{ 
              py: { xs: 1, md: 1.5 },
              minHeight: { xs: 56, md: 64 },
            }}
          >
            <Container 
              maxWidth="xl" 
              sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                width: '100%',
                px: { xs: 2, sm: 3, md: 4 },
              }}
            >
              <Box
                component="a"
                href="/"
                onClick={(e) => {
                  e.preventDefault()
                  navigate('/')
                }}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  cursor: 'pointer',
                  mr: { xs: 2, md: 6 },
                  textDecoration: 'none',
                  '&:hover': {
                    opacity: 0.8,
                  },
                  transition: 'opacity 0.2s ease',
                }}
              >
                <Box
                  component="img"
                  src="/healthforesight-logo.svg"
                  alt="HealthForesight"
                  sx={{
                    height: { xs: 32, sm: 36, md: 44 },
                    width: 'auto',
                  }}
                />
              </Box>

              {/* Desktop Navigation */}
              <Box 
                sx={{ 
                  flexGrow: 1, 
                  display: { xs: 'none', md: 'flex' }, 
                  gap: { md: 3, lg: 4 }, 
                  ml: { md: 4 } 
                }}
              >
                {navigationItems.map((item) => (
                  <Button
                    key={item.path}
                    onClick={() => navigate(item.path)}
                    sx={{
                      color:
                        location.pathname === item.path
                          ? healthForesightColors.primary.main
                          : healthForesightColors.neutral.dark,
                      fontWeight: location.pathname === item.path ? 600 : 400,
                      fontSize: { md: '14px', lg: '15px' },
                      textTransform: 'none',
                      minHeight: 44, // Touch target
                      '&:hover': {
                        backgroundColor: 'transparent',
                        color: healthForesightColors.primary.main,
                      },
                    }}
                  >
                    {item.label}
                  </Button>
                ))}
              </Box>

              {/* Desktop CTA Button */}
              <Button
                variant="contained"
                onClick={() => navigate('/request-demo')}
                sx={{
                  display: { xs: 'none', md: 'inline-flex' },
                  backgroundColor: healthForesightColors.primary.main,
                  color: '#FFFFFF',
                  px: { md: 2.5, lg: 3 },
                  py: 1,
                  fontWeight: 500,
                  fontSize: { md: '14px', lg: '15px' },
                  minHeight: 44,
                  '&:hover': {
                    backgroundColor: healthForesightColors.primary.dark,
                  },
                }}
              >
                Request Demo
              </Button>

              {/* Mobile Menu Button */}
              <IconButton
                onClick={handleMobileMenuToggle}
                sx={{
                  display: { xs: 'flex', md: 'none' },
                  ml: 'auto',
                  color: healthForesightColors.neutral.dark,
                  minWidth: 44,
                  minHeight: 44,
                }}
                aria-label="menu"
              >
                {mobileMenuOpen ? <CloseIcon /> : <MenuIcon />}
              </IconButton>
            </Container>
          </Toolbar>

          {/* Mobile Drawer */}
          <Drawer
            anchor="right"
            open={mobileMenuOpen}
            onClose={handleMobileMenuToggle}
            PaperProps={{
              sx: {
                width: { xs: '85vw', sm: 320 },
                maxWidth: 400,
              },
            }}
          >
            <Box sx={{ pt: 2 }}>
              <List sx={{ px: 2 }}>
                {navigationItems.map((item) => (
                  <ListItem key={item.path} disablePadding>
                    <ListItemButton
                      onClick={() => handleNavigation(item.path)}
                      selected={location.pathname === item.path}
                      sx={{
                        minHeight: 48,
                        borderRadius: 1,
                        mb: 0.5,
                        '&.Mui-selected': {
                          backgroundColor: `${healthForesightColors.primary.main}15`,
                          color: healthForesightColors.primary.main,
                          fontWeight: 600,
                        },
                      }}
                    >
                      <ListItemText 
                        primary={item.label}
                        primaryTypographyProps={{
                          fontSize: '16px',
                        }}
                      />
                    </ListItemButton>
                  </ListItem>
                ))}
                <ListItem disablePadding sx={{ mt: 2 }}>
                  <Button
                    fullWidth
                    variant="contained"
                    onClick={() => handleNavigation('/request-demo')}
                    sx={{
                      backgroundColor: healthForesightColors.primary.main,
                      color: '#FFFFFF',
                      py: 1.5,
                      fontWeight: 600,
                      minHeight: 48,
                      '&:hover': {
                        backgroundColor: healthForesightColors.primary.dark,
                      },
                    }}
                  >
                    Request Demo
                  </Button>
                </ListItem>
              </List>
            </Box>
          </Drawer>
        </AppBar>
      </HideOnScroll>

      <Box component="main" sx={{ flexGrow: 1 }}>
        <Outlet />
      </Box>

      {/* Footer */}
      <Box
        component="footer"
        sx={{
          backgroundColor: healthForesightColors.neutral.dark,
          color: '#FFFFFF',
          py: { xs: 4, md: 6 },
          mt: { xs: 8, md: 12 },
        }}
      >
        <Container 
          maxWidth="xl"
          sx={{
            px: { xs: 2, sm: 3, md: 4 },
          }}
        >
          <Box 
            sx={{ 
              display: 'grid',
              gridTemplateColumns: {
                xs: '1fr',
                sm: '1fr 1fr',
                md: '2fr 1fr 1fr 1fr',
              },
              gap: { xs: 4, md: 4 },
              mb: { xs: 3, md: 4 },
            }}
          >
            {/* Logo and Description */}
            <Box sx={{ mb: { xs: 2, md: 0 } }}>
              <Box
                component="img"
                src="/healthforesight-logo.svg"
                alt="HealthForesight"
                sx={{
                  height: { xs: 36, md: 40 },
                  width: 'auto',
                  mb: 2,
                  opacity: 0.9,
                }}
              />
              <Typography 
                variant="body2" 
                sx={{ 
                  color: 'rgba(255, 255, 255, 0.7)', 
                  maxWidth: { xs: '100%', md: 300 },
                  fontSize: { xs: '14px', md: '15px' },
                  lineHeight: 1.6,
                }}
              >
                Decision intelligence for utilization policy impact. Evidence over intuition.
              </Typography>
            </Box>

            {/* Platform Links */}
            <Box>
              <Typography 
                variant="subtitle2" 
                sx={{ 
                  fontWeight: 600, 
                  mb: { xs: 1.5, md: 2 },
                  fontSize: { xs: '14px', md: '15px' },
                }}
              >
                Platform
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: { xs: 0.5, md: 1 } }}>
                <Button
                  onClick={() => navigate('/platform')}
                  sx={{ 
                    color: 'rgba(255, 255, 255, 0.7)', 
                    justifyContent: 'flex-start',
                    fontSize: { xs: '14px', md: '15px' },
                    minHeight: { xs: 40, md: 36 },
                    py: { xs: 1, md: 0.5 },
                  }}
                >
                  Capabilities
                </Button>
                <Button
                  onClick={() => navigate('/how-it-works')}
                  sx={{ 
                    color: 'rgba(255, 255, 255, 0.7)', 
                    justifyContent: 'flex-start',
                    fontSize: { xs: '14px', md: '15px' },
                    minHeight: { xs: 40, md: 36 },
                    py: { xs: 1, md: 0.5 },
                  }}
                >
                  How It Works
                </Button>
              </Box>
            </Box>

            {/* Company Links */}
            <Box>
              <Typography 
                variant="subtitle2" 
                sx={{ 
                  fontWeight: 600, 
                  mb: { xs: 1.5, md: 2 },
                  fontSize: { xs: '14px', md: '15px' },
                }}
              >
                Company
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: { xs: 0.5, md: 1 } }}>
                <Button
                  onClick={() => navigate('/company')}
                  sx={{ 
                    color: 'rgba(255, 255, 255, 0.7)', 
                    justifyContent: 'flex-start',
                    fontSize: { xs: '14px', md: '15px' },
                    minHeight: { xs: 40, md: 36 },
                    py: { xs: 1, md: 0.5 },
                  }}
                >
                  About
                </Button>
                <Button
                  onClick={() => navigate('/insights')}
                  sx={{ 
                    color: 'rgba(255, 255, 255, 0.7)', 
                    justifyContent: 'flex-start',
                    fontSize: { xs: '14px', md: '15px' },
                    minHeight: { xs: 40, md: 36 },
                    py: { xs: 1, md: 0.5 },
                  }}
                >
                  Insights
                </Button>
              </Box>
            </Box>

            {/* Contact Links */}
            <Box>
              <Typography 
                variant="subtitle2" 
                sx={{ 
                  fontWeight: 600, 
                  mb: { xs: 1.5, md: 2 },
                  fontSize: { xs: '14px', md: '15px' },
                }}
              >
                Contact
              </Typography>
              <Button
                onClick={() => navigate('/request-demo')}
                sx={{ 
                  color: 'rgba(255, 255, 255, 0.7)', 
                  justifyContent: 'flex-start',
                  fontSize: { xs: '14px', md: '15px' },
                  minHeight: { xs: 40, md: 36 },
                  py: { xs: 1, md: 0.5 },
                }}
              >
                Request Demo
              </Button>
            </Box>
          </Box>
          <Box 
            sx={{ 
              mt: { xs: 3, md: 4 }, 
              pt: { xs: 3, md: 4 }, 
              borderTop: '1px solid rgba(255, 255, 255, 0.1)' 
            }}
          >
            <Typography 
              variant="caption" 
              sx={{ 
                color: 'rgba(255, 255, 255, 0.5)',
                fontSize: { xs: '12px', md: '13px' },
              }}
            >
              © {new Date().getFullYear()} HealthForesight. All rights reserved.
            </Typography>
          </Box>
        </Container>
      </Box>
    </Box>
  )
}
