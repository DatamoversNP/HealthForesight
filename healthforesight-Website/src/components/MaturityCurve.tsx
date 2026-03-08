/**
 * Maturity Curve: Static enforcement → Adaptive intelligence
 * Indicator moves right as user scrolls
 */
import React, { useEffect, useState } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'

export default function MaturityCurve() {
  const [indicatorPosition, setIndicatorPosition] = useState(0)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          let position = 0
          const interval = setInterval(() => {
            position += 0.01
            setIndicatorPosition(Math.min(position, 1))
            if (position >= 1) clearInterval(interval)
          }, 20)
          return () => clearInterval(interval)
        }
      },
      { threshold: 0.2 }
    )

    const element = document.getElementById('maturity-curve')
    if (element) observer.observe(element)

    return () => observer.disconnect()
  }, [])

  const width = 600
  const height = 200
  const curveY = height / 2

  // Maturity curve path
  const curvePath = `M 50 ${curveY} 
    Q ${width * 0.3} ${curveY - 40} 
    ${width * 0.5} ${curveY - 30}
    T ${width - 50} ${curveY - 20}`

  const indicatorX = 50 + (width - 100) * indicatorPosition

  return (
    <Box
      id="maturity-curve"
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
          maxHeight: '250px',
        }}
      >
        {/* Curve */}
        <path
          d={curvePath}
          fill="none"
          stroke={healthForesightColors.neutral.mid}
          strokeWidth="3"
          opacity={0.5}
        />

        {/* Indicator */}
        <circle
          cx={indicatorX}
          cy={curveY - 20 * indicatorPosition}
          r="8"
          fill={healthForesightColors.primary.main}
          stroke="#FFFFFF"
          strokeWidth="2"
        />

        {/* Labels */}
        <text
          x={50}
          y={height - 20}
          fill={healthForesightColors.neutral.dark}
          fontSize="12"
          fontWeight="700"
        >
          Static Enforcement
        </text>
        <text
          x={width - 50}
          y={height - 20}
          textAnchor="end"
          fill={healthForesightColors.neutral.dark}
          fontSize="12"
          fontWeight="700"
        >
          Adaptive Intelligence
        </text>
      </Box>
    </Box>
  )
}
