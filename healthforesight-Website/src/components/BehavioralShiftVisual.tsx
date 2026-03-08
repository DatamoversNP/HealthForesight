/**
 * Section 9: Behavioral Intelligence - Directional Shift
 * Clustered network with labeled groups
 * At "policy date", edges re-route (one-time shift)
 */
import React, { useEffect, useRef, useState } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'

export default function BehavioralShiftVisual() {
  const svgRef = useRef<SVGSVGElement>(null)
  const [shiftProgress, setShiftProgress] = useState(0)
  const [labelsVisible, setLabelsVisible] = useState(false)
  const [hasAnimated, setHasAnimated] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !hasAnimated) {
          setHasAnimated(true)
          // Edges re-route over 300ms
          let startTime: number | null = null
          const animate = (timestamp: number) => {
            if (!startTime) startTime = timestamp
            const elapsed = timestamp - startTime
            const progress = Math.min(elapsed / 300, 1)
            setShiftProgress(progress)
            if (progress < 1) {
              requestAnimationFrame(animate)
            } else {
              // Labels appear after shift
              setTimeout(() => setLabelsVisible(true), 100)
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

  const providers = { x: 150, y: 100 }
  const patients = { x: 450, y: 100 }
  const sites = { x: 300, y: 250 }

  // Initial connections (before shift)
  const initialConnections = [
    { from: providers, to: sites, label: 'Compliance', color: healthForesightColors.primary.main },
    { from: patients, to: sites, label: 'Substitution', color: healthForesightColors.accent.main },
    { from: patients, to: providers, label: 'Fallback', color: healthForesightColors.amber.main },
  ]

  // Shifted connections (after policy)
  const shiftedConnections = [
    { from: providers, to: { x: sites.x + 30, y: sites.y - 20 }, label: 'Site shift', color: healthForesightColors.primary.main },
    { from: patients, to: { x: sites.x - 30, y: sites.y - 20 }, label: 'Timing shift', color: healthForesightColors.accent.main },
    { from: patients, to: { x: providers.x + 20, y: providers.y + 30 }, label: 'Fallback', color: healthForesightColors.amber.main },
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
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="10"
            refX="9"
            refY="3"
            orient="auto"
            markerUnits="strokeWidth"
          >
            <polygon points="0 0, 10 3, 0 6" fill="#6366F1" opacity="1" />
          </marker>
        </defs>

        {/* Connections (interpolate between initial and shifted) - brighter, thicker */}
        {initialConnections.map((conn, idx) => {
          const shifted = shiftedConnections[idx]
          const currentTo = {
            x: conn.to.x + (shifted.to.x - conn.to.x) * shiftProgress,
            y: conn.to.y + (shifted.to.y - conn.to.y) * shiftProgress,
          }
          const dx = currentTo.x - conn.from.x
          const dy = currentTo.y - conn.from.y
          const angle = Math.atan2(dy, dx)
          const startX = conn.from.x + Math.cos(angle) * 40
          const startY = conn.from.y + Math.sin(angle) * 40
          const endX = currentTo.x - Math.cos(angle) * 40
          const endY = currentTo.y - Math.sin(angle) * 40

          const colors = ['#6366F1', '#2EC4C6', '#E6A23C']
          return (
            <g key={idx}>
              <path
                d={`M ${startX} ${startY} L ${endX} ${endY}`}
                fill="none"
                stroke={colors[idx]}
                strokeWidth="4"
                opacity="1"
                markerEnd="url(#arrowhead)"
              />
              {labelsVisible && (
                <text
                  x={(startX + endX) / 2}
                  y={(startY + endY) / 2 - 10}
                  textAnchor="middle"
                  fill="#FFFFFF"
                  fontSize="12"
                  fontWeight="700"
                  style={{ transition: 'opacity 200ms ease-out' }}
                >
                  {shifted.label}
                </text>
              )}
            </g>
          )
        })}

        {/* Clusters - brighter, larger */}
        {[
          { pos: providers, label: 'Providers', color: '#6366F1' },
          { pos: patients, label: 'Patients', color: '#2EC4C6' },
          { pos: sites, label: 'Sites', color: '#E6A23C' },
        ].map((cluster, idx) => (
          <g key={idx}>
            <circle
              cx={cluster.pos.x}
              cy={cluster.pos.y}
              r="45"
              fill={cluster.color}
              opacity="0.25"
            />
            <circle
              cx={cluster.pos.x}
              cy={cluster.pos.y}
              r="35"
              fill={cluster.color}
              opacity="1"
            />
            <text
              x={cluster.pos.x}
              y={cluster.pos.y + 6}
              textAnchor="middle"
              fill="#FFFFFF"
              fontSize="15"
              fontWeight="700"
            >
              {cluster.label}
            </text>
          </g>
        ))}
      </Box>
    </Box>
  )
}
