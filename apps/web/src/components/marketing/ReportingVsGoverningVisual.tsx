/**
 * Section 2: Reporting vs Governing Contrast
 * Left: Static chart/table (Reporting)
 * Right: Flow loop (Governing)
 * One-time morph animation on scroll
 */
import React, { useEffect, useRef, useState } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../../theme/healthForesightTheme'

export default function ReportingVsGoverningVisual() {
  const svgRef = useRef<SVGSVGElement>(null)
  const [hasAnimated, setHasAnimated] = useState(false)
  const [loopProgress, setLoopProgress] = useState(0)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !hasAnimated) {
          setHasAnimated(true)
          // Draw loop line over 400ms
          let startTime: number | null = null
          const animate = (timestamp: number) => {
            if (!startTime) startTime = timestamp
            const elapsed = timestamp - startTime
            const progress = Math.min(elapsed / 400, 1)
            setLoopProgress(progress)
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

  const loopPath = `M 450 150 Q 550 120 550 200 T 450 250`
  const pathLength = 400 // Approximate

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
        {/* Left: Reporting (Static, Desaturated) */}
        <g>
          <text
            x="150"
            y="80"
            textAnchor="middle"
            fill="#9CA3AF"
            fontSize="16"
            fontWeight="600"
          >
            Reporting
          </text>
          {/* Static chart - flat, desaturated */}
          {[80, 120, 100, 140, 110].map((height, idx) => (
            <rect
              key={idx}
              x={100 + idx * 25}
              y={250 - height}
              width="20"
              height={height}
              fill="#6B7280"
              opacity="0.6"
            />
          ))}
          {/* Backward arrow - more visible */}
          <path
            d="M 200 200 L 100 200"
            fill="none"
            stroke="#6B7280"
            strokeWidth="3"
            opacity="0.7"
          />
          <path
            d="M 100 200 L 115 195 M 100 200 L 115 205"
            fill="none"
            stroke="#6B7280"
            strokeWidth="3"
            opacity="0.7"
          />
        </g>

        {/* Right: Governing (Animated, Bright) */}
        <g>
          <text
            x="500"
            y="80"
            textAnchor="middle"
            fill="#FFFFFF"
            fontSize="16"
            fontWeight="700"
            opacity={hasAnimated ? 1 : 0}
            style={{ transition: 'opacity 450ms ease-out' }}
          >
            Governing
          </text>
          {/* Loop path - thicker, brighter */}
          <path
            d={loopPath}
            fill="none"
            stroke="#6366F1"
            strokeWidth="6"
            strokeDasharray={`${loopProgress * pathLength} ${pathLength}`}
            opacity="1"
          />
          {/* Loop nodes - larger, brighter, with pulse on arrival */}
          {[
            { x: 450, y: 150, label: 'Define' },
            { x: 550, y: 120, label: 'Predict' },
            { x: 550, y: 200, label: 'Observe' },
            { x: 450, y: 250, label: 'Learn' },
          ].map((node, idx) => {
            const nodeDelay = 400 + idx * 150
            const shouldPulse = hasAnimated && loopProgress > (idx + 1) * 0.2
            return (
              <g key={idx}>
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={shouldPulse ? 28 : 26}
                  fill="#6366F1"
                  opacity={hasAnimated && loopProgress > idx * 0.25 ? 1 : 0}
                  style={{
                    transition: `opacity ${nodeDelay}ms ease-out, r 200ms ease-out`,
                  }}
                />
                <circle
                  cx={node.x}
                  cy={node.y}
                  r="20"
                  fill="#FFFFFF"
                  opacity={hasAnimated && loopProgress > idx * 0.25 ? 1 : 0}
                />
                <text
                  x={node.x}
                  y={node.y + 6}
                  textAnchor="middle"
                  fill="#6366F1"
                  fontSize="12"
                  fontWeight="700"
                  opacity={hasAnimated && loopProgress > idx * 0.25 ? 1 : 0}
                  style={{ transition: `opacity ${nodeDelay}ms ease-out` }}
                >
                  {node.label}
                </text>
              </g>
            )
          })}
        </g>
      </Box>
    </Box>
  )
}
