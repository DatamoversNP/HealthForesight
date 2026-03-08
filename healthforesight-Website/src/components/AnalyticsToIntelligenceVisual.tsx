/**
 * Section 1: Analytics to Intelligence Transformation
 * Morphs from flat bar chart → flowing decision pipeline
 */
import React, { useEffect, useRef, useState } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'

export default function AnalyticsToIntelligenceVisual() {
  const svgRef = useRef<SVGSVGElement>(null)
  const [progress, setProgress] = useState(0)
  const [hasAnimated, setHasAnimated] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !hasAnimated) {
          setHasAnimated(true)
          // Animate from 0 to 1 over 2 seconds
          let startTime: number | null = null
          const animate = (timestamp: number) => {
            if (!startTime) startTime = timestamp
            const elapsed = timestamp - startTime
            const newProgress = Math.min(elapsed / 2000, 1)
            setProgress(newProgress)
            if (newProgress < 1) {
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

  // Interpolate between analytics (progress=0) and intelligence (progress=1)
  const analyticsOpacity = 1 - progress
  const intelligenceOpacity = progress

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
        {/* Traditional Analytics (fades out) */}
        <g opacity={analyticsOpacity}>
          <text
            x="300"
            y="50"
            textAnchor="middle"
            fill={healthForesightColors.neutral.mid}
            fontSize="14"
            fontWeight="600"
          >
            Traditional Analytics
          </text>
          {/* Bar chart */}
          {[100, 150, 120, 180, 140].map((height, idx) => (
            <g key={idx}>
              <rect
                x={150 + idx * 80}
                y={300 - height}
                width="50"
                height={height}
                fill={healthForesightColors.neutral.mid}
                opacity="0.6"
              />
            </g>
          ))}
          {/* Backward arrow */}
          <path
            d="M 500 200 L 100 200"
            fill="none"
            stroke={healthForesightColors.neutral.mid}
            strokeWidth="2"
            opacity="0.5"
          />
          <path
            d="M 100 200 L 120 190 M 100 200 L 120 210"
            fill="none"
            stroke={healthForesightColors.neutral.mid}
            strokeWidth="2"
            opacity="0.5"
          />
          <text
            x="300"
            y="220"
            textAnchor="middle"
            fill={healthForesightColors.neutral.mid}
            fontSize="12"
            opacity="0.7"
          >
            Reporting after the fact
          </text>
        </g>

        {/* Policy Intelligence (fades in) */}
        <g opacity={intelligenceOpacity}>
          <text
            x="300"
            y="50"
            textAnchor="middle"
            fill="#FFFFFF"
            fontSize="16"
            fontWeight="700"
          >
            Policy Intelligence
          </text>
          {/* Flowing pipeline */}
          <path
            d={`M 100 200 Q 200 ${200 - progress * 50} 300 200 Q 400 ${200 - progress * 50} 500 200`}
            fill="none"
            stroke={healthForesightColors.primary.main}
            strokeWidth="7"
            opacity="1"
          />
          {/* Pipeline nodes */}
          {[
            { x: 100, label: 'Policy', color: healthForesightColors.primary.main },
            { x: 220, label: 'Baseline', color: healthForesightColors.primary.main },
            { x: 300, label: 'Predict', color: healthForesightColors.primary.main },
            { x: 380, label: 'Observe', color: healthForesightColors.primary.main },
            { x: 500, label: 'Learn', color: healthForesightColors.accent.main },
          ].map((node, idx) => (
            <g key={idx}>
              <circle
                cx={node.x}
                cy={200}
                r="18"
                fill={node.color}
                opacity="1"
                stroke="#FFFFFF"
                strokeWidth="2"
              />
              <text
                x={node.x}
                y={240}
                textAnchor="middle"
                fill="#FFFFFF"
                fontSize="14"
                fontWeight="700"
              >
                {node.label}
              </text>
            </g>
          ))}
          {/* Forward flow */}
          <circle
            cx={100 + progress * 400}
            cy={200}
            r="8"
            fill={healthForesightColors.accent.main}
            opacity="1"
            stroke="#FFFFFF"
            strokeWidth="2"
          />
          <text
            x="300"
            y="280"
            textAnchor="middle"
            fill={healthForesightColors.accent.light}
            fontSize="16"
            fontWeight="700"
          >
            Decision intelligence over time
          </text>
        </g>
      </Box>
    </Box>
  )
}
