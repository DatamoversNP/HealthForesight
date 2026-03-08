/**
 * Behavioral Response Field
 * Shows policy as a shock that perturbs behavior across multiple actors, over time, with competing adaptations
 * NOT a linear flowchart - a response map showing simultaneity and emergence
 */
import React, { useEffect, useState } from 'react'
import { Box, Typography } from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'

export default function BehavioralSankeyFlow() {
  const [policyVisible, setPolicyVisible] = useState(false)
  const [vectorsVisible, setVectorsVisible] = useState<boolean[]>([])
  const [outcomesVisible, setOutcomesVisible] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          // Policy marker fades in
          setPolicyVisible(true)
          
          // Behavioral vectors expand outward with staggered timing
          setTimeout(() => {
            [0, 1, 2, 3, 4, 5].forEach((idx) => {
              setTimeout(() => {
                setVectorsVisible((prev) => {
                  const newVectors = [...prev]
                  newVectors[idx] = true
                  return newVectors
                })
              }, idx * 100)
            })
            
            // Outcome box fades in last (300-500ms delay)
            setTimeout(() => {
              setOutcomesVisible(true)
            }, 1000)
          }, 300)
        }
      },
      { threshold: 0.2 }
    )

    const element = document.getElementById('behavioral-sankey')
    if (element) observer.observe(element)

    return () => observer.disconnect()
  }, [])

  const width = 900
  const height = 600
  const policyX = width / 2
  const policyY = 80
  const responseLayerY = 280
  const outcomesY = 520

  // Provider response vectors - fan outward from policy point, vary in length, overlap slightly
  const providerVectors = [
    {
      label: 'Compliance',
      angle: -50, // degrees
      length: 140,
      color: healthForesightColors.accent.main,
    },
    {
      label: 'Adaptation',
      angle: -20,
      length: 160, // Longer to show magnitude
      color: healthForesightColors.primary.main,
    },
    {
      label: 'Resistance',
      angle: 10,
      length: 150,
      color: healthForesightColors.amber.main,
    },
  ]

  // Patient response vectors - fan outward, vary in length, overlap slightly
  const patientVectors = [
    {
      label: 'Deferral',
      angle: 20,
      length: 130,
      color: healthForesightColors.accent.main,
    },
    {
      label: 'Substitution',
      angle: 45,
      length: 155, // Longer to show magnitude
      color: healthForesightColors.primary.main,
    },
    {
      label: 'Emergency fallback',
      angle: 70,
      length: 145,
      color: healthForesightColors.amber.main,
    },
  ]

  // Helper function to calculate vector endpoint
  const getVectorEnd = (angle: number, length: number, startX: number, startY: number) => {
    const radians = (angle * Math.PI) / 180
    return {
      x: startX + Math.cos(radians) * length,
      y: startY + Math.sin(radians) * length,
    }
  }

  return (
    <Box id="behavioral-sankey">
      <Box
        sx={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          p: 3,
        }}
      >
        <Box
          component="svg"
          viewBox={`0 0 ${width} ${height}`}
          sx={{
            width: '100%',
            height: '100%',
            maxHeight: '650px',
          }}
        >
          {/* Top: Policy Shock - single vertical marker, neutral color, minimal emphasis */}
          <g opacity={policyVisible ? 1 : 0}>
            <line
              x1={policyX}
              y1={policyY}
              x2={policyX}
              y2={responseLayerY - 40}
              stroke={healthForesightColors.neutral.mid}
              strokeWidth="3"
            />
            <circle
              cx={policyX}
              cy={policyY}
              r="8"
              fill={healthForesightColors.neutral.mid}
              stroke="#FFFFFF"
              strokeWidth="2"
            />
            <text
              x={policyX}
              y={policyY - 15}
              textAnchor="middle"
              fill={healthForesightColors.neutral.dark}
              fontSize="14"
              fontWeight="700"
            >
              Policy Intervention
            </text>
          </g>

          {/* Middle: Behavioral Response Layer - horizontal band, primary focus */}
          <g>
            {/* Band background */}
            <rect
              x={100}
              y={responseLayerY - 60}
              width={width - 200}
              height={120}
              fill={healthForesightColors.neutral.background}
              stroke={healthForesightColors.neutral.light}
              strokeWidth="2"
              rx="4"
              opacity={0.5}
            />
            
            {/* Band label */}
            <text
              x={120}
              y={responseLayerY - 30}
              fill={healthForesightColors.neutral.dark}
              fontSize="15"
              fontWeight="700"
            >
              Behavioral Response Space
            </text>

            {/* Provider response vectors - left half, fan outward from policy point */}
            <g>
              <text
                x={width / 2 - 200}
                y={responseLayerY - 10}
                fill={healthForesightColors.neutral.mid}
                fontSize="13"
                fontWeight="600"
              >
                Provider Responses
              </text>
              {providerVectors.map((vector, idx) => {
                const startX = policyX
                const startY = responseLayerY - 40
                const end = getVectorEnd(vector.angle, vector.length, startX, startY)
                const markerId = vector.color === healthForesightColors.accent.main ? "arrowhead-teal" : vector.color === healthForesightColors.primary.main ? "arrowhead-purple" : "arrowhead-amber"
                
                return (
                  <g key={idx} opacity={vectorsVisible[idx] ? 1 : 0}>
                    {/* Vector arrow - fanning outward */}
                    <line
                      x1={startX}
                      y1={startY}
                      x2={end.x}
                      y2={end.y}
                      stroke={vector.color}
                      strokeWidth={vector.length > 150 ? 4 : 3} // Thicker for longer vectors
                      markerEnd={`url(#${markerId})`}
                      opacity={0.8}
                    />
                    {/* Label */}
                    <text
                      x={end.x}
                      y={end.y + 20}
                      textAnchor="middle"
                      fill={vector.color}
                      fontSize="14"
                      fontWeight="700"
                    >
                      {vector.label}
                    </text>
                  </g>
                )
              })}
            </g>

            {/* Patient response vectors - right half, fan outward from policy point */}
            <g>
              <text
                x={width / 2 + 200}
                y={responseLayerY - 10}
                fill={healthForesightColors.neutral.mid}
                fontSize="13"
                fontWeight="600"
              >
                Patient Responses
              </text>
              {patientVectors.map((vector, idx) => {
                const vectorIdx = idx + 3 // Offset for provider vectors
                const startX = policyX
                const startY = responseLayerY - 40
                const end = getVectorEnd(vector.angle, vector.length, startX, startY)
                const markerId = vector.color === healthForesightColors.accent.main ? "arrowhead-teal" : vector.color === healthForesightColors.primary.main ? "arrowhead-purple" : "arrowhead-amber"
                
                return (
                  <g key={idx} opacity={vectorsVisible[vectorIdx] ? 1 : 0}>
                    {/* Vector arrow - fanning outward */}
                    <line
                      x1={startX}
                      y1={startY}
                      x2={end.x}
                      y2={end.y}
                      stroke={vector.color}
                      strokeWidth={vector.length > 150 ? 4 : 3} // Thicker for longer vectors
                      markerEnd={`url(#${markerId})`}
                      opacity={0.8}
                    />
                    {/* Label */}
                    <text
                      x={end.x}
                      y={end.y + 20}
                      textAnchor="middle"
                      fill={vector.color}
                      fontSize="14"
                      fontWeight="700"
                    >
                      {vector.label}
                    </text>
                  </g>
                )
              })}
            </g>
          </g>

          {/* Arrow marker definitions for different colors */}
          <defs>
            <marker
              id="arrowhead-teal"
              markerWidth="10"
              markerHeight="10"
              refX="9"
              refY="3"
              orient="auto"
            >
              <polygon
                points="0 0, 10 3, 0 6"
                fill={healthForesightColors.accent.main}
              />
            </marker>
            <marker
              id="arrowhead-purple"
              markerWidth="10"
              markerHeight="10"
              refX="9"
              refY="3"
              orient="auto"
            >
              <polygon
                points="0 0, 10 3, 0 6"
                fill={healthForesightColors.primary.main}
              />
            </marker>
            <marker
              id="arrowhead-amber"
              markerWidth="10"
              markerHeight="10"
              refX="9"
              refY="3"
              orient="auto"
            >
              <polygon
                points="0 0, 10 3, 0 6"
                fill={healthForesightColors.amber.main}
              />
            </marker>
          </defs>

          {/* Bottom: Emergent Outcomes - single muted container, convergence arrow */}
          <g opacity={outcomesVisible ? 1 : 0}>
            {/* Convergence arrow from behavioral layer */}
            <path
              d={`M ${width / 2 - 100} ${responseLayerY + 60} 
                Q ${width / 2} ${responseLayerY + 100} 
                ${width / 2} ${outcomesY - 30}
                Q ${width / 2} ${outcomesY - 10} 
                ${width / 2 + 100} ${outcomesY - 30}`}
              fill="none"
              stroke={healthForesightColors.neutral.mid}
              strokeWidth="2"
              strokeDasharray="4 4"
              opacity={0.4}
            />
            
            {/* Outcomes container */}
            <rect
              x={width / 2 - 200}
              y={outcomesY - 40}
              width={400}
              height={60}
              fill={healthForesightColors.neutral.background}
              stroke={healthForesightColors.neutral.mid}
              strokeWidth="2"
              rx="4"
              opacity={0.7}
            />
            
            <text
              x={width / 2}
              y={outcomesY - 20}
              textAnchor="middle"
              fill={healthForesightColors.neutral.mid}
              fontSize="13"
              fontWeight="700"
            >
              Observed System Outcomes
            </text>
            
            {/* Outcome labels */}
            <text
              x={width / 2 - 150}
              y={outcomesY + 5}
              textAnchor="middle"
              fill={healthForesightColors.neutral.dark}
              fontSize="12"
              fontWeight="600"
            >
              Utilization shift
            </text>
            <text
              x={width / 2 - 50}
              y={outcomesY + 5}
              textAnchor="middle"
              fill={healthForesightColors.neutral.dark}
              fontSize="12"
              fontWeight="600"
            >
              Acuity increase
            </text>
            <text
              x={width / 2 + 50}
              y={outcomesY + 5}
              textAnchor="middle"
              fill={healthForesightColors.neutral.dark}
              fontSize="12"
              fontWeight="600"
            >
              Cost redistribution
            </text>
            <text
              x={width / 2 + 150}
              y={outcomesY + 5}
              textAnchor="middle"
              fill={healthForesightColors.neutral.dark}
              fontSize="12"
              fontWeight="600"
            >
              Network leakage
            </text>
          </g>
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
          Key Insight
        </Typography>
        <Typography
          sx={{
            fontSize: '14px',
            color: healthForesightColors.neutral.dark,
            lineHeight: 1.7,
          }}
        >
          Policy does not cause outcomes directly. It perturbs behavior across multiple actors, over time, with competing adaptations. Responses happen in parallel, not sequentially. Outcomes emerge downstream, not immediately.
        </Typography>
      </Box>
    </Box>
  )
}
