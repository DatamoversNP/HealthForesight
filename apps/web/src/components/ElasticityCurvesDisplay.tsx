/**
 * Elasticity Curves Display Component - Visualizes utilization elasticity to policy friction
 */
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Alert,
  LinearProgress,
} from '@mui/material'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart } from 'recharts'

interface ElasticityCurve {
  service_category: string
  elasticity_coefficient: number
  elasticity_function: Record<string, number>
  threshold_friction?: number
  confidence_score: number
  data_points: number
  model_version: string
}

interface ElasticityCurvesDisplayProps {
  elasticityData: {
    policy_id: string
    service_categories: Record<string, ElasticityCurve>
    overall_elasticity: number
    model_quality: 'GOOD' | 'FAIR' | 'POOR'
    warnings: string[]
  }
  selectedCategory?: string
  onCategoryChange?: (category: string) => void
}

export default function ElasticityCurvesDisplay({ 
  elasticityData, 
  selectedCategory,
  onCategoryChange 
}: ElasticityCurvesDisplayProps) {
  // Add defensive checks for data structure
  if (!elasticityData || !elasticityData.service_categories) {
    return (
      <Alert severity="error">
        <Typography>Invalid elasticity data: service_categories not found</Typography>
      </Alert>
    )
  }

  const categories = Object.keys(elasticityData.service_categories)
  if (categories.length === 0) {
    return (
      <Alert severity="warning">
        <Typography>No service categories available in elasticity data</Typography>
      </Alert>
    )
  }

  const selectedCurve = selectedCategory 
    ? elasticityData.service_categories[selectedCategory] 
    : elasticityData.service_categories[categories[0]]

  // Prepare data for chart (elasticity function)
  const chartData = selectedCurve?.elasticity_function
    ? Object.entries(selectedCurve.elasticity_function)
        .map(([friction, elasticity]) => ({
          friction: parseFloat(friction),
          elasticity: elasticity,
          utilization_change: elasticity * 100, // Convert to percentage
        }))
        .sort((a, b) => a.friction - b.friction)
    : []

  const getQualityColor = (quality: string): 'success' | 'warning' | 'error' => {
    switch (quality) {
      case 'GOOD':
        return 'success'
      case 'FAIR':
        return 'warning'
      case 'POOR':
        return 'error'
      default:
        return 'warning'
    }
  }

  const getConfidenceColor = (score: number): 'success' | 'warning' | 'error' => {
    if (score >= 70) return 'success'
    if (score >= 40) return 'warning'
    return 'error'
  }

  return (
    <Box>
      {elasticityData.warnings && elasticityData.warnings.length > 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            <strong>Warnings:</strong>
          </Typography>
          <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
            {elasticityData.warnings.map((warning, idx) => (
              <li key={idx}>{warning}</li>
            ))}
          </ul>
        </Alert>
      )}

      {/* Summary Stats */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Overall Elasticity
              </Typography>
              <Typography variant="h4" color={(elasticityData.overall_elasticity ?? 0) < 0 ? 'success.main' : 'error.main'}>
                {(elasticityData.overall_elasticity ?? 0).toFixed(2)}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {(elasticityData.overall_elasticity ?? 0) < 0 
                  ? 'Demand decreases with friction' 
                  : 'Demand increases with friction'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Model Quality
              </Typography>
              <Chip
                label={elasticityData.model_quality || 'UNKNOWN'}
                color={getQualityColor(elasticityData.model_quality || 'FAIR')}
                size="small"
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Service Categories
              </Typography>
              <Typography variant="h4" color="primary">
                {categories.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Category Selector */}
      {categories.length > 1 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <FormControl fullWidth size="small">
              <InputLabel>Select Service Category</InputLabel>
              <Select
                value={selectedCategory || categories[0]}
                onChange={(e) => onCategoryChange?.(e.target.value)}
                label="Select Service Category"
              >
                {categories.map((category) => (
                  <MenuItem key={category} value={category}>
                    {category.replace(/_/g, ' ')}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </CardContent>
        </Card>
      )}

      {/* Elasticity Curve Chart */}
      {selectedCurve && chartData.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6" gutterBottom>
                Elasticity Curve: {selectedCurve.service_category.replace(/_/g, ' ')}
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                <Typography variant="body2" color="text.secondary">
                  Confidence: {selectedCurve.confidence_score.toFixed(0)}%
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={selectedCurve.confidence_score}
                  color={getConfidenceColor(selectedCurve.confidence_score)}
                  sx={{ width: 60, height: 6, borderRadius: 1 }}
                />
              </Box>
            </Box>

            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Elasticity Coefficient: {selectedCurve.elasticity_coefficient.toFixed(3)}
              {selectedCurve.threshold_friction && (
                <> | Threshold: {selectedCurve.threshold_friction.toFixed(2)}</>
              )}
            </Typography>

            <ResponsiveContainer width="100%" height={400}>
              <AreaChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="friction" 
                  label={{ value: 'Policy Friction Level', position: 'insideBottom', offset: -5 }}
                  domain={[0, 1]}
                />
                <YAxis 
                  label={{ value: 'Elasticity / Utilization Change (%)', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip 
                  formatter={(value: number, name: string) => {
                    if (name === 'elasticity') return [value.toFixed(3), 'Elasticity']
                    if (name === 'utilization_change') return [`${value.toFixed(1)}%`, 'Utilization Change']
                    return [value, name]
                  }}
                  labelFormatter={(label) => `Friction Level: ${label}`}
                />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="utilization_change"
                  stroke="#8884d8"
                  fill="#8884d8"
                  fillOpacity={0.3}
                  name="Utilization Change (%)"
                />
                <Line
                  type="monotone"
                  dataKey="elasticity"
                  stroke="#82ca9d"
                  strokeWidth={2}
                  name="Elasticity"
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                />
                {selectedCurve.threshold_friction && (
                  <Line
                    type="monotone"
                    dataKey={() => 0}
                    stroke="#ff7300"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    name={`Threshold (${selectedCurve.threshold_friction.toFixed(2)})`}
                  />
                )}
              </AreaChart>
            </ResponsiveContainer>

            {/* Threshold Indicator */}
            {selectedCurve.threshold_friction && (
              <Alert severity="info" sx={{ mt: 2 }}>
                <Typography variant="body2">
                  <strong>Threshold Detected:</strong> Elasticity changes significantly at friction level {selectedCurve.threshold_friction.toFixed(2)}.
                  Policy adjustments above this threshold may have non-linear effects.
                </Typography>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Category Comparison Table */}
      {categories.length > 1 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Elasticity by Service Category
            </Typography>
            <Box sx={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #e0e0e0' }}>
                    <th style={{ padding: '8px', textAlign: 'left' }}>Category</th>
                    <th style={{ padding: '8px', textAlign: 'right' }}>Elasticity</th>
                    <th style={{ padding: '8px', textAlign: 'right' }}>Threshold</th>
                    <th style={{ padding: '8px', textAlign: 'right' }}>Confidence</th>
                    <th style={{ padding: '8px', textAlign: 'right' }}>Data Points</th>
                  </tr>
                </thead>
                <tbody>
                  {categories.map((category) => {
                    const curve = elasticityData.service_categories[category]
                    return (
                      <tr 
                        key={category}
                        style={{ 
                          borderBottom: '1px solid #e0e0e0',
                          backgroundColor: selectedCategory === category ? '#f5f5f5' : 'transparent',
                          cursor: 'pointer'
                        }}
                        onClick={() => onCategoryChange?.(category)}
                      >
                        <td style={{ padding: '8px' }}>{category.replace(/_/g, ' ')}</td>
                        <td style={{ padding: '8px', textAlign: 'right' }}>
                          <Typography
                            variant="body2"
                            color={curve.elasticity_coefficient < 0 ? 'success.main' : 'error.main'}
                            fontWeight="medium"
                          >
                            {curve.elasticity_coefficient.toFixed(3)}
                          </Typography>
                        </td>
                        <td style={{ padding: '8px', textAlign: 'right' }}>
                          {curve.threshold_friction ? curve.threshold_friction.toFixed(2) : 'N/A'}
                        </td>
                        <td style={{ padding: '8px', textAlign: 'right' }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, justifyContent: 'flex-end' }}>
                            <LinearProgress
                              variant="determinate"
                              value={curve.confidence_score}
                              color={getConfidenceColor(curve.confidence_score)}
                              sx={{ width: 60, height: 6, borderRadius: 1 }}
                            />
                            <Typography variant="caption">{curve.confidence_score.toFixed(0)}%</Typography>
                          </Box>
                        </td>
                        <td style={{ padding: '8px', textAlign: 'right' }}>{curve.data_points}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  )
}

