/**
 * Counterfactual Timeline: Observed line (solid) vs Counterfactual (dashed)
 * Vertical policy start marker
 * Shaded uncertainty band around counterfactual
 */
import React, { useEffect, useState } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'

export default function CounterfactualTimeline() {
  const [observedProgress, setObservedProgress] = useState(0)
  const [counterfactualVisible, setCounterfactualVisible] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          // Draw observed line first
          let progress = 0
          const interval = setInterval(() => {
            progress += 0.02
            setObservedProgress(Math.min(progress, 1))
            if (progress >= 1) {
              clearInterval(interval)
              setTimeout(() => setCounterfactualVisible(true), 300)
            }
          }, 20)
          return () => clearInterval(interval)
        }
      },
      { threshold: 0.2 }
    )

    const element = document.getElementById('counterfactual-timeline')
    if (element) observer.observe(element)

    return () => observer.disconnect()
  }, [])

  const width = 600
  const height = 300
  const padding = 50
  const policyX = padding + (width - padding * 2) * 0.4

  // Observed path (solid, purple)
  const observedPath = `M ${padding} ${padding + (height - padding * 2) * 0.6} 
    L ${policyX} ${padding + (height - padding * 2) * 0.6}
    L ${padding + (width - padding * 2) * 0.6} ${padding + (height - padding * 2) * 0.4}
    L ${width - padding} ${padding + (height - padding * 2) * 0.3}`

  // Counterfactual path (dashed, teal)
  const counterfactualPath = `M ${padding} ${padding + (height - padding * 2) * 0.6} 
    L ${width - padding} ${padding + (height - padding * 2) * 0.55}`

  return (
    <Box
      id="counterfactual-timeline"
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
        {/* Uncertainty band around counterfactual */}
        {counterfactualVisible && (
          <path
            d={`M ${padding} ${padding + (height - padding * 2) * 0.6 - 15} 
              L ${width - padding} ${padding + (height - padding * 2) * 0.55 - 15}
              L ${width - padding} ${padding + (height - padding * 2) * 0.55 + 15}
              L ${padding} ${padding + (height - padding * 2) * 0.6 + 15} Z`}
            fill={healthForesightColors.accent.main}
            opacity={0.15}
          />
        )}

        {/* Counterfactual line (dashed, teal) */}
        {counterfactualVisible && (
          <path
            d={counterfactualPath}
            fill="none"
            stroke={healthForesightColors.accent.main}
            strokeWidth="2"
            strokeDasharray="8 4"
            opacity={0.7}
          />
        )}

        {/* Observed line (solid, purple) */}
        <path
          d={observedPath}
          fill="none"
          stroke={healthForesightColors.primary.main}
          strokeWidth="3"
          strokeDasharray={`${observedProgress * 600} 600`}
          opacity={observedProgress > 0 ? 1 : 0}
        />

        {/* Policy start marker */}
        <line
          x1={policyX}
          y1={padding}
          x2={policyX}
          y2={height - padding}
          stroke={healthForesightColors.amber.main}
          strokeWidth="3"
          opacity={observedProgress > 0.4 ? 1 : 0}
        />
        <text
          x={policyX}
          y={padding - 10}
          textAnchor="middle"
          fill={healthForesightColors.amber.main}
          fontSize="12"
          fontWeight="700"
          opacity={observedProgress > 0.4 ? 1 : 0}
        >
          Policy Start
        </text>

        {/* Labels */}
        {counterfactualVisible && (
          <g>
            <text
              x={width - padding - 10}
              y={padding + (height - padding * 2) * 0.55 - 20}
              textAnchor="end"
              fill={healthForesightColors.accent.main}
              fontSize="11"
              fontWeight="600"
            >
              Counterfactual
            </text>
            <text
              x={width - padding - 10}
              y={padding + (height - padding * 2) * 0.3 - 20}
              textAnchor="end"
              fill={healthForesightColors.primary.main}
              fontSize="11"
              fontWeight="600"
            >
              Observed
            </text>
          </g>
        )}
      </Box>
    </Box>
  )
}
