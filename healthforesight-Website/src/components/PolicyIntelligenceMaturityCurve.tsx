/**
 * Policy Intelligence Maturity Curve
 * Horizontal maturity curve: Reactive UM → Predictive Policy Intelligence
 */
import React, { useEffect, useState } from 'react'
import { Box, Typography } from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'

export default function PolicyIntelligenceMaturityCurve() {
  const [curveProgress, setCurveProgress] = useState(0)
  const [milestonesVisible, setMilestonesVisible] = useState<boolean[]>([])

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          // Curve draws
          let progress = 0
          const interval = setInterval(() => {
            progress += 0.01
            setCurveProgress(Math.min(progress, 1))
            if (progress >= 1) clearInterval(interval)
          }, 20)

          // Milestones appear sequentially
          [0, 1, 2, 3].forEach((idx) => {
            setTimeout(() => {
              setMilestonesVisible((prev) => {
                const newMilestones = [...prev]
                newMilestones[idx] = true
                return newMilestones
              })
            }, idx * 300)
          })
        }
      },
      { threshold: 0.2 }
    )

    const element = document.getElementById('maturity-curve')
    if (element) observer.observe(element)

    return () => observer.disconnect()
  }, [])

  const width = 800
  const height = 300
  const curveY = height / 2

  // Maturity curve path
  const curvePath = `M 100 ${curveY} 
    Q ${width * 0.25} ${curveY - 40} 
    ${width * 0.5} ${curveY - 30}
    T ${width - 100} ${curveY - 20}`

  const milestones = [
    { label: 'Static rules', x: 150, y: curveY },
    { label: 'Behavioral monitoring', x: 350, y: curveY - 20 },
    { label: 'Causal measurement', x: 550, y: curveY - 25 },
    { label: 'Adaptive governance', x: 750, y: curveY - 20 },
  ]

  return (
    <Box
      id="maturity-curve"
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
          maxHeight: '350px',
        }}
      >
        {/* Curve */}
        <path
          d={curvePath}
          fill="none"
          stroke={healthForesightColors.primary.main}
          strokeWidth="4"
          strokeDasharray={`${curveProgress * 700} 700`}
        />

        {/* Start label */}
        <text
          x={100}
          y={curveY + 30}
          fill={healthForesightColors.neutral.dark}
          fontSize="14"
          fontWeight="700"
        >
          Reactive UM
        </text>

        {/* End label */}
        <text
          x={width - 100}
          y={curveY - 30}
          textAnchor="end"
          fill={healthForesightColors.neutral.dark}
          fontSize="14"
          fontWeight="700"
        >
          Predictive Policy Intelligence
        </text>

        {/* Milestones */}
        {milestones.map((milestone, idx) => (
          <g key={idx} opacity={milestonesVisible[idx] ? 1 : 0}>
            <circle
              cx={milestone.x}
              cy={milestone.y}
              r="6"
              fill={healthForesightColors.accent.main}
              stroke="#FFFFFF"
              strokeWidth="2"
            />
            <text
              x={milestone.x}
              y={milestone.y - 15}
              textAnchor="middle"
              fill={healthForesightColors.neutral.dark}
              fontSize="12"
              fontWeight="600"
            >
              {milestone.label}
            </text>
          </g>
        ))}
      </Box>
    </Box>
  )
}
