/**
 * Substitution Results Display Component Tests
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import SubstitutionResultsDisplay from '../SubstitutionResultsDisplay'
import { mockSubstitutionResults } from '../../test/mockData'

describe('SubstitutionResultsDisplay', () => {
  it('renders substitution results table', () => {
    render(<SubstitutionResultsDisplay substitutionResults={mockSubstitutionResults} />)
    
    expect(screen.getByText('Total Substitutions Detected')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.getByText('High Confidence')).toBeInTheDocument()
  })

  it('displays top pathways', () => {
    render(<SubstitutionResultsDisplay substitutionResults={mockSubstitutionResults} />)
    
    expect(screen.getByText('Top Substitution Pathways')).toBeInTheDocument()
    expect(screen.getByText('70551')).toBeInTheDocument()
    expect(screen.getByText('70450')).toBeInTheDocument()
  })

  it('displays filter and sort controls', () => {
    render(<SubstitutionResultsDisplay substitutionResults={mockSubstitutionResults} />)
    
    expect(screen.getByLabelText(/Filter by Classification/)).toBeInTheDocument()
    expect(screen.getByLabelText(/Sort By/)).toBeInTheDocument()
  })

  it('handles empty results', () => {
    const emptyResults = { substitutions: [], total_substitutions_detected: 0 }
    render(<SubstitutionResultsDisplay substitutionResults={emptyResults} />)
    
    expect(screen.getByText(/No substitutions detected/)).toBeInTheDocument()
  })
})

