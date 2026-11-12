import { mkdirSync, writeFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ThemeProvider, createTheme } from '@mui/material'
import ObservationVerdict from '../../components/ObservationVerdict'
import ScenarioComparison from '../../components/ScenarioComparison'
import { costRollupPresentation, utilizationRollupPresentation } from '../dashboardRollup'

vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  BarChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Bar: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  Legend: () => null,
}))

const theme = createTheme()

function renderWithTheme(node: React.ReactElement) {
  return render(<ThemeProvider theme={theme}>{node}</ThemeProvider>)
}

describe('observation screen verdict', () => {
  it('shows the recomputed inconclusive verdict beside the stored backfire status', () => {
    renderWithTheme(
      <ObservationVerdict
        observation={{
          verdict_status: 'BACKFIRE',
          historical_verdict_status: 'BACKFIRE',
          screen_verdict: 'INCONCLUSIVE',
          screen_verdict_reason: 'No policy endpoint contract is defined. A change in utilization or cost is not a verdict.',
          verdict_is_recomputed: true,
        }}
      />,
    )
    expect(screen.getByText('Current screen verdict: Inconclusive')).toBeInTheDocument()
    expect(screen.getByText('Stored historical verdict: BACKFIRE')).toBeInTheDocument()
    expect(screen.getByText(/No policy endpoint contract is defined/)).toBeInTheDocument()
    expect(screen.queryByText('Backfire risk')).not.toBeInTheDocument()
  })
})

describe('executive rollup presentation', () => {
  it('does not label a claimant or missing rollup as delta PMPM', () => {
    const missing = costRollupPresentation({
      total_cost_impact: 0,
      total_cost_impact_status: 'UNAVAILABLE',
      total_cost_impact_display_unit: 'Σ ΔPMPM',
      cost_denominator_basis: null,
    })
    expect(missing.valueText).toBe('Unavailable')
    expect(missing.unit).toBeUndefined()

    const claimant = costRollupPresentation({
      total_cost_impact: 4,
      total_cost_impact_status: 'MEASURED',
      total_cost_impact_display_unit: 'claimant-month $',
      total_cost_impact_label: 'Sum of claimant-month dollar changes (not enrolled PMPM).',
      total_cost_observation_count: 2,
      cost_denominator_basis: 'CLAIMANT_MONTHS',
    })
    expect(claimant.valueText).toBe('4.00')
    expect(claimant.unit).toBe('claimant-month $')
    expect(claimant.unit).not.toContain('ΔPMPM')

    const enrolled = costRollupPresentation({
      total_cost_impact: -8,
      total_cost_impact_status: 'MEASURED',
      total_cost_impact_display_unit: 'Σ enrolled ΔPMPM',
      total_cost_impact_label: 'Sum of enrolled member-month dollar changes.',
      total_cost_observation_count: 1,
      cost_denominator_basis: 'ENROLLMENT',
    })
    expect(enrolled.unit).toBe('Σ enrolled ΔPMPM')
  })

  it('keeps a measured zero and hides an all-null average', () => {
    const missing = utilizationRollupPresentation({
      avg_utilization_change_pct: 0,
      avg_utilization_change_status: 'UNAVAILABLE',
      avg_utilization_observation_count: 0,
    })
    expect(missing.valueText).toBe('Unavailable')
    expect(missing.unit).toBeUndefined()

    const zero = utilizationRollupPresentation({
      avg_utilization_change_pct: 0,
      avg_utilization_change_status: 'MEASURED',
      avg_utilization_observation_count: 2,
    })
    expect(zero.valueText).toBe('0.0')
    expect(zero.subtitle).toContain('2 measured')
    expect(zero.subtitle).toContain('No change')
  })
})

describe('scenario comparison result', () => {
  it('renders a calculated payment delta and leaves missing percents unavailable', () => {
    renderWithTheme(
      <ScenarioComparison
        scenarios={[{
          scenario_id: 'mppr-whatif',
          scenario_name: 'MPPR secondary 40%',
          baseline_metrics: { utilization_per_1k: null, allowed_pmpm: null, paid_pmpm: null },
          projected_metrics: {},
          impact_metrics: {
            delta_payment_impact: 120,
            percent_changes: {
              utilization_per_1k: null,
              allowed_pmpm: null,
              paid_pmpm: null,
            },
          },
          confidence_score: 1,
        }]}
      />,
    )
    expect(screen.getByText('MPPR secondary 40%')).toBeInTheDocument()
    expect(screen.getAllByText('Unavailable').length).toBeGreaterThan(0)
    expect(screen.getByText(/Payment impact delta/)).toHaveTextContent('Payment impact delta $120.00 (fixture dollars, not enrolled PMPM)')
  })
})

describe('local browser evidence', () => {
  it('writes the corrected screen markup for a local browser capture', () => {
    const view = renderWithTheme(
      <div>
        <h1>Observation</h1>
        <ObservationVerdict
          observation={{
            verdict_status: 'BACKFIRE',
            historical_verdict_status: 'BACKFIRE',
            screen_verdict: 'INCONCLUSIVE',
            screen_verdict_reason: 'No policy endpoint contract is defined. A change in utilization or cost is not a verdict.',
          }}
        />
        <h1>Executive rollup</h1>
        <p>Cost: {costRollupPresentation({ total_cost_impact_status: 'UNAVAILABLE' }).valueText}</p>
        <p>Utilization: {utilizationRollupPresentation({ avg_utilization_change_status: 'UNAVAILABLE', avg_utilization_change_pct: 0 }).valueText}</p>
        <p>Measured zero: {utilizationRollupPresentation({ avg_utilization_change_status: 'MEASURED', avg_utilization_change_pct: 0, avg_utilization_observation_count: 2 }).valueText} across 2 measured observations</p>
        <h1>Scenario</h1>
        <ScenarioComparison
          scenarios={[{
            scenario_id: 'mppr-whatif',
            scenario_name: 'MPPR secondary 40%',
            baseline_metrics: {},
            projected_metrics: {},
            impact_metrics: {
              delta_payment_impact: 120,
              percent_changes: { utilization_per_1k: null, allowed_pmpm: null, paid_pmpm: null },
            },
            confidence_score: null,
          }]}
        />
      </div>,
    )
    const evidenceDir = resolve(
      dirname(fileURLToPath(import.meta.url)),
      '../../../../../docs/production/releases/gate_a_browser_acceptance_remediation',
    )
    mkdirSync(evidenceDir, { recursive: true })
    writeFileSync(
      resolve(evidenceDir, 'local-corrected-screens.html'),
      `<!doctype html><html><head><meta charset="utf-8"><title>Gate A local remediation</title></head><body>${view.container.innerHTML}</body></html>`,
    )
    expect(view.container).toHaveTextContent('Current screen verdict: Inconclusive')
    expect(view.container).toHaveTextContent('Stored historical verdict: BACKFIRE')
  })
})
