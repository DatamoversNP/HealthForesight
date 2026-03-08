/**
 * Section 7: Forecast Band - Institutional Learning
 * Confidence band narrows as more policies are implemented
 * Shows learning system, not time-based forecast decay
 */
import React, { useEffect, useRef, useState } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'

export default function ForecastBandVisual() {
  const svgRef = useRef<SVGSVGElement>(null)
  const [bandOpacity, setBandOpacity] = useState(0)
  const [lineProgress, setLineProgress] = useState(0)
  const [riskOpacity, setRiskOpacity] = useState(0)
  const [hasAnimated, setHasAnimated] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !hasAnimated) {
          setHasAnimated(true)
          // Confidence band fades in (300ms)
          setTimeout(() => setBandOpacity(1), 0)
          // Expected line draws (500ms)
          setTimeout(() => {
            let startTime: number | null = null
            const animate = (timestamp: number) => {
              if (!startTime) startTime = timestamp
              const elapsed = timestamp - startTime
              const progress = Math.min(elapsed / 500, 1)
              setLineProgress(progress)
              if (progress < 1) {
                requestAnimationFrame(animate)
              }
            }
            requestAnimationFrame(animate)
          }, 300)
          // Risk zones appear (250ms)
          setTimeout(() => setRiskOpacity(1), 800)
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
  const startX = 50
  const startY = height * 0.5
  const endX = 550
  const midX = (startX + endX) / 2

  // Confidence band NARROWS (not widens) - early policies have wide uncertainty, later policies have tight
  // Start wide (±50px), end narrow (±15px)
  const startBandWidth = 50
  const endBandWidth = 15

  const upperBand = [
    { x: startX, y: startY - startBandWidth },
    { x: midX, y: startY - (startBandWidth + endBandWidth) / 2 },
    { x: endX, y: startY - endBandWidth },
  ]
  const lowerBand = [
    { x: startX, y: startY + startBandWidth },
    { x: midX, y: startY + (startBandWidth + endBandWidth) / 2 },
    { x: endX, y: startY + endBandWidth },
  ]

  // Risk zone also NARROWS (not expands)
  const startRiskWidth = 25
  const endRiskWidth = 8

  const lineLength = 500

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
        <defs>
          <linearGradient id="confidenceGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#2EC4C6" stopOpacity="0.3" />
            <stop offset="50%" stopColor="#2EC4C6" stopOpacity="0.15" />
            <stop offset="100%" stopColor="#2EC4C6" stopOpacity="0.08" />
          </linearGradient>
          <linearGradient id="riskGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#E6A23C" stopOpacity="0.2" />
            <stop offset="50%" stopColor="#E6A23C" stopOpacity="0.12" />
            <stop offset="100%" stopColor="#E6A23C" stopOpacity="0.05" />
          </linearGradient>
        </defs>

        {/* Confidence band - NARROWS as we progress (learning system) */}
        <path
          d={`M ${upperBand[0].x} ${upperBand[0].y} Q ${upperBand[1].x} ${upperBand[1].y} ${upperBand[2].x} ${upperBand[2].y} L ${lowerBand[2].x} ${lowerBand[2].y} Q ${lowerBand[1].x} ${lowerBand[1].y} ${lowerBand[0].x} ${lowerBand[0].y} Z`}
          fill="url(#confidenceGradient)"
          opacity={bandOpacity}
          style={{ transition: 'opacity 300ms ease-out' }}
        />

        {/* Expected line - becomes more stable as learning accumulates */}
        <path
          d={`M ${startX} ${startY} Q ${midX} ${startY - 5} ${endX} ${startY}`}
          fill="none"
          stroke="#2EC4C6"
          strokeWidth="6"
          strokeDasharray={`${lineProgress * lineLength} ${lineLength}`}
          opacity="1"
        />

        {/* Risk zones - SHRINK as confidence improves */}
        <g opacity={riskOpacity} style={{ transition: 'opacity 250ms ease-out' }}>
          <path
            d={`M ${startX} ${startY - startBandWidth - startRiskWidth} Q ${midX} ${startY - (startBandWidth + endBandWidth) / 2 - (startRiskWidth + endRiskWidth) / 2} ${endX} ${startY - endBandWidth - endRiskWidth} L ${endX} ${startY - endBandWidth} Q ${midX} ${startY - (startBandWidth + endBandWidth) / 2} ${startX} ${startY - startBandWidth} Z`}
            fill="url(#riskGradient)"
          />
          <path
            d={`M ${startX} ${startY + startBandWidth + startRiskWidth} Q ${midX} ${startY + (startBandWidth + endBandWidth) / 2 + (startRiskWidth + endRiskWidth) / 2} ${endX} ${startY + endBandWidth + endRiskWidth} L ${endX} ${startY + endBandWidth} Q ${midX} ${startY + (startBandWidth + endBandWidth) / 2} ${startX} ${startY + startBandWidth} Z`}
            fill="url(#riskGradient)"
          />
        </g>

        {/* Policy markers - show discrete policies, not time */}
        {[0, 1, 2, 3, 4].map((idx) => {
          const x = startX + (idx / 4) * (endX - startX)
          const y = startY
          return (
            <g key={idx}>
              <circle
                cx={x}
                cy={y}
                r="6"
                fill="#6366F1"
                opacity={lineProgress > idx * 0.2 ? 1 : 0}
                style={{ transition: 'opacity 300ms ease-out' }}
              />
            </g>
          )
        })}

        {/* Axis labels - Policy sequence, not time */}
        <text
          x="50"
          y="30"
          fill="#1F2937"
          fontSize="13"
          fontWeight="600"
        >
          Policy Sequence →
        </text>
        <text
          x="50"
          y="280"
          fill="#1F2937"
          fontSize="13"
          fontWeight="600"
        >
          Expected Impact
        </text>

        {/* Confidence range label */}
        {bandOpacity > 0 && (
          <text
            x={midX}
            y={startY - 30}
            textAnchor="middle"
            fill="#2EC4C6"
            fontSize="12"
            fontWeight="600"
            opacity={bandOpacity * 0.8}
          >
            Confidence Range
          </text>
        )}

        {/* Expected line label */}
        <text
          x={endX}
          y={startY - 5}
          textAnchor="end"
          fill="#2EC4C6"
          fontSize="15"
          fontWeight="700"
          opacity={lineProgress > 0.5 ? 1 : 0}
        >
          Expected
        </text>

        {/* Learning indicator */}
        {lineProgress > 0.8 && (
          <text
            x={endX - 20}
            y={startY - endBandWidth - 25}
            textAnchor="end"
            fill="#2EC4C6"
            fontSize="11"
            fontWeight="700"
            style={{ transition: 'opacity 400ms ease-out' }}
          >
            Confidence ↑
          </text>
        )}
      </Box>
    </Box>
  )
}
