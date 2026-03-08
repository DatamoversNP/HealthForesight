/**
 * Visual 6: From Static to Adaptive Planning
 * Side-by-side cards: Static Budget Model vs Elasticity-Aware Planning Model
 */
import React, { useEffect, useState } from 'react'
import { Box, Typography, Card } from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'

export default function StaticVsAdaptivePlanning() {
  const [hoveredCard, setHoveredCard] = useState<string | null>(null)

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: { xs: 'column', md: 'row' },
        gap: 4,
        justifyContent: 'center',
      }}
    >
      {/* Static Budget Model */}
      <Card
        onMouseEnter={() => setHoveredCard('static')}
        onMouseLeave={() => setHoveredCard(null)}
        sx={{
          flex: 1,
          p: 4,
          border: `2px solid ${healthForesightColors.neutral.mid}`,
          backgroundColor: '#FFFFFF',
          transition: 'all 200ms ease',
          transform: hoveredCard === 'static' ? 'scale(1.02)' : 'scale(1)',
        }}
      >
        <Typography
          variant="h5"
          sx={{
            fontSize: { xs: '1.25rem', md: '1.5rem' },
            fontWeight: 700,
            mb: 3,
            color: healthForesightColors.neutral.dark,
          }}
        >
          Static Budget Model
        </Typography>
        <Box component="ul" sx={{ pl: 3, mb: 3 }}>
          {[
            'Fixed numbers',
            'Annual lock',
            'Point estimates',
            'No scenario planning',
          ].map((item, idx) => (
            <Box component="li" key={idx} sx={{ mb: 1.5, fontSize: { xs: '16px', md: '17px' }, lineHeight: 1.8 }}>
              {item}
            </Box>
          ))}
        </Box>
        {/* Visual representation - stays rigid */}
        <Box
          sx={{
            height: '120px',
            display: 'flex',
            alignItems: 'flex-end',
            justifyContent: 'center',
            gap: 2,
          }}
        >
          <Box
            sx={{
              width: '40px',
              height: '80px',
              backgroundColor: healthForesightColors.neutral.mid,
              borderRadius: 1,
            }}
          />
          <Box
            sx={{
              width: '40px',
              height: '80px',
              backgroundColor: healthForesightColors.neutral.mid,
              borderRadius: 1,
            }}
          />
          <Box
            sx={{
              width: '40px',
              height: '80px',
              backgroundColor: healthForesightColors.neutral.mid,
              borderRadius: 1,
            }}
          />
        </Box>
      </Card>

      {/* Elasticity-Aware Planning Model */}
      <Card
        onMouseEnter={() => setHoveredCard('adaptive')}
        onMouseLeave={() => setHoveredCard(null)}
        sx={{
          flex: 1,
          p: 4,
          border: `2px solid ${healthForesightColors.accent.main}`,
          backgroundColor: '#FFFFFF',
          transition: 'all 200ms ease',
          transform: hoveredCard === 'adaptive' ? 'scale(1.02)' : 'scale(1)',
        }}
      >
        <Typography
          variant="h5"
          sx={{
            fontSize: { xs: '1.25rem', md: '1.5rem' },
            fontWeight: 700,
            mb: 3,
            color: healthForesightColors.accent.main,
          }}
        >
          Elasticity-Aware Planning Model
        </Typography>
        <Box component="ul" sx={{ pl: 3, mb: 3 }}>
          {[
            'Scenario bands',
            'Rolling updates',
            'Range estimates',
            'Dynamic re-forecasting',
          ].map((item, idx) => (
            <Box component="li" key={idx} sx={{ mb: 1.5, fontSize: { xs: '16px', md: '17px' }, lineHeight: 1.8 }}>
              {item}
            </Box>
          ))}
        </Box>
        {/* Visual representation - shows shifting scenario band on hover */}
        <Box
          sx={{
            height: '120px',
            display: 'flex',
            alignItems: 'flex-end',
            justifyContent: 'center',
            gap: 2,
            position: 'relative',
          }}
        >
          {/* Scenario band (shifts on hover) */}
          <Box
            sx={{
              position: 'absolute',
              left: '50%',
              transform: 'translateX(-50%)',
              width: '140px',
              height: hoveredCard === 'adaptive' ? '100px' : '80px',
              backgroundColor: healthForesightColors.accent.main,
              opacity: 0.2,
              borderRadius: 1,
              transition: 'height 300ms ease, transform 300ms ease',
              transform: hoveredCard === 'adaptive' ? 'translateX(-50%) translateY(-10px)' : 'translateX(-50%)',
            }}
          />
          {/* Bars within band */}
          <Box
            sx={{
              width: '40px',
              height: hoveredCard === 'adaptive' ? '70px' : '60px',
              backgroundColor: healthForesightColors.accent.main,
              borderRadius: 1,
              transition: 'height 300ms ease',
            }}
          />
          <Box
            sx={{
              width: '40px',
              height: hoveredCard === 'adaptive' ? '90px' : '80px',
              backgroundColor: healthForesightColors.accent.main,
              borderRadius: 1,
              transition: 'height 300ms ease',
            }}
          />
          <Box
            sx={{
              width: '40px',
              height: hoveredCard === 'adaptive' ? '75px' : '65px',
              backgroundColor: healthForesightColors.accent.main,
              borderRadius: 1,
              transition: 'height 300ms ease',
            }}
          />
        </Box>
      </Card>
    </Box>
  )
}
