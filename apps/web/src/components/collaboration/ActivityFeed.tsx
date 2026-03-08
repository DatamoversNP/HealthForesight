/**
 * Activity Feed Component - Epic 6
 * Displays activity events for a resource
 */
import { useState, useEffect } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  List,
  ListItem,
  ListItemText,
  Avatar,
  CircularProgress,
  Alert,
  Chip,
} from '@mui/material'
import {
  Create as CreateIcon,
  Edit as EditIcon,
  Comment as CommentIcon,
  CheckCircle as ApproveIcon,
  ChangeCircle as StateChangeIcon,
} from '@mui/icons-material'
import { apiClient } from '../../lib/api'

interface ActivityEvent {
  event_id: string
  resource_type: string
  resource_id: string
  event_type: string
  user_id: string
  description: string
  metadata?: Record<string, any>
  timestamp: string
}

interface ActivityFeedProps {
  resourceType?: string
  resourceId?: string
  limit?: number
}

export default function ActivityFeed({ resourceType, resourceId, limit = 50 }: ActivityFeedProps) {
  const [events, setEvents] = useState<ActivityEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadActivity()
  }, [resourceType, resourceId])

  const loadActivity = async () => {
    try {
      setLoading(true)
      setError(null)
      const params: any = { limit }
      if (resourceType) params.resource_type = resourceType
      if (resourceId) params.resource_id = resourceId
      const data = await apiClient.getActivityEvents(params)
      setEvents(Array.isArray(data) ? data : [])
    } catch (err: any) {
      console.error('Failed to load activity:', err)
      setError(err.detail || err.message || 'Failed to load activity')
    } finally {
      setLoading(false)
    }
  }

  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case 'created':
        return <CreateIcon />
      case 'updated':
        return <EditIcon />
      case 'commented':
        return <CommentIcon />
      case 'approved':
        return <ApproveIcon />
      case 'state_changed':
        return <StateChangeIcon />
      default:
        return <EditIcon />
    }
  }

  const getEventColor = (eventType: string) => {
    switch (eventType) {
      case 'created':
        return 'success'
      case 'updated':
        return 'info'
      case 'commented':
        return 'primary'
      case 'approved':
        return 'success'
      case 'state_changed':
        return 'warning'
      default:
        return 'default'
    }
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    )
  }

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Activity Feed
        </Typography>

        {events.length === 0 ? (
          <Typography variant="body2" color="text.secondary">
            No activity events found.
          </Typography>
        ) : (
          <List>
            {events.map((event) => (
              <ListItem
                key={event.event_id}
                alignItems="flex-start"
                sx={{ borderBottom: '1px solid', borderColor: 'divider' }}
              >
                <Avatar
                  sx={{
                    mr: 2,
                    bgcolor: `${getEventColor(event.event_type)}.main`,
                  }}
                >
                  {getEventIcon(event.event_type)}
                </Avatar>
                <ListItemText
                  primary={
                    <Box display="flex" alignItems="center" gap={1}>
                      <Typography variant="body2" fontWeight="medium">
                        {event.description}
                      </Typography>
                      <Chip
                        label={event.event_type}
                        color={getEventColor(event.event_type) as any}
                        size="small"
                      />
                    </Box>
                  }
                  secondary={
                    <Typography variant="caption" color="text.secondary">
                      User {event.user_id.substring(0, 8)} • {new Date(event.timestamp).toLocaleString()}
                    </Typography>
                  }
                />
              </ListItem>
            ))}
          </List>
        )}
      </CardContent>
    </Card>
  )
}

