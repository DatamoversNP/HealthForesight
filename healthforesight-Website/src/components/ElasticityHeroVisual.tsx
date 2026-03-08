/**
 * Hero Visual: Conceptual line graph showing forecast vs reality
 * Line starts thin → becomes clearer → splits into expected (teal) and observed (purple)
 */
import React, { useEffect, useState } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'

export default function ElasticityHeroVisual() {
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    let startTime: number | null = null
    const duration = 3000 // 3 seconds

    const animate = (timestamp: number) => {
      if (!startTime) startTime = timestamp
      const elapsed = timestamp - startTime
      const newProgress = Math.min(elapsed / duration, 1)
      setProgress(newProgress)

      if (newProgress < 1) {
        requestAnimationFrame(animate)
      }
    }

    requestAnimationFrame(animate)
  }, [])

  const width = 400
  const height = 250
  const padding = 40
  const chartWidth = width - padding * 2
  const chartHeight = height - padding * 2

  // Paths
  const expectedPath = `M ${padding} ${padding + chartHeight * 0.6} 
    Q ${padding + chartWidth * 0.3} ${padding + chartHeight * 0.4} 
    ${padding + chartWidth * 0.5} ${padding + chartHeight * 0.3}
    T ${padding + chartWidth} ${padding + chartHeight * 0.2}`

  const observedPath = `M ${padding} ${padding + chartHeight * 0.6} 
    Q ${padding + chartWidth * 0.3} ${padding + chartHeight * 0.5} 
    ${padding + chartWidth * 0.5} ${padding + chartHeight * 0.45}
    T ${padding + chartWidth} ${padding + chartHeight * 0.5}`

  const splitPoint = 0.4 // Where paths split
  const beforeSplitProgress = Math.min(progress / splitPoint, 1)
  const afterSplitProgress = progress > splitPoint ? (progress - splitPoint) / (1 - splitPoint) : 0

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
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="xMidYMid meet"
        sx={{
          width: '100%',
          height: '100%',
        }}
      >
        {/* Initial thin line (before split) */}
        {progress < splitPoint && (
          <path
            d={`M ${padding} ${padding + chartHeight * 0.6} L ${padding + chartWidth * beforeSplitProgress} ${padding + chartHeight * 0.6}`}
            fill="none"
            stroke="rgba(255, 255, 255, 0.3)"
            strokeWidth="1"
            strokeDasharray="2 2"
          />
        )}

        {/* Expected path (teal) */}
        {progress >= splitPoint && (
          <path
            d={expectedPath}
            fill="none"
            stroke={healthForesightColors.accent.main}
            strokeWidth={2 + afterSplitProgress * 2}
            strokeDasharray={`${afterSplitProgress * 400} 400`}
            opacity={0.7 + afterSplitProgress * 0.3}
          />
        )}

        {/* Observed path (purple) */}
        {progress >= splitPoint && (
          <path
            d={observedPath}
            fill="none"
            stroke={healthForesightColors.primary.main}
            strokeWidth={2 + afterSplitProgress * 2}
            strokeDasharray={`${afterSplitProgress * 400} 400`}
            opacity={0.7 + afterSplitProgress * 0.3}
          />
        )}

        {/* Labels */}
        {progress > 0.7 && (
          <g opacity={(progress - 0.7) / 0.3}>
            <text
              x={padding + chartWidth * 0.7}
              y={padding + chartHeight * 0.15}
              fill={healthForesightColors.accent.main}
              fontSize="12"
              fontWeight="600"
            >
              Expected
            </text>
            <text
              x={padding + chartWidth * 0.7}
              y={padding + chartHeight * 0.55}
              fill={healthForesightColors.primary.main}
              fontSize="12"
              fontWeight="600"
            >
              Observed
            </text>
          </g>
        )}
      </Box>
    </Box>
  )
}
