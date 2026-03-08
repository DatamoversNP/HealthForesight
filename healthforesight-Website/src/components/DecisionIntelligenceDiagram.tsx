/**
 * Decision Intelligence Diagram
 * Animated diagram showing the learning system flow
 * Inspired by Leo9 Studio's interactive diagrams
 */
import React, { useEffect, useRef } from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'
import { gsap } from 'gsap'

export default function DecisionIntelligenceDiagram() {
  const svgRef = useRef<SVGSVGElement>(null)
  const lightbulbRef = useRef<SVGGElement>(null)
  const gaugeRef = useRef<SVGGElement>(null)
  const dataClusterRef = useRef<SVGGElement>(null)
  const visualizationRef = useRef<SVGGElement>(null)
  const outputGridRef = useRef<SVGGElement>(null)
  const flowPathRef = useRef<SVGPathElement>(null)
  const flowCircleRef = useRef<SVGCircleElement>(null)
  const animationRef = useRef<number>()

  useEffect(() => {
    if (!svgRef.current) return

    // Animate elements on mount
    const tl = gsap.timeline({ repeat: -1, repeatDelay: 1 })

    // Pulse the lightbulb core
    if (lightbulbRef.current) {
      const core = lightbulbRef.current.querySelector('#lightbulbCore')
      if (core) {
        gsap.to(core, {
          scale: 1.2,
          opacity: 0.8,
          duration: 1.5,
          ease: 'power2.inOut',
          repeat: -1,
          yoyo: true,
        })
      }
    }

    // Animate gauge indicator
    if (gaugeRef.current) {
      const indicator = gaugeRef.current.querySelector('#gaugeIndicator')
      if (indicator) {
        gsap.to(indicator, {
          y: -60,
          duration: 2,
          ease: 'power2.inOut',
          repeat: -1,
          yoyo: true,
        })
      }
    }

    // Animate data cluster circles
    if (dataClusterRef.current) {
      const circles = dataClusterRef.current.querySelectorAll('circle')
      circles.forEach((circle, i) => {
        gsap.to(circle, {
          scale: 1.3,
          opacity: 0.6,
          duration: 1 + i * 0.2,
          ease: 'power2.inOut',
          repeat: -1,
          yoyo: true,
          delay: i * 0.1,
        })
      })
    }

    // Animate visualization line
    if (visualizationRef.current) {
      const line = visualizationRef.current.querySelector('#trendLine')
      if (line) {
        const pathLength = (line as SVGPathElement).getTotalLength()
        gsap.set(line, { strokeDasharray: pathLength, strokeDashoffset: pathLength })
        gsap.to(line, {
          strokeDashoffset: 0,
          duration: 3,
          ease: 'power2.inOut',
          repeat: -1,
          yoyo: true,
        })
      }
    }

    // Animate flow circle along path
    if (flowPathRef.current && flowCircleRef.current) {
      const path = flowPathRef.current
      const circle = flowCircleRef.current
      const pathLength = path.getTotalLength()

      // Manual animation along path
      let progress = 0
      const animate = () => {
        progress += 0.003
        if (progress > 1) progress = 0

        const point = path.getPointAtLength(progress * pathLength)
        circle.setAttribute('cx', String(point.x))
        circle.setAttribute('cy', String(point.y))

        animationRef.current = requestAnimationFrame(animate)
      }
      animate()
    }

    // Animate output grid squares
    if (outputGridRef.current) {
      const squares = outputGridRef.current.querySelectorAll('rect')
      squares.forEach((square, i) => {
        gsap.to(square, {
          opacity: 0.3,
          duration: 1.5,
          ease: 'power2.inOut',
          repeat: -1,
          yoyo: true,
          delay: i * 0.2,
        })
      })
    }

    return () => {
      tl.kill()
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [])

  return (
    <Box
      sx={{
        width: '100%',
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        py: 4,
      }}
    >
      <svg
        ref={svgRef}
        width="100%"
        height="600"
        viewBox="0 0 800 600"
        style={{ overflow: 'visible' }}
      >
        <defs>
          {/* Gradients */}
          <linearGradient id="lightbulbGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#FF6B6B" stopOpacity="1" />
            <stop offset="100%" stopColor="#EE5A52" stopOpacity="1" />
          </linearGradient>
          <linearGradient id="connectionGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={healthForesightColors.primary.main} stopOpacity="0.6" />
            <stop offset="100%" stopColor={healthForesightColors.accent.main} stopOpacity="0.6" />
          </linearGradient>
          
          {/* Filters */}
          <filter id="glow">
            <feGaussianBlur stdDeviation="4" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="shadow">
            <feDropShadow dx="0" dy="4" stdDeviation="8" floodOpacity="0.3" />
          </filter>
        </defs>

        {/* Background dotted arc */}
        <path
          d="M 50 50 Q 400 100 750 150"
          stroke={healthForesightColors.neutral.light}
          strokeWidth="2"
          fill="none"
          strokeDasharray="8,8"
          opacity="0.4"
        />

        {/* Main flow path (cyclical) */}
        <path
          ref={flowPathRef}
          id="flowPath"
          d="M 100 450 L 100 350 Q 100 250 200 200 Q 300 150 400 150 Q 500 150 600 200 Q 700 250 700 350 L 700 450 Q 700 550 600 500 Q 500 450 400 450 Q 300 450 200 500 Q 100 550 100 450"
          stroke="none"
          fill="none"
        />

        {/* Animated flow circle - initialized at start of path */}
        <circle
          ref={flowCircleRef}
          cx="100"
          cy="450"
          r="8"
          fill={healthForesightColors.accent.main}
          opacity="0.9"
          style={{
            filter: 'url(#glow)',
          }}
        />

        {/* Left Vertical Gauge */}
        <g ref={gaugeRef} transform="translate(100, 100)">
          <rect
            x="0"
            y="0"
            width="40"
            height="250"
            fill="none"
            stroke={healthForesightColors.neutral.dark}
            strokeWidth="3"
            rx="4"
          />
          {/* Tick marks */}
          {[0, 50, 100, 150, 200, 250].map((y, i) => (
            <line
              key={i}
              x1="40"
              y1={y}
              x2="50"
              y2={y}
              stroke={healthForesightColors.neutral.dark}
              strokeWidth="2"
            />
          ))}
          {/* Animated indicator */}
          <circle
            id="gaugeIndicator"
            cx="20"
            cy="200"
            r="12"
            fill={healthForesightColors.primary.main}
            filter="url(#shadow)"
          />
        </g>

        {/* Connection: Gauge to Data Cluster */}
        <line
          x1="100"
          y1="350"
          x2="200"
          y2="450"
          stroke={healthForesightColors.primary.main}
          strokeWidth="3"
          opacity="0.6"
        />

        {/* Bottom-Left Data Cluster */}
        <g ref={dataClusterRef} transform="translate(200, 450)">
          <rect
            x="-30"
            y="-30"
            width="60"
            height="60"
            fill="none"
            stroke={healthForesightColors.neutral.dark}
            strokeWidth="2"
            rx="4"
          />
          {/* Central circle */}
          <circle cx="0" cy="0" r="8" fill={healthForesightColors.primary.main} opacity="0.8" />
          {/* Surrounding circles */}
          {[0, 72, 144, 216, 288].map((angle, i) => {
            const rad = (angle * Math.PI) / 180
            const x = Math.cos(rad) * 18
            const y = Math.sin(rad) * 18
            return (
              <circle
                key={i}
                cx={x}
                cy={y}
                r="6"
                fill="none"
                stroke={healthForesightColors.accent.main}
                strokeWidth="2"
                opacity="0.7"
              />
            )
          })}
        </g>

        {/* Connection: Data Cluster to Visualization */}
        <line
          x1="200"
          y1="450"
          x2="400"
          y2="450"
          stroke={healthForesightColors.accent.main}
          strokeWidth="3"
          opacity="0.6"
        />

        {/* Bottom-Right Data Visualization */}
        <g ref={visualizationRef} transform="translate(400, 450)">
          <rect
            x="-80"
            y="-40"
            width="160"
            height="80"
            fill="none"
            stroke={healthForesightColors.neutral.dark}
            strokeWidth="2"
            rx="4"
          />
          {/* Trend line (mountain graph) */}
          <path
            id="trendLine"
            d="M -70 30 L -40 10 L -10 20 L 20 -10 L 50 0 L 70 15"
            stroke={healthForesightColors.primary.main}
            strokeWidth="3"
            fill="none"
            opacity="0.8"
          />
          {/* Business impact indicator */}
          <circle cx="60" cy="-20" r="6" fill="#FF6B6B" filter="url(#glow)" />
        </g>

        {/* Connection: Visualization to Output Grid */}
        <line
          x1="400"
          y1="410"
          x2="600"
          y2="200"
          stroke={healthForesightColors.accent.main}
          strokeWidth="3"
          opacity="0.6"
        />

        {/* Top-Right Output Grid */}
        <g ref={outputGridRef} transform="translate(600, 200)">
          <rect
            x="-40"
            y="-60"
            width="80"
            height="120"
            fill="none"
            stroke={healthForesightColors.neutral.dark}
            strokeWidth="2"
            rx="4"
          />
          {/* 2x3 grid of squares */}
          {[0, 1, 2, 3, 4, 5].map((i) => {
            const row = Math.floor(i / 2)
            const col = i % 2
            return (
              <rect
                key={i}
                x={-30 + col * 30}
                y={-50 + row * 40}
                width="20"
                height="20"
                fill="none"
                stroke={healthForesightColors.primary.main}
                strokeWidth="2"
                opacity="0.6"
              />
            )
          })}
          {/* Business impact indicator */}
          <circle cx="0" cy="50" r="6" fill="#FF6B6B" filter="url(#glow)" />
        </g>

        {/* Connection: Output Grid to Hexagonal Connector */}
        <line
          x1="560"
          y1="200"
          x2="500"
          y2="150"
          stroke={healthForesightColors.primary.main}
          strokeWidth="3"
          opacity="0.6"
        />

        {/* Hexagonal Connector */}
        <g transform="translate(400, 150)">
          <polygon
            points="-60,-10 -40,-20 40,-20 60,-10 40,0 -40,0"
            fill="none"
            stroke={healthForesightColors.neutral.dark}
            strokeWidth="3"
          />
        </g>

        {/* Connection: Hexagonal Connector back to Gauge (completing loop) */}
        <line
          x1="340"
          y1="150"
          x2="100"
          y2="200"
          stroke={healthForesightColors.primary.main}
          strokeWidth="3"
          opacity="0.6"
        />

        {/* Central Lightbulb (Idea/Core Concept) */}
        <g ref={lightbulbRef} transform="translate(400, 300)">
          {/* Shadow */}
          <ellipse cx="5" cy="85" rx="35" ry="15" fill="#000000" opacity="0.2" />
          {/* Bulb outline */}
          <path
            d="M 0 0 L -25 0 Q -35 10 -35 25 L -35 50 Q -35 60 -25 70 L 25 70 Q 35 60 35 50 L 35 25 Q 35 10 25 0 Z"
            fill="none"
            stroke={healthForesightColors.neutral.dark}
            strokeWidth="4"
            filter="url(#shadow)"
          />
          {/* Bulb base */}
          <rect x="-15" y="70" width="30" height="20" fill={healthForesightColors.neutral.dark} />
          {/* Core (red circle) */}
          <circle
            id="lightbulbCore"
            cx="0"
            cy="35"
            r="18"
            fill="url(#lightbulbGradient)"
            filter="url(#glow)"
          />
          {/* Filament lines */}
          <line x1="-12" y1="35" x2="12" y2="35" stroke="#FFFFFF" strokeWidth="2" opacity="0.8" />
          <line x1="0" y1="20" x2="0" y2="50" stroke="#FFFFFF" strokeWidth="2" opacity="0.8" />
        </g>

        {/* Connection lines from lightbulb to components */}
        <line
          x1="375"
          y1="300"
          x2="120"
          y2="200"
          stroke={healthForesightColors.neutral.light}
          strokeWidth="2"
          strokeDasharray="4,4"
          opacity="0.4"
        />
        <line
          x1="400"
          y1="330"
          x2="400"
          y2="410"
          stroke={healthForesightColors.neutral.light}
          strokeWidth="2"
          strokeDasharray="4,4"
          opacity="0.4"
        />
        <line
          x1="425"
          y1="300"
          x2="600"
          y2="200"
          stroke={healthForesightColors.neutral.light}
          strokeWidth="2"
          strokeDasharray="4,4"
          opacity="0.4"
        />
      </svg>
    </Box>
  )
}
