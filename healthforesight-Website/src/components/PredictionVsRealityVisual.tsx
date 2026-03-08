/**
 * Section 6: Prediction vs Reality Comparison
 * Predicted curve fades, observed line draws, divergence highlighted
 */
import React, { useEffect, useRef, useState } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'

export default function PredictionVsRealityVisual() {
  const svgRef = useRef<SVGSVGElement>(null)
  const [progress, setProgress] = useState(0)
  const [hasAnimated, setHasAnimated] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !hasAnimated) {
          setHasAnimated(true)
          let startTime: number | null = null
          const animate = (timestamp: number) => {
            if (!startTime) startTime = timestamp
            const elapsed = timestamp - startTime
            const newProgress = Math.min(elapsed / 3000, 1)
            setProgress(newProgress)
            if (newProgress < 1) {
              requestAnimationFrame(animate)
            }
          }
          requestAnimationFrame(animate)
        }
      },
      { threshold: 0.3 }
    )

    if (svgRef.current) {
      observer.observe(svgRef.current)
    }

    return () => observer.disconnect()
  }, [hasAnimated])

  const width = 500
  const height = 300
  const policyX = 50 + width * 0.4
  const baselineY = height * 0.5

  // Predicted trajectory (fades out)
  const predictedPath = `M ${policyX} ${baselineY} Q ${policyX + 100} ${baselineY - 40} ${policyX + 200} ${baselineY - 50} T 550 ${baselineY - 60}`

  // Observed trajectory (draws over time)
  const observedPath = `M ${policyX} ${baselineY} Q ${policyX + 100} ${baselineY - 20} ${policyX + 200} ${baselineY - 15} T 550 ${baselineY - 10}`
  const pathLength = 400 // Approximate
  const drawLength = pathLength * progress

  // Divergence point
  const divergenceX = policyX + 150
  const divergenceY = baselineY - 30

  return (
    <Box
      sx={{
        width: '100%',
        maxWidth: { xs: '100%', md: '800px' },
        height: { xs: '250px', md: '400px' },
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: { xs: 2, md: 3 },
      }}
    >
      <Box
        component="svg"
        ref={svgRef}
        viewBox="0 0 600 350"
        preserveAspectRatio="xMidYMid meet"
        sx={{
          width: '100%',
          height: '100%',
        }}
      >
        {/* Predicted trajectory (fades to background) */}
        <path
          d={predictedPath}
          fill="none"
          stroke={healthForesightColors.accent.light}
          strokeWidth="5"
          strokeDasharray="6,4"
          opacity={0.6 - progress * 0.4}
        />
        {/* Predicted label with background for visibility */}
        <rect
          x={550 - 70}
          y={baselineY - 75}
          width="70"
          height="20"
          rx="4"
          fill={healthForesightColors.neutral.dark}
          opacity="0.7"
        />
        <text
          x={550}
          y={baselineY - 60}
          textAnchor="end"
          fill={healthForesightColors.accent.light}
          fontSize="15"
          fontWeight="700"
          opacity="1"
        >
          Predicted
        </text>

        {/* Observed trajectory (draws over time) */}
        <path
          d={observedPath}
          fill="none"
          stroke={healthForesightColors.primary.light}
          strokeWidth="6"
          strokeDasharray={`${drawLength} ${pathLength}`}
          opacity="1"
        />
        {progress > 0.3 && (
          <text
            x={550}
            y={baselineY - 10}
            textAnchor="end"
            fill={healthForesightColors.primary.light}
            fontSize="15"
            fontWeight="700"
          >
            Observed
          </text>
        )}

        {/* Divergence highlight (appears when paths diverge) */}
        {progress > 0.4 && (
          <g>
            <circle
              cx={divergenceX}
              cy={divergenceY}
              r="12"
              fill={healthForesightColors.amber.main}
              opacity="1"
              stroke="#FFFFFF"
              strokeWidth="2"
            />
            <line
              x1={divergenceX}
              y1={baselineY - 50}
              x2={divergenceX}
              y2={divergenceY + 20}
              stroke={healthForesightColors.amber.main}
              strokeWidth="3"
              strokeDasharray="4,3"
              opacity="0.8"
            />
            {progress > 0.6 && (
              <text
                x={divergenceX}
                y={baselineY - 60}
                textAnchor="middle"
                fill={healthForesightColors.amber.light}
                fontSize="14"
                fontWeight="700"
              >
                Divergence
              </text>
            )}
          </g>
        )}

        {/* Policy date marker */}
        <line
          x1={policyX}
          y1="50"
          x2={policyX}
          y2={height}
          stroke={healthForesightColors.primary.light}
          strokeWidth="4"
          strokeDasharray="6,4"
          opacity="0.9"
        />
        <text
          x={policyX}
          y="40"
          textAnchor="middle"
          fill={healthForesightColors.primary.light}
          fontSize="15"
          fontWeight="700"
        >
          Policy Start
        </text>

        {/* Labels */}
        <text
          x="50"
          y="30"
          fill="#FFFFFF"
          fontSize="15"
          fontWeight="700"
        >
          Time →
        </text>
      </Box>
    </Box>
  )
}
