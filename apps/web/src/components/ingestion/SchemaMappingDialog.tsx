/**
 * Schema Mapping Dialog - Shows detected columns and allows mapping configuration
 */
import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Alert,
  CircularProgress,
  Grid,
  Card,
  CardContent,
} from '@mui/material'
import { CheckCircle as CheckCircleIcon, Warning as WarningIcon } from '@mui/icons-material'

interface ColumnMapping {
  source_column: string
  canonical_column: string | null
  detected: boolean
  sample_value: any
}

interface SchemaMappingDialogProps {
  open: boolean
  onClose: () => void
  onConfirm: (mapping: any) => void
  schemaAnalysis: {
    detected_format?: string
    source_columns?: string[]
    sample_rows?: any[]
    suggested_mapping?: {
      column_mappings: Record<string, string>
      required_fields: string[]
      optional_fields: string[]
    }
    coverage?: {
      mapped: number
      total_canonical: number
      unmapped_source: string[]
    }
  } | null
  ingestionType: string
}

export default function SchemaMappingDialog({
  open,
  onClose,
  onConfirm,
  schemaAnalysis,
  ingestionType,
}: SchemaMappingDialogProps) {
  const [mappings, setMappings] = useState<Record<string, string>>({})
  const [canonicalFields, setCanonicalFields] = useState<string[]>([])

  useEffect(() => {
    if (schemaAnalysis?.suggested_mapping) {
      setMappings(schemaAnalysis.suggested_mapping.column_mappings || {})
      
      // Get canonical fields from required + optional
      const allFields = [
        ...(schemaAnalysis.suggested_mapping.required_fields || []),
        ...(schemaAnalysis.suggested_mapping.optional_fields || []),
      ]
      setCanonicalFields([...new Set(allFields)])
    }
  }, [schemaAnalysis])

  const handleMappingChange = (sourceColumn: string, canonicalColumn: string) => {
    setMappings((prev) => {
      const newMappings = { ...prev }
      if (canonicalColumn === '') {
        delete newMappings[sourceColumn]
      } else {
        newMappings[sourceColumn] = canonicalColumn
      }
      return newMappings
    })
  }

  const handleConfirm = () => {
    onConfirm({
      column_mappings: mappings,
      default_values: {},
      transformations: {},
      required_fields: schemaAnalysis?.suggested_mapping?.required_fields || [],
      optional_fields: schemaAnalysis?.suggested_mapping?.optional_fields || [],
    })
  }

  const getMappedStatus = (sourceColumn: string) => {
    return mappings[sourceColumn] ? 'mapped' : 'unmapped'
  }

  const getUnmappedCanonical = () => {
    const mappedCanonical = new Set(Object.values(mappings))
    return canonicalFields.filter((field) => !mappedCanonical.has(field))
  }

  if (!schemaAnalysis) {
    return null
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">Schema Mapping Configuration</Typography>
        </Box>
      </DialogTitle>
      <DialogContent dividers>
        <Box sx={{ mb: 3 }}>
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Detected Format
                  </Typography>
                  <Chip label={schemaAnalysis.detected_format || 'Unknown'} color="primary" size="small" />
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Mapping Coverage
                  </Typography>
                  <Typography variant="h6">
                    {schemaAnalysis.coverage?.mapped || 0} / {schemaAnalysis.coverage?.total_canonical || 0}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Box>

        {schemaAnalysis.coverage && schemaAnalysis.coverage.unmapped_source?.length > 0 && (
          <Alert severity="info" sx={{ mb: 2 }}>
            {schemaAnalysis.coverage.unmapped_source.length} source columns will be ignored
          </Alert>
        )}

        <Typography variant="subtitle1" gutterBottom sx={{ mt: 2, mb: 1 }}>
          Column Mappings
        </Typography>
        <TableContainer component={Paper} variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Source Column</TableCell>
                <TableCell>Sample Value</TableCell>
                <TableCell>Map To (Canonical)</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {schemaAnalysis.source_columns?.map((col) => {
                const mapped = mappings[col]
                const sampleValue = schemaAnalysis.sample_rows?.[0]?.[col]
                return (
                  <TableRow key={col}>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {col}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary" noWrap sx={{ maxWidth: 200 }}>
                        {sampleValue !== undefined && sampleValue !== null ? String(sampleValue).substring(0, 50) : '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <FormControl fullWidth size="small">
                        <Select
                          value={mapped || ''}
                          onChange={(e) => handleMappingChange(col, e.target.value)}
                          displayEmpty
                        >
                          <MenuItem value="">
                            <em>Don't map</em>
                          </MenuItem>
                          {canonicalFields.map((field) => (
                            <MenuItem key={field} value={field}>
                              {field}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </TableCell>
                    <TableCell>
                      {mapped ? (
                        <Chip
                          icon={<CheckCircleIcon />}
                          label="Mapped"
                          color="success"
                          size="small"
                        />
                      ) : (
                        <Chip
                          icon={<WarningIcon />}
                          label="Unmapped"
                          color="default"
                          size="small"
                        />
                      )}
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </TableContainer>

        {getUnmappedCanonical().length > 0 && (
          <Alert severity="warning" sx={{ mt: 2 }}>
            <Typography variant="body2" gutterBottom>
              <strong>Unmapped Required Fields:</strong>
            </Typography>
            <Typography variant="body2">
              {getUnmappedCanonical()
                .filter((f) => schemaAnalysis.suggested_mapping?.required_fields?.includes(f))
                .join(', ')}
            </Typography>
            <Typography variant="body2" sx={{ mt: 1 }}>
              These fields will use default values or may cause validation errors.
            </Typography>
          </Alert>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleConfirm} variant="contained" color="primary">
          Confirm Mapping
        </Button>
      </DialogActions>
    </Dialog>
  )
}

