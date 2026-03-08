/**
 * Lineage Page - Data Coverage Heatmap
 */
import { useState, useEffect } from 'react'
import {
  Box,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Tabs,
  Tab,
  Alert,
} from '@mui/material'
// Using Material-UI Table for heatmap visualization
import { apiClient } from '../lib/api'
import { format } from 'date-fns'
import { healthForesightColors } from '../theme/healthForesightTheme'

// Helper function to safely format dates
const safeFormatDate = (dateString: string | null | undefined, formatStr: string = 'MMM d, yyyy HH:mm'): string => {
  if (!dateString) return '-'
  try {
    const date = new Date(dateString)
    if (isNaN(date.getTime())) return '-'
    return format(date, formatStr)
  } catch {
    return '-'
  }
}

interface CoverageData {
  snapshot_id: string
  created_at: string
  coverage: Record<string, Record<string, Record<string, Record<string, number>>>>
}

interface Ingestion {
  id: string
  ingestion_type: string
  status: string
  created_at: string
  started_at?: string
  completed_at?: string
}

interface AnalysisRun {
  id: string
  analysis_id: string
  snapshot_id?: string
  status: string
  model_version?: string
  started_at?: string
  ended_at?: string
  duration_seconds?: number
}

interface FullLineage {
  sources: Array<{ id: string; type: string; uri: string; ingestion_id?: string; created_at?: string }>
  ingestions: Array<{ id: string; ingestion_type: string; status: string; created_at?: string }>
  datasets: Array<{ id: string; ingestion_id: string; dataset_type: string; status: string; created_at?: string }>
  analyses: Array<{ id: string; analysis_type: string; status: string; created_at?: string }>
  observations: Array<{ observation_id: string; policy_id?: string; computed_at?: string }>
  exports: Array<{ id: string; export_type: string; status: string; created_at?: string }>
  dashboards: Array<{ id: string; type: string; source_id: string; source_type: string; created_at?: string }>
  relationships: Array<{ from_type: string; from_id: string; to_type: string; to_id: string; relationship_type: string }>
}

