/**
 * Utilization Paradox Visual
 * Shows the paradox: Targeted utilization drops while downstream/substitution rises
 * Includes counterfactual baseline and system-level impact
 */
import React, { useEffect, useState } from 'react'
import { Box, Typography } from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'

export default function UtilizationParadoxVisual() {
  const [counterfactualVisible, setCounterfactualVisible] = useState(false)
  const [line1Progress, setLine1Progress] = useState(0)
  const [line2Progress, setLine2Progress] = useState(0)
  const [systemLineVisible, setSystemLineVisible] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          // Counterfactual appears first
          setCounterfactualVisible(true)
          
          // Line 1 (Targeted) draws first
          let progress = 0
          const interval1 = setInterval(() => {
            progress += 0.02
            setLine1Progress(Math.min(progress, 1))
            if (progress >= 1) {
              clearInterval(interval1)
              // 300ms pause
              setTimeout(() => {
                // Line 2 (Downstream) draws second - showing RISE
                let progress2 = 0
                const interval2 = setInterval(() => {
                  progress2 += 0.02
                  setLine2Progress(Math.min(progress2, 1))
                  if (progress2 >= 1) {
                    clearInterval(interval2)
                    // System line appears last
                    setTimeout(() => setSystemLineVisible(true), 300)
                  }
                }, 20)
              }, 300)
            }
          }, 20)
        }
      },
      { threshold: 0.2 }
    )

    const element = document.getElementById('utilization-paradox')
    if (element) observer.observe(element)

    return () => observer.disconnect()
  }, [])

  const width = 700
  const height = 450
  const padding = 70
  const policyX = padding + (width - padding * 2) * 0.35

  // Counterfactual baseline (what would have happened without policy) - rises slightly
  const counterfactualPath = `M ${padding} ${padding + 180} 
    L ${width - padding} ${padding + 160}`

  // Line 1: Targeted Service Utilization - sharp drop, then flattens, slight rebound
  const targetedPath = `M ${padding} ${padding + 180} 
    L ${policyX - 20} ${padding + 185}
    L ${policyX + 30} ${padding + 250}
    L ${policyX + 100} ${padding + 255}
    L ${policyX + 200} ${padding + 260}
    L ${width - padding} ${padding + 265}`

  // Line 2: Downstream/Adjacent Utilization - flat pre-policy, then RISES with lag
  const downstreamPath = `M ${padding} ${padding + 220} 
    L ${policyX - 20} ${padding + 218}
    L ${policyX + 50} ${padding + 215}
    L ${policyX + 150} ${padding + 200}
    L ${policyX + 250} ${padding + 180}
    L ${width - padding} ${padding + 165}`

  // System-Level Impact - dips slightly, then rises above baseline
  const systemPath = `M ${padding} ${padding + 200} 
    L ${policyX + 30} ${padding + 210}
    L ${policyX + 100} ${padding + 205}
    L ${policyX + 200} ${padding + 195}
    L ${width - padding} ${padding + 150}`

  return (
    <Box
      id="utilization-paradox"
      sx={{
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        p: 3,
      }}
    >
      <Typography
        variant="h4"
        sx={{
          fontSize: { xs: '1.25rem', md: '1.5rem' },
          fontWeight: 700,
          mb: 1,
          color: healthForesightColors.neutral.dark,
        }}
      >
        The Utilization Management Paradox
      </Typography>
      <Typography
        variant="body2"
        sx={{
          fontSize: '13px',
          color: healthForesightColors.neutral.mid,
          mb: 3,
          fontStyle: 'italic',
        }}
      >
        Apparent Control, Hidden Cost
      </Typography>
      <Box
        component="svg"
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="xMidYMid meet"
        sx={{
          width: '100%',
          maxWidth: { xs: '100%', md: '900px' },
          height: { xs: '300px', md: '500px' },
        }}
      >
        {/* Shaded time regions */}
        <g>
          {/* Immediate response */}
          <rect
            x={policyX}
            y={padding}
            width={(width - padding * 2) * 0.2}
            height={height - padding * 2}
            fill={healthForesightColors.accent.main}
            opacity={0.05}
          />
          <text
            x={policyX + (width - padding * 2) * 0.1}
            y={padding + 30}
            textAnchor="middle"
            fill={healthForesightColors.accent.main}
            fontSize="11"
            fontWeight="600"
          >
            Immediate response
          </text>

          {/* Behavioral adaptation */}
          <rect
            x={policyX + (width - padding * 2) * 0.2}
            y={padding}
            width={(width - padding * 2) * 0.3}
            height={height - padding * 2}
            fill={healthForesightColors.primary.main}
            opacity={0.05}
          />
          <text
            x={policyX + (width - padding * 2) * 0.35}
            y={padding + 30}
            textAnchor="middle"
            fill={healthForesightColors.primary.main}
            fontSize="11"
            fontWeight="600"
          >
            Behavioral adaptation
          </text>

          {/* System-level impact */}
          <rect
            x={policyX + (width - padding * 2) * 0.5}
            y={padding}
            width={(width - padding * 2) * 0.5}
            height={height - padding * 2}
            fill={healthForesightColors.amber.main}
            opacity={0.05}
          />
          <text
            x={policyX + (width - padding * 2) * 0.75}
            y={padding + 30}
            textAnchor="middle"
            fill={healthForesightColors.amber.main}
            fontSize="11"
            fontWeight="600"
          >
            System-level impact
          </text>
        </g>

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
          Utilization / Cost Index
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

        {/* Counterfactual baseline (dashed, faint) */}
        {counterfactualVisible && (
          <path
            d={counterfactualPath}
            fill="none"
            stroke={healthForesightColors.neutral.mid}
            strokeWidth="2"
            strokeDasharray="6 4"
            opacity={0.4}
          />
        )}
        {counterfactualVisible && (
          <text
            x={width - padding + 10}
            y={padding + 160}
            fill={healthForesightColors.neutral.mid}
            fontSize="11"
            fontWeight="600"
            opacity={0.6}
          >
            Counterfactual baseline
          </text>
        )}

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
          Policy Introduced
        </text>

        {/* Line 1: Targeted Service Utilization */}
        <path
          d={targetedPath}
          fill="none"
          stroke={healthForesightColors.primary.main}
          strokeWidth="3"
          strokeDasharray={`${line1Progress * 600} 600`}
          opacity={line1Progress > 0 ? 1 : 0}
        />
        {line1Progress > 0.8 && (
          <text
            x={width - padding + 10}
            y={padding + 265}
            fill={healthForesightColors.primary.main}
            fontSize="13"
            fontWeight="700"
          >
            Targeted Service Utilization ↓
          </text>
        )}

        {/* Line 2: Downstream/Adjacent Utilization - RISES */}
        <path
          d={downstreamPath}
          fill="none"
          stroke={healthForesightColors.amber.main}
          strokeWidth="3"
          strokeDasharray={`${line2Progress * 600} 600`}
          opacity={line2Progress > 0 ? 1 : 0}
        />
        {line2Progress > 0.8 && (
          <text
            x={width - padding + 10}
            y={padding + 165}
            fill={healthForesightColors.amber.main}
            fontSize="13"
            fontWeight="700"
          >
            Downstream Utilization ↑
          </text>
        )}

        {/* System-Level Impact line */}
        {systemLineVisible && (
          <path
            d={systemPath}
            fill="none"
            stroke={healthForesightColors.neutral.dark}
            strokeWidth="3"
            strokeDasharray="8 4"
            opacity={0.8}
          />
        )}
        {systemLineVisible && (
          <text
            x={width - padding + 10}
            y={padding + 150}
            fill={healthForesightColors.neutral.dark}
            fontSize="13"
            fontWeight="700"
          >
            System-Level Impact
          </text>
        )}

        {/* Callouts */}
        {line1Progress > 0.5 && (
          <g opacity={(line1Progress - 0.5) * 2}>
            <text
              x={policyX + 60}
              y={padding + 240}
              fill={healthForesightColors.primary.main}
              fontSize="10"
              fontWeight="600"
            >
              Short-term suppression
            </text>
          </g>
        )}
        {line2Progress > 0.4 && (
          <g opacity={(line2Progress - 0.4) / 0.6}>
            <text
              x={policyX + 120}
              y={padding + 195}
              fill={healthForesightColors.amber.main}
              fontSize="10"
              fontWeight="600"
            >
              Behavioral substitution
            </text>
          </g>
        )}
        {systemLineVisible && (
          <g>
            <text
              x={policyX + 250}
              y={padding + 190}
              fill={healthForesightColors.neutral.dark}
              fontSize="10"
              fontWeight="600"
            >
              Delayed acuity rebound
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
        Standard reporting captures only the blue line. The paradox: targeted metrics improve while system-level outcomes deteriorate.
      </Typography>
    </Box>
  )
}
