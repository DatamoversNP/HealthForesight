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
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Schedule as ScheduleIcon,
  TrendingUp as TrendingUpIcon,
  Assessment as AssessmentIcon,
} from '@mui/icons-material';
import { healthForesightColors } from '../theme/healthForesightTheme';
import { useTheme } from '@mui/material/styles';
import { apiClient } from '../lib/api';

interface PipelineMetrics {
  pipeline_id: string;
  pipeline_name: string;
  status: string;
  last_run_at?: string;
  last_successful_run_at?: string;
  total_runs: number;
  successful_runs: number;
  failed_runs: number;
  total_records_processed: number;
  avg_records_per_run: number;
  success_rate: number;
  avg_execution_time: number;
  health_score: number;
  active: boolean;
}

interface PipelineRun {
  run_id: string;
  pipeline_id: string;
  pipeline_name: string;
  status: string;
  started_at: string;
  completed_at?: string;
  records_processed: number;
  records_succeeded: number;
  records_failed: number;
  quality_score?: number;
  execution_time_seconds?: number;
}

export default function PipelineMonitoringPage() {
  const theme = useTheme();
  const [pipelines, setPipelines] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<PipelineMetrics[]>([]);
  const [recentRuns, setRecentRuns] = useState<PipelineRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

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

      // Load all pipelines
      const pipelinesData = await apiClient.getPipelines(false);
      setPipelines(pipelinesData);

      // Load metrics for each pipeline
      const metricsPromises = pipelinesData.map(async (pipeline: any) => {
        try {
          const runs = await apiClient.getPipelineRuns(pipeline.pipeline_id);
          const health = await apiClient.getPipelineHealth(pipeline.pipeline_id).catch(() => null);
          
          const completedRuns = runs.filter((r: any) => r.status === 'COMPLETED');
          const failedRuns = runs.filter((r: any) => r.status === 'FAILED');
          const totalRecords = runs.reduce((sum: number, r: any) => sum + (r.records_processed || 0), 0);
          const totalTime = runs.reduce((sum: number, r: any) => sum + (r.metadata?.metrics?.execution_time_seconds || 0), 0);

          return {
            pipeline_id: pipeline.pipeline_id,
            pipeline_name: pipeline.pipeline_name,
            status: health?.status_message || 'Unknown',
            last_run_at: runs[0]?.started_at,
            last_successful_run_at: completedRuns[0]?.completed_at,
            total_runs: runs.length,
            successful_runs: completedRuns.length,
            failed_runs: failedRuns.length,
            total_records_processed: totalRecords,
            avg_records_per_run: runs.length > 0 ? Math.round(totalRecords / runs.length) : 0,
            success_rate: runs.length > 0 ? (completedRuns.length / runs.length) * 100 : 0,
            avg_execution_time: runs.length > 0 ? totalTime / runs.length : 0,
            health_score: health?.overall_health_score || 0,
            active: pipeline.active,
          };
        } catch (err: any) {
          // Silently handle timeout errors - they're expected if API is slow or endpoint doesn't exist
          const isTimeout = err?.code === 'ECONNABORTED' || 
                           err?.message?.includes('timeout') || 
                           err?.message === 'API timeout';
          if (!isTimeout) {
            console.error(`Error loading metrics for pipeline ${pipeline.pipeline_id}:`, err);
          }
          return null;
        }
      });

      const metricsData = (await Promise.all(metricsPromises)).filter((m): m is PipelineMetrics => m !== null);
      setMetrics(metricsData);

      // Load recent runs across all pipelines
      const allRuns: PipelineRun[] = [];
      for (const pipeline of pipelinesData) {
        try {
          const runs = await apiClient.getPipelineRuns(pipeline.pipeline_id);
          const pipelineRuns = runs.slice(0, 5).map((run: any) => ({
            ...run,
            pipeline_name: pipeline.pipeline_name,
            quality_score: run.metadata?.quality_report?.quality_score,
            execution_time_seconds: run.metadata?.metrics?.execution_time_seconds,
          }));
          allRuns.push(...pipelineRuns);
        } catch (err: any) {
          // Silently handle timeout errors
          const isTimeout = err?.code === 'ECONNABORTED' || 
                           err?.message?.includes('timeout') || 
                           err?.message === 'API timeout';
          if (!isTimeout) {
            console.error(`Error loading runs for pipeline ${pipeline.pipeline_id}:`, err);
          }
        }
      }
      
      // Sort by started_at descending
      allRuns.sort((a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime());
      setRecentRuns(allRuns.slice(0, 20));

    } catch (err: any) {
      setError(err.message || 'Failed to load pipeline monitoring data');
      console.error('Error loading pipeline monitoring data:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
      case 'healthy':
        return 'success';
      case 'failed':
      case 'unhealthy':
        return 'error';
      case 'processing':
      case 'pending':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getHealthScoreColor = (score: number) => {
    if (score >= 0.8) return 'success';
    if (score >= 0.6) return 'warning';
    return 'error';
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 1600, mx: 'auto', p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, color: healthForesightColors.neutral.dark }}>
          Pipeline Monitoring Dashboard
        </Typography>
        <Tooltip title="Refresh">
          <IconButton onClick={loadData} disabled={refreshing} sx={{ color: healthForesightColors.primary.main }}>
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <AssessmentIcon sx={{ color: healthForesightColors.primary.main, mr: 1 }} />
                <Typography variant="h6">Total Pipelines</Typography>
              </Box>
              <Typography variant="h4">{pipelines.length}</Typography>
              <Typography variant="body2" color="text.secondary">
                {pipelines.filter(p => p.active).length} active
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <TrendingUpIcon sx={{ color: theme.palette.success.main, mr: 1 }} />
                <Typography variant="h6">Total Records</Typography>
              </Box>
              <Typography variant="h4">
                {metrics.reduce((sum, m) => sum + m.total_records_processed, 0).toLocaleString()}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Across all pipelines
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <CheckCircleIcon sx={{ color: theme.palette.success.main, mr: 1 }} />
                <Typography variant="h6">Success Rate</Typography>
              </Box>
              <Typography variant="h4">
                {metrics.length > 0
                  ? Math.round(metrics.reduce((sum, m) => sum + m.success_rate, 0) / metrics.length)
                  : 0}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Average across pipelines
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <ScheduleIcon sx={{ color: theme.palette.warning.main, mr: 1 }} />
                <Typography variant="h6">Total Runs</Typography>
              </Box>
              <Typography variant="h4">
                {metrics.reduce((sum, m) => sum + m.total_runs, 0)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {metrics.reduce((sum, m) => sum + m.failed_runs, 0)} failed
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Pipeline Metrics Table */}
      <Paper sx={{ mb: 4 }}>
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <Typography variant="h6">Pipeline Performance Metrics</Typography>
        </Box>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Pipeline Name</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Total Runs</TableCell>
                <TableCell align="right">Success Rate</TableCell>
                <TableCell align="right">Total Records</TableCell>
                <TableCell align="right">Avg Records/Run</TableCell>
                <TableCell align="right">Avg Time (s)</TableCell>
                <TableCell align="right">Health Score</TableCell>
                <TableCell>Last Run</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {metrics.map((metric) => (
                <TableRow key={metric.pipeline_id}>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      {metric.active ? (
                        <Chip label="Active" size="small" color="success" sx={{ mr: 1 }} />
                      ) : (
                        <Chip label="Inactive" size="small" sx={{ mr: 1 }} />
                      )}
                      {metric.pipeline_name}
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={metric.status}
                      size="small"
                      color={getStatusColor(metric.status) as any}
                    />
                  </TableCell>
                  <TableCell align="right">{metric.total_runs}</TableCell>
                  <TableCell align="right">
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                      {metric.success_rate.toFixed(1)}%
                      {metric.success_rate >= 90 ? (
                        <CheckCircleIcon sx={{ color: 'success.main', ml: 0.5, fontSize: 16 }} />
                      ) : metric.success_rate < 70 ? (
                        <ErrorIcon sx={{ color: 'error.main', ml: 0.5, fontSize: 16 }} />
                      ) : (
                        <WarningIcon sx={{ color: 'warning.main', ml: 0.5, fontSize: 16 }} />
                      )}
                    </Box>
                  </TableCell>
                  <TableCell align="right">{metric.total_records_processed.toLocaleString()}</TableCell>
                  <TableCell align="right">{metric.avg_records_per_run.toLocaleString()}</TableCell>
                  <TableCell align="right">{metric.avg_execution_time.toFixed(2)}</TableCell>
                  <TableCell align="right">
                    <Chip
                      label={`${(metric.health_score * 100).toFixed(0)}%`}
                      size="small"
                      color={getHealthScoreColor(metric.health_score) as any}
                    />
                  </TableCell>
                  <TableCell>
                    {metric.last_run_at
                      ? new Date(metric.last_run_at).toLocaleString()
                      : 'Never'}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Recent Runs */}
      <Paper>
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <Typography variant="h6">Recent Pipeline Runs</Typography>
        </Box>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Pipeline</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Records Processed</TableCell>
                <TableCell align="right">Records Succeeded</TableCell>
                <TableCell align="right">Records Failed</TableCell>
                <TableCell align="right">Quality Score</TableCell>
                <TableCell align="right">Duration (s)</TableCell>
                <TableCell>Started At</TableCell>
                <TableCell>Completed At</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {recentRuns.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} align="center">
                    <Typography variant="body2" color="text.secondary">
                      No pipeline runs found
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                recentRuns.map((run) => (
                  <TableRow key={run.run_id}>
                    <TableCell>{run.pipeline_name}</TableCell>
                    <TableCell>
                      <Chip
                        label={run.status}
                        size="small"
                        color={getStatusColor(run.status) as any}
                      />
                    </TableCell>
                    <TableCell align="right">{run.records_processed.toLocaleString()}</TableCell>
                    <TableCell align="right">{run.records_succeeded.toLocaleString()}</TableCell>
                    <TableCell align="right">
                      {run.records_failed > 0 ? (
                        <Chip label={run.records_failed} size="small" color="error" />
                      ) : (
                        run.records_failed
                      )}
                    </TableCell>
                    <TableCell align="right">
                      {run.quality_score !== undefined ? (
                        <Chip
                          label={`${(run.quality_score * 100).toFixed(1)}%`}
                          size="small"
                          color={getHealthScoreColor(run.quality_score) as any}
                        />
                      ) : (
                        '-'
                      )}
                    </TableCell>
                    <TableCell align="right">
                      {run.execution_time_seconds?.toFixed(2) || '-'}
                    </TableCell>
                    <TableCell>{new Date(run.started_at).toLocaleString()}</TableCell>
                    <TableCell>
                      {run.completed_at ? new Date(run.completed_at).toLocaleString() : '-'}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  );
}

