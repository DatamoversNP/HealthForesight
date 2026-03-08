import React, { useState } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Rating,
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
} from '@mui/material'
import {
  ThumbUp as ThumbUpIcon,
  ThumbDown as ThumbDownIcon,
  Send as SendIcon,
} from '@mui/icons-material'
import { useTour } from '../../contexts/TourContext'
import { TourModule } from '../../contexts/TourContext'

interface TourFeedbackProps {
  module: TourModule
  open: boolean
  onClose: () => void
  onSkip?: () => void
}

export default function TourFeedback({ module, open, onClose, onSkip }: TourFeedbackProps) {
  const { completeTour } = useTour()
  const [rating, setRating] = useState<number | null>(null)
  const [helpful, setHelpful] = useState<boolean | null>(null)
  const [feedback, setFeedback] = useState('')
  const [category, setCategory] = useState<string>('')
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async () => {
    setSubmitting(true)
    
    // Save feedback to localStorage (in production, send to API)
    const feedbackData = {
      module,
      rating,
      helpful,
      feedback,
      category,
      timestamp: new Date().toISOString(),
    }
    
    try {
      const existingFeedback = JSON.parse(localStorage.getItem('uepi_tour_feedback') || '[]')
      existingFeedback.push(feedbackData)
      localStorage.setItem('uepi_tour_feedback', JSON.stringify(existingFeedback))
      
      // Mark tour as completed
      completeTour(module)
      
      onClose()
    } catch (error) {
      console.error('Error saving feedback:', error)
    } finally {
      setSubmitting(false)
    }
  }

  const handleSkip = () => {
    completeTour(module)
    onClose()
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="h6">Tour Feedback</Typography>
          <Chip label={module.replace('-', ' ')} size="small" color="primary" />
        </Box>
      </DialogTitle>
      <DialogContent>
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            How would you rate this tour?
          </Typography>
          <Rating
            value={rating}
            onChange={(event, newValue) => setRating(newValue)}
            size="large"
            sx={{ mb: 3 }}
          />
        </Box>

        <Box sx={{ mb: 3 }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Was this tour helpful?
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
            <Button
              variant={helpful === true ? 'contained' : 'outlined'}
              startIcon={<ThumbUpIcon />}
              onClick={() => setHelpful(true)}
              size="small"
            >
              Yes
            </Button>
            <Button
              variant={helpful === false ? 'contained' : 'outlined'}
              color="error"
              startIcon={<ThumbDownIcon />}
              onClick={() => setHelpful(false)}
              size="small"
            >
              No
            </Button>
          </Box>
        </Box>

        <FormControl fullWidth sx={{ mb: 2 }}>
          <InputLabel>Feedback Category</InputLabel>
          <Select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            label="Feedback Category"
          >
            <MenuItem value="content">Content Quality</MenuItem>
            <MenuItem value="clarity">Clarity & Understanding</MenuItem>
            <MenuItem value="completeness">Completeness</MenuItem>
            <MenuItem value="targeting">Element Targeting</MenuItem>
            <MenuItem value="other">Other</MenuItem>
          </Select>
        </FormControl>

        <TextField
          fullWidth
          multiline
          rows={4}
          label="Additional Feedback (Optional)"
          placeholder="Tell us what you liked, what could be improved, or any suggestions..."
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          sx={{ mb: 2 }}
        />

        <Typography variant="caption" color="text.secondary">
          Your feedback helps us improve the product tours. Thank you for taking the time!
        </Typography>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2, pt: 1 }}>
        <Button 
          onClick={onSkip || handleSkip} 
          color="inherit"
          sx={{ textTransform: 'none' }}
        >
          Skip Feedback
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          startIcon={<SendIcon />}
          disabled={submitting || rating === null}
          sx={{ textTransform: 'none' }}
        >
          Submit Feedback
        </Button>
      </DialogActions>
    </Dialog>
  )
}

