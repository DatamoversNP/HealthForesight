/**
 * Solution 4: Institutional Learning Loop Visual
 * Circular learning: Predict → Observe → Learn → Improve
 */
import React, { useEffect, useRef, useState } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'

export default function LearningLoopVisual() {
  const svgRef = useRef<SVGSVGElement>(null)
  const animationRef = useRef<number>()
  const flowCircleRef = useRef<SVGCircleElement>(null)
  const [loopCount, setLoopCount] = useState(0)

  useEffect(() => {
    const centerX = 300
    const centerY = 200
    const radius = 100

    const animate = () => {
      if (flowCircleRef.current) {
        let angle = 0
        const speed = 0.02

        const move = () => {
          angle += speed
          if (angle >= Math.PI * 2) {
            angle = 0
            setLoopCount((prev) => prev + 1)
          }

          const x = centerX + Math.cos(angle - Math.PI / 2) * radius
          const y = centerY + Math.sin(angle - Math.PI / 2) * radius
          
          if (flowCircleRef.current) {
            flowCircleRef.current.setAttribute('cx', String(x))
            flowCircleRef.current.setAttribute('cy', String(y))
          }

          animationRef.current = requestAnimationFrame(move)
        }

        move()
      }
    }

    const timeout = setTimeout(animate, 500)

    return () => {
      clearTimeout(timeout)
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [])

  const centerX = 300
  const centerY = 200
  const radius = 100

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
          <linearGradient id="predictGradient">
            <stop offset="0%" stopColor={healthForesightColors.primary.main} stopOpacity="1" />
            <stop offset="100%" stopColor={healthForesightColors.primary.dark} stopOpacity="1" />
          </linearGradient>
          <linearGradient id="observeGradient">
            <stop offset="0%" stopColor={healthForesightColors.accent.main} stopOpacity="1" />
            <stop offset="100%" stopColor={healthForesightColors.accent.dark} stopOpacity="1" />
          </linearGradient>
          <linearGradient id="learnGradient">
            <stop offset="0%" stopColor={healthForesightColors.amber.main} stopOpacity="1" />
            <stop offset="100%" stopColor={healthForesightColors.amber.dark} stopOpacity="1" />
          </linearGradient>
          <linearGradient id="improveGradient">
            <stop offset="0%" stopColor={healthForesightColors.primary.main} stopOpacity="1" />
            <stop offset="100%" stopColor={healthForesightColors.accent.main} stopOpacity="1" />
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="4" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="shadow">
            <feDropShadow dx="0" dy="4" stdDeviation="6" floodOpacity="0.3" />
          </filter>
        </defs>


        {/* Node 1: Predict */}
        <g>
          <circle
            cx={centerX}
            cy={centerY - radius}
            r="45"
            fill="url(#predictGradient)"
            filter="url(#shadow)"
            opacity={0.9 + loopCount * 0.02}
          />
          <circle
            cx={centerX}
            cy={centerY - radius}
            r="40"
            fill="none"
            stroke="#FFFFFF"
            strokeWidth="2"
            opacity="0.3"
          />
          <text
            x={centerX}
            y={centerY - radius - 8}
            textAnchor="middle"
            fill="#FFFFFF"
            fontSize="16"
            fontWeight="700"
          >
            Predict
          </text>
        </g>

        {/* Node 2: Observe */}
        <g>
          <circle
            cx={centerX + radius}
            cy={centerY}
            r="45"
            fill="url(#observeGradient)"
            filter="url(#shadow)"
            opacity={0.9 + loopCount * 0.02}
          />
          <circle
            cx={centerX + radius}
            cy={centerY}
            r="40"
            fill="none"
            stroke="#FFFFFF"
            strokeWidth="2"
            opacity="0.3"
          />
          <text
            x={centerX + radius}
            y={centerY + 6}
            textAnchor="middle"
            fill="#FFFFFF"
            fontSize="16"
            fontWeight="700"
          >
            Observe
          </text>
        </g>

        {/* Node 3: Learn */}
        <g>
          <circle
            cx={centerX}
            cy={centerY + radius}
            r="45"
            fill="url(#learnGradient)"
            filter="url(#shadow)"
            opacity={0.9 + loopCount * 0.02}
          />
          <circle
            cx={centerX}
            cy={centerY + radius}
            r="40"
            fill="none"
            stroke="#FFFFFF"
            strokeWidth="2"
            opacity="0.3"
          />
          <text
            x={centerX}
            y={centerY + radius + 8}
            textAnchor="middle"
            fill="#FFFFFF"
            fontSize="16"
            fontWeight="700"
          >
            Learn
          </text>
        </g>

        {/* Node 4: Improve */}
        <g>
          <circle
            cx={centerX - radius}
            cy={centerY}
            r="45"
            fill="url(#improveGradient)"
            filter="url(#shadow)"
            opacity={0.9 + loopCount * 0.02}
          />
          <circle
            cx={centerX - radius}
            cy={centerY}
            r="40"
            fill="none"
            stroke="#FFFFFF"
            strokeWidth="2"
            opacity="0.3"
          />
          <text
            x={centerX - radius}
            y={centerY + 6}
            textAnchor="middle"
            fill="#FFFFFF"
            fontSize="16"
            fontWeight="700"
          >
            Improve
          </text>
        </g>

        {/* Circular connection */}
        <circle
          cx={centerX}
          cy={centerY}
          r={radius}
          fill="none"
          stroke={healthForesightColors.primary.main}
          strokeWidth="3"
          strokeDasharray="8,4"
          opacity="0.4"
        />

        {/* Flowing circle */}
        <circle
          ref={flowCircleRef}
          r="10"
          fill={healthForesightColors.primary.main}
          filter="url(#glow)"
          opacity="0.9"
        />

        {/* Center indicator */}
        <circle
          cx={centerX}
          cy={centerY}
          r="20"
          fill={healthForesightColors.primary.main}
          opacity="0.2"
        />
        <text
          x={centerX}
          y={centerY + 5}
          textAnchor="middle"
          fill={healthForesightColors.primary.main}
          fontSize="12"
          fontWeight="700"
        >
          {loopCount}
        </text>
      </Box>
    </Box>
  )
}
