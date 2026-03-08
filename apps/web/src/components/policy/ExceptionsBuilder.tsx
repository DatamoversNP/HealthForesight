/**
 * Exceptions Builder Component - Step 5 of Policy Builder
 * Configure global exceptions (do not apply when)
 */
import { useState } from 'react'
import { Box, Button, Typography, Paper, List, ListItem, ListItemText, IconButton, FormControl, InputLabel, Select, MenuItem, TextField } from '@mui/material'
import { Add as AddIcon, Delete as DeleteIcon } from '@mui/icons-material'

interface ExceptionsBuilderProps {
  exceptions: any[]
  onChange: (exceptions: any[]) => void
}

const OPERATORS = [
  { value: 'IN', label: 'In' },
  { value: 'NOT_IN', label: 'Not In' },
  { value: 'EQUALS', label: 'Equals' },
]

const FIELDS = [
  { value: 'place_of_service', label: 'Place of Service (e.g., ER)' },
  { value: 'diagnosis', label: 'Diagnosis (ICD-10 codes)' },
  { value: 'provider_type', label: 'Provider Type' },
  { value: 'emergency', label: 'Emergency (true/false)' },
]

export default function ExceptionsBuilder({ exceptions, onChange }: ExceptionsBuilderProps) {
  const [newException, setNewException] = useState({
    field: 'place_of_service',
    operator: 'IN',
    value: '',
    description: '',
  })

  const handleAddException = () => {
    if (!newException.value) {
      return
    }
    onChange([...exceptions, { ...newException }])
    setNewException({ field: 'place_of_service', operator: 'IN', value: '', description: '' })
  }

  const handleRemoveException = (index: number) => {
    onChange(exceptions.filter((_, i) => i !== index))
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Global Exceptions
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Define conditions where this policy should NOT apply (e.g., emergency situations, ER visits).
      </Typography>

      {exceptions.length > 0 && (
        <Paper sx={{ p: 2, mb: 2 }}>
          <List dense>
            {exceptions.map((exception, index) => (
              <ListItem
                key={index}
                secondaryAction={
                  <IconButton edge="end" onClick={() => handleRemoveException(index)}>
                    <DeleteIcon />
                  </IconButton>
                }
              >
                <ListItemText
                  primary={`${exception.field} ${exception.operator} ${Array.isArray(exception.value) ? exception.value.join(', ') : exception.value}`}
                  secondary={exception.description || 'No description'}
                />
              </ListItem>
            ))}
          </List>
        </Paper>
      )}

      <Paper sx={{ p: 2 }}>
        <Typography variant="subtitle2" gutterBottom>
          Add Exception
        </Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <FormControl fullWidth>
            <InputLabel>Field</InputLabel>
            <Select
              value={newException.field}
              onChange={(e) => setNewException({ ...newException, field: e.target.value })}
              label="Field"
            >
              {FIELDS.map((field) => (
                <MenuItem key={field.value} value={field.value}>
                  {field.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl fullWidth>
            <InputLabel>Operator</InputLabel>
            <Select
              value={newException.operator}
              onChange={(e) => setNewException({ ...newException, operator: e.target.value })}
              label="Operator"
            >
              {OPERATORS.map((op) => (
                <MenuItem key={op.value} value={op.value}>
                  {op.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <TextField
            fullWidth
            label="Value"
            value={newException.value}
            onChange={(e) => setNewException({ ...newException, value: e.target.value })}
            placeholder={newException.operator === 'IN' ? 'Value1, Value2' : 'Value'}
            helperText={newException.operator === 'IN' ? 'Comma-separated list' : ''}
          />

          <TextField
            fullWidth
            label="Description (optional)"
            value={newException.description}
            onChange={(e) => setNewException({ ...newException, description: e.target.value })}
            placeholder="Human-readable explanation (e.g., 'Do not apply in emergency situations')"
          />

          <Button variant="contained" startIcon={<AddIcon />} onClick={handleAddException}>
            Add Exception
          </Button>
        </Box>
      </Paper>
    </Box>
  )
}

