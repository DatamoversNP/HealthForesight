/**
 * Behavior Dashboard Component - Epic 5
 * Displays provider behavior profiles and clusters
 */
import { useState, useEffect } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  LinearProgress,
} from '@mui/material'
import {
  CheckCircle as CompliantIcon,
  TrendingUp as AdaptiveIcon,
  Block as ResistantIcon,
  Warning as CircumventionIcon,
  Remove as NeutralIcon,
} from '@mui/icons-material'
import { apiClient } from '../../lib/api'

interface BehaviorProfile {
  provider_id: string
  provider_name?: string
  behavior_type: string
  confidence: number
  signals: Array<{
    metric_name: string
    metric_type: string
    value: number
    baseline_value: number
    change_pct: number
    significance: number
  }>
  first_detected: string
  last_updated: string
}

interface BehaviorCluster {
  cluster_id: string
  cluster_name: string
  behavior_type: string
  provider_ids: string[]
  cluster_characteristics: Record<string, any>
}

interface BehaviorDashboardProps {
  policyId?: string
}

export default function BehaviorDashboard({ policyId }: BehaviorDashboardProps) {
  const [profiles, setProfiles] = useState<BehaviorProfile[]>([])
  const [clusters, setClusters] = useState<BehaviorCluster[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState(0)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      const [profilesData, clustersData] = await Promise.all([
        apiClient.getBehaviorProfiles(),
        apiClient.getBehaviorClusters(),
      ])
      setProfiles(Array.isArray(profilesData) ? profilesData : [])
      setClusters(Array.isArray(clustersData) ? clustersData : [])
    } catch (err: any) {
      console.error('Failed to load behavior data:', err)
      setError(err.detail || err.message || 'Failed to load behavior data')
    } finally {
      setLoading(false)
    }
  }

  const getBehaviorIcon = (type: string) => {
    switch (type) {
      case 'COMPLIANCE':
        return <CompliantIcon />
      case 'ADAPTATION':
        return <AdaptiveIcon />
      case 'RESISTANCE':
        return <ResistantIcon />
      case 'CIRCUMVENTION':
        return <CircumventionIcon />
      default:
        return <NeutralIcon />
    }
  }

  const getBehaviorColor = (type: string) => {
    switch (type) {
      case 'COMPLIANCE':
        return 'success'
      case 'ADAPTATION':
        return 'info'
      case 'RESISTANCE':
        return 'warning'
      case 'CIRCUMVENTION':
        return 'error'
      default:
        return 'default'
    }
  }

  const behaviorCounts = profiles.reduce((acc, p) => {
    acc[p.behavior_type] = (acc[p.behavior_type] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    )
  }

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Behavior Dashboard
      </Typography>

      {/* Summary Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="success.main">
                {behaviorCounts['COMPLIANCE'] || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Compliant Providers
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="info.main">
                {behaviorCounts['ADAPTATION'] || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Adaptive Providers
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="warning.main">
                {behaviorCounts['RESISTANCE'] || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Resistant Providers
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="error.main">
                {behaviorCounts['CIRCUMVENTION'] || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Circumvention Providers
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Tabs value={activeTab} onChange={(e, v) => setActiveTab(v)} sx={{ mb: 2 }}>
        <Tab label="Provider Profiles" />
        <Tab label="Behavior Clusters" />
      </Tabs>

      {/* Provider Profiles Tab */}
      {activeTab === 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Provider Behavior Profiles
            </Typography>
            {profiles.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                No behavior profiles found. Profiles are created when behavior signals are detected.
              </Typography>
            ) : (
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell><strong>Provider</strong></TableCell>
                      <TableCell><strong>Behavior Type</strong></TableCell>
                      <TableCell align="right"><strong>Confidence</strong></TableCell>
                      <TableCell align="right"><strong>Signals</strong></TableCell>
                      <TableCell><strong>Last Updated</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {profiles.map((profile) => (
                      <TableRow key={profile.provider_id} hover>
                        <TableCell>
                          <Typography variant="body2" fontWeight="medium">
                            {profile.provider_name || profile.provider_id}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            icon={getBehaviorIcon(profile.behavior_type)}
                            label={profile.behavior_type}
                            color={getBehaviorColor(profile.behavior_type) as any}
                            size="small"
                          />
                        </TableCell>
                        <TableCell align="right">
                          <Box display="flex" alignItems="center" justifyContent="flex-end" gap={1}>
                            <Box sx={{ width: 80 }}>
                              <LinearProgress
                                variant="determinate"
                                value={profile.confidence * 100}
                                sx={{ height: 8, borderRadius: 1 }}
                              />
                            </Box>
                            <Typography variant="body2" sx={{ minWidth: 40 }}>
                              {(profile.confidence * 100).toFixed(0)}%
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell align="right">
                          {profile.signals?.length || 0}
                        </TableCell>
                        <TableCell>
                          <Typography variant="caption">
                            {new Date(profile.last_updated).toLocaleString()}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        </Card>
      )}

      {/* Behavior Clusters Tab */}
      {activeTab === 1 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Behavior Clusters
            </Typography>
            {clusters.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                No behavior clusters found. Clusters group providers with similar behavior patterns.
              </Typography>
            ) : (
              <Grid container spacing={2}>
                {clusters.map((cluster) => (
                  <Grid item xs={12} md={6} key={cluster.cluster_id}>
                    <Card variant="outlined">
                      <CardContent>
                        <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                          <Typography variant="h6">
                            {cluster.cluster_name}
                          </Typography>
                          <Chip
                            icon={getBehaviorIcon(cluster.behavior_type)}
                            label={cluster.behavior_type}
                            color={getBehaviorColor(cluster.behavior_type) as any}
                            size="small"
                          />
                        </Box>
                        <Typography variant="body2" color="text.secondary">
                          {cluster.provider_ids.length} providers
                        </Typography>
                        {Object.keys(cluster.cluster_characteristics || {}).length > 0 && (
                          <Box sx={{ mt: 1 }}>
                            <Typography variant="caption" color="text.secondary">
                              Characteristics: {Object.keys(cluster.cluster_characteristics || {}).join(', ')}
                            </Typography>
                          </Box>
                        )}
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  )
}

