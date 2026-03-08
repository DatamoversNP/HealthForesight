/**
 * Rule Group Builder Component - Step 4 of Policy Builder
 * Enhanced with validation, more field types, visual builder, and better editing
 */
import { useState } from 'react'
import {
  Box,
  Button,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  IconButton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Alert,
  Chip,
  Card,
  CardContent,
  Grid,
  Divider,
  Tooltip,
  Autocomplete,
} from '@mui/material'
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Check as CheckIcon,
  Close as CloseIcon,
  Info as InfoIcon,
} from '@mui/icons-material'

interface RuleGroupBuilderProps {
  ruleGroups: any[]
  levers: any[]
  onChange: (ruleGroups: any[]) => void
}

interface Condition {
  field: string
  operator: string
  value: string | string[]
  id?: string
}

interface RuleGroup {
  conditions: Condition[]
  operator: 'AND' | 'OR'
}

const OPERATORS = [
  { value: 'IN', label: 'In', types: ['string', 'list'] },
  { value: 'NOT_IN', label: 'Not In', types: ['string', 'list'] },
  { value: 'EQUALS', label: 'Equals', types: ['string', 'number'] },
  { value: 'NOT_EQUALS', label: 'Not Equals', types: ['string', 'number'] },
  { value: 'GREATER_THAN', label: 'Greater Than', types: ['number', 'date'] },
  { value: 'LESS_THAN', label: 'Less Than', types: ['number', 'date'] },
  { value: 'GREATER_THAN_OR_EQUAL', label: 'Greater Than or Equal', types: ['number', 'date'] },
  { value: 'LESS_THAN_OR_EQUAL', label: 'Less Than or Equal', types: ['number', 'date'] },
  { value: 'CONTAINS', label: 'Contains', types: ['string'] },
  { value: 'NOT_CONTAINS', label: 'Not Contains', types: ['string'] },
  { value: 'STARTS_WITH', label: 'Starts With', types: ['string'] },
  { value: 'ENDS_WITH', label: 'Ends With', types: ['string'] },
  { value: 'BETWEEN', label: 'Between', types: ['number', 'date'] },
  { value: 'IS_NULL', label: 'Is Null', types: ['all'] },
  { value: 'IS_NOT_NULL', label: 'Is Not Null', types: ['all'] },
]

const FIELD_TYPES = {
  place_of_service: { type: 'list', label: 'Place of Service', options: ['11', '12', '19', '20', '22', '23', '24', '31', '32', '33', '34', '41', '42', '49', '50', '51', '52', '53', '54', '55', '56', '57', '58', '59', '60', '61', '62', '71', '72', '81', '82', '83', '99'] },
  age: { type: 'number', label: 'Age', min: 0, max: 120 },
  diagnosis: { type: 'string', label: 'Diagnosis Code (ICD-10)', pattern: /^[A-Z][0-9]{2}(\.[0-9]{1,4})?$/ },
  service_category: { type: 'list', label: 'Service Category', options: ['MRI', 'CT', 'X-RAY', 'ULTRASOUND', 'LAB', 'SPECIALTY_VISIT', 'PRIMARY_CARE', 'URGENT_CARE', 'EMERGENCY', 'INFUSION', 'PT', 'OT', 'ST', 'HOME_HEALTH', 'HOSPICE', 'DME', 'PHARMACY'] },
  provider_type: { type: 'list', label: 'Provider Type', options: ['PHYSICIAN', 'NURSE_PRACTITIONER', 'PHYSICIAN_ASSISTANT', 'FACILITY', 'LAB', 'IMAGING', 'PHARMACY', 'DME', 'HOME_HEALTH', 'HOSPICE'] },
  network_status: { type: 'list', label: 'Network Status', options: ['IN_NETWORK', 'OUT_OF_NETWORK', 'PREFERRED', 'TIER_1', 'TIER_2', 'TIER_3'] },
  cpt_code: { type: 'string', label: 'CPT/HCPCS Code', pattern: /^[0-9]{5}$|^[A-Z][0-9]{4}$/ },
  revenue_code: { type: 'string', label: 'Revenue Code', pattern: /^[0-9]{3,4}$/ },
  gender: { type: 'list', label: 'Gender', options: ['M', 'F', 'U'] },
  line_of_business: { type: 'list', label: 'Line of Business', options: ['COMMERCIAL', 'MA', 'MEDICAID', 'SELF_INSURED'] },
  market: { type: 'string', label: 'Market' },
  member_risk_score: { type: 'number', label: 'Member Risk Score', min: 0, max: 10, step: 0.1 },
  claim_amount: { type: 'number', label: 'Claim Amount', min: 0 },
  units: { type: 'number', label: 'Units', min: 0 },
  date_of_service: { type: 'date', label: 'Date of Service' },
  provider_specialty: { type: 'string', label: 'Provider Specialty' },
  facility_type: { type: 'list', label: 'Facility Type', options: ['HOSPITAL', 'PHYSICIAN_OFFICE', 'URGENT_CARE', 'AMBULATORY_SURGERY', 'LAB', 'IMAGING_CENTER', 'HOME', 'SKILLED_NURSING', 'REHAB'] },
}

