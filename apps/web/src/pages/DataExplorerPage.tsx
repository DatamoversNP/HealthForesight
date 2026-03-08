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
  Breadcrumbs,
  Link,
  Chip,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Pagination,
  Tooltip,
  Tabs,
  Tab,
} from '@mui/material';
import FileDataViewer from '../components/FileDataViewer';
import {
  Folder as FolderIcon,
  InsertDriveFile as FileIcon,
  ArrowBack as ArrowBackIcon,
  Refresh as RefreshIcon,
  Visibility as ViewIcon,
  Close as CloseIcon,
  NavigateNext as NavigateNextIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Assessment as AssessmentIcon,
  PlayArrow as PlayArrowIcon,
} from '@mui/icons-material';
import {
  Grid,
  Card,
  CardContent,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
} from '@mui/material';
import { healthForesightColors } from '../theme/healthForesightTheme';
import { apiClient } from '../lib/api';

interface FileItem {
  name: string;
  type: 'file' | 'folder';
  path: string;
  size?: number;
  size_mb?: number;
  extension?: string;
}

interface FileListing {
  path: string;
  items: FileItem[];
  parent_path: string | null;
}

interface FileData {
  path: string;
  columns: string[];
  rows: any[];
  total_count: number;
  limit: number;
  offset: number;
  file_size: number;
  file_type: string;
}

