/**
 * GSAP Animation Wrapper
 * Provides smooth, professional animations inspired by Leo9 Studio
 */
import { useEffect, useRef, useState } from 'react'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

// Register ScrollTrigger plugin
if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger)
}

interface GSAPAnimationsProps {
  children: React.ReactNode
  animationType?: 'fadeInUp' | 'fadeIn' | 'scaleIn' | 'slideInLeft' | 'slideInRight'
  delay?: number
  duration?: number
  trigger?: string | Element | null
}

export default function GSAPAnimations({
  children,
  animationType = 'fadeInUp',
  delay = 0,
  duration = 1,
  trigger,
}: GSAPAnimationsProps) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!ref.current) return

    const element = ref.current

    // Set initial state
    const animations = {
      fadeInUp: { opacity: 0, y: 60 },
      fadeIn: { opacity: 0 },
      scaleIn: { opacity: 0, scale: 0.8 },
      slideInLeft: { opacity: 0, x: -60 },
      slideInRight: { opacity: 0, x: 60 },
    }

    const initial = animations[animationType]
    gsap.set(element, initial)

    // Animate on scroll
    const triggerElement = trigger
      ? typeof trigger === 'string'
        ? document.querySelector(trigger)
        : trigger
      : element

      const animation = gsap.to(element, {
        opacity: 1,
        x: 0,
        y: 0,
        scale: 1,
        duration,
        delay,
        ease: 'power3.out',
        paused: true,
      })

      const scrollTrigger = ScrollTrigger.create({
        trigger: triggerElement || element,
        start: 'top 85%',
        animation: animation,
        toggleActions: 'play none none none',
      })

    return () => {
      scrollTrigger.kill()
    }
  }, [animationType, delay, duration, trigger])

  return <div ref={ref}>{children}</div>
}
