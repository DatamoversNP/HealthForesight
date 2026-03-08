/**
 * Section 4: Category Badge + Concept Diagram
 * Badge fades in, nodes appear sequentially, connector draws last
 */
import React, { useEffect, useRef, useState } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'

export default function CategoryBadgeVisual() {
  const svgRef = useRef<SVGSVGElement>(null)
  const [badgeOpacity, setBadgeOpacity] = useState(0)
  const [nodeOpacities, setNodeOpacities] = useState([0, 0, 0, 0])
  const [lineProgress, setLineProgress] = useState(0)
  const [hasAnimated, setHasAnimated] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !hasAnimated) {
          setHasAnimated(true)
          // Badge fades in (300ms)
          setTimeout(() => setBadgeOpacity(1), 0)
          // Nodes appear sequentially (120ms stagger)
          setTimeout(() => setNodeOpacities([1, 0, 0, 0]), 300)
          setTimeout(() => setNodeOpacities([1, 1, 0, 0]), 420)
          setTimeout(() => setNodeOpacities([1, 1, 1, 0]), 540)
          setTimeout(() => setNodeOpacities([1, 1, 1, 1]), 660)
          // Connector draws (350ms)
          setTimeout(() => {
            let startTime: number | null = null
            const animate = (timestamp: number) => {
              if (!startTime) startTime = timestamp
              const elapsed = timestamp - startTime
              const progress = Math.min(elapsed / 350, 1)
              setLineProgress(progress)
              if (progress < 1) {
                requestAnimationFrame(animate)
              }
            }
            requestAnimationFrame(animate)
          }, 780)
        }
      },
      { threshold: 0.3 }
    )

    if (svgRef.current) {
      observer.observe(svgRef.current)
    }

    return () => observer.disconnect()
  }, [hasAnimated])

  // Asymmetrical loop with forward tilt
  const nodes = [
    { x: 120, y: 220, label: 'Define' },
    { x: 280, y: 140, label: 'Predict' },
    { x: 420, y: 200, label: 'Observe' },
    { x: 480, y: 260, label: 'Learn' },
  ]

  const pathLength = 650 // Approximate

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
        {/* Category Badge */}
        <g opacity={badgeOpacity} style={{ transition: 'opacity 300ms ease-out' }}>
          <rect
            x="180"
            y="50"
            width="240"
            height="45"
            rx="22"
            fill="#6366F1"
            opacity="1"
          />
          <text
            x="300"
            y="78"
            textAnchor="middle"
            fill="#FFFFFF"
            fontSize="15"
            fontWeight="700"
            letterSpacing="0.5px"
          >
            Policy Impact Intelligence
          </text>
        </g>

        {/* Concept Loop - Asymmetrical with directional flow, touches all circles */}
        <path
          d={`M ${nodes[0].x} ${nodes[0].y} 
              Q ${(nodes[0].x + nodes[1].x) / 2} ${nodes[0].y - 30} ${nodes[1].x} ${nodes[1].y}
              Q ${(nodes[1].x + nodes[2].x) / 2} ${nodes[1].y + 30} ${nodes[2].x} ${nodes[2].y}
              Q ${(nodes[2].x + nodes[3].x) / 2} ${nodes[2].y + 30} ${nodes[3].x} ${nodes[3].y}
              Q ${(nodes[3].x + nodes[0].x) / 2} ${nodes[3].y - 30} ${nodes[0].x} ${nodes[0].y} Z`}
          fill="none"
          stroke="#6366F1"
          strokeWidth="5"
          strokeDasharray={`${lineProgress * pathLength} ${pathLength}`}
          opacity="1"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Nodes - pulse on arrival, then settle */}
        {nodes.map((node, idx) => {
          const nodeScale = nodeOpacities[idx] === 1 ? (idx === 0 ? 1.08 : 1) : 1
          return (
            <g key={idx}>
              <circle
                cx={node.x}
                cy={node.y}
                r={nodeScale * 30}
                fill="#6366F1"
                opacity={nodeOpacities[idx]}
                style={{ transition: 'opacity 200ms ease-out, r 200ms ease-out' }}
              />
              <circle
                cx={node.x}
                cy={node.y}
                r="22"
                fill="#FFFFFF"
                opacity={nodeOpacities[idx]}
              />
              <text
                x={node.x}
                y={node.y + 6}
                textAnchor="middle"
                fill="#6366F1"
                fontSize="12"
                fontWeight="700"
                opacity={nodeOpacities[idx]}
              >
                {node.label}
              </text>
            </g>
          )
        })}
      </Box>
    </Box>
  )
}
