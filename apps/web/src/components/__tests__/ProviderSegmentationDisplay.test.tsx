/**
 * Provider Segmentation Display Component Tests
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import ProviderSegmentationDisplay from '../ProviderSegmentationDisplay'
import { mockSegmentationResults } from '../../test/mockData'

describe('ProviderSegmentationDisplay', () => {
  it('renders clustering quality indicator', () => {
    render(<ProviderSegmentationDisplay segmentationResults={mockSegmentationResults} />)
    
    expect(screen.getByText('Clustering Quality')).toBeInTheDocument()
    expect(screen.getByText('GOOD')).toBeInTheDocument()
    expect(screen.getByText(/Silhouette Score/)).toBeInTheDocument()
  })

  it('displays archetypes overview', () => {
    render(<ProviderSegmentationDisplay segmentationResults={mockSegmentationResults} />)
    
    expect(screen.getByText('Provider Archetypes')).toBeInTheDocument()
    expect(screen.getByText('COMPLIERS')).toBeInTheDocument()
    expect(screen.getByText('CIRCUMVENTERS')).toBeInTheDocument()
  })

  it('displays provider assignments table', () => {
    render(<ProviderSegmentationDisplay segmentationResults={mockSegmentationResults} />)
    
    expect(screen.getByText('Provider Assignments')).toBeInTheDocument()
    expect(screen.getByText('PROV-001')).toBeInTheDocument()
    expect(screen.getByText('PROV-002')).toBeInTheDocument()
  })

  it('handles empty results', () => {
    const emptyResults = { archetypes: [], provider_assignments: [], total_providers: 0 }
    render(<ProviderSegmentationDisplay segmentationResults={emptyResults} />)
    
    expect(screen.getByText(/No provider assignments available/)).toBeInTheDocument()
  })
})

