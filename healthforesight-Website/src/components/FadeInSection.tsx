/**
 * Fade In Section Component
 * Smooth fade-in animation on scroll
 */
import React, { useEffect, useRef, useState } from 'react'
import { Box, BoxProps } from '@mui/material'

interface FadeInSectionProps extends BoxProps {
  children: React.ReactNode
  delay?: number
}

export default function FadeInSection({ children, delay = 0, ...props }: FadeInSectionProps) {
  const [isVisible, setIsVisible] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true)
        }
      },
      { threshold: 0.1 }
    )

    if (ref.current) {
      observer.observe(ref.current)
    }

    return () => {
      if (ref.current) {
        observer.unobserve(ref.current)
      }
    }
  }, [])

  return (
    <Box
      ref={ref}
      sx={{
        opacity: isVisible ? 1 : 0,
        transform: isVisible ? 'translateY(0)' : 'translateY(30px)',
        transition: `opacity 0.8s ease ${delay}s, transform 0.8s ease ${delay}s`,
        ...props.sx,
      }}
      {...props}
    >
      {children}
    </Box>
  )
}
