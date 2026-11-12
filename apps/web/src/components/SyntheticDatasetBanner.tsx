import React, { useEffect, useState } from 'react'
import { Alert, Typography } from '@mui/material'
import { apiClient } from '../lib/api'

type Identity = {
  synthetic?: boolean
  label?: string
  database_name?: string
  covered_lives?: number
  member_months?: number
  claim_rows?: number
  pharmacy_rows?: number
  dataset_role?: string
}

export default function SyntheticDatasetBanner() {
  const [identity, setIdentity] = useState<Identity | null>(null)

  useEffect(() => {
    let cancelled = false
    apiClient
      .getSyntheticPayerIdentity()
      .then((data) => {
        if (!cancelled) setIdentity(data)
      })
      .catch(() => {
        if (!cancelled) setIdentity(null)
      })
    return () => {
      cancelled = true
    }
  }, [])

  if (!identity?.synthetic) return null
  const lives = Number(identity.covered_lives || 0).toLocaleString()
  const months =
    identity.member_months == null
      ? 'Unavailable'
      : Number(identity.member_months).toLocaleString(undefined, { maximumFractionDigits: 3 })
  const claims = Number(identity.claim_rows || 0).toLocaleString()
  return (
    <Alert severity="info" sx={{ mb: 2 }} data-testid="synthetic-dataset-banner">
      <Typography variant="body2" component="div">
        <strong>{identity.label}</strong>
        {' · '}
        {lives} covered lives
        {' · '}
        {months} member-months
        {' · '}
        {claims} policy-event claim rows
        {' · '}
        pharmacy rows {identity.pharmacy_rows ?? 0}
        {' · '}
        database {identity.database_name}
      </Typography>
      <Typography variant="body2">{identity.dataset_role}</Typography>
      <Typography variant="body2">
        No real payer adjudication and no measured savings. Dollar figures are synthetic simulations.
      </Typography>
    </Alert>
  )
}
