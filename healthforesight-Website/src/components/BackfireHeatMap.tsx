/**
 * Backfire Heat Map
 * Matrix: Rows = Policy types, Columns = Failure modes
 */
import React, { useEffect, useState } from 'react'
import { Box, Typography } from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'

export default function BackfireHeatMap() {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          setVisible(true)
        }
      },
      { threshold: 0.2 }
    )

    const element = document.getElementById('backfire-heatmap')
    if (element) observer.observe(element)

    return () => observer.disconnect()
  }, [])

  const policyTypes = [
    'Prior Authorization',
    'Site-of-Care Restrictions',
    'Benefit Design Changes',
    'Clinical Pathways',
  ]

  const failureModes = [
    'Substitution',
    'Site Leakage',
    'Workarounds',
    'Delayed Cost',
    'Forecast Failure',
  ]

  // Heat intensity (0-1) for each cell
  const heatData = [
    [0.8, 0.6, 0.9, 0.7, 0.5], // Prior Auth
    [0.7, 0.9, 0.5, 0.8, 0.6], // Site-of-Care
    [0.6, 0.4, 0.7, 0.9, 0.8], // Benefit Design
    [0.5, 0.3, 0.6, 0.5, 0.4], // Clinical Pathways
  ]

  const getColor = (intensity: number) => {
    if (intensity < 0.3) return healthForesightColors.neutral.light
    if (intensity < 0.6) return healthForesightColors.accent.main + '40'
    if (intensity < 0.8) return healthForesightColors.amber.main + '60'
    return healthForesightColors.amber.main + '90'
  }

  const cellWidth = 100
  const cellHeight = 50
  const startX = 200
  const startY = 80

  return (
    <Box
      id="backfire-heatmap"
      sx={{
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        p: 3,
      }}
    >
      <Box
        component="svg"
        viewBox="0 0 800 400"
        sx={{
          width: '100%',
          height: '100%',
          maxHeight: '450px',
        }}
      >
        {/* Column headers */}
        {failureModes.map((mode, idx) => (
          <text
            key={idx}
            x={startX + idx * cellWidth + cellWidth / 2}
            y={startY - 20}
            textAnchor="middle"
            fill={healthForesightColors.neutral.dark}
            fontSize="12"
            fontWeight="700"
            opacity={visible ? 1 : 0}
          >
            {mode}
          </text>
        ))}

        {/* Rows */}
        {policyTypes.map((policy, rowIdx) => (
          <g key={rowIdx}>
            {/* Row label */}
            <text
              x={startX - 10}
              y={startY + rowIdx * cellHeight + cellHeight / 2 + 5}
              textAnchor="end"
              fill={healthForesightColors.neutral.dark}
              fontSize="12"
              fontWeight="600"
              opacity={visible ? 1 : 0}
            >
              {policy}
            </text>

            {/* Cells */}
            {failureModes.map((_, colIdx) => {
              const intensity = heatData[rowIdx][colIdx]
              return (
                <g key={colIdx}>
                  <rect
                    x={startX + colIdx * cellWidth}
                    y={startY + rowIdx * cellHeight}
                    width={cellWidth - 4}
                    height={cellHeight - 4}
                    fill={getColor(intensity)}
                    stroke={healthForesightColors.neutral.light}
                    strokeWidth="1"
                    opacity={visible ? 1 : 0}
                  />
                  <text
                    x={startX + colIdx * cellWidth + cellWidth / 2}
                    y={startY + rowIdx * cellHeight + cellHeight / 2 + 5}
                    textAnchor="middle"
                    fill={intensity > 0.5 ? '#FFFFFF' : healthForesightColors.neutral.dark}
                    fontSize="11"
                    fontWeight="600"
                    opacity={visible ? 1 : 0}
                  >
                    {Math.round(intensity * 100)}%
                  </text>
                </g>
              )
            })}
          </g>
        ))}

        {/* Legend */}
        <g opacity={visible ? 1 : 0}>
          <text
            x={startX}
            y={startY + policyTypes.length * cellHeight + 30}
            fill={healthForesightColors.neutral.dark}
            fontSize="12"
            fontWeight="700"
          >
            Frequency/Severity:
          </text>
          {[0, 0.3, 0.6, 0.8, 1.0].map((val, idx) => (
            <g key={idx}>
              <rect
                x={startX + 150 + idx * 50}
                y={startY + policyTypes.length * cellHeight + 20}
                width={40}
                height={20}
                fill={getColor(val)}
                stroke={healthForesightColors.neutral.light}
                strokeWidth="1"
              />
              <text
                x={startX + 150 + idx * 50 + 20}
                y={startY + policyTypes.length * cellHeight + 45}
                textAnchor="middle"
                fill={healthForesightColors.neutral.dark}
                fontSize="10"
              >
                {Math.round(val * 100)}%
              </text>
            </g>
          ))}
        </g>
      </Box>
    </Box>
  )
}
