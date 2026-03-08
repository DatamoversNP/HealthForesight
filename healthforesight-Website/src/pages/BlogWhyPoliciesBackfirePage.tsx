/**
 * Blog Page: Why Utilization Policies Backfire
 * Production-ready enterprise blog for healthcare policy intelligence platform
 * Executive audience: payer executives, actuaries, medical economics teams
 */
import React from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Container,
  Typography,
  Divider,
  Paper,
} from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'
import ScrollReveal from '../components/ScrollReveal'
import UtilizationParadoxVisual from '../components/UtilizationParadoxVisual'
import ClassicalVsHealthcareDemandVisual from '../components/ClassicalVsHealthcareDemandVisual'
import ProviderResponseCards from '../components/ProviderResponseCards'
import PatientJourneyTimeline from '../components/PatientJourneyTimeline'
import ShortTermVsLongTermChart from '../components/ShortTermVsLongTermChart'
import BackfireHeatMap from '../components/BackfireHeatMap'
import PolicyIntelligenceMaturityCurve from '../components/PolicyIntelligenceMaturityCurve'

export default function BlogWhyPoliciesBackfirePage() {
  const navigate = useNavigate()

  return (
    <Box sx={{ backgroundColor: '#FFFFFF' }}>
      {/* Hero Section */}
      <Box
        sx={{
          py: { xs: 8, md: 10 },
          backgroundColor: '#FFFFFF',
          borderBottom: `1px solid ${healthForesightColors.neutral.light}`,
        }}
      >
        <Container maxWidth="md">
          <ScrollReveal delay={0}>
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
              Why Utilization Policies Backfire
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
              Common pitfalls in utilization management — and how to avoid unintended consequences
            </Typography>
            <Divider sx={{ my: 4 }} />
          </ScrollReveal>
        </Container>
      </Box>

      {/* Executive Summary */}
      <Box
        sx={{
          py: { xs: 6, md: 8 },
          backgroundColor: healthForesightColors.neutral.background,
        }}
      >
        <Container maxWidth="md">
          <ScrollReveal delay={200}>
            <Paper
              sx={{
                p: 4,
                backgroundColor: '#FFFFFF',
                border: `2px solid ${healthForesightColors.primary.main}`,
                borderRadius: 2,
              }}
            >
              <Typography
                variant="h3"
                sx={{
                  fontSize: { xs: '1.5rem', md: '1.75rem' },
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
                  maxWidth: { xs: '100%', md: '65ch' },
                  fontSize: { xs: '16px', md: '17px' },
                  color: healthForesightColors.neutral.dark,
                  lineHeight: 1.8,
                  mb: 2,
                }}
              >
                Utilization management policies are designed to reduce unnecessary care and control medical cost growth. Yet in practice, many of these policies fail to deliver sustainable savings — and some increase total cost of care.
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
                The reason is not poor execution. It is misunderstood behavior.
              </Typography>
              <Typography
                variant="body1"
                sx={{
                  maxWidth: { xs: '100%', md: '65ch' },
                  fontSize: { xs: '16px', md: '17px' },
                  color: healthForesightColors.neutral.dark,
                  lineHeight: 1.8,
                }}
              >
                Utilization policies trigger adaptive responses from providers and patients that traditional reporting does not capture. When those responses are ignored, payers overestimate savings, underestimate risk, and misinterpret outcomes.
              </Typography>
            </Paper>
          </ScrollReveal>
        </Container>
      </Box>

      {/* Main Content */}
      <Container maxWidth="md" sx={{ py: { xs: 6, md: 8 } }}>
        {/* Section 1: The Promise and Reality */}
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
            1. The Promise — and Reality — of Utilization Management
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
            Utilization management (UM) has become one of the most widely used levers in healthcare cost control. Prior authorization, site-of-care optimization, benefit design changes, and clinical pathways are now standard across commercial, Medicare Advantage, and Medicaid populations.
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
            On paper, the logic is straightforward:
          </Typography>
          <Box component="ul" sx={{ pl: 3, mb: 3 }}>
            {[
              'Restrict inappropriate utilization',
              'Shift care to lower-cost settings',
              'Reduce medical spend',
            ].map((item, idx) => (
              <Box component="li" key={idx} sx={{ mb: 1.5, fontSize: { xs: '16px', md: '17px' }, lineHeight: 1.8 }}>
                {item}
              </Box>
            ))}
          </Box>
          <Typography
            variant="body1"
            sx={{
              maxWidth: { xs: '100%', md: '65ch' },
              fontSize: { xs: '16px', md: '17px' },
              color: healthForesightColors.neutral.dark,
              lineHeight: 1.8,
              mb: 4,
              fontWeight: 600,
            }}
          >
            The problem is not whether utilization changes — it does. The problem is how and where it changes.
          </Typography>
          <Box sx={{ mb: 6 }}>
            <UtilizationParadoxVisual />
          </Box>
        </ScrollReveal>

        {/* Section 2: Core Misconception */}
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
            2. The Core Misconception: Utilization Is Not a Direct Control Variable
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
            Most utilization policies are evaluated using a simple assumption: If we restrict X, utilization of X will decrease, and costs will fall accordingly. This assumption treats healthcare utilization like consumer demand — responsive, direct, and predictable.
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
            Healthcare does not work this way. Utilization is clinically mediated, provider-driven, behaviorally adaptive, and systemically interconnected. A policy does not act on utilization directly. It acts on behavior, and behavior responds strategically.
          </Typography>
          <Paper
            sx={{
              p: 3,
              mb: 4,
              backgroundColor: healthForesightColors.neutral.background,
              borderLeft: `4px solid ${healthForesightColors.primary.main}`,
            }}
          >
            <Typography
              sx={{
                fontSize: { xs: '16px', md: '17px' },
                color: healthForesightColors.neutral.dark,
                lineHeight: 1.8,
                fontWeight: 600,
              }}
            >
              Key Insight: Utilization policies change decision environments, not demand curves.
            </Typography>
          </Paper>
          <Box sx={{ mb: 6 }}>
            <ClassicalVsHealthcareDemandVisual />
          </Box>
        </ScrollReveal>

        {/* Section 3: Provider Responses */}
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
            3. How Utilization Policies Actually Trigger Behavior
          </Typography>
          <Typography
            variant="h3"
            sx={{
              fontSize: { xs: '1.5rem', md: '1.75rem' },
              fontWeight: 600,
              mb: 3,
              color: healthForesightColors.neutral.dark,
            }}
          >
            3.1 Provider Responses: The First-Order Effect
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
            Providers are the primary agents of utilization change. When a policy is introduced, providers typically respond in one of four ways. These behaviors are rational responses to incentives and constraints — not bad behavior. Critically, adaptation and circumvention often preserve revenue while undermining policy intent.
          </Typography>
          <Box sx={{ mb: 6 }}>
            <ProviderResponseCards />
          </Box>
        </ScrollReveal>

        {/* Section 4: Patient Responses */}
        <ScrollReveal delay={200}>
          <Typography
            variant="h3"
            sx={{
              fontSize: { xs: '1.5rem', md: '1.75rem' },
              fontWeight: 600,
              mb: 3,
              color: healthForesightColors.neutral.dark,
              mt: 6,
            }}
          >
            4. Patient Responses: The Second-Order Effect Most Dashboards Miss
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
            Patients rarely see utilization policies directly, but they feel the effects. Common patient responses include delaying care, seeking alternative providers, substituting services, defaulting to emergency settings, or abandoning care entirely. These behaviors often manifest outside the original service category being measured.
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
            As a result, targeted utilization metrics improve while total cost of care worsens and patient experience declines.
          </Typography>
          <Box sx={{ mb: 6 }}>
            <PatientJourneyTimeline />
          </Box>
        </ScrollReveal>

        {/* Section 5: Why Policies Appear to Work */}
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
            5. Why Policies Appear to "Work" — Until They Don't
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
            Short-term evaluations often show success: 5–15% reduction in targeted services, apparent PMPM savings, and clean pre/post comparisons. But these analyses miss substitution across services, site-of-care shifts, delayed acuity increases, and provider behavioral normalization.
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
            Within 12–24 months, utilization patterns often re-stabilize — sometimes at a higher total cost baseline.
          </Typography>
          <Paper
            sx={{
              p: 3,
              mb: 4,
              backgroundColor: healthForesightColors.amber.main + '15',
              borderLeft: `4px solid ${healthForesightColors.amber.main}`,
            }}
          >
            <Typography
              sx={{
                fontSize: { xs: '16px', md: '17px' },
                color: healthForesightColors.neutral.dark,
                lineHeight: 1.8,
                fontWeight: 600,
              }}
            >
              Key Warning: Short evaluation windows systematically overstate policy effectiveness.
            </Typography>
          </Paper>
          <Box sx={{ mb: 6 }}>
            <ShortTermVsLongTermChart />
          </Box>
        </ScrollReveal>

        {/* Section 6: Common Backfire Modes */}
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
            6. The Most Common Ways Utilization Policies Backfire
          </Typography>
          <Box component="ul" sx={{ pl: 3, mb: 4 }}>
            {[
              'Substitution Instead of Suppression: Reducing one service leads to increased use of another.',
              'Site-of-Care Leakage: Outpatient restrictions push utilization into inpatient or ED settings.',
              'Provider Workarounds: Coding changes preserve volume under different labels.',
              'Delayed Cost Explosion: Deferred care returns as higher-acuity utilization.',
              'Forecasting Failure: Savings assumptions break, budgets miss, confidence erodes.',
            ].map((item, idx) => (
              <Box component="li" key={idx} sx={{ mb: 2, fontSize: { xs: '16px', md: '17px' }, lineHeight: 1.8 }}>
                {item}
              </Box>
            ))}
          </Box>
          <Box sx={{ mb: 6 }}>
            <BackfireHeatMap />
          </Box>
        </ScrollReveal>

        {/* Section 7: Why Traditional Measurement Fails */}
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
            7. Why Traditional Measurement Fails
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
            Most utilization reporting focuses on targeted services, short-term deltas, and aggregate averages. This approach misattributes causality, ignores counterfactuals, and masks behavioral heterogeneity.
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
            Without causal methods and system-wide measurement, payers cannot distinguish true utilization reduction from displacement and deferral.
          </Typography>
          <Paper
            sx={{
              p: 3,
              mb: 4,
              backgroundColor: healthForesightColors.neutral.background,
              borderLeft: `4px solid ${healthForesightColors.accent.main}`,
            }}
          >
            <Typography
              sx={{
                fontSize: { xs: '16px', md: '17px' },
                color: healthForesightColors.neutral.dark,
                lineHeight: 1.8,
                fontWeight: 600,
              }}
            >
              Insight: If you only measure where the policy acts, you will miss where behavior moves.
            </Typography>
          </Paper>
        </ScrollReveal>

        {/* Section 8: High-Performing Organizations */}
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
            8. What High-Performing Organizations Do Differently
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
            Leading payers are shifting from utilization management to policy intelligence. They measure system-wide effects, segment provider behavior, model uncertainty (not just averages), re-evaluate policies continuously, and treat elasticity as contextual, not fixed.
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
            This allows more accurate forecasts, fewer surprises, better provider relationships, and smarter policy design.
          </Typography>
          <Box sx={{ mb: 6 }}>
            <PolicyIntelligenceMaturityCurve />
          </Box>
        </ScrollReveal>

        {/* Section 9: How to Avoid Backfire */}
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
            9. How to Avoid Backfire: Practical Principles
          </Typography>
          <Box component="ul" sx={{ pl: 3, mb: 4 }}>
            {[
              'Design policies expecting adaptation',
              'Measure beyond the targeted service',
              'Segment provider responses',
              'Use causal inference, not pre/post',
              'Model uncertainty explicitly',
              'Monitor continuously, not episodically',
            ].map((item, idx) => (
              <Box component="li" key={idx} sx={{ mb: 2, fontSize: { xs: '16px', md: '17px' }, lineHeight: 1.8 }}>
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
              mb: 4,
              fontStyle: 'italic',
            }}
          >
            These are not academic ideals — they are operational necessities.
          </Typography>
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
              Conclusion: Control Comes from Understanding, Not Restriction
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
              Utilization policies do not fail because they are too weak. They fail because they are too simplistic.
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
              Healthcare utilization is shaped by behavior, incentives, and system dynamics. Policies that ignore this reality create blind spots — and those blind spots become financial risk.
            </Typography>
            <Typography
              variant="body1"
              sx={{
                maxWidth: { xs: '100%', md: '65ch' },
                fontSize: { xs: '16px', md: '17px' },
                color: healthForesightColors.neutral.dark,
                lineHeight: 1.8,
              }}
            >
              Organizations that invest in behavior-aware, causally grounded measurement do not just avoid backfire. They gain a durable advantage in cost control, predictability, and trust.
            </Typography>
          </Box>
        </ScrollReveal>
      </Container>
    </Box>
  )
}
