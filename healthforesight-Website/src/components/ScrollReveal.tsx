/**
 * Scroll Reveal Component
 * Reveal on scroll: opacity 0 → 1 + translateY 12px → 0
 * duration 450-650ms, ease cubic-bezier(0.2, 0.8, 0.2, 1)
 */
import React, { useEffect, useRef, useState } from 'react'
import { Box } from '@mui/material'

interface ScrollRevealProps {
  children: React.ReactNode
  delay?: number
  duration?: number
  stagger?: number
}

export default function ScrollReveal({ children, delay = 0, duration = 550, stagger = 0 }: ScrollRevealProps) {
  const ref = useRef<HTMLDivElement>(null)
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !isVisible) {
          setTimeout(() => setIsVisible(true), delay + stagger)
        }
      },
      { threshold: 0.1 }
    )

    if (ref.current) {
      observer.observe(ref.current)
    }

    return () => observer.disconnect()
  }, [isVisible, delay, stagger])

  return (
    <Box
      ref={ref}
      sx={{
        opacity: isVisible ? 1 : 0,
        transform: isVisible ? 'translateY(0)' : 'translateY(12px)',
        transition: `opacity ${duration}ms cubic-bezier(0.2, 0.8, 0.2, 1), transform ${duration}ms cubic-bezier(0.2, 0.8, 0.2, 1)`,
      }}
    >
      {children}
    </Box>
  )
}
