/**
 * Solutions Page - Enterprise-Grade Design
 * Aligned with Homepage and Platform design standards
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
import { Warning, TrendingDown, Visibility, School } from '@mui/icons-material'
import { healthForesightColors } from '../theme/healthForesightTheme'
import VisualPattern from '../components/VisualPattern'
import ScrollReveal from '../components/ScrollReveal'
import PolicyBlindSpotsVisual from '../components/PolicyBlindSpotsVisual'
import TimelineImpactVisual from '../components/TimelineImpactVisual'
import BehaviorNetworkVisual from '../components/BehaviorNetworkVisual'
import LearningLoopVisual from '../components/LearningLoopVisual'

export default function SolutionsPage() {
  const navigate = useNavigate()
  
  // Safety check for theme colors
  if (!healthForesightColors || !healthForesightColors.primary || !healthForesightColors.amber) {
    console.error('healthForesightColors is not properly loaded', healthForesightColors)
    return (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <Typography>Loading theme...</Typography>
      </Box>
    )
  }

  const solutions = [
    {
      id: 1,
      title: 'Utilization Policy Blind Spots',
      whyProblem: 'Payers implement utilization policies to control cost, manage variation, and protect appropriate care. However, most policies are designed and approved with limited forward insight into how the system will respond.',
      commonRealities: [
        'Decisions rely on historical averages',
        'Impact expectations are directional, not quantified',
        'Risk is discussed qualitatively, not measured',
      ],
      negativeImpact: 'Without clear foresight: Policies underperform expected savings. Cost reductions are offset by substitution (ER, imaging, alternate coding). Access and experience issues surface too late. Leadership loses confidence in utilization controls. Result: policies become blunt instruments instead of strategic levers.',
      solution: 'HealthForesight introduces policy-aware foresight. Before implementation, the platform: evaluates the exact population and services a policy will affect, estimates expected utilization and cost change, surfaces likely substitution and spillover risks, communicates confidence and uncertainty transparently.',
      positiveImpact: 'With HealthForesight: policy decisions are informed, not assumed. Leaders understand trade-offs before execution. Risk is explicit and manageable. Fewer policy reversals and surprises.',
      visual: <PolicyBlindSpotsVisual />,
      icon: <Warning sx={{ fontSize: 48, color: '#FFFFFF' }} />,
      bgColor: 'dark', // Dark section
    },
    {
      id: 2,
      title: 'Misleading Post-Policy Analytics',
      whyProblem: 'After a policy is implemented, payers try to answer a simple question: "Did it work?" In practice, that answer is difficult because: utilization trends shift naturally, seasonality obscures changes, multiple initiatives overlap, reports focus on totals, not causality.',
      commonRealities: [],
      negativeImpact: 'As a result: teams argue over numbers instead of decisions. Savings claims are hard to defend. Unintended consequences are discovered late. Learnings are not reused. Result: analytics explain the past but fail to guide the future.',
      solution: 'HealthForesight applies policy-specific impact measurement. The platform: isolates policy effects from background trends, measures utilization and cost changes attributable to the policy, detects substitution, leakage, and delayed effects, attributes outcomes to provider and patient response patterns.',
      positiveImpact: 'With HealthForesight: policy impact is measurable and defensible. Leadership gets clarity, not conflicting reports. Issues are identified early. Outcomes are understood, not guessed.',
      visual: <TimelineImpactVisual />,
      icon: <TrendingDown sx={{ fontSize: 48, color: healthForesightColors.accent.main }} />,
      bgColor: 'light', // Light section
    },
    {
      id: 3,
      title: 'Provider & Patient Behavior Is Invisible',
      whyProblem: 'Utilization does not change mechanically. Providers and patients respond strategically. Examples: providers substitute services or sites, coding patterns adapt, patients defer care or shift to emergency settings. Most analytics stop at utilization counts — not behavior.',
      commonRealities: [],
      negativeImpact: 'Without behavioral insight: cost appears controlled while risk accumulates elsewhere. Access issues surface downstream. Policy effectiveness erodes over time. Trust between stakeholders declines.',
      solution: 'HealthForesight includes behavioral attribution as a core capability. The platform identifies: provider response patterns (compliance, adaptation, resistance), patient response signals (deferral, substitution, fallback), timing and lag effects following policy changes.',
      positiveImpact: 'With HealthForesight: leaders understand why outcomes occurred. Policies can be adjusted with precision. Unintended consequences are reduced. Utilization strategy becomes more humane and effective.',
      visual: <BehaviorNetworkVisual />,
      icon: <Visibility sx={{ fontSize: 48, color: '#FFFFFF' }} />,
      bgColor: 'dark', // Dark section
    },
    {
      id: 4,
      title: 'No Institutional Learning',
      whyProblem: 'Most organizations treat each policy change as a standalone event. What is missing: systematic learning across policies, institutional memory of what worked and did not, improving prediction accuracy over time.',
      commonRealities: [],
      negativeImpact: 'This leads to: repeated mistakes, slow improvement cycles, reliance on individual experience, fragile decision-making processes.',
      solution: 'HealthForesight is designed as a learning system. Each policy: improves elasticity understanding, informs future predictions, strengthens decision confidence. The system gets smarter with use.',
      positiveImpact: 'With HealthForesight: utilization strategy compounds. Decisions become more reliable. Organizations move from reactive control to strategic governance.',
      visual: <LearningLoopVisual />,
      icon: <School sx={{ fontSize: 48, color: healthForesightColors.primary.main }} />,
      bgColor: 'light', // Light section
    },
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
              Utilization policy decisions carry real financial and clinical risk.
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
              Most payers cannot see that risk clearly.
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
              HealthForesight helps payers understand why utilization behaves the way it does, how policy decisions change that behavior, and what outcomes those decisions truly produce.
            </Typography>
          </ScrollReveal>
        </Container>
      </Box>

      {/* Solution Areas - Alternating Light/Dark */}
      {solutions.map((solution, index) => {
        const isDark = solution.bgColor === 'dark'
        return (
          <Box
            key={solution.id}
            sx={{
              position: 'relative',
              py: { xs: 10, md: 14 },
              backgroundColor: isDark ? healthForesightColors.neutral.dark : '#FFFFFF',
              color: isDark ? '#FFFFFF' : healthForesightColors.neutral.dark,
              overflow: 'hidden',
            }}
          >
            {isDark && <VisualPattern variant="grid" opacity={0.05} />}
            <Container maxWidth="xl" sx={{ position: 'relative', zIndex: 1 }}>
              <Grid container spacing={8} sx={{ alignItems: 'center' }}>
                {/* Content Column */}
                <Grid item xs={12} md={6}>
                  <ScrollReveal delay={100}>
                    {/* Title */}
                    <Box sx={{ mb: 5 }}>
                      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2, mb: 3 }}>
                        <Box
                          sx={{
                            p: 1.5,
                            borderRadius: 2,
                            backgroundColor: isDark 
                              ? 'rgba(255, 255, 255, 0.1)' 
                              : healthForesightColors.primary.main + '15',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                          }}
                        >
                          {solution.icon}
                        </Box>
                        <Typography
                          variant="h2"
                          sx={{
                            fontWeight: 700,
                            color: isDark ? '#FFFFFF' : healthForesightColors.neutral.dark,
                            fontSize: { xs: '2rem', md: '2.5rem' },
                            lineHeight: 1.2,
                            letterSpacing: '-0.01em',
                          }}
                        >
                          {solution.title}
                        </Typography>
                      </Box>
                    </Box>

                    {/* Problem Section */}
                    <Box sx={{ mb: 5 }}>
                      <Typography
                        variant="h5"
                        sx={{
                          fontWeight: 600,
                          color: isDark ? '#FFFFFF' : healthForesightColors.neutral.dark,
                          mb: 2.5,
                          fontSize: { xs: '1.125rem', md: '1.25rem' },
                        }}
                      >
                        The Challenge
                      </Typography>
                      <Typography
                        variant="body1"
                        sx={{
                          maxWidth: { xs: '100%', md: '65ch' },
                          color: isDark ? 'rgba(255, 255, 255, 0.9)' : healthForesightColors.neutral.dark,
                          lineHeight: 1.75,
                          mb: 2.5,
                          fontSize: { xs: '16px', md: '17px' },
                        }}
                      >
                        {solution.whyProblem}
                      </Typography>
                      {solution.commonRealities.length > 0 && (
                        <Box
                          sx={{
                            mt: 3,
                            p: 3,
                            borderRadius: 2,
                            backgroundColor: isDark 
                              ? 'rgba(255, 255, 255, 0.05)' 
                              : healthForesightColors.neutral.background,
                            border: isDark 
                              ? `1px solid rgba(255, 255, 255, 0.1)` 
                              : `1px solid ${healthForesightColors.neutral.light}`,
                          }}
                        >
                          <Typography
                            variant="body2"
                            sx={{
                              color: isDark ? 'rgba(255, 255, 255, 0.9)' : healthForesightColors.neutral.mid,
                              fontWeight: 600,
                              mb: 1.5,
                              fontSize: '13px',
                            }}
                          >
                            Common realities:
                          </Typography>
                          {solution.commonRealities.map((reality, idx) => (
                            <Typography
                              key={idx}
                              variant="body2"
                              sx={{
                                color: isDark ? 'rgba(255, 255, 255, 0.9)' : healthForesightColors.neutral.dark,
                                lineHeight: 1.7,
                                mb: 1,
                                fontSize: '14px',
                              }}
                            >
                              • {reality}
                            </Typography>
                          ))}
                        </Box>
                      )}
                    </Box>

                    {/* Impact Section */}
                    <Box sx={{ mb: 5 }}>
                      <Typography
                        variant="h5"
                        sx={{
                          fontWeight: 600,
                          color: isDark ? '#FFFFFF' : healthForesightColors.neutral.dark,
                          mb: 2.5,
                          fontSize: { xs: '1.125rem', md: '1.25rem' },
                        }}
                      >
                        The Cost
                      </Typography>
                      <Box
                        sx={{
                          p: 3.5,
                          borderRadius: 3,
                          background: isDark
                            ? `linear-gradient(135deg, ${healthForesightColors.amber.main}20 0%, ${healthForesightColors.amber.main}10 100%)`
                            : `linear-gradient(135deg, ${healthForesightColors.amber.main}08 0%, ${healthForesightColors.amber.main}03 100%)`,
                          border: `1px solid ${healthForesightColors.amber.main}30`,
                        }}
                      >
                        <Typography
                          variant="body1"
                          sx={{
                            maxWidth: { xs: '100%', md: '65ch' },
                            color: isDark ? '#FFFFFF' : healthForesightColors.neutral.dark,
                            lineHeight: 1.75,
                            fontSize: { xs: '16px', md: '17px' },
                          }}
                        >
                          {solution.negativeImpact}
                        </Typography>
                      </Box>
                    </Box>

                    {/* Solution Section */}
                    <Box sx={{ mb: 5 }}>
                      <Typography
                        variant="h5"
                        sx={{
                          fontWeight: 600,
                          color: isDark ? '#FFFFFF' : healthForesightColors.neutral.dark,
                          mb: 2.5,
                          fontSize: { xs: '1.125rem', md: '1.25rem' },
                        }}
                      >
                        How HealthForesight Helps
                      </Typography>
                      <Typography
                        variant="body1"
                        sx={{
                          maxWidth: { xs: '100%', md: '65ch' },
                          color: isDark ? 'rgba(255, 255, 255, 0.9)' : healthForesightColors.neutral.dark,
                          lineHeight: 1.75,
                          mb: 3,
                          fontSize: { xs: '16px', md: '17px' },
                        }}
                      >
                        {solution.solution}
                      </Typography>
                    </Box>

                    {/* Outcome Section */}
                    <Box>
                      <Typography
                        variant="h5"
                        sx={{
                          fontWeight: 600,
                          color: isDark ? '#FFFFFF' : healthForesightColors.neutral.dark,
                          mb: 2.5,
                          fontSize: { xs: '1.125rem', md: '1.25rem' },
                        }}
                      >
                        The Result
                      </Typography>
                      <Box
                        sx={{
                          p: 3.5,
                          borderRadius: 3,
                          background: isDark
                            ? `linear-gradient(135deg, ${healthForesightColors.accent.main}20 0%, ${healthForesightColors.accent.main}10 100%)`
                            : `linear-gradient(135deg, ${healthForesightColors.accent.main}12 0%, ${healthForesightColors.accent.main}05 100%)`,
                          border: `1px solid ${healthForesightColors.accent.main}30`,
                        }}
                      >
                        <Typography
                          variant="body1"
                          sx={{
                            maxWidth: { xs: '100%', md: '65ch' },
                            color: isDark ? '#FFFFFF' : healthForesightColors.neutral.dark,
                            lineHeight: 1.75,
                            fontWeight: 500,
                            fontSize: { xs: '16px', md: '17px' },
                          }}
                        >
                          {solution.positiveImpact}
                        </Typography>
                      </Box>
                    </Box>
                  </ScrollReveal>
                </Grid>

                {/* Visual Column */}
                <Grid item xs={12} md={6}>
                  <ScrollReveal delay={300}>
                    <Box
                      sx={{
                        height: { xs: '400px', md: '500px' },
                        borderRadius: 3,
                        overflow: 'hidden',
                        backgroundColor: isDark 
                          ? 'rgba(255, 255, 255, 0.05)' 
                          : healthForesightColors.neutral.background,
                        border: isDark 
                          ? `1px solid rgba(255, 255, 255, 0.1)` 
                          : `1px solid ${healthForesightColors.neutral.light}`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      {solution.visual}
                    </Box>
                  </ScrollReveal>
                </Grid>
              </Grid>
            </Container>
          </Box>
        )
      })}

      {/* CTA - Dark */}
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
              Which utilization challenge can we help you solve?
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
