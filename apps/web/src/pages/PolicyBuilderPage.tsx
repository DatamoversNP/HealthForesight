/**
 * Policy Builder Page - Comprehensive Policy Configuration Wizard
 * Supports metadata + complex policy logic (scope, levers, conditions, exceptions)
 */
import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  Box,
  Button,
  Stepper,
  Step,
  StepLabel,
  Paper,
  Typography,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  TextField,
} from '@mui/material'
import {
  ArrowBack as ArrowBackIcon,
  ArrowForward as ArrowForwardIcon,
  Check as CheckIcon,
} from '@mui/icons-material'
import { apiClient } from '../lib/api'
import ScopeSelectorEnhanced from '../components/policy/ScopeSelectorEnhanced'
import LeverList from '../components/policy/LeverList'
import RuleGroupBuilder from '../components/policy/RuleGroupBuilder'
import ExceptionsBuilder from '../components/policy/ExceptionsBuilder'
import PolicyPreview from '../components/policy/PolicyPreview'
import { POLICY_TEMPLATES } from '../lib/policyTemplates'
import TourButton from '../components/tour/TourButton'

const STEPS = [
  'Basic Info',
  'Scope',
  'Levers',
  'Conditions',
  'Exceptions',
  'Review & Save',
]

interface PolicyBuilderState {
  // Step 1: Basic Info
  name: string
  policy_type: string
  description: string
  owner_role: string
  status: string
  
  // Step 2: Scope (comprehensive)
  scope: {
    lob: string[]
    markets: string[]
    network: string[]
    plans?: string[]
    product_types?: string[]
    states?: string[]
    regions?: string[]
    network_tiers?: string[]
    member_age_min?: number | null
    member_age_max?: number | null
    exclude_pregnant?: boolean | null
    gender_filters?: string[]
    exclude_centers_of_excellence?: boolean | null
    include_provider_types?: string[]
    exclude_provider_types?: string[]
    provider_specialties?: string[]
    exclude_er?: boolean | null
    exclude_hospital_op?: boolean | null
    allowed_sites?: string[]
    applies_to_all?: boolean
    network_inclusion_mode?: 'include' | 'exclude'
  }
  effective_period: {
    start_date: string
    end_date: string | null
  }
  
  // Step 3: Levers
  levers: any[] // PolicyLeverLogic[]
  
  // Step 4: Conditions
  apply_when: any[] // RuleGroup[]
  
  // Step 5: Exceptions
  global_exceptions: any[] // Exception[]
  
  // Template selection
  template: string | null
}

const initialState: PolicyBuilderState = {
  name: '',
  policy_type: 'PRIOR_AUTH',
  description: '',
  owner_role: '',
  status: 'DRAFT',
  scope: {
    lob: [],
    markets: [],
    network: [],
    plans: [],
    product_types: [],
    states: [],
    regions: [],
    network_tiers: [],
    member_age_min: null,
    member_age_max: null,
    exclude_pregnant: null,
    gender_filters: [],
    exclude_centers_of_excellence: null,
    include_provider_types: [],
    exclude_provider_types: [],
    provider_specialties: [],
    exclude_er: null,
    exclude_hospital_op: null,
    allowed_sites: [],
    applies_to_all: false,
    network_inclusion_mode: 'include',
  },
  effective_period: {
    start_date: new Date().toISOString().split('T')[0],
    end_date: null,
  },
  levers: [],
  apply_when: [],
  global_exceptions: [],
  template: null,
}

