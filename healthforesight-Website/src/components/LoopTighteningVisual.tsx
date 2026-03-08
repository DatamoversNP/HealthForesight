/**
 * Section 10: Loop Tightening
 * Same loop, uncertainty band shrinks over 3 cycles
 * Total duration 2.5-3.5s, then stop
 */
import React, { useEffect, useRef, useState } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../../theme/healthForesightTheme'

export default function LoopTighteningVisual() {
  const svgRef = useRef<SVGSVGElement>(null)
  const [cycle, setCycle] = useState(0) // 0, 1, 2
  const [hasAnimated, setHasAnimated] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !hasAnimated) {
          setHasAnimated(true)
          // Cycle 1: wide band
          setTimeout(() => setCycle(1), 800)
          // Cycle 2: narrower band
          setTimeout(() => setCycle(2), 1800)
          // Cycle 3: narrow band + confidence label
          setTimeout(() => setCycle(3), 2800)
        }
      },
      { threshold: 0.3 }
    )

    if (svgRef.current) {
      observer.observe(svgRef.current)
    }

    return () => observer.disconnect()
  }, [hasAnimated])

  const centerX = 300
  const centerY = 200
  const baseRadius = 100
  const uncertaintyWidths = [30, 18, 8, 3] // Cycle 0, 1, 2, 3
  const currentUncertainty = uncertaintyWidths[cycle] || 30

  const stages = [
    { label: 'Predict', angle: -Math.PI / 2 },
    { label: 'Observe', angle: 0 },
    { label: 'Learn', angle: Math.PI / 2 },
    { label: 'Improve', angle: Math.PI },
  ]

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
        viewBox="0 0 600 400"
        preserveAspectRatio="xMidYMid meet"
        sx={{
          width: '100%',
          height: '100%',
        }}
      >
        {/* Uncertainty band (shrinks) - subtle */}
        <circle
          cx={centerX}
          cy={centerY}
          r={baseRadius + currentUncertainty}
          fill="none"
          stroke="#9CA3AF"
          strokeWidth="2"
          strokeDasharray="5,5"
          opacity="0.3"
          style={{ transition: 'r 800ms ease-out' }}
        />

        {/* Main loop - bright purple, thicker */}
        <circle
          cx={centerX}
          cy={centerY}
          r={baseRadius}
          fill="none"
          stroke="#6366F1"
          strokeWidth="6"
          opacity="1"
        />

        {/* Stages - directional activation sequence */}
        {stages.map((stage, idx) => {
          const x = centerX + Math.cos(stage.angle) * baseRadius
          const y = centerY + Math.sin(stage.angle) * baseRadius
          const isActive = cycle >= idx + 1
          return (
            <g key={idx}>
              <circle
                cx={x}
                cy={y}
                r={isActive ? "32" : "30"}
                fill="#6366F1"
                opacity="1"
                style={{ transition: 'r 200ms ease-out' }}
              />
              <circle
                cx={x}
                cy={y}
                r="22"
                fill="#FFFFFF"
              />
              <text
                x={x}
                y={y + 6}
                textAnchor="middle"
                fill="#6366F1"
                fontSize="12"
                fontWeight="700"
              >
                {stage.label}
              </text>
            </g>
          )
        })}

        {/* Confidence label (appears at cycle 3) - bright teal */}
        {cycle >= 3 && (
          <text
            x={centerX}
            y="50"
            textAnchor="middle"
            fill="#2EC4C6"
            fontSize="16"
            fontWeight="700"
            style={{ transition: 'opacity 300ms ease-out' }}
          >
            Confidence ↑
          </text>
        )}
      </Box>
    </Box>
  )
}
