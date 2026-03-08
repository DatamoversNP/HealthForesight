/**
 * Who It's For Page - Decision Authority Focus
 * Enterprise business artifacts: Decision Ledger, Responsibility Matrix, Briefing Tiles
 * No circles, networks, timelines, or repeated motifs
 */
import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Container,
  Typography,
  Button,
} from '@mui/material'
import { healthForesightColors } from '../../theme/healthForesightTheme'
import ScrollReveal from '../../components/marketing/ScrollReveal'

// Decision Ledger Component (Hero)
function DecisionLedger() {
  const [revealed, setRevealed] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => setRevealed(true), 120)
    return () => clearTimeout(timer)
  }, [])

  const rows = [
    { label: 'Decision Type', value: 'Utilization Policy' },
    { label: 'Scope', value: 'Network / Population / Service' },
    { label: 'Outcome', value: 'Expected vs Observed' },
  ]

  return (
    <Box
      sx={{
        width: '100%',
        maxWidth: '400px',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        border: `1px solid ${healthForesightColors.neutral.light}`,
        borderRadius: 2,
        p: 3,
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
        transform: revealed ? 'scaleX(1)' : 'scaleX(0.96)',
        opacity: revealed ? 1 : 0,
        transition: 'all 500ms cubic-bezier(0.2, 0.8, 0.2, 1)',
      }}
    >
      {rows.map((row, idx) => (
        <Box
          key={idx}
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            py: 1.5,
            borderBottom: idx < rows.length - 1 ? `1px solid ${healthForesightColors.neutral.light}` : 'none',
            opacity: revealed ? 1 : 0,
            transform: revealed ? 'translateX(0)' : 'translateX(-6px)',
            transition: `opacity 300ms ease ${80 * idx}ms, transform 300ms ease ${80 * idx}ms`,
          }}
        >
          <Typography
            sx={{
              fontSize: '13px',
              fontWeight: 600,
              color: healthForesightColors.neutral.mid,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            {row.label}:
          </Typography>
          <Typography
            sx={{
              fontSize: '14px',
              fontWeight: 500,
              color: healthForesightColors.neutral.dark,
            }}
          >
            {row.value}
          </Typography>
        </Box>
      ))}
    </Box>
  )
}

// Exclusion Panel Component
function ExclusionPanel() {
  const [visible, setVisible] = useState(false)
  const [borderHeight, setBorderHeight] = useState(0)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          setVisible(true)
          setTimeout(() => setBorderHeight(100), 80)
        }
      },
      { threshold: 0.2 }
    )

    const element = document.getElementById('exclusion-panel')
    if (element) observer.observe(element)

    return () => observer.disconnect()
  }, [])

  return (
    <Box
      id="exclusion-panel"
      sx={{
        position: 'relative',
        p: { xs: 4, md: 6 },
        borderRadius: 2,
        backgroundColor: healthForesightColors.neutral.background,
        border: `1px solid ${healthForesightColors.neutral.light}`,
        borderLeft: `4px solid ${healthForesightColors.neutral.mid}`,
        opacity: visible ? 1 : 0,
        transform: visible ? 'translateY(0)' : 'translateY(8px)',
        transition: 'opacity 320ms ease, transform 320ms ease',
      }}
    >
      <Box
        sx={{
          position: 'absolute',
          left: 0,
          top: 0,
          height: `${borderHeight}%`,
          width: '4px',
          backgroundColor: healthForesightColors.neutral.mid,
          transition: 'height 350ms ease 80ms',
        }}
      />
      <Box
        sx={{
          display: 'inline-block',
          px: 1.5,
          py: 0.5,
          mb: 2,
          backgroundColor: healthForesightColors.neutral.mid,
          color: '#FFFFFF',
          borderRadius: 1,
          fontSize: '11px',
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: '0.1em',
        }}
      >
        NOT A BI TOOL
      </Box>
      <Typography
        variant="h3"
        sx={{
          fontSize: { xs: '1.75rem', md: '2.25rem' },
          fontWeight: 700,
          mb: 3,
          color: healthForesightColors.neutral.mid,
        }}
      >
        Not built for dashboards-only reporting teams
      </Typography>
      <Typography
        variant="body1"
        sx={{
          fontSize: { xs: '16px', md: '17px' },
          color: healthForesightColors.neutral.dark,
          lineHeight: 1.75,
          mb: 3,
        }}
      >
        HealthForesight is not a BI tool, claims viewer, or static reporting layer. If your primary goal is retrospective reporting or operational monitoring, this is not the right platform.
      </Typography>
      <Box component="ul" sx={{ pl: 0, listStyle: 'none', m: 0 }}>
        {[
          'Not designed for operational dashboards',
          'Not a claims data viewer',
          'Not a retrospective reporting tool',
        ].map((item, idx) => (
          <Box
            key={idx}
            component="li"
            sx={{
              display: 'flex',
              alignItems: 'start',
              mb: 2,
              fontSize: { xs: '16px', md: '17px' },
              color: healthForesightColors.neutral.dark,
              lineHeight: 1.7,
            }}
          >
            <Box
              sx={{
                mr: 2,
                mt: 0.5,
                fontSize: '18px',
                fontWeight: 700,
                color: healthForesightColors.neutral.mid,
              }}
            >
              ×
            </Box>
            <Box>{item}</Box>
          </Box>
        ))}
      </Box>
      <Typography
        variant="h5"
        sx={{
          fontSize: { xs: '1.125rem', md: '1.25rem' },
          fontWeight: 600,
          color: healthForesightColors.neutral.dark,
          mt: 3,
        }}
      >
        It is built for policy intelligence — not reporting convenience.
      </Typography>
    </Box>
  )
}

