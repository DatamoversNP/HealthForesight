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
  InputAdornment,
  Toolbar,
  Tooltip,
} from '@mui/material'
import {
  Visibility as ViewIcon,
  FilterList as FilterIcon,
  Refresh as RefreshIcon,
  Close as CloseIcon,
  Download as DownloadIcon,
  Search as SearchIcon,
  Clear as ClearIcon,
} from '@mui/icons-material'
import { apiClient } from '../lib/api'
import CoverageMetrics from './ingestion/CoverageMetrics'
import { healthForesightColors } from '../theme/healthForesightTheme'

interface EnhancedDataViewerProps {
  ingestion: any
  dataType: 'source' | 'curated'
  onClose?: () => void
}

export default function EnhancedDataViewer({ ingestion, dataType, onClose }: EnhancedDataViewerProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [rows, setRows] = useState<any[]>([])
  const [columns, setColumns] = useState<any[]>([])
  const [page, setPage] = useState(1)
  const [limit] = useState(100)
  const [total, setTotal] = useState(0)
  const [filtersOpen, setFiltersOpen] = useState(true)
  const [coverage, setCoverage] = useState<any>(null)
  
  // Search state
  const [searchText, setSearchText] = useState('')
  const [searchColumn, setSearchColumn] = useState<string>('all')
  const [filteredRows, setFilteredRows] = useState<any[]>([])

  useEffect(() => {
    loadData()
  }, [ingestion, dataType, page])

  useEffect(() => {
    // Apply search filter
    if (!searchText.trim()) {
      setFilteredRows(rows)
    } else {
      const filtered = rows.filter((row) => {
        if (searchColumn === 'all') {
          // Search across all columns
          return Object.values(row).some((value) =>
            String(value || '').toLowerCase().includes(searchText.toLowerCase())
          )
        } else {
          // Search in specific column
          const value = row[searchColumn]
          return String(value || '').toLowerCase().includes(searchText.toLowerCase())
        }
      })
      setFilteredRows(filtered)
    }
  }, [searchText, searchColumn, rows])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      let data
      if (dataType === 'source') {
        data = await apiClient.viewSourceData(ingestion.id, limit, (page - 1) * limit)
      } else {
        data = await apiClient.viewCuratedData(ingestion.id, limit, (page - 1) * limit)
      }
      setRows(data.rows || [])
      setTotal(data.total_count || 0)
      setColumns(data.columns || [])
      if (dataType === 'curated' && data.coverage) {
        setCoverage(data.coverage)
      } else {
        setCoverage(null)
      }
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to load data')
      setRows([])
      setColumns([])
      setCoverage(null)
    } finally {
      setLoading(false)
    }
  }

  const handlePageChange = (_: React.ChangeEvent<unknown>, newPage: number) => {
    setPage(newPage)
  }

  const handleClearSearch = () => {
    setSearchText('')
    setSearchColumn('all')
  }

  const displayRows = searchText.trim() ? filteredRows : rows
  const displayTotal = searchText.trim() ? filteredRows.length : total

  return (
    <Box sx={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header with Search */}
      <Paper elevation={0} sx={{ p: 2, mb: 2, bgcolor: 'background.default' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 600, color: healthForesightColors.neutral.dark }}>
            {dataType === 'source' ? 'Source Data' : 'Curated Data'}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Refresh">
              <IconButton onClick={loadData} size="small" disabled={loading}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            {onClose && (
              <Tooltip title="Close">
                <IconButton onClick={onClose} size="small">
                  <CloseIcon />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        </Box>

        {/* Search Bar */}
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
          <TextField
            placeholder="Search in data..."
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            size="small"
            sx={{ flexGrow: 1, minWidth: 200 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              ),
              endAdornment: searchText && (
                <InputAdornment position="end">
                  <IconButton size="small" onClick={handleClearSearch}>
                    <ClearIcon fontSize="small" />
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Search Column</InputLabel>
            <Select
              value={searchColumn}
              onChange={(e) => setSearchColumn(e.target.value)}
              label="Search Column"
            >
              <MenuItem value="all">All Columns</MenuItem>
              {columns.map((col) => (
                <MenuItem key={col} value={col}>
                  {col}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          {searchText && (
            <Chip
              label={`${filteredRows.length} of ${rows.length} rows`}
              size="small"
              color="primary"
            />
          )}
        </Box>
      </Paper>

      {/* Coverage Metrics (for curated data) */}
      {coverage && dataType === 'curated' && (
        <Box sx={{ mb: 2 }}>
          <CoverageMetrics coverage={coverage} />
        </Box>
      )}

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Data Table */}
      <Paper sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', p: 4, flexGrow: 1 }}>
            <CircularProgress />
          </Box>
        ) : displayRows.length > 0 ? (
          <>
            <TableContainer sx={{ flexGrow: 1, overflow: 'auto' }}>
              <Table stickyHeader size="small" sx={{ minWidth: 650 }}>
                <TableHead>
                  <TableRow>
                    {columns.map((col) => (
                      <TableCell
                        key={col}
                        sx={{
                          fontWeight: 600,
                          bgcolor: healthForesightColors.neutral.light,
                          color: healthForesightColors.neutral.dark,
                          borderBottom: `2px solid ${healthForesightColors.primary.main}`,
                          position: 'sticky',
                          top: 0,
                          zIndex: 10,
                        }}
                      >
                        {col}
                      </TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {displayRows.map((row, idx) => (
                    <TableRow
                      key={idx}
                      hover
                      sx={{
                        '&:nth-of-type(even)': {
                          bgcolor: 'action.hover',
                        },
                        '&:hover': {
                          bgcolor: 'action.selected',
                        },
                      }}
                    >
                      {columns.map((col) => (
                        <TableCell
                          key={col}
                          sx={{
                            maxWidth: 200,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                            fontFamily: 'monospace',
                            fontSize: '0.875rem',
                          }}
                          title={String(row[col] ?? '')}
                        >
                          {row[col] !== null && row[col] !== undefined
                            ? String(row[col])
                            : '-'}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            {/* Pagination and Info */}
            <Box
              sx={{
                p: 2,
                borderTop: 1,
                borderColor: 'divider',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: 2,
              }}
            >
              <Typography variant="body2" color="text.secondary">
                Showing {searchText ? filteredRows.length : (page - 1) * limit + 1} to{' '}
                {Math.min(page * limit, displayTotal)} of {displayTotal} records
                {searchText && ` (filtered from ${total} total)`}
              </Typography>
              {!searchText && (
                <Pagination
                  count={Math.ceil(total / limit)}
                  page={page}
                  onChange={handlePageChange}
                  color="primary"
                  size="small"
                />
              )}
            </Box>
          </>
        ) : (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', p: 4, flexGrow: 1 }}>
            <Alert severity="info">No data available</Alert>
          </Box>
        )}
      </Paper>
    </Box>
  )
}
