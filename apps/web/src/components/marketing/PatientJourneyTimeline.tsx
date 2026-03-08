/**
 * Patient Journey Timeline: Measured vs Experienced Reality
 * Shows second-order, delayed, and unmeasured patient effects
 * Two time-series: Tracked Metric (declining) vs Untracked Patient Impact (rising)
 */
import React, { useEffect, useState } from 'react'
import { Box, Typography } from '@mui/material'
import { healthForesightColors } from '../../theme/healthForesightTheme'

export default function PatientJourneyTimeline() {
  const [trackedVisible, setTrackedVisible] = useState(false)
  const [untrackedVisible, setUntrackedVisible] = useState(false)
  const [blindSpotVisible, setBlindSpotVisible] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          // Tracked metric appears first
          setTrackedVisible(true)
          
          // Untracked impact appears later (delayed effect)
          setTimeout(() => {
            setUntrackedVisible(true)
            // Blind spot appears last
            setTimeout(() => setBlindSpotVisible(true), 500)
          }, 600)
        }
      },
      { threshold: 0.2 }
    )

    const element = document.getElementById('patient-journey-timeline')
    if (element) observer.observe(element)

    return () => observer.disconnect()
  }, [])

  const width = 800
  const height = 400
  const padding = 70
  const policyX = padding + (width - padding * 2) * 0.3

  // Tracked Metric: Drops or improves post-policy, stabilizes
  const trackedPath = `M ${padding} ${padding + 150} 
    L ${policyX - 20} ${padding + 155}
    L ${policyX + 50} ${padding + 200}
    L ${policyX + 150} ${padding + 205}
    L ${policyX + 300} ${padding + 210}
    L ${width - padding} ${padding + 210}`

  // Untracked Patient Impact: Flat initially, rises later, overtakes benefits
  const untrackedPath = `M ${padding} ${padding + 200} 
    L ${policyX + 30} ${padding + 200}
    L ${policyX + 100} ${padding + 195}
    L ${policyX + 200} ${padding + 180}
    L ${policyX + 350} ${padding + 150}
    L ${width - padding} ${padding + 120}`

  // Blind spot region - where untracked impact rises
  const blindSpotStartX = policyX + 100
  const blindSpotEndX = width - padding

  return (
    <Box
      id="patient-journey-timeline"
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
          Impact Level
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

        {/* Policy marker */}
        <line
          x1={policyX}
          y1={padding}
          x2={policyX}
          y2={height - padding}
          stroke={healthForesightColors.amber.main}
          strokeWidth="2"
          strokeDasharray="4 4"
          opacity={0.6}
        />
        <text
          x={policyX}
          y={padding - 10}
          textAnchor="middle"
          fill={healthForesightColors.amber.main}
          fontSize="11"
          fontWeight="700"
        >
          Policy
        </text>

        {/* Blind spot region - shaded area where untracked impact rises */}
        {blindSpotVisible && (
          <rect
            x={blindSpotStartX}
            y={padding}
            width={blindSpotEndX - blindSpotStartX}
            height={height - padding * 2}
            fill={healthForesightColors.amber.main}
            opacity={0.1}
          />
        )}
        {blindSpotVisible && (
          <text
            x={blindSpotStartX + (blindSpotEndX - blindSpotStartX) / 2}
            y={padding + 30}
            textAnchor="middle"
            fill={healthForesightColors.amber.main}
            fontSize="12"
            fontWeight="700"
          >
            Outside Measurement Window
          </text>
        )}

        {/* Tracked Metric line - what dashboards show */}
        <path
          d={trackedPath}
          fill="none"
          stroke={healthForesightColors.primary.main}
          strokeWidth="3"
          opacity={trackedVisible ? 1 : 0}
        />
        {trackedVisible && (
          <text
            x={width - padding + 10}
            y={padding + 210}
            fill={healthForesightColors.primary.main}
            fontSize="13"
            fontWeight="700"
          >
            Targeted Utilization (Measured) ↓
          </text>
        )}

        {/* Untracked Patient Impact line - what actually happens */}
        <path
          d={untrackedPath}
          fill="none"
          stroke={healthForesightColors.amber.main}
          strokeWidth="3"
          strokeDasharray="6 4"
          opacity={untrackedVisible ? 1 : 0}
        />
        {untrackedVisible && (
          <text
            x={width - padding + 10}
            y={padding + 120}
            fill={healthForesightColors.amber.main}
            fontSize="13"
            fontWeight="700"
          >
            Deferred / Emergency / Abandoned Care (Unmeasured) ↑
          </text>
        )}

        {/* Divergence annotation */}
        {untrackedVisible && (
          <g>
            <line
              x1={policyX + 250}
              y1={padding + 190}
              x2={policyX + 250}
              y2={padding + 160}
              stroke={healthForesightColors.neutral.mid}
              strokeWidth="1"
              strokeDasharray="2 2"
            />
            <text
              x={policyX + 260}
              y={padding + 175}
              fill={healthForesightColors.neutral.dark}
              fontSize="11"
              fontWeight="600"
            >
              Divergence
            </text>
          </g>
        )}

        {/* Icons at key points on untracked line (minimal) */}
        {untrackedVisible && (
          <g>
            {/* Delay icon */}
            <text
              x={policyX + 150}
              y={padding + 185}
              fontSize="14"
              opacity={0.7}
            >
              ⏳
            </text>
            {/* Emergency icon */}
            <text
              x={policyX + 300}
              y={padding + 155}
              fontSize="14"
              opacity={0.7}
            >
              🚑
            </text>
            {/* Abandonment icon */}
            <text
              x={width - padding - 30}
              y={padding + 125}
              fontSize="14"
              opacity={0.7}
            >
              ❌
            </text>
          </g>
        )}
      </Box>

      {/* Caption */}
      <Typography
        variant="body2"
        sx={{
          fontSize: '12px',
          color: healthForesightColors.neutral.mid,
          mt: 2,
          fontStyle: 'italic',
          textAlign: 'center',
          maxWidth: '600px',
        }}
      >
        Dashboards track the blue line. Patients experience the orange line. The gap widens over time.
      </Typography>
    </Box>
  )
}
