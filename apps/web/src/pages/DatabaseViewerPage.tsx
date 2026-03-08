import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  CircularProgress,
  Alert,
  Pagination,
  Tooltip,
  Chip,
  TextField,
  InputAdornment,
  Divider,
  Grid,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Button,
} from '@mui/material';
import {
  Storage as StorageIcon,
  TableChart as TableChartIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
  FirstPage as FirstPageIcon,
  LastPage as LastPageIcon,
  NavigateBefore as NavigateBeforeIcon,
  NavigateNext as NavigateNextIcon,
  Info as InfoIcon,
  Key as KeyIcon,
  Link as LinkIcon,
  ViewColumn as ViewColumnIcon,
} from '@mui/icons-material';
import { healthForesightColors } from '../theme/healthForesightTheme';
import { apiClient } from '../lib/api';

interface TableInfo {
  name: string;
  row_count: number | null;
}

interface ColumnInfo {
  name: string;
  type: string;
  nullable: boolean;
  default: string | null;
  primary_key: boolean;
}

interface TableSchema {
  table_name: string;
  columns: ColumnInfo[];
  primary_keys: string[];
  foreign_keys: Array<{
    column: string;
    referenced_table: string;
    referenced_column: string;
  }>;
  indexes: Array<{
    name: string;
    columns: string[];
    unique: boolean;
  }>;
}

