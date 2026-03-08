/**
 * Request Demo Page - Executive-Friendly Form
 * Simple, professional demo request form
 */
import React, { useState } from 'react'
import {
  Box,
  Container,
  Typography,
  Button,
  TextField,
  Grid,
  MenuItem,
  Alert,
} from '@mui/material'
import { healthForesightColors } from '../../theme/healthForesightTheme'

export default function RequestDemoPage() {
  const [formData, setFormData] = useState({
    name: '',
    role: '',
    organization: '',
    useCase: '',
    email: '',
  })
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState('')

  const useCases = [
    'Utilization Policy Impact',
    'Cost & Budget Predictability',
    'Behavioral Intelligence',
    'Strategic Planning',
    'Other',
  ]

  const handleChange = (field: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [field]: event.target.value })
    setError('')
  }

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault()
    
    // Basic validation
    if (!formData.name || !formData.email || !formData.organization) {
      setError('Please fill in all required fields.')
      return
    }

    // In a real implementation, this would send to an API
    console.log('Demo request submitted:', formData)
    setSubmitted(true)
  }

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
        <Container maxWidth="md">
          <Typography
            variant="h1"
            sx={{
              fontSize: { xs: '2.5rem', md: '3.5rem' },
              fontWeight: 700,
              mb: 3,
              textAlign: 'center',
            }}
          >
            See HealthForesight in action
          </Typography>
          <Typography
            variant="h6"
            sx={{
              fontSize: { xs: '1.1rem', md: '1.25rem' },
              fontWeight: 400,
              color: healthForesightColors.neutral.mid,
              textAlign: 'center',
              lineHeight: 1.6,
            }}
          >
            Schedule a conversation with our team to see how HealthForesight can transform your
            utilization management.
          </Typography>
        </Container>
      </Box>

      {/* Form */}
      <Box sx={{ py: { xs: 8, md: 12 }, backgroundColor: healthForesightColors.neutral.background }}>
        <Container maxWidth="sm">
          {submitted ? (
            <Box
              sx={{
                backgroundColor: '#FFFFFF',
                borderRadius: 2,
                p: 6,
                textAlign: 'center',
                border: `1px solid ${healthForesightColors.neutral.light}`,
              }}
            >
              <Typography variant="h5" sx={{ fontWeight: 600, mb: 2, color: healthForesightColors.primary.main }}>
                Thank you for your interest
              </Typography>
              <Typography variant="body1" sx={{ color: healthForesightColors.neutral.mid, mb: 4 }}>
                We've received your request and will contact you shortly to schedule a demo.
              </Typography>
              <Button
                variant="outlined"
                onClick={() => {
                  setSubmitted(false)
                  setFormData({
                    name: '',
                    role: '',
                    organization: '',
                    useCase: '',
                    email: '',
                  })
                }}
                sx={{
                  minHeight: 44,
                  px: { xs: 3, md: 4 },
                  py: { xs: 1.5, md: 1 },
                  fontSize: { xs: '14px', md: '16px' },
                }}
              >
                Submit Another Request
              </Button>
            </Box>
          ) : (
            <Box
              component="form"
              onSubmit={handleSubmit}
              sx={{
                backgroundColor: '#FFFFFF',
                borderRadius: 2,
                p: 6,
                border: `1px solid ${healthForesightColors.neutral.light}`,
              }}
            >
              {error && (
                <Alert severity="error" sx={{ mb: 3 }}>
                  {error}
                </Alert>
              )}

              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    required
                    label="Name"
                    value={formData.name}
                    onChange={handleChange('name')}
                    variant="outlined"
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Role"
                    value={formData.role}
                    onChange={handleChange('role')}
                    variant="outlined"
                    placeholder="e.g., VP of Utilization Management"
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    required
                    label="Organization"
                    value={formData.organization}
                    onChange={handleChange('organization')}
                    variant="outlined"
                    placeholder="Your health plan or organization"
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    required
                    type="email"
                    label="Email"
                    value={formData.email}
                    onChange={handleChange('email')}
                    variant="outlined"
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    select
                    label="Use Case Interest"
                    value={formData.useCase}
                    onChange={handleChange('useCase')}
                    variant="outlined"
                  >
                    {useCases.map((useCase) => (
                      <MenuItem key={useCase} value={useCase}>
                        {useCase}
                      </MenuItem>
                    ))}
                  </TextField>
                </Grid>
                <Grid item xs={12}>
                  <Button
                    type="submit"
                    variant="contained"
                    fullWidth
                    size="large"
                    sx={{
                      minHeight: 44,
                      py: { xs: 1.5, md: 1.5 },
                      fontSize: { xs: '14px', md: '16px' },
                      fontWeight: 500,
                    }}
                  >
                    Schedule a conversation
                  </Button>
                </Grid>
              </Grid>
            </Box>
          )}
        </Container>
      </Box>

      {/* Additional Info */}
      <Box sx={{ py: { xs: 6, md: 8 }, backgroundColor: '#FFFFFF' }}>
        <Container maxWidth="md">
          <Box sx={{ textAlign: 'center' }}>
            <Typography
              variant="body1"
              sx={{
                color: healthForesightColors.neutral.mid,
                mb: 2,
              }}
            >
              Questions? Contact us directly at{' '}
              <Box
                component="span"
                sx={{ color: healthForesightColors.primary.main, fontWeight: 500 }}
              >
                info@healthforesight.com
              </Box>
            </Typography>
            <Typography variant="body2" sx={{ color: healthForesightColors.neutral.mid }}>
              We typically respond within one business day.
            </Typography>
          </Box>
        </Container>
      </Box>
    </Box>
  )
}
