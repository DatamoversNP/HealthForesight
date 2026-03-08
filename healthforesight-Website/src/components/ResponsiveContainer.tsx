/**
 * ResponsiveContainer - Production-grade responsive layout wrapper
 * Provides consistent max-width, padding, and responsive behavior
 */
import React from 'react'
import { Box, Container } from '@mui/material'
import { SxProps, Theme } from '@mui/material/styles'

interface ResponsiveContainerProps {
  children: React.ReactNode
  maxWidth?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | false
  disableGutters?: boolean
  sx?: SxProps<Theme>
  /** Additional padding for sections (vertical) */
  section?: boolean
  /** Tight spacing for compact sections */
  tight?: boolean
}

export default function ResponsiveContainer({
  children,
  maxWidth = 'xl',
  disableGutters = false,
  section = false,
  tight = false,
  sx,
}: ResponsiveContainerProps) {
  return (
    <Container
      maxWidth={maxWidth}
      disableGutters={disableGutters}
      sx={{
        px: {
          xs: 2, // 16px on mobile
          sm: 3, // 24px on small tablets
          md: 4, // 32px on tablets
          lg: 5, // 40px on desktop
          xl: 6, // 48px on large desktop
        },
        ...(section && {
          py: {
            xs: tight ? 4 : 6, // 24px or 48px on mobile
            sm: tight ? 6 : 8, // 48px or 64px on small tablets
            md: tight ? 8 : 10, // 64px or 80px on tablets
            lg: tight ? 10 : 12, // 80px or 96px on desktop
            xl: tight ? 12 : 14, // 96px or 112px on large desktop
          },
        }),
        ...sx,
      }}
    >
      {children}
    </Container>
  )
}

/**
 * ResponsiveGrid - Production-grade responsive grid system
 * Automatically adjusts columns based on screen size
 */
interface ResponsiveGridProps {
  children: React.ReactNode
  columns?: {
    xs?: number
    sm?: number
    md?: number
    lg?: number
    xl?: number
  }
  gap?: number | { xs?: number; sm?: number; md?: number; lg?: number; xl?: number }
  sx?: SxProps<Theme>
}

export function ResponsiveGrid({ children, columns = { xs: 1, md: 2, lg: 3 }, gap = 3, sx }: ResponsiveGridProps) {
  const gapValue = typeof gap === 'number' 
    ? gap 
    : { xs: gap.xs || 2, sm: gap.sm || 3, md: gap.md || 3, lg: gap.lg || 4, xl: gap.xl || 4 }

  return (
    <Box
      sx={{
        display: 'grid',
        gridTemplateColumns: {
          xs: `repeat(${columns.xs || 1}, 1fr)`,
          sm: `repeat(${columns.sm || columns.xs || 1}, 1fr)`,
          md: `repeat(${columns.md || 2}, 1fr)`,
          lg: `repeat(${columns.lg || 3}, 1fr)`,
          xl: `repeat(${columns.xl || columns.lg || 3}, 1fr)`,
        },
        gap: gapValue,
        ...sx,
      }}
    >
      {children}
    </Box>
  )
}

/**
 * ResponsiveSection - Standard section wrapper with consistent spacing
 */
interface ResponsiveSectionProps {
  children: React.ReactNode
  background?: 'light' | 'dark' | 'transparent'
  sx?: SxProps<Theme>
  tight?: boolean
}

export function ResponsiveSection({ children, background = 'transparent', tight = false, sx }: ResponsiveSectionProps) {
  const backgroundColor = {
    light: '#FFFFFF',
    dark: '#0F172A',
    transparent: 'transparent',
  }[background]

  return (
    <Box
      component="section"
      sx={{
        backgroundColor,
        py: {
          xs: tight ? 4 : 6,
          sm: tight ? 6 : 8,
          md: tight ? 8 : 10,
          lg: tight ? 10 : 12,
          xl: tight ? 12 : 14,
        },
        ...sx,
      }}
    >
      {children}
    </Box>
  )
}
