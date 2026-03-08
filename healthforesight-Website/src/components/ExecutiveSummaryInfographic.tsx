/**
 * Executive Summary Infographic: Three stacked blocks
 * Policy intent → Behavioral response → System outcome
 * Color progression: neutral → teal → amber (risk)
 */
import React, { useEffect, useState } from 'react'
import { Box, Typography } from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'

export default function ExecutiveSummaryInfographic() {
  const [visibleBlocks, setVisibleBlocks] = useState<boolean[]>([])

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          [0, 1, 2].forEach((idx) => {
            setTimeout(() => {
              setVisibleBlocks((prev) => {
                const newBlocks = [...prev]
                newBlocks[idx] = true
                return newBlocks
              })
            }, idx * 200)
          })
        }
      },
      { threshold: 0.2 }
    )

    const element = document.getElementById('exec-summary-infographic')
    if (element) observer.observe(element)

    return () => observer.disconnect()
  }, [])

  const blocks = [
    {
      label: 'Policy Intent',
      color: healthForesightColors.neutral.mid,
      backgroundColor: healthForesightColors.neutral.background,
    },
    {
      label: 'Behavioral Response',
      color: healthForesightColors.accent.main,
      backgroundColor: `${healthForesightColors.accent.main}15`,
    },
    {
      label: 'System Outcome',
      color: healthForesightColors.amber.main,
      backgroundColor: `${healthForesightColors.amber.main}15`,
    },
  ]

  return (
    <Box
      id="exec-summary-infographic"
      sx={{
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
      }}
    >
      {blocks.map((block, idx) => (
        <Box
          key={idx}
          sx={{
            p: 3,
            backgroundColor: block.backgroundColor,
            border: `2px solid ${block.color}`,
            borderRadius: 2,
            opacity: visibleBlocks[idx] ? 1 : 0,
            transform: visibleBlocks[idx] ? 'translateY(0)' : 'translateY(20px)',
            transition: 'opacity 400ms ease, transform 400ms ease',
          }}
        >
          <Typography
            sx={{
              fontSize: '14px',
              fontWeight: 700,
              color: block.color,
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
              mb: 1,
            }}
          >
            {block.label}
          </Typography>
          <Box
            sx={{
              width: '100%',
              height: '4px',
              backgroundColor: block.color,
              borderRadius: 1,
            }}
          />
        </Box>
      ))}
    </Box>
  )
}
