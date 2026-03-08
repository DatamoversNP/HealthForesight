/**
 * HealthForesight NarrativeBlock Component
 * "Narrative Before Visualization" - Every analytical screen must include this
 */
import React from 'react'
import { Box, Typography, Paper, Divider } from '@mui/material'
import { healthForesightColors } from '../../theme/healthForesightTheme'

interface NarrativeBlockProps {
  title: string
  whatChanged: string
  whyItMatters: string
  howConfident?: string
  assumptions?: string[]
  limitations?: string[]
  children?: React.ReactNode // Optional visualization after narrative
}

export default function NarrativeBlock({
  title,
  whatChanged,
  whyItMatters,
  howConfident,
  assumptions,
  limitations,
  children,
}: NarrativeBlockProps) {
  return (
    <Box sx={{ mb: 3 }}>
      <Paper
        variant="outlined"
        sx={{
          p: 3,
          backgroundColor: '#FFFFFF',
          borderColor: healthForesightColors.neutral.light,
        }}
      >
        <Typography
          variant="h5"
          sx={{
            fontFamily: 'IBM Plex Sans, Inter, sans-serif',
            fontWeight: 600,
            mb: 2,
            color: healthForesightColors.neutral.dark,
          }}
        >
          {title}
        </Typography>

        <Box sx={{ mb: 2 }}>
          <Typography
            variant="body2"
            sx={{
              fontWeight: 600,
              mb: 1,
              color: healthForesightColors.neutral.dark,
            }}
          >
            What changed?
          </Typography>
          <Typography variant="body1" sx={{ color: healthForesightColors.neutral.dark, lineHeight: 1.6 }}>
            {whatChanged}
          </Typography>
        </Box>

        <Box sx={{ mb: 2 }}>
          <Typography
            variant="body2"
            sx={{
              fontWeight: 600,
              mb: 1,
              color: healthForesightColors.neutral.dark,
            }}
          >
            Why it matters
          </Typography>
          <Typography variant="body1" sx={{ color: healthForesightColors.neutral.dark, lineHeight: 1.6 }}>
            {whyItMatters}
          </Typography>
        </Box>

        {howConfident && (
          <Box sx={{ mb: 2 }}>
            <Typography
              variant="body2"
              sx={{
                fontWeight: 600,
                mb: 1,
                color: healthForesightColors.neutral.dark,
              }}
            >
              How confident we are
            </Typography>
            <Typography variant="body1" sx={{ color: healthForesightColors.neutral.dark, lineHeight: 1.6 }}>
              {howConfident}
            </Typography>
          </Box>
        )}

        {(assumptions && assumptions.length > 0) || (limitations && limitations.length > 0) ? (
          <Box sx={{ mt: 2, pt: 2, borderTop: `1px solid ${healthForesightColors.neutral.light}` }}>
            {assumptions && assumptions.length > 0 && (
              <Box sx={{ mb: limitations && limitations.length > 0 ? 2 : 0 }}>
                <Typography
                  variant="caption"
                  sx={{
                    fontWeight: 600,
                    mb: 1,
                    color: healthForesightColors.neutral.mid,
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                  }}
                >
                  Key Assumptions
                </Typography>
                <Box component="ul" sx={{ m: 0, pl: 2.5 }}>
                  {assumptions.map((assumption, idx) => (
                    <li key={idx}>
                      <Typography variant="body2" sx={{ color: healthForesightColors.neutral.mid, lineHeight: 1.6 }}>
                        {assumption}
                      </Typography>
                    </li>
                  ))}
                </Box>
              </Box>
            )}

            {limitations && limitations.length > 0 && (
              <Box>
                <Typography
                  variant="caption"
                  sx={{
                    fontWeight: 600,
                    mb: 1,
                    color: healthForesightColors.neutral.mid,
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                  }}
                >
                  Limitations
                </Typography>
                <Box component="ul" sx={{ m: 0, pl: 2.5 }}>
                  {limitations.map((limitation, idx) => (
                    <li key={idx}>
                      <Typography variant="body2" sx={{ color: healthForesightColors.neutral.mid, lineHeight: 1.6 }}>
                        {limitation}
                      </Typography>
                    </li>
                  ))}
                </Box>
              </Box>
            )}
          </Box>
        ) : null}

        {children && (
          <>
            <Divider sx={{ my: 3 }} />
            <Box>{children}</Box>
          </>
        )}
      </Paper>
    </Box>
  )
}