interface TableData {
  table_name: string;
  data: Record<string, any>[];
  total_count: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export default function DatabaseViewerPage() {
  const [tables, setTables] = useState<TableInfo[]>([]);
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [schema, setSchema] = useState<TableSchema | null>(null);
  const [data, setData] = useState<TableData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(1);
  const [rowsPerPage] = useState(50);

  useEffect(() => {
    loadTables();
  }, []);

  useEffect(() => {
    if (selectedTable) {
      loadSchema(selectedTable);
      loadData(selectedTable, 1);
    }
  }, [selectedTable]);

  useEffect(() => {
    if (selectedTable) {
      loadData(selectedTable, page);
    }
  }, [page, selectedTable]);

  const loadTables = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get('/database/tables');
      setTables(response);
    } catch (err: any) {
      setError(err.message || 'Failed to load tables');
    } finally {
      setLoading(false);
    }
  };

  const loadSchema = async (tableName: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get(`/database/tables/${tableName}/schema`);
      setSchema(response);
    } catch (err: any) {
      setError(err.message || 'Failed to load table schema');
    } finally {
      setLoading(false);
    }
  };

  const loadData = async (tableName: string, pageNum: number) => {
    setLoading(true);
    setError(null);
    try {
      const offset = (pageNum - 1) * rowsPerPage;
      const response = await apiClient.get(`/database/tables/${tableName}/data`, {
        params: {
          limit: rowsPerPage,
          offset: offset,
        },
      });
      setData(response);
    } catch (err: any) {
      setError(err.message || 'Failed to load table data');
    } finally {
      setLoading(false);
    }
  };

  const handleTableSelect = (tableName: string) => {
    setSelectedTable(tableName);
    setPage(1);
  };

  const filteredTables = tables.filter((table) =>
    table.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handlePageChange = (_event: React.ChangeEvent<unknown>, value: number) => {
    setPage(value);
  };

  const totalPages = data ? Math.ceil(data.total_count / rowsPerPage) : 0;

  return (
    <Box sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <StorageIcon sx={{ fontSize: 32, color: healthForesightColors.primary }} />
          <Typography variant="h4" component="h1">
            Database Viewer
          </Typography>
        </Box>
        <Tooltip title="Refresh tables">
          <IconButton onClick={loadTables} disabled={loading}>
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Grid container spacing={2} sx={{ flex: 1, minHeight: 0 }}>
        {/* Tables List */}
        <Grid item xs={12} md={3}>
          <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Tables
              </Typography>
              <TextField
                fullWidth
                size="small"
                placeholder="Search tables..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
                sx={{ mb: 2 }}
              />
              {loading && !tables.length ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                  <CircularProgress />
                </Box>
              ) : (
                <List sx={{ maxHeight: 'calc(100vh - 300px)', overflow: 'auto' }}>
                  {filteredTables.map((table) => (
                    <ListItem
                      key={table.name}
                      button
                      selected={selectedTable === table.name}
                      onClick={() => handleTableSelect(table.name)}
                      sx={{
                        borderRadius: 1,
                        mb: 0.5,
                        '&.Mui-selected': {
                          backgroundColor: healthForesightColors.primary + '20',
                          '&:hover': {
                            backgroundColor: healthForesightColors.primary + '30',
                          },
                        },
                      }}
                    >
                      <ListItemIcon>
                        <TableChartIcon />
                      </ListItemIcon>
                      <ListItemText
                        primary={table.name}
                        secondary={
                          table.row_count !== null
                            ? `${table.row_count.toLocaleString()} rows`
                            : 'Unknown'
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Schema and Data View */}
        <Grid item xs={12} md={9}>
          {selectedTable ? (
            <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 2 }}>
              {/* Schema Card */}
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                    <Typography variant="h6">
                      Schema: {selectedTable}
                    </Typography>
                    <Chip
                      label={`${data?.total_count.toLocaleString() || 0} rows`}
                      size="small"
                      color="primary"
                    />
                  </Box>
                  {schema ? (
                    <Box>
                      <Typography variant="subtitle2" gutterBottom sx={{ mt: 2, fontWeight: 'bold' }}>
                        Columns
                      </Typography>
                      <TableContainer>
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              <TableCell>Name</TableCell>
                              <TableCell>Type</TableCell>
                              <TableCell>Nullable</TableCell>
                              <TableCell>Default</TableCell>
                              <TableCell>Primary Key</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {schema.columns.map((col) => (
                              <TableRow key={col.name}>
                                <TableCell>
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                    {col.primary_key && (
                                      <KeyIcon sx={{ fontSize: 16, color: healthForesightColors.primary }} />
                                    )}
                                    <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                                      {col.name}
                                    </Typography>
                                  </Box>
                                </TableCell>
                                <TableCell>
                                  <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                                    {col.type}
                                  </Typography>
                                </TableCell>
                                <TableCell>
                                  <Chip
                                    label={col.nullable ? 'Yes' : 'No'}
                                    size="small"
                                    color={col.nullable ? 'default' : 'warning'}
                                  />
                                </TableCell>
                                <TableCell>
                                  <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                                    {col.default || '-'}
                                  </Typography>
                                </TableCell>
                                <TableCell>
                                  {col.primary_key && (
                                    <Chip label="PK" size="small" color="primary" />
                                  )}
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>

                      {schema.foreign_keys.length > 0 && (
                        <>
                          <Typography variant="subtitle2" gutterBottom sx={{ mt: 3, fontWeight: 'bold' }}>
                            Foreign Keys
                          </Typography>
                          <List dense>
                            {schema.foreign_keys.map((fk, idx) => (
                              <ListItem key={idx}>
                                <ListItemIcon>
                                  <LinkIcon sx={{ fontSize: 16 }} />
                                </ListItemIcon>
                                <ListItemText
                                  primary={
                                    <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                                      {fk.column} → {fk.referenced_table}.{fk.referenced_column}
                                    </Typography>
                                  }
                                />
                              </ListItem>
                            ))}
                          </List>
                        </>
                      )}
                    </Box>
                  ) : (
                    <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                      <CircularProgress />
                    </Box>
                  )}
                </CardContent>
              </Card>

              {/* Data Card */}
              <Card sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
                <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
                  <Typography variant="h6" gutterBottom>
                    Data
                  </Typography>
                  {data ? (
                    <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
                      <TableContainer sx={{ flex: 1, overflow: 'auto' }}>
                        <Table stickyHeader size="small">
                          <TableHead>
                            <TableRow>
                              {data.data.length > 0 &&
                                Object.keys(data.data[0]).map((col) => (
                                  <TableCell key={col} sx={{ fontFamily: 'monospace', fontWeight: 'bold' }}>
                                    {col}
                                  </TableCell>
                                ))}
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {data.data.map((row, idx) => (
                              <TableRow key={idx} hover>
                                {Object.values(row).map((value: any, colIdx) => (
                                  <TableCell key={colIdx} sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                                    {value === null || value === undefined
                                      ? <Typography variant="body2" color="text.secondary">NULL</Typography>
                                      : typeof value === 'object'
                                      ? JSON.stringify(value)
                                      : String(value)}
                                  </TableCell>
                                ))}
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
                        <Typography variant="body2" color="text.secondary">
                          Showing {data.offset + 1} - {Math.min(data.offset + data.limit, data.total_count)} of{' '}
                          {data.total_count.toLocaleString()} rows
                        </Typography>
                        <Pagination
                          count={totalPages}
                          page={page}
                          onChange={handlePageChange}
                          color="primary"
                          size="small"
                          showFirstButton
                          showLastButton
                        />
                      </Box>
                    </Box>
                  ) : (
                    <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                      <CircularProgress />
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Box>
          ) : (
            <Card>
              <CardContent>
                <Box sx={{ textAlign: 'center', py: 8 }}>
                  <TableChartIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary">
                    Select a table to view its schema and data
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
    </Box>
  );
}
