/**
 * Section 5: 4-Step Horizontal Progress Rail
 * Draws left→right, each step highlights briefly
 */
import React, { useEffect, useRef, useState } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'

export default function ProgressRailVisual() {
  const svgRef = useRef<SVGSVGElement>(null)
  const [railProgress, setRailProgress] = useState(0)
  const [highlightedStep, setHighlightedStep] = useState<number | null>(null)
  const [hasAnimated, setHasAnimated] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !hasAnimated) {
          setHasAnimated(true)
          // Rail draws left→right (450ms)
          let startTime: number | null = null
          const animate = (timestamp: number) => {
            if (!startTime) startTime = timestamp
            const elapsed = timestamp - startTime
            const progress = Math.min(elapsed / 450, 1)
            setRailProgress(progress)
            if (progress < 1) {
              requestAnimationFrame(animate)
            } else {
              // Highlight each step briefly (200ms each)
              steps.forEach((_, idx) => {
                setTimeout(() => {
                  setHighlightedStep(idx)
                  setTimeout(() => setHighlightedStep(null), 200)
                }, 500 + idx * 250)
              })
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

  const steps = [
    { x: 100, label: 'Define', verb: 'Structure policies precisely' },
    { x: 250, label: 'Predict', verb: 'Estimate expected impact' },
    { x: 400, label: 'Observe', verb: 'Measure what happened' },
    { x: 550, label: 'Learn', verb: 'Capture insights' },
  ]

  const railLength = 500

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
        {/* Progress Rail */}
        <line
          x1="100"
          y1="150"
          x2="550"
          y2="150"
          stroke={healthForesightColors.neutral.light}
          strokeWidth="3"
          opacity="0.3"
        />
        <line
          x1="100"
          y1="150"
          x2={100 + railProgress * 450}
          y2="150"
          stroke={healthForesightColors.primary.main}
          strokeWidth="4"
          opacity="0.9"
        />

        {/* Steps */}
        {steps.map((step, idx) => {
          const isHighlighted = highlightedStep === idx
          return (
            <g key={idx}>
              <circle
                cx={step.x}
                cy={150}
                r={isHighlighted ? 32 : 30}
                fill={healthForesightColors.primary.main}
                opacity={railProgress > idx * 0.25 ? 1 : 0.3}
                style={{ transition: 'all 200ms ease-out' }}
              />
              <circle
                cx={step.x}
                cy={150}
                r="22"
                fill="#FFFFFF"
              />
              <text
                x={step.x}
                y={150 + 6}
                textAnchor="middle"
                fill={healthForesightColors.primary.main}
                fontSize="12"
                fontWeight="700"
                opacity={railProgress > idx * 0.25 ? 1 : 0.3}
              >
                {step.label}
              </text>
              <text
                x={step.x}
                y={190}
                textAnchor="middle"
                fill={healthForesightColors.neutral.dark}
                fontSize="11"
                fontWeight="600"
                opacity={railProgress > idx * 0.25 ? 1 : 0.3}
              >
                {step.verb}
              </text>
            </g>
          )
        })}
      </Box>
    </Box>
  )
}
