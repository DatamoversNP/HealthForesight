// Full Lineage Tab Component - extracted for clarity
import { Box, Card, CardContent, Chip, Grid, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Typography } from '@mui/material'

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

interface Props {
  fullLineage: FullLineage | null
}

export default function FullLineageTab({ fullLineage }: Props) {
  if (!fullLineage) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          Loading full lineage data...
        </Typography>
      </Paper>
    )
  }

  return (
    <Grid container spacing={3}>
      {/* Summary Cards */}
      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Typography variant="h6">{fullLineage.sources.length}</Typography>
            <Typography variant="body2" color="text.secondary">
              Data Sources
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Typography variant="h6">{fullLineage.ingestions.length}</Typography>
            <Typography variant="body2" color="text.secondary">
              Ingestions
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Typography variant="h6">{fullLineage.analyses.length}</Typography>
            <Typography variant="body2" color="text.secondary">
              Analyses
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Typography variant="h6">{fullLineage.exports.length}</Typography>
            <Typography variant="body2" color="text.secondary">
              Reports/Exports
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      {/* Lineage Flow Visualization */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Data Flow Pipeline: Source → Reports/Dashboards
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 2 }}>
              {/* Sources */}
              {fullLineage.sources.length > 0 && (
                <Box>
                  <Typography variant="subtitle2" color="primary" gutterBottom>
                    1. Sources ({fullLineage.sources.length})
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, ml: 2 }}>
                    {fullLineage.sources.slice(0, 10).map((source) => (
                      <Chip key={source.id} label={source.type} size="small" variant="outlined" />
                    ))}
                    {fullLineage.sources.length > 10 && (
                      <Chip label={`+${fullLineage.sources.length - 10} more`} size="small" />
                    )}
                  </Box>
                </Box>
              )}

              {/* Ingestions */}
              {fullLineage.ingestions.length > 0 && (
                <Box>
                  <Typography variant="subtitle2" color="primary" gutterBottom>
                    2. Ingestions ({fullLineage.ingestions.length})
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, ml: 2 }}>
                    {fullLineage.ingestions.slice(0, 10).map((ing) => (
                      <Chip
                        key={ing.id}
                        label={`${ing.ingestion_type} (${ing.status})`}
                        size="small"
                        color={ing.status === 'COMPLETED' ? 'success' : 'default'}
                      />
                    ))}
                    {fullLineage.ingestions.length > 10 && (
                      <Chip label={`+${fullLineage.ingestions.length - 10} more`} size="small" />
                    )}
                  </Box>
                </Box>
              )}

              {/* Datasets */}
              {fullLineage.datasets.length > 0 && (
                <Box>
                  <Typography variant="subtitle2" color="primary" gutterBottom>
                    3. Datasets ({fullLineage.datasets.length})
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, ml: 2 }}>
                    {fullLineage.datasets.slice(0, 10).map((dataset) => (
                      <Chip key={dataset.id} label={dataset.dataset_type} size="small" variant="outlined" />
                    ))}
                    {fullLineage.datasets.length > 10 && (
                      <Chip label={`+${fullLineage.datasets.length - 10} more`} size="small" />
                    )}
                  </Box>
                </Box>
              )}

              {/* Analyses */}
              {fullLineage.analyses.length > 0 && (
                <Box>
                  <Typography variant="subtitle2" color="primary" gutterBottom>
                    4. Analyses ({fullLineage.analyses.length})
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, ml: 2 }}>
                    {fullLineage.analyses.slice(0, 10).map((analysis) => (
                      <Chip
                        key={analysis.id}
                        label={`${analysis.analysis_type} (${analysis.status})`}
                        size="small"
                        color={analysis.status === 'COMPLETED' ? 'success' : 'default'}
                      />
                    ))}
                    {fullLineage.analyses.length > 10 && (
                      <Chip label={`+${fullLineage.analyses.length - 10} more`} size="small" />
                    )}
                  </Box>
                </Box>
              )}

              {/* Observations */}
              {fullLineage.observations.length > 0 && (
                <Box>
                  <Typography variant="subtitle2" color="primary" gutterBottom>
                    5. Observations ({fullLineage.observations.length})
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, ml: 2 }}>
                    {fullLineage.observations.slice(0, 10).map((obs) => (
                      <Chip key={obs.observation_id} label="Observed Impact" size="small" color="info" />
                    ))}
                    {fullLineage.observations.length > 10 && (
                      <Chip label={`+${fullLineage.observations.length - 10} more`} size="small" />
                    )}
                  </Box>
                </Box>
              )}

              {/* Exports/Reports */}
              {fullLineage.exports.length > 0 && (
                <Box>
                  <Typography variant="subtitle2" color="primary" gutterBottom>
                    6. Reports/Exports ({fullLineage.exports.length})
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, ml: 2 }}>
                    {fullLineage.exports.slice(0, 10).map((exp) => (
                      <Chip
                        key={exp.id}
                        label={`${exp.export_type} (${exp.status})`}
                        size="small"
                        color={exp.status === 'COMPLETED' ? 'success' : 'default'}
                      />
                    ))}
                    {fullLineage.exports.length > 10 && (
                      <Chip label={`+${fullLineage.exports.length - 10} more`} size="small" />
                    )}
                  </Box>
                </Box>
              )}

              {/* Dashboards */}
              {fullLineage.dashboards.length > 0 && (
                <Box>
                  <Typography variant="subtitle2" color="primary" gutterBottom>
                    7. Dashboards ({fullLineage.dashboards.length})
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, ml: 2 }}>
                    {fullLineage.dashboards.slice(0, 10).map((dash) => (
                      <Chip key={dash.id} label={dash.type.replace('_', ' ')} size="small" color="secondary" />
                    ))}
                    {fullLineage.dashboards.length > 10 && (
                      <Chip label={`+${fullLineage.dashboards.length - 10} more`} size="small" />
                    )}
                  </Box>
                </Box>
              )}
            </Box>

            {/* Relationships Table */}
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
                          <TableCell>
                            <Chip label={`${rel.from_type}: ${rel.from_id.substring(0, 8)}...`} size="small" />
                          </TableCell>
                          <TableCell>
                            <Typography variant="caption">{rel.relationship_type}</Typography>
                          </TableCell>
                          <TableCell>
                            <Chip label={`${rel.to_type}: ${rel.to_id.substring(0, 8)}...`} size="small" />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
                {fullLineage.relationships.length > 20 && (
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                    Showing first 20 of {fullLineage.relationships.length} relationships
                  </Typography>
                )}
              </Box>
            )}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  )
}