export default function DataExplorerPage() {
  const [tabValue, setTabValue] = useState<number>(0);
  const [currentPath, setCurrentPath] = useState<string>('source_data');
  const [listing, setListing] = useState<FileListing | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [viewerOpen, setViewerOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<FileItem | null>(null);
  const [fileData, setFileData] = useState<FileData | null>(null);
  const [dataPage, setDataPage] = useState(1);
  const [dataLoading, setDataLoading] = useState(false);
  // Data Quality state
  const [qualityReport, setQualityReport] = useState<any>(null);
  const [qualitySummary, setQualitySummary] = useState<any>(null);
  const [qualityLoading, setQualityLoading] = useState(false);
  const [validating, setValidating] = useState(false);

  useEffect(() => {
    // Update path based on selected tab
    if (tabValue === 0) {
      setCurrentPath('source_data');
    } else if (tabValue === 1) {
      setCurrentPath('target_data_model');
    } else if (tabValue === 2) {
      // Data Quality tab - load quality data
      loadQualityData();
    }
  }, [tabValue]);

  useEffect(() => {
    loadDirectory();
  }, [currentPath]);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const loadDirectory = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.listDataFiles(currentPath);
      setListing(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load directory');
      console.error('Error loading directory:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleNavigate = (path: string) => {
    setCurrentPath(path);
  };

  const handleViewFile = async (file: FileItem) => {
    setSelectedFile(file);
    setViewerOpen(true);
    setDataPage(1);
    await loadFileData(file.path, 1);
  };

  const loadFileData = async (path: string, page: number) => {
    try {
      setDataLoading(true);
      const limit = 100;
      const offset = (page - 1) * limit;
      const data = await apiClient.viewDataFile(path, limit, offset);
      setFileData(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load file data');
      console.error('Error loading file data:', err);
    } finally {
      setDataLoading(false);
    }
  };

  const handleDataPageChange = async (_: React.ChangeEvent<unknown>, page: number) => {
    setDataPage(page);
    if (selectedFile) {
      await loadFileData(selectedFile.path, page);
    }
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '-';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const getFileIcon = (item: FileItem) => {
    if (item.type === 'folder') {
      return <FolderIcon sx={{ color: '#FFA726' }} />;
    }
    return <FileIcon sx={{ color: '#42A5F5' }} />;
  };

  const loadQualityData = async () => {
    try {
      setQualityLoading(true);
      setError(null);
      
      // Try to get existing report
      try {
        const report = await apiClient.getDataQualityReport();
        setQualityReport(report);
      } catch (e) {
        // Report doesn't exist yet, that's okay
        console.log('No existing quality report found');
      }
      
      // Always load summary
      const summary = await apiClient.getDataQualitySummary();
      setQualitySummary(summary);
    } catch (err: any) {
      setError(err.message || 'Failed to load data quality information');
      console.error('Error loading quality data:', err);
    } finally {
      setQualityLoading(false);
    }
  };

  const handleRunValidation = async () => {
    try {
      setValidating(true);
      setError(null);
      const result = await apiClient.runDataQualityValidation();
      // Reload quality data after validation
      await loadQualityData();
      setValidating(false);
    } catch (err: any) {
      setError(err.message || 'Failed to run data quality validation');
      console.error('Error running validation:', err);
      setValidating(false);
    }
  };

  const getQualityScoreColor = (score: number) => {
    if (score >= 90) return 'success';
    if (score >= 80) return 'info';
    if (score >= 60) return 'warning';
    return 'error';
  };

  const getSeverityColor = (severity: string) => {
    if (severity === 'HIGH') return 'error';
    if (severity === 'MEDIUM') return 'warning';
    return 'info';
  };

  const pathParts = currentPath.split('/').filter(Boolean);
  const breadcrumbPaths: string[] = [];
  pathParts.forEach((part, idx) => {
    breadcrumbPaths.push(pathParts.slice(0, idx + 1).join('/'));
  });

  return (
    <Box sx={{ maxWidth: 1600, mx: 'auto', p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, color: healthForesightColors.neutral.dark }}>
          Data Explorer
        </Typography>
        <Tooltip title="Refresh">
          <IconButton onClick={loadDirectory} disabled={loading}>
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Tabs for Source Data and Target Data Model */}
      <Paper sx={{ mb: 2 }}>
        <Tabs 
          value={tabValue} 
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="Source Data Viewer" />
          <Tab label="Target Data Model Viewer" />
          <Tab 
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <AssessmentIcon fontSize="small" />
                Data Quality
              </Box>
            } 
          />
        </Tabs>
      </Paper>

      {/* Breadcrumbs */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} aria-label="breadcrumb">
          <Link
            component="button"
            variant="body1"
            onClick={() => handleNavigate('')}
            sx={{ cursor: 'pointer', textDecoration: 'none' }}
          >
            data
          </Link>
          {pathParts.map((part, idx) => {
            const path = breadcrumbPaths[idx];
            const isLast = idx === pathParts.length - 1;
            return isLast ? (
              <Typography key={path} color="text.primary">
                {part}
              </Typography>
            ) : (
              <Link
                key={path}
                component="button"
                variant="body1"
                onClick={() => handleNavigate(path)}
                sx={{ cursor: 'pointer', textDecoration: 'none' }}
              >
                {part}
              </Link>
            );
          })}
        </Breadcrumbs>
      </Paper>

      {/* Data Quality Tab Content */}
      {tabValue === 2 && (
        <Box>
          <Paper sx={{ p: 3, mb: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Data Quality Report</Typography>
              <Button
                variant="contained"
                startIcon={validating ? <CircularProgress size={16} /> : <PlayArrowIcon />}
                onClick={handleRunValidation}
                disabled={validating}
              >
                {validating ? 'Validating...' : 'Run Validation'}
              </Button>
            </Box>

            {qualityLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                <CircularProgress />
              </Box>
            ) : qualityReport || qualitySummary ? (
              <Grid container spacing={2}>
                {/* Overall Score */}
                {qualityReport && (
                  <Grid item xs={12}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>Overall Quality Score</Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 2 }}>
                          <Chip
                            label={`${qualityReport.overall_score?.toFixed(1) || 0}%`}
                            color={getQualityScoreColor(qualityReport.overall_score || 0)}
                            sx={{ fontSize: '1.2rem', height: 40, px: 2 }}
                          />
                          <LinearProgress
                            variant="determinate"
                            value={qualityReport.overall_score || 0}
                            sx={{ flexGrow: 1, height: 10, borderRadius: 5 }}
                            color={getQualityScoreColor(qualityReport.overall_score || 0)}
                          />
                        </Box>
                        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                          Report generated: {qualityReport.timestamp ? new Date(qualityReport.timestamp).toLocaleString() : 'N/A'}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                )}

                {/* Dataset Quality Scores */}
                {qualityReport?.datasets && Object.keys(qualityReport.datasets).length > 0 && (
                  <Grid item xs={12}>
                    <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>Dataset Quality Scores</Typography>
                    <Grid container spacing={2}>
                      {Object.entries(qualityReport.datasets).map(([datasetName, dataset]: [string, any]) => (
                        <Grid item xs={12} md={4} key={datasetName}>
                          <Card>
                            <CardContent>
                              <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                                {datasetName}
                              </Typography>
                              <Box sx={{ mt: 2 }}>
                                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                  <Typography variant="body2">Quality Score</Typography>
                                  <Chip
                                    label={`${dataset.quality_score?.toFixed(1) || 0}%`}
                                    color={getQualityScoreColor(dataset.quality_score || 0)}
                                    size="small"
                                  />
                                </Box>
                                <LinearProgress
                                  variant="determinate"
                                  value={dataset.quality_score || 0}
                                  sx={{ mb: 2, height: 8 }}
                                  color={getQualityScoreColor(dataset.quality_score || 0)}
                                />
                                <Typography variant="caption" color="text.secondary">
                                  Completeness: {dataset.completeness?.completeness_score?.toFixed(1) || 0}%<br />
                                  Uniqueness: {dataset.uniqueness?.uniqueness_score?.toFixed(1) || 0}%<br />
                                  Validity: {dataset.validity?.validity_score?.toFixed(1) || 0}%
                                </Typography>
                              </Box>
                            </CardContent>
                          </Card>
                        </Grid>
                      ))}
                    </Grid>
                  </Grid>
                )}

                {/* Issues List */}
                {qualityReport?.issues && qualityReport.issues.length > 0 && (
                  <Grid item xs={12}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Issues Found ({qualityReport.issues.length})
                        </Typography>
                        <List>
                          {qualityReport.issues.slice(0, 20).map((issue: any, idx: number) => (
                            <ListItem key={idx}>
                              <ListItemIcon>
                                {issue.severity === 'HIGH' ? (
                                  <ErrorIcon color="error" />
                                ) : issue.severity === 'MEDIUM' ? (
                                  <WarningIcon color="warning" />
                                ) : (
                                  <CheckCircleIcon color="info" />
                                )}
                              </ListItemIcon>
                              <ListItemText
                                primary={
                                  <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                                    <Chip
                                      label={issue.severity}
                                      color={getSeverityColor(issue.severity)}
                                      size="small"
                                    />
                                    <Typography variant="body2" fontWeight="bold">
                                      {issue.type}
                                    </Typography>
                                    {issue.dataset && (
                                      <Chip label={issue.dataset} size="small" variant="outlined" />
                                    )}
                                  </Box>
                                }
                                secondary={issue.description || issue.issue_description}
                              />
                            </ListItem>
                          ))}
                        </List>
                        {qualityReport.issues.length > 20 && (
                          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                            Showing first 20 of {qualityReport.issues.length} issues
                          </Typography>
                        )}
                      </CardContent>
                    </Card>
                  </Grid>
                )}

                {/* Summary Stats */}
                {qualitySummary && (
                  <Grid item xs={12}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>Dataset Summary</Typography>
                        <Grid container spacing={2} sx={{ mt: 1 }}>
                          {Object.entries(qualitySummary.datasets || {}).map(([datasetName, dataset]: [string, any]) => (
                            <Grid item xs={12} sm={6} md={4} key={datasetName}>
                              <Paper sx={{ p: 2 }}>
                                <Typography variant="subtitle2" fontWeight="bold">{datasetName}</Typography>
                                <Typography variant="body2" color="text.secondary">
                                  {dataset.exists ? `Size: ${dataset.size_mb?.toFixed(2) || 0} MB` : 'Not found'}
                                </Typography>
                              </Paper>
                            </Grid>
                          ))}
                        </Grid>
                      </CardContent>
                    </Card>
                  </Grid>
                )}
              </Grid>
            ) : (
              <Alert severity="info">
                No data quality report found. Click "Run Validation" to generate one.
              </Alert>
            )}
          </Paper>
        </Box>
      )}

      {/* File/Folder Listing */}
      {tabValue !== 2 && (
      <Paper>
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            {listing?.parent_path !== null && (
              <IconButton onClick={() => handleNavigate(listing?.parent_path || '')} size="small">
                <ArrowBackIcon />
              </IconButton>
            )}
            <Typography variant="h6">Path: {currentPath || 'data/'}</Typography>
          </Box>
        </Box>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : listing && listing.items.length > 0 ? (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell align="right">Size</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {listing.items.map((item) => (
                  <TableRow key={item.path} hover>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {getFileIcon(item)}
                        <Typography variant="body2">{item.name}</Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={item.type === 'folder' ? 'Folder' : item.extension?.toUpperCase() || 'File'}
                        size="small"
                        color={item.type === 'folder' ? 'default' : 'primary'}
                      />
                    </TableCell>
                    <TableCell align="right">
                      {item.type === 'file' ? formatFileSize(item.size) : '-'}
                    </TableCell>
                    <TableCell align="center">
                      {item.type === 'folder' ? (
                        <IconButton
                          size="small"
                          onClick={() => handleNavigate(item.path)}
                          title="Open folder"
                        >
                          <NavigateNextIcon />
                        </IconButton>
                      ) : (
                        <IconButton
                          size="small"
                          onClick={() => handleViewFile(item)}
                          title="View file"
                          color="primary"
                        >
                          <ViewIcon />
                        </IconButton>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        ) : (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              No files or folders found
            </Typography>
          </Box>
        )}
      </Paper>
      )}

      {/* File Viewer Dialog */}
      <Dialog
        open={viewerOpen}
        onClose={() => setViewerOpen(false)}
        maxWidth="xl"
        fullWidth
        PaperProps={{
          sx: { height: '90vh', display: 'flex', flexDirection: 'column' },
        }}
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              {selectedFile?.name} ({formatFileSize(selectedFile?.size)})
            </Typography>
            <IconButton onClick={() => setViewerOpen(false)} size="small">
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent dividers sx={{ flexGrow: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column', p: 0 }}>
          <FileDataViewer
            fileData={fileData}
            loading={dataLoading}
            page={dataPage}
            onPageChange={handleDataPageChange}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewerOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

