/**
 * Executive Brief: The Cost of Policy Uncertainty
 * Enterprise-grade brief focused on financial risk, forecast error, and governance impact
 * Finance/governance oriented, distinct from blog and whitepaper pages
 */
import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Container,
  Typography,
  Button,
  Paper,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material'
import { ExpandMore, ArrowBack } from '@mui/icons-material'
import { healthForesightColors } from '../theme/healthForesightTheme'
import ScrollReveal from '../components/ScrollReveal'
import ForecastPrecisionVsReality from '../components/ForecastPrecisionVsReality'
import UncertaintyInjectionPoints from '../components/UncertaintyInjectionPoints'
import PointEstimateVsRange from '../components/PointEstimateVsRange'
import DelayedCostEmergence from '../components/DelayedCostEmergence'
import PolicyWhiplashLoop from '../components/PolicyWhiplashLoop'
import StaticVsAdaptivePlanning from '../components/StaticVsAdaptivePlanning'
import QuickSummaryPanel from '../components/QuickSummaryPanel'

export default function ExecutiveBriefCostOfUncertaintyPage() {
  const navigate = useNavigate()
  const [quickSummaryExpanded, setQuickSummaryExpanded] = useState(false)

  const faqs = [
    {
      question: 'What is policy impact uncertainty?',
      answer: 'Policy impact uncertainty refers to the range of possible outcomes when a utilization policy is implemented. Traditional measurement often produces point estimates (e.g., "8% reduction"), but actual results vary due to behavioral adaptation, substitution, and delayed effects. This uncertainty compounds into financial risk when embedded in budgets and forecasts.',
    },
    {
      question: 'Why do point estimates fail in healthcare?',
      answer: 'Point estimates assume stable, predictable responses. Healthcare utilization is behaviorally mediated—providers adapt, patients substitute, and effects emerge over time. These dynamics create variance that point estimates cannot capture, leading to forecast error and budget volatility.',
    },
    {
      question: 'What are second-order effects?',
      answer: 'Second-order effects are delayed, displaced, or indirect consequences of policy interventions. Examples include: care deferred to emergency settings, site-of-care shifts, coding adaptations, and network leakage. These effects often occur outside the originally measured service category and appear months after policy implementation.',
    },
    {
      question: 'How should payers budget with uncertainty?',
      answer: 'Leading organizations budget using range-based scenarios rather than point estimates. They model elasticity as probability distributions, track second-order effects explicitly, and integrate uncertainty into financial planning. This enables dynamic re-forecasting and reduces budget volatility.',
    },
    {
      question: 'How does HealthForesight help?',
      answer: 'HealthForesight measures policy impact using causal inference and behavioral attribution, producing confidence intervals rather than point estimates. The platform tracks substitution, delayed effects, and system-level outcomes, enabling elasticity-aware financial planning and reducing forecast error.',
    },
    {
      question: 'What is the financial impact of policy uncertainty?',
      answer: 'Policy uncertainty translates directly into budget variance. For a 500,000-member plan, a ±30% elasticity variation on a $3.20 PMPM savings assumption can create $6M+ in annual downside risk. This uncertainty compounds across multiple policies and budgeting cycles, creating persistent forecast error and governance strain.',
    },
  ]

  return (
    <Box sx={{ backgroundColor: '#FFFFFF', position: 'relative' }}>
      {/* Breadcrumb */}
      <Container maxWidth="lg" sx={{ pt: 4 }}>
        <Button
          startIcon={<ArrowBack />}
          onClick={() => navigate('/insights')}
          sx={{
            color: healthForesightColors.neutral.mid,
            mb: 2,
            '&:hover': {
              backgroundColor: healthForesightColors.neutral.background,
            },
          }}
        >
          Back to Insights
        </Button>
      </Container>

      {/* Hero Section */}
      <Box
        sx={{
          py: { xs: 6, md: 8 },
          backgroundColor: '#FFFFFF',
          borderBottom: `1px solid ${healthForesightColors.neutral.light}`,
        }}
      >
        <Container maxWidth="lg">
          <Box sx={{ display: 'flex', flexDirection: { xs: 'column', lg: 'row' }, gap: 4 }}>
            <Box sx={{ flex: 1 }}>
              <ScrollReveal delay={0}>
                <Box sx={{ mb: 2 }}>
                  <Typography
                    component="span"
                    sx={{
                      px: 2,
                      py: 0.5,
                      backgroundColor: healthForesightColors.primary.main,
                      color: '#FFFFFF',
                      fontSize: '12px',
                      fontWeight: 700,
                      textTransform: 'uppercase',
                      letterSpacing: '0.1em',
                      display: 'inline-block',
                      mb: 2,
                    }}
                  >
                    Executive Brief
                  </Typography>
                  <Typography
                    component="span"
                    sx={{
                      ml: 2,
                      fontSize: '13px',
                      color: healthForesightColors.neutral.mid,
                    }}
                  >
                    6–8 min read
                  </Typography>
                </Box>
                <Typography
                  variant="h1"
                  sx={{
                    fontSize: { xs: '2.5rem', md: '3.5rem' },
                    fontWeight: 700,
                    mb: 3,
                    color: healthForesightColors.neutral.dark,
                    lineHeight: 1.2,
                    letterSpacing: '-0.02em',
                  }}
                >
                  The Cost of Policy Uncertainty
                </Typography>
                <Typography
                  variant="h5"
                  sx={{
                    fontSize: { xs: '1.1rem', md: '1.25rem' },
                    fontWeight: 400,
                    color: healthForesightColors.neutral.mid,
                    mb: 4,
                    lineHeight: 1.6,
                  }}
                >
                  How uncertainty in policy impact measurement distorts medical cost forecasting, budget planning, and executive decision-making
                </Typography>
                <Typography
                  variant="body1"
                  sx={{
                    fontSize: { xs: '16px', md: '17px' },
                    color: healthForesightColors.neutral.dark,
                    lineHeight: 1.8,
                    maxWidth: '800px',
                  }}
                >
                  Healthcare organizations often budget using point estimates of "policy savings." But behavioral adaptation, substitution, and delayed effects introduce uncertainty that compounds into forecast error, budget volatility, and reactive governance cycles.
                </Typography>
              </ScrollReveal>
            </Box>
            <Box sx={{ flex: { xs: 1, lg: '0 0 400px' } }}>
              <ForecastPrecisionVsReality />
            </Box>
          </Box>
        </Container>
      </Box>

      {/* Main Content with Sticky Sidebar */}
      <Container maxWidth="lg" sx={{ py: { xs: 6, md: 8 } }}>
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', lg: 'row' }, gap: 4 }}>
          {/* Main Content */}
          <Box sx={{ flex: 1, minWidth: 0 }}>
            {/* Executive Summary */}
            <ScrollReveal delay={200}>
              <Paper
                sx={{
                  p: 4,
                  mb: 6,
                  backgroundColor: healthForesightColors.neutral.background,
                  border: `2px solid ${healthForesightColors.primary.main}`,
                  borderRadius: 2,
                }}
              >
                <Typography
                  variant="h2"
                  sx={{
                    fontSize: { xs: '1.75rem', md: '2rem' },
                    fontWeight: 700,
                    mb: 3,
                    color: healthForesightColors.primary.main,
                  }}
                >
                  Executive Summary
                </Typography>
                <Typography
                  variant="body1"
                  sx={{
                    fontSize: { xs: '16px', md: '17px' },
                    color: healthForesightColors.neutral.dark,
                    lineHeight: 1.8,
                    mb: 2,
                  }}
                >
                  Healthcare organizations increasingly rely on utilization management policies to control cost growth. Yet despite sophisticated analytics investments, most payers and providers operate with material uncertainty about whether these policies actually reduce total cost of care.
                </Typography>
                <Typography
                  variant="body1"
                  sx={{
                    fontSize: { xs: '16px', md: '17px' },
                    color: healthForesightColors.neutral.dark,
                    lineHeight: 1.8,
                    mb: 2,
                  }}
                >
                  This uncertainty is not academic. It manifests directly in:
                </Typography>
                <Box component="ul" sx={{ pl: 3, mb: 2 }}>
                  {[
                    'Budget volatility',
                    'Forecast error',
                    'Missed earnings targets',
                    'Reactive policy reversals',
                    'Erosion of provider and member trust',
                  ].map((item, idx) => (
                    <Box component="li" key={idx} sx={{ mb: 1, fontSize: { xs: '16px', md: '17px' }, lineHeight: 1.8 }}>
                      {item}
                    </Box>
                  ))}
                </Box>
                <Typography
                  variant="body1"
                  sx={{
                    fontSize: { xs: '16px', md: '17px' },
                    color: healthForesightColors.neutral.dark,
                    lineHeight: 1.8,
                    mb: 2,
                  }}
                >
                  The core issue is not policy design — it is policy impact uncertainty. Organizations routinely make multi-million-dollar decisions using point estimates of savings that mask behavioral adaptation, substitution, and delayed effects. As a result, financial plans appear sound on paper but fail in execution.
                </Typography>
              </Paper>
            </ScrollReveal>

            {/* Section 1 */}
            <ScrollReveal delay={200}>
              <Typography
                variant="h2"
                sx={{
                  fontSize: { xs: '2rem', md: '2.5rem' },
                  fontWeight: 700,
                  mb: 3,
                  color: healthForesightColors.neutral.dark,
                  mt: 6,
                }}
              >
                1. Where Policy Uncertainty Enters the Financial System
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
                Policy uncertainty is introduced at three critical points:
              </Typography>
              <Typography
                variant="h3"
                sx={{
                  fontSize: { xs: '1.25rem', md: '1.5rem' },
                  fontWeight: 600,
                  mb: 2,
                  color: healthForesightColors.neutral.dark,
                }}
              >
                A. During Savings Attribution
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
                Most utilization policies are evaluated using pre/post comparisons, service-level metrics, and short observation windows. These methods assume stable baseline trends, no substitution, and no behavioral adaptation. None of these assumptions hold in real healthcare systems.
              </Typography>
              <Typography
                variant="h3"
                sx={{
                  fontSize: { xs: '1.25rem', md: '1.5rem' },
                  fontWeight: 600,
                  mb: 2,
                  color: healthForesightColors.neutral.dark,
                }}
              >
                B. During Financial Translation
              </Typography>
              <Typography
                variant="body1"
                sx={{
                  fontSize: { xs: '16px', md: '17px' },
                  color: healthForesightColors.neutral.dark,
                  lineHeight: 1.8,
                  mb: 3,
                }}
              >
                Estimated utilization changes are converted into PMPM assumptions, medical cost trend adjustments, and budget targets. Small errors in elasticity assumptions translate into outsized financial variance at scale.
              </Typography>
              <Typography
                variant="h3"
                sx={{
                  fontSize: { xs: '1.25rem', md: '1.5rem' },
                  fontWeight: 600,
                  mb: 2,
                  color: healthForesightColors.neutral.dark,
                }}
              >
                C. During Budget Lock-In
              </Typography>
              <Typography
                variant="body1"
                sx={{
                  fontSize: { xs: '16px', md: '17px' },
                  color: healthForesightColors.neutral.dark,
                  lineHeight: 1.8,
                  mb: 4,
                }}
              >
                Once embedded into annual budgets, assumptions harden into targets, revisions become politically costly, and uncertainty becomes invisible — but not gone.
              </Typography>
              <Box sx={{ mb: 6 }}>
                <UncertaintyInjectionPoints />
              </Box>
            </ScrollReveal>

            {/* Section 2 */}
            <ScrollReveal delay={200}>
              <Typography
                variant="h2"
                sx={{
                  fontSize: { xs: '2rem', md: '2.5rem' },
                  fontWeight: 700,
                  mb: 3,
                  color: healthForesightColors.neutral.dark,
                  mt: 6,
                }}
              >
                2. Why Traditional Measurement Amplifies Financial Risk
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
                Most organizations rely on point estimates of policy impact. Example: "This policy reduces utilization by 8%" or "Expected PMPM savings: $3.20". What's missing: confidence intervals, downstream effects, and behavioral variability. This creates an illusion of precision.
              </Typography>

              {/* Quantitative Illustration */}
              <Paper
                sx={{
                  p: 4,
                  mb: 4,
                  backgroundColor: healthForesightColors.neutral.background,
                  border: `1px solid ${healthForesightColors.neutral.light}`,
                  borderRadius: 2,
                }}
              >
                <Typography
                  variant="h4"
                  sx={{
                    fontSize: { xs: '1.25rem', md: '1.5rem' },
                    fontWeight: 700,
                    mb: 3,
                    color: healthForesightColors.neutral.dark,
                  }}
                >
                  Quantitative Illustration
                </Typography>
                <Box sx={{ mb: 3 }}>
                  <Typography
                    sx={{
                      fontSize: { xs: '16px', md: '17px' },
                      color: healthForesightColors.neutral.dark,
                      lineHeight: 1.8,
                      mb: 1,
                    }}
                  >
                    <strong>Population:</strong> 500,000 members
                  </Typography>
                  <Typography
                    sx={{
                      fontSize: { xs: '16px', md: '17px' },
                      color: healthForesightColors.neutral.dark,
                      lineHeight: 1.8,
                      mb: 1,
                    }}
                  >
                    <strong>Estimated PMPM savings:</strong> $3.20
                  </Typography>
                  <Typography
                    sx={{
                      fontSize: { xs: '16px', md: '17px' },
                      color: healthForesightColors.neutral.dark,
                      lineHeight: 1.8,
                      mb: 1,
                    }}
                  >
                    <strong>Annual budget impact:</strong> ~$19M
                  </Typography>
                  <Typography
                    sx={{
                      fontSize: { xs: '16px', md: '17px' },
                      color: healthForesightColors.amber.main,
                      lineHeight: 1.8,
                      fontWeight: 600,
                    }}
                  >
                    <strong>If actual elasticity varies by ±30% due to behavior:</strong>
                  </Typography>
                  <Typography
                    sx={{
                      fontSize: { xs: '16px', md: '17px' },
                      color: healthForesightColors.amber.main,
                      lineHeight: 1.8,
                      fontWeight: 700,
                      ml: 2,
                    }}
                  >
                    Downside risk exceeds $6M annually
                  </Typography>
                  <Typography
                    sx={{
                      fontSize: { xs: '16px', md: '17px' },
                      color: healthForesightColors.neutral.mid,
                      lineHeight: 1.8,
                      fontStyle: 'italic',
                      mt: 2,
                    }}
                  >
                    Often discovered after budgets are finalized
                  </Typography>
                </Box>
                <Typography
                  variant="caption"
                  sx={{
                    fontSize: '12px',
                    color: healthForesightColors.neutral.mid,
                    fontStyle: 'italic',
                  }}
                >
                  Assumptions: Single policy intervention, 8% utilization reduction assumption, behavioral elasticity variance ±30%
                </Typography>
              </Paper>

              {/* CFO Lens Callout */}
              <Paper
                sx={{
                  p: 3,
                  mb: 4,
                  backgroundColor: healthForesightColors.primary.main + '15',
                  borderLeft: `4px solid ${healthForesightColors.primary.main}`,
                }}
              >
                <Typography
                  sx={{
                    fontSize: { xs: '16px', md: '17px' },
                    color: healthForesightColors.neutral.dark,
                    lineHeight: 1.8,
                    fontWeight: 600,
                    mb: 1,
                  }}
                >
                  CFO Lens:
                </Typography>
                <Typography
                  sx={{
                    fontSize: { xs: '16px', md: '17px' },
                    color: healthForesightColors.neutral.dark,
                    lineHeight: 1.8,
                  }}
                >
                  "Which number did we budget?" Point estimates create false confidence. Range-based planning acknowledges risk and enables better capital allocation.
                </Typography>
              </Paper>

              <Box sx={{ mb: 6 }}>
                <PointEstimateVsRange />
              </Box>
            </ScrollReveal>

            {/* Section 3 */}
            <ScrollReveal delay={200}>
              <Typography
                variant="h2"
                sx={{
                  fontSize: { xs: '2rem', md: '2.5rem' },
                  fontWeight: 700,
                  mb: 3,
                  color: healthForesightColors.neutral.dark,
                  mt: 6,
                }}
              >
                3. Behavioral Effects Drive Financial Volatility
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
                Utilization policies do not act on utilization directly — they act on decision environments. Behavioral responses introduce timing shifts (delayed care), site-of-care substitution, coding adaptation, emergency fallback, and network leakage.
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
                These effects often occur outside the measured service, appear months later, and bypass utilization dashboards entirely.
              </Typography>
              <Box sx={{ mb: 6 }}>
                <DelayedCostEmergence />
              </Box>
            </ScrollReveal>

            {/* Section 4 */}
            <ScrollReveal delay={200}>
              <Typography
                variant="h2"
                sx={{
                  fontSize: { xs: '2rem', md: '2.5rem' },
                  fontWeight: 700,
                  mb: 3,
                  color: healthForesightColors.neutral.dark,
                  mt: 6,
                }}
              >
                4. The Governance Cost of Uncertainty
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
                Beyond dollars, policy uncertainty creates governance strain: Finance questions analytics credibility, clinical leaders challenge policy intent, executives lose confidence in forecasts, and policy decisions become reactive.
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
                Organizations oscillate between over-restricting utilization, rapid rollbacks, and ad hoc exceptions. This cycle increases operational cost and reputational risk.
              </Typography>
              <Box sx={{ mb: 6 }}>
                <PolicyWhiplashLoop />
              </Box>
            </ScrollReveal>

            {/* Section 5 */}
            <ScrollReveal delay={200}>
              <Typography
                variant="h2"
                sx={{
                  fontSize: { xs: '2rem', md: '2.5rem' },
                  fontWeight: 700,
                  mb: 3,
                  color: healthForesightColors.neutral.dark,
                  mt: 6,
                }}
              >
                5. What Leading Organizations Do Differently
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
                High-performing organizations treat policy impact as a probabilistic system, not a deterministic one. They measure elasticity as ranges (not points), track second-order effects explicitly, attribute behavior (not just outcomes), integrate uncertainty into financial planning, and re-forecast dynamically.
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
                This shifts decision-making from "Did the policy work?" to "Under what conditions does this policy create value?"
              </Typography>
              <Box sx={{ mb: 6 }}>
                <StaticVsAdaptivePlanning />
              </Box>
            </ScrollReveal>

            {/* Conclusion */}
            <ScrollReveal delay={200}>
              <Box
                sx={{
                  mt: 8,
                  mb: 6,
                  p: 4,
                  backgroundColor: healthForesightColors.neutral.background,
                  borderRadius: 2,
                  border: `1px solid ${healthForesightColors.neutral.light}`,
                }}
              >
                <Typography
                  variant="h2"
                  sx={{
                    fontSize: { xs: '1.75rem', md: '2rem' },
                    fontWeight: 700,
                    mb: 3,
                    color: healthForesightColors.neutral.dark,
                  }}
                >
                  Conclusion: From Cost Control to Financial Confidence
                </Typography>
                <Typography
                  variant="body1"
                  sx={{
                    maxWidth: { xs: '100%', md: '65ch' },
                    fontSize: { xs: '16px', md: '17px' },
                    color: healthForesightColors.neutral.dark,
                    lineHeight: 1.8,
                    mb: 2,
                  }}
                >
                  Policy uncertainty is not a data problem — it is a measurement philosophy problem.
                </Typography>
                <Typography
                  variant="body1"
                  sx={{
                    maxWidth: { xs: '100%', md: '65ch' },
                    fontSize: { xs: '16px', md: '17px' },
                    color: healthForesightColors.neutral.dark,
                    lineHeight: 1.8,
                    mb: 2,
                  }}
                >
                  Organizations that continue to rely on simplified policy impact estimates will experience persistent forecast error, budget volatility, and strategic blind spots. Those that adopt elasticity-aware, behavior-informed measurement gain predictable financial outcomes, stronger governance, and more durable policy strategies.
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
                  The question is no longer whether uncertainty exists — but whether it is acknowledged, measured, and managed.
                </Typography>
              </Box>

              {/* Investor Lens Callout */}
              <Paper
                sx={{
                  p: 3,
                  mb: 6,
                  backgroundColor: healthForesightColors.accent.main + '15',
                  borderLeft: `4px solid ${healthForesightColors.accent.main}`,
                }}
              >
                <Typography
                  variant="h4"
                  sx={{
                    fontSize: { xs: '1.25rem', md: '1.5rem' },
                    fontWeight: 700,
                    mb: 2,
                    color: healthForesightColors.neutral.dark,
                  }}
                >
                  Investor Lens: Reducing policy uncertainty is a financial advantage.
                </Typography>
                <Box component="ul" sx={{ pl: 3, m: 0 }}>
                  {[
                    'Lower forecast error',
                    'Faster policy learning cycles',
                    'Higher confidence capital allocation',
                  ].map((item, idx) => (
                    <Box component="li" key={idx} sx={{ mb: 1, fontSize: { xs: '16px', md: '17px' }, lineHeight: 1.8 }}>
                      {item}
                    </Box>
                  ))}
                </Box>
              </Paper>
            </ScrollReveal>

            {/* FAQ Section */}
            <ScrollReveal delay={200}>
              <Typography
                variant="h2"
                sx={{
                  fontSize: { xs: '2rem', md: '2.5rem' },
                  fontWeight: 700,
                  mb: 4,
                  color: healthForesightColors.neutral.dark,
                  mt: 6,
                }}
              >
                Frequently Asked Questions
              </Typography>
              {faqs.map((faq, idx) => (
                <Accordion
                  key={idx}
                  sx={{
                    mb: 2,
                    border: `1px solid ${healthForesightColors.neutral.light}`,
                    '&:before': { display: 'none' },
                  }}
                >
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Typography
                      sx={{
                        fontSize: { xs: '16px', md: '17px' },
                        fontWeight: 600,
                        color: healthForesightColors.neutral.dark,
                      }}
                    >
                      {faq.question}
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Typography
                      sx={{
                        fontSize: { xs: '16px', md: '17px' },
                        color: healthForesightColors.neutral.dark,
                        lineHeight: 1.8,
                      }}
                    >
                      {faq.answer}
                    </Typography>
                  </AccordionDetails>
                </Accordion>
              ))}
            </ScrollReveal>
          </Box>

          {/* Sticky Quick Summary Panel */}
          <Box
            sx={{
              flex: { xs: 1, lg: '0 0 320px' },
              position: { lg: 'sticky' },
              top: { lg: 100 },
              height: { lg: 'fit-content' },
              maxHeight: { lg: 'calc(100vh - 120px)' },
              alignSelf: { lg: 'flex-start' },
            }}
          >
            <QuickSummaryPanel />
          </Box>
        </Box>
      </Container>

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
                Turn policy uncertainty into financial confidence.
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
                    },
                  }}
                >
                  Request a Demo
                </Button>
                <Button
                  variant="outlined"
                  size="large"
                  onClick={() => navigate('/request-demo')}
                  sx={{
                    minHeight: 44,
                    px: { xs: 3, md: 4 },
                    py: { xs: 1.5, md: 1.5 },
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
                  Talk to an Expert
                </Button>
              </Box>
              <Typography
                variant="body2"
                sx={{
                  fontSize: '13px',
                  color: 'rgba(255, 255, 255, 0.8)',
                }}
              >
                Trusted by leading healthcare payers and risk-bearing providers
              </Typography>
            </Box>
          </ScrollReveal>
        </Container>
      </Box>

      {/* JSON-LD Schema for FAQ */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'FAQPage',
            mainEntity: faqs.map((faq) => ({
              '@type': 'Question',
              name: faq.question,
              acceptedAnswer: {
                '@type': 'Answer',
                text: faq.answer,
              },
            })),
          }),
        }}
      />
    </Box>
  )
}
