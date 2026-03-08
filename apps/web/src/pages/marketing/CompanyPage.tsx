/**
 * Company Page - About HealthForesight
 * Company narrative, values, and trust signals
 */
import React from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Container,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
} from '@mui/material'
import {
  Security,
  VerifiedUser,
  Business,
  CheckCircle,
} from '@mui/icons-material'
import { healthForesightColors } from '../../theme/healthForesightTheme'

export default function CompanyPage() {
  const navigate = useNavigate()

  const values = [
    {
      title: 'Accountability',
      description: 'We believe in measurable outcomes and transparent attribution of policy impact.',
    },
    {
      title: 'Evidence',
      description: 'Data-driven decisions over intuition. Evidence over assumptions.',
    },
    {
      title: 'Learning Systems',
      description: 'Continuous improvement through feedback loops and elasticity learning.',
    },
  ]

  const trustSignals = [
    {
      icon: <Security sx={{ fontSize: 48, color: healthForesightColors.primary.main }} />,
      title: 'HIPAA-Ready',
      description: 'Built with healthcare data privacy and security requirements in mind.',
    },
    {
      icon: <VerifiedUser sx={{ fontSize: 48, color: healthForesightColors.accent.main }} />,
      title: 'Enterprise-Grade Security',
      description: 'Enterprise security standards and compliance frameworks.',
    },
    {
      icon: <Business sx={{ fontSize: 48, color: healthForesightColors.primary.main }} />,
      title: 'Built for Payers',
      description: 'Designed specifically for health plans and utilization management teams.',
    },
  ]

  return (
    <Box>
      {/* Hero */}
      <Box
        sx={{
          backgroundColor: '#FFFFFF',
          pt: { xs: 8, md: 12 },
          pb: { xs: 6, md: 8 },
          borderBottom: `1px solid ${healthForesightColors.neutral.light}`,
        }}
      >
        <Container maxWidth="xl">
          <Typography
            variant="h1"
            sx={{
              fontSize: { xs: '2.5rem', md: '3.5rem' },
              fontWeight: 700,
              mb: 3,
              textAlign: 'center',
            }}
          >
            About HealthForesight
          </Typography>
          <Typography
            variant="h6"
            sx={{
              fontSize: { xs: '1.1rem', md: '1.25rem' },
              fontWeight: 400,
              color: healthForesightColors.neutral.mid,
              textAlign: 'center',
              maxWidth: '900px',
              mx: 'auto',
              lineHeight: 1.6,
            }}
          >
            HealthForesight was built to help healthcare organizations move from reactive utilization
            management to evidence-driven decision making.
          </Typography>
        </Container>
      </Box>

      {/* Narrative */}
      <Box sx={{ py: { xs: 8, md: 12 }, backgroundColor: healthForesightColors.neutral.background }}>
        <Container maxWidth="lg">
          <Typography
            variant="h4"
            sx={{
              fontWeight: 600,
              mb: 4,
            }}
          >
            Our Mission
          </Typography>
          <Typography
            variant="body1"
            sx={{
              fontSize: '1.1rem',
              color: healthForesightColors.neutral.dark,
              lineHeight: 1.8,
              mb: 4,
            }}
          >
            Utilization management is one of the most critical levers for controlling medical costs,
            yet payers often lack the intelligence needed to make informed policy decisions. Policy
            impact is frequently unclear, delayed, or misattributed. Substitution and leakage
            undermine savings. Forecasts are unreliable.
          </Typography>
          <Typography
            variant="body1"
            sx={{
              fontSize: '1.1rem',
              color: healthForesightColors.neutral.dark,
              lineHeight: 1.8,
            }}
          >
            HealthForesight addresses this gap by providing decision intelligence for utilization
            policy impact. We help payers predict, measure, and learn the true effects of
            utilization policies — before and after implementation. Our platform enables
            evidence-based policy decisions, improved forecast accuracy, and continuous learning
            from outcomes.
          </Typography>
        </Container>
      </Box>

      {/* Values */}
      <Box sx={{ py: { xs: 8, md: 12 }, backgroundColor: '#FFFFFF' }}>
        <Container maxWidth="xl">
          <Typography
            variant="h3"
            sx={{
              fontWeight: 700,
              mb: 6,
              textAlign: 'center',
            }}
          >
            Our Values
          </Typography>
          <Grid container spacing={4}>
            {values.map((value, index) => (
              <Grid item xs={12} md={4} key={index}>
                <Card
                  sx={{
                    height: '100%',
                    border: `1px solid ${healthForesightColors.neutral.light}`,
                  }}
                >
                  <CardContent sx={{ p: 4 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <CheckCircle
                        sx={{ fontSize: 32, color: healthForesightColors.primary.main, mr: 2 }}
                      />
                      <Typography variant="h5" sx={{ fontWeight: 600 }}>
                        {value.title}
                      </Typography>
                    </Box>
                    <Typography
                      variant="body1"
                      sx={{ color: healthForesightColors.neutral.mid, mt: 2 }}
                    >
                      {value.description}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* Trust Signals */}
      <Box sx={{ py: { xs: 8, md: 12 }, backgroundColor: healthForesightColors.neutral.background }}>
        <Container maxWidth="xl">
          <Typography
            variant="h3"
            sx={{
              fontWeight: 700,
              mb: 6,
              textAlign: 'center',
            }}
          >
            Trust & Security
          </Typography>
          <Grid container spacing={4}>
            {trustSignals.map((signal, index) => (
              <Grid item xs={12} md={4} key={index}>
                <Card
                  sx={{
                    height: '100%',
                    border: `1px solid ${healthForesightColors.neutral.light}`,
                    textAlign: 'center',
                  }}
                >
                  <CardContent sx={{ p: 4 }}>
                    <Box sx={{ mb: 3 }}>{signal.icon}</Box>
                    <Typography variant="h5" sx={{ fontWeight: 600, mb: 2 }}>
                      {signal.title}
                    </Typography>
                    <Typography
                      variant="body1"
                      sx={{ color: healthForesightColors.neutral.mid }}
                    >
                      {signal.description}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* CTA */}
      <Box
        sx={{
          py: { xs: 8, md: 12 },
          backgroundColor: '#FFFFFF',
        }}
      >
        <Container maxWidth="md">
          <Box sx={{ textAlign: 'center' }}>
            <Typography
              variant="h4"
              sx={{
                fontWeight: 600,
                mb: 3,
              }}
            >
              Ready to transform your utilization management?
            </Typography>
            <Button
              variant="contained"
              size="large"
              onClick={() => navigate('/request-demo')}
              sx={{
                minHeight: 44,
                px: { xs: 3, md: 4 },
                py: { xs: 1.5, md: 1.5 },
                fontSize: { xs: '14px', md: '16px' },
                fontWeight: 500,
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
