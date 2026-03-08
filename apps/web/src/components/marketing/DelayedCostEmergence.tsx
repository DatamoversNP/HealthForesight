/**
 * Visual 4: Delayed Cost Emergence
 * Timeline with policy launch marker
 * Tracked cost dips, untracked cost rises later (lag)
 */
import React, { useEffect, useState } from 'react'
import { Box, Typography } from '@mui/material'
import { healthForesightColors } from '../../theme/healthForesightTheme'

export default function DelayedCostEmergence() {
  const [trackedProgress, setTrackedProgress] = useState(0)
  const [untrackedProgress, setUntrackedProgress] = useState(0)
  const [policyMarkerVisible, setPolicyMarkerVisible] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          // Lines draw from left to right (1200ms)
          let progress = 0
          const interval = setInterval(() => {
            progress += 0.01
            setTrackedProgress(Math.min(progress, 1))
            if (progress >= 0.4) {
              setPolicyMarkerVisible(true)
            }
            if (progress >= 0.6) {
              let untrackedProgress = 0
              const untrackedInterval = setInterval(() => {
                untrackedProgress += 0.015
                setUntrackedProgress(Math.min(untrackedProgress, 1))
                if (untrackedProgress >= 1) clearInterval(untrackedInterval)
              }, 20)
            }
            if (progress >= 1) clearInterval(interval)
          }, 12)
        }
      },
      { threshold: 0.2 }
    )

    const element = document.getElementById('delayed-cost-emergence')
    if (element) observer.observe(element)

    return () => observer.disconnect()
  }, [])

  const width = 700
  const height = 400
  const padding = 60
  const policyX = padding + (width - padding * 2) * 0.35

  // Tracked cost: dips slightly after launch
  const trackedPath = `M ${padding} ${padding + 200} 
    L ${policyX - 20} ${padding + 195}
    L ${policyX + 30} ${padding + 220}
    L ${policyX + 150} ${padding + 225}
    L ${width - padding} ${padding + 230}`

  // Untracked cost: rises later (lag)
  const untrackedPath = `M ${padding} ${padding + 250} 
    L ${policyX + 50} ${padding + 250}
    L ${policyX + 150} ${padding + 240}
    L ${policyX + 300} ${padding + 200}
    L ${width - padding} ${padding + 150}`

  return (
    <Box
      id="delayed-cost-emergence"
      sx={{
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        p: 3,
      }}
    >
      <Box
        component="svg"
        viewBox={`0 0 ${width} ${height}`}
        sx={{
          width: '100%',
          height: '100%',
          maxHeight: '450px',
        }}
      >
        {/* Axes */}
        <line
          x1={padding}
          y1={padding}
          x2={padding}
          y2={height - padding}
          stroke={healthForesightColors.neutral.mid}
          strokeWidth="2"
        />
        <line
          x1={padding}
          y1={height - padding}
          x2={width - padding}
          y2={height - padding}
          stroke={healthForesightColors.neutral.mid}
          strokeWidth="2"
        />

        {/* Axis labels */}
        <text
          x={padding - 10}
          y={padding + 50}
          textAnchor="end"
          fill={healthForesightColors.neutral.dark}
          fontSize="12"
          fontWeight="600"
        >
          Cost
        </text>
        <text
          x={width / 2}
          y={height - padding + 30}
          textAnchor="middle"
          fill={healthForesightColors.neutral.dark}
          fontSize="12"
          fontWeight="600"
        >
          Time →
        </text>

        {/* Policy Launch marker */}
        {policyMarkerVisible && (
          <line
            x1={policyX}
            y1={padding}
            x2={policyX}
            y2={height - padding}
            stroke={healthForesightColors.amber.main}
            strokeWidth="3"
            strokeDasharray="4 4"
          />
        )}
        {policyMarkerVisible && (
          <text
            x={policyX}
            y={padding - 10}
            textAnchor="middle"
            fill={healthForesightColors.amber.main}
            fontSize="12"
            fontWeight="700"
          >
            Policy Launch
          </text>
        )}

        {/* Tracked cost line */}
        <path
          d={trackedPath}
          fill="none"
          stroke={healthForesightColors.primary.main}
          strokeWidth="3"
          strokeDasharray={`${trackedProgress * 600} 600`}
          opacity={trackedProgress > 0 ? 1 : 0}
        />
        {trackedProgress > 0.8 && (
          <text
            x={width - padding + 10}
            y={padding + 230}
            fill={healthForesightColors.primary.main}
            fontSize="12"
            fontWeight="700"
          >
            Measured Savings
          </text>
        )}

        {/* Untracked cost line */}
        <path
          d={untrackedPath}
          fill="none"
          stroke={healthForesightColors.amber.main}
          strokeWidth="3"
          strokeDasharray={`${untrackedProgress * 600} 600`}
          opacity={untrackedProgress > 0 ? 1 : 0}
        />
        {untrackedProgress > 0.8 && (
          <text
            x={width - padding + 10}
            y={padding + 150}
            fill={healthForesightColors.amber.main}
            fontSize="12"
            fontWeight="700"
          >
            Deferred & Displaced Cost
          </text>
        )}
      </Box>
      <Typography
        variant="caption"
        sx={{
          fontSize: '12px',
          color: healthForesightColors.neutral.mid,
          fontStyle: 'italic',
          textAlign: 'center',
          mt: 1,
          maxWidth: '600px',
        }}
      >
        By the time cost reappears, the policy has already been declared successful.
      </Typography>
    </Box>
  )
}
