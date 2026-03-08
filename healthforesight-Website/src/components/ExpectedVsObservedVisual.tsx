/**
 * Section 8: Expected vs Observed Overlay
 * Expected appears instantly at low opacity
 * Observed draws across timeline
 * Divergence points pop
 */
import React, { useEffect, useRef, useState } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'

export default function ExpectedVsObservedVisual() {
  const svgRef = useRef<SVGSVGElement>(null)
  const [observedProgress, setObservedProgress] = useState(0)
  const [divergenceVisible, setDivergenceVisible] = useState(false)
  const [hasAnimated, setHasAnimated] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !hasAnimated) {
          setHasAnimated(true)
          // Observed line draws (700-900ms)
          let startTime: number | null = null
          const animate = (timestamp: number) => {
            if (!startTime) startTime = timestamp
            const elapsed = timestamp - startTime
            const progress = Math.min(elapsed / 800, 1)
            setObservedProgress(progress)
            if (progress < 1) {
              requestAnimationFrame(animate)
            } else {
              // Divergence appears after line completes
              setTimeout(() => setDivergenceVisible(true), 200)
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
  const height = 250
  const policyX = 50 + width * 0.4
  const baselineY = height * 0.5

  // Predicted trajectory
  const predictedPath = `M ${policyX} ${baselineY} Q ${policyX + 100} ${baselineY - 40} ${policyX + 200} ${baselineY - 50} T 550 ${baselineY - 60}`

  // Observed trajectory
  const observedPath = `M ${policyX} ${baselineY} Q ${policyX + 100} ${baselineY - 20} ${policyX + 200} ${baselineY - 15} T 550 ${baselineY - 10}`
  const pathLength = 400

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
        viewBox="0 0 600 300"
        preserveAspectRatio="xMidYMid meet"
        sx={{
          width: '100%',
          height: '100%',
        }}
      >
        {/* Expected line (low opacity reference) - bold teal dashed */}
        <path
          d={predictedPath}
          fill="none"
          stroke="#2EC4C6"
          strokeWidth="5"
          strokeDasharray="8,6"
          opacity="0.4"
        />
        <text
          x={550}
          y={baselineY - 60}
          textAnchor="end"
          fill="#2EC4C6"
          fontSize="13"
          fontWeight="600"
          opacity="0.6"
        >
          Expected
        </text>

        {/* Observed line (draws over time) - solid purple */}
        <path
          d={observedPath}
          fill="none"
          stroke="#6366F1"
          strokeWidth="7"
          strokeDasharray={`${observedProgress * pathLength} ${pathLength}`}
          opacity="1"
        />
        {observedProgress > 0.3 && (
          <text
            x={550}
            y={baselineY - 10}
            textAnchor="end"
            fill="#FFFFFF"
            fontSize="15"
            fontWeight="700"
          >
            Observed
          </text>
        )}

        {/* Divergence point - bright orange with glow */}
        {divergenceVisible && (
          <g>
            <circle
              cx={divergenceX}
              cy={divergenceY}
              r="14"
              fill="#E6A23C"
              opacity="1"
              stroke="#FFFFFF"
              strokeWidth="3"
              style={{ transition: 'opacity 150ms ease-out' }}
            >
              <animate
                attributeName="r"
                values="14;18;14"
                dur="0.6s"
                repeatCount="1"
              />
            </circle>
            <line
              x1={divergenceX}
              y1={baselineY - 50}
              x2={divergenceX}
              y2={divergenceY + 25}
              stroke="#E6A23C"
              strokeWidth="3"
              strokeDasharray="4,4"
              opacity="0.8"
            />
            <text
              x={divergenceX}
              y={baselineY - 65}
              textAnchor="middle"
              fill="#FFFFFF"
              fontSize="14"
              fontWeight="700"
            >
              Divergence
            </text>
          </g>
        )}

        {/* Policy date marker */}
        <line
          x1={policyX}
          y1="50"
          x2={policyX}
          y2={height}
          stroke="#9CA3AF"
          strokeWidth="3"
          strokeDasharray="5,5"
          opacity="0.6"
        />
        <text
          x={policyX}
          y="40"
          textAnchor="middle"
          fill="#FFFFFF"
          fontSize="13"
          fontWeight="600"
        >
          Policy Start
        </text>
      </Box>
    </Box>
  )
}
