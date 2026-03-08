/**
 * Section 3: Institutional Learning Over Multiple Policies
 * Narrowing confidence band with policy markers
 * Shows increasing precision as more policies are learned from
 */
import React, { useEffect, useRef, useState } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../../theme/healthForesightTheme'

export default function FogToClarityVisual() {
  const svgRef = useRef<SVGSVGElement>(null)
  const [revealProgress, setRevealProgress] = useState(0)
  const [hasAnimated, setHasAnimated] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !hasAnimated) {
          setHasAnimated(true)
          // Reveal animation: policies appear sequentially, band narrows
          let startTime: number | null = null
          const animate = (timestamp: number) => {
            if (!startTime) startTime = timestamp
            const elapsed = timestamp - startTime
            const progress = Math.min(elapsed / 2000, 1)
            setRevealProgress(progress)
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
  const height = 250
  const centerY = height * 0.5
  const startX = 80
  const endX = 520

  // 5 policies, evenly spaced
  const policyCount = 5
  const policies = Array.from({ length: policyCount }, (_, i) => {
    const x = startX + (i / (policyCount - 1)) * (endX - startX)
    const progress = revealProgress
    const visible = progress > (i / policyCount) * 0.8
    return { x, visible, index: i }
  })

  // Confidence band narrows with each policy
  // Early policies: wide band (±40px)
  // Later policies: tight band (±12px)
  const getBandWidth = (policyIndex: number) => {
    // Band width decreases from 40 to 12 as we progress
    return 40 - (policyIndex / (policyCount - 1)) * 28
  }

  // Expected impact line (slight upward trend)
  const expectedLine = (x: number) => {
    return centerY - 10 - ((x - startX) / (endX - startX)) * 8
  }

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
        </defs>

        {/* Confidence band - narrowing cone shape */}
        {revealProgress > 0.1 && (
          <path
            d={`M ${startX} ${expectedLine(startX) - getBandWidth(0)} 
               L ${endX} ${expectedLine(endX) - getBandWidth(policyCount - 1)}
               L ${endX} ${expectedLine(endX) + getBandWidth(policyCount - 1)}
               L ${startX} ${expectedLine(startX) + getBandWidth(0)} Z`}
            fill="url(#confidenceGradient)"
            opacity={revealProgress > 0.1 ? 1 : 0}
            style={{ transition: 'opacity 400ms ease-out' }}
          />
        )}

        {/* Expected impact line */}
        <path
          d={`M ${startX} ${expectedLine(startX)} Q ${(startX + endX) / 2} ${expectedLine((startX + endX) / 2)} ${endX} ${expectedLine(endX)}`}
          fill="none"
          stroke="#2EC4C6"
          strokeWidth="5"
          strokeDasharray="8,6"
          opacity={revealProgress > 0.2 ? 1 : 0}
          style={{ transition: 'opacity 400ms ease-out' }}
        />

        {/* Policy markers - appear sequentially */}
        {policies.map((policy, idx) => {
          const y = expectedLine(policy.x)
          const isEarly = idx < 2
          return (
            <g key={idx}>
              <circle
                cx={policy.x}
                cy={y}
                r={isEarly ? "10" : "8"}
                fill="#6366F1"
                opacity={policy.visible ? 1 : 0}
                style={{ transition: 'opacity 300ms ease-out, r 200ms ease-out' }}
              />
              <circle
                cx={policy.x}
                cy={y}
                r={isEarly ? "6" : "5"}
                fill="#FFFFFF"
                opacity={policy.visible ? 1 : 0}
              />
              <text
                x={policy.x}
                y={y + (isEarly ? 25 : 20)}
                textAnchor="middle"
                fill="#6366F1"
                fontSize={isEarly ? "11" : "10"}
                fontWeight="700"
                opacity={policy.visible ? 1 : 0}
              >
                Policy {idx + 1}
              </text>
            </g>
          )
        })}

        {/* Axis labels */}
        <text
          x="80"
          y="30"
          fill="#1F2937"
          fontSize="13"
          fontWeight="600"
        >
          Policy Sequence →
        </text>
        <text
          x="80"
          y="280"
          fill="#1F2937"
          fontSize="13"
          fontWeight="600"
        >
          Expected Impact
        </text>

        {/* Learning indicator - appears after all policies */}
        {revealProgress > 0.9 && (
          <text
            x={endX - 20}
            y={expectedLine(endX) - 30}
            textAnchor="end"
            fill="#2EC4C6"
            fontSize="12"
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
