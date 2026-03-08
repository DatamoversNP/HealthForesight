import { useState, useEffect } from 'react'
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  CircularProgress,
  Alert,
  Pagination,
  Typography,
  TextField,
  InputAdornment,
  IconButton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Tooltip,
} from '@mui/material'
import {
  Search as SearchIcon,
  Clear as ClearIcon,
} from '@mui/icons-material'
import { healthForesightColors } from '../theme/healthForesightTheme'

interface FileDataViewerProps {
  fileData: any
  loading: boolean
  page: number
  onPageChange: (event: React.ChangeEvent<unknown>, page: number) => void
}

export default function FileDataViewer({ fileData, loading, page, onPageChange }: FileDataViewerProps) {
  const [searchText, setSearchText] = useState('')
  const [searchColumn, setSearchColumn] = useState<string>('all')
  const [filteredRows, setFilteredRows] = useState<any[]>([])

  useEffect(() => {
    // Apply search filter
    if (!searchText.trim() || !fileData?.rows) {
      setFilteredRows(fileData?.rows || [])
    } else {
      const filtered = (fileData.rows || []).filter((row: any) => {
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
  }, [searchText, searchColumn, fileData])

  const handleClearSearch = () => {
    setSearchText('')
    setSearchColumn('all')
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', p: 4, flexGrow: 1 }}>
        <CircularProgress />
      </Box>
    )
  }

  if (!fileData || !fileData.rows || fileData.rows.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', p: 4, flexGrow: 1 }}>
        <Alert severity="info">No data available</Alert>
      </Box>
    )
  }

  const displayRows = searchText.trim() ? filteredRows : fileData.rows
  const displayTotal = searchText.trim() ? filteredRows.length : fileData.total_count

  return (
    <Box sx={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', p: 2 }}>
      {/* Search Bar */}
      <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 2, flexWrap: 'wrap' }}>
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
            {(fileData.columns || []).map((col: string) => (
              <MenuItem key={col} value={col}>
                {col}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        {searchText && (
          <Chip
            label={`${filteredRows.length} of ${fileData.rows.length} rows`}
            size="small"
            color="primary"
          />
        )}
      </Box>

      {/* Data Table */}
      <Paper sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <TableContainer sx={{ flexGrow: 1, overflow: 'auto' }}>
          <Table stickyHeader size="small" sx={{ minWidth: 650 }}>
            <TableHead>
              <TableRow>
                {(fileData.columns || []).map((col: string) => (
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
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {col}
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {displayRows.map((row: any, idx: number) => (
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
                  {(fileData.columns || []).map((col: string) => (
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
            Showing {searchText ? (displayRows.length > 0 ? 1 : 0) : fileData.offset + 1} to{' '}
            {Math.min(searchText ? displayRows.length : fileData.offset + fileData.limit, displayTotal)} of{' '}
            {displayTotal} records
            {searchText && ` (filtered from ${fileData.total_count} total)`}
          </Typography>
          {!searchText && (
            <Pagination
              count={Math.ceil(fileData.total_count / fileData.limit)}
              page={page}
              onChange={onPageChange}
              color="primary"
              size="small"
            />
          )}
        </Box>
      </Paper>
    </Box>
  )
}

