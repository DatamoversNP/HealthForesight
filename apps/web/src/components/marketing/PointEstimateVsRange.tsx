/**
 * Visual 3: Point Estimate vs Range-Based Reality
 * Left: single bar, Right: same bar expands into range band with downside tail
 */
import React, { useEffect, useState } from 'react'
import { Box, Typography } from '@mui/material'
import { healthForesightColors } from '../../theme/healthForesightTheme'

export default function PointEstimateVsRange() {
  const [expanded, setExpanded] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          setTimeout(() => setExpanded(true), 500)
        }
      },
      { threshold: 0.2 }
    )

    const element = document.getElementById('point-estimate-vs-range')
    if (element) observer.observe(element)

    return () => observer.disconnect()
  }, [])

  const width = 350
  const height = 300
  const padding = 50
  const barWidth = 60
  const barHeight = 150
  const centerX = width / 2

  return (
    <Box
      id="point-estimate-vs-range"
      sx={{
        display: 'flex',
        flexDirection: { xs: 'column', md: 'row' },
        gap: 6,
        justifyContent: 'center',
        mb: 4,
      }}
    >
      {/* Left: Point Estimate */}
      <Box sx={{ flex: 1, textAlign: 'center' }}>
        <Typography
          variant="h6"
          sx={{
            mb: 3,
            fontSize: '16px',
            fontWeight: 700,
            color: healthForesightColors.neutral.dark,
          }}
        >
          Point Estimate
        </Typography>
        <Box
          component="svg"
          viewBox={`0 0 ${width} ${height}`}
          sx={{
            width: '100%',
            height: '100%',
            maxHeight: '350px',
          }}
        >
          {/* Single bar */}
          <rect
            x={centerX - barWidth / 2}
            y={height - padding - barHeight}
            width={barWidth}
            height={barHeight}
            fill={healthForesightColors.primary.main}
            rx="4"
          />
          <text
            x={centerX}
            y={height - padding - barHeight - 10}
            textAnchor="middle"
            fill={healthForesightColors.neutral.dark}
            fontSize="12"
            fontWeight="600"
          >
            $19M
          </text>
          <text
            x={centerX}
            y={height - 20}
            textAnchor="middle"
            fill={healthForesightColors.neutral.dark}
            fontSize="11"
            fontWeight="600"
          >
            Expected Savings
          </text>
        </Box>
      </Box>

      {/* Right: Range-Based Reality */}
      <Box sx={{ flex: 1, textAlign: 'center' }}>
        <Typography
          variant="h6"
          sx={{
            mb: 3,
            fontSize: '16px',
            fontWeight: 700,
            color: healthForesightColors.neutral.dark,
          }}
        >
          Range-Based Reality
        </Typography>
        <Box
          component="svg"
          viewBox={`0 0 ${width} ${height}`}
          sx={{
            width: '100%',
            height: '100%',
            maxHeight: '350px',
          }}
        >
          {/* Range band */}
          {expanded && (
            <g>
              {/* Min bar */}
              <rect
                x={centerX - 80}
                y={height - padding - 100}
                width={barWidth}
                height={100}
                fill={healthForesightColors.accent.main}
                opacity={0.6}
                rx="4"
              />
              <text
                x={centerX - 50}
                y={height - padding - 100 - 10}
                textAnchor="middle"
                fill={healthForesightColors.accent.main}
                fontSize="11"
                fontWeight="600"
              >
                $13M
              </text>

              {/* Max bar */}
              <rect
                x={centerX + 20}
                y={height - padding - 180}
                width={barWidth}
                height={180}
                fill={healthForesightColors.primary.main}
                opacity={0.6}
                rx="4"
              />
              <text
                x={centerX + 50}
                y={height - padding - 180 - 10}
                textAnchor="middle"
                fill={healthForesightColors.primary.main}
                fontSize="11"
                fontWeight="600"
              >
                $25M
              </text>

              {/* Downside tail (highlighted in red) */}
              <rect
                x={centerX - 140}
                y={height - padding - 60}
                width={barWidth}
                height={60}
                fill={healthForesightColors.amber.main}
                opacity={0.8}
                rx="4"
              />
              <text
                x={centerX - 110}
                y={height - padding - 60 - 10}
                textAnchor="middle"
                fill={healthForesightColors.amber.main}
                fontSize="11"
                fontWeight="700"
              >
                $6M
              </text>
              <text
                x={centerX - 110}
                y={height - 20}
                textAnchor="middle"
                fill={healthForesightColors.amber.main}
                fontSize="10"
                fontWeight="600"
              >
                Downside Risk
              </text>

              {/* Range connector */}
              <line
                x1={centerX - 50}
                y1={height - padding - 50}
                x2={centerX + 50}
                y2={height - padding - 90}
                stroke={healthForesightColors.neutral.mid}
                strokeWidth="2"
                strokeDasharray="4 4"
                opacity={0.5}
              />
            </g>
          )}
        </Box>
      </Box>
    </Box>
  )
}
