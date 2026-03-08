/**
 * Side-by-side contrast: Classical Economics vs Healthcare
 * Left: Straight demand curve (draws instantly)
 * Right: Fractured, branching response paths with policy intervention anchor
 * Labels: Provider Adaptation, Patient Deferral, Site-of-Care Shift, Escalation
 */
import React, { useEffect, useState } from 'react'
import { Box, Typography } from '@mui/material'
import { healthForesightColors } from '../../theme/healthForesightTheme'

export default function ClassicalVsHealthcareVisual() {
  const [classicalVisible, setClassicalVisible] = useState(false)
  const [healthcareMainVisible, setHealthcareMainVisible] = useState(false)
  const [policyPointVisible, setPolicyPointVisible] = useState(false)
  const [branchesVisible, setBranchesVisible] = useState<boolean[]>([])
  const [labelsVisible, setLabelsVisible] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          // Classical draws fully in 300ms
          setClassicalVisible(true)
          
          // Healthcare main line draws until policy point
          setTimeout(() => {
            setHealthcareMainVisible(true)
            setTimeout(() => {
              setPolicyPointVisible(true)
              // Brief pause (150ms) then branches split one by one
              setTimeout(() => {
                const branchSequence = [false, false, false, false]
                branchSequence.forEach((_, idx) => {
                  setTimeout(() => {
                    setBranchesVisible((prev) => {
                      const newBranches = [...prev]
                      newBranches[idx] = true
                      return newBranches
                    })
                  }, idx * 200)
                })
                // Labels fade in last
                setTimeout(() => setLabelsVisible(true), 1000)
              }, 150)
            }, 600)
          }, 300)
        }
      },
      { threshold: 0.2 }
    )

    const element = document.getElementById('classical-vs-healthcare')
    if (element) observer.observe(element)

    return () => observer.disconnect()
  }, [])

  const width = 300
  const height = 280
  const padding = 30

  // Classical: Simple demand curve
  const classicalPath = `M ${padding} ${padding} 
    Q ${padding + width * 0.3} ${padding + height * 0.3} 
    ${padding + width * 0.5} ${padding + height * 0.5}
    T ${padding + width} ${padding + height}`

  // Healthcare: Main path until policy point
  const policyX = padding + width * 0.4
  const policyY = padding + height * 0.3
  const mainPath = `M ${padding} ${padding} L ${policyX} ${policyY}`

  // Healthcare branches with labels, colors, and weights
  const branches = [
    {
      path: `M ${policyX} ${policyY} L ${padding + width * 0.6} ${padding + height * 0.2} L ${padding + width} ${padding + height * 0.1}`,
      label: 'Provider Adaptation',
      sublabel: '(coding / substitution)',
      color: healthForesightColors.primary.main, // Purple for provider-driven
      thickness: 3,
      impact: 'high',
    },
    {
      path: `M ${policyX} ${policyY} L ${padding + width * 0.7} ${padding + height * 0.5} L ${padding + width} ${padding + height * 0.6}`,
      label: 'Patient Deferral',
      sublabel: '/ Avoidance',
      color: healthForesightColors.accent.main, // Teal for expected/intended
      thickness: 2,
      impact: 'medium',
    },
    {
      path: `M ${policyX} ${policyY} L ${padding + width * 0.65} ${padding + height * 0.7} L ${padding + width} ${padding + height * 0.9}`,
      label: 'Site-of-Care Shift',
      color: healthForesightColors.primary.light, // Lighter purple
      thickness: 2.5,
      impact: 'medium',
    },
    {
      path: `M ${policyX} ${policyY} L ${padding + width * 0.75} ${padding + height * 0.4} L ${padding + width} ${padding + height * 0.25}`,
      label: 'Escalation',
      sublabel: '(Higher-Acuity)',
      color: healthForesightColors.amber.main, // Amber for risk/unintended
      thickness: 4, // Thickest for high impact
      impact: 'high',
    },
  ]

  return (
    <Box id="classical-vs-healthcare">
      <Box
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
            mb: 2,
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
            maxHeight: { xs: '250px', md: '300px' },
          }}
        >
          {classicalVisible && (
            <path
              d={classicalPath}
              fill="none"
              stroke={healthForesightColors.neutral.mid}
              strokeWidth="3"
              opacity={1}
            />
          )}
          {/* Time cue */}
          <text
            x={width / 2}
            y={height - 5}
            textAnchor="middle"
            fill={healthForesightColors.neutral.mid}
            fontSize="11"
            fontWeight="600"
          >
            Time →
          </text>
        </Box>
      </Box>

      {/* Healthcare */}
      <Box sx={{ flex: 1, textAlign: 'center' }}>
        <Typography
          variant="h6"
          sx={{
            mb: 2,
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
            maxHeight: { xs: '250px', md: '300px' },
          }}
        >
          {/* Main path until policy point */}
          {healthcareMainVisible && (
            <path
              d={mainPath}
              fill="none"
              stroke={healthForesightColors.neutral.mid}
              strokeWidth="2"
              opacity={0.6}
            />
          )}

          {/* Policy intervention anchor */}
          {policyPointVisible && (
            <g>
              <circle
                cx={policyX}
                cy={policyY}
                r="6"
                fill={healthForesightColors.primary.main}
                stroke="#FFFFFF"
                strokeWidth="2"
              />
              <text
                x={policyX}
                y={policyY - 15}
                textAnchor="middle"
                fill={healthForesightColors.primary.main}
                fontSize="10"
                fontWeight="700"
              >
                Policy Intervention
              </text>
            </g>
          )}

          {/* Branches */}
          {branches.map((branch, idx) => (
            <g key={idx}>
              {branchesVisible[idx] && (
                <path
                  d={branch.path}
                  fill="none"
                  stroke={branch.color}
                  strokeWidth={branch.thickness}
                  opacity={branch.impact === 'high' ? 0.9 : 0.7}
                  strokeLinecap="round"
                />
              )}
              {/* Labels */}
              {labelsVisible && branchesVisible[idx] && (
                <g>
                  <text
                    x={padding + width * 0.75}
                    y={idx === 0 ? padding + height * 0.15 : idx === 1 ? padding + height * 0.55 : idx === 2 ? padding + height * 0.85 : padding + height * 0.2}
                    fill={branch.color}
                    fontSize="10"
                    fontWeight="700"
                    opacity={0.9}
                  >
                    {branch.label}
                  </text>
                  {branch.sublabel && (
                    <text
                      x={padding + width * 0.75}
                      y={idx === 0 ? padding + height * 0.15 + 12 : idx === 1 ? padding + height * 0.55 + 12 : padding + height * 0.2 + 12}
                      fill={branch.color}
                      fontSize="9"
                      fontWeight="500"
                      opacity={0.8}
                    >
                      {branch.sublabel}
                    </text>
                  )}
                </g>
              )}
            </g>
          ))}

          {/* Time cue with dotted extension */}
          <text
            x={width / 2}
            y={height - 5}
            textAnchor="middle"
            fill={healthForesightColors.neutral.mid}
            fontSize="11"
            fontWeight="600"
          >
            Time →
          </text>
          {policyPointVisible && (
            <path
              d={`M ${policyX} ${height - 15} L ${padding + width} ${height - 15}`}
              fill="none"
              stroke={healthForesightColors.neutral.mid}
              strokeWidth="1"
              strokeDasharray="2 2"
              opacity={0.3}
            />
          )}
        </Box>
      </Box>
      </Box>

      {/* Key Insight micro-copy */}
      <Box
        sx={{
          width: '100%',
          mt: 3,
          p: 3,
          backgroundColor: healthForesightColors.neutral.background,
          borderRadius: 2,
          border: `1px solid ${healthForesightColors.neutral.light}`,
        }}
      >
        <Typography
          sx={{
            fontSize: '13px',
            fontWeight: 700,
            color: healthForesightColors.primary.main,
            mb: 1,
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
          }}
        >
          Key Insight:
        </Typography>
        <Typography
          sx={{
            fontSize: '14px',
            color: healthForesightColors.neutral.dark,
            lineHeight: 1.7,
          }}
        >
          Classical elasticity assumes a single, predictable response to intervention. Healthcare utilization responds through multiple behavioral pathways, many of which increase total cost despite reducing targeted services.
        </Typography>
      </Box>
    </Box>
  )
}
