/**
 * Analysis Workspace Page Integration Tests
 * Tests the complete Phase 1-6 UI workflow
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import AnalysisWorkspacePage from '../AnalysisWorkspacePage'
import { apiClient } from '../../lib/api'
import { mockAnalysis, mockImpactResult, mockTrustPanel, mockMethodChecks, mockSubstitutionResults, mockSegmentationResults } from '../../test/mockData'

// Mock API client
vi.mock('../../lib/api', () => ({
  apiClient: {
    getAnalyses: vi.fn(),
    getPolicies: vi.fn(),
    getAnalysisResults: vi.fn(),
    getAnalysisMethodChecks: vi.fn(),
    getAnalysisTrustPanel: vi.fn(),
    getAnalysisTimeseries: vi.fn(),
    createImpactAnalysis: vi.fn(),
    createCohort: vi.fn(),
  },
}))

// Mock WebSocket hook
vi.mock('../../hooks/useWebSocket', () => ({
  useAnalysisUpdates: vi.fn(() => {}),
}))

const mockApiClient = apiClient as any

describe('AnalysisWorkspacePage - Phase 1-6 Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders analysis workspace with empty state', async () => {
    mockApiClient.getAnalyses.mockResolvedValue([])
    mockApiClient.getPolicies.mockResolvedValue([])

    render(
      <BrowserRouter>
        <AnalysisWorkspacePage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Analysis Workspace')).toBeInTheDocument()
      expect(screen.getByText(/No analyses found/)).toBeInTheDocument()
    })
  })

  it('displays analyses list', async () => {
    mockApiClient.getAnalyses.mockResolvedValue([mockAnalysis])
    mockApiClient.getPolicies.mockResolvedValue([])

    render(
      <BrowserRouter>
        <AnalysisWorkspacePage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(mockAnalysis.policy_id)).toBeInTheDocument()
      expect(screen.getByText('COMPLETED')).toBeInTheDocument()
    })
  })

  it('loads and displays analysis results', async () => {
    mockApiClient.getAnalyses.mockResolvedValue([mockAnalysis])
    mockApiClient.getPolicies.mockResolvedValue([])
    mockApiClient.getAnalysisResults.mockResolvedValue({ impact_result: mockImpactResult })
    mockApiClient.getAnalysisTrustPanel.mockResolvedValue(mockTrustPanel)
    mockApiClient.getAnalysisMethodChecks.mockResolvedValue(mockMethodChecks)
    mockApiClient.getAnalysisTimeseries.mockResolvedValue({ data: [] })

    render(
      <BrowserRouter>
        <AnalysisWorkspacePage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(mockAnalysis.policy_id)).toBeInTheDocument()
    })

    // Click on analysis to view results
    const analysisRow = screen.getByText(mockAnalysis.policy_id).closest('tr')
    if (analysisRow) {
      analysisRow.click()
    }

    await waitFor(() => {
      expect(screen.getByText('Impact Results')).toBeInTheDocument()
      expect(screen.getByText(/Effect Size/)).toBeInTheDocument()
      expect(screen.getByText(/Percent Change/)).toBeInTheDocument()
    })
  })

  it('displays method checks tab', async () => {
    mockApiClient.getAnalyses.mockResolvedValue([mockAnalysis])
    mockApiClient.getPolicies.mockResolvedValue([])
    mockApiClient.getAnalysisResults.mockResolvedValue({ impact_result: mockImpactResult })
    mockApiClient.getAnalysisTrustPanel.mockResolvedValue(mockTrustPanel)
    mockApiClient.getAnalysisMethodChecks.mockResolvedValue(mockMethodChecks)

    render(
      <BrowserRouter>
        <AnalysisWorkspacePage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(mockAnalysis.policy_id)).toBeInTheDocument()
    })

    // Click on analysis
    const analysisRow = screen.getByText(mockAnalysis.policy_id).closest('tr')
    if (analysisRow) {
      analysisRow.click()
    }

    // Click Method Checks tab
    await waitFor(() => {
      const methodChecksTab = screen.getByRole('tab', { name: /Method Checks/i })
      if (methodChecksTab) {
        methodChecksTab.click()
      }
    })

    await waitFor(() => {
      expect(screen.getByText('Pre-Trends Diagnostic')).toBeInTheDocument()
      expect(screen.getByText('Control Group Balance')).toBeInTheDocument()
      expect(screen.getByText('Seasonality Diagnostic')).toBeInTheDocument()
    })
  })

  it('displays substitution results tab for IMPACT analysis', async () => {
    mockApiClient.getAnalyses.mockResolvedValue([mockAnalysis])
    mockApiClient.getPolicies.mockResolvedValue([])
    mockApiClient.getAnalysisResults
      .mockResolvedValueOnce({ impact_result: mockImpactResult }) // Initial load
      .mockResolvedValueOnce(mockSubstitutionResults) // Substitution load
    mockApiClient.getAnalysisTrustPanel.mockResolvedValue(mockTrustPanel)
    mockApiClient.getAnalysisMethodChecks.mockResolvedValue(mockMethodChecks)

    render(
      <BrowserRouter>
        <AnalysisWorkspacePage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(mockAnalysis.policy_id)).toBeInTheDocument()
    })

    // Click on analysis
    const analysisRow = screen.getByText(mockAnalysis.policy_id).closest('tr')
    if (analysisRow) {
      analysisRow.click()
    }

    // Click Substitution tab
    await waitFor(() => {
      const substitutionTab = screen.getByRole('tab', { name: /Substitution/i })
      if (substitutionTab) {
        substitutionTab.click()
      }
    })

    await waitFor(() => {
      expect(screen.getByText(/Total Substitutions Detected/i)).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('displays provider segmentation tab for IMPACT analysis', async () => {
    mockApiClient.getAnalyses.mockResolvedValue([mockAnalysis])
    mockApiClient.getPolicies.mockResolvedValue([])
    mockApiClient.getAnalysisResults
      .mockResolvedValueOnce({ impact_result: mockImpactResult }) // Initial load
      .mockResolvedValueOnce(mockSegmentationResults) // Segmentation load
    mockApiClient.getAnalysisTrustPanel.mockResolvedValue(mockTrustPanel)
    mockApiClient.getAnalysisMethodChecks.mockResolvedValue(mockMethodChecks)

    render(
      <BrowserRouter>
        <AnalysisWorkspacePage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(mockAnalysis.policy_id)).toBeInTheDocument()
    })

    // Click on analysis
    const analysisRow = screen.getByText(mockAnalysis.policy_id).closest('tr')
    if (analysisRow) {
      analysisRow.click()
    }

    // Click Provider Segmentation tab
    await waitFor(() => {
      const segmentationTab = screen.getByRole('tab', { name: /Provider Segmentation/i })
      if (segmentationTab) {
        segmentationTab.click()
      }
    })

    await waitFor(() => {
      expect(screen.getByText(/Clustering Quality/i)).toBeInTheDocument()
      expect(screen.getByText(/Provider Archetypes/i)).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('displays trust panel with confidence score', async () => {
    mockApiClient.getAnalyses.mockResolvedValue([mockAnalysis])
    mockApiClient.getPolicies.mockResolvedValue([])
    mockApiClient.getAnalysisResults.mockResolvedValue({ impact_result: mockImpactResult })
    mockApiClient.getAnalysisTrustPanel.mockResolvedValue(mockTrustPanel)
    mockApiClient.getAnalysisMethodChecks.mockResolvedValue(mockMethodChecks)

    render(
      <BrowserRouter>
        <AnalysisWorkspacePage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(mockAnalysis.policy_id)).toBeInTheDocument()
    })

    // Click on analysis
    const analysisRow = screen.getByText(mockAnalysis.policy_id).closest('tr')
    if (analysisRow) {
      analysisRow.click()
    }

    await waitFor(() => {
      expect(screen.getByText(/Trust & Confidence/i)).toBeInTheDocument()
      expect(screen.getByText(/Confidence Score/i)).toBeInTheDocument()
      expect(screen.getByText(/85/)).toBeInTheDocument() // Confidence score from mockTrustPanel
    })
  })
})

