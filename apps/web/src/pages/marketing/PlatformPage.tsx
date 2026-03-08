/**
 * Platform Page - Enterprise Decision Intelligence
 * System-based visuals, flowing sections, progressive clarity
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
import { healthForesightColors } from '../../theme/healthForesightTheme'
import VisualPattern from '../../components/marketing/VisualPattern'
import EnterpriseParticles from '../../components/marketing/EnterpriseParticles'
import GSAPAnimations from '../../components/marketing/GSAPAnimations'
import SystemFlowAnimation from '../../components/marketing/SystemFlowAnimation'
import AnalyticsToIntelligenceVisual from '../../components/marketing/AnalyticsToIntelligenceVisual'
import PolicyObjectVisual from '../../components/marketing/PolicyObjectVisual'
import BaselineFormationVisual from '../../components/marketing/BaselineFormationVisual'
import ForecastEnvelopeVisual from '../../components/marketing/ForecastEnvelopeVisual'
import PredictionVsRealityVisual from '../../components/marketing/PredictionVsRealityVisual'
import BehaviorClustersVisual from '../../components/marketing/BehaviorClustersVisual'
import EnhancedLearningLoop from '../../components/marketing/EnhancedLearningLoop'

export default function PlatformPage() {
  const navigate = useNavigate()

  const outcomes = [
    'Better policy decisions',
    'Fewer unintended consequences',
    'Improved financial predictability',
    'Stronger leadership confidence',
    'Institutional learning, not one-off analysis',
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
        <VisualPattern variant="dots" opacity={0.15} />
        <VisualPattern variant="grid" opacity={0.08} />
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            opacity: 0.08,
            zIndex: 0,
          }}
        >
          <SystemFlowAnimation />
        </Box>
        <Container maxWidth="xl" sx={{ position: 'relative', zIndex: 1 }}>
          <GSAPAnimations animationType="fadeInUp" delay={0.2}>
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
              Most organizations still manage them without clarity.
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
              HealthForesight is an enterprise decision intelligence platform that makes utilization policy outcomes predictable before implementation and measurable after implementation — with continuous learning over time.
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
                onClick={() => navigate('/how-it-works')}
                sx={{
                  minHeight: 44,
                  px: { xs: 4, md: 5 },
                  py: { xs: 1.5, md: 1.75 },
                  fontSize: { xs: '14px', md: '16px' },
                  fontWeight: 600,
                }}
              >
                Explore How It Works
              </Button>
            </Box>
          </GSAPAnimations>
        </Container>
      </Box>

      {/* Section 1: Category Definition - Dark */}
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
              <GSAPAnimations animationType="fadeInUp" delay={0.1}>
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
                    color: 'rgba(255, 255, 255, 0.9)',
                    lineHeight: 1.7,
                    mb: 3,
                  }}
                >
                  Traditional analytics platforms focus on reporting utilization and cost after the fact. HealthForesight is designed around decisions — specifically, utilization policy decisions that affect cost, access, and behavior.
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
                        color: 'rgba(255, 255, 255, 0.95)',
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
                    fontSize: { xs: '1.25rem', md: '1.5rem' },
                    fontWeight: 600,
                    color: healthForesightColors.accent.main,
                  }}
                >
                  This is the difference between reporting data and governing utilization.
                </Typography>
              </GSAPAnimations>
            </Grid>
            <Grid item xs={12} md={6}>
              <GSAPAnimations animationType="fadeIn" delay={0.3}>
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
                  <AnalyticsToIntelligenceVisual />
                </Box>
              </GSAPAnimations>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Section 2: Why Platform Exists - Light */}
      <Box
        sx={{
          position: 'relative',
          py: { xs: 10, md: 14 },
          backgroundColor: '#FFFFFF',
          overflow: 'hidden',
        }}
      >
        <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
          <GSAPAnimations animationType="fadeInUp" delay={0.2}>
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
              Payers deploy utilization controls to influence behavior — not just to count claims.
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
                'policies are approved with limited forward insight',
                'expected savings are directional, not quantified',
                'post-implementation analysis is slow and inconclusive',
                'substitution and spillover obscure true outcomes',
                'learnings are rarely reused',
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
          </GSAPAnimations>
        </Container>
      </Box>

      {/* Section 3: Policy as First-Class Object - Dark */}
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
          <GSAPAnimations animationType="fadeInUp" delay={0.2}>
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
              HealthForesight understands policies — not just data
            </Typography>
            <Typography
              variant="body1"
              sx={{
                fontSize: { xs: '16px', md: '17px' },
                color: 'rgba(255, 255, 255, 0.9)',
                lineHeight: 1.7,
                mb: 5,
                textAlign: 'center',
                maxWidth: '900px',
                mx: 'auto',
              }}
            >
              HealthForesight treats each utilization policy as a structured, analyzable decision. Policies are explicitly defined by who they apply to, where they apply, how they operate, when they apply, and what they exclude. This structure allows the platform to understand exactly what utilization a policy is intended to influence.
            </Typography>
            <Box
              sx={{
                maxWidth: '600px',
                mx: 'auto',
                mb: 5,
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
              <PolicyObjectVisual />
            </Box>
            <Box
              sx={{
                p: 4,
                borderRadius: 3,
                backgroundColor: healthForesightColors.primary.main + '20',
                border: `1px solid ${healthForesightColors.primary.main}40`,
                maxWidth: '800px',
                mx: 'auto',
              }}
            >
              <Typography
                variant="h5"
                sx={{
                  fontSize: '1.25rem',
                  fontWeight: 700,
                  mb: 2,
                  color: healthForesightColors.accent.main,
                }}
              >
                Why This Matters
              </Typography>
              <Typography
                variant="body1"
                sx={{
                  fontSize: { xs: '16px', md: '17px' },
                  color: 'rgba(255, 255, 255, 0.95)',
                  lineHeight: 1.7,
                }}
              >
                If the system does not understand the policy, it cannot credibly predict or measure its impact.
              </Typography>
            </Box>
          </GSAPAnimations>
        </Container>
      </Box>

      {/* Section 4: Policy-Scoped Baselines - Light */}
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
              <GSAPAnimations animationType="fadeInUp" delay={0.1}>
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
                  Impact can only be measured against the right baseline
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
                  HealthForesight establishes policy-specific baselines that reflect what utilization and cost looked like before a policy existed.
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
                    lineHeight: 1.7,
                    fontStyle: 'italic',
                    fontWeight: 500,
                  }}
                >
                  Instead of broad averages, the platform answers: "What would have happened if this policy had not been introduced?"
                </Typography>
              </GSAPAnimations>
            </Grid>
            <Grid item xs={12} md={6}>
              <GSAPAnimations animationType="fadeIn" delay={0.3}>
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
                  <BaselineFormationVisual />
                </Box>
              </GSAPAnimations>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Section 5: Expected Impact - Dark */}
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
          <GSAPAnimations animationType="fadeInUp" delay={0.2}>
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
              See what a policy is likely to do before it creates consequences
            </Typography>
            <Typography
              variant="body1"
              sx={{
                fontSize: { xs: '16px', md: '17px' },
                color: 'rgba(255, 255, 255, 0.9)',
                lineHeight: 1.7,
                mb: 5,
                textAlign: 'center',
                maxWidth: '800px',
                mx: 'auto',
              }}
            >
              Before implementation, HealthForesight estimates expected policy impact based on historical behavior and learned elasticity patterns. The platform provides projected utilization change, projected cost impact, early signals of substitution and leakage, and confidence indicators and limitations.
            </Typography>
            <Box
              sx={{
                maxWidth: '700px',
                mx: 'auto',
                mb: 5,
                height: { xs: '400px', md: '450px' },
                borderRadius: 3,
                overflow: 'hidden',
                backgroundColor: 'rgba(255, 255, 255, 0.05)',
                border: `1px solid rgba(255, 255, 255, 0.1)`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <ForecastEnvelopeVisual />
            </Box>
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
              Predictions are transparent, bounded, and explicitly labeled as expectations — not guarantees.
            </Typography>
            <Box
              sx={{
                p: 4,
                borderRadius: 3,
                backgroundColor: healthForesightColors.accent.main + '20',
                border: `1px solid ${healthForesightColors.accent.main}40`,
                maxWidth: '800px',
                mx: 'auto',
              }}
            >
              <Typography
                variant="h5"
                sx={{
                  fontSize: '1.25rem',
                  fontWeight: 700,
                  mb: 2,
                  color: healthForesightColors.accent.main,
                }}
              >
                Why This Matters
              </Typography>
              <Typography
                variant="body1"
                sx={{
                  fontSize: { xs: '16px', md: '17px' },
                  color: 'rgba(255, 255, 255, 0.95)',
                  lineHeight: 1.7,
                }}
              >
                Leaders can challenge assumptions, adjust scope, or reconsider design before operational and financial consequences occur.
              </Typography>
            </Box>
          </GSAPAnimations>
        </Container>
      </Box>

      {/* Section 6: Observed Impact - Light */}
      <Box
        sx={{
          position: 'relative',
          py: { xs: 10, md: 14 },
          backgroundColor: '#FFFFFF',
          overflow: 'hidden',
        }}
      >
        <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
          <GSAPAnimations animationType="fadeInUp" delay={0.2}>
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
              Understand what actually happened — and why
            </Typography>
            <Typography
              variant="body1"
              sx={{
                fontSize: { xs: '16px', md: '17px' },
                color: healthForesightColors.neutral.dark,
                lineHeight: 1.7,
                mb: 5,
                textAlign: 'center',
                maxWidth: '800px',
                mx: 'auto',
              }}
            >
              Once a policy is live and data accrues, HealthForesight measures observed impact. The platform isolates policy effects from background trends, quantifies utilization and cost changes attributable to the policy, detects substitution, spillover, and leakage, and explains outcomes via provider and patient behavior patterns.
            </Typography>
            <Box
              sx={{
                maxWidth: '700px',
                mx: 'auto',
                mb: 4,
                height: { xs: '400px', md: '450px' },
                borderRadius: 3,
                overflow: 'hidden',
                backgroundColor: healthForesightColors.neutral.background,
                border: `1px solid ${healthForesightColors.neutral.light}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <PredictionVsRealityVisual />
            </Box>
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
              Observed results are compared directly against: the original baseline and the earlier expected impact.
            </Typography>
          </GSAPAnimations>
        </Container>
      </Box>

      {/* Section 7: Behavioral Attribution - Dark */}
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
              <GSAPAnimations animationType="fadeInUp" delay={0.1}>
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
                  Utilization changes because behavior changes
                </Typography>
                <Typography
                  variant="body1"
                  sx={{
                    fontSize: { xs: '16px', md: '17px' },
                    color: 'rgba(255, 255, 255, 0.9)',
                    lineHeight: 1.7,
                    mb: 3,
                  }}
                >
                  Utilization policies influence behavior — not just volume.
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
                  HealthForesight identifies:
                </Typography>
                <Box component="ul" sx={{ pl: 0, listStyle: 'none', mb: 4 }}>
                  {[
                    'provider response patterns (compliance, adaptation, resistance)',
                    'patient response signals (deferral, substitution, fallback)',
                    'timing and lag effects',
                  ].map((item, idx) => (
                    <Box
                      key={idx}
                      component="li"
                      sx={{
                        mb: 2,
                        pl: 3,
                        position: 'relative',
                        fontSize: { xs: '16px', md: '17px' },
                        color: 'rgba(255, 255, 255, 0.95)',
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
                      {item}
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
                  This behavioral context explains why outcomes occurred — not just what changed.
                </Typography>
              </GSAPAnimations>
            </Grid>
            <Grid item xs={12} md={6}>
              <GSAPAnimations animationType="fadeIn" delay={0.3}>
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
                  <BehaviorClustersVisual />
                </Box>
              </GSAPAnimations>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Section 8: Learning & Elasticity - Light */}
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
              <GSAPAnimations animationType="fadeIn" delay={0.3}>
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
                  <EnhancedLearningLoop />
                </Box>
              </GSAPAnimations>
            </Grid>
            <Grid item xs={12} md={6}>
              <GSAPAnimations animationType="fadeInUp" delay={0.1}>
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
                  The platform improves with every policy
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
                  HealthForesight is designed as a learning system. Each implemented policy strengthens elasticity understanding, improves future prediction accuracy, and builds institutional knowledge.
                </Typography>
                <Typography
                  variant="h5"
                  sx={{
                    fontSize: { xs: '1.125rem', md: '1.25rem' },
                    fontWeight: 600,
                    color: healthForesightColors.neutral.dark,
                  }}
                >
                  Over time, utilization strategy becomes more reliable, consistent, and defensible.
                </Typography>
              </GSAPAnimations>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Section 9: Outcomes - Dark */}
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
          <GSAPAnimations animationType="fadeInUp" delay={0.2}>
            <Typography
              variant="h2"
              sx={{
                fontSize: { xs: '2.25rem', md: '3rem' },
                fontWeight: 700,
                mb: 6,
                textAlign: 'center',
                color: '#FFFFFF',
                lineHeight: 1.2,
                letterSpacing: '-0.01em',
              }}
            >
              From reactive control to strategic governance
            </Typography>
            <Grid container spacing={3}>
              {outcomes.map((outcome, idx) => (
                <Grid item xs={12} sm={6} key={idx}>
                  <Box
                    sx={{
                      p: 3,
                      borderRadius: 2,
                      backgroundColor: 'rgba(255, 255, 255, 0.05)',
                      border: `1px solid rgba(255, 255, 255, 0.1)`,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 2,
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
                        color: 'rgba(255, 255, 255, 0.95)',
                        lineHeight: 1.7,
                        fontWeight: 500,
                      }}
                    >
                      {outcome}
                    </Typography>
                  </Box>
                </Grid>
              ))}
            </Grid>
          </GSAPAnimations>
        </Container>
      </Box>

      {/* Final CTA - Light */}
      <Box
        sx={{
          py: { xs: 10, md: 14 },
          backgroundColor: '#FFFFFF',
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
                color: healthForesightColors.neutral.dark,
                lineHeight: 1.2,
                letterSpacing: '-0.01em',
              }}
            >
              Make utilization policy a governed, learnable capability
            </Typography>
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
          </Box>
        </Container>
      </Box>
    </Box>
  )
}
