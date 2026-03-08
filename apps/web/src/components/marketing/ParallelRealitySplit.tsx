/**
 * How It Works Section 4: Parallel Reality Split
 * Two synchronized lanes showing baseline vs observed
 */
import React, { useEffect, useState } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../../theme/healthForesightTheme'

export default function ParallelRealitySplit() {
  const [dividerPosition, setDividerPosition] = useState(0)
  const [deltasVisible, setDeltasVisible] = useState(false)
  const [hasAnimated, setHasAnimated] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !hasAnimated) {
          setHasAnimated(true)
          // Divider slides in
          let startTime: number | null = null
          const animate = (timestamp: number) => {
            if (!startTime) startTime = timestamp
            const elapsed = timestamp - startTime
            const progress = Math.min(elapsed / 1000, 1)
            setDividerPosition(progress)
            if (progress >= 1) {
              setTimeout(() => setDeltasVisible(true), 300)
            } else {
              requestAnimationFrame(animate)
            }
          }
          requestAnimationFrame(animate)
        }
      },
      { threshold: 0.3 }
    )

    const element = document.getElementById('parallel-reality')
    if (element) {
      observer.observe(element)
    }

    return () => observer.disconnect()
  }, [hasAnimated])

  const width = 500
  const height = 300
  const dividerX = 50 + dividerPosition * 450
  const laneWidth = 250

  // Baseline trajectory (flat)
  const baselinePath = `M 50 ${height / 2} L ${dividerX} ${height / 2}`

  // Observed trajectory (slight decline after policy)
  const observedPath = `M ${dividerX} ${height / 2} Q ${dividerX + 100} ${height / 2 + 20} ${dividerX + 200} ${height / 2 + 15} T 550 ${height / 2 + 10}`

  // Divergence point
  const divergenceX = dividerX + 150
  const divergenceY = height / 2 + 12

  return (
    <Box
      id="parallel-reality"
      sx={{
        width: '100%',
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: 2,
      }}
    >
      <Box
        component="svg"
        viewBox="0 0 600 400"
        sx={{
          width: '100%',
          height: '100%',
          maxHeight: '400px',
        }}
      >
        {/* Lane A: Baseline world */}
        <g opacity={dividerPosition > 0.2 ? 1 : 0}>
          <rect
            x="0"
            y="0"
            width={dividerX}
            height={height}
            fill={healthForesightColors.neutral.background}
            opacity="0.6"
          />
          <path
            d={baselinePath}
            fill="none"
            stroke="#9CA3AF"
            strokeWidth="5"
            strokeDasharray="8,6"
            opacity="1"
          />
          <text
            x={dividerX / 2}
            y="30"
            textAnchor="middle"
            fill="#FFFFFF"
            fontSize="16"
            fontWeight="700"
          >
            Baseline World
          </text>
        </g>

        {/* Lane B: Observed world */}
        <g opacity={dividerPosition > 0.5 ? 1 : 0}>
          <rect
            x={dividerX}
            y="0"
            width={600 - dividerX}
            height={height}
            fill={healthForesightColors.accent.main + '15'}
            opacity="0.6"
          />
          <path
            d={observedPath}
            fill="none"
            stroke="#6366F1"
            strokeWidth="6"
            opacity="1"
          />
          <text
            x={dividerX + (600 - dividerX) / 2}
            y="30"
            textAnchor="middle"
            fill="#FFFFFF"
            fontSize="16"
            fontWeight="700"
          >
            Observed World
          </text>
        </g>

        {/* Divider */}
        <line
          x1={dividerX}
          y1="0"
          x2={dividerX}
          y2={height}
          stroke="#FFFFFF"
          strokeWidth="5"
          strokeDasharray="10,6"
          opacity={dividerPosition > 0.1 ? 1 : 0}
        />

        {/* Delta indicators */}
        {deltasVisible && (
          <g>
            <circle
              cx={divergenceX}
              cy={divergenceY}
              r="14"
              fill="#E6A23C"
              opacity="1"
              stroke="#FFFFFF"
              strokeWidth="3"
            />
            <text
              x={divergenceX}
              y={divergenceY - 25}
              textAnchor="middle"
              fill="#FFFFFF"
              fontSize="15"
              fontWeight="700"
            >
              -12%
            </text>
          </g>
        )}

        {/* Policy marker */}
        <line
          x1={dividerX}
          y1="50"
          x2={dividerX}
          y2={height}
          stroke="#6366F1"
          strokeWidth="4"
          opacity={dividerPosition > 0.1 ? 1 : 0}
        />
        <text
          x={dividerX}
          y="40"
          textAnchor="middle"
          fill="#FFFFFF"
          fontSize="14"
          fontWeight="700"
          opacity={dividerPosition > 0.1 ? 1 : 0}
        >
          Policy Start
        </text>
      </Box>
    </Box>
  )
}
