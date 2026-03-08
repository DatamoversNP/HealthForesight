/**
 * Clear, Professional Policy Flow Diagram
 * Redesigned for maximum clarity and readability
 */
import React, { useEffect, useRef } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'

export default function PolicyFlowDiagram() {
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
          const speed = 0.0025

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
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        py: 4,
        px: 2,
      }}
    >
      <svg
        ref={svgRef}
        width="100%"
        height="600"
        viewBox="0 0 1200 600"
        style={{ overflow: 'visible' }}
      >
        <defs>
          {/* Clean Gradients */}
          <linearGradient id="policyGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#4A5FC7" />
            <stop offset="100%" stopColor="#2E3A8A" />
          </linearGradient>
          <linearGradient id="expectedGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#14B8A6" />
            <stop offset="100%" stopColor="#0D9488" />
          </linearGradient>
          <linearGradient id="observedGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#5EEAD4" />
            <stop offset="100%" stopColor="#2DD4BF" />
          </linearGradient>
          <linearGradient id="businessGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#F59E0B" />
            <stop offset="100%" stopColor="#D97706" />
          </linearGradient>
          
          {/* Professional Shadows */}
          <filter id="nodeShadow" x="-50%" y="-50%" width="200%" height="200%">
            <feDropShadow dx="0" dy="4" stdDeviation="12" floodOpacity="0.25" />
          </filter>
          <filter id="flowGlow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="4" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Clean Background */}
        <rect width="1200" height="600" fill="#FAFBFC" rx="8" />

        {/* Main Flow Path */}
        <path
          id="flowPath"
          d="M 100 300 L 500 300 L 900 300"
          stroke="none"
          fill="none"
        />

        {/* Policy Node - Clear and Prominent */}
        <g>
          <circle
            cx="100"
            cy="300"
            r="80"
            fill="url(#policyGrad)"
            filter="url(#nodeShadow)"
          />
          <circle
            cx="100"
            cy="300"
            r="75"
            fill="none"
            stroke="#FFFFFF"
            strokeWidth="4"
            opacity="0.8"
          />
          <text
            x="100"
            y="310"
            textAnchor="middle"
            fill="#FFFFFF"
            fontSize="28"
            fontWeight="700"
            letterSpacing="2px"
          >
            Policy
          </text>
        </g>

        {/* Arrow: Policy to Expected */}
        <defs>
          <marker
            id="arrowBlue"
            markerWidth="20"
            markerHeight="20"
            refX="18"
            refY="6"
            orient="auto"
          >
            <polygon points="0 0, 20 6, 0 12" fill="#4A5FC7" />
          </marker>
        </defs>
        <line
          x1="180"
          y1="300"
          x2="420"
          y2="300"
          stroke="#4A5FC7"
          strokeWidth="8"
          markerEnd="url(#arrowBlue)"
        />

        {/* Expected Impact Node */}
        <g>
          <circle
            cx="500"
            cy="300"
            r="80"
            fill="url(#expectedGrad)"
            filter="url(#nodeShadow)"
          />
          <circle
            cx="500"
            cy="300"
            r="75"
            fill="none"
            stroke="#FFFFFF"
            strokeWidth="4"
            opacity="0.8"
          />
          <text
            x="500"
            y="285"
            textAnchor="middle"
            fill="#FFFFFF"
            fontSize="24"
            fontWeight="700"
            letterSpacing="2px"
          >
            Expected
          </text>
          <text
            x="500"
            y="315"
            textAnchor="middle"
            fill="#FFFFFF"
            fontSize="24"
            fontWeight="700"
            letterSpacing="2px"
          >
            Impact
          </text>
        </g>

        {/* Business Impact: Cost */}
        <g>
          <circle
            cx="400"
            cy="180"
            r="50"
            fill="url(#businessGrad)"
            filter="url(#nodeShadow)"
          />
          <circle
            cx="400"
            cy="180"
            r="46"
            fill="none"
            stroke="#FFFFFF"
            strokeWidth="3"
            opacity="0.7"
          />
          <text
            x="400"
            y="190"
            textAnchor="middle"
            fill="#FFFFFF"
            fontSize="20"
            fontWeight="700"
          >
            Cost
          </text>
          <line
            x1="400"
            y1="230"
            x2="460"
            y2="250"
            stroke="#F59E0B"
            strokeWidth="3"
            strokeDasharray="6,6"
            opacity="0.6"
          />
        </g>

        {/* Business Impact: ROI Measure */}
        <g>
          <circle
            cx="400"
            cy="420"
            r="50"
            fill="url(#businessGrad)"
            filter="url(#nodeShadow)"
          />
          <circle
            cx="400"
            cy="420"
            r="46"
            fill="none"
            stroke="#FFFFFF"
            strokeWidth="3"
            opacity="0.7"
          />
          <text
            x="400"
            y="410"
            textAnchor="middle"
            fill="#FFFFFF"
            fontSize="18"
            fontWeight="700"
          >
            ROI
          </text>
          <text
            x="400"
            y="432"
            textAnchor="middle"
            fill="#FFFFFF"
            fontSize="18"
            fontWeight="700"
          >
            Measure
          </text>
          <line
            x1="400"
            y1="370"
            x2="460"
            y2="350"
            stroke="#F59E0B"
            strokeWidth="3"
            strokeDasharray="6,6"
            opacity="0.6"
          />
        </g>

        {/* Arrow: Expected to Observed */}
        <defs>
          <marker
            id="arrowTeal"
            markerWidth="20"
            markerHeight="20"
            refX="18"
            refY="6"
            orient="auto"
          >
            <polygon points="0 0, 20 6, 0 12" fill="#14B8A6" />
          </marker>
        </defs>
        <line
          x1="580"
          y1="300"
          x2="820"
          y2="300"
          stroke="#14B8A6"
          strokeWidth="8"
          markerEnd="url(#arrowTeal)"
        />

        {/* Observed Impact Node */}
        <g>
          <circle
            cx="900"
            cy="300"
            r="80"
            fill="url(#observedGrad)"
            filter="url(#nodeShadow)"
          />
          <circle
            cx="900"
            cy="300"
            r="75"
            fill="none"
            stroke="#FFFFFF"
            strokeWidth="4"
            opacity="0.8"
          />
          <text
            x="900"
            y="285"
            textAnchor="middle"
            fill="#1F2937"
            fontSize="24"
            fontWeight="700"
            letterSpacing="2px"
          >
            Observed
          </text>
          <text
            x="900"
            y="315"
            textAnchor="middle"
            fill="#1F2937"
            fontSize="24"
            fontWeight="700"
            letterSpacing="2px"
          >
            Impact
          </text>
        </g>

        {/* Business Impact: Utilization Control */}
        <g>
          <circle
            cx="1000"
            cy="180"
            r="50"
            fill="url(#businessGrad)"
            filter="url(#nodeShadow)"
          />
          <circle
            cx="1000"
            cy="180"
            r="46"
            fill="none"
            stroke="#FFFFFF"
            strokeWidth="3"
            opacity="0.7"
          />
          <text
            x="1000"
            y="170"
            textAnchor="middle"
            fill="#FFFFFF"
            fontSize="18"
            fontWeight="700"
          >
            Utilization
          </text>
          <text
            x="1000"
            y="192"
            textAnchor="middle"
            fill="#FFFFFF"
            fontSize="18"
            fontWeight="700"
          >
            Control
          </text>
          <line
            x1="1000"
            y1="230"
            x2="940"
            y2="250"
            stroke="#F59E0B"
            strokeWidth="3"
            strokeDasharray="6,6"
            opacity="0.6"
          />
        </g>

        {/* Learning Loop - Clear Curved Path */}
        <defs>
          <marker
            id="arrowLoop"
            markerWidth="24"
            markerHeight="24"
            refX="22"
            refY="8"
            orient="auto"
          >
            <polygon points="0 0, 24 8, 0 16" fill="#2E3A8A" />
          </marker>
          <linearGradient id="loopGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#2E3A8A" />
            <stop offset="50%" stopColor="#4A5FC7" />
            <stop offset="100%" stopColor="#2E3A8A" />
          </linearGradient>
        </defs>
        <path
          d="M 980 300 Q 1100 150 1000 100 Q 800 50 400 100 Q 200 150 100 250 Q 50 300 100 300"
          stroke="url(#loopGrad)"
          strokeWidth="10"
          fill="none"
          strokeDasharray="20,12"
          markerEnd="url(#arrowLoop)"
          opacity="0.9"
        />

        {/* Learning Loop Label */}
        <rect
          x="550"
          y="80"
          width="180"
          height="45"
          rx="22"
          fill="#FFFFFF"
          filter="url(#nodeShadow)"
        />
        <text
          x="640"
          y="108"
          textAnchor="middle"
          fill="#2E3A8A"
          fontSize="22"
          fontWeight="700"
          letterSpacing="3px"
        >
          Learning Loop
        </text>

        {/* Animated Flow Circle */}
        <circle
          ref={flowCircleRef}
          cx="100"
          cy="300"
          r="16"
          fill="#5EEAD4"
          filter="url(#flowGlow)"
        />
        <circle
          ref={flowCircleRef}
          cx="100"
          cy="300"
          r="24"
          fill="none"
          stroke="#5EEAD4"
          strokeWidth="2"
          opacity="0.4"
        />

        <style>
          {`
            @keyframes dash {
              to {
                stroke-dashoffset: -1000;
              }
            }
          `}
        </style>
      </svg>
    </Box>
  )
}
