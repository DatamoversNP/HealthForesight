/**
 * Home Page - Decision Narrative
 * Calm, enterprise, inevitable motion language
 * One-time explanatory animations, no card repetition
 */
import React from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Container,
  Typography,
  Button,
  Grid,
} from '@mui/material'
import { CheckCircle } from '@mui/icons-material'
import { healthForesightColors } from '../theme/healthForesightTheme'
import VisualPattern from '../components/VisualPattern'
import ScrollReveal from '../components/ScrollReveal'
import DecisionFieldVisual from '../components/DecisionFieldVisual'
import ReportingVsGoverningVisual from '../components/ReportingVsGoverningVisual'
import FogToClarityVisual from '../components/FogToClarityVisual'
import CategoryBadgeVisual from '../components/CategoryBadgeVisual'
import ProgressRailVisual from '../components/ProgressRailVisual'
import BaselineStabilizationVisual from '../components/BaselineStabilizationVisual'
import ForecastBandVisual from '../components/ForecastBandVisual'
import ExpectedVsObservedVisual from '../components/ExpectedVsObservedVisual'
import BehavioralShiftVisual from '../components/BehavioralShiftVisual'
import LoopTighteningVisual from '../components/LoopTighteningVisual'

export default function HomePage() {
  const navigate = useNavigate()

  const outcomes = [
    'Better policy decisions',
    'Fewer unintended consequences',
    'Improved financial predictability',
    'Stronger leadership confidence',
    'Institutional learning — not one-off analysis',
  ]

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
        <VisualPattern variant="dots" opacity={0.1} />
        <DecisionFieldVisual />
        <Container maxWidth="xl" sx={{ position: 'relative', zIndex: 1 }}>
          <ScrollReveal delay={200}>
            <Typography
              variant="h1"
              sx={{
                fontSize: { xs: '2.75rem', md: '4rem' },
                fontWeight: 700,
                mb: 3,
                textAlign: 'center',
                color: healthForesightColors.neutral.dark,
                lineHeight: 1.1,
                letterSpacing: '-0.02em',
              }}
            >
              Utilization policy decisions shape outcomes.
            </Typography>
            <Typography
              variant="h3"
              sx={{
                fontSize: { xs: '1.5rem', md: '2rem' },
                fontWeight: 400,
                mb: 4,
                textAlign: 'center',
                color: healthForesightColors.neutral.mid,
                lineHeight: 1.3,
              }}
            >
              Yet most organizations still make them without knowing what will happen next.
            </Typography>
            <Typography
              variant="h5"
              sx={{
                fontSize: { xs: '1.1rem', md: '1.25rem' },
                fontWeight: 400,
                textAlign: 'center',
                color: healthForesightColors.neutral.dark,
                maxWidth: '900px',
                mx: 'auto',
                mb: 5,
                lineHeight: 1.6,
              }}
            >
              HealthForesight is an enterprise policy impact intelligence platform that makes utilization policy outcomes predictable before implementation and measurable after implementation — with continuous learning over time.
            </Typography>
            <Typography
              variant="body1"
              sx={{
                fontSize: { xs: '0.95rem', md: '1rem' },
                textAlign: 'center',
                color: healthForesightColors.neutral.mid,
                mb: 5,
              }}
            >
              Built specifically for healthcare payers managing complex utilization controls at scale.
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
              <Button
                variant="contained"
                size="large"
                onClick={() => navigate('/platform')}
                sx={{
                  px: { xs: 4, md: 5 },
                  py: { xs: 1.5, md: 1.75 },
                  fontSize: { xs: '14px', md: '16px' },
                  fontWeight: 600,
                  minHeight: 44,
                  backgroundColor: healthForesightColors.primary.main,
                  '&:hover': {
                    backgroundColor: healthForesightColors.primary.dark,
                  },
                }}
              >
                Explore the Platform
              </Button>
              <Button
                variant="outlined"
                size="large"
                onClick={() => navigate('/how-it-works')}
                sx={{
                  px: { xs: 4, md: 5 },
                  py: { xs: 1.5, md: 1.75 },
                  fontSize: { xs: '14px', md: '16px' },
                  fontWeight: 600,
                  minHeight: 44,
                }}
              >
                See How It Works
              </Button>
            </Box>
          </ScrollReveal>
        </Container>
      </Box>

      {/* Section 2: Reframe the Problem - Dark */}
      <Box
        sx={{
          position: 'relative',
          py: { xs: 10, md: 14 },
          backgroundColor: healthForesightColors.neutral.dark,
          color: '#FFFFFF',
          overflow: 'hidden',
        }}
      >
        <VisualPattern variant="grid" opacity={0.05} />
        <Container maxWidth="xl" sx={{ position: 'relative', zIndex: 1 }}>
          <Grid container spacing={8} sx={{ alignItems: 'center' }}>
            <Grid item xs={12} md={6}>
              <ScrollReveal delay={100}>
                <Typography
                  variant="h2"
                  sx={{
                    fontSize: { xs: '2.25rem', md: '3rem' },
                    fontWeight: 700,
                    mb: 4,
                    color: '#FFFFFF',
                    lineHeight: 1.2,
                    letterSpacing: '-0.01em',
                  }}
                >
                  This is not analytics. This is policy impact intelligence.
                </Typography>
                <Typography
                  variant="body1"
                  sx={{
                    fontSize: { xs: '16px', md: '17px' },
                    color: '#FFFFFF',
                    lineHeight: 1.7,
                    mb: 3,
                  }}
                >
                  Traditional analytics platforms focus on reporting utilization and cost after the fact. They explain what happened — but not why it happened or what should have happened instead.
                </Typography>
                <Typography
                  variant="body1"
                  sx={{
                    fontSize: { xs: '16px', md: '17px' },
                    color: '#FFFFFF',
                    lineHeight: 1.7,
                    mb: 4,
                  }}
                >
                  Utilization policies, however, are decisions. They are designed to influence behavior, redirect care, control spend, and protect access. HealthForesight is designed around those decisions — not just the data they generate.
                </Typography>
                <Typography
                  variant="h5"
                  sx={{
                    fontSize: { xs: '1.125rem', md: '1.25rem' },
                    fontWeight: 600,
                    mb: 2,
                    color: '#FFFFFF',
                  }}
                >
                  HealthForesight answers questions traditional systems cannot:
                </Typography>
                <Box component="ul" sx={{ pl: 0, listStyle: 'none', mb: 4 }}>
                  {[
                    'What is this policy expected to do before we roll it out?',
                    'What actually happened because of the policy?',
                    'How did providers and patients respond?',
                    'What should we do differently next time?',
                  ].map((question, idx) => (
                    <Box
                      key={idx}
                      component="li"
                      sx={{
                        mb: 2.5,
                        pl: 3,
                        position: 'relative',
                        fontSize: { xs: '16px', md: '17px' },
                        color: '#FFFFFF',
                        lineHeight: 1.7,
                        '&::before': {
                          content: '"→"',
                          position: 'absolute',
                          left: 0,
                          color: healthForesightColors.accent.main,
                          fontWeight: 700,
                          fontSize: '20px',
                        },
                      }}
                    >
                      {question}
                    </Box>
                  ))}
                </Box>
                <Typography
                  variant="h5"
                  sx={{
                    fontSize: { xs: '1.125rem', md: '1.25rem' },
                    fontWeight: 600,
                    color: healthForesightColors.accent.main,
                  }}
                >
                  This is the difference between reporting utilization and governing utilization.
                </Typography>
              </ScrollReveal>
            </Grid>
            <Grid item xs={12} md={6}>
              <ScrollReveal delay={300}>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <ReportingVsGoverningVisual />
                </Box>
              </ScrollReveal>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Section 3: Industry Reality - Light */}
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
                mb: 4,
                textAlign: 'center',
                color: healthForesightColors.neutral.dark,
                lineHeight: 1.2,
                letterSpacing: '-0.01em',
              }}
            >
              Utilization policy outcomes are inherently uncertain — unless measured correctly
            </Typography>
            <Typography
              variant="body1"
              sx={{
                fontSize: { xs: '16px', md: '17px' },
                color: healthForesightColors.neutral.dark,
                lineHeight: 1.7,
                mb: 3,
                textAlign: 'center',
                maxWidth: '800px',
                mx: 'auto',
              }}
            >
              Payers deploy utilization controls to influence behavior — not simply to count claims.
            </Typography>
            <Typography
              variant="h5"
              sx={{
                fontSize: { xs: '1.125rem', md: '1.25rem' },
                fontWeight: 600,
                mb: 3,
                color: healthForesightColors.neutral.dark,
              }}
            >
              Yet in practice:
            </Typography>
            <Box component="ul" sx={{ pl: 0, listStyle: 'none', mb: 5, maxWidth: '700px', mx: 'auto' }}>
              {[
                'Policies are approved with limited forward insight',
                'Expected savings are directional, not quantified',
                'Post-implementation analysis is slow and inconclusive',
                'Substitution and leakage obscure true outcomes',
                'Provider and patient responses are poorly understood',
                'Learnings are rarely reused across policy cycles',
              ].map((item, idx) => (
                <ScrollReveal key={idx} delay={100 + idx * 100} stagger={idx * 100}>
                  <Box
                    component="li"
                    sx={{
                      mb: 2,
                      pl: 3,
                      position: 'relative',
                      fontSize: { xs: '16px', md: '17px' },
                      color: healthForesightColors.neutral.dark,
                      lineHeight: 1.7,
                      '&::before': {
                        content: '"-"',
                        position: 'absolute',
                        left: 0,
                        color: healthForesightColors.amber.main,
                        fontWeight: 700,
                        fontSize: '18px',
                      },
                    }}
                  >
                    {item}
                  </Box>
                </ScrollReveal>
              ))}
            </Box>
            <Typography
              variant="body1"
              sx={{
                fontSize: { xs: '16px', md: '17px' },
                color: healthForesightColors.neutral.dark,
                lineHeight: 1.7,
                mb: 3,
                textAlign: 'center',
                maxWidth: '800px',
                mx: 'auto',
              }}
            >
              As a result, utilization policy remains one of the least predictable levers in healthcare cost management.
            </Typography>
            <Typography
              variant="h4"
              sx={{
                fontSize: { xs: '1.5rem', md: '2rem' },
                fontWeight: 700,
                textAlign: 'center',
                color: healthForesightColors.primary.main,
              }}
            >
              HealthForesight was built to change that.
            </Typography>
          </ScrollReveal>
          <Box
            sx={{
              mt: 6,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <FogToClarityVisual />
          </Box>
        </Container>
      </Box>

      {/* Section 4: Introduce the Category - Dark */}
      <Box
        sx={{
          position: 'relative',
          py: { xs: 10, md: 14 },
          backgroundColor: healthForesightColors.neutral.dark,
          color: '#FFFFFF',
          overflow: 'hidden',
        }}
      >
        <VisualPattern variant="grid" opacity={0.05} />
        <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
          <ScrollReveal delay={200}>
            <Typography
              variant="h2"
              sx={{
                fontSize: { xs: '2.25rem', md: '3rem' },
                fontWeight: 700,
                mb: 4,
                textAlign: 'center',
                color: '#FFFFFF',
                lineHeight: 1.2,
                letterSpacing: '-0.01em',
              }}
            >
              A new decision category for healthcare payers
            </Typography>
            <Typography
              variant="body1"
              sx={{
                fontSize: { xs: '16px', md: '17px' },
                color: 'rgba(255, 255, 255, 0.9)',
                lineHeight: 1.7,
                mb: 4,
                textAlign: 'center',
                maxWidth: '800px',
                mx: 'auto',
              }}
            >
              HealthForesight introduces policy impact intelligence — a purpose-built category focused on understanding how utilization policies actually work in the real world.
            </Typography>
            <Typography
              variant="body1"
              sx={{
                fontSize: { xs: '16px', md: '17px' },
                color: 'rgba(255, 255, 255, 0.9)',
                lineHeight: 1.7,
                mb: 4,
                textAlign: 'center',
                maxWidth: '800px',
                mx: 'auto',
              }}
            >
              The platform treats every utilization policy as a structured, analyzable decision with: a defined scope, expected behavioral effects, measurable outcomes, and learnings that compound over time.
            </Typography>
            <Typography
              variant="h5"
              sx={{
                fontSize: { xs: '1.125rem', md: '1.25rem' },
                fontWeight: 600,
                textAlign: 'center',
                color: healthForesightColors.accent.main,
                maxWidth: '800px',
                mx: 'auto',
              }}
            >
              This allows organizations to move from assumption-driven policy design to evidence-driven policy governance.
            </Typography>
          </ScrollReveal>
          <Box
            sx={{
              mt: 6,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <CategoryBadgeVisual />
          </Box>
        </Container>
      </Box>

      {/* Section 5: How It Works - Light */}
      <Box
        sx={{
          position: 'relative',
          py: { xs: 10, md: 14 },
          backgroundColor: '#FFFFFF',
          overflow: 'hidden',
        }}
      >
        <Container maxWidth="xl" sx={{ position: 'relative', zIndex: 1 }}>
          <ScrollReveal delay={200}>
            <Typography
              variant="h2"
              sx={{
                fontSize: { xs: '2.25rem', md: '3rem' },
                fontWeight: 700,
                mb: 4,
                textAlign: 'center',
                color: healthForesightColors.neutral.dark,
                lineHeight: 1.2,
                letterSpacing: '-0.01em',
              }}
            >
              From policy design to measurable outcomes — and back again
            </Typography>
            <Grid container spacing={4} sx={{ mb: 6 }}>
              {[
                { label: 'Define', verb: 'Structure policies precisely — who they apply to, where they apply, how they operate, and what they exclude.' },
                { label: 'Predict', verb: 'Estimate expected utilization and cost impact before implementation based on historical behavior and learned elasticity patterns.' },
                { label: 'Observe', verb: 'Measure what actually happened after the policy goes live — isolating true policy effects from background trends.' },
                { label: 'Learn', verb: 'Capture behavioral insights and outcomes to improve future policy decisions.' },
              ].map((step, idx) => (
                <Grid item xs={12} sm={6} md={3} key={idx}>
                  <ScrollReveal delay={100 + idx * 80} stagger={idx * 80}>
                    <Box
                      sx={{
                        p: 3,
                        borderRadius: 2,
                        backgroundColor: healthForesightColors.neutral.background,
                        border: `1px solid ${healthForesightColors.neutral.light}`,
                        height: '100%',
                        '&:hover': {
                          borderColor: healthForesightColors.primary.main + '40',
                          boxShadow: `0 4px 16px ${healthForesightColors.primary.main}15`,
                        },
                        transition: 'all 0.3s ease',
                      }}
                    >
                      <Typography
                        variant="h5"
                        sx={{
                          fontSize: '1.25rem',
                          fontWeight: 700,
                          mb: 2,
                          color: healthForesightColors.primary.main,
                        }}
                      >
                        {step.label}
                      </Typography>
                      <Typography
                        variant="body2"
                        sx={{
                          fontSize: '14px',
                          color: healthForesightColors.neutral.dark,
                          lineHeight: 1.7,
                        }}
                      >
                        {step.verb}
                      </Typography>
                    </Box>
                  </ScrollReveal>
                </Grid>
              ))}
            </Grid>
            <Typography
              variant="body1"
              sx={{
                fontSize: { xs: '16px', md: '17px' },
                color: healthForesightColors.neutral.dark,
                lineHeight: 1.7,
                textAlign: 'center',
                maxWidth: '800px',
                mx: 'auto',
              }}
            >
              This closed loop turns utilization management into a learning system, not a one-off exercise.
            </Typography>
          </ScrollReveal>
          <Box
            sx={{
              mt: 6,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <ProgressRailVisual />
          </Box>
        </Container>
      </Box>

      {/* Section 6: Baselines & Measurement - Dark */}
      <Box
        sx={{
          position: 'relative',
          py: { xs: 10, md: 14 },
          backgroundColor: healthForesightColors.neutral.dark,
          color: '#FFFFFF',
          overflow: 'hidden',
        }}
      >
        <VisualPattern variant="grid" opacity={0.05} />
        <Container maxWidth="xl" sx={{ position: 'relative', zIndex: 1 }}>
          <Grid container spacing={8} sx={{ alignItems: 'center' }}>
            <Grid item xs={12} md={6}>
              <ScrollReveal delay={100}>
                <Typography
                  variant="h2"
                  sx={{
                    fontSize: { xs: '2.25rem', md: '3rem' },
                    fontWeight: 700,
                    mb: 4,
                    color: '#FFFFFF',
                    lineHeight: 1.2,
                    letterSpacing: '-0.01em',
                  }}
                >
                  Impact can only be measured against the right baseline
                </Typography>
                <Typography
                  variant="body1"
                  sx={{
                    fontSize: { xs: '16px', md: '17px' },
                    color: '#FFFFFF',
                    lineHeight: 1.7,
                    mb: 3,
                  }}
                >
                  HealthForesight establishes policy-specific baselines that reflect what utilization and cost looked like before a policy existed.
                </Typography>
                <Typography
                  variant="h5"
                  sx={{
                    fontSize: { xs: '1.125rem', md: '1.25rem' },
                    fontWeight: 600,
                    mb: 2,
                    color: '#FFFFFF',
                  }}
                >
                  Baselines are:
                </Typography>
                <Box component="ul" sx={{ pl: 0, listStyle: 'none', mb: 4 }}>
                  {[
                    'scoped precisely to the policy definition',
                    'derived from recent pre-policy data',
                    'aware of trend and seasonality',
                    'consistent across prediction and measurement',
                  ].map((item, idx) => (
                    <Box
                      key={idx}
                      component="li"
                      sx={{
                        mb: 2,
                        pl: 3,
                        position: 'relative',
                        fontSize: { xs: '16px', md: '17px' },
                        color: '#FFFFFF',
                        lineHeight: 1.7,
                        '&::before': {
                          content: '"✓"',
                          position: 'absolute',
                          left: 0,
                          color: healthForesightColors.accent.main,
                          fontWeight: 700,
                        },
                      }}
                    >
                      {item}
                    </Box>
                  ))}
                </Box>
                <Typography
                  variant="body1"
                  sx={{
                    fontSize: { xs: '16px', md: '17px' },
                    color: '#FFFFFF',
                    lineHeight: 1.7,
                    fontStyle: 'italic',
                    fontWeight: 500,
                  }}
                >
                  Instead of broad averages, the platform answers: "What would have happened if this policy had not been introduced?"
                </Typography>
              </ScrollReveal>
            </Grid>
            <Grid item xs={12} md={6}>
              <ScrollReveal delay={300}>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <BaselineStabilizationVisual />
                </Box>
              </ScrollReveal>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Section 7: Expected Impact - Light */}
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
                mb: 4,
                textAlign: 'center',
                color: healthForesightColors.neutral.dark,
                lineHeight: 1.2,
                letterSpacing: '-0.01em',
              }}
            >
              See what a policy is likely to do — before it creates consequences
            </Typography>
            <Grid container spacing={3} sx={{ mb: 4 }}>
              {[
                'projected utilization change',
                'projected cost impact (PMPM and total)',
                'early signals of substitution and leakage',
                'confidence indicators and limitations',
              ].map((item, idx) => (
                <Grid item xs={12} sm={6} key={idx}>
                  <Box
                    sx={{
                      p: 3,
                      borderRadius: 2,
                      backgroundColor: healthForesightColors.accent.main + '08',
                      border: `1px solid ${healthForesightColors.accent.main}20`,
                    }}
                  >
                    <Typography
                      variant="body1"
                      sx={{
                        fontSize: '15px',
                        color: healthForesightColors.neutral.dark,
                        lineHeight: 1.7,
                      }}
                    >
                      {item}
                    </Typography>
                  </Box>
                </Grid>
              ))}
            </Grid>
            <Typography
              variant="body1"
              sx={{
                fontSize: { xs: '16px', md: '17px' },
                color: healthForesightColors.neutral.dark,
                lineHeight: 1.7,
                mb: 4,
                textAlign: 'center',
                maxWidth: '800px',
                mx: 'auto',
              }}
            >
              Predictions are transparent, bounded, and explicitly labeled as expectations — not guarantees.
            </Typography>
            <Box
              sx={{
                p: 4,
                borderRadius: 3,
                backgroundColor: healthForesightColors.accent.main + '10',
                border: `1px solid ${healthForesightColors.accent.main}30`,
                maxWidth: '800px',
                mx: 'auto',
                mb: 6,
              }}
            >
              <Typography
                variant="h6"
                sx={{
                  fontSize: '1rem',
                  fontWeight: 700,
                  mb: 2,
                  color: healthForesightColors.accent.main,
                }}
              >
                Why this matters
              </Typography>
              <Typography
                variant="body1"
                sx={{
                  fontSize: { xs: '16px', md: '17px' },
                  color: healthForesightColors.neutral.dark,
                  lineHeight: 1.7,
                }}
              >
                Leaders can challenge assumptions, adjust scope, or reconsider design before consequences occur.
              </Typography>
            </Box>
          </ScrollReveal>
          <Box
            sx={{
              mt: 6,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <ForecastBandVisual />
          </Box>
        </Container>
      </Box>

      {/* Section 8: Observed Impact - Dark */}
      <Box
        sx={{
          position: 'relative',
          py: { xs: 10, md: 14 },
          backgroundColor: healthForesightColors.neutral.dark,
          color: '#FFFFFF',
          overflow: 'hidden',
        }}
      >
        <VisualPattern variant="grid" opacity={0.05} />
        <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
          <ScrollReveal delay={200}>
            <Typography
              variant="h2"
              sx={{
                fontSize: { xs: '2.25rem', md: '3rem' },
                fontWeight: 700,
                mb: 4,
                textAlign: 'center',
                color: '#FFFFFF',
                lineHeight: 1.2,
                letterSpacing: '-0.01em',
              }}
            >
              Understand what actually happened — and why
            </Typography>
            <Typography
              variant="body1"
              sx={{
                fontSize: { xs: '16px', md: '17px' },
                color: 'rgba(255, 255, 255, 0.9)',
                lineHeight: 1.7,
                mb: 3,
                textAlign: 'center',
                maxWidth: '800px',
                mx: 'auto',
              }}
            >
              Once a policy is live and data accrues, HealthForesight measures observed impact.
            </Typography>
            <Grid container spacing={3} sx={{ mb: 4 }}>
              {[
                'isolates policy effects from background trends',
                'quantifies utilization and cost changes attributable to the policy',
                'detects substitution, spillover, and leakage',
                'explains outcomes through provider and patient behavior patterns',
              ].map((item, idx) => (
                <Grid item xs={12} sm={6} key={idx}>
                  <Box
                    sx={{
                      p: 3,
                      borderRadius: 2,
                      backgroundColor: 'rgba(255, 255, 255, 0.05)',
                      border: `1px solid rgba(255, 255, 255, 0.1)`,
                    }}
                  >
                    <Typography
                      variant="body1"
                      sx={{
                        fontSize: '15px',
                        color: '#FFFFFF',
                        lineHeight: 1.7,
                      }}
                    >
                      {item}
                    </Typography>
                  </Box>
                </Grid>
              ))}
            </Grid>
            <Typography
              variant="body1"
              sx={{
                fontSize: { xs: '16px', md: '17px' },
                color: 'rgba(255, 255, 255, 0.9)',
                lineHeight: 1.7,
                textAlign: 'center',
                maxWidth: '800px',
                mx: 'auto',
              }}
            >
              Observed results are compared directly against both baseline and expected impact.
            </Typography>
          </ScrollReveal>
          <Box
            sx={{
              mt: 6,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <ExpectedVsObservedVisual />
          </Box>
        </Container>
      </Box>

      {/* Section 9: Behavioral Intelligence - Light */}
      <Box
        sx={{
          position: 'relative',
          py: { xs: 10, md: 14 },
          backgroundColor: '#FFFFFF',
          overflow: 'hidden',
        }}
      >
        <Container maxWidth="xl" sx={{ position: 'relative', zIndex: 1 }}>
          <Grid container spacing={8} sx={{ alignItems: 'center' }}>
            <Grid item xs={12} md={6}>
              <ScrollReveal delay={100}>
                <Typography
                  variant="h2"
                  sx={{
                    fontSize: { xs: '2.25rem', md: '3rem' },
                    fontWeight: 700,
                    mb: 4,
                    color: healthForesightColors.neutral.dark,
                    lineHeight: 1.2,
                    letterSpacing: '-0.01em',
                  }}
                >
                  Utilization changes because behavior changes
                </Typography>
                <Typography
                  variant="body1"
                  sx={{
                    fontSize: { xs: '16px', md: '17px' },
                    color: healthForesightColors.neutral.dark,
                    lineHeight: 1.7,
                    mb: 3,
                  }}
                >
                  HealthForesight identifies: provider response patterns (compliance, adaptation, resistance), patient response signals (deferral, substitution, fallback), and timing and lag effects.
                </Typography>
                <Typography
                  variant="h5"
                  sx={{
                    fontSize: { xs: '1.125rem', md: '1.25rem' },
                    fontWeight: 600,
                    color: healthForesightColors.accent.main,
                  }}
                >
                  This behavioral context explains why outcomes occurred, not just what changed.
                </Typography>
              </ScrollReveal>
            </Grid>
            <Grid item xs={12} md={6}>
              <ScrollReveal delay={300}>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <BehavioralShiftVisual />
                </Box>
              </ScrollReveal>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Section 10: Continuous Learning - Dark */}
      <Box
        sx={{
          position: 'relative',
          py: { xs: 10, md: 14 },
          backgroundColor: healthForesightColors.neutral.dark,
          color: '#FFFFFF',
          overflow: 'hidden',
        }}
      >
        <VisualPattern variant="grid" opacity={0.05} />
        <Container maxWidth="xl" sx={{ position: 'relative', zIndex: 1 }}>
          <Grid container spacing={8} sx={{ alignItems: 'center' }}>
            <Grid item xs={12} md={6}>
              <ScrollReveal delay={300}>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <LoopTighteningVisual />
                </Box>
              </ScrollReveal>
            </Grid>
            <Grid item xs={12} md={6}>
              <ScrollReveal delay={100}>
                <Typography
                  variant="h2"
                  sx={{
                    fontSize: { xs: '2.25rem', md: '3rem' },
                    fontWeight: 700,
                    mb: 4,
                    color: '#FFFFFF',
                    lineHeight: 1.2,
                    letterSpacing: '-0.01em',
                  }}
                >
                  The platform improves with every policy
                </Typography>
                <Typography
                  variant="body1"
                  sx={{
                    fontSize: { xs: '16px', md: '17px' },
                    color: '#FFFFFF',
                    lineHeight: 1.7,
                    mb: 3,
                  }}
                >
                  Each implemented policy: strengthens elasticity understanding, improves future prediction accuracy, and builds institutional knowledge.
                </Typography>
                <Typography
                  variant="h5"
                  sx={{
                    fontSize: { xs: '1.125rem', md: '1.25rem' },
                    fontWeight: 600,
                    color: healthForesightColors.accent.main,
                  }}
                >
                  Over time, utilization strategy becomes more reliable, consistent, and defensible.
                </Typography>
              </ScrollReveal>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Section 11: Outcomes - Light */}
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
                textAlign: 'center',
                color: healthForesightColors.neutral.dark,
                lineHeight: 1.2,
                letterSpacing: '-0.01em',
              }}
            >
              From reactive control to strategic governance
            </Typography>
            <Grid container spacing={3}>
              {outcomes.map((outcome, idx) => (
                <Grid item xs={12} sm={6} key={idx}>
                  <ScrollReveal delay={100 + idx * 80} stagger={idx * 80}>
                    <Box
                      sx={{
                        p: 4,
                        borderRadius: 2,
                        backgroundColor: healthForesightColors.neutral.background,
                        border: `1px solid ${healthForesightColors.neutral.light}`,
                        display: 'flex',
                        alignItems: 'center',
                        gap: 2,
                        height: '100%',
                        '&:hover': {
                          borderColor: healthForesightColors.primary.main + '40',
                          boxShadow: `0 4px 16px ${healthForesightColors.primary.main}15`,
                        },
                        transition: 'all 0.3s ease',
                      }}
                    >
                      <Box
                        sx={{
                          color: healthForesightColors.accent.main,
                          display: 'flex',
                          alignItems: 'center',
                        }}
                      >
                        <CheckCircle />
                      </Box>
                      <Typography
                        variant="body1"
                        sx={{
                          fontSize: '16px',
                          color: healthForesightColors.neutral.dark,
                          lineHeight: 1.7,
                          fontWeight: 500,
                        }}
                      >
                        {outcome}
                      </Typography>
                    </Box>
                  </ScrollReveal>
                </Grid>
              ))}
            </Grid>
          </ScrollReveal>
        </Container>
      </Box>

      {/* Final CTA - Dark */}
      <Box
        sx={{
          position: 'relative',
          py: { xs: 10, md: 14 },
          backgroundColor: healthForesightColors.neutral.dark,
          color: '#FFFFFF',
        }}
      >
        <Container maxWidth="md">
          <Box sx={{ textAlign: 'center' }}>
            <Typography
              variant="h2"
              sx={{
                fontSize: { xs: '2.25rem', md: '3rem' },
                fontWeight: 700,
                mb: 4,
                color: '#FFFFFF',
                lineHeight: 1.2,
                letterSpacing: '-0.01em',
              }}
            >
              Govern utilization with foresight — not hindsight.
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
              <Button
                variant="contained"
                size="large"
                onClick={() => navigate('/platform')}
                sx={{
                  px: 5,
                  py: 1.75,
                  fontSize: '16px',
                  fontWeight: 600,
                  backgroundColor: healthForesightColors.primary.main,
                  '&:hover': {
                    backgroundColor: healthForesightColors.primary.dark,
                  },
                }}
              >
                Explore the Platform
              </Button>
              <Button
                variant="outlined"
                size="large"
                onClick={() => navigate('/how-it-works')}
                sx={{
                  px: 5,
                  py: 1.75,
                  fontSize: '16px',
                  fontWeight: 600,
                  borderColor: 'rgba(255, 255, 255, 0.3)',
                  color: '#FFFFFF',
                  '&:hover': {
                    borderColor: '#FFFFFF',
                    backgroundColor: 'rgba(255, 255, 255, 0.1)',
                  },
                }}
              >
                See How It Works
              </Button>
            </Box>
          </Box>
        </Container>
      </Box>
    </Box>
  )
}
