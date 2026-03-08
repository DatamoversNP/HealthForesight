/**
 * Solution 1: Policy Blind Spots Visual
 * Animated loop: Policy → Expected Impact → Risk Signals → Decision
 */
import React, { useEffect, useRef } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'

export default function PolicyBlindSpotsVisual() {
  const svgRef = useRef<SVGSVGElement>(null)
  const animationRef = useRef<number>()
  const flowCircleRef = useRef<SVGCircleElement>(null)

  useEffect(() => {
    const animate = () => {
      if (svgRef.current && flowCircleRef.current) {
        const path = svgRef.current.querySelector('#flowPath') as SVGPathElement
        if (path) {
          const length = path.getTotalLength()
          let progress = 0
          const speed = 0.003

          const move = () => {
            progress += speed
            if (progress > 1) progress = 0

            const offset = progress * length
            const point = path.getPointAtLength(offset)
            
            if (flowCircleRef.current) {
              flowCircleRef.current.setAttribute('cx', String(point.x))
              flowCircleRef.current.setAttribute('cy', String(point.y))
            }

            animationRef.current = requestAnimationFrame(move)
          }

          move()
        }
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
          <linearGradient id="policyGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={healthForesightColors.primary.main} stopOpacity="1" />
            <stop offset="100%" stopColor={healthForesightColors.primary.dark} stopOpacity="1" />
          </linearGradient>
          <linearGradient id="impactGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={healthForesightColors.accent.main} stopOpacity="1" />
            <stop offset="100%" stopColor={healthForesightColors.accent.dark} stopOpacity="1" />
          </linearGradient>
          <linearGradient id="riskGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={healthForesightColors.amber.main} stopOpacity="1" />
            <stop offset="100%" stopColor={healthForesightColors.amber.dark} stopOpacity="1" />
          </linearGradient>
          <linearGradient id="decisionGradient" x1="0%" y1="0%" x2="100%" y2="100%">
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
            <feDropShadow dx="0" dy="4" stdDeviation="8" floodOpacity="0.3" />
          </filter>
        </defs>

        {/* Flow Path - Circular loop */}
        <path
          id="flowPath"
          d="M 150 200 Q 300 100 450 200 T 300 300 T 150 200"
          fill="none"
          stroke="none"
        />

        {/* Node 1: Policy */}
        <g className="policy-node">
          <circle
            cx="150"
            cy="200"
            r="50"
            fill="url(#policyGradient)"
            filter="url(#shadow)"
            opacity="0.9"
          />
          <circle
            cx="150"
            cy="200"
            r="45"
            fill="none"
            stroke="#FFFFFF"
            strokeWidth="2"
            opacity="0.3"
          />
          <text
            x="150"
            y="195"
            textAnchor="middle"
            fill="#FFFFFF"
            fontSize="18"
            fontWeight="700"
          >
            Policy
          </text>
          <text
            x="150"
            y="215"
            textAnchor="middle"
            fill="#FFFFFF"
            fontSize="12"
            fontWeight="500"
          >
            Definition
          </text>
        </g>

        {/* Node 2: Expected Impact */}
        <g className="impact-node">
          <circle
            cx="450"
            cy="200"
            r="50"
            fill="url(#impactGradient)"
            filter="url(#shadow)"
            opacity="0.9"
          />
          <circle
            cx="450"
            cy="200"
            r="45"
            fill="none"
            stroke="#FFFFFF"
            strokeWidth="2"
            opacity="0.3"
          />
          <text
            x="450"
            y="195"
            textAnchor="middle"
            fill="#FFFFFF"
            fontSize="18"
            fontWeight="700"
          >
            Expected
          </text>
          <text
            x="450"
            y="215"
            textAnchor="middle"
            fill="#FFFFFF"
            fontSize="12"
            fontWeight="500"
          >
            Impact
          </text>
        </g>

        {/* Node 3: Risk Signals */}
        <g className="risk-node">
          <circle
            cx="300"
            cy="100"
            r="50"
            fill="url(#riskGradient)"
            filter="url(#shadow)"
            opacity="0.9"
          />
          <circle
            cx="300"
            cy="100"
            r="45"
            fill="none"
            stroke="#FFFFFF"
            strokeWidth="2"
            opacity="0.3"
          />
          <text
            x="300"
            y="95"
            textAnchor="middle"
            fill="#FFFFFF"
            fontSize="18"
            fontWeight="700"
          >
            Risk
          </text>
          <text
            x="300"
            y="115"
            textAnchor="middle"
            fill="#FFFFFF"
            fontSize="12"
            fontWeight="500"
          >
            Signals
          </text>
        </g>

        {/* Node 4: Decision */}
        <g className="decision-node">
          <circle
            cx="300"
            cy="300"
            r="50"
            fill="url(#decisionGradient)"
            filter="url(#shadow)"
            opacity="0.9"
          />
          <circle
            cx="300"
            cy="300"
            r="45"
            fill="none"
            stroke="#FFFFFF"
            strokeWidth="2"
            opacity="0.3"
          />
          <text
            x="300"
            y="295"
            textAnchor="middle"
            fill="#FFFFFF"
            fontSize="18"
            fontWeight="700"
          >
            Decision
          </text>
          <text
            x="300"
            y="315"
            textAnchor="middle"
            fill="#FFFFFF"
            fontSize="12"
            fontWeight="500"
          >
            Informed
          </text>
        </g>

        {/* Connection Lines */}
        <path
          d="M 200 200 Q 300 150 400 200"
          fill="none"
          stroke={healthForesightColors.primary.main}
          strokeWidth="3"
          strokeDasharray="5,5"
          opacity="0.4"
        />
        <path
          d="M 400 200 Q 375 150 300 100"
          fill="none"
          stroke={healthForesightColors.accent.main}
          strokeWidth="3"
          strokeDasharray="5,5"
          opacity="0.4"
        />
        <path
          d="M 300 100 Q 300 200 300 250"
          fill="none"
          stroke={healthForesightColors.amber.main}
          strokeWidth="3"
          strokeDasharray="5,5"
          opacity="0.4"
        />
        <path
          d="M 300 300 Q 225 250 150 200"
          fill="none"
          stroke={healthForesightColors.primary.main}
          strokeWidth="3"
          strokeDasharray="5,5"
          opacity="0.4"
        />

        {/* Flowing Circle */}
        <circle
          ref={flowCircleRef}
          r="8"
          fill={healthForesightColors.primary.main}
          filter="url(#glow)"
          opacity="0.9"
        />
      </Box>
    </Box>
  )
}
