/**
 * Comments Panel Component - Epic 6
 * Displays and manages comments on resources
 */
import { useState, useEffect } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  List,
  ListItem,
  ListItemText,
  Avatar,
  CircularProgress,
  Alert,
  Paper,
} from '@mui/material'
import {
  Send as SendIcon,
} from '@mui/icons-material'
import { apiClient } from '../../lib/api'

interface Comment {
  comment_id: string
  resource_type: string
  resource_id: string
  user_id: string
  content: string
  mentions: string[]
  parent_comment_id?: string
  created_at: string
  updated_at: string
}

interface CommentsPanelProps {
  resourceType: string
  resourceId: string
}

export default function CommentsPanel({ resourceType, resourceId }: CommentsPanelProps) {
  const [comments, setComments] = useState<Comment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [newComment, setNewComment] = useState('')

  useEffect(() => {
    loadComments()
  }, [resourceType, resourceId])

  const loadComments = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await apiClient.getComments({
        resource_type: resourceType,
        resource_id: resourceId,
      })
      setComments(Array.isArray(data) ? data : [])
    } catch (err: any) {
      console.error('Failed to load comments:', err)
      setError(err.detail || err.message || 'Failed to load comments')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async () => {
    if (!newComment.trim()) {
      return
    }

    try {
      setError(null)
      await apiClient.createComment({
        resource_type: resourceType,
        resource_id: resourceId,
        content: newComment.trim(),
      })
      setNewComment('')
      await loadComments()
    } catch (err: any) {
      console.error('Failed to create comment:', err)
      setError(err.detail || err.message || 'Failed to create comment')
    }
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Comments
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Comment Input */}
        <Box sx={{ mb: 2 }}>
          <TextField
            fullWidth
            multiline
            rows={3}
            placeholder="Add a comment..."
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            variant="outlined"
          />
          <Box sx={{ mt: 1, display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              variant="contained"
              startIcon={<SendIcon />}
              onClick={handleSubmit}
              disabled={!newComment.trim()}
            >
              Post Comment
            </Button>
          </Box>
        </Box>

        {/* Comments List */}
        {comments.length === 0 ? (
          <Typography variant="body2" color="text.secondary">
            No comments yet. Be the first to comment!
          </Typography>
        ) : (
          <List>
            {comments.map((comment) => (
              <ListItem
                key={comment.comment_id}
                alignItems="flex-start"
                sx={{ borderBottom: '1px solid', borderColor: 'divider' }}
              >
                <Avatar sx={{ mr: 2, bgcolor: 'primary.main' }}>
                  {comment.user_id.substring(0, 2).toUpperCase()}
                </Avatar>
                <ListItemText
                  primary={
                    <Box>
                      <Typography variant="body2" fontWeight="medium" component="span">
                        User {comment.user_id.substring(0, 8)}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                        {new Date(comment.created_at).toLocaleString()}
                      </Typography>
                    </Box>
                  }
                  secondary={
                    <Typography variant="body2" sx={{ mt: 0.5, whiteSpace: 'pre-wrap' }}>
                    {comment.content}
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

