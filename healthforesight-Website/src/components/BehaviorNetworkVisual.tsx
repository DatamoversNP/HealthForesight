/**
 * Solution 3: Provider & Patient Behavior Network Visual
 * Abstract network with nodes representing providers/patients, edges shifting over time
 */
import React, { useEffect, useRef, useState } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'

interface Node {
  id: number
  x: number
  y: number
  type: 'provider' | 'patient'
  size: number
}

interface Edge {
  from: number
  to: number
  strength: number
}

export default function BehaviorNetworkVisual() {
  const svgRef = useRef<SVGSVGElement>(null)
  const [nodes, setNodes] = useState<Node[]>([])
  const [edges, setEdges] = useState<Edge[]>([])
  const [time, setTime] = useState(0)

  useEffect(() => {
    // Initialize nodes
    const initialNodes: Node[] = []
    const nodeCount = 12
    const centerX = 300
    const centerY = 200
    const radius = 120

    for (let i = 0; i < nodeCount; i++) {
      const angle = (i / nodeCount) * Math.PI * 2
      initialNodes.push({
        id: i,
        x: centerX + Math.cos(angle) * radius,
        y: centerY + Math.sin(angle) * radius,
        type: i % 3 === 0 ? 'provider' : 'patient',
        size: i % 3 === 0 ? 12 : 8,
      })
    }

    // Initialize edges (connections)
    const initialEdges: Edge[] = []
    for (let i = 0; i < nodeCount; i++) {
      for (let j = i + 1; j < nodeCount; j++) {
        if (Math.random() > 0.7) {
          initialEdges.push({
            from: i,
            to: j,
            strength: Math.random(),
          })
        }
      }
    }

    setNodes(initialNodes)
    setEdges(initialEdges)

    // Animate nodes shifting
    const animate = () => {
      setTime((prev) => prev + 0.02)
      setNodes((prevNodes) =>
        prevNodes.map((node, idx) => {
          const angle = (idx / nodeCount) * Math.PI * 2 + time
          const baseRadius = 120
          const shift = Math.sin(time * 2 + idx) * 15
          return {
            ...node,
            x: centerX + Math.cos(angle) * (baseRadius + shift),
            y: centerY + Math.sin(angle) * (baseRadius + shift),
          }
        })
      )
      requestAnimationFrame(animate)
    }

    const animationId = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(animationId)
  }, [time])

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
          <filter id="nodeGlow">
            <feGaussianBlur stdDeviation="2" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Edges (connections) */}
        {edges.map((edge, idx) => {
          const fromNode = nodes[edge.from]
          const toNode = nodes[edge.to]
          if (!fromNode || !toNode) return null

          return (
            <line
              key={idx}
              x1={fromNode.x}
              y1={fromNode.y}
              x2={toNode.x}
              y2={toNode.y}
              stroke={healthForesightColors.accent.main}
              strokeWidth={edge.strength * 2 + 0.5}
              opacity={0.3 + edge.strength * 0.3}
            />
          )
        })}

        {/* Nodes */}
        {nodes.map((node) => (
          <g key={node.id}>
            <circle
              cx={node.x}
              cy={node.y}
              r={node.size}
              fill={node.type === 'provider' ? healthForesightColors.primary.main : healthForesightColors.accent.main}
              filter="url(#nodeGlow)"
              opacity="0.9"
            />
            <circle
              cx={node.x}
              cy={node.y}
              r={node.size - 2}
              fill="none"
              stroke="#FFFFFF"
              strokeWidth="1"
              opacity="0.5"
            />
          </g>
        ))}

        {/* Labels */}
        <text
          x="50"
          y="30"
          fill="#FFFFFF"
          fontSize="14"
          fontWeight="700"
        >
          Provider & Patient Response Patterns
        </text>
      </Box>
    </Box>
  )
}
