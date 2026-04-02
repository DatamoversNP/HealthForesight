/**
 * What-If Analysis Page
 * Allows users to adjust policy parameters and see projected impact
 */
import React, { useState, useEffect } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  LinearProgress,
  Paper,
  Slider,
  TextField,
  Typography,
  MenuItem,
  Alert,
  Tabs,
  Tab,
  FormControl,
  InputLabel,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Checkbox,
} from '@mui/material'
import {
  PlayArrow as RunIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Analytics as AnalyticsIcon,
} from '@mui/icons-material'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { apiClient } from '../lib/api'
import TrustPanel from '../components/TrustPanel'
import ElasticityCurvesDisplay from '../components/ElasticityCurvesDisplay'
import ScenarioComparison from '../components/ScenarioComparison'
import { healthForesightColors } from '../theme/healthForesightTheme'

interface Policy {
  id: string
  name: string
  policy_type: string
  policy_logic?: any
}

interface ScenarioResult {
  scenario_id: string
  scenario_name?: string
  baseline_metrics: {
    utilization_per_1k: number
    allowed_pmpm: number
    paid_pmpm: number
    claim_count: number
    member_months: number
  }
  projected_metrics: {
    utilization_per_1k: number
    allowed_pmpm: number
    paid_pmpm: number
    claim_count: number
    member_months: number
  }
  impact_metrics: {
    utilization_per_1k: number
    allowed_pmpm: number
    paid_pmpm: number
    percent_changes: {
      utilization_per_1k: number
      allowed_pmpm: number
      paid_pmpm: number
    }
    tradeoff_analysis?: {
      utilization_change_pct: number
      cost_change_pct: number
      tradeoff_ratio: number
      efficiency_score: number
      efficiency_category: 'HIGH' | 'MEDIUM' | 'LOW' | 'POOR'
      interpretation: string
    }
    risk_analysis?: {
      worst_case: {
        utilization_per_1k: number
        utilization_change_pct: number
        cost_pmpm: number
        cost_change_pct: number
      }
      best_case: {
        utilization_per_1k: number
        utilization_change_pct: number
        cost_pmpm: number
        cost_change_pct: number
      }
      confidence_interval_width: {
        utilization_pct: number
        cost_pct: number
      }
      risk_level: 'HIGH' | 'MEDIUM' | 'LOW' | 'MINIMAL'
      risk_factors: string[]
      risk_summary: string
    }
  }
  confidence_intervals: {
    utilization_per_1k: [number, number]
    allowed_pmpm: [number, number]
    paid_pmpm: [number, number]
  }
  confidence_score: number
  sensitivity_analysis: any
}

