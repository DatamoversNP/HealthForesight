/**
 * Classical vs Healthcare Demand Visual
 * Shows control theory: Direct control (Classical) vs Mediated control (Healthcare)
 * Policy does NOT act directly on utilization - it passes through a decision environment
 */
import React, { useEffect, useState } from 'react'
import { Box, Typography } from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'

export default function ClassicalVsHealthcareDemandVisual() {
  const [classicalVisible, setClassicalVisible] = useState(false)
  const [healthcareVisible, setHealthcareVisible] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          setClassicalVisible(true)
          setTimeout(() => setHealthcareVisible(true), 300)
        }
      },
      { threshold: 0.2 }
    )

    const element = document.getElementById('classical-vs-demand')
    if (element) observer.observe(element)

    return () => observer.disconnect()
  }, [])

  const width = 350
  const height = 350

  // Classical: Simple direct relationship
  const classicalPath = `M 50 80 
    Q 150 150 250 250
    T 350 320`

  return (
    <Box
      id="classical-vs-demand"
      sx={{
        display: 'flex',
        flexDirection: { xs: 'column', md: 'row' },
        gap: 6,
        justifyContent: 'center',
        mb: 4,
      }}
    >
      {/* Classical Economics */}
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
          Classical Economics
        </Typography>
        <Box
          component="svg"
          viewBox={`0 0 ${width} ${height}`}
          preserveAspectRatio="xMidYMid meet"
          sx={{
            width: '100%',
            height: '100%',
            maxHeight: { xs: '250px', md: '380px' },
          }}
        >
          {/* Price box */}
          <rect
            x={150}
            y={40}
            width={100}
            height={40}
            fill={healthForesightColors.neutral.mid}
            rx="4"
            opacity={classicalVisible ? 1 : 0}
          />
          <text
            x={200}
            y={65}
            textAnchor="middle"
            fill="#FFFFFF"
            fontSize="14"
            fontWeight="700"
            opacity={classicalVisible ? 1 : 0}
          >
            Price
          </text>

          {/* Direct arrow */}
          {classicalVisible && (
            <line
              x1={200}
              y1={80}
              x2={200}
              y2={180}
              stroke={healthForesightColors.neutral.mid}
              strokeWidth="3"
            />
          )}
          {classicalVisible && (
            <polygon
              points="200,180 195,170 205,170"
              fill={healthForesightColors.neutral.mid}
            />
          )}

          {/* Demand curve */}
          {classicalVisible && (
            <path
              d={classicalPath}
              fill="none"
              stroke={healthForesightColors.neutral.mid}
              strokeWidth="3"
            />
          )}

          {/* Demand label */}
          <text
            x={300}
            y={310}
            fill={healthForesightColors.neutral.dark}
            fontSize="14"
            fontWeight="700"
            opacity={classicalVisible ? 1 : 0}
          >
            Demand
          </text>

          {/* Annotation */}
          <text
            x={width / 2}
            y={height - 10}
            textAnchor="middle"
            fill={healthForesightColors.neutral.mid}
            fontSize="12"
            fontWeight="600"
            opacity={classicalVisible ? 1 : 0}
          >
            Control variable acts directly on demand
          </text>
        </Box>
      </Box>

      {/* Healthcare */}
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
          Healthcare
        </Typography>
        <Box
          component="svg"
          viewBox={`0 0 ${width} ${height}`}
          preserveAspectRatio="xMidYMid meet"
          sx={{
            width: '100%',
            height: '100%',
            maxHeight: { xs: '250px', md: '380px' },
          }}
        >
          {/* Policy box */}
          <rect
            x={150}
            y={40}
            width={100}
            height={40}
            fill={healthForesightColors.primary.main}
            rx="4"
            opacity={healthcareVisible ? 1 : 0}
          />
          <text
            x={200}
            y={65}
            textAnchor="middle"
            fill="#FFFFFF"
            fontSize="14"
            fontWeight="700"
            opacity={healthcareVisible ? 1 : 0}
          >
            Policy
          </text>

          {/* Arrow to decision environment */}
          {healthcareVisible && (
            <line
              x1={200}
              y1={80}
              x2={200}
              y2={140}
              stroke={healthForesightColors.primary.main}
              strokeWidth="3"
            />
          )}
          {healthcareVisible && (
            <polygon
              points="200,140 195,130 205,130"
              fill={healthForesightColors.primary.main}
            />
          )}

          {/* Decision Environment - Intervening Layer (shaded band/container) */}
          <rect
            x={50}
            y={150}
            width={250}
            height={100}
            fill={healthForesightColors.neutral.background}
            stroke={healthForesightColors.primary.main}
            strokeWidth="2"
            strokeDasharray="4 4"
            rx="4"
            opacity={healthcareVisible ? 0.3 : 0}
          />
          <text
            x={width / 2}
            y={175}
            textAnchor="middle"
            fill={healthForesightColors.primary.main}
            fontSize="13"
            fontWeight="700"
            opacity={healthcareVisible ? 1 : 0}
          >
            Decision Environment
          </text>
          
          {/* Environment components (subtle) */}
          <text
            x={width / 2}
            y={195}
            textAnchor="middle"
            fill={healthForesightColors.neutral.mid}
            fontSize="11"
            fontWeight="500"
            opacity={healthcareVisible ? 0.7 : 0}
          >
            Provider incentives
          </text>
          <text
            x={width / 2}
            y={215}
            textAnchor="middle"
            fill={healthForesightColors.neutral.mid}
            fontSize="11"
            fontWeight="500"
            opacity={healthcareVisible ? 0.7 : 0}
          >
            Clinical judgment • Patient constraints
          </text>
          <text
            x={width / 2}
            y={235}
            textAnchor="middle"
            fill={healthForesightColors.neutral.mid}
            fontSize="11"
            fontWeight="500"
            opacity={healthcareVisible ? 0.7 : 0}
          >
            Administrative friction
          </text>

          {/* Arrow from decision environment to utilization */}
          {healthcareVisible && (
            <line
              x1={200}
              y1={250}
              x2={200}
              y2={290}
              stroke={healthForesightColors.accent.main}
              strokeWidth="3"
            />
          )}
          {healthcareVisible && (
            <polygon
              points="200,290 195,280 205,280"
              fill={healthForesightColors.accent.main}
            />
          )}

          {/* Utilization box */}
          <rect
            x={150}
            y={300}
            width={100}
            height={40}
            fill={healthForesightColors.accent.main}
            rx="4"
            opacity={healthcareVisible ? 1 : 0}
          />
          <text
            x={200}
            y={325}
            textAnchor="middle"
            fill="#FFFFFF"
            fontSize="14"
            fontWeight="700"
            opacity={healthcareVisible ? 1 : 0}
          >
            Utilization
          </text>

          {/* Annotation */}
          <text
            x={width / 2}
            y={height - 10}
            textAnchor="middle"
            fill={healthForesightColors.neutral.mid}
            fontSize="12"
            fontWeight="600"
            opacity={healthcareVisible ? 1 : 0}
          >
            Policy reshapes decisions — utilization emerges downstream
          </text>
        </Box>
      </Box>
    </Box>
  )
}
