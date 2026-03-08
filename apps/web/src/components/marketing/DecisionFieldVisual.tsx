/**
 * Hero: Decision Field Background
 * Soft grid + faint nodes + sparse connecting lines
 * One dominant left-to-right flow path (Policy → Outcomes)
 */
import React, { useEffect, useRef, useState } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../../theme/healthForesightTheme'

export default function DecisionFieldVisual() {
  const svgRef = useRef<SVGSVGElement>(null)
  const [connections, setConnections] = useState<Array<{ from: number; to: number; opacity: number; time: number }>>([])
  const [policyGlow, setPolicyGlow] = useState(0.4)

  useEffect(() => {
    // Create initial nodes
    const nodeCount = 15
    const nodes: Array<{ x: number; y: number; id: number }> = []
    for (let i = 0; i < nodeCount; i++) {
      nodes.push({
        x: 100 + (i / (nodeCount - 1)) * 500,
        y: 100 + Math.sin(i * 0.5) * 80 + Math.random() * 40,
        id: i,
      })
    }

    // Policy node glow animation
    let glowDirection = 1
    const glowInterval = setInterval(() => {
      setPolicyGlow((prev) => {
        const newValue = prev + glowDirection * 0.05
        if (newValue >= 0.7) glowDirection = -1
        if (newValue <= 0.4) glowDirection = 1
        return Math.max(0.4, Math.min(0.7, newValue))
      })
    }, 200)

    // Connection discovery animation (every 3-5 seconds)
    const discoverConnection = () => {
      const fromIdx = Math.floor(Math.random() * (nodeCount - 1))
      const toIdx = fromIdx + 1 + Math.floor(Math.random() * 3)
      if (toIdx < nodeCount) {
        setConnections((prev) => [
          ...prev,
          { from: fromIdx, to: toIdx, opacity: 1, time: Date.now() },
        ])
        // Fade to 15% after 200-300ms
        setTimeout(() => {
          setConnections((prev) =>
            prev.map((conn) =>
              conn.from === fromIdx && conn.to === toIdx
                ? { ...conn, opacity: 0.15 }
                : conn
            )
          )
        }, 250)
      }
    }

    // Initial connections
    discoverConnection()
    const connectionInterval = setInterval(discoverConnection, 3500)

    return () => {
      clearInterval(glowInterval)
      clearInterval(connectionInterval)
    }
  }, [])

  const nodeCount = 15
  const nodes = Array.from({ length: nodeCount }, (_, i) => ({
    x: 100 + (i / (nodeCount - 1)) * 500,
    y: 100 + Math.sin(i * 0.5) * 80 + (i % 3) * 15,
    id: i,
    isPolicy: i === 2,
  }))

  return (
    <Box
      sx={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        opacity: 0.08,
        zIndex: 0,
      }}
    >
      <Box
        component="svg"
        ref={svgRef}
        viewBox="0 0 600 400"
        sx={{
          width: '100%',
          height: '100%',
        }}
      >
        <defs>
          <pattern id="softGrid" x="0" y="0" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#6366F1" strokeWidth="0.5" opacity="0.05" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#softGrid)" />

        {/* Connections - subtle */}
        {connections.map((conn, idx) => {
          const fromNode = nodes[conn.from]
          const toNode = nodes[conn.to]
          if (!fromNode || !toNode) return null
          return (
            <line
              key={idx}
              x1={fromNode.x}
              y1={fromNode.y}
              x2={toNode.x}
              y2={toNode.y}
              stroke="#6366F1"
              strokeWidth="1.5"
              opacity={conn.opacity * 0.3}
            />
          )
        })}

        {/* Dominant flow path (Policy → Outcomes) - subtle */}
        <path
          d={`M ${nodes[2].x} ${nodes[2].y} Q ${nodes[7].x} ${nodes[7].y - 20} ${nodes[12].x} ${nodes[12].y}`}
          fill="none"
          stroke="#6366F1"
          strokeWidth="2"
          opacity="0.15"
        />

        {/* Nodes - very subtle */}
        {nodes.map((node) => (
          <g key={node.id}>
            {node.isPolicy ? (
              <circle
                cx={node.x}
                cy={node.y}
                r="5"
                fill="#6366F1"
                opacity={policyGlow * 0.3}
              />
            ) : (
              <circle
                cx={node.x}
                cy={node.y}
                r="2.5"
                fill="#9CA3AF"
                opacity="0.2"
              />
            )}
          </g>
        ))}
      </Box>
    </Box>
  )
}
