/**
 * Dashboard Widget Component - Reusable widget wrapper with drag-and-drop support
 */
import { ReactNode } from 'react'
import {
  Card,
  CardContent,
  IconButton,
  Box,
  Typography,
} from '@mui/material'
import {
  DragIndicator as DragIcon,
  Close as CloseIcon,
} from '@mui/icons-material'

interface DashboardWidgetProps {
  id: string
  title: string
  children: ReactNode
  onRemove?: (id: string) => void
  draggable?: boolean
  onDragStart?: (e: React.DragEvent, id: string) => void
  onDragOver?: (e: React.DragEvent) => void
  onDrop?: (e: React.DragEvent, id: string) => void
  isDragging?: boolean
}

export default function DashboardWidget({
  id,
  title,
  children,
  onRemove,
  draggable = false,
  onDragStart,
  onDragOver,
  onDrop,
  isDragging = false,
}: DashboardWidgetProps) {
  const handleDragStart = (e: React.DragEvent) => {
    if (onDragStart) {
      onDragStart(e, id)
    }
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', id)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    if (onDragOver) {
      onDragOver(e)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    if (onDrop) {
      onDrop(e, id)
    }
  }

  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        opacity: isDragging ? 0.5 : 1,
        cursor: draggable ? 'move' : 'default',
        position: 'relative',
        '&:hover .widget-actions': {
          opacity: 1,
        },
      }}
      draggable={draggable}
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >
      <Box
        className="widget-actions"
        sx={{
          position: 'absolute',
          top: 8,
          right: 8,
          display: 'flex',
          gap: 0.5,
          opacity: 0,
          transition: 'opacity 0.2s',
          zIndex: 1,
        }}
      >
        {draggable && (
          <IconButton
            size="small"
            sx={{
              bgcolor: 'background.paper',
              '&:hover': { bgcolor: 'action.hover' },
            }}
            onMouseDown={(e) => {
              // Prevent drag from starting on the icon
              e.stopPropagation()
            }}
          >
            <DragIcon fontSize="small" />
          </IconButton>
        )}
        {onRemove && (
          <IconButton
            size="small"
            onClick={() => onRemove(id)}
            sx={{
              bgcolor: 'background.paper',
              '&:hover': { bgcolor: 'error.light', color: 'error.contrastText' },
            }}
          >
            <CloseIcon fontSize="small" />
          </IconButton>
        )}
      </Box>
      <CardContent sx={{ flexGrow: 1, pt: 2 }}>
        <Typography variant="h6" gutterBottom sx={{ pr: 4 }}>
          {title}
        </Typography>
        <Box sx={{ mt: 2 }}>{children}</Box>
      </CardContent>
    </Card>
  )
}
