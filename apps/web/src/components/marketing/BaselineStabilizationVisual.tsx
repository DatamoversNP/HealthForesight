/**
 * Section 6: Baseline Stabilization Timeline
 * Raw dots → trend line → policy marker → counterfactual
 * One-time sequence animation
 */
import React, { useEffect, useRef, useState } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../../theme/healthForesightTheme'

export default function BaselineStabilizationVisual() {
  const svgRef = useRef<SVGSVGElement>(null)
  const [stage, setStage] = useState(0) // 0: dots, 1: trend, 2: policy, 3: counterfactual
  const [hasAnimated, setHasAnimated] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !hasAnimated) {
          setHasAnimated(true)
          // Sequence: dots (300ms) → trend (450ms) → policy (200ms) → counterfactual (350ms)
          setTimeout(() => setStage(1), 300)
          setTimeout(() => setStage(2), 750)
          setTimeout(() => setStage(3), 950)
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
  const height = 250
  const policyX = width * 0.4
  const baselineY = height * 0.5

  // Generate data points
  const dataPoints = Array.from({ length: 25 }, (_, i) => {
    const x = 50 + (i / 24) * policyX
    const noise = stage === 0 ? Math.random() * 25 - 12.5 : 0
    const trend = (i / 24) * 15
    return { x, y: baselineY - trend + noise }
  })

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
        viewBox="0 0 600 300"
        preserveAspectRatio="xMidYMid meet"
        sx={{
          width: '100%',
          height: '100%',
        }}
      >
        {/* Raw data dots (stage 0) */}
        {stage >= 0 && (
          <g opacity={stage === 0 ? 1 : 0.2}>
            {dataPoints.map((point, idx) => (
              <circle
                key={idx}
                cx={point.x}
                cy={point.y}
                r="3"
                fill={healthForesightColors.neutral.mid}
                opacity="0.6"
              />
            ))}
          </g>
        )}

        {/* Trend line (stage 1) - thin, neutral gray baseline */}
        {stage >= 1 && (
          <g>
            <path
              d={`M 50 ${baselineY} Q 150 ${baselineY - 8} 250 ${baselineY - 6} T ${policyX} ${baselineY}`}
              fill="none"
              stroke="#9CA3AF"
              strokeWidth="3"
              opacity="1"
              style={{ transition: 'opacity 450ms ease-out' }}
            />
            <text
              x="50"
              y={baselineY - 10}
              fill="#9CA3AF"
              fontSize="12"
              fontWeight="600"
              opacity="0.8"
            >
              Baseline
            </text>
          </g>
        )}

        {/* Policy marker (stage 2) - bright purple */}
        {stage >= 2 && (
          <g>
            <line
              x1={policyX}
              y1="50"
              x2={policyX}
              y2={height}
              stroke="#6366F1"
              strokeWidth="5"
              opacity="1"
            />
            <circle
              cx={policyX}
              cy={baselineY}
              r="14"
              fill="#6366F1"
              opacity="1"
            />
            <text
              x={policyX}
              y="40"
              textAnchor="middle"
              fill="#FFFFFF"
              fontSize="14"
              fontWeight="700"
            >
              Policy Date
            </text>
          </g>
        )}

        {/* Counterfactual (stage 3) - bold teal dashed */}
        {stage >= 3 && (
          <g>
            <path
              d={`M ${policyX} ${baselineY} Q ${policyX + 100} ${baselineY - 4} ${policyX + 200} ${baselineY - 2} T 550 ${baselineY}`}
              fill="none"
              stroke="#2EC4C6"
              strokeWidth="5"
              strokeDasharray="12,8"
              opacity="1"
              style={{ transition: 'opacity 350ms ease-out' }}
            />
            <text
              x={policyX + 150}
              y={baselineY - 15}
              fill="#2EC4C6"
              fontSize="12"
              fontWeight="600"
            >
              Counterfactual
            </text>
          </g>
        )}

        {/* Axis labels */}
        <text
          x="50"
          y="30"
          fill="#FFFFFF"
          fontSize="14"
          fontWeight="600"
        >
          Time →
        </text>
        <text
          x="50"
          y="280"
          fill="#FFFFFF"
          fontSize="13"
          fontWeight="600"
        >
          Utilization
        </text>
      </Box>
    </Box>
  )
}
