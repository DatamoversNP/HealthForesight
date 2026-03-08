/**
 * Policy Preview Component - Step 6 (Review & Save) of Policy Builder
 * Human-readable summary with complexity warnings
 */
import { Box, Typography, Paper, Alert, Chip, Divider, List, ListItem, ListItemText } from '@mui/material'
import { Warning as WarningIcon, CheckCircle as CheckCircleIcon } from '@mui/icons-material'

interface PolicyPreviewProps {
  policy: any
}

export default function PolicyPreview({ policy }: PolicyPreviewProps) {
  const warnings: string[] = []
  const isValid: boolean[] = []

  // Validation checks
  if (!policy.name) {
    warnings.push('Policy name is required')
  } else {
    isValid.push(true)
  }

  if (!policy.scope.lob.length) {
    warnings.push('At least one Line of Business must be selected')
  } else {
    isValid.push(true)
  }

  if (!policy.scope.markets.length) {
    warnings.push('At least one Market must be selected')
  } else {
    isValid.push(true)
  }

  if (!policy.levers || policy.levers.length === 0) {
    warnings.push('At least one lever is required')
  } else {
    isValid.push(true)
    // Check if levers have codes
    policy.levers.forEach((lever: any, idx: number) => {
      // Check both parameters.codes and targets.codes (for different lever types)
      const hasCodes = 
        (lever.parameters?.codes && lever.parameters.codes.length > 0) ||
        (lever.parameters?.allowed_sites && lever.parameters.allowed_sites.length > 0) ||
        (lever.parameters?.disallowed_sites && lever.parameters.disallowed_sites.length > 0) ||
        (lever.targets?.codes && lever.targets.codes.length > 0) ||
        (lever.targets?.code_groups && lever.targets.code_groups.length > 0)
      
      if (!hasCodes) {
        warnings.push(`Lever ${idx + 1} (${lever.lever_type}) has no target codes`)
      }
    })
  }

  if (!policy.effective_period.start_date) {
    warnings.push('Effective start date is required')
  } else {
    isValid.push(true)
  }

  // Complexity warnings
  if (policy.levers?.length > 3) {
    warnings.push('Policy has multiple levers - ensure they don\'t conflict')
  }

  if (policy.apply_when?.length > 2) {
    warnings.push('Multiple condition groups may make policy complex to analyze')
  }

  const allValid = warnings.length === 0

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Typography variant="h6">Policy Summary</Typography>

      {!allValid && (
        <Alert severity="warning" icon={<WarningIcon />}>
          <Typography variant="subtitle2" gutterBottom>
            Please address the following issues:
          </Typography>
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {warnings.map((warning, idx) => (
              <li key={idx}>{warning}</li>
            ))}
          </ul>
        </Alert>
      )}

      {allValid && (
        <Alert severity="success" icon={<CheckCircleIcon />}>
          Policy is ready to save. Review the summary below.
        </Alert>
      )}

      {/* Basic Info */}
      <Paper sx={{ p: 2 }}>
        <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
          Basic Information
        </Typography>
        <List dense>
          <ListItem>
            <ListItemText primary="Name" secondary={policy.name || 'Not set'} />
          </ListItem>
          <ListItem>
            <ListItemText primary="Type" secondary={policy.policy_type?.replace(/_/g, ' ') || 'Not set'} />
          </ListItem>
          <ListItem>
            <ListItemText primary="Description" secondary={policy.description || 'No description'} />
          </ListItem>
          <ListItem>
            <ListItemText primary="Owner Role" secondary={policy.owner_role || 'Not set'} />
          </ListItem>
          <ListItem>
            <ListItemText 
              primary="Status" 
              secondary={
                <Box component="span">
                  <Chip label={policy.status || 'DRAFT'} size="small" />
                </Box>
              } 
            />
          </ListItem>
        </List>
      </Paper>

      {/* Scope */}
      <Paper sx={{ p: 2 }}>
        <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
          Scope
        </Typography>
        <List dense>
          <ListItem>
            <ListItemText
              primary="Line of Business"
              secondaryTypographyProps={{ component: 'div' }}
              secondary={
                <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 0.5 }}>
                  {policy.scope.lob.length > 0 ? (
                    policy.scope.lob.map((lob: string) => <Chip key={lob} label={lob} size="small" />)
                  ) : (
                    <Typography variant="body2" color="error" component="span">
                      Not set
                    </Typography>
                  )}
                </Box>
              }
            />
          </ListItem>
          <ListItem>
            <ListItemText
              primary="Markets"
              secondaryTypographyProps={{ component: 'div' }}
              secondary={
                <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 0.5 }}>
                  {policy.scope.markets.length > 0 ? (
                    policy.scope.markets.map((market: string) => <Chip key={market} label={market} size="small" />)
                  ) : (
                    <Typography variant="body2" color="error" component="span">
                      Not set
                    </Typography>
                  )}
                </Box>
              }
            />
          </ListItem>
          <ListItem>
            <ListItemText
              primary="Network"
              secondaryTypographyProps={{ component: 'div' }}
              secondary={
                <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 0.5 }}>
                  {policy.scope.network.length > 0 ? (
                    policy.scope.network.map((net: string) => <Chip key={net} label={net} size="small" />)
                  ) : (
                    <Typography variant="body2" color="error" component="span">
                      Not set
                    </Typography>
                  )}
                </Box>
              }
            />
          </ListItem>
          <ListItem>
            <ListItemText primary="Effective Start Date" secondary={policy.effective_period.start_date || 'Not set'} />
          </ListItem>
          {policy.effective_period.end_date && (
            <ListItem>
              <ListItemText primary="Effective End Date" secondary={policy.effective_period.end_date} />
            </ListItem>
          )}
        </List>
      </Paper>

      {/* Levers */}
      <Paper sx={{ p: 2 }}>
        <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
          Policy Levers ({policy.levers?.length || 0})
        </Typography>
        {policy.levers && policy.levers.length > 0 ? (
          <List dense>
            {policy.levers.map((lever: any, idx: number) => (
              <ListItem key={idx}>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Chip label={lever.lever_type?.replace(/_/g, ' ') || 'Unknown'} size="small" color="primary" />
                      <Typography variant="caption" color="text.secondary">
                        Priority: {lever.priority || idx + 1}
                      </Typography>
                    </Box>
                  }
                  secondaryTypographyProps={{ component: 'div' }}
                  secondary={
                    <Box sx={{ mt: 0.5, display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                      {/* Show codes from parameters or targets */}
                      {lever.parameters?.codes && lever.parameters.codes.length > 0 && (
                        <Box>
                          <Typography variant="body2" component="span">
                            Codes: {lever.parameters.codes.join(', ')}
                          </Typography>
                        </Box>
                      )}
                      {lever.targets?.codes && lever.targets.codes.length > 0 && (
                        <Box>
                          <Typography variant="body2" component="span">
                            Codes ({lever.targets.code_type || 'CPT'}): {lever.targets.codes.join(', ')}
                          </Typography>
                        </Box>
                      )}
                      {lever.parameters?.allowed_sites && lever.parameters.allowed_sites.length > 0 && (
                        <Box>
                          <Typography variant="body2" component="span">
                            Allowed Sites: {lever.parameters.allowed_sites.join(', ')}
                          </Typography>
                        </Box>
                      )}
                      {lever.parameters?.disallowed_sites && lever.parameters.disallowed_sites.length > 0 && (
                        <Box>
                          <Typography variant="body2" component="span">
                            Disallowed Sites: {lever.parameters.disallowed_sites.join(', ')}
                          </Typography>
                        </Box>
                      )}
                      {!lever.parameters?.codes?.length && !lever.targets?.codes?.length && 
                       !lever.parameters?.allowed_sites?.length && (
                        <Box>
                          <Typography variant="body2" color="error" component="span">
                            No codes or sites configured
                          </Typography>
                        </Box>
                      )}
                      {lever.targets?.code_groups?.length > 0 && (
                        <Box>
                          <Typography variant="body2" color="text.secondary" component="span">
                            Code Groups: {lever.targets.code_groups.join(', ')}
                          </Typography>
                        </Box>
                      )}
                      {/* Show other parameters */}
                      {lever.parameters?.enforcement && (
                        <Box>
                          <Typography variant="body2" color="text.secondary" component="span">
                            Enforcement: {lever.parameters.enforcement}
                          </Typography>
                        </Box>
                      )}
                      {lever.parameters?.criteria_set && (
                        <Box>
                          <Typography variant="body2" color="text.secondary" component="span">
                            Criteria Set: {lever.parameters.criteria_set}
                          </Typography>
                        </Box>
                      )}
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        ) : (
          <Typography variant="body2" color="error">
            No levers configured
          </Typography>
        )}
      </Paper>

      {/* Conditions */}
      {policy.apply_when && policy.apply_when.length > 0 && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
            Apply When Conditions
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {policy.apply_when.length} rule group(s) configured
          </Typography>
        </Paper>
      )}

      {/* Exceptions */}
      {policy.global_exceptions && policy.global_exceptions.length > 0 && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
            Global Exceptions ({policy.global_exceptions.length})
          </Typography>
          <List dense>
            {policy.global_exceptions.map((exception: any, idx: number) => (
              <ListItem key={idx}>
                <ListItemText
                  primary={`${exception.field} ${exception.operator} ${Array.isArray(exception.value) ? exception.value.join(', ') : exception.value}`}
                  secondary={exception.description || 'No description'}
                />
              </ListItem>
            ))}
          </List>
        </Paper>
      )}
    </Box>
  )
}

