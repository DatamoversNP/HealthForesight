/**
 * Visual 5: Policy Whiplash Loop
 * Circular loop: Policy → Reported Savings → Behavioral Response → Cost Spike → Policy Reversal
 */
import React, { useEffect, useState } from 'react'
import { Box, Typography } from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'

export default function PolicyWhiplashLoop() {
  const [dotPosition, setDotPosition] = useState(0)

  useEffect(() => {
    let interval: NodeJS.Timeout | null = null

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          // Dot travels around loop continuously (8-10s loop)
          let position = 0
          interval = setInterval(() => {
            position += 0.01
            setDotPosition(position % 1)
          }, 80)
        }
      },
      { threshold: 0.2 }
    )

    const element = document.getElementById('policy-whiplash-loop')
    if (element) observer.observe(element)

    return () => {
      observer.disconnect()
      if (interval) clearInterval(interval)
    }
  }, [])

  const width = 500
  const height = 500
  const centerX = width / 2
  const centerY = height / 2
  const radius = 150

  // Calculate positions for 5 stages around circle
  const stages = [
    { label: 'Policy', angle: -90, color: healthForesightColors.primary.main },
    { label: 'Reported Savings', angle: -18, color: healthForesightColors.accent.main },
    { label: 'Behavioral Response', angle: 54, color: healthForesightColors.neutral.mid },
    { label: 'Cost Spike', angle: 126, color: healthForesightColors.amber.main },
    { label: 'Policy Reversal', angle: 198, color: healthForesightColors.amber.main },
  ]

  const getPosition = (angle: number) => {
    const radians = ((angle - 90) * Math.PI) / 180
    return {
      x: centerX + Math.cos(radians) * radius,
      y: centerY + Math.sin(radians) * radius,
    }
  }

  // Loop path
  const loopPath = stages
    .map((stage, idx) => {
      const pos = getPosition(stage.angle)
      return idx === 0 ? `M ${pos.x} ${pos.y}` : `L ${pos.x} ${pos.y}`
    })
    .join(' ') + ' Z'

  // Dot position on loop
  const dotAngle = -90 + dotPosition * 360
  const dotPos = getPosition(dotAngle)

  return (
    <Box
      id="policy-whiplash-loop"
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
          maxHeight: '550px',
        }}
      >
        {/* Arrow marker - must be defined before use */}
        <defs>
          <marker
            id="arrowhead-loop"
            markerWidth="10"
            markerHeight="10"
            refX="9"
            refY="3"
            orient="auto"
          >
            <polygon
              points="0 0, 10 3, 0 6"
              fill={healthForesightColors.neutral.mid}
            />
          </marker>
        </defs>

        {/* Loop path */}
        <path
          d={loopPath}
          fill="none"
          stroke={healthForesightColors.neutral.mid}
          strokeWidth="3"
          opacity={0.3}
        />

        {/* Stages */}
        {stages.map((stage, idx) => {
          const pos = getPosition(stage.angle)
          const isWarning = stage.label === 'Cost Spike' || stage.label === 'Policy Reversal'
          return (
            <g key={idx}>
              <circle
                cx={pos.x}
                cy={pos.y}
                r={isWarning ? 12 : 10}
                fill={stage.color}
                stroke="#FFFFFF"
                strokeWidth="2"
              />
              <text
                x={pos.x}
                y={pos.y - 25}
                textAnchor="middle"
                fill={stage.color}
                fontSize="12"
                fontWeight="700"
              >
                {stage.label}
              </text>
              {/* Arrow to next stage */}
              {idx < stages.length - 1 && (
                <line
                  x1={pos.x}
                  y1={pos.y}
                  x2={getPosition(stages[idx + 1].angle).x}
                  y2={getPosition(stages[idx + 1].angle).y}
                  stroke={healthForesightColors.neutral.mid}
                  strokeWidth="2"
                  markerEnd="url(#arrowhead-loop)"
                  opacity={0.5}
                />
              )}
            </g>
          )
        })}

        {/* Arrow from last to first */}
        <line
          x1={getPosition(stages[stages.length - 1].angle).x}
          y1={getPosition(stages[stages.length - 1].angle).y}
          x2={getPosition(stages[0].angle).x}
          y2={getPosition(stages[0].angle).y}
          stroke={healthForesightColors.neutral.mid}
          strokeWidth="2"
          markerEnd="url(#arrowhead-loop)"
          opacity={0.5}
        />

        {/* Traveling dot */}
        <circle
          cx={dotPos.x}
          cy={dotPos.y}
          r="6"
          fill={healthForesightColors.primary.main}
          stroke="#FFFFFF"
          strokeWidth="2"
        />
      </Box>
    </Box>
  )
}
