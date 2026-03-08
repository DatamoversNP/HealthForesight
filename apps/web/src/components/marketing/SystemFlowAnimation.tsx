/**
 * Hero Section: System Flow Animation
 * Nodes connecting/disconnecting, policy highlighted, time flow (left → right)
 */
import React, { useEffect, useRef, useState } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../../theme/healthForesightTheme'

export default function SystemFlowAnimation() {
  const svgRef = useRef<SVGSVGElement>(null)
  const [time, setTime] = useState(0)
  const animationRef = useRef<number>()

  useEffect(() => {
    const animate = () => {
      setTime((prev) => (prev + 0.01) % (Math.PI * 2))
      animationRef.current = requestAnimationFrame(animate)
    }
    animationRef.current = requestAnimationFrame(animate)

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [])

  const nodeCount = 12
  const centerX = 300
  const centerY = 200
  const baseRadius = 140

  // Create nodes in a flowing pattern
  const nodes = Array.from({ length: nodeCount }, (_, i) => {
    const angle = (i / nodeCount) * Math.PI * 2 + time * 0.3
    const radius = baseRadius + Math.sin(time * 2 + i) * 20
    return {
      x: centerX + Math.cos(angle) * radius,
      y: centerY + Math.sin(angle) * radius,
      id: i,
      isPolicy: i === 3, // Highlight one as "Policy"
    }
  })

  // Create connections between nearby nodes
  const connections: Array<{ from: number; to: number; strength: number }> = []
  nodes.forEach((node, i) => {
    nodes.slice(i + 1).forEach((otherNode, j) => {
      const dx = node.x - otherNode.x
      const dy = node.y - otherNode.y
      const distance = Math.sqrt(dx * dx + dy * dy)
      if (distance < 120) {
        connections.push({
          from: i,
          to: i + j + 1,
          strength: 1 - distance / 120,
        })
      }
    })
  })

  return (
    <Box
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
        ref={svgRef}
        viewBox="0 0 600 400"
        sx={{
          width: '100%',
          height: '100%',
          maxHeight: '400px',
        }}
      >
        <defs>
          <filter id="nodeGlow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="policyGlow">
            <feGaussianBlur stdDeviation="6" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Connections */}
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
              stroke={healthForesightColors.primary.light}
              strokeWidth={conn.strength * 3 + 2}
              opacity={0.6 + conn.strength * 0.3}
            />
          )
        })}

        {/* Nodes */}
        {nodes.map((node) => (
          <g key={node.id}>
            {node.isPolicy ? (
              <>
                {/* Policy node - highlighted */}
                <circle
                  cx={node.x}
                  cy={node.y}
                  r="18"
                  fill={healthForesightColors.primary.main}
                  filter="url(#policyGlow)"
                  opacity="0.9"
                />
                <circle
                  cx={node.x}
                  cy={node.y}
                  r="14"
                  fill="#FFFFFF"
                />
                <text
                  x={node.x}
                  y={node.y + 5}
                  textAnchor="middle"
                  fill="#FFFFFF"
                  fontSize="13"
                  fontWeight="700"
                >
                  Policy
                </text>
              </>
            ) : (
              <>
                <circle
                  cx={node.x}
                  cy={node.y}
                  r="10"
                  fill={healthForesightColors.accent.main}
                  filter="url(#nodeGlow)"
                  opacity="0.9"
                  stroke="#FFFFFF"
                  strokeWidth="1.5"
                />
              </>
            )}
          </g>
        ))}

        {/* Time flow indicator (left to right) */}
        <path
          d="M 50 350 Q 300 340 550 350"
          fill="none"
          stroke={healthForesightColors.accent.main}
          strokeWidth="3"
          strokeDasharray="6,4"
          opacity="0.6"
        />
        <circle
          cx={50 + (time / (Math.PI * 2)) * 500}
          cy={350}
          r="8"
          fill={healthForesightColors.accent.main}
          opacity="1"
          stroke="#FFFFFF"
          strokeWidth="2"
        />
        <text
          x="50"
          y="340"
          fill={healthForesightColors.accent.light}
          fontSize="14"
          fontWeight="700"
        >
          Time →
        </text>
      </Box>
    </Box>
  )
}
