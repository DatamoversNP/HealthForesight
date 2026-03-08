/**
 * Solution 2: Timeline Impact Visual
 * Split timeline: Baseline → Policy Date → Observed Impact
 */
import React, { useEffect, useRef, useState } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../../theme/healthForesightTheme'

export default function TimelineImpactVisual() {
  const svgRef = useRef<SVGSVGElement>(null)
  const [policyDate, setPolicyDate] = useState(0.4) // 40% along timeline

  useEffect(() => {
    const animate = () => {
      // Subtle animation - policy date marker pulses
      let direction = 1
      const animatePolicyMarker = () => {
        setPolicyDate((prev) => {
          const newValue = prev + direction * 0.001
          if (newValue > 0.45) direction = -1
          if (newValue < 0.35) direction = 1
          return Math.max(0.35, Math.min(0.45, newValue))
        })
        requestAnimationFrame(animatePolicyMarker)
      }
      animatePolicyMarker()
    }

    const timeout = setTimeout(animate, 500)
    return () => clearTimeout(timeout)
  }, [])

  const timelineWidth = 500
  const timelineHeight = 300
  const policyX = policyDate * timelineWidth
  const baselineY = timelineHeight * 0.4
  const impactY = timelineHeight * 0.6

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
        <defs>
          <linearGradient id="baselineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={healthForesightColors.neutral.light} stopOpacity="0.3" />
            <stop offset="100%" stopColor={healthForesightColors.neutral.light} stopOpacity="0.1" />
          </linearGradient>
          <linearGradient id="impactGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={healthForesightColors.accent.main} stopOpacity="0.3" />
            <stop offset="100%" stopColor={healthForesightColors.accent.main} stopOpacity="0.1" />
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Background trend line (baseline) */}
        <path
          d={`M 50 ${baselineY} Q 150 ${baselineY - 20} 250 ${baselineY - 10} T ${policyX} ${baselineY}`}
          fill="none"
          stroke={healthForesightColors.neutral.mid}
          strokeWidth="2"
          strokeDasharray="4,4"
          opacity="0.5"
        />

        {/* Policy date marker */}
        <line
          x1={policyX}
          y1="50"
          x2={policyX}
          y2={timelineHeight}
          stroke={healthForesightColors.primary.main}
          strokeWidth="3"
          opacity="0.8"
        />
        <circle
          cx={policyX}
          cy={baselineY}
          r="8"
          fill={healthForesightColors.primary.main}
          filter="url(#glow)"
        />
        <text
          x={policyX}
          y="40"
          textAnchor="middle"
          fill={healthForesightColors.primary.main}
          fontSize="14"
          fontWeight="700"
        >
          Policy Date
        </text>

        {/* Baseline area (before policy) */}
        <path
          d={`M 50 ${baselineY} Q 150 ${baselineY - 20} 250 ${baselineY - 10} T ${policyX} ${baselineY} L ${policyX} ${timelineHeight} L 50 ${timelineHeight} Z`}
          fill="url(#baselineGradient)"
          opacity="0.6"
        />
        <text
          x={policyX / 2}
          y={timelineHeight - 20}
          textAnchor="middle"
          fill={healthForesightColors.neutral.mid}
          fontSize="12"
          fontWeight="600"
        >
          Baseline Trend
        </text>

        {/* Observed impact area (after policy) */}
        <path
          d={`M ${policyX} ${baselineY} Q ${policyX + 100} ${impactY - 30} ${policyX + 200} ${impactY - 20} T 550 ${impactY} L 550 ${timelineHeight} L ${policyX} ${timelineHeight} Z`}
          fill="url(#impactGradient)"
          opacity="0.6"
        />
        <text
          x={(policyX + 550) / 2}
          y={timelineHeight - 20}
          textAnchor="middle"
          fill={healthForesightColors.accent.main}
          fontSize="12"
          fontWeight="600"
        >
          Policy Effect
        </text>

        {/* Impact line (after policy) */}
        <path
          d={`M ${policyX} ${baselineY} Q ${policyX + 100} ${impactY - 30} ${policyX + 200} ${impactY - 20} T 550 ${impactY}`}
          fill="none"
          stroke={healthForesightColors.accent.main}
          strokeWidth="3"
          opacity="0.9"
        />

        {/* Labels */}
        <text
          x="50"
          y="30"
          fill={healthForesightColors.neutral.dark}
          fontSize="14"
          fontWeight="600"
        >
          Time →
        </text>
      </Box>
    </Box>
  )
}
