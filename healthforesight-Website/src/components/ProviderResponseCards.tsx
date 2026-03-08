/**
 * Provider Response Cards
 * 4 horizontal cards: Compliance, Adaptation, Resistance, Circumvention
 * Each with 1-line definition and 1 example
 */
import React, { useEffect, useState } from 'react'
import { Box, Typography, Card } from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'

export default function ProviderResponseCards() {
  const [cardsVisible, setCardsVisible] = useState<boolean[]>([])

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          // Cards fade in left → right
          [0, 1, 2, 3].forEach((idx) => {
            setTimeout(() => {
              setCardsVisible((prev) => {
                const newCards = [...prev]
                newCards[idx] = true
                return newCards
              })
            }, idx * 150)
          })
        }
      },
      { threshold: 0.2 }
    )

    const element = document.getElementById('provider-response-cards')
    if (element) observer.observe(element)

    return () => observer.disconnect()
  }, [])

  const responses = [
    {
      title: 'Compliance',
      definition: 'Providers reduce utilization when policies align with clinical norms.',
      example: 'Prior auth for imaging reduces unnecessary scans.',
      color: healthForesightColors.accent.main,
    },
    {
      title: 'Adaptation',
      definition: 'Providers substitute services, alter care pathways, or shift sites of care.',
      example: 'Outpatient restrictions lead to ED utilization.',
      color: healthForesightColors.primary.main,
    },
    {
      title: 'Resistance',
      definition: 'Providers increase appeals, documentation intensity, or administrative escalation.',
      example: 'Appeal rates increase 40% post-policy.',
      color: healthForesightColors.neutral.mid,
    },
    {
      title: 'Circumvention',
      definition: 'Providers exploit policy gaps, exceptions, or ungoverned settings.',
      example: 'Coding changes preserve volume under different labels.',
      color: healthForesightColors.amber.main,
    },
  ]

  return (
    <Box
      id="provider-response-cards"
      sx={{
        display: 'flex',
        flexDirection: { xs: 'column', md: 'row' },
        gap: 3,
        flexWrap: 'wrap',
      }}
    >
      {responses.map((response, idx) => (
        <Card
          key={idx}
          sx={{
            flex: { xs: '1 1 100%', md: '1 1 calc(25% - 24px)' },
            minWidth: { xs: '100%', md: '200px' },
            p: 3,
            border: `2px solid ${response.color}`,
            backgroundColor: '#FFFFFF',
            opacity: cardsVisible[idx] ? 1 : 0,
            transform: cardsVisible[idx] ? 'translateX(0)' : 'translateX(-20px)',
            transition: 'opacity 400ms ease, transform 400ms ease',
          }}
        >
          <Typography
            variant="h6"
            sx={{
              fontSize: '18px',
              fontWeight: 700,
              mb: 2,
              color: response.color,
            }}
          >
            {response.title}
          </Typography>
          <Typography
            variant="body2"
            sx={{
              fontSize: '14px',
              color: healthForesightColors.neutral.dark,
              lineHeight: 1.7,
              mb: 2,
            }}
          >
            {response.definition}
          </Typography>
          <Typography
            variant="body2"
            sx={{
              fontSize: '13px',
              color: healthForesightColors.neutral.mid,
              lineHeight: 1.6,
              fontStyle: 'italic',
            }}
          >
            Example: {response.example}
          </Typography>
        </Card>
      ))}
    </Box>
  )
}
