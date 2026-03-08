import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Container,
  Paper,
  Button,
  Typography,
  Box,
  Alert,
  CircularProgress,
} from '@mui/material'
import { useAuth } from '../contexts/AuthContext'
import { healthForesightColors } from '../theme/healthForesightTheme'

const OIDC_ISSUER = import.meta.env.VITE_OIDC_ISSUER || ''
const OIDC_CLIENT_ID = import.meta.env.VITE_OIDC_CLIENT_ID || 'uepi-web'
const REDIRECT_URI = `${window.location.origin}/login/callback`

export default function LoginPage() {
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const { login, isAuthenticated } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    // If already authenticated, redirect to home
    if (isAuthenticated) {
      navigate('/')
    }

    // Check for OIDC callback
    const urlParams = new URLSearchParams(window.location.search)
    const errorParam = urlParams.get('error')

    if (errorParam) {
      setError(`Authentication failed: ${errorParam}`)
      return
    }

    const code = urlParams.get('code')
    if (code) {
      handleOIDCCallback(code).catch(() => {})
    }
  }, [isAuthenticated, navigate])

  const handleOIDCCallback = async (code: string) => {
    setLoading(true)
    setError(null)

    try {
      // Exchange code for token
      // In production, this should be done server-side for security
      // For now, we'll use a mock token for development
      if (OIDC_ISSUER && OIDC_ISSUER !== '') {
        // Real OIDC flow would exchange code for token here
        // For MVP, we'll use a development token
        const mockToken = 'dev-token-' + Date.now()
        await login(mockToken)
      } else {
        // Development mode: use mock token
        const mockToken = 'dev-token-' + Date.now()
        await login(mockToken)
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  const handleOIDCLogin = () => {
    if (!OIDC_ISSUER || OIDC_ISSUER === '') {
      // Development mode: use mock login
      handleMockLogin()
      return
    }

    // Redirect to OIDC provider
    const authUrl = new URL(`${OIDC_ISSUER}/authorize`)
    authUrl.searchParams.set('client_id', OIDC_CLIENT_ID)
    authUrl.searchParams.set('redirect_uri', REDIRECT_URI)
    authUrl.searchParams.set('response_type', 'code')
    authUrl.searchParams.set('scope', 'openid profile email')
    authUrl.searchParams.set('state', 'random-state-' + Date.now())

    window.location.href = authUrl.toString()
  }

  const handleMockLogin = async () => {
    setLoading(true)
    setError(null)

    try {
      // For development, create a mock token
      const mockToken = 'dev-token-' + Date.now()
      await login(mockToken)
    } catch (err: any) {
      setError(err.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        {/* HealthForesight Logo */}
        <Box sx={{ mb: 4, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <Box
            component="img"
            src="/healthforesight-logo.svg"
            alt="HealthForesight"
            sx={{
              height: { xs: 56, sm: 64, md: 72 },
              width: 'auto',
            }}
          />
        </Box>

        <Paper sx={{ p: 4, width: '100%' }}>
          <Typography
            component="h2"
            variant="h6"
            align="center"
            gutterBottom
            sx={{
              fontFamily: 'IBM Plex Sans, Inter, sans-serif',
              fontWeight: 600,
              color: healthForesightColors.neutral.dark,
              mb: 2,
            }}
          >
            Sign In
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mt: 2, mb: 2 }}>
              {error}
            </Alert>
          )}

          <Box sx={{ mt: 3, mb: 2 }}>
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                <CircularProgress />
              </Box>
            ) : (
              <Button
                fullWidth
                variant="contained"
                size="large"
                onClick={handleOIDCLogin}
                disabled={loading}
              >
                {OIDC_ISSUER && OIDC_ISSUER !== '' ? 'Sign in with OIDC' : 'Sign in (Dev Mode)'}
              </Button>
            )}
          </Box>

          {(!OIDC_ISSUER || OIDC_ISSUER === '') && (
            <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 2 }}>
              Development mode: Using mock authentication
            </Typography>
          )}
        </Paper>
      </Box>
    </Container>
  )
}