// Responsibility Matrix Component
function ResponsibilityMatrix() {
  const [visibleRows, setVisibleRows] = useState<boolean[]>([])

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          const rows = [true, false, false, false, false]
          rows.forEach((_, idx) => {
            setTimeout(() => {
              setVisibleRows((prev) => {
                const newRows = [...prev]
                newRows[idx] = true
                return newRows
              })
            }, idx * 70)
          })
        }
      },
      { threshold: 0.2 }
    )

    const element = document.getElementById('responsibility-matrix')
    if (element) observer.observe(element)

    return () => observer.disconnect()
  }, [])

  const decisionOwners = [
    { role: 'Medical Policy Leaders', decision: 'What to approve, restrict, or revise', tag: 'Approval' },
    { role: 'Network Strategy Leaders', decision: 'Where care should occur — and at what risk', tag: 'Network' },
    { role: 'Utilization Management', decision: 'How rules change behavior and volume', tag: 'Policy Design' },
    { role: 'Value-Based Care Leaders', decision: 'Whether policy supports intended outcomes', tag: 'Outcomes' },
    { role: 'Actuarial & Finance', decision: 'Whether expected impact matches reality', tag: 'ROI Defense' },
  ]

  return (
    <Box id="responsibility-matrix">
      <Box
        sx={{
          backgroundColor: 'rgba(255, 255, 255, 0.05)',
          borderRadius: 3,
          border: `1px solid rgba(255, 255, 255, 0.1)`,
          overflow: 'hidden',
        }}
      >
        {decisionOwners.map((row, idx) => (
          <Box
            key={idx}
            sx={{
              display: 'flex',
              alignItems: 'center',
              p: 3,
              borderBottom: idx < decisionOwners.length - 1 ? `1px solid rgba(255, 255, 255, 0.1)` : 'none',
              backgroundColor: idx % 2 === 0 ? 'rgba(255, 255, 255, 0.02)' : 'transparent',
              position: 'relative',
              opacity: visibleRows[idx] ? 1 : 0,
              transform: visibleRows[idx] ? 'translateY(0)' : 'translateY(10px)',
              transition: 'opacity 260ms ease, transform 260ms ease',
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.08)',
                '&::before': {
                  width: '4px',
                },
              },
              '&::before': {
                content: '""',
                position: 'absolute',
                left: 0,
                top: 0,
                bottom: 0,
                width: '0px',
                backgroundColor: healthForesightColors.accent.main,
                transition: 'width 200ms ease',
              },
            }}
          >
            <Box sx={{ flex: 1, mr: 3 }}>
              <Typography
                sx={{
                  fontSize: { xs: '16px', md: '17px' },
                  fontWeight: 700,
                  color: '#FFFFFF',
                  mb: 1,
                }}
              >
                {row.role}
              </Typography>
              <Typography
                sx={{
                  fontSize: { xs: '15px', md: '16px' },
                  color: 'rgba(255, 255, 255, 0.9)',
                  lineHeight: 1.7,
                }}
              >
                {row.decision}
              </Typography>
            </Box>
            <Box
              sx={{
                px: 2,
                py: 0.75,
                backgroundColor: 'rgba(255, 255, 255, 0.15)',
                borderRadius: 1,
                border: `1px solid rgba(255, 255, 255, 0.2)`,
              }}
            >
              <Typography
                sx={{
                  fontSize: '12px',
                  fontWeight: 700,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                }}
              >
                {row.tag}
              </Typography>
            </Box>
          </Box>
        ))}
      </Box>
    </Box>
  )
}

