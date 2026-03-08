/**
 * Policy Import Page - Import policies from external systems
 * Workflow: Upload → Review Mapping → Save
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Alert,
  Stepper,
  Step,
  StepLabel,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  CircularProgress,
} from '@mui/material'
import {
  CloudUpload as UploadIcon,
  Check as CheckIcon,
  Close as CloseIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  ArrowBack as ArrowBackIcon,
  ArrowForward as ArrowForwardIcon,
} from '@mui/icons-material'
import { apiClient } from '../lib/api'

const STEPS = ['Upload Package', 'Review Mapping', 'Save Policy']

interface PolicyMappingResult {
  success: boolean
  mapping_confidence: number
  unmapped_fields: string[]
  mapping_warnings: string[]
  mapping_errors: string[]
  canonical_policy?: {
    policy_name: string
    policy_type: string
    description: string
    status: string
    scope?: any
    effective_period?: any
    enforcement?: any
    policy_levers?: any[]
  }
}

export default function PolicyImportPage() {
  const navigate = useNavigate()
  const [activeStep, setActiveStep] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Step 1: Upload
  const [file, setFile] = useState<File | null>(null)
  const [sourceSystem, setSourceSystem] = useState('')
  const [sourceFormat, setSourceFormat] = useState('JSON')
  
  // Step 2: Review
  const [mappingResult, setMappingResult] = useState<PolicyMappingResult | null>(null)
  const [canonicalPolicy, setCanonicalPolicy] = useState<any>(null)
  const [saveAsVersion, setSaveAsVersion] = useState(false)
  const [existingPolicyId, setExistingPolicyId] = useState<string | null>(null)
  const [changeDescription, setChangeDescription] = useState('')
  
  // Step 3: Save
  const [savedPolicyId, setSavedPolicyId] = useState<string | null>(null)
  const [savedVersionId, setSavedVersionId] = useState<string | null>(null)

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0]
    if (selectedFile) {
      setFile(selectedFile)
      setError(null)
    }
  }

  const handleUpload = async () => {
    if (!file || !sourceSystem) {
      setError('Please select a file and specify source system')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('source_system', sourceSystem)
      formData.append('source_format', sourceFormat)

      const response = await apiClient.uploadPolicyPackage(file, sourceSystem, sourceFormat)

      setMappingResult(response.data.mapping_result)
      setCanonicalPolicy(response.data.mapping_result.canonical_policy)
      
      if (response.data.warnings && response.data.warnings.length > 0) {
        setError(`Warnings: ${response.data.warnings.join(', ')}`)
      }
      
      if (response.data.errors && response.data.errors.length > 0) {
        setError(`Errors: ${response.data.errors.join(', ')}`)
        return
      }

      setActiveStep(1) // Move to review step
    } catch (err: any) {
      setError(err.message || 'Failed to upload policy package')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!canonicalPolicy) {
      setError('No policy to save')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const reviewData = {
        policy_id: saveAsVersion && existingPolicyId ? existingPolicyId : null,
        canonical_policy: canonicalPolicy,
        save_as_version: saveAsVersion,
        change_description: changeDescription || 'Imported from external system',
      }

      const response = await apiClient.reviewAndSavePolicyImport(reviewData)

      setSavedPolicyId(response.data.policy_id)
      setSavedVersionId(response.data.version_id || null)
      setActiveStep(2) // Move to completion step
    } catch (err: any) {
      setError(err.message || 'Failed to save imported policy')
    } finally {
      setLoading(false)
    }
  }

  const handleNext = () => {
    if (activeStep === 0) {
      handleUpload()
    } else if (activeStep === 1) {
      handleSave()
    } else {
      navigate('/policies')
    }
  }

  const handleBack = () => {
    if (activeStep > 0) {
      setActiveStep(activeStep - 1)
    } else {
      navigate('/policies')
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'success'
    if (confidence >= 0.5) return 'warning'
    return 'error'
  }

  return (
    <Box p={3}>
      <Box sx={{ mb: 3 }}>
        <Typography
          variant="h4"
          component="h1"
          sx={{
            fontFamily: 'IBM Plex Sans, Inter, sans-serif',
            fontWeight: 600,
            mb: 1,
            color: '#0F172A',
          }}
        >
          Policy Import
        </Typography>
        <Typography
          variant="body1"
          sx={{
            color: '#64748B',
            lineHeight: 1.6,
            mb: 2,
          }}
        >
          Import policies from external systems. Upload policy files, review mappings, and save to catalog.
        </Typography>
      </Box>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 3 }}>
        <Button
          variant="outlined"
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/policies')}
        >
          Back to Policies
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Stepper */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Stepper activeStep={activeStep}>
          {STEPS.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>
      </Paper>

      {/* Step 1: Upload */}
      {activeStep === 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Upload Policy Package
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Upload a policy package from an external system (Epic UM, HealthRules, etc.)
            </Typography>

            <Box sx={{ mt: 3, display: 'flex', flexDirection: 'column', gap: 2 }}>
              <FormControl fullWidth>
                <InputLabel>Source System</InputLabel>
                <Select
                  value={sourceSystem}
                  onChange={(e) => setSourceSystem(e.target.value)}
                  label="Source System"
                >
                  <MenuItem value="Epic UM">Epic UM</MenuItem>
                  <MenuItem value="HealthRules">HealthRules</MenuItem>
                  <MenuItem value="Midas+">Midas+</MenuItem>
                  <MenuItem value="Internal">Internal</MenuItem>
                  <MenuItem value="Other">Other</MenuItem>
                </Select>
              </FormControl>

              <FormControl fullWidth>
                <InputLabel>Source Format</InputLabel>
                <Select
                  value={sourceFormat}
                  onChange={(e) => setSourceFormat(e.target.value)}
                  label="Source Format"
                >
                  <MenuItem value="JSON">JSON</MenuItem>
                  <MenuItem value="CSV" disabled>CSV (Coming Soon)</MenuItem>
                  <MenuItem value="EXCEL" disabled>Excel (Coming Soon)</MenuItem>
                </Select>
              </FormControl>

              <Box>
                <Button
                  variant="outlined"
                  component="label"
                  startIcon={<UploadIcon />}
                  fullWidth
                  sx={{ mb: 1 }}
                >
                  {file ? file.name : 'Select Policy Package File'}
                  <input
                    type="file"
                    hidden
                    accept=".json"
                    onChange={handleFileChange}
                  />
                </Button>
                {file && (
                  <Typography variant="caption" color="text.secondary">
                    Selected: {file.name} ({(file.size / 1024).toFixed(2)} KB)
                  </Typography>
                )}
              </Box>

              <Box display="flex" gap={2} justifyContent="flex-end" mt={3}>
                <Button onClick={handleBack}>Cancel</Button>
                <Button
                  variant="contained"
                  onClick={handleNext}
                  disabled={!file || !sourceSystem || loading}
                  startIcon={loading ? <CircularProgress size={20} /> : <ArrowForwardIcon />}
                >
                  Upload & Map
                </Button>
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Step 2: Review */}
      {activeStep === 1 && mappingResult && canonicalPolicy && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Review Policy Mapping
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Review the mapped policy structure. You can edit fields before saving.
            </Typography>

            {/* Mapping Confidence */}
            <Alert
              severity={getConfidenceColor(mappingResult.mapping_confidence) as any}
              sx={{ mb: 3 }}
            >
              <Typography variant="body2">
                Mapping Confidence: {(mappingResult.mapping_confidence * 100).toFixed(0)}%
              </Typography>
              {mappingResult.unmapped_fields.length > 0 && (
                <Typography variant="caption" component="div" sx={{ mt: 1 }}>
                  Unmapped Fields: {mappingResult.unmapped_fields.join(', ')}
                </Typography>
              )}
            </Alert>

            {/* Warnings */}
            {mappingResult.mapping_warnings.length > 0 && (
              <Alert severity="warning" sx={{ mb: 3 }}>
                <Typography variant="body2" fontWeight="bold">Warnings:</Typography>
                <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
                  {mappingResult.mapping_warnings.map((warning, idx) => (
                    <li key={idx}>{warning}</li>
                  ))}
                </ul>
              </Alert>
            )}

            {/* Policy Details */}
            <Box sx={{ mt: 3 }}>
              <Typography variant="subtitle1" gutterBottom fontWeight="bold">
                Mapped Policy Details
              </Typography>

              <TableContainer component={Paper} variant="outlined" sx={{ mt: 2 }}>
                <Table size="small">
                  <TableBody>
                    <TableRow>
                      <TableCell><strong>Policy Name</strong></TableCell>
                      <TableCell>
                        <TextField
                          fullWidth
                          size="small"
                          value={canonicalPolicy.policy_name || ''}
                          onChange={(e) =>
                            setCanonicalPolicy({ ...canonicalPolicy, policy_name: e.target.value })
                          }
                        />
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell><strong>Policy Type</strong></TableCell>
                      <TableCell>
                        <FormControl fullWidth size="small">
                          <Select
                            value={canonicalPolicy.policy_type || 'PRIOR_AUTH'}
                            onChange={(e) =>
                              setCanonicalPolicy({ ...canonicalPolicy, policy_type: e.target.value })
                            }
                          >
                            <MenuItem value="PRIOR_AUTH">Prior Authorization</MenuItem>
                            <MenuItem value="SITE_OF_CARE">Site of Care</MenuItem>
                            <MenuItem value="DURATION_FREQUENCY_LIMIT">Duration/Frequency Limit</MenuItem>
                            <MenuItem value="COST_SHARING">Cost Sharing</MenuItem>
                            <MenuItem value="NETWORK_RESTRICTION">Network Restriction</MenuItem>
                            <MenuItem value="REFERRAL_REQUIREMENT">Referral Requirement</MenuItem>
                            <MenuItem value="COMPOSITE">Composite</MenuItem>
                          </Select>
                        </FormControl>
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell><strong>Description</strong></TableCell>
                      <TableCell>
                        <TextField
                          fullWidth
                          multiline
                          rows={2}
                          size="small"
                          value={canonicalPolicy.description || ''}
                          onChange={(e) =>
                            setCanonicalPolicy({ ...canonicalPolicy, description: e.target.value })
                          }
                        />
                      </TableCell>
                    </TableRow>
                    {canonicalPolicy.scope && (
                      <TableRow>
                        <TableCell><strong>Scope</strong></TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            LOB: {canonicalPolicy.scope.lob || 'All'}
                            <br />
                            Markets: {canonicalPolicy.scope.markets?.join(', ') || 'All'}
                            <br />
                            Network: {canonicalPolicy.scope.network?.join(', ') || 'All'}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    )}
                    {canonicalPolicy.effective_period && (
                      <TableRow>
                        <TableCell><strong>Effective Period</strong></TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            Start: {canonicalPolicy.effective_period.start_date || 'Not set'}
                            <br />
                            End: {canonicalPolicy.effective_period.end_date || 'Ongoing'}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    )}
                    {canonicalPolicy.policy_levers && canonicalPolicy.policy_levers.length > 0 && (
                      <TableRow>
                        <TableCell><strong>Policy Levers</strong></TableCell>
                        <TableCell>
                          {canonicalPolicy.policy_levers.map((lever: any, idx: number) => (
                            <Chip
                              key={idx}
                              label={lever.lever_type || 'Unknown'}
                              size="small"
                              sx={{ mr: 1, mb: 1 }}
                            />
                          ))}
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>

              {/* Save Options */}
              <Box sx={{ mt: 3 }}>
                <Typography variant="subtitle1" gutterBottom fontWeight="bold">
                  Save Options
                </Typography>
                <FormControl fullWidth sx={{ mt: 2 }}>
                  <Select
                    value={saveAsVersion ? 'version' : 'new'}
                    onChange={(e) => setSaveAsVersion(e.target.value === 'version')}
                  >
                    <MenuItem value="new">Save as New Policy</MenuItem>
                    <MenuItem value="version">Save as New Version of Existing Policy</MenuItem>
                  </Select>
                </FormControl>

                {saveAsVersion && (
                  <TextField
                    fullWidth
                    label="Existing Policy ID"
                    value={existingPolicyId || ''}
                    onChange={(e) => setExistingPolicyId(e.target.value)}
                    sx={{ mt: 2 }}
                    helperText="Enter the ID of the existing policy to create a new version"
                  />
                )}

                <TextField
                  fullWidth
                  label="Change Description"
                  multiline
                  rows={2}
                  value={changeDescription}
                  onChange={(e) => setChangeDescription(e.target.value)}
                  sx={{ mt: 2 }}
                  helperText="Describe the changes made in this import"
                  placeholder="Imported from external system"
                />
              </Box>

              <Box display="flex" gap={2} justifyContent="flex-end" mt={3}>
                <Button onClick={handleBack} startIcon={<ArrowBackIcon />}>
                  Back
                </Button>
                <Button
                  variant="contained"
                  onClick={handleNext}
                  disabled={loading}
                  startIcon={loading ? <CircularProgress size={20} /> : <SaveIcon />}
                >
                  Save Policy
                </Button>
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Step 3: Completion */}
      {activeStep === 2 && (
        <Card>
          <CardContent>
            <Box textAlign="center" py={4}>
              <CheckIcon color="success" sx={{ fontSize: 64, mb: 2 }} />
              <Typography variant="h5" gutterBottom>
                Policy Imported Successfully!
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                The policy has been imported and saved.
              </Typography>

              <Box sx={{ mt: 3 }}>
                <Typography variant="body2">
                  <strong>Policy ID:</strong> {savedPolicyId}
                </Typography>
                {savedVersionId && (
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    <strong>Version ID:</strong> {savedVersionId}
                  </Typography>
                )}
              </Box>

              <Box display="flex" gap={2} justifyContent="center" mt={4}>
                <Button
                  variant="outlined"
                  onClick={() => navigate(`/policies/builder/${savedPolicyId}`)}
                >
                  View Policy
                </Button>
                <Button
                  variant="contained"
                  onClick={() => navigate('/policies')}
                >
                  Back to Policies
                </Button>
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  )
}

