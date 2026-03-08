/**
 * Insights Page - Thought Leadership
 * Blog posts, whitepapers, and executive briefs
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
  Chip,
} from '@mui/material'
import { Article, Description, MenuBook } from '@mui/icons-material'
import { healthForesightColors } from '../../theme/healthForesightTheme'

export default function InsightsPage() {
  const navigate = useNavigate()

  const insights = [
    {
      type: 'Whitepaper',
      icon: <Description sx={{ fontSize: 32, color: healthForesightColors.primary.main }} />,
      title: 'Measuring Elasticity in Healthcare Utilization',
      description:
        'A comprehensive guide to understanding utilization elasticity and its impact on policy effectiveness.',
      category: 'Research',
    },
    {
      type: 'Blog',
      icon: <Article sx={{ fontSize: 32, color: healthForesightColors.accent.main }} />,
      title: 'Why Utilization Policies Backfire',
      description:
        'Common pitfalls in utilization management and how to avoid unintended consequences.',
      category: 'Strategy',
    },
    {
      type: 'Executive Brief',
      icon: <MenuBook sx={{ fontSize: 32, color: healthForesightColors.primary.main }} />,
      title: 'The Cost of Policy Uncertainty',
      description:
        'How uncertainty in policy impact measurement affects medical cost forecasting and budget planning.',
      category: 'Finance',
    },
    {
      type: 'Blog',
      icon: <Article sx={{ fontSize: 32, color: healthForesightColors.accent.main }} />,
      title: 'From Dashboards to Decisions',
      description:
        'Moving beyond reporting to actionable intelligence in utilization management.',
      category: 'Analytics',
    },
    {
      type: 'Whitepaper',
      icon: <Description sx={{ fontSize: 32, color: healthForesightColors.primary.main }} />,
      title: 'Causal Attribution in Healthcare Policy',
      description:
        'Methods for measuring true policy impact while accounting for confounding factors.',
      category: 'Research',
    },
    {
      type: 'Executive Brief',
      icon: <MenuBook sx={{ fontSize: 32, color: healthForesightColors.accent.main }} />,
      title: 'Substitution and Leakage in Utilization Management',
      description:
        'Understanding how provider and patient behavior changes affect policy outcomes.',
      category: 'Strategy',
    },
  ]

  const categories = ['All', 'Research', 'Strategy', 'Finance', 'Analytics']

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
            Insights & Thought Leadership
          </Typography>
          <Typography
            variant="h6"
            sx={{
              fontSize: { xs: '1.1rem', md: '1.25rem' },
              fontWeight: 400,
              color: healthForesightColors.neutral.mid,
              textAlign: 'center',
              maxWidth: '800px',
              mx: 'auto',
              lineHeight: 1.6,
            }}
          >
            Evidence-based perspectives on utilization management, policy impact measurement, and
            healthcare decision intelligence.
          </Typography>
        </Container>
      </Box>

      {/* Category Filter */}
      <Box
        sx={{
          py: 4,
          backgroundColor: healthForesightColors.neutral.background,
          borderBottom: `1px solid ${healthForesightColors.neutral.light}`,
        }}
      >
        <Container maxWidth="xl">
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
            {categories.map((category) => (
              <Chip
                key={category}
                label={category}
                clickable
                sx={{
                  backgroundColor: category === 'All' ? healthForesightColors.primary.main : '#FFFFFF',
                  color: category === 'All' ? '#FFFFFF' : healthForesightColors.neutral.dark,
                  fontWeight: category === 'All' ? 600 : 400,
                  '&:hover': {
                    backgroundColor:
                      category === 'All'
                        ? healthForesightColors.primary.dark
                        : healthForesightColors.neutral.light,
                  },
                }}
              />
            ))}
          </Box>
        </Container>
      </Box>

      {/* Insights Grid */}
      <Box sx={{ py: { xs: 8, md: 12 }, backgroundColor: '#FFFFFF' }}>
        <Container maxWidth="xl">
          <Grid container spacing={4}>
            {insights.map((insight, index) => (
              <Grid item xs={12} sm={6} md={4} key={index}>
                <Card
                  onClick={() => {
                    if (insight.title === 'Measuring Elasticity in Healthcare Utilization') {
                      navigate('/insights/measuring-elasticity')
                    } else if (insight.title === 'Why Utilization Policies Backfire') {
                      navigate('/insights/why-policies-backfire')
                    } else if (insight.title === 'The Cost of Policy Uncertainty') {
                      navigate('/insights/cost-of-policy-uncertainty')
                    }
                  }}
                  sx={{
                    height: '100%',
                    border: `1px solid ${healthForesightColors.neutral.light}`,
                    cursor: 'pointer',
                    '&:hover': {
                      borderColor: healthForesightColors.primary.main,
                      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
                    },
                    transition: 'all 0.3s ease',
                  }}
                >
                  <CardContent sx={{ p: 3 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      {insight.icon}
                      <Chip
                        label={insight.type}
                        size="small"
                        sx={{
                          ml: 'auto',
                          backgroundColor: healthForesightColors.neutral.background,
                          fontSize: '11px',
                        }}
                      />
                    </Box>
                    <Typography variant="h6" sx={{ fontWeight: 600, mb: 1.5 }}>
                      {insight.title}
                    </Typography>
                    <Typography
                      variant="body2"
                      sx={{ color: healthForesightColors.neutral.mid, mb: 2 }}
                    >
                      {insight.description}
                    </Typography>
                    <Chip
                      label={insight.category}
                      size="small"
                      sx={{
                        backgroundColor: healthForesightColors.accent.main,
                        color: '#FFFFFF',
                        fontSize: '11px',
                      }}
                    />
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
          backgroundColor: healthForesightColors.neutral.background,
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
              Want to learn more about utilization intelligence?
            </Typography>
            <Button
              variant="contained"
              size="large"
              onClick={() => navigate('/request-demo')}
              sx={{
                px: 4,
                py: 1.5,
                fontSize: '16px',
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
