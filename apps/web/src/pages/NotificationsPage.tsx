/**
 * Notifications Center Page - View and manage system notifications
 */
import { useState, useEffect } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  IconButton,
  Paper,
  Typography,
  Alert,
  Tabs,
  Tab,
  Badge,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
} from '@mui/material'
import {
  Notifications as NotificationsIcon,
  NotificationsActive as NotificationsActiveIcon,
  CheckCircle as ReadIcon,
  Info as InfoIcon,
  CheckCircle as SuccessIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material'
import { apiClient } from '../lib/api'
import { format } from 'date-fns'
import { healthForesightColors } from '../theme/healthForesightTheme'

interface Notification {
  id: string
  type: string
  category: string
  title: string
  message: string
  action_url?: string
  read: boolean
  created_at: string
  read_at?: string
}

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [unreadCount, setUnreadCount] = useState(0)
  const [filter, setFilter] = useState<'all' | 'unread'>('all')

  useEffect(() => {
    loadNotifications()
    loadUnreadCount()
    // Refresh every 30 seconds
    const interval = setInterval(() => {
      loadNotifications()
      loadUnreadCount()
    }, 30000)
    return () => clearInterval(interval)
  }, [filter])

  const loadNotifications = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await apiClient.getNotifications(filter === 'unread', 100)
      setNotifications(Array.isArray(data) ? data : [])
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to load notifications')
      console.error('Failed to load notifications:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadUnreadCount = async () => {
    try {
      const data = await apiClient.getUnreadNotificationCount()
      setUnreadCount(data.count || 0)
    } catch (err: any) {
      console.error('Failed to load unread count:', err)
    }
  }

  const handleMarkAsRead = async (notificationId: string) => {
    try {
      setError(null)
      await apiClient.markNotificationRead(notificationId)
      loadNotifications()
      loadUnreadCount()
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to mark notification as read')
    }
  }

  const handleMarkAllAsRead = async () => {
    try {
      setError(null)
      await apiClient.markAllNotificationsRead()
      loadNotifications()
      loadUnreadCount()
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to mark all as read')
    }
  }

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'SUCCESS':
        return <SuccessIcon color="success" />
      case 'WARNING':
        return <WarningIcon color="warning" />
      case 'ERROR':
        return <ErrorIcon color="error" />
      default:
        return <InfoIcon color="info" />
    }
  }

  const getNotificationColor = (type: string): 'success' | 'warning' | 'error' | 'info' | 'default' => {
    switch (type) {
      case 'SUCCESS':
        return 'success'
      case 'WARNING':
        return 'warning'
      case 'ERROR':
        return 'error'
      default:
        return 'info'
    }
  }

  if (loading && notifications.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    )
  }

  const unreadNotifications = notifications.filter(n => !n.read)
  const readNotifications = notifications.filter(n => n.read)

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="h4" component="h1">
            Notifications
          </Typography>
          {unreadCount > 0 && (
            <Badge badgeContent={unreadCount} color="error">
              <NotificationsActiveIcon color="action" />
            </Badge>
          )}
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          {unreadNotifications.length > 0 && (
            <Button
              variant="outlined"
              startIcon={<ReadIcon />}
              onClick={handleMarkAllAsRead}
            >
              Mark All Read
            </Button>
          )}
          <IconButton onClick={loadNotifications} title="Refresh">
            <RefreshIcon />
          </IconButton>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Paper sx={{ mb: 2 }}>
        <Tabs value={filter} onChange={(_, newValue) => setFilter(newValue)}>
          <Tab
            label={
              <Badge badgeContent={unreadCount} color="error">
                All
              </Badge>
            }
            value="all"
          />
          <Tab
            label={
              <Badge badgeContent={unreadCount} color="error">
                Unread
              </Badge>
            }
            value="unread"
          />
        </Tabs>
      </Paper>

      {notifications.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <NotificationsIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No notifications
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {filter === 'unread' 
              ? 'You have no unread notifications'
              : 'You have no notifications yet'}
          </Typography>
        </Paper>
      ) : (
        <Box>
          {/* Unread Notifications */}
          {unreadNotifications.length > 0 && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Badge badgeContent={unreadNotifications.length} color="error">
                    <NotificationsActiveIcon />
                  </Badge>
                  Unread ({unreadNotifications.length})
                </Typography>
                <List>
                  {unreadNotifications.map((notification) => (
                    <ListItem
                      key={notification.id}
                      sx={{
                        bgcolor: 'action.hover',
                        mb: 1,
                        borderRadius: 1,
                        border: '1px solid',
                        borderColor: 'divider',
                      }}
                    >
                      <ListItemIcon>{getNotificationIcon(notification.type)}</ListItemIcon>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                            <Typography variant="subtitle2" fontWeight={600}>
                              {notification.title}
                            </Typography>
                            <Chip
                              label={notification.category}
                              size="small"
                              variant="outlined"
                            />
                            <Chip
                              label={notification.type}
                              size="small"
                              color={getNotificationColor(notification.type)}
                            />
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography variant="body2" color="text.secondary">
                              {notification.message}
                            </Typography>
                            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                              {format(new Date(notification.created_at), 'MMM d, yyyy HH:mm')}
                            </Typography>
                          </Box>
                        }
                      />
                      <ListItemSecondaryAction>
                        <IconButton
                          edge="end"
                          onClick={() => handleMarkAsRead(notification.id)}
                          title="Mark as read"
                        >
                          <ReadIcon fontSize="small" />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          )}

          {/* Read Notifications */}
          {filter === 'all' && readNotifications.length > 0 && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <NotificationsIcon />
                  Read ({readNotifications.length})
                </Typography>
                <List>
                  {readNotifications.map((notification) => (
                    <ListItem
                      key={notification.id}
                      sx={{
                        opacity: 0.7,
                        mb: 1,
                        borderRadius: 1,
                        border: '1px solid',
                        borderColor: 'divider',
                      }}
                    >
                      <ListItemIcon>{getNotificationIcon(notification.type)}</ListItemIcon>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                            <Typography variant="subtitle2">
                              {notification.title}
                            </Typography>
                            <Chip
                              label={notification.category}
                              size="small"
                              variant="outlined"
                            />
                            <Chip
                              label={notification.type}
                              size="small"
                              color={getNotificationColor(notification.type)}
                              variant="outlined"
                            />
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography variant="body2" color="text.secondary">
                              {notification.message}
                            </Typography>
                            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                              {format(new Date(notification.created_at), 'MMM d, yyyy HH:mm')}
                              {notification.read_at && (
                                <span> • Read {format(new Date(notification.read_at), 'MMM d, HH:mm')}</span>
                              )}
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          )}
        </Box>
      )}
    </Box>
  )
}
