/**
 * Fan Chart Component - Epic 4
 * Visualizes forecast distributions with P10/P50/P90 ranges and confidence intervals
 */
import { useMemo } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  useTheme,
} from '@mui/material'
import {
  LineChart,
  Line,
  Area,
  AreaChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'

interface UncertaintyRange {
  p10: number
  p50: number
  p90: number
  mean?: number
  std_dev?: number
}

interface ConfidenceInterval {
  lower_bound: number
  upper_bound: number
  confidence_level: number
  distribution_type?: string
}

interface ForecastData {
  forecast_id: string
  metric_name: string
  point_estimate: number
  uncertainty_range?: UncertaintyRange
  confidence_interval?: ConfidenceInterval
  distribution_data?: any
}

interface FanChartProps {
  forecast: ForecastData
  height?: number
}

export default function FanChart({ forecast, height = 300 }: FanChartProps) {
  const theme = useTheme()

  // Generate data points for fan chart
  const chartData = useMemo(() => {
    if (!forecast.uncertainty_range) {
      return []
    }

    const { p10, p50, p90 } = forecast.uncertainty_range
    const pointEstimate = forecast.point_estimate

    // Generate time series data (example: 12 months)
    const months = Array.from({ length: 12 }, (_, i) => i + 1)
    
    return months.map((month) => {
      // Simulate fan widening over time (uncertainty increases)
      const timeFactor = 1 + (month - 1) * 0.1
      return {
        month: `M${month}`,
        p10: p10 * timeFactor,
        p50: p50 * timeFactor,
        p90: p90 * timeFactor,
        pointEstimate: pointEstimate * timeFactor,
        lowerBound: forecast.confidence_interval?.lower_bound 
          ? forecast.confidence_interval.lower_bound * timeFactor 
          : undefined,
        upperBound: forecast.confidence_interval?.upper_bound 
          ? forecast.confidence_interval.upper_bound * timeFactor 
          : undefined,
      }
    })
  }, [forecast])

  if (!forecast.uncertainty_range || chartData.length === 0) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            {forecast.metric_name}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Point Estimate: {forecast.point_estimate.toLocaleString(undefined, {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            No uncertainty range data available for visualization.
          </Typography>
        </CardContent>
      </Card>
    )
  }

  const { p10, p50, p90 } = forecast.uncertainty_range

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {forecast.metric_name}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Forecast Distribution (P10/P50/P90)
        </Typography>

        <Box sx={{ width: '100%', height }}>
          <ResponsiveContainer>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorP90" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={theme.palette.primary.light} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={theme.palette.primary.light} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip
                formatter={(value: number) => value.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              />
              <Legend />
              
              {/* P90 range (widest) */}
              <Area
                type="monotone"
                dataKey="p90"
                stroke={theme.palette.primary.light}
                fill="url(#colorP90)"
                fillOpacity={0.2}
                name="P90 (Optimistic)"
              />
              
              {/* P10 range */}
              <Area
                type="monotone"
                dataKey="p10"
                stroke={theme.palette.primary.dark}
                fill={theme.palette.primary.dark}
                fillOpacity={0.1}
                name="P10 (Conservative)"
              />
              
              {/* P50 median line */}
              <Line
                type="monotone"
                dataKey="p50"
                stroke={theme.palette.primary.main}
                strokeWidth={2}
                name="P50 (Median)"
              />
              
              {/* Point estimate */}
              <Line
                type="monotone"
                dataKey="pointEstimate"
                stroke={theme.palette.secondary.main}
                strokeWidth={2}
                strokeDasharray="5 5"
                name="Point Estimate"
              />
              
              {/* Confidence interval bounds if available */}
              {forecast.confidence_interval && (
                <>
                  <ReferenceLine
                    y={forecast.confidence_interval.lower_bound}
                    stroke={theme.palette.warning.main}
                    strokeDasharray="3 3"
                    label="Lower CI"
                  />
                  <ReferenceLine
                    y={forecast.confidence_interval.upper_bound}
                    stroke={theme.palette.warning.main}
                    strokeDasharray="3 3"
                    label="Upper CI"
                  />
                </>
              )}
            </AreaChart>
          </ResponsiveContainer>
        </Box>

        <Box sx={{ mt: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Box>
            <Typography variant="caption" color="text.secondary">
              P10 (Conservative)
            </Typography>
            <Typography variant="body2" fontWeight="bold">
              {p10.toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">
              P50 (Median)
            </Typography>
            <Typography variant="body2" fontWeight="bold">
              {p50.toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">
              P90 (Optimistic)
            </Typography>
            <Typography variant="body2" fontWeight="bold">
              {p90.toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </Typography>
          </Box>
          {forecast.confidence_interval && (
            <Box>
              <Typography variant="caption" color="text.secondary">
                {forecast.confidence_interval.confidence_level * 100}% CI
              </Typography>
              <Typography variant="body2" fontWeight="bold">
                [{forecast.confidence_interval.lower_bound.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}, {forecast.confidence_interval.upper_bound.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}]
              </Typography>
            </Box>
          )}
        </Box>
      </CardContent>
    </Card>
  )
}

