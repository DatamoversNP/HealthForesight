/**
 * ResponsiveVisualWrapper - Wrapper for all SVG/chart visual components
 * Ensures consistent responsive behavior across all visualizations
 */
import React from 'react'
import { Box, BoxProps } from '@mui/material'

interface ResponsiveVisualWrapperProps extends Omit<BoxProps, 'children'> {
  children: React.ReactNode
  /** Mobile height - defaults to 250px */
  mobileHeight?: number | string
  /** Desktop height - defaults to 400px */
  desktopHeight?: number | string
  /** Max width on desktop - defaults to 800px */
  maxWidth?: number | string
}

export default function ResponsiveVisualWrapper({
  children,
  mobileHeight = 250,
  desktopHeight = 400,
  maxWidth = 800,
  sx,
  ...props
}: ResponsiveVisualWrapperProps) {
  return (
    <Box
      {...props}
      sx={{
        width: '100%',
        maxWidth: { xs: '100%', md: maxWidth },
        height: { xs: mobileHeight, md: desktopHeight },
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: { xs: 2, md: 3 },
        ...sx,
      }}
    >
      {children}
    </Box>
  )
}
