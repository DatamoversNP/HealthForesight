/**
 * How It Works Section 1: Policy Blueprint Card
 * Sections slide in one by one with snap animation
 */
import React, { useEffect, useState } from 'react'
import { Box, Typography } from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'

export default function PolicyBlueprintCard() {
  const [visibleSections, setVisibleSections] = useState<boolean[]>([false, false, false, false, false])
  const [hasAnimated, setHasAnimated] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !hasAnimated) {
          setHasAnimated(true)
          // Sections appear sequentially with snap animation
          setTimeout(() => setVisibleSections([true, false, false, false, false]), 0)
          setTimeout(() => setVisibleSections([true, true, false, false, false]), 200)
          setTimeout(() => setVisibleSections([true, true, true, false, false]), 400)
          setTimeout(() => setVisibleSections([true, true, true, true, false]), 600)
          setTimeout(() => setVisibleSections([true, true, true, true, true]), 800)
        }
      },
      { threshold: 0.3 }
    )

    const element = document.getElementById('policy-blueprint')
    if (element) {
      observer.observe(element)
    }

    return () => observer.disconnect()
  }, [hasAnimated])

  const sections = [
    { label: 'Who', value: 'Population, Plan, Geography', icon: '👥' },
    { label: 'Where', value: 'Networks, Providers, Sites', icon: '📍' },
    { label: 'How', value: 'Authorization, Restriction, Sequencing', icon: '⚙️' },
    { label: 'When', value: 'Effective Dates, Versions', icon: '📅' },
    { label: 'Exclusions', value: 'Exceptions, Carve-outs', icon: '🚫' },
  ]

  return (
    <Box
      id="policy-blueprint"
      sx={{
        width: '100%',
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: 2,
        overflow: 'visible',
      }}
    >
      <Box
        sx={{
          width: '100%',
          maxWidth: '480px',
          backgroundColor: '#FFFFFF',
          borderRadius: 3,
          boxShadow: `0 8px 32px ${healthForesightColors.neutral.dark}20`,
          overflow: 'visible',
        }}
      >
        {/* Header */}
        <Box
          sx={{
            p: 2.5,
            backgroundColor: healthForesightColors.primary.main,
            color: '#FFFFFF',
          }}
        >
          <Typography
            sx={{
              fontSize: '16px',
              fontWeight: 700,
              color: '#FFFFFF',
            }}
          >
            Policy Definition
          </Typography>
        </Box>

        {/* Sections */}
        {sections.map((section, idx) => (
          <Box
            key={idx}
            sx={{
              p: 2.5,
              borderBottom: idx < sections.length - 1 ? `1px solid ${healthForesightColors.neutral.light}` : 'none',
              transform: visibleSections[idx] ? 'translateX(0)' : 'translateX(-20px)',
              opacity: visibleSections[idx] ? 1 : 0,
              boxShadow: visibleSections[idx] ? `0 4px 12px ${healthForesightColors.primary.main}15` : 'none',
              transition: 'all 200ms cubic-bezier(0.4, 0, 0.2, 1)',
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2, mb: 1 }}>
              <Box
                sx={{
                  width: 36,
                  height: 36,
                  borderRadius: 2,
                  backgroundColor: healthForesightColors.primary.main + '15',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '18px',
                  flexShrink: 0,
                }}
              >
                {section.icon}
              </Box>
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Typography
                  sx={{
                    fontSize: '15px',
                    fontWeight: 700,
                    color: healthForesightColors.neutral.dark,
                    mb: 0.5,
                  }}
                >
                  {section.label}
                </Typography>
                <Typography
                  sx={{
                    fontSize: '13px',
                    color: healthForesightColors.neutral.mid,
                    lineHeight: 1.5,
                  }}
                >
                  {section.value}
                </Typography>
              </Box>
            </Box>
          </Box>
        ))}
      </Box>
    </Box>
  )
}
