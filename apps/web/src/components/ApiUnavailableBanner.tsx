import { Alert, Button, Box } from '@mui/material'
import { useAuth } from '../contexts/AuthContext'

/**
 * Shows a banner when the API is unreachable (e.g. connection refused).
 * Helps users know they need to start the API server.
 */
export default function ApiUnavailableBanner() {
  const { apiUnavailable, clearApiUnavailable } = useAuth()
  if (!apiUnavailable) return null

  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
  const baseUrl = apiUrl.replace(/\/api\/v1\/?$/, '')

  return (
    <Box sx={{ position: 'sticky', top: 0, zIndex: 1300 }}>
      <Alert
        severity="error"
        action={
          <Button color="inherit" size="small" onClick={clearApiUnavailable}>
            Dismiss
          </Button>
        }
      >
        <strong>Cannot reach API.</strong> The server at {baseUrl} is not responding (connection refused).
        Start the API from the project root: <code style={{ background: 'rgba(0,0,0,0.1)', padding: '2px 6px', borderRadius: 4 }}>./restart_api_now.sh</code> or <code style={{ background: 'rgba(0,0,0,0.1)', padding: '2px 6px', borderRadius: 4 }}>./start_api_and_worker.sh api</code>.
      </Alert>
    </Box>
  )
}