// Task-to-Outcome Mapping Component
function TaskToOutcomeMapping() {
  const [visiblePairs, setVisiblePairs] = useState<boolean[]>([])

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          const pairs = [false, false, false, false]
          pairs.forEach((_, idx) => {
            setTimeout(() => {
              setVisiblePairs((prev) => {
                const newPairs = [...prev]
                newPairs[idx] = true
                return newPairs
              })
            }, idx * 90)
          })
        }
      },
      { threshold: 0.2 }
    )

    const element = document.getElementById('task-outcome-mapping')
    if (element) observer.observe(element)

    return () => observer.disconnect()
  }, [])

  const mappings = [
    { task: 'Draft policy language', outcome: 'Structured logic + scoped baseline' },
    { task: 'Assess expected impact', outcome: 'Pre-policy utilization and risk projections' },
    { task: 'Monitor rollout', outcome: 'Early divergence and lag detection' },
    { task: 'Explain results', outcome: 'Behavioral drivers, not just metrics' },
  ]

  return (
    <Box id="task-outcome-mapping">
      {mappings.map((mapping, idx) => (
        <Box
          key={idx}
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 2,
            mb: 3,
            opacity: visiblePairs[idx] ? 1 : 0,
            transform: visiblePairs[idx] ? 'translateX(0)' : (idx % 2 === 0 ? 'translateX(-10px)' : 'translateX(10px)'),
            transition: 'opacity 280ms ease, transform 280ms ease',
          }}
        >
          {/* Task Card */}
          <Box
            sx={{
              flex: 1,
              p: 2.5,
              backgroundColor: healthForesightColors.neutral.background,
              border: `1px solid ${healthForesightColors.neutral.light}`,
              borderRadius: 2,
              '&:hover': {
                borderColor: healthForesightColors.primary.main,
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
              },
              transition: 'all 200ms ease',
            }}
          >
            <Typography
              sx={{
                fontSize: { xs: '16px', md: '17px' },
                fontWeight: 600,
                color: healthForesightColors.neutral.dark,
              }}
            >
              {mapping.task}
            </Typography>
          </Box>

          {/* Arrow */}
          <Box
            sx={{
              fontSize: '24px',
              color: healthForesightColors.primary.main,
              fontWeight: 700,
              opacity: visiblePairs[idx] ? 1 : 0,
              transition: 'opacity 280ms ease',
            }}
          >
            →
          </Box>

          {/* Outcome Card */}
          <Box
            sx={{
              flex: 1,
              p: 2.5,
              backgroundColor: healthForesightColors.primary.main,
              borderRadius: 2,
              '&:hover': {
                backgroundColor: healthForesightColors.primary.light,
                boxShadow: '0 4px 12px rgba(59, 47, 143, 0.3)',
              },
              transition: 'all 200ms ease',
            }}
          >
            <Typography
              sx={{
                fontSize: { xs: '16px', md: '17px' },
                fontWeight: 600,
                color: '#FFFFFF',
              }}
            >
              {mapping.outcome}
            </Typography>
          </Box>
        </Box>
      ))}
    </Box>
  )
}

