/**
 * Short Term vs Long Term Chart
 * Two stacked panels: Top = 6-month window (looks successful), Bottom = 24-month window (rebound visible)
 */
import React, { useEffect, useState } from 'react'
import { Box, Typography } from '@mui/material'
import { healthForesightColors } from '../../theme/healthForesightTheme'

export default function ShortTermVsLongTermChart() {
  const [topVisible, setTopVisible] = useState(false)
  const [bottomVisible, setBottomVisible] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          setTopVisible(true)
          setTimeout(() => setBottomVisible(true), 500)
        }
      },
      { threshold: 0.2 }
    )

    const element = document.getElementById('short-long-term-chart')
    if (element) observer.observe(element)

    return () => observer.disconnect()
  }, [])

  const width = 700
  const height = 200
  const padding = 50

  // 6-month window: declining line
  const shortTermPath = `M ${padding} ${padding + 50} 
    L ${padding + 200} ${padding + 80}
    L ${width - padding} ${padding + 90}`

  // 24-month window: declining then rebounding
  const longTermPath = `M ${padding} ${padding + 50} 
    L ${padding + 200} ${padding + 80}
    L ${padding + 400} ${padding + 90}
    L ${width - padding} ${padding + 120}`

  return (
    <Box
      id="short-long-term-chart"
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
        viewBox={`0 0 ${width} ${height * 2 + 50}`}
        sx={{
          width: '100%',
          height: '100%',
          maxHeight: '500px',
        }}
      >
        {/* Top Panel: 6-month window */}
        <g>
          <text
            x={width / 2}
            y={30}
            textAnchor="middle"
            fill={healthForesightColors.neutral.dark}
            fontSize="16"
            fontWeight="700"
          >
            6-Month Window (Looks Successful)
          </text>
          <rect
            x={padding - 20}
            y={40}
            width={width - padding * 2 + 40}
            height={height}
            fill={healthForesightColors.neutral.background}
            stroke={healthForesightColors.neutral.light}
            strokeWidth="2"
            rx="4"
          />
          {/* Axes */}
          <line
            x1={padding}
            y1={60}
            x2={padding}
            y2={height + 20}
            stroke={healthForesightColors.neutral.mid}
            strokeWidth="2"
          />
          <line
            x1={padding}
            y1={height + 20}
            x2={width - padding}
            y2={height + 20}
            stroke={healthForesightColors.neutral.mid}
            strokeWidth="2"
          />
          {/* Line */}
          {topVisible && (
            <path
              d={shortTermPath}
              fill="none"
              stroke={healthForesightColors.primary.main}
              strokeWidth="3"
            />
          )}
        </g>

        {/* Bottom Panel: 24-month window */}
        <g transform={`translate(0, ${height + 50})`}>
          <text
            x={width / 2}
            y={30}
            textAnchor="middle"
            fill={healthForesightColors.neutral.dark}
            fontSize="16"
            fontWeight="700"
          >
            24-Month Window (Rebound Visible)
          </text>
          <rect
            x={padding - 20}
            y={40}
            width={width - padding * 2 + 40}
            height={height}
            fill={healthForesightColors.neutral.background}
            stroke={healthForesightColors.neutral.light}
            strokeWidth="2"
            rx="4"
          />
          {/* Axes */}
          <line
            x1={padding}
            y1={60}
            x2={padding}
            y2={height + 20}
            stroke={healthForesightColors.neutral.mid}
            strokeWidth="2"
          />
          <line
            x1={padding}
            y1={height + 20}
            x2={width - padding}
            y2={height + 20}
            stroke={healthForesightColors.neutral.mid}
            strokeWidth="2"
          />
          {/* Line */}
          {bottomVisible && (
            <path
              d={longTermPath}
              fill="none"
              stroke={healthForesightColors.amber.main}
              strokeWidth="3"
            />
          )}
        </g>
      </Box>
    </Box>
  )
}
