import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import SyntheticJourneyStatus from '../../components/SyntheticJourneyStatus'

const journeys = [
  { document_id: 'HF-RP-PAY-MPPR-001', execution_status: 'SYNTHETIC_SIMULATION', screen_verdict: 'INCONCLUSIVE', customer_label: 'Synthetic payment difference $600.00. Not real-world savings and not enrolled-population proof.', real_world_savings: false },
  { document_id: 'HF-RP-SOC-IMG-001', execution_status: 'SYNTHETIC_SIMULATION', screen_verdict: 'INCONCLUSIVE', customer_label: 'Synthetic payment difference $520.00. Not real-world savings and not enrolled-population proof.', real_world_savings: false },
  { document_id: 'HF-RP-CODE-PTP-001', execution_status: 'SYNTHETIC_SIMULATION', screen_verdict: 'INCONCLUSIVE', customer_label: 'Synthetic payment difference $800.00. Not real-world savings and not enrolled-population proof.', real_world_savings: false },
  { document_id: 'HF-RP-CODE-MUE-001', execution_status: 'SYNTHETIC_SIMULATION', screen_verdict: 'INCONCLUSIVE', customer_label: 'Synthetic payment difference $100.00. Not real-world savings and not enrolled-population proof.', real_world_savings: false },
  { document_id: 'HF-RP-COV-THER-001', execution_status: 'SYNTHETIC_SIMULATION', screen_verdict: 'INCONCLUSIVE', customer_label: 'Synthetic payment difference $80.00. Not real-world savings and not enrolled-population proof.', real_world_savings: false },
  { document_id: 'HF-RP-SOC-INF-001', execution_status: 'SYNTHETIC_SIMULATION', screen_verdict: 'INCONCLUSIVE', customer_label: 'Synthetic payment difference $3600.00. Not real-world savings and not enrolled-population proof.', real_world_savings: false },
  { document_id: 'HF-RP-UM-MRI-001', execution_status: 'NOT_MEASURABLE', screen_verdict: 'INCONCLUSIVE', customer_label: 'Not measurable. No population outcome is shown.', real_world_savings: false },
  { document_id: 'HF-RP-COV-NCD2202-001', execution_status: 'NOT_MEASURABLE', screen_verdict: 'INCONCLUSIVE', customer_label: 'Not measurable. No population outcome is shown.', real_world_savings: false },
  { document_id: 'HF-RP-COV-L34425-001', execution_status: 'NOT_MEASURABLE', screen_verdict: 'INCONCLUSIVE', customer_label: 'Not measurable. No population outcome is shown.', real_world_savings: false },
]

describe('nine synthetic policy journeys', () => {
  it('shows execution status and does not present a real savings claim', () => {
    render(<SyntheticJourneyStatus journeys={journeys} />)
    expect(screen.getAllByText('INCONCLUSIVE')).toHaveLength(9)
    expect(screen.getAllByText('NOT_MEASURABLE')).toHaveLength(3)
    expect(screen.getAllByText('SYNTHETIC_SIMULATION')).toHaveLength(6)
    expect(screen.getByText(/Not real-world savings or CMS adjudication/)).toBeInTheDocument()
    expect(screen.queryByText('Blocked label')).not.toBeInTheDocument()
    expect(screen.queryByText(/enrolled PMPM/i)).not.toBeInTheDocument()
  })
})