// Briefing Tile Component
function BriefingTile({
  title,
  decisionPressure,
  uses,
  outcomes,
  accentColor,
  delay = 0,
}: {
  title: string
  decisionPressure: string
  uses: string[]
  outcomes: string[]
  accentColor: string
  delay?: number
}) {
  const [visible, setVisible] = useState(false)
  const [panelVisible, setPanelVisible] = useState(false)
  const [highlightedOutcome, setHighlightedOutcome] = useState(-1)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          setVisible(true)
          setTimeout(() => setPanelVisible(true), 120)
          // Highlight outcomes one by one
          outcomes.forEach((_, idx) => {
            setTimeout(() => {
              setHighlightedOutcome(idx)
              setTimeout(() => setHighlightedOutcome(-1), 1000)
            }, 2000 + idx * 500)
          })
        }
      },
      { threshold: 0.2 }
    )

    const element = document.getElementById(`briefing-tile-${title.replace(/\s+/g, '-')}`)
    if (element) observer.observe(element)

    return () => observer.disconnect()
  }, [title, outcomes])

  return (
    <Box
      id={`briefing-tile-${title.replace(/\s+/g, '-')}`}
      sx={{
        p: 4,
        backgroundColor: 'rgba(255, 255, 255, 0.05)',
        border: `1px solid rgba(255, 255, 255, 0.1)`,
        borderRadius: 3,
        mb: 4,
        opacity: visible ? 1 : 0,
        transform: visible ? 'translateY(0)' : 'translateY(12px)',
        transition: 'opacity 360ms ease, transform 360ms ease',
        '&:hover': {
          '& .outcome-panel': {
            transform: 'scale(1.02)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.2)',
          },
        },
      }}
    >
      <Typography
        variant="h3"
        sx={{
          fontSize: { xs: '1.75rem', md: '2rem' },
          fontWeight: 700,
          color: '#FFFFFF',
          mb: 2,
        }}
      >
        {title}
      </Typography>
      <Typography
        variant="body1"
        sx={{
          fontSize: { xs: '16px', md: '17px' },
          color: 'rgba(255, 255, 255, 0.9)',
          lineHeight: 1.75,
          mb: 3,
          fontStyle: 'italic',
        }}
      >
        {decisionPressure}
      </Typography>
      <Box component="ul" sx={{ pl: 0, listStyle: 'none', mb: 3 }}>
        {uses.map((use, idx) => (
          <Box
            key={idx}
            component="li"
            sx={{
              mb: 2,
              pl: 3,
              position: 'relative',
              fontSize: { xs: '16px', md: '17px' },
              color: 'rgba(255, 255, 255, 0.9)',
              lineHeight: 1.7,
              '&::before': {
                content: '"→"',
                position: 'absolute',
                left: 0,
                color: healthForesightColors.accent.main,
                fontWeight: 700,
                fontSize: '18px',
              },
            }}
          >
            {use}
          </Box>
        ))}
      </Box>
      <Box
        className="outcome-panel"
        sx={{
          mt: 3,
          p: 2.5,
          backgroundColor: 'rgba(255, 255, 255, 0.1)',
          border: `1px solid rgba(255, 255, 255, 0.15)`,
          borderRadius: 2,
          opacity: panelVisible ? 1 : 0,
          transition: 'opacity 300ms ease 120ms, transform 200ms ease, box-shadow 200ms ease',
        }}
      >
        <Typography
          sx={{
            fontSize: '12px',
            fontWeight: 700,
            color: 'rgba(255, 255, 255, 0.8)',
            textTransform: 'uppercase',
            letterSpacing: '0.1em',
            mb: 1.5,
          }}
        >
          Typical Outcomes
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          {outcomes.map((outcome, idx) => (
            <Box
              key={idx}
              sx={{
                px: 1.5,
                py: 0.75,
                backgroundColor: highlightedOutcome === idx ? accentColor : 'rgba(255, 255, 255, 0.15)',
                borderRadius: 1,
                transition: 'background-color 300ms ease',
              }}
            >
              <Typography
                sx={{
                  fontSize: '13px',
                  fontWeight: 600,
                  color: '#FFFFFF',
                }}
              >
                {outcome}
              </Typography>
            </Box>
          ))}
        </Box>
      </Box>
    </Box>
  )
}

