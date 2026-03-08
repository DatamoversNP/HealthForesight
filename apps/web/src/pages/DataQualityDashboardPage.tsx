import React, { useEffect, useState } from 'react';
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
  Chip,
  CircularProgress,
  Alert,
  Grid,
  Card,
  CardContent,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
  Tooltip,
  Button,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Assessment as AssessmentIcon,
  TrendingUp as TrendingUpIcon,
  PlayArrow as PlayArrowIcon,
} from '@mui/icons-material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
  LineChart,
  Line,
} from 'recharts';
import { healthForesightColors } from '../theme/healthForesightTheme';
import { useTheme } from '@mui/material/styles';
import { apiClient } from '../lib/api';

interface QualityReport {
  pipeline_id: string;
  run_id: string;
  quality_score: number;
  completeness_score: number;
  validity_score: number;
  uniqueness_score: number;
  issues: QualityIssue[];
  generated_at: string;
}

interface QualityIssue {
  severity: string;
  type?: string;
  issue_type?: string;
  description?: string;
  issue_description?: string;
  field?: string;
  field_name?: string;
  dataset?: string;
  affected_rows?: number;
  affected_percentage?: number;
  affected_row_indices?: number[];
  sample_values?: any[];
}

interface DatasetQuality {
  dataset_type: string;
  total_runs: number;
  avg_quality_score: number;
  avg_completeness: number;
  avg_validity: number;
  avg_uniqueness: number;
  total_issues: number;
  critical_issues: number;
  high_issues: number;
  medium_issues: number;
  low_issues: number;
  latest_report?: QualityReport;
}