export default function PolicyBuilderPage() {
  const navigate = useNavigate()
  const { id } = useParams<{ id?: string }>()
  const [activeStep, setActiveStep] = useState(0)
  const [state, setState] = useState<PolicyBuilderState>(initialState)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [templateDialogOpen, setTemplateDialogOpen] = useState(false)
  const [isEditing, setIsEditing] = useState(false)

  // Load policy data if editing
  useEffect(() => {
    if (id) {
      setIsEditing(true)
      setLoading(true)
      apiClient.getPolicy(id)
        .then((policy) => {
          // Map policy data to form state
          // API returns data in logic.scope, logic.levers, etc.
          const logic = policy.logic || {}
          const metadata = policy.metadata || {}
          
          setState({
            name: policy.name || logic.policy_name || '',
            // Normalize policy_type - convert display names to enum values
            policy_type: (() => {
              const type = policy.policy_type || 'PRIOR_AUTH';
              // Convert spaces to underscores for enum values
              return type.replace(/\s+/g, '_').toUpperCase();
            })(),
            description: policy.description || logic.policy_description || '',
            // Map owner role - convert display names to enum values
            owner_role: (() => {
              const owner = metadata.owner || logic.policy_owner || policy.owner_role || '';
              // Map display names to enum values
              if (owner === 'UM + Strategy' || owner === 'UM + Strategy') return 'STRATEGY';
              if (owner === 'Policy Admin') return 'POLICY_ADMIN';
              if (owner === 'UM Leader') return 'UM_LEADER';
              if (owner === 'Actuarial') return 'ACTUARIAL';
              if (owner === 'Compliance') return 'COMPLIANCE';
              return owner || '';
            })(),
            status: policy.status || 'DRAFT',
            scope: {
              lob: logic.scope?.lob || policy.scope?.lob || logic.scope?.line_of_business || [],
              markets: logic.scope?.markets || policy.scope?.markets || [],
              network: policy.scope?.network || logic.scope?.network || (logic.scope?.network_tier ? [logic.scope.network_tier] : []),
              plans: policy.scope?.plans || logic.scope?.plans || [],
              product_types: policy.scope?.product_types || logic.scope?.product_types || [],
              states: policy.scope?.states || logic.scope?.states || [],
              regions: policy.scope?.regions || logic.scope?.regions || [],
              network_tiers: policy.scope?.network_tiers || logic.scope?.network_tiers || [],
              member_age_min: policy.scope?.member_age_min || logic.scope?.member_age_min || null,
              member_age_max: policy.scope?.member_age_max || logic.scope?.member_age_max || null,
              exclude_pregnant: policy.scope?.exclude_pregnant || logic.scope?.exclude_pregnant || null,
              gender_filters: policy.scope?.gender_filters || logic.scope?.gender_filters || [],
              exclude_centers_of_excellence: policy.scope?.exclude_centers_of_excellence || logic.scope?.exclude_centers_of_excellence || null,
              include_provider_types: policy.scope?.include_provider_types || logic.scope?.include_provider_types || [],
              exclude_provider_types: policy.scope?.exclude_provider_types || logic.scope?.exclude_provider_types || [],
              provider_specialties: policy.scope?.provider_specialties || logic.scope?.provider_specialties || [],
              exclude_er: policy.scope?.exclude_er || logic.scope?.exclude_er || null,
              exclude_hospital_op: policy.scope?.exclude_hospital_op || logic.scope?.exclude_hospital_op || null,
              allowed_sites: policy.scope?.allowed_sites || logic.scope?.allowed_sites || [],
              applies_to_all: policy.scope?.applies_to_all || logic.scope?.applies_to_all || false,
              network_inclusion_mode: policy.scope?.network_inclusion_mode || logic.scope?.network_inclusion_mode || 'include', // 'include' or 'exclude'
            },
            effective_period: {
              start_date: logic.effective_start || policy.effective_date || policy.effective_period?.start_date || 
                         (policy.effective_period && typeof policy.effective_period === 'object' && 'start_date' in policy.effective_period 
                          ? policy.effective_period.start_date 
                          : new Date().toISOString().split('T')[0]),
              end_date: logic.effective_end || policy.expiration_date || policy.effective_period?.end_date || null,
            },
            levers: (() => {
              // Try multiple locations for levers
              const levers = 
                logic.levers || 
                logic.policy_levers || 
                policy.policy_levers || 
                policy.levers || 
                (policy.logic && policy.logic.levers) ||
                (policy.logic && policy.logic.policy_levers) ||
                (policy.metadata && policy.metadata.levers) ||
                []
              
              // If no levers found but policy has lever_count in metadata, create empty levers
              if (levers.length === 0 && policy.metadata?.lever_count) {
                // Return empty array - user will need to add levers
                return []
              }
              
              return levers
            })(),
            // Map conditions/criteria - ensure it's always an array and properly formatted
            apply_when: (() => {
              const conditions = logic.global_conditions || policy.policy_logic?.apply_when || policy.apply_when
              if (!conditions) return []
              // Ensure it's an array
              if (!Array.isArray(conditions)) return []
              // Ensure each item has the correct structure for RuleGroupBuilder
              return conditions.map((item: any) => {
                // If it's already a rule group with conditions array, return as-is
                if (item.conditions && Array.isArray(item.conditions)) {
                  return {
                    conditions: item.conditions,
                    operator: item.operator || 'AND',
                  }
                }
                // If it's a flat condition object, wrap it in a rule group
                if (item.field || item.operator || item.value !== undefined) {
                  return {
                    conditions: [item],
                    operator: 'AND',
                  }
                }
                // Default: empty rule group
                return {
                  conditions: [],
                  operator: 'AND',
                }
              })
            })(),
            global_exceptions: logic.global_exceptions || policy.policy_logic?.exceptions || policy.global_exceptions || [],
            template: null,
          })
          setError(null)
        })
        .catch((err: any) => {
          setError(err.detail || err.message || 'Failed to load policy')
          console.error('Error loading policy:', err)
        })
        .finally(() => {
          setLoading(false)
        })
    }
  }, [id])

  const handleNext = () => {
    // Validate current step
    if (activeStep === 0) {
      if (!state.name || !state.policy_type) {
        setError('Policy name and type are required')
        return
      }
    } else if (activeStep === 1) {
      // Scope validation - at minimum need LOB and effective date
      // Markets and network can be empty (defaults to "all")
      if (!state.scope.lob.length || !state.effective_period.start_date) {
        setError('Scope (LOB, markets, effective date) is required')
        return
      }
    } else if (activeStep === 2) {
      if (!state.levers.length) {
        setError('At least one lever is required')
        return
      }
    }
    
    setError(null)
    if (activeStep < STEPS.length - 1) {
      setActiveStep(activeStep + 1)
    }
  }

  const handleBack = () => {
    setError(null)
    if (activeStep > 0) {
      setActiveStep(activeStep - 1)
    }
  }
  
  // Clear error when step changes
  useEffect(() => {
    setError(null)
  }, [activeStep])

  const handleApplyTemplate = (templateId: string) => {
    const template = POLICY_TEMPLATES.find((t) => t.id === templateId)
    if (template) {
      setState({
        ...state,
        ...template.data,
        template: templateId,
      })
      setTemplateDialogOpen(false)
      setError(null)
    }
  }

  const handleSave = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Build PolicyLogic JSON with comprehensive scope
      const policyLogic = {
        scope: {
          lob: state.scope.lob,
          markets: state.scope.markets,
          network: state.scope.network,
          plans: state.scope.plans,
          product_types: state.scope.product_types,
          states: state.scope.states,
          regions: state.scope.regions,
          network_tiers: state.scope.network_tiers,
          member_age_min: state.scope.member_age_min,
          member_age_max: state.scope.member_age_max,
          exclude_pregnant: state.scope.exclude_pregnant,
          gender_filters: state.scope.gender_filters,
          exclude_centers_of_excellence: state.scope.exclude_centers_of_excellence,
          include_provider_types: state.scope.include_provider_types,
          exclude_provider_types: state.scope.exclude_provider_types,
          provider_specialties: state.scope.provider_specialties,
          exclude_er: state.scope.exclude_er,
          exclude_hospital_op: state.scope.exclude_hospital_op,
          allowed_sites: state.scope.allowed_sites,
          applies_to_all: state.scope.applies_to_all,
          network_inclusion_mode: state.scope.network_inclusion_mode,
        },
        effective_period: {
          start_date: state.effective_period.start_date,
          end_date: state.effective_period.end_date || null,
        },
        levers: state.levers.map((lever, idx) => ({
          ...lever,
          apply_when: state.apply_when.filter((rg) => rg.lever_index === idx),
          priority: idx + 1,
        })),
        global_exceptions: state.global_exceptions,
        version: 1,
      }
      
      // Create policy via API
      const policyData = {
        name: state.name,
        policy_type: state.policy_type,
        description: state.description,
        owner_role: state.owner_role,
        status: state.status,
        scope: policyLogic.scope,
        effective_period: policyLogic.effective_period,
        enforcement: {
          mechanism: 'HARD',
          touchpoint: ['CLAIM_EDIT'],
          override_allowed: false,
        },
        policy_levers: state.levers.map((l) => ({
          lever_type: l.lever_type,
          parameters: l.config || {},
        })),
        policy_logic: policyLogic,
      }
      
      let savedPolicyId: string
      
      if (isEditing && id) {
        // Update existing policy
        const updated = await apiClient.updatePolicy(id, policyData)
        savedPolicyId = id
      } else {
        // Create new policy
        const created = await apiClient.createPolicy(policyData)
        savedPolicyId = created.id || created.policy_id || id || ''
      }
      
      // Create initial version and changelog entry (Epic 2)
      if (savedPolicyId) {
        try {
          const userId = '00000000-0000-0000-0000-000000000001' // Demo user - would come from auth context
          
          // Create version
          await apiClient.createPolicyVersion(savedPolicyId, {
            effective_start_date: state.effective_period.start_date,
            effective_end_date: state.effective_period.end_date || null,
            state: state.status || 'DRAFT',
            change_summary: isEditing ? 'Policy updated' : 'Policy created',
            change_details: {
              name: state.name,
              policy_type: state.policy_type,
              levers_count: state.levers.length,
            },
            created_by: userId,
          })
        } catch (err) {
          // Don't fail policy save if versioning fails
          console.warn('Failed to create policy version:', err)
        }
      }
      
      // Navigate to policy catalog
      navigate('/policies')
    } catch (err: any) {
      console.error('Error saving policy:', err)
      setError(err.detail || err.message || 'Failed to save policy')
    } finally {
      setLoading(false)
    }
  }

  const renderStepContent = () => {
    switch (activeStep) {
      case 0: // Basic Info
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <Button
              variant="outlined"
              onClick={() => setTemplateDialogOpen(true)}
              sx={{ alignSelf: 'flex-start' }}
            >
              Load Template
            </Button>
            
            <TextField
              fullWidth
              label="Policy Name"
              value={state.name}
              onChange={(e) => setState({ ...state, name: e.target.value })}
              placeholder="e.g., Outpatient MRI Prior Authorization"
              required
            />
            
            <FormControl fullWidth>
              <InputLabel>Policy Type</InputLabel>
              <Select
                value={state.policy_type}
                onChange={(e) => setState({ ...state, policy_type: e.target.value })}
                label="Policy Type"
              >
                <MenuItem value="PRIOR_AUTH">Prior Authorization</MenuItem>
                <MenuItem value="SITE_OF_CARE">Site of Care</MenuItem>
                <MenuItem value="DURATION_FREQUENCY_LIMIT">Frequency Limit</MenuItem>
                <MenuItem value="QUANTITY_LIMIT">Quantity Limit</MenuItem>
                <MenuItem value="COST_SHARING">Cost Sharing</MenuItem>
                <MenuItem value="NETWORK_RESTRICTION">Network Restriction</MenuItem>
                <MenuItem value="REFERRAL_REQUIREMENT">Referral Requirement</MenuItem>
                <MenuItem value="CLINICAL_CRITERIA">Clinical Criteria</MenuItem>
                <MenuItem value="COMPOSITE">Composite (Multiple Levers)</MenuItem>
              </Select>
            </FormControl>
            
            <TextField
              fullWidth
              label="Description"
              value={state.description}
              onChange={(e) => setState({ ...state, description: e.target.value })}
              placeholder="Describe the policy's purpose and expected impact..."
              multiline
              rows={4}
            />
            
            <FormControl fullWidth>
              <InputLabel>Owner Role</InputLabel>
              <Select
                value={state.owner_role}
                onChange={(e) => setState({ ...state, owner_role: e.target.value })}
                label="Owner Role"
              >
                <MenuItem value="POLICY_ADMIN">Policy Admin</MenuItem>
                <MenuItem value="UM_LEADER">UM Leader</MenuItem>
                <MenuItem value="ACTUARIAL">Actuarial</MenuItem>
                <MenuItem value="STRATEGY">Strategy</MenuItem>
                <MenuItem value="COMPLIANCE">Compliance</MenuItem>
              </Select>
            </FormControl>
          </Box>
        )
      
      case 1: // Scope
        return (
          <Box className="scope-selector">
            <ScopeSelectorEnhanced
              scope={state.scope}
              effective_period={state.effective_period}
              onChange={(updates) => setState({ ...state, ...updates })}
            />
          </Box>
        )
      
      case 2: // Levers
        return (
          <Box className="levers-config">
            <LeverList
              levers={state.levers}
              policy_type={state.policy_type}
              onChange={(levers) => setState({ ...state, levers })}
            />
          </Box>
        )
      
      case 3: // Conditions
        return (
          <RuleGroupBuilder
            ruleGroups={state.apply_when}
            levers={state.levers}
            onChange={(apply_when) => setState({ ...state, apply_when })}
          />
        )
      
      case 4: // Exceptions
        return (
          <ExceptionsBuilder
            exceptions={state.global_exceptions}
            onChange={(global_exceptions) => setState({ ...state, global_exceptions })}
          />
        )
      
      case 5: // Review & Save
        return (
          <PolicyPreview
            policy={{
              ...state,
              policy_logic: {
                scope: state.scope,
                effective_period: state.effective_period,
                levers: state.levers,
                global_exceptions: state.global_exceptions,
              },
            }}
          />
        )
      
      default:
        return null
    }
  }

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      <Box 
        className="policy-builder-header"
        sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}
      >
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <Typography
              variant="h4"
              component="h1"
              sx={{
                fontFamily: 'IBM Plex Sans, Inter, sans-serif',
                fontWeight: 600,
                color: '#0F172A',
              }}
            >
              Policy Builder
            </Typography>
            <TourButton module="policy-builder" size="small" />
          </Box>
          <Typography
            variant="body1"
            sx={{
              color: '#64748B',
              lineHeight: 1.6,
              mb: 2,
            }}
          >
            Configure policy metadata and logic for analytics. Create structured policies with scope, levers, conditions, and exceptions.
          </Typography>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 3, mb: 3 }}>
        <Stepper className="builder-steps" activeStep={activeStep}>
          {STEPS.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>
      </Paper>

      <Paper sx={{ p: 4, minHeight: 400 }}>
        {renderStepContent()}
      </Paper>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={handleBack}
          disabled={activeStep === 0}
        >
          Back
        </Button>
        {activeStep === STEPS.length - 1 ? (
          <Button
            variant="contained"
            startIcon={<CheckIcon />}
            onClick={handleSave}
            disabled={loading}
          >
            {loading ? 'Saving...' : 'Save Policy'}
          </Button>
        ) : (
          <Button
            variant="contained"
            endIcon={<ArrowForwardIcon />}
            onClick={handleNext}
          >
            Next
          </Button>
        )}
      </Box>

      {/* Template Selection Dialog */}
      <Dialog open={templateDialogOpen} onClose={() => setTemplateDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Load Policy Template</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
            {POLICY_TEMPLATES.map((template) => (
              <Paper
                key={template.id}
                sx={{ p: 2, cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' } }}
                onClick={() => handleApplyTemplate(template.id)}
              >
                <Typography variant="h6">{template.name}</Typography>
                <Typography variant="body2" color="text.secondary">
                  {template.description}
                </Typography>
              </Paper>
            ))}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTemplateDialogOpen(false)}>Cancel</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

