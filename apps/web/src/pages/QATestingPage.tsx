import React, { useState } from 'react'
import {
  Box,
  Container,
  Typography,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Alert,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
} from '@mui/material'
import {
  PlayArrow as PlayIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
} from '@mui/icons-material'
import { runQATests, QATestSuite, QA_USERS } from '../utils/qa-testing'

export default function QATestingPage() {
  const [running, setRunning] = useState(false)
  const [results, setResults] = useState<QATestSuite[]>([])
  const [errors, setErrors] = useState<string[]>([])

  const handleRunTests = async () => {
    setRunning(true)
    setErrors([])
    setResults([])

    try {
      const suites = await runQATests()
      setResults(suites)
    } catch (error: any) {
      setErrors([error.message || String(error)])
    } finally {
      setRunning(false)
    }
  }

  const getStatusColor = (passed: boolean) => {
    return passed ? 'success' : 'error'
  }

  const getStatusIcon = (passed: boolean) => {
    return passed ? <CheckIcon color="success" /> : <ErrorIcon color="error" />
  }

  const totalTests = results.reduce((sum, suite) => sum + suite.summary.total, 0)
  const totalPassed = results.reduce((sum, suite) => sum + suite.summary.passed, 0)
  const totalFailed = results.reduce((sum, suite) => sum + suite.summary.failed, 0)

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          QA Testing Framework
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          Test the platform from different user role perspectives. This will test all workflows,
          check functional issues, technical errors, and console problems.
        </Typography>

        <Box sx={{ mt: 3, display: 'flex', gap: 2, alignItems: 'center' }}>
          <Button
            variant="contained"
            startIcon={running ? <CircularProgress size={20} /> : <PlayIcon />}
            onClick={handleRunTests}
            disabled={running}
            size="large"
          >
            {running ? 'Running Tests...' : 'Run All QA Tests'}
          </Button>

          {results.length > 0 && (
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
              <Chip
                label={`Total: ${totalTests}`}
                color="default"
                variant="outlined"
              />
              <Chip
                label={`Passed: ${totalPassed}`}
                color="success"
                variant="outlined"
              />
              <Chip
                label={`Failed: ${totalFailed}`}
                color="error"
                variant="outlined"
              />
              <Chip
                label={`Pass Rate: ${totalTests > 0 ? ((totalPassed / totalTests) * 100).toFixed(1) : 0}%`}
                color={totalPassed === totalTests ? 'success' : 'warning'}
              />
            </Box>
          )}
        </Box>
      </Box>

      {errors.length > 0 && (
        <Alert severity="error" sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>Errors:</Typography>
          {errors.map((error, idx) => (
            <Typography key={idx} variant="body2">• {error}</Typography>
          ))}
        </Alert>
      )}

      {results.length > 0 && (
        <Box>
          <Typography variant="h5" gutterBottom sx={{ mt: 4, mb: 2 }}>
            Test Results by Role
          </Typography>

          {results.map((suite) => (
            <Accordion key={suite.role} sx={{ mb: 2 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                  <Typography variant="h6" sx={{ flexGrow: 1 }}>
                    {suite.role}
                  </Typography>
                  <Chip
                    label={`${suite.summary.passed}/${suite.summary.total} passed`}
                    color={suite.summary.passed === suite.summary.total ? 'success' : 'error'}
                    size="small"
                  />
                  <Chip
                    label={suite.summary.passRate}
                    color={suite.summary.passed === suite.summary.total ? 'success' : 'warning'}
                    size="small"
                    variant="outlined"
                  />
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Test Name</TableCell>
                        <TableCell align="center">Status</TableCell>
                        <TableCell>Errors</TableCell>
                        <TableCell>Warnings</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {suite.tests.map((test, idx) => (
                        <TableRow key={idx}>
                          <TableCell>{test.testName}</TableCell>
                          <TableCell align="center">
                            {getStatusIcon(test.passed)}
                          </TableCell>
                          <TableCell>
                            {test.errors.length > 0 ? (
                              <Box>
                                {test.errors.map((error, eIdx) => (
                                  <Typography key={eIdx} variant="caption" color="error" display="block">
                                    • {error}
                                  </Typography>
                                ))}
                              </Box>
                            ) : (
                              <Typography variant="caption" color="text.secondary">
                                None
                              </Typography>
                            )}
                          </TableCell>
                          <TableCell>
                            {test.warnings.length > 0 ? (
                              <Box>
                                {test.warnings.map((warning, wIdx) => (
                                  <Typography key={wIdx} variant="caption" color="warning.main" display="block">
                                    • {warning}
                                  </Typography>
                                ))}
                              </Box>
                            ) : (
                              <Typography variant="caption" color="text.secondary">
                                None
                              </Typography>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </AccordionDetails>
            </Accordion>
          ))}
        </Box>
      )}

      <Box sx={{ mt: 4 }}>
        <Typography variant="h5" gutterBottom>
          QA Test Users
        </Typography>
        <TableContainer component={Paper} sx={{ mt: 2 }}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Role</TableCell>
                <TableCell>Email</TableCell>
                <TableCell>User ID</TableCell>
                <TableCell>Roles</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {Object.entries(QA_USERS).map(([roleName, userConfig]) => (
                <TableRow key={roleName}>
                  <TableCell>{roleName}</TableCell>
                  <TableCell>{userConfig.email}</TableCell>
                  <TableCell>{userConfig.userId}</TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                      {userConfig.roles.map((role) => (
                        <Chip key={role} label={role} size="small" />
                      ))}
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
    </Container>
  )
}

