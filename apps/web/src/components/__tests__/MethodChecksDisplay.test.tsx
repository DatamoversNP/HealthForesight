/**
 * Method Checks Display Component Tests
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import MethodChecksDisplay from '../MethodChecksDisplay'
import { mockMethodChecks } from '../../test/mockData'

describe('MethodChecksDisplay', () => {
  it('renders pre-trends check with PASS status', () => {
    render(<MethodChecksDisplay methodChecks={mockMethodChecks} />)
    
    expect(screen.getByText('Pre-Trends Diagnostic')).toBeInTheDocument()
    expect(screen.getByText('Parallel Trends: PASS')).toBeInTheDocument()
    expect(screen.getByText(/Treatment Group Trend/)).toBeInTheDocument()
    expect(screen.getByText(/Control Group Trend/)).toBeInTheDocument()
  })

  it('displays control balance information', () => {
    render(<MethodChecksDisplay methodChecks={mockMethodChecks} />)
    
    expect(screen.getByText('Control Group Balance')).toBeInTheDocument()
    expect(screen.getByText(/Balance Score/)).toBeInTheDocument()
    expect(screen.getByText(/Standardized Mean Difference/)).toBeInTheDocument()
  })

  it('displays seasonality check', () => {
    render(<MethodChecksDisplay methodChecks={mockMethodChecks} />)
    
    expect(screen.getByText('Seasonality Diagnostic')).toBeInTheDocument()
    expect(screen.getByText(/Risk: LOW/)).toBeInTheDocument()
    expect(screen.getByText(/Seasonal Pattern Detected/)).toBeInTheDocument()
  })

  it('displays sample size adequacy', () => {
    render(<MethodChecksDisplay methodChecks={mockMethodChecks} />)
    
    expect(screen.getByText('Sample Size Adequacy')).toBeInTheDocument()
    expect(screen.getByText(/Actual Sample Size/)).toBeInTheDocument()
    expect(screen.getByText(/50,000/)).toBeInTheDocument()
  })

  it('handles missing data gracefully', () => {
    const emptyChecks = { method_checks: {} }
    render(<MethodChecksDisplay methodChecks={emptyChecks} />)
    
    // Should still render the component structure
    expect(screen.getByText('Pre-Trends Diagnostic')).toBeInTheDocument()
  })
})

