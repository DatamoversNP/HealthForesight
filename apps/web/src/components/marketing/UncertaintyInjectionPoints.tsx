/**
 * Visual 2: Uncertainty Injection Points
 * Horizontal pipeline: Policy → Measurement → Forecast → Budget
 * Risk bar grows as user scrolls into view
 */
import React, { useEffect, useState } from 'react'
import { Box, Typography } from '@mui/material'
import { healthForesightColors } from '../../theme/healthForesightTheme'

export default function UncertaintyInjectionPoints() {
  const [riskBarProgress, setRiskBarProgress] = useState(0)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          // Risk bar grows as user scrolls
          let progress = 0
          const interval = setInterval(() => {
            progress += 0.02
            setRiskBarProgress(Math.min(progress, 1))
            if (progress >= 1) clearInterval(interval)
          }, 30)
        }
      },
      { threshold: 0.2 }
    )

    const element = document.getElementById('uncertainty-injection')
    if (element) observer.observe(element)

    return () => observer.disconnect()
  }, [])

  const width = 700
  const height = 250
  const stages = [
    { label: 'Policy', x: 100 },
    { label: 'Measurement', x: 250 },
    { label: 'Forecast', x: 400 },
    { label: 'Budget', x: 550 },
  ]

  return (
    <Box
      id="uncertainty-injection"
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
        viewBox={`0 0 ${width} ${height}`}
        sx={{
          width: '100%',
          height: '100%',
          maxHeight: '300px',
        }}
      >
        {/* Pipeline stages */}
        {stages.map((stage, idx) => (
          <g key={idx}>
            {/* Stage box */}
            <rect
              x={stage.x - 50}
              y={80}
              width={100}
              height={50}
              fill={healthForesightColors.neutral.background}
              stroke={healthForesightColors.neutral.mid}
              strokeWidth="2"
              rx="4"
            />
            <text
              x={stage.x}
              y={110}
              textAnchor="middle"
              fill={healthForesightColors.neutral.dark}
              fontSize="13"
              fontWeight="700"
            >
              {stage.label}
            </text>

            {/* Uncertainty leak icon */}
            <circle
              cx={stage.x}
              cy={140}
              r="6"
              fill={healthForesightColors.amber.main}
              opacity={0.8}
            />
            <text
              x={stage.x}
              y={165}
              textAnchor="middle"
              fill={healthForesightColors.amber.main}
              fontSize="10"
              fontWeight="600"
            >
              Uncertainty
            </text>

            {/* Connection arrow */}
            {idx < stages.length - 1 && (
              <line
                x1={stage.x + 50}
                y1={105}
                x2={stages[idx + 1].x - 50}
                y2={105}
                stroke={healthForesightColors.neutral.mid}
                strokeWidth="2"
              />
            )}
          </g>
        ))}

        {/* Accumulating risk bar */}
        <rect
          x={50}
          y={200}
          width={(width - 100) * riskBarProgress}
          height={20}
          fill={healthForesightColors.amber.main}
          rx="10"
        />
        <text
          x={width / 2}
          y={215}
          textAnchor="middle"
          fill={healthForesightColors.neutral.dark}
          fontSize="12"
          fontWeight="700"
        >
          Accumulating Risk
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
          maxWidth: '600px',
        }}
      >
        Uncertainty compounds as it moves from analytics to finance.
      </Typography>
    </Box>
  )
}
