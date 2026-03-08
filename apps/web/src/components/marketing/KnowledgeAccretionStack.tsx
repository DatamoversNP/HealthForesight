/**
 * How It Works Section 6: Knowledge Accretion Stack
 * Horizontal layers stacking upward
 */
import React, { useEffect, useState } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../../theme/healthForesightTheme'

export default function KnowledgeAccretionStack() {
  const [visibleLayers, setVisibleLayers] = useState<boolean[]>([false, false, false, false, false])
  const [hasAnimated, setHasAnimated] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !hasAnimated) {
          setHasAnimated(true)
          // Layers add sequentially with settling motion
          setTimeout(() => setVisibleLayers([true, false, false, false, false]), 0)
          setTimeout(() => setVisibleLayers([true, true, false, false, false]), 400)
          setTimeout(() => setVisibleLayers([true, true, true, false, false]), 800)
          setTimeout(() => setVisibleLayers([true, true, true, true, false]), 1200)
          setTimeout(() => setVisibleLayers([true, true, true, true, true]), 1600)
        }
      },
      { threshold: 0.3 }
    )

    const element = document.getElementById('knowledge-stack')
    if (element) {
      observer.observe(element)
    }

    return () => observer.disconnect()
  }, [hasAnimated])

  const layers = [
    { label: 'Policy A', outcome: 'Elasticity +0.12' },
    { label: 'Policy B', outcome: 'Confidence +8%' },
    { label: 'Policy C', outcome: 'Precision +15%' },
    { label: 'Policy D', outcome: 'Reliability +22%' },
    { label: 'Policy E', outcome: 'Governance ↑' },
  ]

  const baseY = 300
  const layerHeight = 40
  const layerSpacing = 5

  return (
    <Box
      id="knowledge-stack"
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
        {layers.map((layer, idx) => {
          const y = baseY - idx * (layerHeight + layerSpacing)
          const isVisible = visibleLayers[idx]
          const offset = isVisible ? 0 : 20

          return (
            <g key={idx}>
              <rect
                x="100"
                y={y - layerHeight / 2 - offset}
                width="400"
                height={layerHeight}
                rx="4"
                fill={healthForesightColors.primary.main}
                opacity={isVisible ? 0.9 - idx * 0.1 : 0}
                style={{ transition: 'all 300ms cubic-bezier(0.4, 0, 0.2, 1)' }}
              />
              <text
                x="120"
                y={y - offset + 5}
                fill="#FFFFFF"
                fontSize="14"
                fontWeight="700"
                opacity={isVisible ? 1 : 0}
                style={{ transition: 'opacity 300ms ease-out' }}
              >
                {layer.label}
              </text>
              <text
                x="480"
                y={y - offset + 5}
                textAnchor="end"
                fill="#FFFFFF"
                fontSize="13"
                fontWeight="600"
                opacity={isVisible ? 1 : 0}
                style={{ transition: 'opacity 300ms ease-out' }}
              >
                {layer.outcome}
              </text>
            </g>
          )
        })}

        {/* Base line */}
        <line
          x1="100"
          y1={baseY + 20}
          x2="500"
          y2={baseY + 20}
          stroke={healthForesightColors.neutral.mid}
          strokeWidth="2"
          opacity="0.3"
        />
      </Box>
    </Box>
  )
}