const FIELDS = Object.entries(FIELD_TYPES).map(([value, config]) => ({
  value,
  label: config.label,
  type: config.type,
}))

export default function RuleGroupBuilder({ ruleGroups, onChange }: RuleGroupBuilderProps) {
  const [newCondition, setNewCondition] = useState<Condition>({
    field: 'place_of_service',
    operator: 'IN',
    value: '',
  })
  const [editingCondition, setEditingCondition] = useState<{ groupId: number; conditionId: number } | null>(null)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [editingValue, setEditingValue] = useState<string>('')

  const getFieldConfig = (fieldName: string) => {
    return FIELD_TYPES[fieldName as keyof typeof FIELD_TYPES] || FIELD_TYPES.place_of_service
  }

  const getOperatorsForField = (fieldName: string) => {
    const fieldConfig = getFieldConfig(fieldName)
    const fieldType = fieldConfig.type === 'list' ? 'list' : fieldConfig.type === 'number' ? 'number' : fieldConfig.type === 'date' ? 'date' : 'string'
    
    return OPERATORS.filter(op => 
      op.types.includes('all') || op.types.includes(fieldType) || (fieldType === 'list' && op.types.includes('string'))
    )
  }

  const validateCondition = (condition: Condition): string | null => {
    if (!condition.field) {
      return 'Field is required'
    }

    const fieldConfig = getFieldConfig(condition.field)
    const operators = getOperatorsForField(condition.field)

    if (!operators.find(op => op.value === condition.operator)) {
      return `Operator "${condition.operator}" is not valid for field type "${fieldConfig.type}"`
    }

    // Skip value validation for NULL/NOT_NULL operators
    if (condition.operator === 'IS_NULL' || condition.operator === 'IS_NOT_NULL') {
      return null
    }

    if (!condition.value || (Array.isArray(condition.value) && condition.value.length === 0)) {
      return 'Value is required'
    }

    // Type-specific validation
    if (fieldConfig.type === 'number') {
      const numValue = Array.isArray(condition.value) 
        ? condition.value.map(v => parseFloat(String(v))).find(v => isNaN(v))
        : parseFloat(String(condition.value))
      
      if (numValue !== undefined && isNaN(numValue)) {
        return 'Value must be a number'
      }

      if (fieldConfig.min !== undefined && numValue < fieldConfig.min) {
        return `Value must be at least ${fieldConfig.min}`
      }

      if (fieldConfig.max !== undefined && numValue > fieldConfig.max) {
        return `Value must be at most ${fieldConfig.max}`
      }
    }

    if (fieldConfig.pattern && typeof condition.value === 'string') {
      if (!fieldConfig.pattern.test(condition.value)) {
        return `Invalid format. Expected pattern: ${fieldConfig.pattern}`
      }
    }

    return null
  }

  const handleFieldChange = (field: string) => {
    const fieldConfig = getFieldConfig(field)
    const operators = getOperatorsForField(field)
    
    // Reset operator if current one is not valid for new field
    const currentOpValid = operators.find(op => op.value === newCondition.operator)
    
    setNewCondition({
      field,
      operator: currentOpValid ? newCondition.operator : operators[0].value,
      value: '',
    })
    setErrors({})
  }

  const handleOperatorChange = (operator: string) => {
    setNewCondition({ ...newCondition, operator, value: '' })
    setErrors({})
  }

  const handleValueChange = (value: string | string[]) => {
    setNewCondition({ ...newCondition, value })
    setErrors({})
  }

  const handleAddCondition = (groupId: number) => {
    const error = validateCondition(newCondition)
    if (error) {
      setErrors({ [`group-${groupId}`]: error })
      return
    }

    const updated = [...ruleGroups]
    if (!updated[groupId]) {
      updated[groupId] = { conditions: [], operator: 'AND' }
    }

    // Process value based on operator
    let processedValue = newCondition.value
    if (newCondition.operator === 'IN' || newCondition.operator === 'NOT_IN') {
      processedValue = typeof newCondition.value === 'string' 
        ? newCondition.value.split(',').map(v => v.trim()).filter(v => v)
        : newCondition.value
    } else if (newCondition.operator === 'BETWEEN') {
      // For BETWEEN, value should be "min,max"
      if (typeof newCondition.value === 'string') {
        const parts = newCondition.value.split(',').map(v => v.trim())
        if (parts.length === 2) {
          processedValue = parts
        }
      }
    }

    updated[groupId].conditions.push({
      ...newCondition,
      value: processedValue,
      id: `cond-${Date.now()}-${Math.random()}`,
    })
    onChange(updated)
    setNewCondition({ field: 'place_of_service', operator: 'IN', value: '' })
    setErrors({})
  }

  const handleEditCondition = (groupId: number, conditionId: number) => {
    const condition = ruleGroups[groupId].conditions[conditionId]
    setEditingCondition({ groupId, conditionId })
    setEditingValue(
      Array.isArray(condition.value) 
        ? condition.value.join(', ')
        : String(condition.value || '')
    )
  }

  const handleSaveEdit = (groupId: number, conditionId: number) => {
    const updated = [...ruleGroups]
    const fieldConfig = getFieldConfig(updated[groupId].conditions[conditionId].field)
    
    let processedValue: string | string[] = editingValue
    const operator = updated[groupId].conditions[conditionId].operator
    
    if (operator === 'IN' || operator === 'NOT_IN') {
      processedValue = editingValue.split(',').map(v => v.trim()).filter(v => v)
    } else if (operator === 'BETWEEN') {
      const parts = editingValue.split(',').map(v => v.trim())
      if (parts.length === 2) {
        processedValue = parts
      }
    } else if (fieldConfig.type === 'number') {
      processedValue = editingValue
    }

    const updatedCondition = {
      ...updated[groupId].conditions[conditionId],
      value: processedValue,
    }

    const error = validateCondition(updatedCondition)
    if (error) {
      setErrors({ [`edit-${groupId}-${conditionId}`]: error })
      return
    }

    updated[groupId].conditions[conditionId] = updatedCondition
    onChange(updated)
    setEditingCondition(null)
    setEditingValue('')
    setErrors({})
  }

  const handleCancelEdit = () => {
    setEditingCondition(null)
    setEditingValue('')
    setErrors({})
  }

  const handleRemoveCondition = (groupId: number, conditionId: number) => {
    const updated = [...ruleGroups]
    updated[groupId].conditions = updated[groupId].conditions.filter((_, idx) => idx !== conditionId)
    onChange(updated)
  }

  const handleRemoveRuleGroup = (groupId: number) => {
    const updated = ruleGroups.filter((_, idx) => idx !== groupId)
    onChange(updated)
  }

  const handleAddRuleGroup = () => {
    onChange([...ruleGroups, { conditions: [], operator: 'AND' }])
  }

  const formatConditionValue = (condition: Condition): string => {
    if (condition.operator === 'IS_NULL' || condition.operator === 'IS_NOT_NULL') {
      return ''
    }

    if (Array.isArray(condition.value)) {
      return condition.value.join(', ')
    }
    return String(condition.value || '')
  }

  const renderValueInput = (condition: Condition, value: string | string[], onChangeValue: (val: string | string[]) => void, error?: string) => {
    const fieldConfig = getFieldConfig(condition.field)
    const operator = OPERATORS.find(op => op.value === condition.operator)

    // NULL operators don't need values
    if (condition.operator === 'IS_NULL' || condition.operator === 'IS_NOT_NULL') {
      return null
    }

    // List fields with IN/NOT_IN operators
    if (fieldConfig.type === 'list' && (condition.operator === 'IN' || condition.operator === 'NOT_IN')) {
      const currentValue = Array.isArray(value) ? value : (typeof value === 'string' ? value.split(',').map(v => v.trim()) : [])
      return (
        <Autocomplete
          multiple
          options={fieldConfig.options || []}
          freeSolo
          value={currentValue}
          onChange={(_, newValue) => onChangeValue(newValue)}
          renderInput={(params) => (
            <TextField
              {...params}
              size="small"
              label="Values"
              error={!!error}
              helperText={error || 'Select or type multiple values'}
              placeholder="Select or type values"
            />
          )}
          sx={{ flex: 1 }}
        />
      )
    }

    // Single-select list fields
    if (fieldConfig.type === 'list') {
      return (
        <FormControl size="small" sx={{ flex: 1 }} error={!!error}>
          <InputLabel>Value</InputLabel>
          <Select
            value={typeof value === 'string' ? value : ''}
            onChange={(e) => onChangeValue(e.target.value)}
            label="Value"
          >
            {fieldConfig.options?.map((opt) => (
              <MenuItem key={opt} value={opt}>
                {opt}
              </MenuItem>
            ))}
          </Select>
          {error && <Typography variant="caption" color="error" sx={{ mt: 0.5, ml: 1.75 }}>{error}</Typography>}
        </FormControl>
      )
    }

    // Number fields
    if (fieldConfig.type === 'number') {
      return (
        <TextField
          size="small"
          type="number"
          label="Value"
          value={typeof value === 'string' ? value : String(value || '')}
          onChange={(e) => onChangeValue(e.target.value)}
          error={!!error}
          helperText={error}
          inputProps={{
            min: fieldConfig.min,
            max: fieldConfig.max,
            step: fieldConfig.step || 1,
          }}
          sx={{ flex: 1 }}
        />
      )
    }

    // Date fields
    if (fieldConfig.type === 'date') {
      return (
        <TextField
          size="small"
          type="date"
          label="Value"
          value={typeof value === 'string' ? value : ''}
          onChange={(e) => onChangeValue(e.target.value)}
          error={!!error}
          helperText={error}
          InputLabelProps={{ shrink: true }}
          sx={{ flex: 1 }}
        />
      )
    }

    // BETWEEN operator needs two values
    if (condition.operator === 'BETWEEN') {
      return (
        <TextField
          size="small"
          label="Range (min, max)"
          value={Array.isArray(value) ? value.join(', ') : (typeof value === 'string' ? value : '')}
          onChange={(e) => onChangeValue(e.target.value)}
          error={!!error}
          helperText={error || 'Enter two values separated by comma (e.g., 10, 100)'}
          placeholder="10, 100"
          sx={{ flex: 1 }}
        />
      )
    }

    // Default text input
    return (
      <TextField
        size="small"
        label="Value"
        value={typeof value === 'string' ? value : (Array.isArray(value) ? value.join(', ') : String(value || ''))}
        onChange={(e) => onChangeValue(e.target.value)}
        error={!!error}
        helperText={error}
        placeholder={condition.operator === 'IN' || condition.operator === 'NOT_IN' ? 'Value1, Value2, ...' : 'Value'}
        sx={{ flex: 1 }}
      />
    )
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box>
          <Typography variant="h6">Apply When Conditions</Typography>
          <Typography variant="body2" color="text.secondary">
            Conditions within a group are combined with AND. Multiple groups are combined with OR.
          </Typography>
        </Box>
        <Button variant="outlined" startIcon={<AddIcon />} onClick={handleAddRuleGroup}>
          Add Rule Group (OR)
        </Button>
      </Box>

      {ruleGroups.length === 0 ? (
        <Card variant="outlined" sx={{ p: 4, textAlign: 'center', bgcolor: 'grey.50' }}>
          <Typography variant="body2" color="text.secondary">
            No condition groups. Policies without conditions apply to all matching services.
          </Typography>
          <Button
            variant="outlined"
            startIcon={<AddIcon />}
            onClick={handleAddRuleGroup}
            sx={{ mt: 2 }}
          >
            Add First Rule Group
          </Button>
        </Card>
      ) : (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {ruleGroups.map((group, groupId) => (
            <Card key={groupId} variant="outlined">
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip label={`Group ${groupId + 1}`} color="primary" size="small" />
                    <Typography variant="subtitle2" color="text.secondary">
                      (All conditions must match - AND)
                    </Typography>
                  </Box>
                  <IconButton
                    size="small"
                    color="error"
                    onClick={() => handleRemoveRuleGroup(groupId)}
                    disabled={ruleGroups.length === 1}
                  >
                    <DeleteIcon />
                  </IconButton>
                </Box>

                {group.conditions && group.conditions.length > 0 ? (
                  <Box sx={{ mb: 2 }}>
                    {group.conditions.map((condition: Condition, conditionId: number) => {
                      const isEditing = editingCondition?.groupId === groupId && editingCondition?.conditionId === conditionId
                      const fieldConfig = getFieldConfig(condition.field)
                      const operatorLabel = OPERATORS.find(op => op.value === condition.operator)?.label || condition.operator

                      return (
                        <Paper
                          key={condition.id || conditionId}
                          variant="outlined"
                          sx={{
                            p: 2,
                            mb: 1,
                            bgcolor: isEditing ? 'action.hover' : 'background.paper',
                            border: isEditing ? 2 : 1,
                            borderColor: isEditing ? 'primary.main' : 'divider',
                          }}
                        >
                          {isEditing ? (
                            <Grid container spacing={2} alignItems="flex-start">
                              <Grid item xs={12} sm={3}>
                                <FormControl fullWidth size="small">
                                  <InputLabel>Field</InputLabel>
                                  <Select
                                    value={condition.field}
                                    onChange={(e) => {
                                      const updated = [...ruleGroups]
                                      const fieldConfig = getFieldConfig(e.target.value)
                                      const operators = getOperatorsForField(e.target.value)
                                      updated[groupId].conditions[conditionId] = {
                                        ...condition,
                                        field: e.target.value,
                                        operator: operators[0].value,
                                        value: '',
                                      }
                                      onChange(updated)
                                    }}
                                    label="Field"
                                  >
                                    {FIELDS.map((field) => (
                                      <MenuItem key={field.value} value={field.value}>
                                        {field.label}
                                      </MenuItem>
                                    ))}
                                  </Select>
                                </FormControl>
                              </Grid>
                              <Grid item xs={12} sm={3}>
                                <FormControl fullWidth size="small">
                                  <InputLabel>Operator</InputLabel>
                                  <Select
                                    value={condition.operator}
                                    onChange={(e) => {
                                      const updated = [...ruleGroups]
                                      updated[groupId].conditions[conditionId] = {
                                        ...condition,
                                        operator: e.target.value,
                                        value: '',
                                      }
                                      onChange(updated)
                                    }}
                                    label="Operator"
                                  >
                                    {getOperatorsForField(condition.field).map((op) => (
                                      <MenuItem key={op.value} value={op.value}>
                                        {op.label}
                                      </MenuItem>
                                    ))}
                                  </Select>
                                </FormControl>
                              </Grid>
                              <Grid item xs={12} sm={4}>
                                {renderValueInput(
                                  condition,
                                  editingValue,
                                  setEditingValue,
                                  errors[`edit-${groupId}-${conditionId}`]
                                )}
                              </Grid>
                              <Grid item xs={12} sm={2}>
                                <Box sx={{ display: 'flex', gap: 1 }}>
                                  <IconButton
                                    size="small"
                                    color="primary"
                                    onClick={() => handleSaveEdit(groupId, conditionId)}
                                  >
                                    <CheckIcon />
                                  </IconButton>
                                  <IconButton size="small" onClick={handleCancelEdit}>
                                    <CloseIcon />
                                  </IconButton>
                                </Box>
                              </Grid>
                            </Grid>
                          ) : (
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flex: 1 }}>
                                <Chip label={fieldConfig.label} size="small" variant="outlined" />
                                <Typography variant="body2" color="text.secondary">
                                  {operatorLabel}
                                </Typography>
                                {condition.operator !== 'IS_NULL' && condition.operator !== 'IS_NOT_NULL' && (
                                  <Typography variant="body2" sx={{ fontWeight: 500 }}>
                                    {formatConditionValue(condition) || '(empty)'}
                                  </Typography>
                                )}
                              </Box>
                              <Box>
                                <IconButton
                                  size="small"
                                  onClick={() => handleEditCondition(groupId, conditionId)}
                                >
                                  <EditIcon fontSize="small" />
                                </IconButton>
                                <IconButton
                                  size="small"
                                  color="error"
                                  onClick={() => handleRemoveCondition(groupId, conditionId)}
                                >
                                  <DeleteIcon fontSize="small" />
                                </IconButton>
                              </Box>
                            </Box>
                          )}
                        </Paper>
                      )
                    })}
                  </Box>
                ) : (
                  <Alert severity="info" sx={{ mb: 2 }}>
                    No conditions in this group. Add at least one condition below.
                  </Alert>
                )}

                {errors[`group-${groupId}`] && (
                  <Alert severity="error" sx={{ mb: 2 }}>
                    {errors[`group-${groupId}`]}
                  </Alert>
                )}

                <Divider sx={{ my: 2 }} />

                <Typography variant="subtitle2" gutterBottom sx={{ mb: 1.5 }}>
                  Add New Condition
                </Typography>

                <Grid container spacing={2} alignItems="flex-start">
                  <Grid item xs={12} sm={3}>
                    <FormControl fullWidth size="small">
                      <InputLabel>Field</InputLabel>
                      <Select
                        value={newCondition.field}
                        onChange={(e) => handleFieldChange(e.target.value)}
                        label="Field"
                      >
                        {FIELDS.map((field) => (
                          <MenuItem key={field.value} value={field.value}>
                            {field.label}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>

                  <Grid item xs={12} sm={3}>
                    <FormControl fullWidth size="small">
                      <InputLabel>Operator</InputLabel>
                      <Select
                        value={newCondition.operator}
                        onChange={(e) => handleOperatorChange(e.target.value)}
                        label="Operator"
                      >
                        {getOperatorsForField(newCondition.field).map((op) => (
                          <MenuItem key={op.value} value={op.value}>
                            {op.label}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>

                  <Grid item xs={12} sm={4}>
                    {renderValueInput(newCondition, newCondition.value, handleValueChange, errors[`group-${groupId}`])}
                  </Grid>

                  <Grid item xs={12} sm={2}>
                    <Button
                      variant="contained"
                      startIcon={<AddIcon />}
                      onClick={() => handleAddCondition(groupId)}
                      fullWidth
                      disabled={!newCondition.field || !newCondition.operator}
                    >
                      Add
                    </Button>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          ))}

          {ruleGroups.length > 1 && (
            <Paper variant="outlined" sx={{ p: 2, bgcolor: 'info.light', bgcolor: 'rgba(25, 118, 210, 0.08)' }}>
              <Box sx={{ display: 'flex', alignItems: 'start', gap: 1 }}>
                <InfoIcon color="info" sx={{ mt: 0.5 }} />
                <Box>
                  <Typography variant="body2" fontWeight="medium">
                    Multiple Rule Groups
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Multiple rule groups are combined with OR logic. This means the policy applies if ANY group matches.
                    Within each group, all conditions must match (AND logic).
                  </Typography>
                </Box>
              </Box>
            </Paper>
          )}
        </Box>
      )}
    </Box>
  )
}
