/**
 * Quick Summary Panel - Sticky right sidebar for Executive Brief
 * Collapsible on mobile, sticky on desktop
 */
import React, { useState } from 'react'
import { Box, Typography, Accordion, AccordionSummary, AccordionDetails } from '@mui/material'
import { ExpandMore } from '@mui/icons-material'
import { healthForesightColors } from '../../theme/healthForesightTheme'

export default function QuickSummaryPanel() {
  const [expanded, setExpanded] = useState(false)

  const keyTakeaways = [
    'Policy uncertainty compounds into budget volatility and forecast error',
    'Point estimates mask behavioral adaptation and substitution effects',
    'Delayed cost emergence occurs outside measured service categories',
    'Leading organizations use range-based, elasticity-aware planning',
  ]

  return (
    <>
      {/* Desktop: Always visible */}
      <Box
        sx={{
          display: { xs: 'none', lg: 'block' },
          p: 3,
          backgroundColor: healthForesightColors.neutral.background,
          borderRadius: 2,
          border: `1px solid ${healthForesightColors.neutral.light}`,
        }}
      >
        <Typography
          variant="h6"
          sx={{
            fontSize: '18px',
            fontWeight: 700,
            mb: 3,
            color: healthForesightColors.neutral.dark,
          }}
        >
          Quick Summary
        </Typography>
        <Box component="ul" sx={{ pl: 2, m: 0 }}>
          {keyTakeaways.map((takeaway, idx) => (
            <Box component="li" key={idx} sx={{ mb: 2, fontSize: '14px', lineHeight: 1.7, color: healthForesightColors.neutral.dark }}>
              {takeaway}
            </Box>
          ))}
        </Box>
      </Box>

      {/* Mobile: Collapsible */}
      <Box sx={{ display: { xs: 'block', lg: 'none' }, mb: 4 }}>
        <Accordion
          expanded={expanded}
          onChange={() => setExpanded(!expanded)}
          sx={{
            border: `1px solid ${healthForesightColors.neutral.light}`,
            '&:before': { display: 'none' },
          }}
        >
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Typography
              sx={{
                fontSize: '16px',
                fontWeight: 700,
                color: healthForesightColors.neutral.dark,
              }}
            >
              Quick Summary
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Box component="ul" sx={{ pl: 2, m: 0 }}>
              {keyTakeaways.map((takeaway, idx) => (
                <Box component="li" key={idx} sx={{ mb: 2, fontSize: '14px', lineHeight: 1.7, color: healthForesightColors.neutral.dark }}>
                  {takeaway}
                </Box>
              ))}
            </Box>
          </AccordionDetails>
        </Accordion>
      </Box>
    </>
  )
}
