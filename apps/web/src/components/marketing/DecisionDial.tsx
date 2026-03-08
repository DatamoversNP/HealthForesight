/**
 * How It Works Section 3: Decision Dial
 * Circular dial with three zones and pointer
 */
import React, { useEffect, useState } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../../theme/healthForesightTheme'

export default function DecisionDial() {
  const [pointerAngle, setPointerAngle] = useState(0)
  const [confidenceWidth, setConfidenceWidth] = useState(60)
  const [hasAnimated, setHasAnimated] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !hasAnimated) {
          setHasAnimated(true)
          // Pointer moves smoothly
          let startTime: number | null = null
          const animate = (timestamp: number) => {
            if (!startTime) startTime = timestamp
            const elapsed = timestamp - startTime
            const progress = Math.min(elapsed / 1200, 1)
            // Pointer moves from -60° to 30° (green zone)
            setPointerAngle(-60 + progress * 90)
            // Confidence band tightens slightly
            setConfidenceWidth(60 - progress * 20)
            if (progress < 1) {
              requestAnimationFrame(animate)
            }
          }
          requestAnimationFrame(animate)
        }
      },
      { threshold: 0.3 }
    )

    const element = document.getElementById('decision-dial')
    if (element) {
      observer.observe(element)
    }

    return () => observer.disconnect()
  }, [hasAnimated])

  const centerX = 300
  const centerY = 200
  const radius = 120
  const pointerLength = 80

  const pointerX = centerX + Math.cos((pointerAngle * Math.PI) / 180) * pointerLength
  const pointerY = centerY + Math.sin((pointerAngle * Math.PI) / 180) * pointerLength

  return (
    <Box
      id="decision-dial"
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
        {/* Green zone (within expectation) */}
        <path
          d={`M ${centerX} ${centerY} 
              A ${radius} ${radius} 0 0 1 ${centerX + radius * Math.cos((30 * Math.PI) / 180)} ${centerY + radius * Math.sin((30 * Math.PI) / 180)}
              L ${centerX} ${centerY} Z`}
          fill={healthForesightColors.semantic.positive + '30'}
          stroke={healthForesightColors.semantic.positive}
          strokeWidth="2"
          opacity="0.6"
        />

        {/* Amber zone (sensitivity) */}
        <path
          d={`M ${centerX} ${centerY} 
              A ${radius} ${radius} 0 0 1 ${centerX + radius * Math.cos((90 * Math.PI) / 180)} ${centerY + radius * Math.sin((90 * Math.PI) / 180)}
              L ${centerX} ${centerY} Z`}
          fill={healthForesightColors.amber.main + '30'}
          stroke={healthForesightColors.amber.main}
          strokeWidth="2"
          opacity="0.6"
        />

        {/* Gray zone (insufficient confidence) */}
        <path
          d={`M ${centerX} ${centerY} 
              A ${radius} ${radius} 0 0 1 ${centerX + radius * Math.cos((150 * Math.PI) / 180)} ${centerY + radius * Math.sin((150 * Math.PI) / 180)}
              L ${centerX} ${centerY} Z`}
          fill={healthForesightColors.neutral.mid + '20'}
          stroke={healthForesightColors.neutral.mid}
          strokeWidth="2"
          opacity="0.4"
        />

        {/* Confidence band arc */}
        <path
          d={`M ${centerX + Math.cos(((pointerAngle - confidenceWidth / 2) * Math.PI) / 180) * radius} ${centerY + Math.sin(((pointerAngle - confidenceWidth / 2) * Math.PI) / 180) * radius}
              A ${radius} ${radius} 0 0 1 ${centerX + Math.cos(((pointerAngle + confidenceWidth / 2) * Math.PI) / 180) * radius} ${centerY + Math.sin(((pointerAngle + confidenceWidth / 2) * Math.PI) / 180) * radius}`}
          fill="none"
          stroke={healthForesightColors.accent.main}
          strokeWidth="4"
          opacity="0.8"
        />

        {/* Pointer */}
        <line
          x1={centerX}
          y1={centerY}
          x2={pointerX}
          y2={pointerY}
          stroke={healthForesightColors.primary.main}
          strokeWidth="5"
          strokeLinecap="round"
        />
        <circle
          cx={pointerX}
          cy={pointerY}
          r="8"
          fill={healthForesightColors.primary.main}
        />

        {/* Center circle */}
        <circle
          cx={centerX}
          cy={centerY}
          r="12"
          fill="#FFFFFF"
          stroke={healthForesightColors.primary.main}
          strokeWidth="3"
        />

        {/* Zone labels */}
        <text
          x={centerX + Math.cos((15 * Math.PI) / 180) * (radius + 30)}
          y={centerY + Math.sin((15 * Math.PI) / 180) * (radius + 30)}
          textAnchor="middle"
          fill={healthForesightColors.semantic.positive}
          fontSize="12"
          fontWeight="700"
        >
          Within Expectation
        </text>
        <text
          x={centerX + Math.cos((60 * Math.PI) / 180) * (radius + 30)}
          y={centerY + Math.sin((60 * Math.PI) / 180) * (radius + 30)}
          textAnchor="middle"
          fill={healthForesightColors.amber.main}
          fontSize="12"
          fontWeight="700"
        >
          Sensitivity Zone
        </text>
        <text
          x={centerX + Math.cos((120 * Math.PI) / 180) * (radius + 30)}
          y={centerY + Math.sin((120 * Math.PI) / 180) * (radius + 30)}
          textAnchor="middle"
          fill={healthForesightColors.neutral.mid}
          fontSize="12"
          fontWeight="700"
        >
          Insufficient Confidence
        </text>
      </Box>
    </Box>
  )
}
