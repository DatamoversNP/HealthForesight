/**
 * How It Works Section 5: Behavior Signal Map
 * Event-driven pulses, not constant motion
 */
import React, { useEffect, useState } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'

export default function BehaviorSignalMap() {
  const [activeConnections, setActiveConnections] = useState<Array<{ from: number; to: number; pulse: number }>>([])
  const [hasAnimated, setHasAnimated] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !hasAnimated) {
          setHasAnimated(true)
          // Trigger pulses sequentially
          const connections = [
            { from: 0, to: 1 }, // Providers to Patients
            { from: 1, to: 2 }, // Patients to Sites
            { from: 0, to: 2 }, // Providers to Sites
          ]
          connections.forEach((conn, idx) => {
            setTimeout(() => {
              setActiveConnections((prev) => [...prev, { ...conn, pulse: 1 }])
              setTimeout(() => {
                setActiveConnections((prev) =>
                  prev.map((c) =>
                    c.from === conn.from && c.to === conn.to ? { ...c, pulse: 0 } : c
                  )
                )
              }, 600)
            }, idx * 800)
          })
        }
      },
      { threshold: 0.3 }
    )

    const element = document.getElementById('behavior-signal-map')
    if (element) {
      observer.observe(element)
    }

    return () => observer.disconnect()
  }, [hasAnimated])

  const nodes = [
    { x: 200, y: 150, label: 'Providers', color: healthForesightColors.primary.main },
    { x: 400, y: 150, label: 'Patients', color: healthForesightColors.accent.main },
    { x: 300, y: 250, label: 'Sites', color: healthForesightColors.amber.main },
  ]

  const connections = [
    { from: 0, to: 1, label: 'Compliance' },
    { from: 1, to: 2, label: 'Substitution' },
    { from: 0, to: 2, label: 'Adaptation' },
  ]

  return (
    <Box
      id="behavior-signal-map"
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
        viewBox="0 0 600 400"
        sx={{
          width: '100%',
          height: '100%',
          maxHeight: '400px',
        }}
      >
        {/* Connections - pulse only when active */}
        {connections.map((conn, idx) => {
          const fromNode = nodes[conn.from]
          const toNode = nodes[conn.to]
          const active = activeConnections.find(
            (c) => c.from === conn.from && c.to === conn.to
          )
          const pulse = active?.pulse || 0

          return (
            <g key={idx}>
              <line
                x1={fromNode.x}
                y1={fromNode.y}
                x2={toNode.x}
                y2={toNode.y}
                stroke={fromNode.color}
                strokeWidth={3 + pulse * 2}
                opacity={0.3 + pulse * 0.5}
                style={{ transition: 'all 300ms ease-out' }}
              />
              {pulse > 0.5 && (
                <text
                  x={(fromNode.x + toNode.x) / 2}
                  y={(fromNode.y + toNode.y) / 2 - 8}
                  textAnchor="middle"
                  fill="#FFFFFF"
                  fontSize="11"
                  fontWeight="700"
                  style={{ transition: 'opacity 200ms ease-out' }}
                >
                  {conn.label}
                </text>
              )}
            </g>
          )
        })}

        {/* Nodes */}
        {nodes.map((node, idx) => (
          <g key={idx}>
            <circle
              cx={node.x}
              cy={node.y}
              r="35"
              fill={node.color}
              opacity="0.9"
            />
            <circle
              cx={node.x}
              cy={node.y}
              r="28"
              fill="#FFFFFF"
            />
            <text
              x={node.x}
              y={node.y + 6}
              textAnchor="middle"
              fill={node.color}
              fontSize="13"
              fontWeight="700"
            >
              {node.label}
            </text>
          </g>
        ))}
      </Box>
    </Box>
  )
}
