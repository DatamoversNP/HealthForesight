/**
 * Care Continuum Heat Band: Outpatient → ED → Inpatient → Post-acute
 * When one segment cools (↓), others warm (↑)
 */
import React, { useEffect, useState } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../../theme/healthForesightTheme'

export default function CareContinuumHeatBand() {
  const [visible, setVisible] = useState(false)
  const [policyActive, setPolicyActive] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          setVisible(true)
          setTimeout(() => setPolicyActive(true), 1000)
        }
      },
      { threshold: 0.2 }
    )

    const element = document.getElementById('care-continuum-heat')
    if (element) observer.observe(element)

    return () => observer.disconnect()
  }, [])

  const width = 600
  const height = 200
  const segmentWidth = width / 4
  const segments = [
    { label: 'Outpatient', baseTemp: 0.7 },
    { label: 'ED', baseTemp: 0.5 },
    { label: 'Inpatient', baseTemp: 0.6 },
    { label: 'Post-acute', baseTemp: 0.4 },
  ]

  // Policy reduces outpatient, increases others
  const getTemp = (idx: number, baseTemp: number) => {
    if (!policyActive) return baseTemp
    if (idx === 0) return baseTemp - 0.3 // Outpatient cools
    return baseTemp + 0.2 // Others warm
  }

  const getColor = (temp: number) => {
    if (temp < 0.3) return healthForesightColors.accent.main // Cool (teal)
    if (temp < 0.6) return healthForesightColors.neutral.mid // Neutral
    return healthForesightColors.amber.main // Warm (amber/orange)
  }

  return (
    <Box
      id="care-continuum-heat"
      sx={{
        width: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: 2,
      }}
    >
      <Box
        component="svg"
        viewBox={`0 0 ${width} ${height}`}
        sx={{
          width: '100%',
          height: '100%',
          maxHeight: '250px',
        }}
      >
        {segments.map((segment, idx) => {
          const temp = getTemp(idx, segment.baseTemp)
          const color = getColor(temp)
          const heightValue = temp * 120 + 40

          return (
            <g key={idx} opacity={visible ? 1 : 0}>
              <rect
                x={idx * segmentWidth + 20}
                y={height - heightValue - 20}
                width={segmentWidth - 40}
                height={heightValue}
                fill={color}
                opacity={0.6}
                rx="4"
              />
              <text
                x={idx * segmentWidth + segmentWidth / 2}
                y={height - 10}
                textAnchor="middle"
                fill={healthForesightColors.neutral.dark}
                fontSize="12"
                fontWeight="700"
              >
                {segment.label}
              </text>
              {policyActive && (
                <text
                  x={idx * segmentWidth + segmentWidth / 2}
                  y={height - heightValue - 30}
                  textAnchor="middle"
                  fill={color}
                  fontSize="14"
                  fontWeight="700"
                >
                  {idx === 0 ? '↓' : '↑'}
                </text>
              )}
            </g>
          )
        })}

        {/* Policy marker */}
        {policyActive && (
          <line
            x1={width / 2}
            y1={20}
            x2={width / 2}
            y2={height - 20}
            stroke={healthForesightColors.primary.main}
            strokeWidth="2"
            strokeDasharray="4 4"
            opacity={0.5}
          />
        )}
      </Box>
    </Box>
  )
}