export default function LineagePage() {
  const [coverage, setCoverage] = useState<CoverageData | null>(null)
  const [ingestions, setIngestions] = useState<Ingestion[]>([])
  const [analysisRuns, setAnalysisRuns] = useState<AnalysisRun[]>([])
  const [fullLineage, setFullLineage] = useState<FullLineage | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [tabValue, setTabValue] = useState(0)

  useEffect(() => {
    loadData()
    // Poll for updates every 10 seconds
    const interval = setInterval(loadData, 10000)
    return () => clearInterval(interval)
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const [coverageData, ingestionData, runsData, lineageData] = await Promise.all([
        apiClient.getDataCoverage().catch(() => null),
        apiClient.getRecentIngestions().catch(() => []),
        apiClient.getAnalysisRuns().catch(() => []),
        apiClient.getFullLineage().catch(() => null),
      ])

      if (coverageData) setCoverage(coverageData)
      setIngestions(ingestionData)
      setAnalysisRuns(runsData)
      if (lineageData) setFullLineage(lineageData)
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to load lineage data')
    } finally {
      setLoading(false)
    }
  }

  // Prepare heatmap data
  const prepareHeatmapData = () => {
    if (!coverage?.coverage) return { data: [], xLabels: [], yLabels: [] }

    const years = Object.keys(coverage.coverage).sort()
    const months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
    const lobs = ['COMMERCIAL', 'MA', 'MEDICAID']
    const markets = ['NYC', 'DFW', 'BOS']

    const yLabels: string[] = []
    const data: number[][] = []

    // Create rows: Year-Month combinations
    years.forEach((year) => {
      months.forEach((month) => {
        yLabels.push(`${year}-${month}`)
        const row: number[] = []

        // Create columns: LOB-Market combinations
        lobs.forEach((lob) => {
          markets.forEach((market) => {
            const count =
              coverage.coverage[year]?.[month]?.[lob]?.[market] || 0
            row.push(count)
          })
        })

        data.push(row)
      })
    })

    const xLabels = lobs.flatMap((lob) => markets.map((market) => `${lob}-${market}`))

    return { data, xLabels, yLabels }
  }

  const { data: heatmapData, xLabels, yLabels } = prepareHeatmapData()

  const getHeatmapColor = (value: number) => {
    if (value === 0) return '#f0f0f0'
    if (value < 1000) return '#ffcccc'
    if (value < 10000) return '#ff9999'
    if (value < 50000) return '#ff6666'
    if (value < 100000) return '#ff3333'
    return '#cc0000'
  }

  if (loading && !coverage) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography
          variant="h4"
          component="h1"
          sx={{
            fontFamily: 'IBM Plex Sans, Inter, sans-serif',
            fontWeight: 600,
            mb: 1,
            color: healthForesightColors.neutral.dark,
          }}
        >
          Lineage
        </Typography>
        <Typography
          variant="body1"
          sx={{
            color: healthForesightColors.neutral.mid,
            lineHeight: 1.6,
            mb: 2,
          }}
        >
          Track data freshness, ingestion history, and analysis runs. View coverage heatmap and data lineage.
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)} sx={{ mb: 3 }}>
        <Tab label="Coverage Heatmap" />
        <Tab label="Recent Ingestions" />
        <Tab label="Analysis Runs" />
        <Tab label="Full Lineage" />
      </Tabs>

      {tabValue === 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Data Coverage Heatmap
                </Typography>
                {coverage && (
                  <Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Snapshot: {safeFormatDate(coverage.created_at) || 'N/A'}
                    </Typography>
                    {heatmapData.length > 0 ? (
                      <Box sx={{ overflowX: 'auto', mt: 2 }}>
                        <TableContainer>
                          <Table size="small">
                            <TableHead>
                              <TableRow>
                                <TableCell>Period</TableCell>
                                {xLabels.map((label) => (
                                  <TableCell key={label} align="center">
                                    {label}
                                  </TableCell>
                                ))}
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              {yLabels.map((period, idx) => (
                                <TableRow key={period}>
                                  <TableCell>{period}</TableCell>
                                  {heatmapData[idx]?.map((value, colIdx) => (
                                    <TableCell
                                      key={colIdx}
                                      align="center"
                                      sx={{
                                        bgcolor: getHeatmapColor(value),
                                        color: value > 0 ? 'white' : 'text.primary',
                                        fontWeight: value > 0 ? 'bold' : 'normal',
                                      }}
                                    >
                                      {value > 0 ? value.toLocaleString() : '-'}
                                    </TableCell>
                                  ))}
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </TableContainer>
                      </Box>
                    ) : (
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                        No coverage data available
                      </Typography>
                    )}
                  </Box>
                )}
                {!coverage && (
                  <Typography variant="body2" color="text.secondary">
                    No coverage data available. Run an ingestion to populate data.
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {tabValue === 1 && (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Type</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Created</TableCell>
                <TableCell>Started</TableCell>
                <TableCell>Completed</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {ingestions.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} align="center">
                    <Typography variant="body2" color="text.secondary">
                      No ingestions found
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                ingestions.map((ingestion) => (
                  <TableRow key={ingestion.id} hover>
                    <TableCell>
                      <Chip label={ingestion.ingestion_type} size="small" />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={ingestion.status}
                        color={
                          ingestion.status === 'COMPLETED'
                            ? 'success'
                            : ingestion.status === 'FAILED'
                            ? 'error'
                            : 'default'
                        }
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {safeFormatDate(ingestion.created_at)}
                    </TableCell>
                    <TableCell>
                      {safeFormatDate(ingestion.started_at)}
                    </TableCell>
                    <TableCell>
                      {safeFormatDate(ingestion.completed_at)}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {tabValue === 2 && (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Analysis ID</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Model Version</TableCell>
                <TableCell>Started</TableCell>
                <TableCell>Ended</TableCell>
                <TableCell>Duration</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {analysisRuns.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    <Typography variant="body2" color="text.secondary">
                      No analysis runs found
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                analysisRuns.map((run) => (
                  <TableRow key={run.id} hover>
                    <TableCell>{run.analysis_id.substring(0, 8)}...</TableCell>
                    <TableCell>
                      <Chip
                        label={run.status}
                        color={
                          run.status === 'COMPLETED'
                            ? 'success'
                            : run.status === 'FAILED'
                            ? 'error'
                            : 'default'
                        }
                        size="small"
                      />
                    </TableCell>
                    <TableCell>{run.model_version || '-'}</TableCell>
                    <TableCell>
                      {safeFormatDate(run.started_at)}
                    </TableCell>
                    <TableCell>
                      {safeFormatDate(run.ended_at)}
                    </TableCell>
                    <TableCell>
                      {run.duration_seconds
                        ? `${(run.duration_seconds / 60).toFixed(1)} min`
                        : '-'}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {tabValue === 3 && (
        <Box>
          {!fullLineage ? (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                Loading full lineage data...
              </Typography>
            </Paper>
          ) : (
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent>
                    <Typography variant="h6">{fullLineage.sources.length}</Typography>
                    <Typography variant="body2" color="text.secondary">Data Sources</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent>
                    <Typography variant="h6">{fullLineage.ingestions.length}</Typography>
                    <Typography variant="body2" color="text.secondary">Ingestions</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent>
                    <Typography variant="h6">{fullLineage.analyses.length}</Typography>
                    <Typography variant="body2" color="text.secondary">Analyses</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent>
                    <Typography variant="h6">{fullLineage.exports.length}</Typography>
                    <Typography variant="body2" color="text.secondary">Reports/Exports</Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Data Flow Pipeline: Source → Reports/Dashboards
                    </Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 2 }}>
                      {fullLineage.sources.length > 0 && (
                        <Box>
                          <Typography variant="subtitle2" color="primary" gutterBottom>
                            1. Sources ({fullLineage.sources.length})
                          </Typography>
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, ml: 2 }}>
                            {fullLineage.sources.slice(0, 10).map((source) => (
                              <Chip key={source.id} label={source.type} size="small" variant="outlined" />
                            ))}
                          </Box>
                        </Box>
                      )}
                      {fullLineage.ingestions.length > 0 && (
                        <Box>
                          <Typography variant="subtitle2" color="primary" gutterBottom>
                            2. Ingestions ({fullLineage.ingestions.length})
                          </Typography>
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, ml: 2 }}>
                            {fullLineage.ingestions.slice(0, 10).map((ing) => (
                              <Chip key={ing.id} label={`${ing.ingestion_type} (${ing.status})`} size="small" 
                                    color={ing.status === 'COMPLETED' ? 'success' : 'default'} />
                            ))}
                          </Box>
                        </Box>
                      )}
                      {fullLineage.analyses.length > 0 && (
                        <Box>
                          <Typography variant="subtitle2" color="primary" gutterBottom>
                            3. Analyses ({fullLineage.analyses.length})
                          </Typography>
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, ml: 2 }}>
                            {fullLineage.analyses.slice(0, 10).map((analysis) => (
                              <Chip key={analysis.id} label={`${analysis.analysis_type} (${analysis.status})`} size="small"
                                    color={analysis.status === 'COMPLETED' ? 'success' : 'default'} />
                            ))}
                          </Box>
                        </Box>
                      )}
                      {fullLineage.observations.length > 0 && (
                        <Box>
                          <Typography variant="subtitle2" color="primary" gutterBottom>
                            4. Observations ({fullLineage.observations.length})
                          </Typography>
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, ml: 2 }}>
                            {fullLineage.observations.slice(0, 10).map((obs) => (
                              <Chip key={obs.observation_id} label="Observed Impact" size="small" color="info" />
                            ))}
                          </Box>
                        </Box>
                      )}
                      {fullLineage.exports.length > 0 && (
                        <Box>
                          <Typography variant="subtitle2" color="primary" gutterBottom>
                            5. Reports/Exports ({fullLineage.exports.length})
                          </Typography>
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, ml: 2 }}>
                            {fullLineage.exports.slice(0, 10).map((exp) => (
                              <Chip key={exp.id} label={`${exp.export_type} (${exp.status})`} size="small"
                                    color={exp.status === 'COMPLETED' ? 'success' : 'default'} />
                            ))}
                          </Box>
                        </Box>
                      )}
                    </Box>
                    {fullLineage.relationships.length > 0 && (
                      <Box sx={{ mt: 4 }}>
                        <Typography variant="h6" gutterBottom>
                          Relationships ({fullLineage.relationships.length})
                        </Typography>
                        <TableContainer>
                          <Table size="small">
                            <TableHead>
                              <TableRow>
                                <TableCell>From</TableCell>
                                <TableCell>Relationship</TableCell>
                                <TableCell>To</TableCell>
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              {fullLineage.relationships.slice(0, 20).map((rel, idx) => (
                                <TableRow key={idx}>
                                  <TableCell><Chip label={`${rel.from_type}: ${rel.from_id.substring(0, 8)}...`} size="small" /></TableCell>
                                  <TableCell><Typography variant="caption">{rel.relationship_type}</Typography></TableCell>
                                  <TableCell><Chip label={`${rel.to_type}: ${rel.to_id.substring(0, 8)}...`} size="small" /></TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </TableContainer>
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </Box>
      )}
    </Box>
  )
}
