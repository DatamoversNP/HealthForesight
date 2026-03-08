/**
 * Section 5: Forecast Envelope Visualization
 * Cone of outcomes with confidence bands, not boxes
 */
import React, { useEffect, useRef, useState } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'

export default function ForecastEnvelopeVisual() {
  const svgRef = useRef<SVGSVGElement>(null)
  const [hasAnimated, setHasAnimated] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !hasAnimated) {
          setHasAnimated(true)
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
  const height = 300
  const startX = 50
  const startY = height * 0.5
  const endX = 550
  const midX = (startX + endX) / 2

  // Confidence bands (cone shape)
  const upperBand = [
    { x: startX, y: startY - 20 },
    { x: midX, y: startY - 60 },
    { x: endX, y: startY - 80 },
  ]
  const lowerBand = [
    { x: startX, y: startY + 20 },
    { x: midX, y: startY + 40 },
    { x: endX, y: startY + 50 },
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
        viewBox="0 0 600 350"
        preserveAspectRatio="xMidYMid meet"
        sx={{
          width: '100%',
          height: '100%',
        }}
      >
        <defs>
          <linearGradient id="confidenceGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={healthForesightColors.accent.main} stopOpacity="0.5" />
            <stop offset="100%" stopColor={healthForesightColors.accent.main} stopOpacity="0.2" />
          </linearGradient>
          <linearGradient id="riskGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={healthForesightColors.amber.main} stopOpacity="0.4" />
            <stop offset="100%" stopColor={healthForesightColors.amber.main} stopOpacity="0.15" />
          </linearGradient>
        </defs>

        {/* Confidence envelope */}
        <path
          d={`M ${upperBand[0].x} ${upperBand[0].y} Q ${upperBand[1].x} ${upperBand[1].y} ${upperBand[2].x} ${upperBand[2].y} L ${lowerBand[2].x} ${lowerBand[2].y} Q ${lowerBand[1].x} ${lowerBand[1].y} ${lowerBand[0].x} ${lowerBand[0].y} Z`}
          fill="url(#confidenceGradient)"
        />

        {/* Expected line (center) */}
        <path
          d={`M ${startX} ${startY} Q ${midX} ${startY - 10} ${endX} ${startY - 15}`}
          fill="none"
          stroke={healthForesightColors.accent.light}
          strokeWidth="6"
          opacity="1"
        />

        {/* Risk zones (outer edges) */}
        <path
          d={`M ${upperBand[0].x} ${upperBand[0].y - 10} Q ${upperBand[1].x} ${upperBand[1].y - 20} ${upperBand[2].x} ${upperBand[2].y - 30} L ${upperBand[2].x} ${upperBand[2].y} Q ${upperBand[1].x} ${upperBand[1].y} ${upperBand[0].x} ${upperBand[0].y} Z`}
          fill="url(#riskGradient)"
        />
        <path
          d={`M ${lowerBand[0].x} ${lowerBand[0].y + 10} Q ${lowerBand[1].x} ${lowerBand[1].y + 20} ${lowerBand[2].x} ${lowerBand[2].y + 30} L ${lowerBand[2].x} ${lowerBand[2].y} Q ${lowerBand[1].x} ${lowerBand[1].y} ${lowerBand[0].x} ${lowerBand[0].y} Z`}
          fill="url(#riskGradient)"
        />

        {/* Labels */}
        <text
          x={endX}
          y={upperBand[2].y - 10}
          textAnchor="end"
          fill={healthForesightColors.amber.light}
          fontSize="13"
          fontWeight="700"
        >
          Upper Bound
        </text>
        <text
          x={endX}
          y={startY - 15}
          textAnchor="end"
          fill={healthForesightColors.accent.light}
          fontSize="14"
          fontWeight="700"
        >
          Expected
        </text>
        <text
          x={endX}
          y={lowerBand[2].y + 20}
          textAnchor="end"
          fill={healthForesightColors.amber.light}
          fontSize="13"
          fontWeight="700"
        >
          Lower Bound
        </text>
        <text
          x={startX}
          y={startY - 50}
          fill={healthForesightColors.accent.main}
          fontSize="13"
          fontWeight="700"
        >
          Confidence Band
        </text>
        <text
          x="50"
          y="30"
          fill="#FFFFFF"
          fontSize="15"
          fontWeight="700"
        >
          Forecast Envelope
        </text>
      </Box>
    </Box>
  )
}
