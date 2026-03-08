/**
 * How It Works Section 5: Behavioral Flow Lanes
 * Horizontal lanes showing behavioral responses over time
 * Shows direction, magnitude, and type of behavior - not just entity relationships
 */
import React, { useEffect, useState } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'

export default function BehavioralFlowLanes() {
  const [animationProgress, setAnimationProgress] = useState(0)
  const [labelsVisible, setLabelsVisible] = useState(false)
  const [hasAnimated, setHasAnimated] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !hasAnimated) {
          setHasAnimated(true)
          // Animate paths drawing
          let startTime: number | null = null
          const animate = (timestamp: number) => {
            if (!startTime) startTime = timestamp
            const elapsed = timestamp - startTime
            const progress = Math.min(elapsed / 1500, 1)
            setAnimationProgress(progress)
            if (progress >= 1) {
              setTimeout(() => setLabelsVisible(true), 300)
            } else {
              requestAnimationFrame(animate)
            }
          }
          requestAnimationFrame(animate)
        }
      },
      { threshold: 0.3 }
    )

    const element = document.getElementById('behavioral-flow-lanes')
    if (element) {
      observer.observe(element)
    }

    return () => observer.disconnect()
  }, [hasAnimated])

  const width = 500
  const height = 300
  const policyX = 150
  const laneHeight = 80
  const startY = 80

  // Three horizontal lanes
  const lanes = [
    {
      label: 'Providers',
      y: startY,
      color: healthForesightColors.primary.main,
      beforePath: `M 50 ${startY} L ${policyX} ${startY}`,
      afterPath: `M ${policyX} ${startY} Q ${policyX + 80} ${startY - 15} ${policyX + 160} ${startY - 10} T 550 ${startY - 5}`,
      responseLabel: 'Adapted',
      responseX: policyX + 120,
      responseY: startY - 20,
      thickness: 5,
    },
    {
      label: 'Patients',
      y: startY + laneHeight,
      color: healthForesightColors.accent.main,
      beforePath: `M 50 ${startY + laneHeight} L ${policyX} ${startY + laneHeight}`,
      afterPath: `M ${policyX} ${startY + laneHeight} Q ${policyX + 100} ${startY + laneHeight + 20} ${policyX + 200} ${startY + laneHeight + 15} T 550 ${startY + laneHeight + 10}`,
      responseLabel: 'Substituted',
      responseX: policyX + 140,
      responseY: startY + laneHeight + 35,
      thickness: 4,
    },
    {
      label: 'Sites',
      y: startY + laneHeight * 2,
      color: healthForesightColors.amber.main,
      beforePath: `M 50 ${startY + laneHeight * 2} L ${policyX} ${startY + laneHeight * 2}`,
      afterPath: `M ${policyX} ${startY + laneHeight * 2} Q ${policyX + 60} ${startY + laneHeight * 2 - 10} ${policyX + 120} ${startY + laneHeight * 2 - 8} T 550 ${startY + laneHeight * 2 - 5}`,
      responseLabel: 'Shifted',
      responseX: policyX + 100,
      responseY: startY + laneHeight * 2 - 18,
      thickness: 6,
    },
  ]

  const pathLength = 400

  return (
    <Box
      id="behavioral-flow-lanes"
      sx={{
        width: '100%',
        maxWidth: { xs: '100%', md: '800px' },
        height: { xs: '250px', md: '400px' },
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: { xs: 2, md: 3 },
        p: 2,
      }}
    >
      <Box
        component="svg"
        viewBox="0 0 600 400"
        preserveAspectRatio="xMidYMid meet"
        sx={{
          width: '100%',
          height: '100%',
        }}
      >
        {/* Policy event marker */}
        <line
          x1={policyX}
          y1="50"
          x2={policyX}
          y2={height}
          stroke="#6366F1"
          strokeWidth="4"
          opacity="1"
        />
        <text
          x={policyX}
          y="40"
          textAnchor="middle"
          fill="#FFFFFF"
          fontSize="13"
          fontWeight="700"
        >
          Policy Event
        </text>

        {/* Lanes */}
        {lanes.map((lane, idx) => {
          const beforeProgress = Math.min(animationProgress * 1.5, 1)
          const afterProgress = animationProgress > 0.3 ? (animationProgress - 0.3) / 0.7 : 0

          return (
            <g key={idx}>
              {/* Lane label */}
              <text
                x="50"
                y={lane.y + 5}
                fill="#FFFFFF"
                fontSize="14"
                fontWeight="700"
              >
                {lane.label}
              </text>

              {/* Before policy - straight line */}
              <path
                d={lane.beforePath}
                fill="none"
                stroke="#9CA3AF"
                strokeWidth={lane.thickness}
                strokeDasharray={`${beforeProgress * 100} 100`}
                opacity="0.8"
              />

              {/* After policy - bent/split line */}
              <path
                d={lane.afterPath}
                fill="none"
                stroke={lane.color}
                strokeWidth={lane.thickness + 1}
                strokeDasharray={`${afterProgress * pathLength} ${pathLength}`}
                opacity="1"
              />

              {/* Response label */}
              {labelsVisible && afterProgress > 0.5 && (
                <g>
                  <rect
                    x={lane.responseX - (lane.responseLabel.length * 3.5)}
                    y={lane.responseY - 12}
                    width={lane.responseLabel.length * 7}
                    height="18"
                    rx="4"
                    fill={lane.color}
                    opacity="0.9"
                  />
                  <text
                    x={lane.responseX}
                    y={lane.responseY}
                    textAnchor="middle"
                    fill="#FFFFFF"
                    fontSize="11"
                    fontWeight="700"
                  >
                    {lane.responseLabel}
                  </text>
                </g>
              )}
            </g>
          )
        })}

        {/* Time axis */}
        <text
          x="50"
          y="30"
          fill="#FFFFFF"
          fontSize="13"
          fontWeight="600"
        >
          Time →
        </text>
      </Box>
    </Box>
  )
}
