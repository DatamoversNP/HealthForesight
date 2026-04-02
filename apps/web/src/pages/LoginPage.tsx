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
  TextField,
  Divider,
} from '@mui/material'
import { useAuth } from '../contexts/AuthContext'
import { apiClient } from '../lib/api'
import { healthForesightColors } from '../theme/healthForesightTheme'

const OIDC_ISSUER = import.meta.env.VITE_OIDC_ISSUER || ''
const OIDC_CLIENT_ID = import.meta.env.VITE_OIDC_CLIENT_ID || 'uepi-web'
const REDIRECT_URI = `${window.location.origin}/login/callback`

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const { login, isAuthenticated } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/')
    }

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
      if (OIDC_ISSUER && OIDC_ISSUER !== '') {
        const mockToken = 'dev-token-' + Date.now()
        await login(mockToken)
      } else {
        await login('dev-token-' + Date.now())
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  const handleEmailPasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    const trimmedEmail = email.trim()
    if (!trimmedEmail || !password) {
      setError('Please enter email and password.')
      return
    }
    setLoading(true)
    try {
      const res = await apiClient.login(trimmedEmail, password) as { access_token?: string }
      const token = res?.access_token
      if (!token) {
        setError('Invalid response from server.')
        return
      }
      await login(token)
    } catch (err: any) {
      const raw =
        err?.detail ??
        err?.response?.data?.detail ??
        (Array.isArray(err?.response?.data?.detail)
          ? err.response.data.detail.map((d: any) => d?.msg || d).join(' ')
          : null) ??
        err?.message
      const msg =
        typeof raw === 'string'
          ? raw
          : raw != null
            ? String(raw)
            : 'Invalid email or password.'
      if (err?.status === 503 || /database|PostgreSQL|DATABASE_URL|unavailable/i.test(msg)) {
        setError(
          `${msg}\n\nIf this mentions the database: set DATABASE_URL on the API app, open PostgreSQL firewall to Azure, run migrations + seed (see scripts/azure/seed-azure-db.sh).`
        )
      } else {
        setError(msg)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleOIDCLogin = () => {
    if (!OIDC_ISSUER || OIDC_ISSUER === '') {
      setError('OIDC is not configured. Sign in with email and password above.')
      return
    }
    const authUrl = new URL(`${OIDC_ISSUER}/authorize`)
    authUrl.searchParams.set('client_id', OIDC_CLIENT_ID)
    authUrl.searchParams.set('redirect_uri', REDIRECT_URI)
    authUrl.searchParams.set('response_type', 'code')
    authUrl.searchParams.set('scope', 'openid profile email')
    authUrl.searchParams.set('state', 'random-state-' + Date.now())
    window.location.href = authUrl.toString()
  }

  return (
    <Container maxWidth="sm">
      <Box sx={{ marginTop: 8, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <Box sx={{ mb: 4, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <Box
            component="img"
            src="/healthforesight-logo.svg"
            alt="HealthForesight"
            sx={{ height: { xs: 56, sm: 64, md: 72 }, width: 'auto' }}
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
              color: healthForesightColors.neutral?.dark ?? '#1a1a1a',
              mb: 2,
            }}
          >
            Sign in
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mt: 2, mb: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleEmailPasswordLogin} sx={{ mt: 2 }}>
            <TextField
              margin="normal"
              fullWidth
              label="Email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
            />
            <TextField
              margin="normal"
              fullWidth
              label="Password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              sx={{ mt: 3, mb: 2 }}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} color="inherit" /> : 'Sign in with email'}
            </Button>
          </Box>

          {OIDC_ISSUER && OIDC_ISSUER !== '' && (
            <>
              <Divider sx={{ my: 2 }}>or</Divider>
              <Button
                fullWidth
                variant="outlined"
                size="large"
                onClick={handleOIDCLogin}
                disabled={loading}
              >
                Sign in with organization (SSO)
              </Button>
            </>
          )}
        </Paper>
      </Box>
    </Container>
  )
}

