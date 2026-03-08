/**
 * Cohort Builder Dialog - For analysts to create reusable policy cohorts
 * A cohort is a saved filter specification that can be used in analyses
 */
import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  TextField,
  Chip,
  Paper,
  List,
  ListItem,
  ListItemText,
  Divider,
  Alert,
  CircularProgress,
  Grid,
} from '@mui/material'
import {
  Save as SaveIcon,
  Preview as PreviewIcon,
  Close as CloseIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material'
import { apiClient } from '../../lib/api'

interface CohortBuilderDialogProps {
  open: boolean
  onClose: () => void
  initialCohort?: {
    name: string
    description: string
    filter: any
  }
  policies: any[]
  performance: any[]
  onCohortSaved?: () => void // Callback when cohort is saved
}

export default function CohortBuilderDialog({
  open,
  onClose,
  initialCohort,
  policies,
  performance,
  onCohortSaved,
}: CohortBuilderDialogProps) {
  const [cohortName, setCohortName] = useState(initialCohort?.name || '')
  const [cohortDescription, setCohortDescription] = useState(initialCohort?.description || '')
  const [matchingPolicies, setMatchingPolicies] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Apply filters to find matching policies
  useEffect(() => {
    if (!open || !initialCohort?.filter) {
      setMatchingPolicies([])
      return
    }

    setLoading(true)
    setError(null)

    try {
      const filter = initialCohort.filter
      let matched: any[] = []

      // Start with all policies that have performance data
      let candidatePolicies = performance.length > 0 ? performance : []

      // Apply filters based on criteria
      if (filter.utilization_change) {
        const min = filter.utilization_change.min !== undefined ? filter.utilization_change.min : -Infinity
        const max = filter.utilization_change.max !== undefined ? filter.utilization_change.max : Infinity
        candidatePolicies = candidatePolicies.filter((p: any) => {
          const change = p.avg_utilization_change_pct || 0
          return change >= min && change <= max
        })
      }
      
      if (filter.cost_impact) {
        const min = filter.cost_impact.min !== undefined ? filter.cost_impact.min : -Infinity
        const max = filter.cost_impact.max !== undefined ? filter.cost_impact.max : Infinity
        candidatePolicies = candidatePolicies.filter((p: any) => {
          const impact = p.avg_cost_impact || 0
          // For cost savings (negative values), we want impact <= max (e.g., <= -10000 means savings >= $10k)
          return impact >= min && impact <= max
        })
      }
      
      if (filter.created_after) {
        const afterDate = new Date(filter.created_after)
        // Filter policies by creation date
        candidatePolicies = candidatePolicies.filter((p: any) => {
          const policyId = p.policy_id || p.id
          const policy = policies.find((pol: any) => (pol.id || pol.policy_id) === policyId)
          if (!policy) return false
          const created = policy.created_at ? new Date(policy.created_at) : null
          return created && created >= afterDate
        })
      }
      
      if (filter.status) {
        // Filter policies by status
        candidatePolicies = candidatePolicies.filter((p: any) => {
          const policyId = p.policy_id || p.id
          const policy = policies.find((pol: any) => (pol.id || pol.policy_id) === policyId)
          return policy && policy.status === filter.status
        })
      }

      // If no performance data, try filtering policies directly
      if (candidatePolicies.length === 0 && performance.length === 0 && policies.length > 0) {
        // Fallback: filter policies directly if no performance data
        candidatePolicies = policies.map((p: any) => ({
          ...p,
          policy_id: p.id || p.policy_id,
          avg_utilization_change_pct: 0,
          avg_cost_impact: 0,
        }))
        
        if (filter.status) {
          candidatePolicies = candidatePolicies.filter((p: any) => p.status === filter.status)
        }
        if (filter.created_after) {
          const afterDate = new Date(filter.created_after)
          candidatePolicies = candidatePolicies.filter((p: any) => {
            const created = p.created_at ? new Date(p.created_at) : null
            return created && created >= afterDate
          })
        }
      }

      // Get full policy details for matched policies
      const matchedWithDetails = candidatePolicies.map((match: any) => {
        const policyId = match.policy_id || match.id
        const policy = policies.find((p: any) => (p.id || p.policy_id) === policyId) || match
        const perf = performance.find((p: any) => (p.policy_id || p.id) === policyId) || match
        return {
          ...policy,
          ...perf,
          policy_id: policyId,
          name: policy?.name || policy?.policy_name || match.name || match.policy_name || 'Unnamed Policy',
          policy_name: policy?.name || policy?.policy_name || match.policy_name || 'Unnamed Policy',
        }
      })

      setMatchingPolicies(matchedWithDetails)
    } catch (err: any) {
      console.error('Failed to filter policies:', err)
      setError(err.message || 'Failed to filter policies')
      setMatchingPolicies([])
    } finally {
      setLoading(false)
    }
  }, [open, initialCohort, policies, performance])

  const handleSave = async () => {
    if (!cohortName.trim()) {
      setError('Cohort name is required')
      return
    }

    if (matchingPolicies.length === 0) {
      setError('No policies match the criteria. Cannot save empty cohort.')
      return
    }

    setSaving(true)
    setError(null)

    try {
      const cohortData = {
        name: cohortName,
        description: cohortDescription || undefined,
        criteria: initialCohort?.filter || {},
      }

      await apiClient.createCohort(cohortData)
      setSaved(true)

      // Notify parent that cohort was saved
      if (onCohortSaved) {
        onCohortSaved()
      }

      // Close after a brief delay
      setTimeout(() => {
        onClose()
        setSaved(false)
        setCohortName('')
        setCohortDescription('')
      }, 1500)
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to save cohort')
    } finally {
      setSaving(false)
    }
  }

  const getFilterDescription = () => {
    if (!initialCohort?.filter) return 'No filters applied'
    
    const filter = initialCohort.filter
    if (filter.utilization_change) {
      const min = filter.utilization_change.min !== undefined ? `${filter.utilization_change.min}%` : 'any'
      const max = filter.utilization_change.max !== undefined ? `${filter.utilization_change.max}%` : 'any'
      return `Utilization change: ${min} to ${max}`
    }
    if (filter.cost_impact) {
      const min = filter.cost_impact.min !== undefined ? `$${filter.cost_impact.min.toLocaleString()}` : 'any'
      const max = filter.cost_impact.max !== undefined ? `$${filter.cost_impact.max.toLocaleString()}` : 'any'
      return `Cost impact: ${min} to ${max}`
    }
    if (filter.created_after) {
      return `Created after: ${new Date(filter.created_after).toLocaleDateString()}`
    }
    if (filter.status) {
      return `Status: ${filter.status}`
    }
    return 'Custom filters'
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">Build Cohort</Typography>
          <Button onClick={onClose} size="small" startIcon={<CloseIcon />}>
            Close
          </Button>
        </Box>
      </DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {saved && (
          <Alert severity="success" sx={{ mb: 2 }} icon={<CheckCircleIcon />}>
            Cohort saved successfully!
          </Alert>
        )}

        {/* Cohort Details */}
        <Box sx={{ mb: 3 }}>
          <TextField
            label="Cohort Name"
            value={cohortName}
            onChange={(e) => setCohortName(e.target.value)}
            fullWidth
            required
            sx={{ mb: 2 }}
            placeholder="e.g., High Impact Policies Q1 2024"
          />
          <TextField
            label="Description (Optional)"
            value={cohortDescription}
            onChange={(e) => setCohortDescription(e.target.value)}
            fullWidth
            multiline
            rows={2}
            placeholder="Describe what this cohort represents and how it will be used"
          />
        </Box>

        {/* Filter Summary */}
        <Paper sx={{ p: 2, mb: 3, bgcolor: 'background.default' }}>
          <Typography variant="subtitle2" gutterBottom>
            Filter Criteria
          </Typography>
          <Chip label={getFilterDescription()} color="primary" />
        </Paper>

        {/* Matching Policies Preview */}
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="subtitle1" fontWeight={600}>
              Matching Policies ({matchingPolicies.length})
            </Typography>
            {loading && <CircularProgress size={20} />}
          </Box>

          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : matchingPolicies.length === 0 ? (
            <Alert severity="info">
              No policies match the selected criteria. Adjust your filters or try a different cohort shortcut.
            </Alert>
          ) : (
            <Paper variant="outlined" sx={{ maxHeight: 400, overflow: 'auto' }}>
              <List>
                {matchingPolicies.slice(0, 20).map((policy: any, idx: number) => (
                  <Box key={idx}>
                    <ListItem>
                      <ListItemText
                        primary={
                          <Typography variant="subtitle2">
                            {policy.name || policy.policy_name || 'Unnamed Policy'}
                          </Typography>
                        }
                        secondary={
                          <Box>
                            {policy.avg_utilization_change_pct !== undefined && (
                              <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                                Utilization: {policy.avg_utilization_change_pct.toFixed(1)}%
                              </Typography>
                            )}
                            {policy.avg_cost_impact !== undefined && (
                              <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                                Cost Impact: ${Math.abs(policy.avg_cost_impact).toLocaleString()}
                              </Typography>
                            )}
                            {policy.status && (
                              <Chip label={policy.status} size="small" sx={{ mt: 0.5 }} />
                            )}
                          </Box>
                        }
                      />
                    </ListItem>
                    {idx < Math.min(19, matchingPolicies.length - 1) && <Divider />}
                  </Box>
                ))}
              </List>
              {matchingPolicies.length > 20 && (
                <Box sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="caption" color="text.secondary">
                    Showing first 20 of {matchingPolicies.length} policies
                  </Typography>
                </Box>
              )}
            </Paper>
          )}
        </Box>

        {/* Use Cases */}
        <Paper sx={{ p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
          <Typography variant="subtitle2" gutterBottom>
            How to Use This Cohort
          </Typography>
          <Typography variant="body2" color="text.secondary" component="div">
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              <li>Run batch analyses on all policies in this cohort</li>
              <li>Compare performance across similar policies</li>
              <li>Track cohort metrics over time</li>
              <li>Use in sensitivity analysis runs</li>
              <li>Export cohort-specific reports</li>
            </ul>
          </Typography>
        </Paper>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={saving}>
          Cancel
        </Button>
        <Button
          onClick={handleSave}
          variant="contained"
          startIcon={saved ? <CheckCircleIcon /> : <SaveIcon />}
          disabled={saving || !cohortName.trim()}
        >
          {saving ? 'Saving...' : saved ? 'Saved!' : 'Save Cohort'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}