export default function DataQualityDashboardPage() {
  const theme = useTheme();
  const [datasets, setDatasets] = useState<DatasetQuality[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [expandedDataset, setExpandedDataset] = useState<string | null>(null);
  const [runningValidation, setRunningValidation] = useState(false);
  const [validationStatus, setValidationStatus] = useState<string | null>(null);

  useEffect(() => {
    loadData();
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      setRefreshing(true);
      setError(null);

      // Load data quality report from API
      const report = await apiClient.getDataQualityReport();
      
      console.log('[DataQuality] Received report:', {
        overall_score: report.overall_score,
        datasets_count: Object.keys(report.datasets || {}).length,
        issues_count: (report.issues || []).length,
        datasets_keys: Object.keys(report.datasets || {}),
      });
      
      // Transform API response to frontend format
      const datasetsMap = report.datasets || {};
      const issues = report.issues || [];
      
      // Handle case where datasets might be empty or null
      if (!datasetsMap || Object.keys(datasetsMap).length === 0) {
        console.warn('[DataQuality] No datasets found in report');
        setDatasets([]);
        setError('No dataset quality data found in report. Please run validation first.');
        return;
      }
      
      // Group issues by dataset
      const issuesByDataset = new Map<string, QualityIssue[]>();
      for (const issue of issues) {
        const dataset = issue.dataset || 'UNKNOWN';
        if (!issuesByDataset.has(dataset)) {
          issuesByDataset.set(dataset, []);
        }
        issuesByDataset.get(dataset)!.push(issue);
      }
      
      // Transform datasets to frontend format
      const datasetQualities: DatasetQuality[] = Object.entries(datasetsMap).map(([datasetType, datasetData]: [string, any]) => {
        const datasetIssues = issuesByDataset.get(datasetType) || [];
        const issuesBySeverity = {
          CRITICAL: datasetIssues.filter((i: QualityIssue) => (i.severity || '').toUpperCase() === 'CRITICAL').length,
          HIGH: datasetIssues.filter((i: QualityIssue) => (i.severity || '').toUpperCase() === 'HIGH').length,
          MEDIUM: datasetIssues.filter((i: QualityIssue) => (i.severity || '').toUpperCase() === 'MEDIUM').length,
          LOW: datasetIssues.filter((i: QualityIssue) => (i.severity || '').toUpperCase() === 'LOW').length,
        };
        
        // Handle both percentage (0-100) and decimal (0-1) formats
        const qualityScoreRaw = datasetData.quality_score || 0;
        const qualityScore = qualityScoreRaw > 1 ? qualityScoreRaw / 100 : qualityScoreRaw;
        
        const completenessRaw = datasetData.completeness?.completeness_score || 0;
        const completeness = completenessRaw > 1 ? completenessRaw / 100 : completenessRaw;
        
        const validityRaw = datasetData.validity?.validity_score || 0;
        const validity = validityRaw > 1 ? validityRaw / 100 : validityRaw;
        
        const uniquenessRaw = datasetData.uniqueness?.uniqueness_score || 0;
        const uniqueness = uniquenessRaw > 1 ? uniquenessRaw / 100 : uniquenessRaw;
        
        return {
          dataset_type: datasetType,
          total_runs: 0, // Not applicable for database reports
          avg_quality_score: qualityScore,
          avg_completeness: completeness,
          avg_validity: validity,
          avg_uniqueness: uniqueness,
          total_issues: datasetIssues.length,
          critical_issues: issuesBySeverity.CRITICAL,
          high_issues: issuesBySeverity.HIGH,
          medium_issues: issuesBySeverity.MEDIUM,
          low_issues: issuesBySeverity.LOW,
          latest_report: {
            pipeline_id: '',
            run_id: '',
            quality_score: qualityScore,
            completeness_score: completeness,
            validity_score: validity,
            uniqueness_score: uniqueness,
            issues: datasetIssues,
            generated_at: report.timestamp || new Date().toISOString(),
          },
        };
      });

      setDatasets(datasetQualities.sort((a, b) => b.avg_quality_score - a.avg_quality_score));

    } catch (err: any) {
      // If report doesn't exist, show empty state
      if (err.response?.status === 404) {
        setDatasets([]);
        setError('No data quality report found. Please run validation first.');
      } else {
        setError(err.message || 'Failed to load data quality metrics');
        console.error('Error loading data quality dashboard:', err);
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.9) return 'success';
    if (score >= 0.7) return 'warning';
    return 'error';
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return 'error';
      case 'HIGH':
        return 'error';
      case 'MEDIUM':
        return 'warning';
      case 'LOW':
        return 'info';
      default:
        return 'default';
    }
  };

  const handleRunValidation = async () => {
    try {
      setRunningValidation(true);
      setError(null);
      setValidationStatus('Running data quality validation...');

      const result = await apiClient.runDataQualityValidation();
      
      setValidationStatus('Validation completed successfully! Refreshing data...');
      
      // Wait a moment then reload
      setTimeout(() => {
        loadData();
        setValidationStatus(null);
      }, 2000);
    } catch (err: any) {
      setError(err.message || 'Failed to run data quality validation');
      setValidationStatus(null);
      console.error('Error running validation:', err);
    } finally {
      setRunningValidation(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <CircularProgress />
      </Box>
    );
  }

  // Calculate overall metrics from datasets with data
  const datasetsWithData = datasets.filter(d => d.avg_quality_score > 0);
  const overallQuality = datasetsWithData.length > 0
    ? datasetsWithData.reduce((sum, d) => sum + d.avg_quality_score, 0) / datasetsWithData.length
    : 0;
  const totalIssues = datasets.reduce((sum, d) => sum + d.total_issues, 0);
  const totalCriticalIssues = datasets.reduce((sum, d) => sum + d.critical_issues, 0);
  const avgCompleteness = datasetsWithData.length > 0
    ? datasetsWithData.reduce((sum, d) => sum + d.avg_completeness, 0) / datasetsWithData.length
    : 0;

  return (
    <Box sx={{ maxWidth: 1600, mx: 'auto', p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, color: healthForesightColors.neutral.dark }}>
          Data Quality Dashboard
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="contained"
            startIcon={<PlayArrowIcon />}
            onClick={handleRunValidation}
            disabled={runningValidation}
            sx={{ minWidth: 150 }}
          >
            {runningValidation ? 'Running...' : 'Run Validation'}
          </Button>
          <Tooltip title="Refresh">
            <IconButton onClick={loadData} disabled={refreshing} sx={{ color: healthForesightColors.primary.main }}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {validationStatus && (
        <Alert severity="info" sx={{ mb: 3 }} onClose={() => setValidationStatus(null)}>
          {validationStatus}
        </Alert>
      )}

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <AssessmentIcon sx={{ color: healthForesightColors.primary.main, mr: 1 }} />
                <Typography variant="h6">Overall Quality</Typography>
              </Box>
              <Typography variant="h4">
                {(overallQuality * 100).toFixed(1)}%
              </Typography>
              <LinearProgress
                variant="determinate"
                value={overallQuality * 100}
                color={getScoreColor(overallQuality) as any}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <ErrorIcon sx={{ color: theme.palette.error.main, mr: 1 }} />
                <Typography variant="h6">Total Issues</Typography>
              </Box>
              <Typography variant="h4">{totalIssues}</Typography>
              <Typography variant="body2" color="text.secondary">
                {totalCriticalIssues} critical
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <TrendingUpIcon sx={{ color: theme.palette.success.main, mr: 1 }} />
                <Typography variant="h6">Datasets Monitored</Typography>
              </Box>
              <Typography variant="h4">{datasets.length}</Typography>
              <Typography variant="body2" color="text.secondary">
                Active datasets
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <CheckCircleIcon sx={{ color: theme.palette.success.main, mr: 1 }} />
                <Typography variant="h6">Avg Completeness</Typography>
              </Box>
              <Typography variant="h4">
                {(avgCompleteness * 100).toFixed(1)}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Across all datasets
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Visualizations Section */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* Quality Scores Heatmap */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quality Scores by Dataset
              </Typography>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart 
                  data={datasets.map(d => ({
                    name: d.dataset_type.length > 15 ? d.dataset_type.substring(0, 15) + '...' : d.dataset_type,
                    fullName: d.dataset_type,
                    Quality: Number((d.avg_quality_score * 100).toFixed(1)),
                    Completeness: Number((d.avg_completeness * 100).toFixed(1)),
                    Validity: Number((d.avg_validity * 100).toFixed(1)),
                    Uniqueness: Number((d.avg_uniqueness * 100).toFixed(1)),
                  }))}
                  margin={{ top: 20, right: 30, left: 20, bottom: 100 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                  <XAxis 
                    dataKey="name" 
                    angle={-45} 
                    textAnchor="end" 
                    height={120}
                    interval={0}
                    tick={{ fontSize: 11 }}
                  />
                  <YAxis 
                    domain={[0, 100]} 
                    tick={{ fontSize: 12 }}
                    label={{ value: 'Score (%)', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle' } }}
                  />
                  <RechartsTooltip 
                    formatter={(value: any, name: string) => [`${value}%`, name]}
                    labelFormatter={(label, payload) => payload?.[0]?.payload?.fullName || label}
                    contentStyle={{ backgroundColor: '#fff', border: '1px solid #ccc', borderRadius: '4px' }}
                  />
                  <Legend 
                    wrapperStyle={{ paddingTop: '20px' }}
                    iconType="rect"
                  />
                  <Bar dataKey="Quality" fill="#3B2F8F" radius={[4, 4, 0, 0]} maxBarSize={60}>
                    {datasets.map((d, idx) => (
                      <Cell key={`quality-${idx}`} fill={
                        d.avg_quality_score >= 0.9 ? '#4caf50' :
                        d.avg_quality_score >= 0.8 ? '#8bc34a' :
                        d.avg_quality_score >= 0.7 ? '#ff9800' : '#f44336'
                      } />
                    ))}
                  </Bar>
                  <Bar dataKey="Completeness" fill="#2196f3" radius={[4, 4, 0, 0]} maxBarSize={60} />
                  <Bar dataKey="Validity" fill="#00bcd4" radius={[4, 4, 0, 0]} maxBarSize={60} />
                  <Bar dataKey="Uniqueness" fill="#9c27b0" radius={[4, 4, 0, 0]} maxBarSize={60} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Issues Distribution */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Issues by Severity
              </Typography>
              <ResponsiveContainer width="100%" height={400}>
                {(() => {
                  const issueData = [
                    { name: 'Critical', value: datasets.reduce((sum, d) => sum + d.critical_issues, 0), fill: '#d32f2f' },
                    { name: 'High', value: datasets.reduce((sum, d) => sum + d.high_issues, 0), fill: '#f57c00' },
                    { name: 'Medium', value: datasets.reduce((sum, d) => sum + d.medium_issues, 0), fill: '#fbc02d' },
                    { name: 'Low', value: datasets.reduce((sum, d) => sum + d.low_issues, 0), fill: '#689f38' },
                  ].filter(item => item.value > 0);

                  if (issueData.length === 0) {
                    return (
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                        <Typography variant="body2" color="text.secondary">
                          No issues found - All datasets are clean!
                        </Typography>
                      </Box>
                    );
                  }

                  return (
                    <PieChart>
                      <Pie
                        data={issueData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, value, percent }) => `${name}: ${value} (${(percent * 100).toFixed(0)}%)`}
                        outerRadius={120}
                        innerRadius={40}
                        fill="#8884d8"
                        dataKey="value"
                        paddingAngle={2}
                      >
                        {issueData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Pie>
                      <RechartsTooltip 
                        formatter={(value: any, name: string, props: any) => {
                          const total = issueData.reduce((sum, d) => sum + d.value, 0);
                          const percent = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                          return [`${value} (${percent}%)`, name];
                        }}
                        contentStyle={{ backgroundColor: '#fff', border: '1px solid #ccc', borderRadius: '4px' }}
                      />
                      <Legend 
                        verticalAlign="bottom"
                        height={36}
                        iconType="circle"
                      />
                    </PieChart>
                  );
                })()}
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Quality Heatmap Matrix */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quality Metrics Heatmap
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Dataset</TableCell>
                      <TableCell align="right">Quality Score</TableCell>
                      <TableCell align="right">Completeness</TableCell>
                      <TableCell align="right">Validity</TableCell>
                      <TableCell align="right">Uniqueness</TableCell>
                      <TableCell align="right">Total Issues</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {datasets.map((dataset) => {
                      const getHeatmapColor = (value: number) => {
                        if (value >= 0.9) return '#4caf50';
                        if (value >= 0.8) return '#8bc34a';
                        if (value >= 0.7) return '#cddc39';
                        if (value >= 0.6) return '#ffeb3b';
                        if (value >= 0.5) return '#ffc107';
                        return '#ff9800';
                      };
                      
                      return (
                        <TableRow key={dataset.dataset_type}>
                          <TableCell sx={{ fontWeight: 600 }}>{dataset.dataset_type}</TableCell>
                          <TableCell align="right">
                            <Box
                              sx={{
                                display: 'inline-block',
                                px: 1.5,
                                py: 0.5,
                                borderRadius: 1,
                                bgcolor: getHeatmapColor(dataset.avg_quality_score),
                                color: 'white',
                                fontWeight: 600,
                                minWidth: 60,
                                textAlign: 'center',
                              }}
                            >
                              {(dataset.avg_quality_score * 100).toFixed(1)}%
                            </Box>
                          </TableCell>
                          <TableCell align="right">
                            <Box
                              sx={{
                                display: 'inline-block',
                                px: 1.5,
                                py: 0.5,
                                borderRadius: 1,
                                bgcolor: getHeatmapColor(dataset.avg_completeness),
                                color: 'white',
                                fontWeight: 600,
                                minWidth: 60,
                                textAlign: 'center',
                              }}
                            >
                              {(dataset.avg_completeness * 100).toFixed(1)}%
                            </Box>
                          </TableCell>
                          <TableCell align="right">
                            <Box
                              sx={{
                                display: 'inline-block',
                                px: 1.5,
                                py: 0.5,
                                borderRadius: 1,
                                bgcolor: getHeatmapColor(dataset.avg_validity),
                                color: 'white',
                                fontWeight: 600,
                                minWidth: 60,
                                textAlign: 'center',
                              }}
                            >
                              {(dataset.avg_validity * 100).toFixed(1)}%
                            </Box>
                          </TableCell>
                          <TableCell align="right">
                            <Box
                              sx={{
                                display: 'inline-block',
                                px: 1.5,
                                py: 0.5,
                                borderRadius: 1,
                                bgcolor: getHeatmapColor(dataset.avg_uniqueness),
                                color: 'white',
                                fontWeight: 600,
                                minWidth: 60,
                                textAlign: 'center',
                              }}
                            >
                              {(dataset.avg_uniqueness * 100).toFixed(1)}%
                            </Box>
                          </TableCell>
                          <TableCell align="right">
                            <Chip
                              label={dataset.total_issues}
                              size="small"
                              color={
                                dataset.total_issues === 0 ? 'success' :
                                dataset.total_issues < 10 ? 'warning' : 'error'
                              }
                            />
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Quality Trends Over Time (if we have historical data) */}
        {datasets.some(d => d.latest_report) && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Latest Quality Metrics Comparison
                </Typography>
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart 
                    data={datasets
                      .filter(d => d.latest_report)
                      .map(d => ({
                        name: d.dataset_type.length > 15 ? d.dataset_type.substring(0, 15) + '...' : d.dataset_type,
                        fullName: d.dataset_type,
                        Quality: Number((d.latest_report!.quality_score * 100).toFixed(1)),
                        Completeness: Number((d.latest_report!.completeness_score * 100).toFixed(1)),
                        Validity: Number((d.latest_report!.validity_score * 100).toFixed(1)),
                        Uniqueness: Number((d.latest_report!.uniqueness_score * 100).toFixed(1)),
                      }))}
                    margin={{ top: 20, right: 30, left: 20, bottom: 100 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                    <XAxis 
                      dataKey="name" 
                      angle={-45} 
                      textAnchor="end" 
                      height={120}
                      interval={0}
                      tick={{ fontSize: 11 }}
                    />
                    <YAxis 
                      domain={[0, 100]} 
                      tick={{ fontSize: 12 }}
                      label={{ value: 'Score (%)', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle' } }}
                    />
                    <RechartsTooltip 
                      formatter={(value: any, name: string) => [`${value}%`, name]}
                      labelFormatter={(label, payload) => payload?.[0]?.payload?.fullName || label}
                      contentStyle={{ backgroundColor: '#fff', border: '1px solid #ccc', borderRadius: '4px' }}
                    />
                    <Legend 
                      wrapperStyle={{ paddingTop: '20px' }}
                      iconType="rect"
                    />
                    <Bar dataKey="Quality" fill="#3B2F8F" radius={[4, 4, 0, 0]} maxBarSize={60} />
                    <Bar dataKey="Completeness" fill="#2196f3" radius={[4, 4, 0, 0]} maxBarSize={60} />
                    <Bar dataKey="Validity" fill="#00bcd4" radius={[4, 4, 0, 0]} maxBarSize={60} />
                    <Bar dataKey="Uniqueness" fill="#9c27b0" radius={[4, 4, 0, 0]} maxBarSize={60} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      {/* Dataset Quality Table */}
      <Paper>
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <Typography variant="h6">Dataset Quality Metrics</Typography>
        </Box>
        {datasets.length === 0 ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              No quality data available
            </Typography>
          </Box>
        ) : (
          datasets.map((dataset) => (
            <Accordion
              key={dataset.dataset_type}
              expanded={expandedDataset === dataset.dataset_type}
              onChange={() => setExpandedDataset(
                expandedDataset === dataset.dataset_type ? null : dataset.dataset_type
              )}
            >
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Grid container spacing={2} alignItems="center" sx={{ width: '100%', pr: 2 }}>
                  <Grid item xs={12} md={3}>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                      {dataset.dataset_type}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {dataset.total_runs} runs
                    </Typography>
                  </Grid>
                  <Grid item xs={6} md={2}>
                    <Box>
                      <Typography variant="caption" color="text.secondary">Quality Score</Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', mt: 0.5 }}>
                        <Chip
                          label={`${(dataset.avg_quality_score * 100).toFixed(1)}%`}
                          size="small"
                          color={getScoreColor(dataset.avg_quality_score) as any}
                        />
                      </Box>
                    </Box>
                  </Grid>
                  <Grid item xs={6} md={2}>
                    <Box>
                      <Typography variant="caption" color="text.secondary">Completeness</Typography>
                      <Typography variant="body2">
                        {(dataset.avg_completeness * 100).toFixed(1)}%
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6} md={2}>
                    <Box>
                      <Typography variant="caption" color="text.secondary">Validity</Typography>
                      <Typography variant="body2">
                        {(dataset.avg_validity * 100).toFixed(1)}%
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6} md={3}>
                    <Box>
                      <Typography variant="caption" color="text.secondary">Issues</Typography>
                      <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5 }}>
                        {dataset.critical_issues > 0 && (
                          <Chip label={`${dataset.critical_issues} Critical`} size="small" color="error" />
                        )}
                        {dataset.high_issues > 0 && (
                          <Chip label={`${dataset.high_issues} High`} size="small" color="error" />
                        )}
                        {dataset.medium_issues > 0 && (
                          <Chip label={`${dataset.medium_issues} Medium`} size="small" color="warning" />
                        )}
                        {dataset.total_issues === 0 && (
                          <Chip label="No Issues" size="small" color="success" />
                        )}
                      </Box>
                    </Box>
                  </Grid>
                </Grid>
              </AccordionSummary>
              <AccordionDetails>
                {dataset.latest_report && (
                  <Box>
                    <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600 }}>
                      Latest Quality Report Issues
                    </Typography>
                    {dataset.latest_report.issues.length === 0 ? (
                      <Alert severity="success">No issues found in latest report</Alert>
                    ) : (
                      <TableContainer>
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              <TableCell>Severity</TableCell>
                              <TableCell>Type</TableCell>
                              <TableCell>Field</TableCell>
                              <TableCell>Description</TableCell>
                              <TableCell align="right">Affected Rows</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {dataset.latest_report.issues
                              .sort((a, b) => {
                                const severityOrder = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3, INFO: 4 };
                                return (severityOrder[a.severity as keyof typeof severityOrder] || 99) -
                                  (severityOrder[b.severity as keyof typeof severityOrder] || 99);
                              })
                              .map((issue, idx) => (
                                <TableRow key={idx}>
                                  <TableCell>
                                    <Chip
                                      label={issue.severity}
                                      size="small"
                                      color={getSeverityColor(issue.severity) as any}
                                    />
                                  </TableCell>
                                  <TableCell>{issue.issue_type}</TableCell>
                                  <TableCell>{issue.field || '-'}</TableCell>
                                  <TableCell>{issue.issue_description}</TableCell>
                                  <TableCell align="right">
                                    {issue.affected_row_indices?.length || 0}
                                  </TableCell>
                                </TableRow>
                              ))}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    )}
                  </Box>
                )}
              </AccordionDetails>
            </Accordion>
          ))
        )}
      </Paper>
    </Box>
  );
}

