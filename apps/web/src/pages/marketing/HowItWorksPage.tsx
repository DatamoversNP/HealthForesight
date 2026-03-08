/**
 * How It Works Page - Methodical, Governed, Auditable
 * Explains mechanics, not philosophy
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
import { healthForesightColors } from '../../theme/healthForesightTheme'
import VisualPattern from '../../components/marketing/VisualPattern'
import ScrollReveal from '../../components/marketing/ScrollReveal'
import PolicyBlueprintCard from '../../components/marketing/PolicyBlueprintCard'
import BaselineIsolationLens from '../../components/marketing/BaselineIsolationLens'
import DecisionDial from '../../components/marketing/DecisionDial'
import ParallelRealitySplit from '../../components/marketing/ParallelRealitySplit'
import BehavioralFlowLanes from '../../components/marketing/BehavioralFlowLanes'
import KnowledgeAccretionStack from '../../components/marketing/KnowledgeAccretionStack'

export default function HowItWorksPage() {
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
        <VisualPattern variant="dots" opacity={0.1} />
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
              From policy idea → measured outcome → institutional learning
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
              HealthForesight makes utilization policy outcomes predictable before implementation and measurable after implementation — with continuous learning over time.
            </Typography>
          </ScrollReveal>
        </Container>
      </Box>

      {/* Section 1: Start with a policy - Light */}
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
                  Everything starts with a policy decision
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
                  HealthForesight begins where utilization strategy actually lives: with a specific policy decision.
                </Typography>
                <Typography
                  variant="body1"
                  sx={{
                    fontSize: { xs: '16px', md: '17px' },
                    color: healthForesightColors.neutral.dark,
                    lineHeight: 1.75,
                    mb: 4,
                  }}
                >
                  Instead of analyzing utilization broadly, the platform treats each policy as a structured intervention with explicit scope, intent, and operational mechanics. Policies are not inferred. They are defined.
                </Typography>
                <Typography
                  variant="h5"
                  sx={{
                    fontSize: { xs: '1.125rem', md: '1.25rem' },
                    fontWeight: 600,
                    mb: 2,
                    color: healthForesightColors.neutral.dark,
                  }}
                >
                  What the system captures:
                </Typography>
                <Box component="ul" sx={{ pl: 0, listStyle: 'none', mb: 4 }}>
                  {[
                    'Who the policy applies to (population, plan, geography)',
                    'Where it applies (networks, providers, sites of care)',
                    'How it operates (authorization, restriction, sequencing)',
                    'When it applies (effective dates, versions)',
                    'What it excludes (exceptions, carve-outs)',
                  ].map((item, idx) => (
                    <Box
                      key={idx}
                      component="li"
                      sx={{
                        mb: 2,
                        pl: 3,
                        position: 'relative',
                        fontSize: { xs: '16px', md: '17px' },
                        color: healthForesightColors.neutral.dark,
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
                    color: healthForesightColors.neutral.dark,
                    lineHeight: 1.75,
                    fontStyle: 'italic',
                    fontWeight: 500,
                  }}
                >
                  This definition becomes the analytical backbone for everything that follows.
                </Typography>
              </ScrollReveal>
            </Grid>
            <Grid item xs={12} md={6}>
              <ScrollReveal delay={300}>
                <Box
                  sx={{
                    minHeight: { xs: '400px', md: '500px' },
                    borderRadius: 3,
                    overflow: 'visible',
                    backgroundColor: healthForesightColors.neutral.background,
                    border: `1px solid ${healthForesightColors.neutral.light}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    p: 2,
                  }}
                >
                  <PolicyBlueprintCard />
                </Box>
              </ScrollReveal>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Section 2: Establish baseline - Dark */}
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
                    height: { xs: '400px', md: '500px' },
                    borderRadius: 3,
                    overflow: 'hidden',
                    backgroundColor: 'rgba(255, 255, 255, 0.05)',
                    border: `1px solid rgba(255, 255, 255, 0.1)`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <BaselineIsolationLens />
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
                  Impact only matters relative to the right baseline
                </Typography>
                <Typography
                  variant="body1"
                  sx={{
                    fontSize: { xs: '16px', md: '17px' },
                    color: 'rgba(255, 255, 255, 0.9)',
                    lineHeight: 1.75,
                    mb: 3,
                  }}
                >
                  Once a policy is defined, HealthForesight constructs a policy-specific baseline — a representation of what utilization and cost would have looked like if the policy had never existed.
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
                  This baseline is:
                </Typography>
                <Box component="ul" sx={{ pl: 0, listStyle: 'none', mb: 4 }}>
                  {[
                    'Scoped exactly to the policy definition',
                    'Derived from recent pre-policy behavior',
                    'Adjusted for trend and seasonality',
                    'Locked and reused consistently across prediction and measurement',
                  ].map((item, idx) => (
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
                    color: 'rgba(255, 255, 255, 0.9)',
                    lineHeight: 1.75,
                    fontWeight: 500,
                  }}
                >
                  This ensures every result is interpretable, comparable, and defensible.
                </Typography>
              </ScrollReveal>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Section 3: Estimate expected impact - Light */}
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
                  See likely outcomes before consequences exist
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
                  Before implementation, HealthForesight estimates expected policy impact using historical behavior and learned elasticity patterns from similar policies.
                </Typography>
                <Typography
                  variant="h5"
                  sx={{
                    fontSize: { xs: '1.125rem', md: '1.25rem' },
                    fontWeight: 600,
                    mb: 2,
                    color: healthForesightColors.neutral.dark,
                  }}
                >
                  Estimates include:
                </Typography>
                <Box component="ul" sx={{ pl: 0, listStyle: 'none', mb: 4 }}>
                  {[
                    'Direction and magnitude of utilization change',
                    'Cost impact (PMPM and total)',
                    'Early indicators of substitution or leakage',
                    'Confidence bounds and explicit limitations',
                  ].map((item, idx) => (
                    <Box
                      key={idx}
                      component="li"
                      sx={{
                        mb: 2,
                        pl: 3,
                        position: 'relative',
                        fontSize: { xs: '16px', md: '17px' },
                        color: healthForesightColors.neutral.dark,
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
                      {item}
                    </Box>
                  ))}
                </Box>
                <Typography
                  variant="body1"
                  sx={{
                    fontSize: { xs: '16px', md: '17px' },
                    color: healthForesightColors.neutral.dark,
                    lineHeight: 1.75,
                    fontStyle: 'italic',
                    fontWeight: 500,
                  }}
                >
                  Predictions are presented as expectations, not guarantees — designed to inform decision-making, not automate it.
                </Typography>
              </ScrollReveal>
            </Grid>
            <Grid item xs={12} md={6}>
              <ScrollReveal delay={300}>
                <Box
                  sx={{
                    height: { xs: '400px', md: '500px' },
                    borderRadius: 3,
                    overflow: 'hidden',
                    backgroundColor: healthForesightColors.neutral.background,
                    border: `1px solid ${healthForesightColors.neutral.light}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <DecisionDial />
                </Box>
              </ScrollReveal>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Section 4: Measure observed impact - Dark */}
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
                    height: { xs: '400px', md: '500px' },
                    borderRadius: 3,
                    overflow: 'hidden',
                    backgroundColor: 'rgba(255, 255, 255, 0.05)',
                    border: `1px solid rgba(255, 255, 255, 0.1)`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <ParallelRealitySplit />
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
                  Separate policy effect from everything else
                </Typography>
                <Typography
                  variant="body1"
                  sx={{
                    fontSize: { xs: '16px', md: '17px' },
                    color: 'rgba(255, 255, 255, 0.9)',
                    lineHeight: 1.75,
                    mb: 3,
                  }}
                >
                  After a policy goes live and data accrues, HealthForesight measures observed impact by comparing real-world outcomes against the original baseline.
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
                  The platform:
                </Typography>
                <Box component="ul" sx={{ pl: 0, listStyle: 'none', mb: 4 }}>
                  {[
                    'Isolates policy effects from background trends',
                    'Quantifies utilization and cost changes attributable to the policy',
                    'Detects substitution, spillover, and leakage',
                    'Compares observed outcomes to earlier expectations',
                  ].map((item, idx) => (
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
                      {item}
                    </Box>
                  ))}
                </Box>
                <Typography
                  variant="body1"
                  sx={{
                    fontSize: { xs: '16px', md: '17px' },
                    color: 'rgba(255, 255, 255, 0.9)',
                    lineHeight: 1.75,
                    fontWeight: 500,
                  }}
                >
                  This creates a clear answer to the question: "What happened because of this policy?"
                </Typography>
              </ScrollReveal>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Section 5: Understand behavior - Light */}
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
                    lineHeight: 1.75,
                    mb: 3,
                  }}
                >
                  Numbers alone do not explain outcomes.
                </Typography>
                <Typography
                  variant="body1"
                  sx={{
                    fontSize: { xs: '16px', md: '17px' },
                    color: healthForesightColors.neutral.dark,
                    lineHeight: 1.75,
                    mb: 4,
                  }}
                >
                  HealthForesight analyzes provider and patient response patterns to explain why utilization changed, including: provider compliance, adaptation, or resistance; patient deferral, substitution, or fallback behavior; timing and lag effects; differences by site of care or network.
                </Typography>
                <Typography
                  variant="h5"
                  sx={{
                    fontSize: { xs: '1.125rem', md: '1.25rem' },
                    fontWeight: 600,
                    color: healthForesightColors.accent.main,
                  }}
                >
                  This behavioral context turns results into insight — not just metrics.
                </Typography>
              </ScrollReveal>
            </Grid>
            <Grid item xs={12} md={6}>
              <ScrollReveal delay={300}>
                <Box
                  sx={{
                    height: { xs: '400px', md: '500px' },
                    borderRadius: 3,
                    overflow: 'hidden',
                    backgroundColor: healthForesightColors.neutral.background,
                    border: `1px solid ${healthForesightColors.neutral.light}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <BehavioralFlowLanes />
                </Box>
              </ScrollReveal>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Section 6: Capture learning - Dark */}
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
                    height: { xs: '400px', md: '500px' },
                    borderRadius: 3,
                    overflow: 'hidden',
                    backgroundColor: 'rgba(255, 255, 255, 0.05)',
                    border: `1px solid rgba(255, 255, 255, 0.1)`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <KnowledgeAccretionStack />
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
                  Every policy makes the next one better
                </Typography>
                <Typography
                  variant="body1"
                  sx={{
                    fontSize: { xs: '16px', md: '17px' },
                    color: 'rgba(255, 255, 255, 0.9)',
                    lineHeight: 1.75,
                    mb: 3,
                  }}
                >
                  HealthForesight is designed as an institutional learning system.
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
                  Each implemented policy:
                </Typography>
                <Box component="ul" sx={{ pl: 0, listStyle: 'none', mb: 4 }}>
                  {[
                    'Improves elasticity understanding',
                    'Refines confidence bounds',
                    'Strengthens future predictions',
                    'Builds a reusable evidence base',
                  ].map((item, idx) => (
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
                          content: '"↑"',
                          position: 'absolute',
                          left: 0,
                          color: healthForesightColors.accent.main,
                          fontWeight: 700,
                          fontSize: '18px',
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
                    color: 'rgba(255, 255, 255, 0.9)',
                    lineHeight: 1.75,
                    fontWeight: 500,
                  }}
                >
                  Over time, utilization strategy becomes more reliable, consistent, and defensible.
                </Typography>
              </ScrollReveal>
            </Grid>
          </Grid>
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
        <VisualPattern variant="grid" opacity={0.05} />
        <Container maxWidth="md" sx={{ position: 'relative', zIndex: 1 }}>
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
              From reactive control to governed decision-making
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
              <Button
                variant="contained"
                size="large"
                onClick={() => navigate('/request-demo')}
                sx={{
                  minHeight: 44,
                  px: { xs: 4, md: 5 },
                  py: { xs: 1.5, md: 1.75 },
                  fontSize: { xs: '14px', md: '16px' },
                  fontWeight: 600,
                  backgroundColor: healthForesightColors.primary.main,
                  '&:hover': {
                    backgroundColor: healthForesightColors.primary.dark,
                  },
                }}
              >
                Request a Demo
              </Button>
              <Button
                variant="outlined"
                size="large"
                onClick={() => navigate('/platform')}
                sx={{
                  minHeight: 44,
                  px: { xs: 4, md: 5 },
                  py: { xs: 1.5, md: 1.75 },
                  fontSize: { xs: '14px', md: '16px' },
                  fontWeight: 600,
                  borderColor: 'rgba(255, 255, 255, 0.3)',
                  color: '#FFFFFF',
                  '&:hover': {
                    borderColor: '#FFFFFF',
                    backgroundColor: 'rgba(255, 255, 255, 0.1)',
                  },
                }}
              >
                See Platform Capabilities
              </Button>
            </Box>
          </Box>
        </Container>
      </Box>
    </Box>
  )
}