export default function WhoItsForPage() {
  const navigate = useNavigate()

  return (
    <Box>
      {/* Hero - Light */}
      <Box
        sx={{
          position: 'relative',
          background: `linear-gradient(135deg, ${healthForesightColors.neutral.background} 0%, #FFFFFF 30%, ${healthForesightColors.primary.main}02 100%)`,
          pt: { xs: 10, md: 14 },
          pb: { xs: 8, md: 10 },
          borderBottom: `1px solid ${healthForesightColors.neutral.light}`,
          overflow: 'hidden',
        }}
      >
        <Container maxWidth="xl" sx={{ position: 'relative', zIndex: 1 }}>
          <Box sx={{ display: 'flex', flexDirection: { xs: 'column', lg: 'row' }, gap: 6, alignItems: 'flex-start' }}>
            <Box sx={{ flex: 1 }}>
              <ScrollReveal delay={0}>
                <Typography
                  variant="h1"
                  sx={{
                    fontSize: { xs: '2.75rem', md: '4rem' },
                    fontWeight: 700,
                    mb: 3,
                    color: healthForesightColors.neutral.dark,
                    lineHeight: 1.1,
                    letterSpacing: '-0.02em',
                  }}
                >
                  Built for decision-makers accountable for policy outcomes
                </Typography>
                <Typography
                  variant="h5"
                  sx={{
                    fontSize: { xs: '1.1rem', md: '1.25rem' },
                    fontWeight: 400,
                    color: healthForesightColors.neutral.dark,
                    mb: 5,
                    lineHeight: 1.6,
                  }}
                >
                  HealthForesight is for teams who design, approve, and defend healthcare policy — and need to understand impact before and after decisions are made.
                </Typography>
              </ScrollReveal>
            </Box>
            <Box sx={{ flex: { xs: 1, lg: '0 0 auto' } }}>
              <DecisionLedger />
            </Box>
          </Box>
        </Container>
      </Box>

      {/* Section 1: Not for - Light */}
      <Box
        sx={{
          position: 'relative',
          py: { xs: 10, md: 14 },
          backgroundColor: '#FFFFFF',
          overflow: 'hidden',
        }}
      >
        <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
          <ExclusionPanel />
        </Container>
      </Box>

      {/* Section 2: Primary Audience - Dark */}
      <Box
        sx={{
          position: 'relative',
          py: { xs: 10, md: 14 },
          backgroundColor: healthForesightColors.neutral.dark,
          color: '#FFFFFF',
          overflow: 'hidden',
        }}
      >
        <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
          <ScrollReveal delay={200}>
            <Typography
              variant="h2"
              sx={{
                fontSize: { xs: '2.25rem', md: '3rem' },
                fontWeight: 700,
                mb: 6,
                color: '#FFFFFF',
                lineHeight: 1.2,
                letterSpacing: '-0.01em',
                textAlign: 'center',
              }}
            >
              Built for teams who own policy decisions
            </Typography>
          </ScrollReveal>
          <ResponsibilityMatrix />
          <ScrollReveal delay={600}>
            <Typography
              variant="body1"
              sx={{
                fontSize: { xs: '16px', md: '17px' },
                color: 'rgba(255, 255, 255, 0.9)',
                lineHeight: 1.75,
                textAlign: 'center',
                fontStyle: 'italic',
                fontWeight: 500,
                mt: 4,
              }}
            >
              These teams don't ask "what happened?" — they ask "what will happen if we do this?"
            </Typography>
          </ScrollReveal>
        </Container>
      </Box>

      {/* Section 3: Secondary Audience - Light */}
      <Box
        sx={{
          position: 'relative',
          py: { xs: 10, md: 14 },
          backgroundColor: '#FFFFFF',
          overflow: 'hidden',
        }}
      >
        <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
          <ScrollReveal delay={200}>
            <Typography
              variant="h2"
              sx={{
                fontSize: { xs: '2.25rem', md: '3rem' },
                fontWeight: 700,
                mb: 6,
                color: healthForesightColors.neutral.dark,
                lineHeight: 1.2,
                letterSpacing: '-0.01em',
                textAlign: 'center',
              }}
            >
              Also used by teams who operationalize policy
            </Typography>
          </ScrollReveal>
          <TaskToOutcomeMapping />
          <ScrollReveal delay={600}>
            <Typography
              variant="body1"
              sx={{
                fontSize: { xs: '16px', md: '17px' },
                color: healthForesightColors.neutral.dark,
                lineHeight: 1.75,
                textAlign: 'center',
                fontStyle: 'italic',
                fontWeight: 500,
                mt: 4,
              }}
            >
              The platform connects intent to execution to outcome.
            </Typography>
          </ScrollReveal>
        </Container>
      </Box>

      {/* Section 4: Industry Segments - Dark */}
      <Box
        sx={{
          position: 'relative',
          py: { xs: 10, md: 14 },
          backgroundColor: healthForesightColors.neutral.dark,
          color: '#FFFFFF',
          overflow: 'hidden',
        }}
      >
        <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
          <ScrollReveal delay={200}>
            <Typography
              variant="h2"
              sx={{
                fontSize: { xs: '2.25rem', md: '3rem' },
                fontWeight: 700,
                mb: 6,
                color: '#FFFFFF',
                lineHeight: 1.2,
                letterSpacing: '-0.01em',
                textAlign: 'center',
              }}
            >
              Industry segments
            </Typography>
          </ScrollReveal>

          <BriefingTile
            title="Health Plans & Payers"
            decisionPressure="When policy risk translates directly into financial risk"
            uses={[
              'Forecast utilization shifts',
              'Manage network leakage',
              'Defend policy decisions with evidence',
            ]}
            outcomes={['Leakage ↓', 'Predictability ↑', 'Defensibility ↑']}
            accentColor={healthForesightColors.primary.main}
            delay={100}
          />

          <BriefingTile
            title="Risk-Bearing Providers & ACOs"
            decisionPressure="When utilization decisions affect performance and margin"
            uses={[
              'Understand downstream behavior',
              'Align policy with clinical operations',
              'Anticipate unintended shifts',
            ]}
            outcomes={['Performance ↑', 'Margin ↑', 'Alignment ↑']}
            accentColor={healthForesightColors.accent.main}
            delay={200}
          />

          <BriefingTile
            title="Life Sciences & Market Access"
            decisionPressure="When policy interpretation determines access"
            uses={[
              'Assess how coverage decisions affect real-world utilization',
              'Understand substitution and site-of-care dynamics',
              'Support value narratives with evidence',
            ]}
            outcomes={['Access ↑', 'Evidence ↑', 'Value ↑']}
            accentColor={healthForesightColors.amber.main}
            delay={300}
          />
        </Container>
      </Box>

      {/* Closing CTA - Light */}
      <Box
        sx={{
          position: 'relative',
          py: { xs: 8, md: 10 },
          backgroundColor: '#FFFFFF',
          overflow: 'hidden',
        }}
      >
        <Container maxWidth="md" sx={{ position: 'relative', zIndex: 1 }}>
          <Box
            sx={{
              borderTop: `1px solid ${healthForesightColors.neutral.light}`,
              pt: 6,
            }}
          >
            <ScrollReveal delay={200}>
              <Typography
                variant="h3"
                sx={{
                  fontSize: { xs: '1.75rem', md: '2.25rem' },
                  fontWeight: 700,
                  textAlign: 'center',
                  color: healthForesightColors.neutral.dark,
                  lineHeight: 1.3,
                  mb: 4,
                }}
              >
                If you are accountable for policy outcomes — not just reporting results — HealthForesight is built for you.
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap', mb: 3 }}>
                <Button
                  variant="contained"
                  size="large"
                  onClick={() => navigate('/request-demo')}
                  sx={{
                    minHeight: 44,
                    px: { xs: 3, md: 4 },
                    py: { xs: 1.5, md: 1.5 },
                    fontSize: { xs: '14px', md: '16px' },
                    fontWeight: 600,
                    backgroundColor: healthForesightColors.primary.main,
                    '&:hover': {
                      backgroundColor: healthForesightColors.primary.light,
                      transform: 'translateY(-2px)',
                      boxShadow: '0 4px 12px rgba(59, 47, 143, 0.3)',
                    },
                    transition: 'all 200ms ease',
                  }}
                >
                  Request Demo
                </Button>
                <Button
                  variant="outlined"
                  size="large"
                  onClick={() => navigate('/platform')}
                  sx={{
                    minHeight: 44,
                    px: { xs: 3, md: 4 },
                    py: { xs: 1.5, md: 1.5 },
                    fontSize: { xs: '14px', md: '16px' },
                    fontWeight: 600,
                    borderColor: healthForesightColors.primary.main,
                    color: healthForesightColors.primary.main,
                    '&:hover': {
                      borderColor: healthForesightColors.primary.light,
                      backgroundColor: `${healthForesightColors.primary.main}08`,
                      transform: 'translateY(-2px)',
                    },
                    transition: 'all 200ms ease',
                  }}
                >
                  See Platform
                </Button>
              </Box>
              <Typography
                variant="body2"
                sx={{
                  fontSize: '14px',
                  color: healthForesightColors.neutral.mid,
                  textAlign: 'center',
                }}
              >
                If your team owns policy outcomes, we'll show you the difference in 15 minutes.
              </Typography>
            </ScrollReveal>
          </Box>
        </Container>
      </Box>
    </Box>
  )
}
