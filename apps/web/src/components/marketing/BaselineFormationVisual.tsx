/**
 * Section 4: Baseline Formation Animation
 * Raw data → noise fades → trend stabilizes → policy date → counterfactual
 */
import React, { useEffect, useRef, useState } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../../theme/healthForesightTheme'

export default function BaselineFormationVisual() {
  const svgRef = useRef<SVGSVGElement>(null)
  const [stage, setStage] = useState(0) // 0: raw data, 1: noise fades, 2: trend, 3: policy, 4: counterfactual
  const [hasAnimated, setHasAnimated] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !hasAnimated) {
          setHasAnimated(true)
          // Progress through stages
          setTimeout(() => setStage(1), 500)
          setTimeout(() => setStage(2), 1500)
          setTimeout(() => setStage(3), 2500)
          setTimeout(() => setStage(4), 3500)
        }
      },
      { threshold: 0.3 }
    )

    if (svgRef.current) {
      observer.observe(svgRef.current)
    }

    return () => observer.disconnect()
  }, [hasAnimated])

  const timelineWidth = 500
  const timelineHeight = 300
  const policyX = timelineWidth * 0.4
  const baselineY = timelineHeight * 0.5

  // Generate data points
  const dataPoints = Array.from({ length: 30 }, (_, i) => {
    const x = 50 + (i / 29) * timelineWidth
    const noise = stage >= 1 ? 0 : Math.random() * 30 - 15
    const trend = (i / 29) * 20
    const y = baselineY - trend + noise
    return { x, y }
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
        viewBox="0 0 600 350"
        preserveAspectRatio="xMidYMid meet"
        sx={{
          width: '100%',
          height: '100%',
        }}
      >
        {/* Raw data points (fade out) */}
        {stage < 2 && (
          <g opacity={stage === 0 ? 1 : 0.3}>
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

        {/* Trend line (appears at stage 2) */}
        {stage >= 2 && (
          <path
            d={`M 50 ${baselineY} Q 150 ${baselineY - 10} 250 ${baselineY - 8} T ${policyX} ${baselineY}`}
            fill="none"
            stroke={healthForesightColors.accent.light}
            strokeWidth="6"
            strokeDasharray={stage === 2 ? '6,4' : '0,0'}
            opacity="1"
          />
        )}

        {/* Policy date marker (appears at stage 3) */}
        {stage >= 3 && (
          <g>
            <line
              x1={policyX}
              y1="50"
              x2={policyX}
              y2={timelineHeight}
              stroke={healthForesightColors.primary.main}
              strokeWidth="4"
              opacity="1"
            />
            <circle
              cx={policyX}
              cy={baselineY}
              r="14"
              fill={healthForesightColors.primary.main}
              opacity="1"
              stroke="#FFFFFF"
              strokeWidth="3"
            />
            <text
              x={policyX}
              y="40"
              textAnchor="middle"
              fill={healthForesightColors.primary.light}
              fontSize="16"
              fontWeight="700"
            >
              Policy Date
            </text>
          </g>
        )}

        {/* Counterfactual path (appears at stage 4) */}
        {stage >= 4 && (
          <path
            d={`M ${policyX} ${baselineY} Q ${policyX + 100} ${baselineY - 5} ${policyX + 200} ${baselineY - 3} T 550 ${baselineY}`}
            fill="none"
            stroke={healthForesightColors.accent.main}
            strokeWidth="5"
            strokeDasharray="10,6"
            opacity="0.9"
          />
        )}

        {/* Baseline area (shaded) */}
        {stage >= 2 && (
          <path
            d={`M 50 ${baselineY} Q 150 ${baselineY - 10} 250 ${baselineY - 8} T ${policyX} ${baselineY} L ${policyX} ${timelineHeight} L 50 ${timelineHeight} Z`}
            fill={healthForesightColors.neutral.light}
            opacity="0.3"
          />
        )}

        {/* Labels */}
        {stage >= 2 && (
          <text
            x={policyX / 2}
            y={timelineHeight - 20}
            textAnchor="middle"
            fill={healthForesightColors.accent.light}
            fontSize="14"
            fontWeight="700"
          >
            Pre-Policy Baseline
          </text>
        )}
        {stage >= 4 && (
          <text
            x={(policyX + 550) / 2}
            y={timelineHeight - 20}
            textAnchor="middle"
            fill={healthForesightColors.accent.main}
            fontSize="14"
            fontWeight="700"
            fontStyle="italic"
          >
            Counterfactual
          </text>
        )}
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
