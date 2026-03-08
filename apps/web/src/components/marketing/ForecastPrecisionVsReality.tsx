/**
 * Visual 1: Forecast Precision vs Reality
 * Two overlapping forecast cones: narrow (assumed) vs wide (actual)
 */
import React, { useEffect, useState } from 'react'
import { Box, Typography } from '@mui/material'
import { healthForesightColors } from '../../theme/healthForesightTheme'

export default function ForecastPrecisionVsReality() {
  const [narrowVisible, setNarrowVisible] = useState(false)
  const [wideVisible, setWideVisible] = useState(false)

  useEffect(() => {
    // Narrow cone appears first
    setNarrowVisible(true)
    // Wide cone fades/expands in over 900ms
    setTimeout(() => setWideVisible(true), 300)
  }, [])

  const width = 400
  const height = 300
  const padding = 50
  const centerX = width / 2
  const startY = padding
  const endY = height - padding

  // Narrow cone (assumed certainty)
  const narrowTopWidth = 20
  const narrowBottomWidth = 40

  // Wide cone (actual uncertainty)
  const wideTopWidth = 30
  const wideBottomWidth = 180

  return (
    <Box
      sx={{
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
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
        {/* Narrow cone - Assumed Policy Savings */}
        {narrowVisible && (
          <g opacity={0.6}>
            <path
              d={`M ${centerX - narrowTopWidth / 2} ${startY} 
                L ${centerX - narrowBottomWidth / 2} ${endY}
                L ${centerX + narrowBottomWidth / 2} ${endY}
                L ${centerX + narrowTopWidth / 2} ${startY} Z`}
              fill={healthForesightColors.primary.main}
              opacity={0.2}
            />
            <line
              x1={centerX}
              y1={startY}
              x2={centerX}
              y2={endY}
              stroke={healthForesightColors.primary.main}
              strokeWidth="2"
            />
            <text
              x={centerX}
              y={startY - 10}
              textAnchor="middle"
              fill={healthForesightColors.primary.main}
              fontSize="11"
              fontWeight="700"
            >
              Assumed Policy Savings (Point Estimate)
            </text>
          </g>
        )}

        {/* Wide cone - Actual Cost Outcomes */}
        {wideVisible && (
          <g opacity={wideVisible ? 1 : 0} style={{ transition: 'opacity 900ms ease' }}>
            <path
              d={`M ${centerX - wideTopWidth / 2} ${startY + 20} 
                L ${centerX - wideBottomWidth / 2} ${endY}
                L ${centerX + wideBottomWidth / 2} ${endY}
                L ${centerX + wideTopWidth / 2} ${startY + 20} Z`}
              fill={healthForesightColors.amber.main}
              opacity={0.15}
            />
            <line
              x1={centerX}
              y1={startY + 20}
              x2={centerX}
              y2={endY}
              stroke={healthForesightColors.amber.main}
              strokeWidth="2"
              strokeDasharray="4 4"
            />
            <text
              x={centerX}
              y={endY + 20}
              textAnchor="middle"
              fill={healthForesightColors.amber.main}
              fontSize="11"
              fontWeight="700"
            >
              Actual Cost Outcomes (Behavior-Driven)
            </text>
          </g>
        )}

        {/* Time axis */}
        <text
          x={width / 2}
          y={height - 10}
          textAnchor="middle"
          fill={healthForesightColors.neutral.mid}
          fontSize="11"
          fontWeight="600"
        >
          Time →
        </text>
      </Box>
      <Typography
        variant="caption"
        sx={{
          fontSize: '12px',
          color: healthForesightColors.neutral.mid,
          fontStyle: 'italic',
          textAlign: 'center',
          mt: 1,
          maxWidth: '350px',
        }}
      >
        Most organizations budget as if uncertainty doesn't exist — until it shows up in financial results.
      </Typography>
    </Box>
  )
}
