/**
 * Data Viewer Component - View ingested data with filtering capabilities
 */
import { useState, useEffect } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  Grid,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
  Alert,
  Pagination,
  Stack,
} from '@mui/material'
import {
  Visibility as ViewIcon,
  FilterList as FilterIcon,
  Refresh as RefreshIcon,
  Close as CloseIcon,
  Download as DownloadIcon,
} from '@mui/icons-material'
import { apiClient } from '../lib/api'

interface Dataset {
  id: string
  dataset_type: string
  year: number
  month: number
  lob?: string
  market?: string
  record_count: number
  created_at: string
}

interface DatasetRow {
  [key: string]: any
}

interface DataViewerProps {
  dataset: Dataset
  onClose?: () => void
}

export default function DataViewer({ dataset, onClose }: DataViewerProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [rows, setRows] = useState<DatasetRow[]>([])
  const [schema, setSchema] = useState<any>(null)
  const [page, setPage] = useState(1)
  const [limit] = useState(100)
  const [total, setTotal] = useState(0)
  const [filtersOpen, setFiltersOpen] = useState(true)
  
  // Filter state
  const [filters, setFilters] = useState({
    lob: '',
    market: '',
    year: '',
    month: '',
    cpt_code: '',
    place_of_service: '',
    service_category: '',
    member_id: '',
    provider_id: '',
  })

  useEffect(() => {
    loadSchema()
    loadData()
  }, [dataset.id])

  useEffect(() => {
    loadData()
  }, [page, filters])

  const loadSchema = async () => {
    try {
      const schemaData = await apiClient.getDatasetSchema(dataset.id)
      setSchema(schemaData)
    } catch (err: any) {
      console.error('Error loading schema:', err)
      setError(err.detail || err.message || 'Failed to load schema')
    }
  }

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const params: any = {
        limit,
        offset: (page - 1) * limit,
      }

      // Add filters that have values
      Object.entries(filters).forEach(([key, value]) => {
        if (value && value.toString().trim() !== '') {
          params[key] = value
        }
      })

      const data = await apiClient.viewDataset(dataset.id, params)
      setRows(data.rows || [])
      setTotal(data.pagination?.total || data.record_count || 0)
    } catch (err: any) {
      console.error('Error loading data:', err)
      setError(err.detail || err.message || 'Failed to load data')
      setRows([])
    } finally {
      setLoading(false)
    }
  }

  const handleFilterChange = (field: string, value: string) => {
    setFilters((prev) => ({ ...prev, [field]: value }))
    setPage(1) // Reset to first page when filters change
  }

  const handleClearFilters = () => {
    setFilters({
      lob: '',
      market: '',
      year: '',
      month: '',
      cpt_code: '',
      place_of_service: '',
      service_category: '',
      member_id: '',
      provider_id: '',
    })
    setPage(1)
  }

  const handlePageChange = (_event: React.ChangeEvent<unknown>, newPage: number) => {
    setPage(newPage)
  }

  const columns = schema?.schema?.columns || []

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5">
          Data Viewer: {dataset.dataset_type} - {dataset.year}/{String(dataset.month).padStart(2, '0')}
        </Typography>
        <Box>
          <IconButton onClick={() => setFiltersOpen(!filtersOpen)} title="Toggle Filters">
            <FilterIcon />
          </IconButton>
          <IconButton onClick={loadData} title="Refresh">
            <RefreshIcon />
          </IconButton>
          {onClose && (
            <IconButton onClick={onClose} title="Close">
              <CloseIcon />
            </IconButton>
          )}
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Filters */}
      {filtersOpen && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Filters</Typography>
              <Button size="small" onClick={handleClearFilters}>
                Clear All
              </Button>
            </Box>
            <Grid container spacing={2}>
              {dataset.dataset_type === 'CLAIMS' && (
                <>
                  <Grid item xs={12} sm={6} md={3}>
                    <TextField
                      label="CPT Code"
                      fullWidth
                      size="small"
                      value={filters.cpt_code}
                      onChange={(e) => handleFilterChange('cpt_code', e.target.value)}
                      placeholder="e.g., 72148"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <TextField
                      label="Place of Service"
                      fullWidth
                      size="small"
                      value={filters.place_of_service}
                      onChange={(e) => handleFilterChange('place_of_service', e.target.value)}
                      placeholder="e.g., 11, 22"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <TextField
                      label="Service Category"
                      fullWidth
                      size="small"
                      value={filters.service_category}
                      onChange={(e) => handleFilterChange('service_category', e.target.value)}
                      placeholder="e.g., MRI, PT"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <TextField
                      label="Member ID"
                      fullWidth
                      size="small"
                      value={filters.member_id}
                      onChange={(e) => handleFilterChange('member_id', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <TextField
                      label="Provider ID"
                      fullWidth
                      size="small"
                      value={filters.provider_id}
                      onChange={(e) => handleFilterChange('provider_id', e.target.value)}
                    />
                  </Grid>
                </>
              )}
              <Grid item xs={12} sm={6} md={3}>
                <FormControl fullWidth size="small">
                  <InputLabel>LOB</InputLabel>
                  <Select
                    value={filters.lob}
                    label="LOB"
                    onChange={(e) => handleFilterChange('lob', e.target.value)}
                  >
                    <MenuItem value="">All</MenuItem>
                    <MenuItem value="COMMERCIAL">Commercial</MenuItem>
                    <MenuItem value="MA">Medicare Advantage</MenuItem>
                    <MenuItem value="MEDICAID">Medicaid</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <TextField
                  label="Market"
                  fullWidth
                  size="small"
                  value={filters.market}
                  onChange={(e) => handleFilterChange('market', e.target.value)}
                  placeholder="e.g., NYC, DFW"
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <TextField
                  label="Year"
                  fullWidth
                  size="small"
                  type="number"
                  value={filters.year}
                  onChange={(e) => handleFilterChange('year', e.target.value)}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <TextField
                  label="Month"
                  fullWidth
                  size="small"
                  type="number"
                  inputProps={{ min: 1, max: 12 }}
                  value={filters.month}
                  onChange={(e) => handleFilterChange('month', e.target.value)}
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Data Table */}
      <Paper>
        <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Showing {rows.length > 0 ? (page - 1) * limit + 1 : 0} - {Math.min(page * limit, total)} of {total} records
          </Typography>
          <Chip label={dataset.dataset_type} color="primary" size="small" />
        </Box>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : rows.length === 0 ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <Typography color="text.secondary">No data found</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Try adjusting your filters or check if data has been ingested
            </Typography>
          </Box>
        ) : (
          <>
            <TableContainer sx={{ maxHeight: 600 }}>
              <Table stickyHeader size="small">
                <TableHead>
                  <TableRow>
                    {columns.map((col: any) => (
                      <TableCell key={col.name} sx={{ fontWeight: 'bold' }}>
                        {col.name}
                      </TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {rows.map((row, idx) => (
                    <TableRow key={idx} hover>
                      {columns.map((col: any) => (
                        <TableCell key={col.name}>
                          {row[col.name] !== null && row[col.name] !== undefined
                            ? String(row[col.name])
                            : '-'}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            {total > limit && (
              <Box sx={{ p: 2, display: 'flex', justifyContent: 'center' }}>
                <Pagination
                  count={Math.ceil(total / limit)}
                  page={page}
                  onChange={handlePageChange}
                  color="primary"
                />
              </Box>
            )}
          </>
        )}
      </Paper>
    </Box>
  )
}

