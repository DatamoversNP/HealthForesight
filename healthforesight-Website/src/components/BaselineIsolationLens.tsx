/**
 * How It Works Section 2: Baseline Isolation Lens
 * Circular lens moves across blurred field, sharpening signals inside
 */
import React, { useEffect, useRef, useState } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'

export default function BaselineIsolationLens() {
  const svgRef = useRef<SVGSVGElement>(null)
  const [lensPosition, setLensPosition] = useState(0)
  const [hasAnimated, setHasAnimated] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !hasAnimated) {
          setHasAnimated(true)
          // Lens sweeps left to right
          let startTime: number | null = null
          const animate = (timestamp: number) => {
            if (!startTime) startTime = timestamp
            const elapsed = timestamp - startTime
            const progress = Math.min(elapsed / 1500, 1)
            setLensPosition(progress)
            if (progress < 1) {
              requestAnimationFrame(animate)
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
  const height = 300
  const lensX = 100 + lensPosition * 400
  const lensY = height / 2
  const lensRadius = 80

  // Generate blurred signals in background
  const signals = Array.from({ length: 20 }, (_, i) => ({
    x: 50 + (i / 19) * 450,
    y: 50 + Math.sin(i * 0.5) * 100 + Math.random() * 50,
    size: 3 + Math.random() * 4,
  }))

  return (
    <Box
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
        ref={svgRef}
        viewBox="0 0 600 400"
        sx={{
          width: '100%',
          height: '100%',
          maxHeight: '400px',
        }}
      >
        <defs>
          <filter id="blur">
            <feGaussianBlur stdDeviation="4" />
          </filter>
          <mask id="lensMask">
            <rect x="0" y="0" width="600" height="400" fill="black" />
            <circle
              cx={lensX}
              cy={lensY}
              r={lensRadius}
              fill="white"
            />
          </mask>
        </defs>

        {/* Blurred background signals */}
        <g filter="url(#blur)" opacity="0.4">
          {signals.map((signal, idx) => (
            <circle
              key={idx}
              cx={signal.x}
              cy={signal.y}
              r={signal.size}
              fill={healthForesightColors.neutral.mid}
            />
          ))}
        </g>

        {/* Sharp signals inside lens */}
        <g mask="url(#lensMask)">
          {signals
            .filter((s) => {
              const dx = s.x - lensX
              const dy = s.y - lensY
              return Math.sqrt(dx * dx + dy * dy) < lensRadius
            })
            .map((signal, idx) => (
              <circle
                key={idx}
                cx={signal.x}
                cy={signal.y}
                r={signal.size}
                fill={healthForesightColors.accent.main}
              />
            ))}
          {/* Baseline line inside lens */}
          {lensPosition > 0.3 && (
            <path
              d={`M ${lensX - lensRadius} ${lensY} L ${lensX + lensRadius} ${lensY}`}
              fill="none"
              stroke={healthForesightColors.accent.main}
              strokeWidth="4"
              opacity="1"
            />
          )}
        </g>

        {/* Lens circle outline */}
        <circle
          cx={lensX}
          cy={lensY}
          r={lensRadius}
          fill="none"
          stroke="#FFFFFF"
          strokeWidth="3"
          opacity="0.8"
        />
      </Box>
    </Box>
  )
}
