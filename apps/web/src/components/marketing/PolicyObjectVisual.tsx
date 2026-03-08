/**
 * Section 3: Policy Object Visualization
 * Central policy object with orbiting/expanding attributes
 */
import React, { useEffect, useRef, useState } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../../theme/healthForesightTheme'

interface Attribute {
  id: string
  label: string
  detail: string
  angle: number
  distance: number
}

export default function PolicyObjectVisual() {
  const svgRef = useRef<SVGSVGElement>(null)
  const [hoveredAttr, setHoveredAttr] = useState<string | null>(null)
  const [time, setTime] = useState(0)

  useEffect(() => {
    const animate = () => {
      setTime((prev) => (prev + 0.005) % (Math.PI * 2))
      requestAnimationFrame(animate)
    }
    const animationId = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(animationId)
  }, [])

  const centerX = 300
  const centerY = 200
  const baseRadius = 80

  const attributes: Attribute[] = [
    { id: 'who', label: 'Who', detail: 'Population, plan, geography', angle: 0, distance: 120 },
    { id: 'where', label: 'Where', detail: 'Networks, providers, sites', angle: Math.PI * 0.4, distance: 120 },
    { id: 'how', label: 'How', detail: 'Authorization, restriction', angle: Math.PI * 0.8, distance: 120 },
    { id: 'when', label: 'When', detail: 'Effective dates, versions', angle: Math.PI * 1.2, distance: 120 },
    { id: 'what', label: 'What', detail: 'Exceptions, carve-outs', angle: Math.PI * 1.6, distance: 120 },
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
        viewBox="0 0 600 400"
        preserveAspectRatio="xMidYMid meet"
        sx={{
          width: '100%',
          height: '100%',
        }}
      >
        <defs>
          <filter id="policyCoreGlow">
            <feGaussianBlur stdDeviation="4" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="attrGlow">
            <feGaussianBlur stdDeviation="2" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Connection lines */}
        {attributes.map((attr) => {
          const x = centerX + Math.cos(attr.angle + time * 0.2) * attr.distance
          const y = centerY + Math.sin(attr.angle + time * 0.2) * attr.distance
          const isHovered = hoveredAttr === attr.id
          return (
            <line
              key={attr.id}
              x1={centerX}
              y1={centerY}
              x2={x}
              y2={y}
              stroke={healthForesightColors.primary.light}
              strokeWidth={isHovered ? 5 : 3}
              opacity={isHovered ? 1 : 0.7}
            />
          )
        })}

        {/* Attributes */}
        {attributes.map((attr) => {
          const x = centerX + Math.cos(attr.angle + time * 0.2) * attr.distance
          const y = centerY + Math.sin(attr.angle + time * 0.2) * attr.distance
          const isHovered = hoveredAttr === attr.id
          const scale = isHovered ? 1.3 : 1

          return (
            <g
              key={attr.id}
              onMouseEnter={() => setHoveredAttr(attr.id)}
              onMouseLeave={() => setHoveredAttr(null)}
              style={{ cursor: 'pointer' }}
            >
              <circle
                cx={x}
                cy={y}
                r={16 * scale}
                fill={isHovered ? healthForesightColors.primary.main : healthForesightColors.accent.main}
                filter="url(#attrGlow)"
                opacity="1"
                stroke="#FFFFFF"
                strokeWidth="2"
              />
              <text
                x={x}
                y={y + 5}
                textAnchor="middle"
                fill="#FFFFFF"
                fontSize={isHovered ? 11 : 10}
                fontWeight="700"
              >
                {attr.label}
              </text>
              {isHovered && (
                <g>
                  <rect
                    x={x - 60}
                    y={y - 40}
                    width="120"
                    height="30"
                    rx="4"
                    fill={healthForesightColors.neutral.dark}
                    opacity="0.9"
                  />
                  <text
                    x={x}
                    y={y - 20}
                    textAnchor="middle"
                    fill="#FFFFFF"
                    fontSize="11"
                    fontWeight="600"
                  >
                    {attr.detail}
                  </text>
                </g>
              )}
            </g>
          )
        })}

        {/* Central Policy Object */}
        <g>
          <circle
            cx={centerX}
            cy={centerY}
            r={baseRadius}
            fill={healthForesightColors.primary.main}
            filter="url(#policyCoreGlow)"
            opacity="0.9"
          />
          <circle
            cx={centerX}
            cy={centerY}
            r={baseRadius - 5}
            fill="none"
            stroke="#FFFFFF"
            strokeWidth="3"
            opacity="0.3"
          />
          <text
            x={centerX}
            y={centerY - 10}
            textAnchor="middle"
            fill="#FFFFFF"
            fontSize="24"
            fontWeight="700"
          >
            Policy
          </text>
          <text
            x={centerX}
            y={centerY + 15}
            textAnchor="middle"
            fill="#FFFFFF"
            fontSize="14"
            fontWeight="500"
          >
            Object
          </text>
        </g>
      </Box>
    </Box>
  )
}
