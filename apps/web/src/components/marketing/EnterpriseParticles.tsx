/**
 * Enterprise-Grade Particle System
 * Professional, sophisticated particle effects for enterprise healthcare brand
 */
import { useEffect, useRef } from 'react'
import { healthForesightColors } from '../../theme/healthForesightTheme'

interface EnterpriseParticlesProps {
  count?: number
  color?: string
  speed?: number
  intensity?: 'subtle' | 'moderate' | 'strong'
}

interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  radius: number
  opacity: number
  targetOpacity: number
  life: number
  maxLife: number
}

export default function EnterpriseParticles({
  count = 120,
  color,
  speed = 0.4,
  intensity = 'moderate',
}: EnterpriseParticlesProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const particlesRef = useRef<Particle[]>([])
  const animationRef = useRef<number>()
  const mouseRef = useRef({ x: 0, y: 0 })
  const lastTimeRef = useRef<number>(0)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d', { alpha: true, desynchronized: true })
    if (!ctx) return

    // High DPI support
    const dpr = window.devicePixelRatio || 1
    const resizeCanvas = () => {
      const rect = canvas.getBoundingClientRect()
      canvas.width = rect.width * dpr
      canvas.height = rect.height * dpr
      ctx.scale(dpr, dpr)
      canvas.style.width = rect.width + 'px'
      canvas.style.height = rect.height + 'px'
    }

    resizeCanvas()
    window.addEventListener('resize', resizeCanvas)

    // Initialize particles with better distribution
    const particles: Particle[] = []
    const particleColor = color || healthForesightColors.primary.main
    const intensityMultiplier = intensity === 'subtle' ? 0.5 : intensity === 'moderate' ? 1 : 1.5

    for (let i = 0; i < count; i++) {
      particles.push({
        x: Math.random() * canvas.width / dpr,
        y: Math.random() * canvas.height / dpr,
        vx: (Math.random() - 0.5) * speed * 0.8,
        vy: (Math.random() - 0.5) * speed * 0.8,
        radius: Math.random() * 2.5 + 1.5,
        opacity: Math.random() * 0.4 + 0.1,
        targetOpacity: Math.random() * 0.4 + 0.1,
        life: Math.random() * 1000,
        maxLife: 2000 + Math.random() * 2000,
      })
    }

    particlesRef.current = particles

    // Mouse tracking with smoothing
    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect()
      mouseRef.current = {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      }
    }

    canvas.addEventListener('mousemove', handleMouseMove)

    // Create gradient for particles
    const createGradient = (x: number, y: number, radius: number) => {
      const gradient = ctx.createRadialGradient(x, y, 0, x, y, radius)
      gradient.addColorStop(0, particleColor + 'FF')
      gradient.addColorStop(0.5, particleColor + '80')
      gradient.addColorStop(1, particleColor + '00')
      return gradient
    }

    const animate = (currentTime: number) => {
      const deltaTime = currentTime - lastTimeRef.current
      lastTimeRef.current = currentTime

      ctx.clearRect(0, 0, canvas.width / dpr, canvas.height / dpr)

      const particles = particlesRef.current
      const mouse = mouseRef.current

      // Draw connections first (behind particles)
      ctx.globalCompositeOperation = 'multiply'
      particles.forEach((particle, i) => {
        particles.slice(i + 1).forEach((otherParticle) => {
          const dx = particle.x - otherParticle.x
          const dy = particle.y - otherParticle.y
          const distance = Math.sqrt(dx * dx + dy * dy)

          if (distance < 100) {
            const opacity = (1 - distance / 100) * 0.15 * intensityMultiplier
            const gradient = ctx.createLinearGradient(
              particle.x,
              particle.y,
              otherParticle.x,
              otherParticle.y
            )
            gradient.addColorStop(0, particleColor + Math.floor(opacity * 255).toString(16).padStart(2, '0'))
            gradient.addColorStop(1, particleColor + Math.floor(opacity * 255).toString(16).padStart(2, '0'))
            
            ctx.beginPath()
            ctx.moveTo(particle.x, particle.y)
            ctx.lineTo(otherParticle.x, otherParticle.y)
            ctx.strokeStyle = gradient
            ctx.lineWidth = 1.5
            ctx.stroke()
          }
        })
      })

      ctx.globalCompositeOperation = 'source-over'

      particles.forEach((particle) => {
        // Mouse interaction with smooth easing
        const dx = mouse.x - particle.x
        const dy = mouse.y - particle.y
        const distance = Math.sqrt(dx * dx + dy * dy)

        if (distance < 200) {
          const force = (200 - distance) / 200
          const angle = Math.atan2(dy, dx)
          particle.vx -= Math.cos(angle) * force * 0.015 * intensityMultiplier
          particle.vy -= Math.sin(angle) * force * 0.015 * intensityMultiplier
        }

        // Update position with smooth movement
        particle.x += particle.vx
        particle.y += particle.vy

        // Boundary handling with smooth bounce
        if (particle.x < 0 || particle.x > canvas.width / dpr) {
          particle.vx *= -0.85
          particle.x = Math.max(0, Math.min(canvas.width / dpr, particle.x))
        }
        if (particle.y < 0 || particle.y > canvas.height / dpr) {
          particle.vy *= -0.85
          particle.y = Math.max(0, Math.min(canvas.height / dpr, particle.y))
        }

        // Smooth damping
        particle.vx *= 0.985
        particle.vy *= 0.985

        // Life cycle for opacity pulsing
        particle.life += deltaTime
        if (particle.life > particle.maxLife) {
          particle.life = 0
          particle.targetOpacity = Math.random() * 0.4 + 0.1
        }
        particle.opacity += (particle.targetOpacity - particle.opacity) * 0.02

        // Draw particle with gradient glow
        const gradient = createGradient(particle.x, particle.y, particle.radius * 3)
        ctx.beginPath()
        ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2)
        ctx.fillStyle = gradient
        ctx.globalAlpha = particle.opacity * intensityMultiplier
        ctx.fill()
        ctx.globalAlpha = 1

        // Outer glow ring
        ctx.beginPath()
        ctx.arc(particle.x, particle.y, particle.radius * 2, 0, Math.PI * 2)
        ctx.strokeStyle = particleColor + Math.floor(particle.opacity * 30).toString(16).padStart(2, '0')
        ctx.lineWidth = 0.5
        ctx.stroke()
      })

      animationRef.current = requestAnimationFrame(animate)
    }

    animationRef.current = requestAnimationFrame(animate)
    lastTimeRef.current = performance.now()

    return () => {
      window.removeEventListener('resize', resizeCanvas)
      canvas.removeEventListener('mousemove', handleMouseMove)
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [count, speed, color, intensity])

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        zIndex: 0,
      }}
    />
  )
}
