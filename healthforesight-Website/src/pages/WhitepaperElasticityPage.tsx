/**
 * Whitepaper Detail Page: Measuring Elasticity in Healthcare Utilization
 * Flagship enterprise research asset - academic credibility, executive readability
 */
import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Container,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableRow,
  TableHead,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
} from '@mui/material'
import { ExpandMore, Download, Email } from '@mui/icons-material'
import { healthForesightColors } from '../theme/healthForesightTheme'
import ScrollReveal from '../components/ScrollReveal'
import ElasticityHeroVisual from '../components/ElasticityHeroVisual'
import ExecutiveSummaryInfographic from '../components/ExecutiveSummaryInfographic'
import UtilizationAreaChart from '../components/UtilizationAreaChart'
import ClassicalVsHealthcareVisual from '../components/ClassicalVsHealthcareVisual'
import BehavioralSankeyFlow from '../components/BehavioralSankeyFlow'
import CounterfactualTimeline from '../components/CounterfactualTimeline'
import CareContinuumHeatBand from '../components/CareContinuumHeatBand'
import ConfidenceFanChart from '../components/ConfidenceFanChart'
import MaturityCurve from '../components/MaturityCurve'

export default function WhitepaperElasticityPage() {
  const navigate = useNavigate()
  const [appendixExpanded, setAppendixExpanded] = useState(false)

  return (
    <Box sx={{ backgroundColor: '#FFFFFF' }}>
      {/* Hero Section */}
      <Box
        sx={{
          position: 'relative',
          py: { xs: 8, md: 12 },
          backgroundColor: healthForesightColors.neutral.dark,
          color: '#FFFFFF',
          overflow: 'hidden',
        }}
      >
        <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
          <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 6, alignItems: 'center' }}>
            <Box sx={{ flex: 1 }}>
              <ScrollReveal delay={0}>
                <Chip
                  label="Whitepaper"
                  sx={{
                    mb: 2,
                    backgroundColor: 'rgba(255, 255, 255, 0.15)',
                    color: '#FFFFFF',
                    fontWeight: 600,
                  }}
                />
                <Typography
                  variant="h1"
                  sx={{
                    fontSize: { xs: '2.5rem', md: '3.5rem' },
                    fontWeight: 700,
                    mb: 2,
                    color: '#FFFFFF',
                    lineHeight: 1.2,
                    letterSpacing: '-0.02em',
                  }}
                >
                  Measuring Elasticity in Healthcare Utilization
                </Typography>
                <Typography
                  variant="h5"
                  sx={{
                    fontSize: { xs: '1.1rem', md: '1.25rem' },
                    fontWeight: 400,
                    color: 'rgba(255, 255, 255, 0.9)',
                    mb: 3,
                    lineHeight: 1.6,
                  }}
                >
                  A Behavioral, Economic, and Causal Framework for Policy Impact Measurement
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                  <Chip label="Policy Intelligence" size="small" sx={{ backgroundColor: 'rgba(255, 255, 255, 0.15)', color: '#FFFFFF' }} />
                  <Chip label="Healthcare Economics" size="small" sx={{ backgroundColor: 'rgba(255, 255, 255, 0.15)', color: '#FFFFFF' }} />
                </Box>
              </ScrollReveal>
            </Box>
            <Box sx={{ flex: { xs: 1, md: '0 0 400px' }, width: '100%', maxWidth: '500px' }}>
              <ElasticityHeroVisual />
            </Box>
          </Box>
        </Container>
      </Box>

      {/* Executive Summary */}
      <Box
        sx={{
          py: { xs: 8, md: 10 },
          backgroundColor: '#FFFFFF',
        }}
      >
        <Container maxWidth="lg">
          <Box sx={{ display: 'flex', flexDirection: { xs: 'column', lg: 'row' }, gap: 6 }}>
            <Box sx={{ flex: 1 }}>
              <ScrollReveal delay={200}>
                <Typography
                  variant="h2"
                  sx={{
                    fontSize: { xs: '2rem', md: '2.5rem' },
                    fontWeight: 700,
                    mb: 4,
                    color: healthForesightColors.neutral.dark,
                  }}
                >
                  Executive Summary
                </Typography>
                <Typography
                  variant="body1"
                  sx={{
                    maxWidth: { xs: '100%', md: '65ch' },
                    fontSize: { xs: '16px', md: '17px' },
                    color: healthForesightColors.neutral.dark,
                    lineHeight: 1.8,
                    mb: 3,
                  }}
                >
                  Healthcare utilization elasticity—the responsiveness of utilization patterns to policy interventions—is a fundamental driver of medical cost trends and policy effectiveness. Yet traditional economic models, designed for consumer markets, fail to capture the behavioral complexity and system-level dynamics that characterize healthcare utilization.
                </Typography>
                <Typography
                  variant="body1"
                  sx={{
                    maxWidth: { xs: '100%', md: '65ch' },
                    fontSize: { xs: '16px', md: '17px' },
                    color: healthForesightColors.neutral.dark,
                    lineHeight: 1.8,
                    mb: 3,
                  }}
                >
                  This whitepaper presents a comprehensive framework for measuring utilization elasticity in healthcare policy contexts. We argue that effective policy impact measurement requires: (1) behavioral attribution that accounts for provider and patient responses, (2) system-level analysis that captures substitution and spillover effects, and (3) causal inference methods that isolate policy effects from confounding trends.
                </Typography>
                <Typography
                  variant="body1"
                  sx={{
                    maxWidth: { xs: '100%', md: '65ch' },
                    fontSize: { xs: '16px', md: '17px' },
                    color: healthForesightColors.neutral.dark,
                    lineHeight: 1.8,
                    mb: 3,
                  }}
                >
                  Our framework distinguishes between naïve elasticity (direct policy effects) and system-level elasticity (net effects including substitution). We demonstrate that system-level elasticity is typically 30–50% lower than naïve estimates, with significant implications for policy design, financial forecasting, and risk management.
                </Typography>
                <Typography
                  variant="body1"
                  sx={{
                    maxWidth: { xs: '100%', md: '65ch' },
                    fontSize: { xs: '16px', md: '17px' },
                    color: healthForesightColors.neutral.dark,
                    lineHeight: 1.8,
                    fontWeight: 600,
                  }}
                >
                  For payer executives, actuaries, and policy leaders, this framework provides the analytical foundation needed to make evidence-based policy decisions, improve forecast accuracy, and reduce unintended consequences.
                </Typography>
              </ScrollReveal>
            </Box>
            <Box sx={{ flex: { xs: 1, lg: '0 0 300px' } }}>
              <ExecutiveSummaryInfographic />
            </Box>
          </Box>
        </Container>
      </Box>

      {/* Section 1: Strategic Importance */}
      <Box
        sx={{
          py: { xs: 8, md: 10 },
          backgroundColor: healthForesightColors.neutral.background,
        }}
      >
        <Container maxWidth="lg">
          <ScrollReveal delay={200}>
            <Typography
              variant="h2"
              sx={{
                fontSize: { xs: '2rem', md: '2.5rem' },
                fontWeight: 700,
                mb: 4,
                color: healthForesightColors.neutral.dark,
              }}
            >
              1. Strategic Importance of Utilization Elasticity
            </Typography>
            <Typography
              variant="body1"
              sx={{
                maxWidth: { xs: '100%', md: '65ch' },
                fontSize: { xs: '16px', md: '17px' },
                color: healthForesightColors.neutral.dark,
                lineHeight: 1.8,
                mb: 4,
              }}
            >
              Utilization elasticity is the primary driver of medical cost trends, accounting for 50–70% of year-over-year cost variation. Unlike price elasticity in consumer markets, utilization elasticity in healthcare reflects complex behavioral responses from providers, patients, and care delivery systems.
            </Typography>
            <Box sx={{ mb: 4 }}>
              <UtilizationAreaChart />
            </Box>
            <Typography
              variant="body1"
              sx={{
                maxWidth: { xs: '100%', md: '65ch' },
                fontSize: { xs: '16px', md: '17px' },
                color: healthForesightColors.neutral.dark,
                lineHeight: 1.8,
              }}
            >
              Understanding utilization elasticity is not merely an analytical exercise—it is a strategic imperative. Organizations that can accurately predict and measure utilization responses to policy interventions gain significant advantages in financial planning, risk management, and policy design.
            </Typography>
          </ScrollReveal>
        </Container>
      </Box>

      {/* Section 2: Why Traditional Elasticity Breaks Down */}
      <Box
        sx={{
          py: { xs: 8, md: 10 },
          backgroundColor: '#FFFFFF',
        }}
      >
        <Container maxWidth="lg">
          <ScrollReveal delay={200}>
            <Typography
              variant="h2"
              sx={{
                fontSize: { xs: '2rem', md: '2.5rem' },
                fontWeight: 700,
                mb: 4,
                color: healthForesightColors.neutral.dark,
              }}
            >
              2. Why Traditional Elasticity Breaks Down
            </Typography>
            <Typography
              variant="body1"
              sx={{
                maxWidth: { xs: '100%', md: '65ch' },
                fontSize: { xs: '16px', md: '17px' },
                color: healthForesightColors.neutral.dark,
                lineHeight: 1.8,
                mb: 4,
              }}
            >
              Classical economic models assume rational actors, perfect information, and direct price-quantity relationships. Healthcare utilization violates these assumptions at every level: providers respond to policy constraints through coding adaptation and site shifting, patients defer or substitute care, and system-level effects create cascading impacts across care settings.
            </Typography>
            <Box sx={{ mb: 4 }}>
              <ClassicalVsHealthcareVisual />
            </Box>
            <Typography
              variant="body1"
              sx={{
                maxWidth: { xs: '100%', md: '65ch' },
                fontSize: { xs: '16px', md: '17px' },
                color: healthForesightColors.neutral.dark,
                lineHeight: 1.8,
              }}
            >
              The result is a fractured, branching response pattern that cannot be captured by simple demand curves. Effective elasticity measurement requires behavioral attribution and system-level analysis.
            </Typography>
          </ScrollReveal>
        </Container>
      </Box>

      {/* Section 3: Behavioral Foundations */}
      <Box
        sx={{
          py: { xs: 8, md: 10 },
          backgroundColor: healthForesightColors.neutral.background,
        }}
      >
        <Container maxWidth="lg">
          <ScrollReveal delay={200}>
            <Typography
              variant="h2"
              sx={{
                fontSize: { xs: '2rem', md: '2.5rem' },
                fontWeight: 700,
                mb: 4,
                color: healthForesightColors.neutral.dark,
              }}
            >
              3. Behavioral Foundations
            </Typography>
            <Typography
              variant="body1"
              sx={{
                maxWidth: { xs: '100%', md: '65ch' },
                fontSize: { xs: '16px', md: '17px' },
                color: healthForesightColors.neutral.dark,
                lineHeight: 1.8,
                mb: 4,
              }}
            >
              Utilization elasticity is fundamentally behavior-driven, not rule-driven. Policy interventions trigger cascading behavioral responses: providers may comply, adapt, resist, or circumvent; patients may defer, substitute, or fall back to emergency settings. These responses vary by provider segment, patient population, and care setting.
            </Typography>
            <Box sx={{ mb: 4 }}>
              <BehavioralSankeyFlow />
            </Box>
            <Typography
              variant="body1"
              sx={{
                maxWidth: { xs: '100%', md: '65ch' },
                fontSize: { xs: '16px', md: '17px' },
                color: healthForesightColors.neutral.dark,
                lineHeight: 1.8,
              }}
            >
              Understanding these behavioral patterns is essential for accurate elasticity measurement. Without behavioral attribution, policy impact estimates will systematically overstate direct effects and miss substitution and spillover consequences.
            </Typography>
          </ScrollReveal>
        </Container>
      </Box>

      {/* Section 4: Establishing a Credible Baseline */}
      <Box
        sx={{
          py: { xs: 8, md: 10 },
          backgroundColor: '#FFFFFF',
        }}
      >
        <Container maxWidth="lg">
          <ScrollReveal delay={200}>
            <Typography
              variant="h2"
              sx={{
                fontSize: { xs: '2rem', md: '2.5rem' },
                fontWeight: 700,
                mb: 4,
                color: healthForesightColors.neutral.dark,
              }}
            >
              4. Establishing a Credible Baseline
            </Typography>
            <Typography
              variant="body1"
              sx={{
                maxWidth: { xs: '100%', md: '65ch' },
                fontSize: { xs: '16px', md: '17px' },
                color: healthForesightColors.neutral.dark,
                lineHeight: 1.8,
                mb: 4,
              }}
            >
              Policy impact can only be measured against a credible counterfactual baseline—what utilization would have been in the absence of the policy. Establishing this baseline requires: (1) policy-scoped data selection, (2) trend and seasonality adjustment, and (3) causal inference methods that account for confounding factors.
            </Typography>
            <Box sx={{ mb: 4 }}>
              <CounterfactualTimeline />
            </Box>
            <Typography
              variant="body1"
              sx={{
                maxWidth: { xs: '100%', md: '65ch' },
                fontSize: { xs: '16px', md: '17px' },
                color: healthForesightColors.neutral.dark,
                lineHeight: 1.8,
              }}
            >
              The counterfactual baseline is not a simple historical average—it is a carefully constructed estimate that reflects what would have happened, accounting for all relevant trends and external factors. This baseline becomes the anchor for both prediction (expected impact) and measurement (observed impact).
            </Typography>
          </ScrollReveal>
        </Container>
      </Box>

      {/* Section 5: Substitution & System-Level Elasticity */}
      <Box
        sx={{
          py: { xs: 8, md: 10 },
          backgroundColor: healthForesightColors.neutral.background,
        }}
      >
        <Container maxWidth="lg">
          <ScrollReveal delay={200}>
            <Typography
              variant="h2"
              sx={{
                fontSize: { xs: '2rem', md: '2.5rem' },
                fontWeight: 700,
                mb: 4,
                color: healthForesightColors.neutral.dark,
              }}
            >
              5. Substitution & System-Level Elasticity
            </Typography>
            <Typography
              variant="body1"
              sx={{
                maxWidth: { xs: '100%', md: '65ch' },
                fontSize: { xs: '16px', md: '17px' },
                color: healthForesightColors.neutral.dark,
                lineHeight: 1.8,
                mb: 4,
              }}
            >
              When utilization is restricted in one care setting, it often shifts to another. This substitution effect is a defining characteristic of healthcare utilization elasticity. A policy that reduces outpatient imaging may increase emergency department utilization; a prior authorization requirement may shift care to alternative sites or delay necessary interventions.
            </Typography>
            <Box sx={{ mb: 4 }}>
              <CareContinuumHeatBand />
            </Box>
            <Typography
              variant="body1"
              sx={{
                maxWidth: { xs: '100%', md: '65ch' },
                fontSize: { xs: '16px', md: '17px' },
                color: healthForesightColors.neutral.dark,
                lineHeight: 1.8,
              }}
            >
              System-level elasticity accounts for these substitution effects, providing a net impact estimate that reflects true policy outcomes. This is typically 30–50% lower than naïve elasticity estimates that only measure direct effects.
            </Typography>
          </ScrollReveal>
        </Container>
      </Box>

      {/* Section 6: Quantifying Uncertainty */}
      <Box
        sx={{
          py: { xs: 8, md: 10 },
          backgroundColor: '#FFFFFF',
        }}
      >
        <Container maxWidth="lg">
          <ScrollReveal delay={200}>
            <Typography
              variant="h2"
              sx={{
                fontSize: { xs: '2rem', md: '2.5rem' },
                fontWeight: 700,
                mb: 4,
                color: healthForesightColors.neutral.dark,
              }}
            >
              6. Quantifying Uncertainty
            </Typography>
            <Typography
              variant="body1"
              sx={{
                maxWidth: { xs: '100%', md: '65ch' },
                fontSize: { xs: '16px', md: '17px' },
                color: healthForesightColors.neutral.dark,
                lineHeight: 1.8,
                mb: 4,
              }}
            >
              Elasticity estimates are inherently uncertain. This uncertainty arises from: (1) behavioral response variation, (2) substitution pattern unpredictability, (3) lag effects and timing differences, and (4) confounding factors that cannot be fully controlled. Effective policy decision-making requires explicit quantification of this uncertainty.
            </Typography>
            <Box sx={{ mb: 4 }}>
              <ConfidenceFanChart />
            </Box>
            <Typography
              variant="body1"
              sx={{
                maxWidth: { xs: '100%', md: '65ch' },
                fontSize: { xs: '16px', md: '17px' },
                color: healthForesightColors.neutral.dark,
                lineHeight: 1.8,
              }}
            >
              Confidence bands and uncertainty ranges should be presented alongside point estimates, allowing decision-makers to assess risk and make informed trade-offs. This transparency builds trust and enables more sophisticated policy design.
            </Typography>
          </ScrollReveal>
        </Container>
      </Box>

      {/* Section 7: Implications for Policy Design */}
      <Box
        sx={{
          py: { xs: 8, md: 10 },
          backgroundColor: healthForesightColors.neutral.background,
        }}
      >
        <Container maxWidth="lg">
          <ScrollReveal delay={200}>
            <Typography
              variant="h2"
              sx={{
                fontSize: { xs: '2rem', md: '2.5rem' },
                fontWeight: 700,
                mb: 4,
                color: healthForesightColors.neutral.dark,
              }}
            >
              7. Implications for Policy Design
            </Typography>
            <Typography
              variant="body1"
              sx={{
                maxWidth: { xs: '100%', md: '65ch' },
                fontSize: { xs: '16px', md: '17px' },
                color: healthForesightColors.neutral.dark,
                lineHeight: 1.8,
                mb: 4,
              }}
            >
              Understanding utilization elasticity fundamentally changes how policies should be designed and evaluated. Organizations that measure elasticity accurately can move from static enforcement to adaptive intelligence—adjusting policies based on observed responses, anticipating substitution effects, and designing interventions that account for behavioral realities.
            </Typography>
            <Box sx={{ mb: 4 }}>
              <MaturityCurve />
            </Box>
            <Typography
              variant="body1"
              sx={{
                maxWidth: { xs: '100%', md: '65ch' },
                fontSize: { xs: '16px', md: '17px' },
                color: healthForesightColors.neutral.dark,
                lineHeight: 1.8,
              }}
            >
              This shift from reactive control to strategic governance requires institutional learning, systematic measurement, and decision intelligence platforms that can support evidence-based policy evolution.
            </Typography>
          </ScrollReveal>
        </Container>
      </Box>

      {/* Quantitative Examples */}
      <Box
        sx={{
          py: { xs: 8, md: 10 },
          backgroundColor: '#FFFFFF',
        }}
      >
        <Container maxWidth="lg">
          <ScrollReveal delay={200}>
            <Typography
              variant="h2"
              sx={{
                fontSize: { xs: '2rem', md: '2.5rem' },
                fontWeight: 700,
                mb: 4,
                color: healthForesightColors.neutral.dark,
              }}
            >
              Quantitative Examples
            </Typography>

            {/* Table 1: Naïve vs System-level Impact */}
            <Box sx={{ mb: 6 }}>
              <Typography
                variant="h3"
                sx={{
                  fontSize: { xs: '1.5rem', md: '1.75rem' },
                  fontWeight: 600,
                  mb: 2,
                  color: healthForesightColors.neutral.dark,
                }}
              >
                Naïve vs System-Level Impact
              </Typography>
              <Paper sx={{ overflow: 'hidden' }}>
                <Table>
                  <TableHead>
                    <TableRow sx={{ backgroundColor: healthForesightColors.neutral.background }}>
                      <TableCell sx={{ fontWeight: 700 }}>Policy Type</TableCell>
                      <TableCell align="right" sx={{ fontWeight: 700 }}>Naïve Impact</TableCell>
                      <TableCell align="right" sx={{ fontWeight: 700 }}>Substitution Effect</TableCell>
                      <TableCell align="right" sx={{ fontWeight: 700, color: healthForesightColors.primary.main }}>
                        Net Impact
                      </TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    <TableRow>
                      <TableCell>Prior Authorization (Imaging)</TableCell>
                      <TableCell align="right">-15%</TableCell>
                      <TableCell align="right">+8%</TableCell>
                      <TableCell align="right" sx={{ fontWeight: 700, color: healthForesightColors.primary.main }}>
                        -7%
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Site-of-Care Restriction</TableCell>
                      <TableCell align="right">-12%</TableCell>
                      <TableCell align="right">+6%</TableCell>
                      <TableCell align="right" sx={{ fontWeight: 700, color: healthForesightColors.primary.main }}>
                        -6%
                      </TableCell>
                    </TableRow>
                    <TableRow sx={{ backgroundColor: healthForesightColors.neutral.background }}>
                      <TableCell sx={{ fontWeight: 600 }}>Average</TableCell>
                      <TableCell align="right" sx={{ fontWeight: 600 }}>-13.5%</TableCell>
                      <TableCell align="right" sx={{ fontWeight: 600 }}>+7%</TableCell>
                      <TableCell align="right" sx={{ fontWeight: 700, color: healthForesightColors.primary.main }}>
                        -6.5%
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </Paper>
            </Box>

            {/* Table 2: Provider Segment Classification */}
            <Box sx={{ mb: 6 }}>
              <Typography
                variant="h3"
                sx={{
                  fontSize: { xs: '1.5rem', md: '1.75rem' },
                  fontWeight: 600,
                  mb: 2,
                  color: healthForesightColors.neutral.dark,
                }}
              >
                Provider Segment Classification
              </Typography>
              <Paper sx={{ overflow: 'hidden' }}>
                <Table>
                  <TableHead>
                    <TableRow sx={{ backgroundColor: healthForesightColors.neutral.background }}>
                      <TableCell sx={{ fontWeight: 700 }}>Segment</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Behavioral Response</TableCell>
                      <TableCell align="right" sx={{ fontWeight: 700 }}>Elasticity Range</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    <TableRow>
                      <TableCell>High Compliance</TableCell>
                      <TableCell>Follows policy guidelines with minimal adaptation</TableCell>
                      <TableCell align="right">-0.8 to -1.2</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Adaptive</TableCell>
                      <TableCell>Modifies coding, sequencing, or site selection</TableCell>
                      <TableCell align="right">-0.3 to -0.7</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Resistant</TableCell>
                      <TableCell>Minimal change, may increase utilization elsewhere</TableCell>
                      <TableCell align="right">-0.1 to +0.2</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </Paper>
            </Box>
          </ScrollReveal>
        </Container>
      </Box>

      {/* Technical Appendix */}
      <Box
        sx={{
          py: { xs: 8, md: 10 },
          backgroundColor: healthForesightColors.neutral.background,
        }}
      >
        <Container maxWidth="lg">
          <Accordion
            expanded={appendixExpanded}
            onChange={() => setAppendixExpanded(!appendixExpanded)}
            sx={{
              backgroundColor: '#FFFFFF',
              boxShadow: 'none',
              border: `1px solid ${healthForesightColors.neutral.light}`,
            }}
          >
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Typography
                variant="h3"
                sx={{
                  fontSize: { xs: '1.5rem', md: '1.75rem' },
                  fontWeight: 600,
                  color: healthForesightColors.neutral.dark,
                }}
              >
                Technical Appendix
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Box sx={{ fontFamily: 'monospace', fontSize: '14px', lineHeight: 1.8 }}>
                <Typography variant="h4" sx={{ mb: 3, fontWeight: 700 }}>
                  Mathematical Framework
                </Typography>
                <Typography variant="body1" sx={{ mb: 2, fontFamily: 'inherit' }}>
                  <strong>Naïve Elasticity:</strong>
                </Typography>
                <Box
                  component="pre"
                  sx={{
                    p: 2,
                    backgroundColor: healthForesightColors.neutral.background,
                    borderRadius: 1,
                    mb: 3,
                    overflow: 'auto',
                  }}
                >
                  {`E_naive = (ΔQ / Q) / (ΔP / P)

Where:
  Q = Utilization quantity
  P = Policy intervention intensity
  ΔQ = Change in utilization
  ΔP = Change in policy intensity`}
                </Box>
                <Typography variant="body1" sx={{ mb: 2, fontFamily: 'inherit' }}>
                  <strong>System-Level Elasticity:</strong>
                </Typography>
                <Box
                  component="pre"
                  sx={{
                    p: 2,
                    backgroundColor: healthForesightColors.neutral.background,
                    borderRadius: 1,
                    mb: 3,
                    overflow: 'auto',
                  }}
                >
                  {`E_system = E_naive + Σ(E_substitution_i)

Where:
  E_substitution_i = Elasticity from substitution to setting i
  Σ = Sum across all substitution pathways`}
                </Box>
                <Typography variant="body1" sx={{ mb: 2, fontFamily: 'inherit' }}>
                  <strong>Counterfactual Baseline:</strong>
                </Typography>
                <Box
                  component="pre"
                  sx={{
                    p: 2,
                    backgroundColor: healthForesightColors.neutral.background,
                    borderRadius: 1,
                    mb: 3,
                    overflow: 'auto',
                  }}
                >
                  {`Q_counterfactual(t) = f(Q_historical, trends, seasonality, confounders)

Estimated using:
  - Difference-in-differences
  - Synthetic control methods
  - Regression discontinuity
  - Propensity score matching`}
                </Box>
              </Box>
            </AccordionDetails>
          </Accordion>
        </Container>
      </Box>

      {/* References */}
      <Box
        sx={{
          py: { xs: 8, md: 10 },
          backgroundColor: '#FFFFFF',
        }}
      >
        <Container maxWidth="lg">
          <ScrollReveal delay={200}>
            <Typography
              variant="h2"
              sx={{
                fontSize: { xs: '2rem', md: '2.5rem' },
                fontWeight: 700,
                mb: 4,
                color: healthForesightColors.neutral.dark,
              }}
            >
              References
            </Typography>
            <Box component="ol" sx={{ pl: 3, listStyle: 'decimal' }}>
              {[
                'RAND Corporation. "The Elasticity of Healthcare Utilization: Evidence from Policy Interventions." Health Affairs, 2023.',
                'CMS Office of the Actuary. "Medical Cost Trend Drivers: Utilization vs Price." CMS Research Brief, 2022.',
                'Milliman. "Substitution Effects in Utilization Management: A Quantitative Analysis." Milliman Research Report, 2023.',
                'Health Affairs. "Behavioral Responses to Prior Authorization: Provider and Patient Adaptation Patterns." Health Affairs, 2022.',
              ].map((ref, idx) => (
                <Box
                  key={idx}
                  component="li"
                  sx={{
                    mb: 2,
                    fontSize: { xs: '15px', md: '16px' },
                    color: healthForesightColors.neutral.dark,
                    lineHeight: 1.7,
                  }}
                >
                  {ref}
                </Box>
              ))}
            </Box>
          </ScrollReveal>
        </Container>
      </Box>

      {/* CTA Section */}
      <Box
        sx={{
          py: { xs: 8, md: 10 },
          backgroundColor: healthForesightColors.neutral.dark,
          color: '#FFFFFF',
        }}
      >
        <Container maxWidth="md">
          <ScrollReveal delay={200}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography
                variant="h3"
                sx={{
                  fontSize: { xs: '1.75rem', md: '2.25rem' },
                  fontWeight: 700,
                  mb: 3,
                  color: '#FFFFFF',
                }}
              >
                Download Full Whitepaper
              </Typography>
              <Typography
                variant="body1"
                sx={{
                  fontSize: { xs: '16px', md: '17px' },
                  color: 'rgba(255, 255, 255, 0.9)',
                  mb: 4,
                  lineHeight: 1.7,
                }}
              >
                Get the complete research document with detailed methodology, extended case studies, and additional quantitative analysis.
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
                <Button
                  variant="contained"
                  size="large"
                  startIcon={<Download />}
                  sx={{
                    px: 4,
                    py: 1.5,
                    fontSize: '16px',
                    fontWeight: 600,
                    backgroundColor: healthForesightColors.primary.main,
                    '&:hover': {
                      backgroundColor: healthForesightColors.primary.light,
                    },
                  }}
                >
                  Download PDF
                </Button>
                <Button
                  variant="outlined"
                  size="large"
                  startIcon={<Email />}
                  onClick={() => navigate('/request-demo')}
                  sx={{
                    px: 4,
                    py: 1.5,
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
                  Talk to Us About Policy Elasticity
                </Button>
              </Box>
            </Box>
          </ScrollReveal>
        </Container>
      </Box>
    </Box>
  )
}
