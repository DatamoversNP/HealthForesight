/**
 * Confidence Fan Chart: Center line = expected, expanding bands = uncertainty
 * Label ranges: Target elasticity, Downstream elasticity, Net elasticity
 * Fan widens slowly over time
 */
import React, { useEffect, useState } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'

export default function ConfidenceFanChart() {
  const [fanWidth, setFanWidth] = useState(0)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          let width = 0
          const interval = setInterval(() => {
            width += 0.01
            setFanWidth(Math.min(width, 1))
            if (width >= 1) clearInterval(interval)
          }, 30)
          return () => clearInterval(interval)
        }
      },
      { threshold: 0.2 }
    )

    const element = document.getElementById('confidence-fan')
    if (element) observer.observe(element)

    return () => observer.disconnect()
  }, [])

  const width = 600
  const height = 300
  const centerX = width / 2
  const centerY = height - 50
  const maxRadius = 200

  const bands = [
    { label: 'Target Elasticity', radius: maxRadius * 0.3, color: healthForesightColors.accent.main },
    { label: 'Downstream Elasticity', radius: maxRadius * 0.6, color: healthForesightColors.primary.main },
    { label: 'Net Elasticity', radius: maxRadius, color: healthForesightColors.amber.main },
  ]

  return (
    <Box
      id="confidence-fan"
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
        {/* Fan bands */}
        {bands.map((band, idx) => {
          const currentRadius = band.radius * fanWidth
          const path = `M ${centerX} ${centerY} 
            A ${currentRadius} ${currentRadius} 0 0 1 ${centerX + currentRadius} ${centerY}
            L ${centerX} ${centerY} Z`

          return (
            <g key={idx}>
              <path
                d={path}
                fill={band.color}
                opacity={0.2 - idx * 0.05}
              />
              {fanWidth > 0.5 && (
                <text
                  x={centerX + currentRadius * 0.7}
                  y={centerY - currentRadius * 0.3}
                  fill={band.color}
                  fontSize="11"
                  fontWeight="600"
                  opacity={fanWidth}
                >
                  {band.label}
                </text>
              )}
            </g>
          )
        })}

        {/* Center expected line */}
        <line
          x1={centerX}
          y1={centerY}
          x2={centerX + maxRadius * fanWidth}
          y2={centerY}
          stroke={healthForesightColors.neutral.dark}
          strokeWidth="3"
          opacity={fanWidth > 0.3 ? 1 : 0}
        />
        <text
          x={centerX + maxRadius * fanWidth * 0.5}
          y={centerY + 20}
          textAnchor="middle"
          fill={healthForesightColors.neutral.dark}
          fontSize="12"
          fontWeight="700"
          opacity={fanWidth > 0.3 ? 1 : 0}
        >
          Expected
        </text>
      </Box>
    </Box>
  )
}
