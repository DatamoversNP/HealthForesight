/**
 * Stacked Area Chart: Price, Utilization, Risk
 * Utilization area pulses subtly to show volatility
 */
import React, { useEffect, useState } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'

export default function UtilizationAreaChart() {
  const [pulse, setPulse] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setPulse((prev) => (prev + 0.1) % (Math.PI * 2))
    }, 100)
    return () => clearInterval(interval)
  }, [])

  const width = 600
  const height = 300
  const padding = 50

  // Utilization area (dominant, pulsing)
  const utilizationPoints = [
    { x: padding, y: height - padding - 100 },
    { x: padding + 100, y: height - padding - 80 },
    { x: padding + 200, y: height - padding - 120 },
    { x: padding + 300, y: height - padding - 90 },
    { x: padding + 400, y: height - padding - 110 },
    { x: padding + 500, y: height - padding - 100 },
  ]

  const utilizationPath = `M ${utilizationPoints[0].x} ${utilizationPoints[0].y} 
    ${utilizationPoints.slice(1).map((p) => `L ${p.x} ${p.y}`).join(' ')} 
    L ${utilizationPoints[utilizationPoints.length - 1].x} ${height - padding} 
    L ${padding} ${height - padding} Z`

  const pulseOffset = Math.sin(pulse) * 5

  return (
    <Box
      sx={{
        width: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: 2,
      }}
    >
      <Box
        component="svg"
        viewBox={`0 0 ${width} ${height}`}
        sx={{
          width: '100%',
          height: '100%',
          maxHeight: '350px',
        }}
      >
        {/* Price area (small, bottom) */}
        <path
          d={`M ${padding} ${height - padding} L ${padding + 500} ${height - padding} L ${padding + 500} ${height - padding - 30} L ${padding} ${height - padding - 30} Z`}
          fill={healthForesightColors.neutral.mid}
          opacity={0.3}
        />
        <text
          x={padding + 250}
          y={height - padding - 15}
          textAnchor="middle"
          fill={healthForesightColors.neutral.dark}
          fontSize="12"
          fontWeight="600"
        >
          Price
        </text>

        {/* Utilization area (dominant, pulsing) */}
        <path
          d={utilizationPath}
          fill={healthForesightColors.primary.main}
          opacity={0.4 + Math.sin(pulse) * 0.1}
          transform={`translate(0, ${pulseOffset})`}
        />
        <path
          d={utilizationPoints.map((p) => `L ${p.x} ${p.y}`).join(' ').replace('L', 'M')}
          fill="none"
          stroke={healthForesightColors.primary.main}
          strokeWidth="3"
          transform={`translate(0, ${pulseOffset})`}
        />
        <text
          x={padding + 250}
          y={height - padding - 60}
          textAnchor="middle"
          fill={healthForesightColors.primary.main}
          fontSize="14"
          fontWeight="700"
        >
          Utilization
        </text>

        {/* Risk area (top, small) */}
        <path
          d={`M ${padding} ${height - padding - 200} L ${padding + 500} ${height - padding - 200} L ${padding + 500} ${height - padding - 180} L ${padding} ${height - padding - 180} Z`}
          fill={healthForesightColors.amber.main}
          opacity={0.3}
        />
        <text
          x={padding + 250}
          y={height - padding - 185}
          textAnchor="middle"
          fill={healthForesightColors.amber.main}
          fontSize="12"
          fontWeight="600"
        >
          Risk
        </text>
      </Box>
    </Box>
  )
}
