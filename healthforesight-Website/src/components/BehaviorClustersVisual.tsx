/**
 * Section 7: Role-Based Behavior Clusters
 * Providers, Patients, Sites - with directional response patterns
 */
import React, { useEffect, useRef, useState } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'

export default function BehaviorClustersVisual() {
  const svgRef = useRef<SVGSVGElement>(null)
  const [time, setTime] = useState(0)

  useEffect(() => {
    const animate = () => {
      setTime((prev) => (prev + 0.01) % (Math.PI * 2))
      requestAnimationFrame(animate)
    }
    const animationId = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(animationId)
  }, [])

  const centerX = 300
  const centerY = 200

  // Three clusters
  const providers = {
    x: centerX - 120,
    y: centerY - 60,
    nodes: Array.from({ length: 6 }, (_, i) => ({
      angle: (i / 6) * Math.PI * 2,
      distance: 30 + Math.sin(time + i) * 5,
    })),
    color: healthForesightColors.primary.main,
    label: 'Providers',
  }

  const patients = {
    x: centerX + 120,
    y: centerY - 60,
    nodes: Array.from({ length: 6 }, (_, i) => ({
      angle: (i / 6) * Math.PI * 2,
      distance: 30 + Math.sin(time + i + 2) * 5,
    })),
    color: healthForesightColors.accent.main,
    label: 'Patients',
  }

  const sites = {
    x: centerX,
    y: centerY + 80,
    nodes: Array.from({ length: 5 }, (_, i) => ({
      angle: (i / 5) * Math.PI * 2,
      distance: 25 + Math.sin(time + i + 1) * 4,
    })),
    color: healthForesightColors.amber.main,
    label: 'Sites',
  }

  const clusters = [providers, patients, sites]

  // Response patterns (arrows between clusters)
  const responses = [
    { from: providers, to: sites, label: 'Compliance', color: healthForesightColors.primary.main },
    { from: patients, to: sites, label: 'Substitution', color: healthForesightColors.accent.main },
    { from: patients, to: providers, label: 'Fallback', color: healthForesightColors.amber.main },
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
          <filter id="clusterGlow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Response arrows */}
        {responses.map((response, idx) => {
          const dx = response.to.x - response.from.x
          const dy = response.to.y - response.from.y
          const angle = Math.atan2(dy, dx)
          const startX = response.from.x + Math.cos(angle) * 40
          const startY = response.from.y + Math.sin(angle) * 40
          const endX = response.to.x - Math.cos(angle) * 40
          const endY = response.to.y - Math.sin(angle) * 40

          return (
            <g key={idx}>
              <path
                d={`M ${startX} ${startY} L ${endX} ${endY}`}
                fill="none"
                stroke={response.color}
                strokeWidth="4"
                opacity="0.8"
                markerEnd="url(#arrowhead)"
              />
              <text
                x={(startX + endX) / 2}
                y={(startY + endY) / 2 - 10}
                textAnchor="middle"
                fill="#FFFFFF"
                fontSize="13"
                fontWeight="700"
              >
                {response.label}
              </text>
            </g>
          )
        })}

        {/* Arrow marker */}
        <defs>
            <marker
            id="arrowhead"
            markerWidth="12"
            markerHeight="12"
            refX="11"
            refY="4"
            orient="auto"
          >
            <polygon points="0 0, 12 4, 0 8" fill={healthForesightColors.primary.main} opacity="0.9" />
          </marker>
        </defs>

        {/* Clusters */}
        {clusters.map((cluster) => (
          <g key={cluster.label}>
            {/* Cluster center */}
            <circle
              cx={cluster.x}
              cy={cluster.y}
              r="35"
              fill={cluster.color}
              filter="url(#clusterGlow)"
              opacity="0.2"
            />
            <circle
              cx={cluster.x}
              cy={cluster.y}
              r="25"
              fill={cluster.color}
              opacity="0.9"
            />
            <text
              x={cluster.x}
              y={cluster.y + 5}
              textAnchor="middle"
              fill="#FFFFFF"
              fontSize="12"
              fontWeight="700"
            >
              {cluster.label}
            </text>

            {/* Cluster nodes */}
            {cluster.nodes.map((node, idx) => {
              const x = cluster.x + Math.cos(node.angle) * node.distance
              const y = cluster.y + Math.sin(node.angle) * node.distance
              return (
                <circle
                  key={idx}
                  cx={x}
                  cy={y}
                  r="8"
                  fill={cluster.color}
                  opacity="1"
                  stroke="#FFFFFF"
                  strokeWidth="1.5"
                />
              )
            })}
          </g>
        ))}
      </Box>
    </Box>
  )
}
