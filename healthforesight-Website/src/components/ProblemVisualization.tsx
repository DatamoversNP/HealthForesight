/**
 * Problem Visualization Component
 * Visual representation of the core problems: no preview, limited measurement, no learning
 * Conceptually aligned with the problem statement text
 */
import React, { useEffect, useRef } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'
import { VisibilityOff, Assessment, School } from '@mui/icons-material'

export default function ProblemVisualization() {
  const svgRef = useRef<SVGSVGElement>(null)

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
        height="500"
        viewBox="0 0 600 500"
        style={{ overflow: 'visible' }}
      >
        <defs>
          <linearGradient id="problemGrad1" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={healthForesightColors.primary.main} stopOpacity="0.1" />
            <stop offset="100%" stopColor={healthForesightColors.primary.main} stopOpacity="0.05" />
          </linearGradient>
          <linearGradient id="problemGrad2" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={healthForesightColors.accent.main} stopOpacity="0.1" />
            <stop offset="100%" stopColor={healthForesightColors.accent.main} stopOpacity="0.05" />
          </linearGradient>
          <filter id="blur">
            <feGaussianBlur stdDeviation="8" />
          </filter>
          <filter id="shadow">
            <feDropShadow dx="0" dy="4" stdDeviation="8" floodOpacity="0.2" />
          </filter>
        </defs>

        {/* Background */}
        <rect width="600" height="500" fill="#FAFBFC" rx="8" />

        {/* Problem 1: No Preview - Policy with Question Mark */}
        <g transform="translate(100, 80)">
          {/* Policy Document/Box */}
          <rect
            x="0"
            y="0"
            width="120"
            height="100"
            rx="8"
            fill="#FFFFFF"
            stroke={healthForesightColors.primary.main}
            strokeWidth="3"
            strokeDasharray="8,4"
            opacity="0.6"
            filter="url(#shadow)"
          />
          <text
            x="60"
            y="50"
            textAnchor="middle"
            fill={healthForesightColors.primary.main}
            fontSize="16"
            fontWeight="600"
          >
            Policy
          </text>
          {/* Question Mark - Showing Uncertainty */}
          <circle
            cx="60"
            cy="70"
            r="20"
            fill={healthForesightColors.primary.main}
            opacity="0.2"
          />
          <text
            x="60"
            y="78"
            textAnchor="middle"
            fill={healthForesightColors.primary.main}
            fontSize="28"
            fontWeight="700"
          >
            ?
          </text>
          {/* Arrow pointing to unknown */}
          <path
            d="M 130 50 L 200 50"
            stroke={healthForesightColors.primary.main}
            strokeWidth="3"
            strokeDasharray="6,6"
            opacity="0.5"
            markerEnd="url(#arrowUnknown)"
          />
          {/* Blurred/Unknown Impact */}
          <rect
            x="200"
            y="20"
            width="100"
            height="60"
            rx="8"
            fill={healthForesightColors.primary.main}
            opacity="0.1"
            filter="url(#blur)"
          />
          <text
            x="250"
            y="50"
            textAnchor="middle"
            fill={healthForesightColors.primary.main}
            fontSize="14"
            fontWeight="500"
            opacity="0.5"
          >
            ???
          </text>
        </g>

        {/* Problem 2: Limited Measurement - Partial Visibility */}
        <g transform="translate(100, 220)">
          {/* Policy Implemented */}
          <rect
            x="0"
            y="0"
            width="100"
            height="80"
            rx="8"
            fill={healthForesightColors.primary.main}
            opacity="0.8"
            filter="url(#shadow)"
          />
          <text
            x="50"
            y="45"
            textAnchor="middle"
            fill="#FFFFFF"
            fontSize="14"
            fontWeight="600"
          >
            Policy
          </text>
          {/* Arrow to measurement */}
          <path
            d="M 110 40 L 180 40"
            stroke={healthForesightColors.accent.main}
            strokeWidth="4"
            markerEnd="url(#arrowTeal)"
          />
          {/* Partial/Incomplete Measurement */}
          <rect
            x="180"
            y="10"
            width="140"
            height="60"
            rx="8"
            fill="#FFFFFF"
            stroke={healthForesightColors.accent.main}
            strokeWidth="2"
            strokeDasharray="4,4"
            opacity="0.8"
            filter="url(#shadow)"
          />
          {/* Partial chart bars - showing incomplete data */}
          <rect x="195" y="45" width="20" height="15" fill={healthForesightColors.accent.main} opacity="0.6" />
          <rect x="225" y="40" width="20" height="20" fill={healthForesightColors.accent.main} opacity="0.6" />
          <rect x="255" y="50" width="20" height="10" fill={healthForesightColors.accent.main} opacity="0.3" />
          <rect x="285" y="55" width="20" height="5" fill={healthForesightColors.accent.main} opacity="0.2" />
          {/* "Limited" label */}
          <text
            x="250"
            y="85"
            textAnchor="middle"
            fill={healthForesightColors.neutral.mid}
            fontSize="12"
            fontWeight="500"
            fontStyle="italic"
          >
            Limited visibility
          </text>
        </g>

        {/* Problem 3: No Learning Loop - Broken Cycle */}
        <g transform="translate(100, 340)">
          {/* Policy */}
          <circle
            cx="50"
            cy="50"
            r="35"
            fill={healthForesightColors.primary.main}
            opacity="0.8"
            filter="url(#shadow)"
          />
          <text
            x="50"
            y="58"
            textAnchor="middle"
            fill="#FFFFFF"
            fontSize="14"
            fontWeight="600"
          >
            Policy
          </text>
          {/* Forward arrow */}
          <path
            d="M 90 50 L 200 50"
            stroke={healthForesightColors.primary.main}
            strokeWidth="4"
            markerEnd="url(#arrowBlue)"
          />
          {/* Impact */}
          <circle
            cx="240"
            cy="50"
            r="35"
            fill={healthForesightColors.accent.main}
            opacity="0.8"
            filter="url(#shadow)"
          />
          <text
            x="240"
            y="58"
            textAnchor="middle"
            fill="#FFFFFF"
            fontSize="14"
            fontWeight="600"
          >
            Impact
          </text>
          {/* Broken/Incomplete Feedback Loop */}
          <path
            d="M 275 50 Q 300 20 250 20 Q 200 20 150 30 Q 100 40 50 50"
            stroke={healthForesightColors.neutral.light}
            strokeWidth="3"
            strokeDasharray="8,8"
            fill="none"
            opacity="0.4"
          />
          {/* X mark showing broken connection */}
          <g transform="translate(150, 30)">
            <line x1="-8" y1="-8" x2="8" y2="8" stroke="#EF4444" strokeWidth="3" />
            <line x1="8" y1="-8" x2="-8" y2="8" stroke="#EF4444" strokeWidth="3" />
          </g>
          <text
            x="150"
            y="15"
            textAnchor="middle"
            fill="#EF4444"
            fontSize="11"
            fontWeight="600"
          >
            No Learning
          </text>
        </g>

        {/* Arrow Markers */}
        <defs>
          <marker
            id="arrowUnknown"
            markerWidth="12"
            markerHeight="12"
            refX="10"
            refY="4"
            orient="auto"
          >
            <polygon points="0 0, 12 4, 0 8" fill={healthForesightColors.primary.main} opacity="0.5" />
          </marker>
          <marker
            id="arrowTeal"
            markerWidth="12"
            markerHeight="12"
            refX="10"
            refY="4"
            orient="auto"
          >
            <polygon points="0 0, 12 4, 0 8" fill={healthForesightColors.accent.main} />
          </marker>
          <marker
            id="arrowBlue"
            markerWidth="12"
            markerHeight="12"
            refX="10"
            refY="4"
            orient="auto"
          >
            <polygon points="0 0, 12 4, 0 8" fill={healthForesightColors.primary.main} />
          </marker>
        </defs>

        {/* Icons representing problems */}
        <g transform="translate(450, 100)">
          {/* No Preview Icon */}
          <circle
            cx="0"
            cy="0"
            r="40"
            fill={healthForesightColors.primary.main}
            opacity="0.1"
          />
          <foreignObject x="-20" y="-20" width="40" height="40">
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '100%',
                height: '100%',
                color: healthForesightColors.primary.main,
              }}
            >
              <VisibilityOff sx={{ fontSize: 32 }} />
            </Box>
          </foreignObject>
        </g>

        <g transform="translate(450, 250)">
          {/* Limited Measurement Icon */}
          <circle
            cx="0"
            cy="0"
            r="40"
            fill={healthForesightColors.accent.main}
            opacity="0.1"
          />
          <foreignObject x="-20" y="-20" width="40" height="40">
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '100%',
                height: '100%',
                color: healthForesightColors.accent.main,
              }}
            >
              <Assessment sx={{ fontSize: 32, opacity: 0.6 }} />
            </Box>
          </foreignObject>
        </g>

        <g transform="translate(450, 400)">
          {/* No Learning Icon */}
          <circle
            cx="0"
            cy="0"
            r="40"
            fill="#EF4444"
            opacity="0.1"
          />
          <foreignObject x="-20" y="-20" width="40" height="40">
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '100%',
                height: '100%',
                color: '#EF4444',
              }}
            >
              <School sx={{ fontSize: 32, opacity: 0.5 }} />
            </Box>
          </foreignObject>
        </g>
      </svg>
    </Box>
  )
}
