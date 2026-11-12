export type SyntheticJourney = {
  document_id: string
  execution_status: string
  screen_verdict: string
  payment_impact?: number | null
  customer_label: string
  real_world_savings: boolean
}

export default function SyntheticJourneyStatus({ journeys }: { journeys: SyntheticJourney[] }) {
  return (
    <table>
      <caption>Synthetic illustration. Not real-world savings or CMS adjudication.</caption>
      <thead>
        <tr>
          <th>Policy</th>
          <th>Execution</th>
          <th>Screen verdict</th>
          <th>What the customer sees</th>
        </tr>
      </thead>
      <tbody>
        {journeys.map((journey) => (
          <tr key={journey.document_id}>
            <td>{journey.document_id}</td>
            <td>{journey.execution_status}</td>
            <td>{journey.screen_verdict}</td>
            <td>{journey.real_world_savings ? 'Blocked label' : journey.customer_label}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