export default function WhatIfAnalysisPage() {
  const [policies, setPolicies] = useState<Policy[]>([])
  const [selectedPolicy, setSelectedPolicy] = useState<Policy | null>(null)
  const [selectedPolicies, setSelectedPolicies] = useState<Policy[]>([]) // Multi-policy support
  const [multiPolicyMode, setMultiPolicyMode] = useState(false) // Toggle between single and multi-policy
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [scenarioResult, setScenarioResult] = useState<ScenarioResult | null>(null)
  const [scenarios, setScenarios] = useState<ScenarioResult[]>([]) // Store multiple scenarios for comparison
  const [running, setRunning] = useState(false)
  const [workerHint, setWorkerHint] = useState<string | null>(null)
  const [scenarioName, setScenarioName] = useState<string>('')
  const [nameDialogOpen, setNameDialogOpen] = useState(false)
  const [multiPolicyProgress, setMultiPolicyProgress] = useState<{
    current: number
    total: number
    currentPolicyName: string
    completed: number
  } | null>(null)
  const [activeTab, setActiveTab] = useState<'configure' | 'elasticity' | 'results' | 'compare' | 'sensitivity' | 'accuracy'>('configure')
  const [elasticityData, setElasticityData] = useState<any>(null)
  const [elasticityLoading, setElasticityLoading] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  /** Policies with claim counts (sorted by most data). Used to suggest policy for what-if. */
  const [policiesWithClaimCounts, setPoliciesWithClaimCounts] = useState<Array<{ id: string; name: string; policy_type: string; claim_count: number }> | null>(null)
  
  // Scenario Accuracy Tracking (Phase 7)
  const [scenarioAccuracy, setScenarioAccuracy] = useState<any[]>([])
  const [scenarioLinks, setScenarioLinks] = useState<any[]>([])
  const [currentScenarioAnalysisId, setCurrentScenarioAnalysisId] = useState<string | null>(null)
  const [observations, setObservations] = useState<any[]>([])
  const [linkDialogOpen, setLinkDialogOpen] = useState(false)
  const [accuracyDialogOpen, setAccuracyDialogOpen] = useState(false)
  const [selectedObservationId, setSelectedObservationId] = useState<string | null>(null)
  
  // Scenario parameters
  const [scenarioParams, setScenarioParams] = useState({
    lever_adjustments: {} as Record<string, any>,
    elasticity_adjustments: {} as Record<string, number>,
    member_count_multiplier: 1.0,
    utilization_trend: 0.0,
    cost_inflation: 0.02,
    projection_months: 12,
  })
  
  // Baseline filters
  const [baselineFilters, setBaselineFilters] = useState({
    lob: [] as string[],
    markets: [] as string[],
    cpt_codes: [] as string[],
  })

  useEffect(() => {
    loadPolicies()
  }, [])

  useEffect(() => {
    if (selectedPolicy) {
      loadElasticityData(selectedPolicy.id)
      loadPreviousScenarios(selectedPolicy.id)
      loadScenarioAccuracy(selectedPolicy.id)
      loadObservations(selectedPolicy.id)
    } else {
      setScenarios([])
      setScenarioResult(null)
      setScenarioAccuracy([])
      setScenarioLinks([])
    }
  }, [selectedPolicy])
  
  useEffect(() => {
    if (currentScenarioAnalysisId) {
      loadScenarioAccuracy(selectedPolicy?.id, currentScenarioAnalysisId)
    }
  }, [currentScenarioAnalysisId])

  const loadPreviousScenarios = async (policyId: string) => {
    try {
      // Get all SIMULATE analyses for this policy
      const analyses = await apiClient.getAnalyses({ analysis_type: 'SIMULATE' })
      const policyScenarios = Array.isArray(analyses)
        ? analyses.filter((a: any) => a.policy_id === policyId && a.status === 'COMPLETED')
        : []

      // Load results for each completed scenario
      const loadedScenarios: ScenarioResult[] = []
      for (const analysis of policyScenarios) {
        try {
          const results = await apiClient.getAnalysisResults(analysis.id, 'whatif_scenario')
          if (results.results) {
            const scenarioData = results.results.whatif_scenario || 
                               results.results.WHATIF_SCENARIO ||
                               results.results
            if (scenarioData && scenarioData.scenario_id) {
              // Add analysis metadata to scenario for reference
              loadedScenarios.push({
                ...scenarioData,
                _analysis_id: analysis.id,
                _created_at: analysis.created_at,
              } as ScenarioResult & { _analysis_id: string; _created_at?: string })
            }
          }
        } catch (err) {
          console.warn(`Failed to load scenario ${analysis.id}:`, err)
          // Continue loading other scenarios
        }
      }

      // Sort by creation date (most recent first)
      loadedScenarios.sort((a: any, b: any) => {
        const dateA = a._created_at ? new Date(a._created_at).getTime() : 0
        const dateB = b._created_at ? new Date(b._created_at).getTime() : 0
        return dateB - dateA
      })

      setScenarios(loadedScenarios)
      
      // If we have scenarios but no current result, show the most recent one
      if (loadedScenarios.length > 0 && !scenarioResult) {
        setScenarioResult(loadedScenarios[0])
      }
    } catch (err) {
      console.error('Error loading previous scenarios:', err)
      // Don't show error - scenarios are optional
    }
  }

  const loadPolicies = async () => {
    try {
      const data = await apiClient.getPolicies()
      const policiesList = Array.isArray(data) ? data : (data.items || [])
      setPolicies(policiesList)
      try {
        const withCounts = await apiClient.getPoliciesWithClaimCounts(20)
        setPoliciesWithClaimCounts(Array.isArray(withCounts) ? withCounts : [])
      } catch {
        setPoliciesWithClaimCounts(null)
      }
    } catch (err: any) {
      console.error('Error loading policies:', err)
      setError(err.detail || err.message || 'Failed to load policies')
    }
  }

  // Combine results from multiple policies
  const combineMultiPolicyResults = (policyResults: Array<{ policy: Policy; scenario: any }>, scenarioName: string): ScenarioResult => {
    if (policyResults.length === 0) {
      throw new Error('No policy results to combine')
    }

    // Aggregate baseline metrics (use first policy's baseline as reference)
    const baselineMetrics = { ...policyResults[0].scenario.baseline_metrics }

    // Aggregate projected metrics by summing impacts
    let totalCostChangePMPM = 0
    let totalUtilizationChange1K = 0
    let totalCostChangeTotal = 0
    let totalUtilizationChangePct = 0
    let totalClaimCount = 0
    let totalMemberMonths = baselineMetrics.member_months || 0
    let totalConfidenceScore = 0
    let totalAllowedPMPM = baselineMetrics.allowed_pmpm || 0
    let totalPaidPMPM = baselineMetrics.paid_pmpm || 0

    for (const { scenario } of policyResults) {
      const impact = scenario.impact_metrics || {}
      const projected = scenario.projected_metrics || {}
      
      totalCostChangePMPM += impact.allowed_pmpm || 0
      totalUtilizationChange1K += impact.utilization_per_1k || 0
      totalCostChangeTotal += impact.allowed_pmpm ? (impact.allowed_pmpm * (projected.member_months || totalMemberMonths)) : 0
      totalUtilizationChangePct += impact.percent_changes?.utilization_per_1k || 0
      totalClaimCount += projected.claim_count || 0
      totalAllowedPMPM += impact.allowed_pmpm || 0
      totalPaidPMPM += impact.paid_pmpm || 0
      totalConfidenceScore += scenario.confidence_score || 0
    }

    // Average confidence score
    const avgConfidenceScore = totalConfidenceScore / policyResults.length

    // Calculate combined projected metrics
    const projectedMetrics = {
      utilization_per_1k: baselineMetrics.utilization_per_1k + totalUtilizationChange1K,
      allowed_pmpm: baselineMetrics.allowed_pmpm + totalCostChangePMPM,
      paid_pmpm: baselineMetrics.paid_pmpm + (totalPaidPMPM - totalCostChangePMPM),
      claim_count: totalClaimCount || baselineMetrics.claim_count,
      member_months: totalMemberMonths,
    }

    // Combined impact metrics
    const impactMetrics = {
      utilization_per_1k: totalUtilizationChange1K,
      allowed_pmpm: totalCostChangePMPM,
      paid_pmpm: totalPaidPMPM - totalCostChangePMPM,
      claim_count: totalClaimCount - (baselineMetrics.claim_count || 0),
      member_months: 0,
      percent_changes: {
        utilization_per_1k: totalUtilizationChangePct / policyResults.length,
        allowed_pmpm: baselineMetrics.allowed_pmpm ? ((totalCostChangePMPM / baselineMetrics.allowed_pmpm) * 100) : 0,
        paid_pmpm: baselineMetrics.paid_pmpm ? (((totalPaidPMPM - totalCostChangePMPM) / baselineMetrics.paid_pmpm) * 100) : 0,
      },
    }

    return {
      scenario_id: `multi-policy-${Date.now()}`,
      scenario_name: scenarioName,
      baseline_metrics: baselineMetrics,
      projected_metrics: projectedMetrics,
      impact_metrics: impactMetrics,
      confidence_intervals: policyResults[0].scenario.confidence_intervals || {},
      confidence_score: avgConfidenceScore,
      sensitivity_analysis: {
        policies_count: policyResults.length,
        individual_impacts: policyResults.map(({ policy, scenario }) => ({
          policy_id: policy.id,
          policy_name: policy.name,
          cost_impact: scenario.impact_metrics?.allowed_pmpm || 0,
          utilization_impact: scenario.impact_metrics?.utilization_per_1k || 0,
        })),
      },
    }
  }

  // Scenario Accuracy Tracking Functions (Phase 7)
  const loadScenarioAccuracy = async (policyId?: string, scenarioAnalysisId?: string) => {
    try {
      const accuracyRecords = await apiClient.getScenarioAccuracy(scenarioAnalysisId || undefined, policyId || undefined)
      setScenarioAccuracy(accuracyRecords || [])
      
      const links = await apiClient.getScenarioLinks(scenarioAnalysisId || undefined, policyId || undefined)
      setScenarioLinks(links || [])
    } catch (err: any) {
      console.error('Error loading scenario accuracy:', err)
      // Don't show error to user - accuracy data may not exist yet
    }
  }
  
  const loadObservations = async (policyId: string) => {
    try {
      const obs = await apiClient.getObservations({ policy_id: policyId })
      setObservations(obs || [])
    } catch (err: any) {
      console.error('Error loading observations:', err)
    }
  }
  
  const handleLinkScenario = async () => {
    if (!currentScenarioAnalysisId || !selectedPolicy) {
      setError('Please select a scenario and policy')
      return
    }
    
    try {
      await apiClient.linkScenarioToPolicy(currentScenarioAnalysisId, selectedPolicy.id, {
        linked_by: 'user',
        linked_at: new Date().toISOString(),
      })
      await loadScenarioAccuracy(selectedPolicy.id, currentScenarioAnalysisId)
      setLinkDialogOpen(false)
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to link scenario')
    }
  }
  
  const handleComputeAccuracy = async () => {
    if (!currentScenarioAnalysisId || !selectedObservationId) {
      setError('Please select a scenario and observation')
      return
    }
    
    try {
      const accuracy = await apiClient.computeScenarioAccuracy(currentScenarioAnalysisId, selectedObservationId)
      await loadScenarioAccuracy(selectedPolicy?.id, currentScenarioAnalysisId)
      setAccuracyDialogOpen(false)
      setActiveTab('accuracy')
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to compute accuracy')
    }
  }
  
  const loadElasticityData = async (policyId: string) => {
    try {
      setElasticityLoading(true)
      // First, check if elasticity analysis exists for this policy
      const analyses = await apiClient.getAnalyses({ analysis_type: 'ELASTICITY' })
      const elasticityAnalysis = Array.isArray(analyses) 
        ? analyses.find((a: any) => a.policy_id === policyId)
        : null
      
      if (elasticityAnalysis) {
        // If analysis failed, show error_message instead of "old format"
        if (elasticityAnalysis.status === 'FAILED') {
          const analysisDetail = await apiClient.getAnalysis(elasticityAnalysis.id).catch(() => ({}))
          const detail = analysisDetail?.error_message || 'Job failed (check worker logs).'
          const msg = `${detail} Create a new elasticity analysis to regenerate (results are now saved to the database).`
          console.warn('Elasticity analysis failed:', detail)
          setElasticityData(null)
          setError(`Elasticity: ${msg}`)
          return
        }
        // Load elasticity results
        const results = await apiClient.getAnalysisResults(elasticityAnalysis.id, 'ELASTICITY')
        if (results?.status === 'FAILED' && results?.error_message) {
          console.warn('Elasticity analysis failed:', results.error_message)
          setElasticityData(null)
          setError(`Elasticity: ${results.error_message}`)
          return
        }
        let elasticityData = null
        if (results.results && results.results.ELASTICITY) {
          elasticityData = results.results.ELASTICITY
        } else if (results.service_categories) {
          elasticityData = results
        } else if (results.results) {
          elasticityData = results.results[Object.keys(results.results)[0]]
        }
        if (elasticityData && elasticityData.service_categories && Object.keys(elasticityData.service_categories).length > 0) {
          setElasticityData(elasticityData)
          setError(null)
        } else {
          console.warn('Elasticity data missing service_categories. Create a new elasticity analysis.')
          setElasticityData(null)
        }
      } else {
        // No elasticity analysis exists - could trigger one or show default
        setElasticityData(null)
      }
    } catch (err) {
      console.error('Error loading elasticity data:', err)
      // Don't show error - elasticity is optional
      setElasticityData(null)
    } finally {
      setElasticityLoading(false)
    }
  }

  const handleRunScenario = () => {
    if (!multiPolicyMode && !selectedPolicy) {
      setError('Please select a policy')
      return
    }
    if (multiPolicyMode && selectedPolicies.length === 0) {
      setError('Please select at least one policy')
      return
    }
    // Open dialog to get scenario name
    setNameDialogOpen(true)
  }

  const handleRunScenarioConfirmed = async () => {
    if (!multiPolicyMode && !selectedPolicy) {
      setError('Please select a policy')
      return
    }
    if (multiPolicyMode && selectedPolicies.length === 0) {
      setError('Please select at least one policy')
      return
    }

    // Generate default name if not provided
    const finalName = scenarioName.trim() || `Scenario ${new Date().toLocaleString()}`

    try {
      setRunning(true)
      setError(null)
      setWorkerHint(null)
      setNameDialogOpen(false)
      
      if (multiPolicyMode && selectedPolicies.length > 1) {
        // Multi-policy scenario: run simulations for each policy and combine results
        const policyResults = []
        const totalPolicies = selectedPolicies.length
        
        // Initialize progress tracking
        setMultiPolicyProgress({
          current: 1,
          total: totalPolicies,
          currentPolicyName: selectedPolicies[0]?.name || 'Unknown',
          completed: 0,
        })
        
        for (let i = 0; i < selectedPolicies.length; i++) {
          const policy = selectedPolicies[i]
          try {
            // Update progress: starting new policy
            setMultiPolicyProgress({
              current: i + 1,
              total: totalPolicies,
              currentPolicyName: policy.name,
              completed: i,
            })
            
            const result = await apiClient.createSimulateAnalysis({
              policy_id: policy.id,
              scenario_params: scenarioParams,
              filters: baselineFilters,
            })
            
            // Poll for completion (what-if can take several minutes per policy)
            let analysis = result
            let attempts = 0
            const maxAttempts = 120 // ~10 min per policy at 5s interval

            while (analysis.status === 'PENDING' || analysis.status === 'RUNNING') {
              if (attempts >= maxAttempts) {
                throw new Error('Analysis timed out for this policy. Large datasets can take 10+ minutes.')
              }
              await new Promise(resolve => setTimeout(resolve, 5000))
              analysis = await apiClient.getAnalysis(analysis.id)
              attempts++
            }
            
            if (analysis.status === 'COMPLETED') {
              const results = await apiClient.getAnalysisResults(analysis.id, 'whatif_scenario')
              if (results.results) {
                const scenarioData = results.results.whatif_scenario || 
                                   results.results.WHATIF_SCENARIO ||
                                   results.results
                if (scenarioData) {
                  policyResults.push({
                    policy,
                    scenario: scenarioData,
                  })
                  
                  // Update progress: policy completed
                  setMultiPolicyProgress({
                    current: i + 1,
                    total: totalPolicies,
                    currentPolicyName: policy.name,
                    completed: i + 1,
                  })
                }
              }
            }
          } catch (err) {
            console.error(`Error simulating policy ${policy.id}:`, err)
            // Continue with other policies, but still update completed count
            setMultiPolicyProgress(prev => prev ? {
              ...prev,
              completed: prev.completed,
            } : null)
          }
        }
        
        // Combine results from multiple policies
        if (policyResults.length > 0) {
          // Update progress: combining results
          setMultiPolicyProgress(prev => prev ? {
            ...prev,
            currentPolicyName: 'Combining results...',
          } : null)
          
          const combinedResult = combineMultiPolicyResults(policyResults, finalName)
          setScenarioResult(combinedResult)
          
          // Clear progress indicator
          setMultiPolicyProgress(null)
          setActiveTab('results')
        } else {
          setMultiPolicyProgress(null)
          throw new Error('Failed to simulate any policies')
        }
      } else {
        // Single policy scenario (existing logic)
        const policy = multiPolicyMode ? selectedPolicies[0] : selectedPolicy!
        const result = await apiClient.createSimulateAnalysis({
          policy_id: policy.id,
          scenario_params: scenarioParams,
          filters: baselineFilters,
        })
        
        console.log('Simulation created:', result)
        
        // Check if result is already in response (synchronous completion)
        if (result.status === 'COMPLETED' && result.result) {
          console.log('Simulation completed synchronously, result:', result.result)
          const newScenario = {
            ...result.result,
            scenario_name: finalName,
            _analysis_id: result.id,
            _created_at: result.created_at,
          } as ScenarioResult & { _analysis_id: string; _created_at?: string }
          setScenarioResult(newScenario)
          setCurrentScenarioAnalysisId(result.id)
          setScenarios((prev) => {
            const exists = prev.some((s) => s.scenario_id === newScenario.scenario_id)
            return exists ? prev : [newScenario, ...prev]  // Add to front (most recent first)
          })
          setActiveTab('results')
          setRunning(false)
          loadScenarioAccuracy(selectedPolicy?.id, result.id)
          return
        }
        
        // Poll for results (if async). What-if with large claims can take 2–5+ minutes.
        let attempts = 0
        const maxAttempts = 300 // ~10 min at 2s interval
        const pollIntervalMs = 2000
        const workerHintAfterPolls = 15 // ~30s: show hint if Celery worker may not be running

        while (attempts < maxAttempts) {
          await new Promise(resolve => setTimeout(resolve, pollIntervalMs))
          
          try {
            const analysis = await apiClient.getAnalysis(result.id)
            if (attempts < 5 || attempts % 10 === 9) {
              console.log(`Polling attempt ${attempts + 1}: status = ${analysis.status}`)
            }
            if (attempts + 1 >= workerHintAfterPolls && analysis.status === 'PENDING') {
              setWorkerHint('Simulation is still running. If it doesn\'t complete, the Celery worker may not be running. From the project root run: ./apps/worker/start_worker.sh')
            }
            
            if (analysis.status === 'COMPLETED') {
              const results = await apiClient.getAnalysisResults(result.id, 'whatif_scenario')
              console.log('Analysis results:', results)
              
              let scenarioData = null
              
              // Try multiple result type formats
              if (results.results) {
                scenarioData = results.results.whatif_scenario || 
                              results.results.WHATIF_SCENARIO ||
                              results.results[Object.keys(results.results)[0]] // Get first result if available
              }
              
              // Also check if result is directly in response
              if (!scenarioData && (results.scenario_id || results.baseline_metrics)) {
                scenarioData = results
              }
              
              if (scenarioData) {
                console.log('Found scenario data:', scenarioData)
                const scenarioWithMeta = {
                  ...scenarioData,
                  scenario_name: scenarioData.scenario_name || finalName || `Scenario ${new Date().toLocaleString()}`,
                  _analysis_id: result.id,
                  _created_at: result.created_at,
                } as ScenarioResult & { _analysis_id: string; _created_at?: string }
                setScenarioResult(scenarioWithMeta)
                // Add to scenarios list for comparison (avoid duplicates)
                setScenarios((prev) => {
                  const exists = prev.some((s) => s.scenario_id === scenarioWithMeta.scenario_id)
                  return exists ? prev : [scenarioWithMeta, ...prev]  // Add to front (most recent first)
                })
                setActiveTab('results') // Switch to results tab
                setWorkerHint(null)
                break
              } else {
                console.warn('No scenario data found in results:', results)
              }
            } else if (analysis.status === 'FAILED') {
              setError(`Scenario simulation failed: ${analysis.error_message || 'Unknown error'}`)
              setWorkerHint(null)
              break
            }
          } catch (err: any) {
            if (attempts < 5 || attempts % 10 === 9) console.error('Error polling for results:', err)
            // Continue polling
          }
          
          attempts++
        }
        
        if (attempts >= maxAttempts) {
          setWorkerHint(null)
          setError('Scenario simulation timed out. The Celery worker may not be running—from the project root run: ./apps/worker/start_worker.sh (requires Redis). You can also check analysis status later from the analyses list.')
        }
      }
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to run scenario')
    } finally {
      setRunning(false)
      setMultiPolicyProgress(null) // Clear progress on completion or error
    }
  }

  const handleLeverAdjustment = (leverId: string, parameter: string, value: any) => {
    setScenarioParams(prev => ({
      ...prev,
      lever_adjustments: {
        ...prev.lever_adjustments,
        [leverId]: {
          ...prev.lever_adjustments[leverId],
          [parameter]: value,
        },
      },
    }))
  }

  const handleElasticityAdjustment = (category: string, value: number) => {
    setScenarioParams(prev => ({
      ...prev,
      elasticity_adjustments: {
        ...prev.elasticity_adjustments,
        [category]: value,
      },
    }))
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2 }).format(value)
  }

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
  }

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography
          variant="h4"
          component="h1"
          sx={{
            fontFamily: 'IBM Plex Sans, Inter, sans-serif',
            fontWeight: 600,
            mb: 1,
            color: healthForesightColors.neutral.dark,
          }}
        >
          What-If Scenarios
        </Typography>
        <Typography
          variant="body1"
          sx={{
            color: healthForesightColors.neutral.mid,
            lineHeight: 1.6,
            mb: 2,
          }}
        >
          Adjust policy parameters and examine projected impact before implementation.
        </Typography>
      </Box>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 3, gap: 1 }}>
          {scenarioResult && scenarios.length > 0 && (
            <Button
              variant="outlined"
              onClick={() => {
                // Switch to comparison tab
                setActiveTab('compare')
              }}
            >
              View Comparison ({scenarios.length})
            </Button>
          )}
          <Button
            variant="contained"
            startIcon={running ? <CircularProgress size={20} /> : <RunIcon />}
            onClick={handleRunScenario}
            disabled={!selectedPolicy || running}
          >
            {running ? 'Running...' : 'Run Scenario'}
          </Button>
          
          {/* Scenario Name Dialog */}
          <Dialog open={nameDialogOpen} onClose={() => setNameDialogOpen(false)}>
            <DialogTitle>Name Your Scenario</DialogTitle>
            <DialogContent>
              <TextField
                autoFocus
                margin="dense"
                label="Scenario Name"
                fullWidth
                variant="outlined"
                value={scenarioName}
                onChange={(e) => setScenarioName(e.target.value)}
                placeholder="e.g., Aggressive Prior Auth, Baseline Comparison, etc."
                sx={{ mt: 1, minWidth: 400 }}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && scenarioName.trim()) {
                    handleRunScenarioConfirmed()
                  }
                }}
              />
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                Give your scenario a descriptive name to easily identify it later in comparisons.
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                Large datasets may take 2–5 minutes. The page will update automatically when the run completes.
              </Typography>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => {
                setNameDialogOpen(false)
                setScenarioName('')
              }}>
                Cancel
              </Button>
              <Button 
                onClick={handleRunScenarioConfirmed}
                variant="contained"
              >
                Run Scenario
              </Button>
            </DialogActions>
          </Dialog>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {running && !multiPolicyProgress && (
        <Alert severity="info" sx={{ mb: 2 }} icon={<CircularProgress size={20} />}>
          What-if analysis is running. This may take 2–5 minutes for large datasets. Please wait — the page will update when complete.
        </Alert>
      )}
      {workerHint && (
        <Alert severity="warning" sx={{ mb: 2 }} onClose={() => setWorkerHint(null)}>
          {workerHint}
        </Alert>
      )}

      {/* Build visible tabs array */}
      {(() => {
        const visibleTabs: Array<{ label: string; key: typeof activeTab }> = [
          { label: 'Configure Scenario', key: 'configure' },
        ]
        if (selectedPolicy) {
          visibleTabs.push({ label: 'Elasticity Curves', key: 'elasticity' })
        }
        if (scenarioResult) {
          visibleTabs.push({ label: 'Results', key: 'results' })
        }
        if (scenarios.length > 0) {
          visibleTabs.push({ label: `Compare Scenarios (${scenarios.length})`, key: 'compare' })
        }
        if (scenarioResult && scenarioResult.sensitivity_analysis) {
          visibleTabs.push({ label: 'Sensitivity Analysis', key: 'sensitivity' })
        }
        if (scenarioAccuracy.length > 0 || scenarioLinks.length > 0) {
          visibleTabs.push({ label: `Accuracy (${scenarioAccuracy.length})`, key: 'accuracy' })
        }
        
        const currentTabIndex = visibleTabs.findIndex(t => t.key === activeTab)
        
        return (
          <Tabs 
            value={currentTabIndex >= 0 ? currentTabIndex : 0}
            onChange={(_, newValue) => {
              if (newValue >= 0 && newValue < visibleTabs.length) {
                setActiveTab(visibleTabs[newValue].key)
              }
            }}
            sx={{ mb: 3 }}
          >
            {visibleTabs.map((tab) => (
              <Tab 
                key={tab.key}
                label={tab.label}
              />
            ))}
          </Tabs>
        )
      })()}

      {activeTab === 'configure' && (
        <Grid container spacing={3} className="scenario-builder">
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                {policiesWithClaimCounts && policiesWithClaimCounts.length > 0 && policiesWithClaimCounts[0].claim_count > 0 && (
                  <Alert severity="info" sx={{ mb: 2 }} action={
                    <Button
                      color="inherit"
                      size="small"
                      onClick={() => {
                        const top = policiesWithClaimCounts[0]
                        const policy = policies.find(p => p.id === top.id)
                        if (policy) {
                          setSelectedPolicy(policy)
                          if (multiPolicyMode) setSelectedPolicies([policy])
                        }
                      }}
                    >
                      Use this policy
                    </Button>
                  }>
                    <strong>Policy with most data:</strong> {policiesWithClaimCounts[0].name} ({policiesWithClaimCounts[0].claim_count.toLocaleString()} claims in last 12 months). Use for what-if to get non-zero results.
                  </Alert>
                )}
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">
                    Select {multiPolicyMode ? 'Policies' : 'Policy'}
                  </Typography>
                  <Chip
                    label={multiPolicyMode ? 'Multi-Policy Mode' : 'Single Policy Mode'}
                    color={multiPolicyMode ? 'primary' : 'default'}
                    onClick={() => {
                      setMultiPolicyMode(!multiPolicyMode)
                      if (!multiPolicyMode) {
                        // Switching to multi-policy mode
                        if (selectedPolicy) {
                          setSelectedPolicies([selectedPolicy])
                        }
                      } else {
                        // Switching to single policy mode
                        if (selectedPolicies.length > 0) {
                          setSelectedPolicy(selectedPolicies[0])
                        }
                        setSelectedPolicies([])
                      }
                    }}
                    clickable
                  />
                </Box>
                {multiPolicyMode ? (
                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>Policies</InputLabel>
                    <Select
                      multiple
                      value={selectedPolicies.map(p => p.id)}
                      label="Policies"
                      onChange={(e) => {
                        const selectedIds = e.target.value as string[]
                        const selected = policies.filter(p => selectedIds.includes(p.id))
                        setSelectedPolicies(selected)
                        // Also set first as selectedPolicy for backward compatibility
                        if (selected.length > 0) {
                          setSelectedPolicy(selected[0])
                        } else {
                          setSelectedPolicy(null)
                        }
                      }}
                      renderValue={(selected) => (
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {(selected as string[]).map((value) => {
                            const policy = policies.find(p => p.id === value)
                            return policy ? (
                              <Chip key={value} label={`${policy.name} (${policy.policy_type})`} size="small" />
                            ) : null
                          })}
                        </Box>
                      )}
                    >
                      {policies.map((policy) => (
                        <MenuItem key={policy.id} value={policy.id}>
                          <Checkbox checked={selectedPolicies.some(p => p.id === policy.id)} />
                          {policy.name} ({policy.policy_type})
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                ) : (
                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>Policy</InputLabel>
                    <Select
                      value={selectedPolicy?.id || ''}
                      label="Policy"
                      onChange={(e) => {
                        const policy = policies.find(p => p.id === e.target.value)
                        setSelectedPolicy(policy || null)
                      }}
                    >
                      {policies.map((policy) => (
                        <MenuItem key={policy.id} value={policy.id}>
                          {policy.name} ({policy.policy_type})
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                )}
                {multiPolicyMode && selectedPolicies.length > 1 && (
                  <Alert severity="info" sx={{ mt: 2 }}>
                    {selectedPolicies.length} policies selected. The scenario will simulate the combined impact of all selected policies.
                  </Alert>
                )}
                
                {/* Multi-Policy Progress Indicator */}
                {multiPolicyProgress && running && (
                  <Card sx={{ mt: 2, bgcolor: 'primary.main', color: 'primary.contrastText' }}>
                    <CardContent>
                      <Typography variant="h6" gutterBottom sx={{ color: 'primary.contrastText' }}>
                        Processing Multi-Policy Scenario
                      </Typography>
                      <Box sx={{ mb: 2 }}>
                        <LinearProgress 
                          variant="determinate" 
                          value={(multiPolicyProgress.completed / multiPolicyProgress.total) * 100} 
                          sx={{ 
                            height: 8, 
                            borderRadius: 4, 
                            mb: 1,
                            bgcolor: 'rgba(255, 255, 255, 0.3)',
                            '& .MuiLinearProgress-bar': {
                              bgcolor: 'rgba(255, 255, 255, 0.9)'
                            }
                          }}
                        />
                        <Typography variant="body2" sx={{ mt: 1, color: 'primary.contrastText' }}>
                          {multiPolicyProgress.completed} of {multiPolicyProgress.total} policies completed
                        </Typography>
                      </Box>
                      <Typography variant="body2" sx={{ fontStyle: 'italic', color: 'primary.contrastText' }}>
                        Currently processing: <strong>{multiPolicyProgress.currentPolicyName}</strong>
                        {' '}({multiPolicyProgress.current} of {multiPolicyProgress.total})
                      </Typography>
                    </CardContent>
                  </Card>
                )}

                {selectedPolicy && selectedPolicy.policy_logic && (
                  <Box sx={{ mt: 3 }}>
                    <Typography variant="subtitle1" gutterBottom>
                      Policy Levers
                    </Typography>
                    {selectedPolicy.policy_logic.levers?.map((lever: any, idx: number) => {
                      const leverId = `${lever.lever_type}_${idx}`
                      return (
                        <Accordion key={leverId} sx={{ mt: 1 }}>
                          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                            <Typography>{lever.lever_type.replace(/_/g, ' ')}</Typography>
                          </AccordionSummary>
                          <AccordionDetails>
                            {lever.lever_type === 'PRIOR_AUTH' && (
                              <Box>
                                <Typography variant="body2" gutterBottom>
                                  Requires PA: {lever.config?.requires_pa ? 'Yes' : 'No'}
                                </Typography>
                                <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                                  <Typography variant="body2" sx={{ mr: 1 }}>
                                    Override Allowed:
                                  </Typography>
                                  <Checkbox
                                    checked={lever.config?.override_allowed || false}
                                    onChange={(e) => handleLeverAdjustment(leverId, 'override_allowed', e.target.checked)}
                                    size="small"
                                  />
                                </Box>
                              </Box>
                            )}
                            {lever.lever_type === 'COST_SHARING' && (
                              <Box>
                                <Typography variant="body2" gutterBottom>
                                  Copay Adjustment
                                </Typography>
                                <Slider
                                  value={lever.config?.copay || 0}
                                  onChange={(_, value) => handleLeverAdjustment(leverId, 'copay', value)}
                                  min={0}
                                  max={200}
                                  step={5}
                                  marks
                                  valueLabelDisplay="auto"
                                  sx={{ mt: 2 }}
                                />
                                <Typography variant="body2" gutterBottom sx={{ mt: 2 }}>
                                  Coinsurance: {(lever.config?.coinsurance || 0) * 100}%
                                </Typography>
                                <Slider
                                  value={(lever.config?.coinsurance || 0) * 100}
                                  onChange={(_, value) => handleLeverAdjustment(leverId, 'coinsurance', (value as number) / 100)}
                                  min={0}
                                  max={50}
                                  step={1}
                                  marks
                                  valueLabelDisplay="auto"
                                />
                              </Box>
                            )}
                            {lever.lever_type === 'DURATION_FREQUENCY_LIMIT' && (
                              <Box>
                                <Typography variant="body2" gutterBottom>
                                  Max Visits
                                </Typography>
                                <TextField
                                  type="number"
                                  value={lever.config?.max_visits || 0}
                                  onChange={(e) => handleLeverAdjustment(leverId, 'max_visits', parseInt(e.target.value))}
                                  size="small"
                                  fullWidth
                                />
                              </Box>
                            )}
                          </AccordionDetails>
                        </Accordion>
                      )
                    })}
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Environmental Variables
                </Typography>
                
                <Box sx={{ mt: 2 }}>
                  <Typography gutterBottom>
                    Member Count Multiplier: {scenarioParams.member_count_multiplier.toFixed(2)}x
                  </Typography>
                  <Slider
                    value={scenarioParams.member_count_multiplier}
                    onChange={(_, value) => setScenarioParams(prev => ({ ...prev, member_count_multiplier: value as number }))}
                    min={0.5}
                    max={2.0}
                    step={0.1}
                    marks={[
                      { value: 0.5, label: '0.5x' },
                      { value: 1.0, label: '1.0x' },
                      { value: 1.5, label: '1.5x' },
                      { value: 2.0, label: '2.0x' },
                    ]}
                    valueLabelDisplay="auto"
                  />
                </Box>

                <Box sx={{ mt: 3 }}>
                  <Typography gutterBottom>
                    Utilization Trend: {formatPercent(scenarioParams.utilization_trend)} per month
                  </Typography>
                  <Slider
                    value={scenarioParams.utilization_trend}
                    onChange={(_, value) => setScenarioParams(prev => ({ ...prev, utilization_trend: value as number }))}
                    min={-5}
                    max={5}
                    step={0.1}
                    marks
                    valueLabelDisplay="auto"
                  />
                </Box>

                <Box sx={{ mt: 3 }}>
                  <Typography gutterBottom>
                    Cost Inflation: {(scenarioParams.cost_inflation * 100).toFixed(2)}% per month
                  </Typography>
                  <Slider
                    value={scenarioParams.cost_inflation * 100}
                    onChange={(_, value) => setScenarioParams(prev => ({ ...prev, cost_inflation: (value as number) / 100 }))}
                    min={0}
                    max={5}
                    step={0.1}
                    marks
                    valueLabelDisplay="auto"
                  />
                </Box>

                <Box sx={{ mt: 3 }}>
                  <Typography gutterBottom>
                    Projection Horizon: {scenarioParams.projection_months} months
                  </Typography>
                  <Slider
                    value={scenarioParams.projection_months}
                    onChange={(_, value) => setScenarioParams(prev => ({ ...prev, projection_months: value as number }))}
                    min={1}
                    max={24}
                    step={1}
                    marks={[
                      { value: 1, label: '1m' },
                      { value: 6, label: '6m' },
                      { value: 12, label: '12m' },
                      { value: 24, label: '24m' },
                    ]}
                    valueLabelDisplay="auto"
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {activeTab === 'elasticity' && (
        <Box>
          {elasticityLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : elasticityData ? (
            <ElasticityCurvesDisplay
              elasticityData={elasticityData}
              selectedCategory={selectedCategory || undefined}
              onCategoryChange={(category) => setSelectedCategory(category)}
            />
          ) : (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Elasticity Curves
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  Elasticity analysis models utilization sensitivity to policy friction. Create an elasticity analysis for {selectedPolicy?.name || 'the selected policy'} to visualize elasticity curves. This usually completes within 1–2 minutes.
                </Typography>
                <Button
                  variant="contained"
                  onClick={async () => {
                    if (!selectedPolicy) {
                      setError('Please select a policy first')
                      return
                    }
                    try {
                      setElasticityLoading(true)
                      setError(null)
                      const result = await apiClient.createElasticityAnalysis({
                        policy_id: selectedPolicy.id,
                        service_categories: undefined, // Will model all categories
                      })
                      // Poll for results (large tenants / Celery queue: allow up to ~8 min)
                      let attempts = 0
                      const maxAttempts = 240
                      while (attempts < maxAttempts) {
                        await new Promise((resolve) => setTimeout(resolve, 2000))
                        try {
                          const analysis = await apiClient.getAnalysis(result.id)
                          if (analysis.status === 'COMPLETED') {
                            const results = await apiClient.getAnalysisResults(result.id, 'ELASTICITY')
                            const payload = results.results?.ELASTICITY ?? (results.service_categories ? results : results.results?.[Object.keys(results.results || {})[0]])
                            if (payload?.service_categories && Object.keys(payload.service_categories).length > 0) {
                              setElasticityData(payload)
                              setError(null)
                              break
                            }
                          } else if (analysis.status === 'FAILED') {
                            setError(analysis.error_message || 'Elasticity analysis failed')
                            break
                          }
                        } catch (err) {
                          // Continue polling
                        }
                        attempts++
                      }
                      if (attempts >= maxAttempts) {
                        setError('Elasticity analysis timed out')
                      }
                    } catch (err: any) {
                      setError(err.detail || err.message || 'Failed to create elasticity analysis')
                    } finally {
                      setElasticityLoading(false)
                    }
                  }}
                  disabled={!selectedPolicy || elasticityLoading}
                  startIcon={elasticityLoading ? <CircularProgress size={20} /> : <AnalyticsIcon />}
                >
                  {elasticityLoading ? 'Creating Analysis...' : 'Create Elasticity Analysis'}
                </Button>
              </CardContent>
            </Card>
          )}
        </Box>
      )}

      {activeTab === 'results' && scenarioResult && (
        <Grid container spacing={3}>
          {/* Scenario Summary Header */}
          <Grid item xs={12}>
            <Card sx={{ mb: 3, bgcolor: 'primary.main', color: 'primary.contrastText' }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Box>
                    <Typography variant="h5" gutterBottom sx={{ color: 'primary.contrastText', fontWeight: 600 }}>
                      {scenarioResult.scenario_name || 'Unnamed Scenario'}
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                      {multiPolicyMode && selectedPolicies.length > 1 ? (
                        <>
                          <Chip 
                            label={`${selectedPolicies.length} Policies`} 
                            size="small" 
                            sx={{ bgcolor: 'rgba(255, 255, 255, 0.2)', color: 'primary.contrastText' }}
                          />
                          {selectedPolicies.map((policy) => (
                            <Chip 
                              key={policy.id}
                              label={policy.name} 
                              size="small" 
                              sx={{ bgcolor: 'rgba(255, 255, 255, 0.2)', color: 'primary.contrastText' }}
                            />
                          ))}
                        </>
                      ) : selectedPolicy ? (
                        <Chip 
                          label={selectedPolicy.name} 
                          size="small" 
                          sx={{ bgcolor: 'rgba(255, 255, 255, 0.2)', color: 'primary.contrastText' }}
                        />
                      ) : null}
                      {(scenarioResult as any)._created_at && (
                        <Chip 
                          label={new Date((scenarioResult as any)._created_at).toLocaleString()} 
                          size="small" 
                          sx={{ bgcolor: 'rgba(255, 255, 255, 0.2)', color: 'primary.contrastText' }}
                          icon={<span>📅</span>}
                        />
                      )}
                      {(scenarioResult as any)._analysis_id && (
                        <Chip 
                          label={`ID: ${(scenarioResult as any)._analysis_id.substring(0, 8)}...`} 
                          size="small" 
                          sx={{ bgcolor: 'rgba(255, 255, 255, 0.2)', color: 'primary.contrastText' }}
                        />
                      )}
                    </Box>
                  </Box>
                  {scenarioResult.confidence_score !== undefined && (
                    <Box sx={{ textAlign: 'right' }}>
                      <Typography variant="body2" sx={{ color: 'primary.contrastText', mb: 0.5 }}>
                        Confidence (reliability of projection)
                      </Typography>
                      <Typography 
                        variant="h4" 
                        sx={{ 
                          color: scenarioResult.confidence_score >= 80 ? 'success.light' :
                                 scenarioResult.confidence_score >= 60 ? 'warning.light' :
                                 scenarioResult.confidence_score >= 40 ? 'info.light' : 'error.light',
                          fontWeight: 600
                        }}
                      >
                        {scenarioResult.confidence_score?.toFixed(0) || 0}%
                      </Typography>
                    </Box>
                  )}
                </Box>
                
                {/* Scenario Parameters Summary */}
                <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid rgba(255, 255, 255, 0.2)' }}>
                  <Typography variant="subtitle2" sx={{ color: 'primary.contrastText', mb: 1, opacity: 0.9 }}>
                    Scenario Parameters
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                    <Typography variant="body2" sx={{ color: 'primary.contrastText', opacity: 0.9 }}>
                      <strong>Projection Horizon:</strong> {scenarioParams.projection_months} months
                    </Typography>
                    <Typography variant="body2" sx={{ color: 'primary.contrastText', opacity: 0.9 }}>
                      <strong>Cost Inflation:</strong> {(scenarioParams.cost_inflation * 100).toFixed(1)}%
                    </Typography>
                    {scenarioParams.member_count_multiplier !== 1.0 && (
                      <Typography variant="body2" sx={{ color: 'primary.contrastText', opacity: 0.9 }}>
                        <strong>Member Count:</strong> {scenarioParams.member_count_multiplier.toFixed(2)}x
                      </Typography>
                    )}
                    {scenarioParams.utilization_trend !== 0.0 && (
                      <Typography variant="body2" sx={{ color: 'primary.contrastText', opacity: 0.9 }}>
                        <strong>Utilization Trend:</strong> {formatPercent(scenarioParams.utilization_trend)}/month
                      </Typography>
                    )}
                    {Object.keys(scenarioParams.lever_adjustments || {}).length > 0 && (
                      <Typography variant="body2" sx={{ color: 'primary.contrastText', opacity: 0.9 }}>
                        <strong>Lever Adjustments:</strong> {Object.keys(scenarioParams.lever_adjustments).length} active
                      </Typography>
                    )}
                    {Object.keys(scenarioParams.elasticity_adjustments || {}).length > 0 && (
                      <Typography variant="body2" sx={{ color: 'primary.contrastText', opacity: 0.9 }}>
                        <strong>Elasticity Adjustments:</strong> {Object.keys(scenarioParams.elasticity_adjustments).length} categories
                      </Typography>
                    )}
                    {scenarioResult.impact_metrics.tradeoff_analysis && (
                      <Typography variant="body2" sx={{ color: 'primary.contrastText', opacity: 0.9 }}>
                        <strong>Efficiency Score (cost vs utilization tradeoff):</strong> {scenarioResult.impact_metrics.tradeoff_analysis.efficiency_score.toFixed(0)}%
                      </Typography>
                    )}
                  </Box>
                  
                  {/* Confidence Score Explanation */}
                  {scenarioResult.confidence_score !== undefined && scenarioResult.confidence_score < 60 && (
                    <Alert 
                      severity="info" 
                      sx={{ 
                        mt: 2, 
                        bgcolor: 'rgba(255, 255, 255, 0.1)',
                        color: 'primary.contrastText',
                        '& .MuiAlert-icon': { color: 'primary.contrastText' }
                      }}
                    >
                      <Typography variant="body2" sx={{ color: 'primary.contrastText', fontWeight: 600, mb: 0.5 }}>
                        Low Confidence Score ({scenarioResult.confidence_score.toFixed(0)}%)
                      </Typography>
                      <Typography variant="body2" sx={{ color: 'primary.contrastText', opacity: 0.9, fontSize: '0.85rem' }}>
                        To improve: Use shorter projection horizon (≤12 months), ensure sufficient baseline data (500+ claims), and run elasticity analysis for more accurate models.
                      </Typography>
                    </Alert>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={8}>
            {/* Explain why all numbers are 0 when no baseline data */}
            {scenarioResult.baseline_metrics?.claim_count === 0 && scenarioResult.projected_metrics?.claim_count === 0 && (
              <Alert severity="info" sx={{ mb: 2 }}>
                All metrics are 0 because no baseline or claims data is loaded for this policy. Load baseline or claims data (Ingestion / Data Health) to see non-zero projections.
              </Alert>
            )}
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Impact Summary
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6} md={4}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="body2" color="text.secondary">
                        Utilization per 1k
                      </Typography>
                      <Typography variant="h5" color={scenarioResult.impact_metrics.percent_changes.utilization_per_1k < 0 ? 'success.main' : 'error.main'}>
                        {formatPercent(scenarioResult.impact_metrics.percent_changes.utilization_per_1k)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {scenarioResult.baseline_metrics.utilization_per_1k.toFixed(2)} → {scenarioResult.projected_metrics.utilization_per_1k.toFixed(2)}
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={12} sm={6} md={4}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="body2" color="text.secondary">
                        Allowed PMPM
                      </Typography>
                      <Typography variant="h5" color={scenarioResult.impact_metrics.percent_changes.allowed_pmpm < 0 ? 'success.main' : 'error.main'}>
                        {formatPercent(scenarioResult.impact_metrics.percent_changes.allowed_pmpm)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {formatCurrency(scenarioResult.baseline_metrics.allowed_pmpm)} → {formatCurrency(scenarioResult.projected_metrics.allowed_pmpm)}
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={12} sm={6} md={4}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="body2" color="text.secondary">
                        Paid PMPM
                      </Typography>
                      <Typography variant="h5" color={scenarioResult.impact_metrics.percent_changes.paid_pmpm < 0 ? 'success.main' : 'error.main'}>
                        {formatPercent(scenarioResult.impact_metrics.percent_changes.paid_pmpm)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {formatCurrency(scenarioResult.baseline_metrics.paid_pmpm)} → {formatCurrency(scenarioResult.projected_metrics.paid_pmpm)}
                      </Typography>
                    </Paper>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>

            {/* Tradeoff Analysis */}
            {scenarioResult.impact_metrics.tradeoff_analysis && (
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Tradeoff Analysis: Cost vs Utilization
                  </Typography>
                  <Grid container spacing={3} sx={{ mt: 1 }}>
                    <Grid item xs={12} md={6}>
                      <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'background.paper' }}>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Efficiency Score
                        </Typography>
                        <Typography 
                          variant="h3" 
                          sx={{ 
                            color: scenarioResult.impact_metrics.tradeoff_analysis.efficiency_score >= 80 ? 'success.main' :
                                   scenarioResult.impact_metrics.tradeoff_analysis.efficiency_score >= 60 ? 'warning.main' :
                                   scenarioResult.impact_metrics.tradeoff_analysis.efficiency_score >= 40 ? 'info.main' : 'error.main',
                            fontWeight: 600,
                          }}
                        >
                          {scenarioResult.impact_metrics.tradeoff_analysis.efficiency_score.toFixed(0)}
                        </Typography>
                        <Chip 
                          label={scenarioResult.impact_metrics.tradeoff_analysis.efficiency_category}
                          color={
                            scenarioResult.impact_metrics.tradeoff_analysis.efficiency_category === 'HIGH' ? 'success' :
                            scenarioResult.impact_metrics.tradeoff_analysis.efficiency_category === 'MEDIUM' ? 'warning' :
                            scenarioResult.impact_metrics.tradeoff_analysis.efficiency_category === 'LOW' ? 'info' : 'error'
                          }
                          size="small"
                          sx={{ mt: 1 }}
                        />
                      </Paper>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Paper sx={{ p: 2 }}>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Tradeoff Ratio
                        </Typography>
                        <Typography variant="h6">
                          {scenarioResult.impact_metrics.tradeoff_analysis.tradeoff_ratio.toFixed(2)}%
                        </Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                          Cost change per 1% utilization change
                        </Typography>
                        <Typography variant="body2" sx={{ mt: 2, fontStyle: 'italic' }}>
                          {scenarioResult.impact_metrics.tradeoff_analysis.interpretation}
                        </Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={12}>
                      <Paper sx={{ p: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Impact Breakdown
                        </Typography>
                        <Grid container spacing={2}>
                          <Grid item xs={6}>
                            <Typography variant="body2" color="text.secondary">
                              Utilization Change
                            </Typography>
                            <Typography 
                              variant="h6" 
                              color={scenarioResult.impact_metrics.tradeoff_analysis.utilization_change_pct < 0 ? 'success.main' : 'error.main'}
                            >
                              {formatPercent(scenarioResult.impact_metrics.tradeoff_analysis.utilization_change_pct)}
                            </Typography>
                          </Grid>
                          <Grid item xs={6}>
                            <Typography variant="body2" color="text.secondary">
                              Cost Change
                            </Typography>
                            <Typography 
                              variant="h6" 
                              color={scenarioResult.impact_metrics.tradeoff_analysis.cost_change_pct < 0 ? 'success.main' : 'error.main'}
                            >
                              {formatPercent(scenarioResult.impact_metrics.tradeoff_analysis.cost_change_pct)}
                            </Typography>
                          </Grid>
                        </Grid>
                      </Paper>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            )}

            {/* Risk Analysis */}
            {scenarioResult.impact_metrics.risk_analysis && (
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Risk Analysis
                  </Typography>
                  <Box sx={{ mb: 2 }}>
                    <Chip 
                      label={`Risk Level: ${scenarioResult.impact_metrics.risk_analysis.risk_level}`}
                      color={
                        scenarioResult.impact_metrics.risk_analysis.risk_level === 'HIGH' ? 'error' :
                        scenarioResult.impact_metrics.risk_analysis.risk_level === 'MEDIUM' ? 'warning' :
                        scenarioResult.impact_metrics.risk_analysis.risk_level === 'LOW' ? 'info' : 'success'
                      }
                      sx={{ mb: 2 }}
                    />
                    <Typography variant="body2" color="text.secondary">
                      {scenarioResult.impact_metrics.risk_analysis.risk_summary}
                    </Typography>
                  </Box>
                  
                  <Grid container spacing={3} sx={{ mt: 1 }}>
                    <Grid item xs={12} md={6}>
                      <Paper sx={{ p: 2, border: '2px solid', borderColor: 'error.main' }}>
                        <Typography variant="subtitle1" gutterBottom color="error.main">
                          Worst-Case Scenario
                        </Typography>
                        <Table size="small">
                          <TableBody>
                            <TableRow>
                              <TableCell>Utilization per 1k</TableCell>
                              <TableCell align="right">
                                {scenarioResult.impact_metrics.risk_analysis.worst_case.utilization_per_1k.toFixed(2)}
                                {' '}
                                <Typography component="span" variant="caption" color="error.main">
                                  ({formatPercent(scenarioResult.impact_metrics.risk_analysis.worst_case.utilization_change_pct)})
                                </Typography>
                              </TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>Cost PMPM</TableCell>
                              <TableCell align="right">
                                {formatCurrency(scenarioResult.impact_metrics.risk_analysis.worst_case.cost_pmpm)}
                                {' '}
                                <Typography component="span" variant="caption" color="error.main">
                                  ({formatPercent(scenarioResult.impact_metrics.risk_analysis.worst_case.cost_change_pct)})
                                </Typography>
                              </TableCell>
                            </TableRow>
                          </TableBody>
                        </Table>
                      </Paper>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Paper sx={{ p: 2, border: '2px solid', borderColor: 'success.main' }}>
                        <Typography variant="subtitle1" gutterBottom color="success.main">
                          Best-Case Scenario
                        </Typography>
                        <Table size="small">
                          <TableBody>
                            <TableRow>
                              <TableCell>Utilization per 1k</TableCell>
                              <TableCell align="right">
                                {scenarioResult.impact_metrics.risk_analysis.best_case.utilization_per_1k.toFixed(2)}
                                {' '}
                                <Typography component="span" variant="caption" color="success.main">
                                  ({formatPercent(scenarioResult.impact_metrics.risk_analysis.best_case.utilization_change_pct)})
                                </Typography>
                              </TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>Cost PMPM</TableCell>
                              <TableCell align="right">
                                {formatCurrency(scenarioResult.impact_metrics.risk_analysis.best_case.cost_pmpm)}
                                {' '}
                                <Typography component="span" variant="caption" color="success.main">
                                  ({formatPercent(scenarioResult.impact_metrics.risk_analysis.best_case.cost_change_pct)})
                                </Typography>
                              </TableCell>
                            </TableRow>
                          </TableBody>
                        </Table>
                      </Paper>
                    </Grid>
                    {scenarioResult.impact_metrics.risk_analysis.risk_factors.length > 0 && (
                      <Grid item xs={12}>
                        <Paper sx={{ p: 2 }}>
                          <Typography variant="subtitle2" gutterBottom>
                            Risk Factors
                          </Typography>
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                            {scenarioResult.impact_metrics.risk_analysis.risk_factors.map((factor, idx) => (
                              <Chip 
                                key={idx}
                                label={factor.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                                color="warning"
                                size="small"
                              />
                            ))}
                          </Box>
                        </Paper>
                      </Grid>
                    )}
                  </Grid>
                </CardContent>
              </Card>
            )}

            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Confidence Intervals (95%)
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Metric</TableCell>
                        <TableCell align="right">Baseline</TableCell>
                        <TableCell align="right">Projected</TableCell>
                        <TableCell align="right">Lower Bound</TableCell>
                        <TableCell align="right">Upper Bound</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      <TableRow>
                        <TableCell>Utilization per 1k</TableCell>
                        <TableCell align="right">{scenarioResult.baseline_metrics.utilization_per_1k.toFixed(2)}</TableCell>
                        <TableCell align="right">{scenarioResult.projected_metrics.utilization_per_1k.toFixed(2)}</TableCell>
                        <TableCell align="right">{scenarioResult.confidence_intervals.utilization_per_1k[0].toFixed(2)}</TableCell>
                        <TableCell align="right">{scenarioResult.confidence_intervals.utilization_per_1k[1].toFixed(2)}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Allowed PMPM</TableCell>
                        <TableCell align="right">{formatCurrency(scenarioResult.baseline_metrics.allowed_pmpm)}</TableCell>
                        <TableCell align="right">{formatCurrency(scenarioResult.projected_metrics.allowed_pmpm)}</TableCell>
                        <TableCell align="right">{formatCurrency(scenarioResult.confidence_intervals.allowed_pmpm[0])}</TableCell>
                        <TableCell align="right">{formatCurrency(scenarioResult.confidence_intervals.allowed_pmpm[1])}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Paid PMPM</TableCell>
                        <TableCell align="right">{formatCurrency(scenarioResult.baseline_metrics.paid_pmpm)}</TableCell>
                        <TableCell align="right">{formatCurrency(scenarioResult.projected_metrics.paid_pmpm)}</TableCell>
                        <TableCell align="right">{formatCurrency(scenarioResult.confidence_intervals.paid_pmpm[0])}</TableCell>
                        <TableCell align="right">{formatCurrency(scenarioResult.confidence_intervals.paid_pmpm[1])}</TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <TrustPanel
              confidenceScore={scenarioResult.confidence_score}
              dataCoverage={{
                claimMonths: scenarioParams.projection_months,
              }}
              checks={[]}
              limitations={[
                "Projections based on historical patterns",
                "Does not account for external factors",
                "Elasticity estimates may vary",
              ]}
            />
          </Grid>
        </Grid>
      )}

      {activeTab === 'compare' && scenarios.length > 0 && (
        <Box className="scenario-comparison">
          <ScenarioComparison
            scenarios={scenarios}
            onRemoveScenario={(scenarioId) => {
              setScenarios((prev) => prev.filter((s) => s.scenario_id !== scenarioId))
              if (scenarioResult?.scenario_id === scenarioId) {
                setScenarioResult(scenarios.find((s) => s.scenario_id !== scenarioId) || null)
              }
            }}
            onRenameScenario={(scenarioId, name) => {
              setScenarios((prev) =>
                prev.map((s) => (s.scenario_id === scenarioId ? { ...s, scenario_name: name } : s))
              )
              if (scenarioResult?.scenario_id === scenarioId) {
                // Note: scenario_name is stored in scenarios array, not in scenarioResult
              // The ScenarioResult interface doesn\'t include scenario_name
              }
            }}
          />
        </Box>
      )}

      {activeTab === 'sensitivity' && scenarioResult && scenarioResult.sensitivity_analysis && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Sensitivity Analysis
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Impact of individual parameter adjustments
            </Typography>
            
            {scenarioResult.sensitivity_analysis.lever_adjustments && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle1" gutterBottom>
                  Lever Adjustments
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Lever</TableCell>
                        <TableCell align="right">Estimated Impact</TableCell>
                        <TableCell>Parameters</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {Object.entries(scenarioResult.sensitivity_analysis.lever_adjustments).map(([leverId, data]: [string, any]) => (
                        <TableRow key={leverId}>
                          <TableCell>{leverId.replace(/_/g, ' ')}</TableCell>
                          <TableCell align="right">
                            {formatPercent(data.estimated_impact_percent || 0)}
                          </TableCell>
                          <TableCell>
                            {JSON.stringify(data.parameters || {})}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            )}

            {scenarioResult.sensitivity_analysis.environmental_variables && (
              <Box>
                <Typography variant="subtitle1" gutterBottom>
                  Environmental Variables
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Variable</TableCell>
                        <TableCell>Value</TableCell>
                        <TableCell>Impact</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {Object.entries(scenarioResult.sensitivity_analysis.environmental_variables).map(([varName, data]: [string, any]) => (
                        <TableRow key={varName}>
                          <TableCell>{varName.replace(/_/g, ' ')}</TableCell>
                          <TableCell>{data.value}</TableCell>
                          <TableCell>{data.impact}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            )}
          </CardContent>
        </Card>
      )}
      
      {/* Scenario Accuracy Tab (Phase 7) */}
      {activeTab === 'accuracy' && (
        <Box>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  Scenario Accuracy Tracking
                </Typography>
                <Box>
                  {currentScenarioAnalysisId && (
                    <>
                      <Button
                        variant="outlined"
                        size="small"
                        onClick={() => setLinkDialogOpen(true)}
                        sx={{ mr: 1 }}
                      >
                        Link to Policy
                      </Button>
                      <Button
                        variant="outlined"
                        size="small"
                        onClick={() => setAccuracyDialogOpen(true)}
                      >
                        Compute Accuracy
                      </Button>
                    </>
                  )}
                </Box>
              </Box>
              
              {scenarioLinks.length > 0 && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    Scenario Links ({scenarioLinks.length})
                  </Typography>
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Scenario ID</TableCell>
                          <TableCell>Policy ID</TableCell>
                          <TableCell>Linked At</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {scenarioLinks.map((link) => (
                          <TableRow key={link.link_id}>
                            <TableCell>{link.scenario_id.substring(0, 8)}...</TableCell>
                            <TableCell>{link.policy_id.substring(0, 8)}...</TableCell>
                            <TableCell>{new Date(link.linked_at).toLocaleString()}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Box>
              )}
              
              {scenarioAccuracy.length > 0 ? (
                <Box>
                  <Typography variant="subtitle1" gutterBottom>
                    Accuracy Records ({scenarioAccuracy.length})
                  </Typography>
                  {scenarioAccuracy.map((acc) => (
                    <Card key={acc.accuracy_id} sx={{ mb: 2 }}>
                      <CardContent>
                        <Grid container spacing={2}>
                          <Grid item xs={12} md={6}>
                            <Typography variant="subtitle2" color="text.secondary">
                              Overall Accuracy
                            </Typography>
                            <Typography variant="h4" color={
                              acc.accuracy_metrics.overall_accuracy_pct >= 80 ? 'success.main' :
                              acc.accuracy_metrics.overall_accuracy_pct >= 60 ? 'warning.main' : 'error.main'
                            }>
                              {acc.accuracy_metrics.overall_accuracy_pct.toFixed(1)}%
                            </Typography>
                          </Grid>
                          <Grid item xs={12} md={6}>
                            <Typography variant="subtitle2" color="text.secondary">
                              Utilization Accuracy
                            </Typography>
                            <Typography variant="h6">
                              {acc.accuracy_metrics.utilization_accuracy.accuracy_pct.toFixed(1)}%
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Predicted: {acc.accuracy_metrics.utilization_accuracy.predicted_pct.toFixed(1)}% | 
                              Observed: {acc.accuracy_metrics.utilization_accuracy.observed_pct.toFixed(1)}% | 
                              Error: {acc.accuracy_metrics.utilization_accuracy.error_pct.toFixed(1)}%
                            </Typography>
                          </Grid>
                          <Grid item xs={12} md={6}>
                            <Typography variant="subtitle2" color="text.secondary">
                              Cost Accuracy
                            </Typography>
                            <Typography variant="h6">
                              {acc.accuracy_metrics.cost_accuracy.accuracy_pct.toFixed(1)}%
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Predicted: {acc.accuracy_metrics.cost_accuracy.predicted_pct.toFixed(1)}% | 
                              Observed: {acc.accuracy_metrics.cost_accuracy.observed_pct.toFixed(1)}% | 
                              Error: {acc.accuracy_metrics.cost_accuracy.error_pct.toFixed(1)}%
                            </Typography>
                          </Grid>
                          <Grid item xs={12}>
                            <Typography variant="caption" color="text.secondary">
                              Computed: {new Date(acc.computed_at).toLocaleString()}
                            </Typography>
                          </Grid>
                        </Grid>
                      </CardContent>
                    </Card>
                  ))}
                </Box>
              ) : (
                <Alert severity="info">
                  No accuracy records found. Link a scenario to a policy and compute accuracy after observations are available.
                </Alert>
              )}
            </CardContent>
          </Card>
        </Box>
      )}
      
      {/* Link Scenario Dialog */}
      <Dialog open={linkDialogOpen} onClose={() => setLinkDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Link Scenario to Policy</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Link this scenario to a policy implementation to enable accuracy tracking.
          </Typography>
          {selectedPolicy && (
            <Alert severity="info" sx={{ mb: 2 }}>
              Policy: {selectedPolicy.name}
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setLinkDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleLinkScenario} variant="contained">
            Link
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Compute Accuracy Dialog */}
      <Dialog open={accuracyDialogOpen} onClose={() => setAccuracyDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Compute Scenario Accuracy</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Select an observation to compare against this scenario's predictions.
          </Typography>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Observation</InputLabel>
            <Select
              value={selectedObservationId || ''}
              onChange={(e) => setSelectedObservationId(e.target.value)}
              label="Observation"
            >
              {observations.map((obs) => (
                <MenuItem key={obs.observation_id} value={obs.observation_id}>
                  {new Date(obs.observation_period_start || obs.computed_at).toLocaleDateString()} - 
                  {new Date(obs.observation_period_end || obs.computed_at).toLocaleDateString()}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAccuracyDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleComputeAccuracy} 
            variant="contained"
            disabled={!selectedObservationId}
          >
            Compute Accuracy
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

