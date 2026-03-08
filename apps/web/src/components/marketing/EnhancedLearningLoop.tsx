/**
 * Section 8: Enhanced Learning Loop
 * Progressive clarity, uncertainty reduction, tightening cycles
 */
import React, { useEffect, useRef, useState } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../../theme/healthForesightTheme'

export default function EnhancedLearningLoop() {
  const svgRef = useRef<SVGSVGElement>(null)
  const [cycleCount, setCycleCount] = useState(0)
  const [angle, setAngle] = useState(0)
  const animationRef = useRef<number>()

  useEffect(() => {
    const animate = () => {
      setAngle((prev) => {
        const newAngle = prev + 0.015
        if (newAngle >= Math.PI * 2) {
          setCycleCount((c) => c + 1)
          return 0
        }
        return newAngle
      })
      animationRef.current = requestAnimationFrame(animate)
    }
    animationRef.current = requestAnimationFrame(animate)

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [])

  const centerX = 300
  const centerY = 200
  const baseRadius = 110
  // Radius tightens with each cycle (max 3 cycles shown)
  const currentRadius = baseRadius - Math.min(cycleCount, 3) * 8

  const stages = [
    { label: 'Predict', angle: -Math.PI / 2 },
    { label: 'Observe', angle: 0 },
    { label: 'Learn', angle: Math.PI / 2 },
    { label: 'Improve', angle: Math.PI },
  ]

  // Uncertainty band (reduces with cycles)
  const uncertaintyReduction = Math.min(cycleCount / 3, 1)
  const uncertaintyWidth = 30 * (1 - uncertaintyReduction)

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
        <defs>
          <filter id="stageGlow">
            <feGaussianBlur stdDeviation="4" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Uncertainty band (outer ring, shrinks) */}
        {uncertaintyWidth > 5 && (
          <circle
            cx={centerX}
            cy={centerY}
            r={currentRadius + uncertaintyWidth}
            fill="none"
            stroke={healthForesightColors.neutral.mid}
            strokeWidth="3"
            strokeDasharray="6,4"
            opacity="0.5"
          />
        )}

        {/* Main loop circle */}
        <circle
          cx={centerX}
          cy={centerY}
          r={currentRadius}
          fill="none"
          stroke={healthForesightColors.primary.light}
          strokeWidth="7"
          opacity="1"
        />

        {/* Stages */}
        {stages.map((stage, idx) => {
          const x = centerX + Math.cos(stage.angle) * currentRadius
          const y = centerY + Math.sin(stage.angle) * currentRadius
          const isActive = Math.abs(angle - stage.angle) < 0.3 || Math.abs(angle - stage.angle - Math.PI * 2) < 0.3

          return (
            <g key={idx}>
              <circle
                cx={x}
                cy={y}
                r={isActive ? 32 : 28}
                fill={healthForesightColors.primary.light}
                filter="url(#stageGlow)"
                opacity="1"
                stroke="#FFFFFF"
                strokeWidth="3"
              />
              <circle
                cx={x}
                cy={y}
                r={isActive ? 26 : 22}
                fill="#FFFFFF"
              />
              <text
                x={x}
                y={y + 5}
                textAnchor="middle"
                fill={healthForesightColors.primary.main}
                fontSize={isActive ? 13 : 12}
                fontWeight="700"
              >
                {stage.label}
              </text>
            </g>
          )
        })}

        {/* Flowing indicator */}
        <circle
          cx={centerX + Math.cos(angle - Math.PI / 2) * currentRadius}
          cy={centerY + Math.sin(angle - Math.PI / 2) * currentRadius}
          r="11"
          fill={healthForesightColors.accent.light}
          filter="url(#stageGlow)"
          opacity="1"
          stroke="#FFFFFF"
          strokeWidth="2.5"
        />

        {/* Center - cycle counter */}
        <circle
          cx={centerX}
          cy={centerY}
          r="35"
          fill={healthForesightColors.primary.main}
          opacity="0.2"
        />
        <text
          x={centerX}
          y={centerY + 7}
          textAnchor="middle"
          fill={healthForesightColors.primary.main}
          fontSize="20"
          fontWeight="700"
        >
          {cycleCount}
        </text>
        <text
          x={centerX}
          y={centerY + 24}
          textAnchor="middle"
          fill={healthForesightColors.neutral.mid}
          fontSize="11"
          fontWeight="600"
        >
          cycles
        </text>

        {/* Clarity indicator (increases) */}
        <text
          x={centerX}
          y="50"
          textAnchor="middle"
          fill={healthForesightColors.accent.light}
          fontSize="14"
          fontWeight="700"
        >
          Clarity: {Math.min(Math.round(uncertaintyReduction * 100), 100)}%
        </text>
      </Box>
    </Box>
  )
}
