/**
 * Baseline Analysis Page - Stage 3: Baseline Utilization + Baseline Behavior Profiling
 * Enhanced with name field, comparison functionality, and rich visualizations
 */
import { useState, useEffect } from 'react'
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
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
  Alert,
  Tabs,
  Tab,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Divider,
  LinearProgress,
  InputAdornment,
  Pagination,
  Stack,
} from '@mui/material'
import {
  PlayArrow as RunIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  TrendingUp as TrendingIcon,
  Assessment as BenchmarkIcon,
  Group as ProviderIcon,
  People as PatientIcon,
  Event as CalendarIcon,
  Cancel as CancelIcon,
  CompareArrows as CompareIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  ArrowBack as BackIcon,
} from '@mui/icons-material'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  Area,
  AreaChart,
  PieChart,
  Pie,
  Cell,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ScatterChart,
  Scatter,
  ZAxis,
} from 'recharts'
import { apiClient } from '../lib/api'
import { format } from 'date-fns'
import { healthForesightColors } from '../theme/healthForesightTheme'
import MetricTooltip from '../components/MetricTooltip'

interface BaselineAnalysis {
  id: string
  name?: string
  status: string
  created_at: string
  result?: BaselineAnalysisResult | null
  loading?: boolean
}

interface ArchetypeNarrative {
  archetype_id: number
  archetype_name: string
  interpretation?: string
  key_insights?: string[]
  recommendations?: string[]
  calculation_notes?: Record<string, string>
}

interface BaselineAnalysisResult {
  analysis_id: string
  time_series?: TimeSeriesPoint[]
  benchmarks?: Benchmark[]
  provider_archetypes?: ProviderArchetype[]
  patient_segments?: PatientSegment[]
  confounder_events?: ConfounderEvent[]
  data_coverage?: any
  model_parameters?: any
  archetype_narratives?: ArchetypeNarrative[]
  baseline_summary_narrative?: {
    summary?: string
    key_findings?: string[]
    recommendations?: string[]
  }
}

interface TimeSeriesPoint {
  date: string
  observed: number
  trend: number
  seasonal: number
  residual: number
  lower_bound: number
  upper_bound: number
}

interface Benchmark {
  metric_name: string
  metric_value: number
  unit: string
  segment?: string
  segment_value?: string
  sample_size: number
}

interface ProviderArchetype {
  archetype_id: number
  archetype_name: string
  provider_count: number
  characteristics: Record<string, any>
  representative_providers: string[]
}

interface PatientSegment {
  segment_id: number
  segment_name: string
  member_count: number
  characteristics: Record<string, any>
  utilization_profile: Record<string, number>
}

interface ConfounderEvent {
  event_date: string
  event_type: string
  event_description: string
  impact_magnitude?: number
  affected_segments: string[]
}

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#00ff00', '#0088fe', '#00c49f', '#ffbb28', '#ff8042']

export default function BaselineAnalysisPage() {
  const [analyses, setAnalyses] = useState<BaselineAnalysis[]>([])
  const [selectedAnalysis, setSelectedAnalysis] = useState<BaselineAnalysis | null>(null)
  const [compareAnalysis1, setCompareAnalysis1] = useState<BaselineAnalysis | null>(null)
  const [compareAnalysis2, setCompareAnalysis2] = useState<BaselineAnalysis | null>(null)
  const [compareMode, setCompareMode] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [running, setRunning] = useState(false)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [tabValue, setTabValue] = useState(0)
  // Default baseline window: 12 months ago through today (ISO date strings)
  const defaultBaselineFrom = format(new Date(Date.now() - 365 * 24 * 60 * 60 * 1000), 'yyyy-MM-dd')
  const defaultBaselineTo = format(new Date(), 'yyyy-MM-dd')
  const [formData, setFormData] = useState({
    name: '',
    start_date: defaultBaselineFrom,
    end_date: defaultBaselineTo,
    n_clusters: 5,
    baseline_type: 'GENERAL' as 'GENERAL' | 'POLICY_SPECIFIC',
    policy_id: '' as string | '',
  })
  const [refreshingBaseline, setRefreshingBaseline] = useState(false)
  const [refreshingAllStoredBaselines, setRefreshingAllStoredBaselines] = useState(false)
  const [generatingAllBaselines, setGeneratingAllBaselines] = useState(false)
  const [generatingProgress, setGeneratingProgress] = useState<{ current: number; total: number; name: string } | null>(null)
  const [generateAllDialogOpen, setGenerateAllDialogOpen] = useState(false)
  const generateAllDefaultFrom = format(new Date(Date.now() - 365 * 24 * 60 * 60 * 1000), 'yyyy-MM-dd')
  const generateAllDefaultTo = format(new Date(), 'yyyy-MM-dd')
  const [generateAllDateRange, setGenerateAllDateRange] = useState({ start_date: generateAllDefaultFrom, end_date: generateAllDefaultTo })
  const [baselines, setBaselines] = useState<any[]>([])
  const [policies, setPolicies] = useState<any[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('ALL')
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage] = useState(20)
  /** Unified selection: when user selects a stored baseline from the combined list */
  const [selectedStoredBaseline, setSelectedStoredBaseline] = useState<any | null>(null)

  useEffect(() => {
    loadAnalyses()
    loadBaselines()
    loadPolicies()
  }, [])

  // Add error boundary - if error persists, show empty state
  useEffect(() => {
    if (error && analyses.length === 0 && !loading) {
      // If we have an error and no analyses after loading completes, 
      // clear error after 5 seconds to allow user to retry
      const timer = setTimeout(() => {
        setError(null)
      }, 5000)
      return () => clearTimeout(timer)
    }
  }, [error, analyses.length, loading])

  const loadPolicies = async () => {
    try {
      const data = await apiClient.getPolicies()
      const policiesList = Array.isArray(data) ? data : (data.items || [])
      setPolicies(policiesList)
    } catch (err: any) {
      console.error('Error loading policies:', err)
    }
  }

  const loadBaselines = async () => {
    try {
      const data = await apiClient.listBaselines()
      const list = Array.isArray(data) ? data : (data?.items ?? data?.data ?? data?.baselines ?? [])
      setBaselines(Array.isArray(list) ? list : [])
    } catch (err: any) {
      console.error('Error loading baselines:', err)
      setBaselines([])
    }
  }

  const handleRefreshBaseline = async (policyId?: string) => {
    try {
      setRefreshingBaseline(true)
      setError(null)
      
      const result = await apiClient.refreshBaseline(policyId, 'ROLLING', 12)
      
      alert(
        `Baseline refreshed successfully!\n` +
        `Baseline ID: ${result.baseline_id}\n` +
        `Type: ${result.baseline_type}\n` +
        `Window: ${result.window_start_date} to ${result.window_end_date}`
      )
      
      await loadBaselines()
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to refresh baseline')
      console.error('Error refreshing baseline:', err)
    } finally {
      setRefreshingBaseline(false)
    }
  }

  /** Stored baselines from DB (tenant + each policy) — includes claim-derived archetypes/segments; no sklearn required. */
  const handleRefreshAllStoredBaselines = async () => {
    try {
      setRefreshingAllStoredBaselines(true)
      setError(null)
      const res = await apiClient.refreshAllBaselines('ROLLING', 12)
      const nPolicy = Array.isArray(res?.policy_baselines) ? res.policy_baselines.length : 0
      const hasGen = Boolean(res?.general_baseline)
      alert(
        `Stored baselines refreshed.\nGeneral: ${hasGen ? 'yes' : 'no'}\nPolicy rows: ${nPolicy}` +
          (res?.errors?.length ? `\nWarnings: ${res.errors.slice(0, 3).join('; ')}` : '')
      )
      await loadBaselines()
    } catch (err: any) {
      const detail = err?.response?.data?.detail ?? err?.detail ?? err?.message ?? 'Failed to refresh all baselines'
      setError(typeof detail === 'string' ? detail : JSON.stringify(detail))
      console.error('Error refresh-all baselines:', err)
    } finally {
      setRefreshingAllStoredBaselines(false)
    }
  }

  const handleGenerateAllBaselines = async (start_date: string, end_date: string) => {
    try {
      setGenerateAllDialogOpen(false)
      setGeneratingAllBaselines(true)
      setError(null)
      setGeneratingProgress(null)
      const policiesResponse = await apiClient.getPolicies()
      const policyList = Array.isArray(policiesResponse) ? policiesResponse : (policiesResponse as any)?.items ?? []
      const suffix = new Date().toISOString().slice(0, 19).replace(/[-:T]/g, '').replace(/(\d{8})(\d{6})/, '$1_$2')
      const tasks: { name: string; baseline_type: 'GENERAL' | 'POLICY_SPECIFIC'; policy_id?: string }[] = [
        { name: `General Baseline ${suffix}`, baseline_type: 'GENERAL' },
        ...policyList.map((p: any) => {
          const id = p.id ?? p.policy_id
          const label = (p.name ?? p.policy_name ?? String(id)).slice(0, 50)
          return { name: `${label} Baseline ${suffix}`, baseline_type: 'POLICY_SPECIFIC' as const, policy_id: id }
        }),
      ].filter((t) => t.baseline_type === 'GENERAL' || t.policy_id)

      const created: { id: string; name: string; status: string }[] = []
      const errs: { name: string; detail: string }[] = []
      const total = tasks.length

      for (let i = 0; i < tasks.length; i++) {
        const task = tasks[i]
        setGeneratingProgress({ current: i + 1, total, name: task.name })
        try {
          const result = await apiClient.createBaselineAnalysis({
            name: task.name,
            baseline_type: task.baseline_type,
            policy_id: task.policy_id ?? undefined,
            n_clusters: 5,
            start_date: start_date || undefined,
            end_date: end_date || undefined,
          })
          created.push({ id: result.id, name: result.name, status: result.status })
        } catch (e: any) {
          const detail = typeof e?.response?.data?.detail === 'string' ? e.response.data.detail : (e?.message ?? String(e))
          errs.push({ name: task.name, detail })
        }
      }

      setGeneratingProgress(null)
      const message = [
        `Full analyses created: ${created.length} of ${total}.`,
        ...(errs.length > 0 ? ['Errors: ' + errs.slice(0, 5).map((e) => `${e.name}: ${e.detail}`).join('; ') + (errs.length > 5 ? ` (+${errs.length - 5} more)` : '')] : []),
      ].join('\n')
      alert(message)
      await loadAnalyses()
      await loadBaselines()
      setTimeout(() => { loadAnalyses(); loadBaselines() }, 800)
    } catch (err: any) {
      setError(err.detail || err.response?.data?.detail || err.message || 'Failed to generate all baselines')
      console.error('Error generating all baselines:', err)
    } finally {
      setGeneratingAllBaselines(false)
      setGeneratingProgress(null)
    }
  }

  const loadAnalyses = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await apiClient.getAnalyses({ analysis_type: 'BASELINE' })
      const analysesList = Array.isArray(data) ? data : (data.items || [])
      
      console.log(`Loaded ${analysesList.length} baseline analyses`)
      
      // DON'T load results here - load lazily when user selects an analysis
      // This prevents timeout issues when there are many analyses
      const analysesWithoutResults = analysesList.map((analysis: any) => ({
        id: analysis.id,
        name: analysis.name,
        status: analysis.status,
        created_at: analysis.created_at,
        result: null, // Will be loaded on demand
      }))
      
      setAnalyses(analysesWithoutResults)
      
      // Select the most recent COMPLETED analysis (but don't load results yet)
      if (analysesWithoutResults.length > 0) {
        const latestCompleted = analysesWithoutResults.find(a => a.status === 'COMPLETED')
        if (latestCompleted) {
          setSelectedAnalysis(latestCompleted)
          // Load results for the selected analysis asynchronously (don't await)
          // This prevents blocking the page load
          setTimeout(() => {
            loadAnalysisResults(latestCompleted.id).catch(err => {
              console.error('Error loading initial analysis results:', err)
            })
          }, 100)
        } else {
          // If no completed, select the first one
          setSelectedAnalysis(analysesWithoutResults[0])
        }
      }
    } catch (err: any) {
      console.error('Error loading baseline analyses:', err)
      const errorMsg = err.detail || err.message || 'Failed to load baseline analyses'
      setError(errorMsg)
      // Set empty array so page can still render
      setAnalyses([])
    } finally {
      setLoading(false)
    }
  }

  const loadAnalysisResults = async (analysisId: string) => {
    // Check if already loading or loaded
    const currentAnalysis = analyses.find(a => a.id === analysisId)
    if (currentAnalysis?.loading || (currentAnalysis?.result !== null && currentAnalysis?.result !== undefined)) {
      console.log(`Skipping load for ${analysisId}: already loading or loaded`)
      return // Already loading or loaded
    }
    
    try {
      console.log(`Loading baseline results for analysis: ${analysisId}`)
      
      // Set loading state
      setAnalyses((prev) =>
        prev.map((a) =>
          a.id === analysisId ? { ...a, loading: true } : a
        )
      )
      setSelectedAnalysis((prev) => {
        if (prev && prev.id === analysisId) {
          return { ...prev, loading: true }
        }
        return prev
      })
      
      const result = await apiClient.getBaselineAnalysis(analysisId)
      // API returns { id, name, status, created_at, result } — result may be null if no baseline stored for this analysis
      const updatedResult =
        result?.result ?? (result as { result_data?: unknown })?.result_data ?? null

      if (updatedResult && typeof updatedResult === 'object') {
        console.log(`Setting result for ${analysisId}, keys:`, Object.keys(updatedResult).slice(0, 5))
      } else if (result?.status === 'COMPLETED') {
        console.warn(`No result payload for completed analysis ${analysisId} — baseline may not be stored yet`)
      }
      
      setSelectedAnalysis((prev) => {
        if (prev && prev.id === analysisId) {
          return {
            ...prev,
            result: updatedResult,
            loading: false,
          }
        }
        return prev
      })
      
      setAnalyses((prev) =>
        prev.map((a) =>
          a.id === analysisId
            ? { ...a, result: updatedResult, loading: false }
            : a
        )
      )
      
      console.log(`✅ Successfully loaded and set results for ${analysisId}`)
    } catch (err: any) {
      console.error(`❌ Error loading baseline results for ${analysisId}:`, err)
      console.error('Error details:', {
        message: err.message,
        status: err.response?.status,
        data: err.response?.data,
      })
      
      // Clear loading state on error
      setAnalyses((prev) =>
        prev.map((a) =>
          a.id === analysisId ? { ...a, loading: false, error: err.message } : a
        )
      )
      setSelectedAnalysis((prev) => {
        if (prev && prev.id === analysisId) {
          return { ...prev, loading: false, error: err.message }
        }
        return prev
      })
      
      // Show error to user
      if (err.response?.status === 404) {
        setError(`Baseline analysis ${analysisId} not found`)
      } else if (err.response?.status === 401 || err.response?.status === 403) {
        setError('Authentication error. Please refresh the page.')
      } else if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
        setError('Request timed out. The baseline results may be very large. Please try again.')
      } else {
        setError(`Failed to load baseline results: ${err.message || 'Unknown error'}`)
      }
    }
  }

  const handleRunAnalysis = async () => {
    if (!formData.name || formData.name.trim() === '') {
      setError('Analysis name is required')
      return
    }
    if (!formData.start_date || !formData.end_date) {
      setError('Please select both From date and To date for the baseline period')
      return
    }
    if (formData.start_date > formData.end_date) {
      setError('From date must be on or before To date')
      return
    }

    try {
      setRunning(true)
      setError(null)
      
      const data: any = {
        name: formData.name.trim(),
        start_date: formData.start_date,
        end_date: formData.end_date,
        n_clusters: formData.n_clusters,
        baseline_type: formData.baseline_type,
      }
      
      // Add policy_id if baseline_type is POLICY_SPECIFIC
      if (formData.baseline_type === 'POLICY_SPECIFIC') {
        if (!formData.policy_id) {
          setError('Policy selection is required for policy-specific baselines')
          return
        }
        data.policy_id = formData.policy_id
      }
      
      const result = await apiClient.createBaselineAnalysis(data)
      
      const payload = result?.result ?? (result as { result_data?: unknown })?.result_data ?? null
      const newAnalysis: BaselineAnalysis = {
        id: result.id,
        name: result.name,
        status: result.status,
        created_at: result.created_at,
        result: payload ?? null,
      }
      
      setAnalyses((prev) => [newAnalysis, ...prev])
      setSelectedAnalysis(newAnalysis)
      setDialogOpen(false)
      setFormData({ ...formData, name: '' }) // Reset name
      
      setTimeout(() => {
        loadAnalyses()
      }, 2000)
    } catch (err: any) {
      console.error('Error running baseline analysis:', err)
      
      let errorMessage = 'Failed to run baseline analysis'
      if (err.status === 0 || err.message?.includes('Network Error') || err.message?.includes('ERR_FAILED')) {
        errorMessage = 'Unable to connect to the API server. Please check if the API is running and accessible.'
      } else if (err.detail) {
        errorMessage = err.detail
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail
      } else if (err.message) {
        errorMessage = err.message
      } else if (err.response?.data) {
        const data = err.response.data
        if (typeof data === 'string') {
          errorMessage = data
        } else if (data.message) {
          errorMessage = data.message
        } else {
          errorMessage = `Server error (${err.response?.status || 'unknown'}): ${JSON.stringify(data)}`
        }
      }
      
      setError(errorMessage)
    } finally {
      setRunning(false)
    }
  }

  const formatDate = (dateStr: string) => {
    try {
      return format(new Date(dateStr), 'MMM d, yyyy')
    } catch {
      return dateStr
    }
  }

  const formatMetricValue = (value: number, unit: string) => {
    if (unit === 'percentage') {
      return `${value.toFixed(1)}%`
    } else if (unit === 'PMPM') {
      return `$${value.toFixed(2)}`
    } else if (unit === 'per_1k') {
      return value.toFixed(1)
    }
    return value.toFixed(2)
  }

  const getDisplayName = (analysis: BaselineAnalysis) => {
    return analysis.name || formatDate(analysis.created_at)
  }

  // Filter and paginate analyses
  const filteredAnalyses = analyses.filter((analysis) => {
    const matchesSearch = searchTerm === '' || 
      (analysis.name?.toLowerCase().includes(searchTerm.toLowerCase()) ?? false) ||
      analysis.status.toLowerCase().includes(searchTerm.toLowerCase())
    
    const matchesStatus = statusFilter === 'ALL' || analysis.status === statusFilter
    
    return matchesSearch && matchesStatus
  })

  const totalPages = Math.ceil(filteredAnalyses.length / itemsPerPage)
  const paginatedAnalyses = filteredAnalyses.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  )

  /** Unified list: full analyses first (by created_at desc), then stored baselines (by computed_at desc) */
  const formatDateForSort = (d: string) => (d ? new Date(d).getTime() : 0)
  const allBaselineRows: { id: string; type: 'Full analysis' | 'Stored'; scope: string; label: string; date: string; source: 'analysis' | 'stored'; analysis?: BaselineAnalysis; baseline?: any }[] = [
    ...analyses.map((a) => ({
      id: `analysis-${a.id}`,
      type: 'Full analysis' as const,
      scope: '—',
      label: a.name || format(new Date(a.created_at), 'MMM d, yyyy'),
      date: a.created_at,
      source: 'analysis' as const,
      analysis: a,
    })),
    ...baselines.map((b: any) => ({
      id: `stored-${b.baseline_id || b.id}`,
      type: 'Stored' as const,
      scope: b.policy_id ? 'Policy' : 'General',
      label: b.window_start_date && b.window_end_date
        ? `${format(new Date(b.window_start_date), 'MMM d')} – ${format(new Date(b.window_end_date), 'MMM d')}`
        : (b.baseline_id || b.id || 'Baseline').toString().slice(0, 12),
      date: b.computed_at || b.created_at || '',
      source: 'stored' as const,
      baseline: b,
    })),
  ].sort((a, b) => formatDateForSort(b.date) - formatDateForSort(a.date))

  // Reset to page 1 when search or filter changes
  useEffect(() => {
    setCurrentPage(1)
  }, [searchTerm, statusFilter])

  // Comparison helper functions
  const getComparisonData = () => {
    if (!compareAnalysis1?.result || !compareAnalysis2?.result) return null
    
    return {
      benchmarks: compareBenchmarks(compareAnalysis1.result.benchmarks || [], compareAnalysis2.result.benchmarks || []),
      providerArchetypes: compareProviderArchetypes(
        compareAnalysis1.result.provider_archetypes || [],
        compareAnalysis2.result.provider_archetypes || []
      ),
      patientSegments: comparePatientSegments(
        compareAnalysis1.result.patient_segments || [],
        compareAnalysis2.result.patient_segments || []
      ),
      timeSeries: compareTimeSeries(
        compareAnalysis1.result.time_series || [],
        compareAnalysis2.result.time_series || []
      ),
    }
  }

  const compareBenchmarks = (benchmarks1: Benchmark[], benchmarks2: Benchmark[]) => {
    const map1 = new Map(benchmarks1.map(b => [b.metric_name, b]))
    const map2 = new Map(benchmarks2.map(b => [b.metric_name, b]))
    
    const allMetrics = new Set([...map1.keys(), ...map2.keys()])
    
    return Array.from(allMetrics).map(metric => ({
      metric_name: metric,
      value1: map1.get(metric)?.metric_value || 0,
      value2: map2.get(metric)?.metric_value || 0,
      unit: map1.get(metric)?.unit || map2.get(metric)?.unit || '',
      change: map1.get(metric) && map2.get(metric) 
        ? ((map2.get(metric)!.metric_value - map1.get(metric)!.metric_value) / map1.get(metric)!.metric_value) * 100
        : 0,
    }))
  }

  const compareProviderArchetypes = (archetypes1: ProviderArchetype[], archetypes2: ProviderArchetype[]) => {
    // Simple comparison by index - in production, you'd want better matching
    const maxLen = Math.max(archetypes1.length, archetypes2.length)
    return Array.from({ length: maxLen }, (_, i) => ({
      index: i,
      archetype1: archetypes1[i] || null,
      archetype2: archetypes2[i] || null,
    }))
  }

  const comparePatientSegments = (segments1: PatientSegment[], segments2: PatientSegment[]) => {
    const map1 = new Map(segments1.map(s => [s.segment_name, s]))
    const map2 = new Map(segments2.map(s => [s.segment_name, s]))
    
    const allSegments = new Set([...map1.keys(), ...map2.keys()])
    
    return Array.from(allSegments).map(segmentName => ({
      segment_name: segmentName,
      segment1: map1.get(segmentName) || null,
      segment2: map2.get(segmentName) || null,
    }))
  }

  const compareTimeSeries = (series1: TimeSeriesPoint[], series2: TimeSeriesPoint[]) => {
    const map1 = new Map(series1.map(s => [s.date, s]))
    const map2 = new Map(series2.map(s => [s.date, s]))
    
    const allDates = new Set([...map1.keys(), ...map2.keys()])
    
    return Array.from(allDates)
      .sort()
      .map(date => ({
        date,
        observed1: map1.get(date)?.observed || 0,
        observed2: map2.get(date)?.observed || 0,
        trend1: map1.get(date)?.trend || 0,
        trend2: map2.get(date)?.trend || 0,
      }))
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
            Baseline Analysis
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Stage 3: Baseline Utilization + Baseline Behavior Profiling
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadAnalyses}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="outlined"
            startIcon={refreshingBaseline ? <CircularProgress size={16} /> : <TrendingIcon />}
            onClick={() => handleRefreshBaseline()}
            disabled={refreshingBaseline || refreshingAllStoredBaselines}
            color="primary"
          >
            {refreshingBaseline ? 'Refreshing...' : 'Refresh General Baseline'}
          </Button>
          <Button
            variant="outlined"
            startIcon={refreshingAllStoredBaselines ? <CircularProgress size={16} /> : <RefreshIcon />}
            onClick={() => handleRefreshAllStoredBaselines()}
            disabled={refreshingBaseline || refreshingAllStoredBaselines || generatingAllBaselines}
            color="secondary"
          >
            {refreshingAllStoredBaselines ? 'Refreshing all…' : 'Refresh all stored baselines'}
          </Button>
          <Button
            variant="outlined"
            startIcon={generatingAllBaselines ? <CircularProgress size={16} /> : <FilterIcon />}
            onClick={() => setGenerateAllDialogOpen(true)}
            disabled={generatingAllBaselines}
            color="primary"
          >
            {generatingAllBaselines
              ? (generatingProgress ? `${generatingProgress.current}/${generatingProgress.total}` : 'Generating...')
              : 'Generate all baselines'}
          </Button>
      </Box>
      {generatingProgress && (
        <Box sx={{ mb: 2 }}>
          <LinearProgress variant="determinate" value={(generatingProgress.current / generatingProgress.total) * 100} sx={{ mb: 0.5 }} />
          <Typography variant="caption" color="text.secondary">
            Creating full analysis {generatingProgress.current} of {generatingProgress.total}: {generatingProgress.name}
          </Typography>
        </Box>
      )}
      <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          {analyses.filter(a => a.status === 'COMPLETED' && a.result).length >= 2 && (
            <Button
              variant={compareMode ? 'contained' : 'outlined'}
              startIcon={<CompareIcon />}
              onClick={() => {
                setCompareMode(!compareMode)
                if (!compareMode) {
                  const completed = analyses.filter(a => a.status === 'COMPLETED' && a.result)
                  if (completed.length >= 2) {
                    setCompareAnalysis1(completed[0])
                    setCompareAnalysis2(completed[1])
                  }
                } else {
                  setCompareAnalysis1(null)
                  setCompareAnalysis2(null)
                }
              }}
              sx={{
                ...(compareMode && {
                  backgroundColor: healthForesightColors.primary.main,
                  '&:hover': {
                    backgroundColor: healthForesightColors.primary.dark,
                  },
                }),
              }}
            >
              {compareMode ? 'Exit Compare' : 'Compare Baselines'}
            </Button>
          )}
          <Button
            variant="contained"
            startIcon={<RunIcon />}
            onClick={() => setDialogOpen(true)}
            sx={{
              backgroundColor: healthForesightColors.primary.main,
              '&:hover': {
                backgroundColor: healthForesightColors.primary.dark,
              },
            }}
          >
            Run Baseline Analysis
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert 
          severity="error" 
          sx={{ mb: 3 }} 
          onClose={() => setError(null)}
          action={
            <Button color="inherit" size="small" onClick={loadAnalyses}>
              Retry
            </Button>
          }
        >
          <Typography variant="body2" fontWeight="medium" gutterBottom>
            Analysis Error
          </Typography>
          <Typography variant="body2">
            {error}
          </Typography>
        </Alert>
      )}

      {/* Unified: All baselines (from Run Baseline Analysis, script, Refresh, Generate all) */}
      <Paper sx={{ mb: 3, p: 2 }}>
        <Typography variant="h6" sx={{ mb: 0.5 }}>
          All baselines
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
          Full analysis = Run Baseline Analysis or Generate all baselines (time series, benchmarks, archetypes, segments, confounders). Stored = script or Refresh General Baseline (metrics + same 5 tabs on click).
        </Typography>
        {allBaselineRows.length === 0 && !loading ? (
          <Typography color="text.secondary" sx={{ py: 2 }}>No baselines yet. Use &quot;Run Baseline Analysis&quot;, &quot;Refresh General Baseline&quot;, or &quot;Generate all baselines&quot; above.</Typography>
        ) : (
          <TableContainer sx={{ maxHeight: 420 }}>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>Name / Window</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Scope</TableCell>
                  <TableCell>Date</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {allBaselineRows.map((row) => {
                  const isAnalysis = row.source === 'analysis'
                  const isSelectedAnalysis = isAnalysis && selectedAnalysis?.id === row.analysis?.id
                  const isSelectedStored = !isAnalysis && selectedStoredBaseline && (selectedStoredBaseline.baseline_id === row.baseline?.baseline_id || selectedStoredBaseline.id === row.baseline?.id)
                  const isSelected = isSelectedAnalysis || isSelectedStored
                  return (
                    <TableRow
                      key={row.id}
                      selected={!!isSelected}
                      onClick={() => {
                        if (isAnalysis && row.analysis) {
                          setSelectedStoredBaseline(null)
                          setSelectedAnalysis(row.analysis)
                          if (row.analysis.status === 'COMPLETED' && !row.analysis.result) loadAnalysisResults(row.analysis.id)
                        } else if (!isAnalysis && row.baseline) {
                          setSelectedAnalysis(null)
                          setSelectedStoredBaseline(row.baseline)
                        }
                      }}
                      sx={{ cursor: 'pointer' }}
                    >
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: isSelected ? 600 : 400 }}>
                          {row.label}
                        </Typography>
                        {isAnalysis && row.analysis?.status && (
                          <Chip label={row.analysis.status} size="small" color={row.analysis.status === 'COMPLETED' ? 'success' : row.analysis.status === 'FAILED' ? 'error' : 'default'} sx={{ mt: 0.5 }} />
                        )}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={row.type}
                          size="small"
                          color={row.type === 'Full analysis' ? 'primary' : 'default'}
                          variant={row.type === 'Full analysis' ? 'filled' : 'outlined'}
                        />
                      </TableCell>
                      <TableCell>{row.scope}</TableCell>
                      <TableCell>{row.date ? formatDate(row.date) : '—'}</TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '280px' }}>
          <CircularProgress />
        </Box>
      ) : compareMode && compareAnalysis1?.result && compareAnalysis2?.result ? (
        <ComparisonView
          analysis1={compareAnalysis1}
          analysis2={compareAnalysis2}
          comparisonData={getComparisonData()}
          formatDate={formatDate}
          formatMetricValue={formatMetricValue}
        />
      ) : selectedAnalysis ? (
        selectedAnalysis.result ? (
          <SingleAnalysisView
            analysis={selectedAnalysis}
            tabValue={tabValue}
            setTabValue={setTabValue}
            formatDate={formatDate}
            formatMetricValue={formatMetricValue}
          />
        ) : (
          <AnalysisStatusView analysis={selectedAnalysis} loadAnalysisResults={loadAnalysisResults} />
        )
      ) : selectedStoredBaseline ? (
        <StoredBaselineDetailView
          baseline={selectedStoredBaseline}
          formatDate={formatDate}
          onBack={() => setSelectedStoredBaseline(null)}
        />
      ) : allBaselineRows.length > 0 ? (
        <Card>
          <CardContent>
            <Typography color="text.secondary">Select a baseline from the table above to view details (all five tabs: Time Series, Benchmarks, Provider Archetypes, Patient Segments, Confounder Calendar).</Typography>
          </CardContent>
        </Card>
      ) : (
        <EmptyStateView onRunAnalysis={() => setDialogOpen(true)} />
      )}

      {/* Run Analysis Dialog */}
      <Dialog open={dialogOpen} onClose={() => !running && setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Run Baseline Analysis</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
            <TextField
              label="Analysis Name *"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Q1 2026 Baseline, Pre-Policy Baseline"
              fullWidth
              required
              helperText="Each analysis must have a unique name"
              error={!formData.name.trim() && formData.name !== ''}
            />
            <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 1 }}>
              Baseline period (claims in this range are used to compute the baseline)
            </Typography>
            <TextField
              label="From date *"
              type="date"
              value={formData.start_date}
              onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
              InputLabelProps={{ shrink: true }}
              fullWidth
              required
              helperText="Start of the baseline window"
            />
            <TextField
              label="To date *"
              type="date"
              value={formData.end_date}
              onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
              InputLabelProps={{ shrink: true }}
              fullWidth
              required
              helperText="End of the baseline window"
            />
            <FormControl fullWidth>
              <InputLabel>Baseline Type *</InputLabel>
              <Select
                value={formData.baseline_type}
                onChange={(e) => {
                  const newType = e.target.value as 'GENERAL' | 'POLICY_SPECIFIC'
                  setFormData({ 
                    ...formData, 
                    baseline_type: newType,
                    policy_id: newType === 'GENERAL' ? '' : formData.policy_id // Clear policy_id if switching to GENERAL
                  })
                }}
                label="Baseline Type *"
              >
                <MenuItem value="GENERAL">General Baseline (All Population)</MenuItem>
                <MenuItem value="POLICY_SPECIFIC">Policy-Specific Baseline</MenuItem>
              </Select>
            </FormControl>
            
            {formData.baseline_type === 'POLICY_SPECIFIC' && (
              <FormControl fullWidth required>
                <InputLabel>Policy *</InputLabel>
                <Select
                  value={formData.policy_id}
                  onChange={(e) => setFormData({ ...formData, policy_id: e.target.value })}
                  label="Policy *"
                  error={!formData.policy_id}
                >
                  {policies.map((policy) => (
                    <MenuItem key={policy.id} value={policy.id}>
                      {policy.name}
                    </MenuItem>
                  ))}
                </Select>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                  Select a policy to compute baseline metrics for its specific scope
                </Typography>
              </FormControl>
            )}
            
            <FormControl fullWidth>
              <InputLabel>Number of Provider Clusters</InputLabel>
              <Select
                value={formData.n_clusters}
                onChange={(e) => setFormData({ ...formData, n_clusters: e.target.value as number })}
                label="Number of Provider Clusters"
              >
                <MenuItem value={3}>3</MenuItem>
                <MenuItem value={4}>4</MenuItem>
                <MenuItem value={5}>5</MenuItem>
                <MenuItem value={6}>6</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)} disabled={running}>
            Cancel
          </Button>
          <Button
            onClick={handleRunAnalysis}
            variant="contained"
            disabled={running || !formData.name.trim() || !formData.start_date || !formData.end_date || formData.start_date > formData.end_date}
            startIcon={running ? <CircularProgress size={20} /> : <RunIcon />}
          >
            {running ? 'Running...' : 'Run Analysis'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Generate all baselines: date range only */}
      <Dialog open={generateAllDialogOpen} onClose={() => !generatingAllBaselines && setGenerateAllDialogOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Generate all baselines</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Select the baseline period. One full analysis (General + per policy) will be created for this date range.
          </Typography>
          <TextField
            label="Start date"
            type="date"
            value={generateAllDateRange.start_date}
            onChange={(e) => setGenerateAllDateRange((prev) => ({ ...prev, start_date: e.target.value }))}
            InputLabelProps={{ shrink: true }}
            fullWidth
            sx={{ mb: 2 }}
          />
          <TextField
            label="End date"
            type="date"
            value={generateAllDateRange.end_date}
            onChange={(e) => setGenerateAllDateRange((prev) => ({ ...prev, end_date: e.target.value }))}
            InputLabelProps={{ shrink: true }}
            fullWidth
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setGenerateAllDialogOpen(false)} disabled={generatingAllBaselines}>
            Cancel
          </Button>
          <Button
            variant="contained"
            disabled={!generateAllDateRange.start_date || !generateAllDateRange.end_date || generateAllDateRange.start_date > generateAllDateRange.end_date}
            onClick={() => handleGenerateAllBaselines(generateAllDateRange.start_date, generateAllDateRange.end_date)}
          >
            Generate
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

// Component for single analysis view
function SingleAnalysisView({
  analysis,
  tabValue,
  setTabValue,
  formatDate,
  formatMetricValue,
}: {
  analysis: BaselineAnalysis
  tabValue: number
  setTabValue: (v: number) => void
  formatDate: (d: string) => string
  formatMetricValue: (v: number, u: string) => string
}) {
  return (
    <Box>
      <Paper sx={{ mb: 3, p: 2 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>
          Analysis Summary: {analysis.name || 'Unnamed Analysis'}
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <Typography variant="caption" color="text.secondary">
              Analysis ID
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {analysis.result?.analysis_id?.slice(0, 8) || analysis.id.slice(0, 8)}...
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Typography variant="caption" color="text.secondary">
              Status
            </Typography>
            <Chip
              label={analysis.status}
              color={analysis.status === 'COMPLETED' ? 'success' : 'default'}
              size="small"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Typography variant="caption" color="text.secondary">
              Data Coverage
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {analysis.result?.data_coverage?.claims_records?.toLocaleString() || 'N/A'} records
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Typography variant="caption" color="text.secondary">
              Date Range
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {analysis.result?.data_coverage?.date_range?.start && analysis.result?.data_coverage?.date_range?.end
                ? `${formatDate(analysis.result.data_coverage.date_range.start)} - ${formatDate(analysis.result.data_coverage.date_range.end)}`
                : 'N/A'}
            </Typography>
          </Grid>
        </Grid>
      </Paper>

      <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)} sx={{ mb: 3 }}>
        <Tab icon={<TrendingIcon />} iconPosition="start" label="Time Series" />
        <Tab icon={<BenchmarkIcon />} iconPosition="start" label="Benchmarks" />
        <Tab icon={<ProviderIcon />} iconPosition="start" label="Provider Archetypes" />
        <Tab icon={<PatientIcon />} iconPosition="start" label="Patient Segments" />
        <Tab icon={<CalendarIcon />} iconPosition="start" label="Confounder Calendar" />
      </Tabs>

      {/* Time Series Tab */}
      {tabValue === 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 3 }}>
              Baseline Time-Series Analysis
            </Typography>
            {analysis.result?.time_series && analysis.result.time_series.length > 0 ? (
              <ResponsiveContainer width="100%" height={400}>
                <AreaChart
                  data={analysis.result.time_series}
                  margin={{ top: 24, right: 24, left: 72, bottom: 80 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="date"
                    tickFormatter={formatDate}
                    angle={-45}
                    textAnchor="end"
                    height={80}
                    interval={Math.max(0, Math.floor((analysis.result.time_series.length - 1) / 12))}
                    tick={{ fontSize: 11 }}
                  />
                  <YAxis
                    width={64}
                    tick={{ fontSize: 11 }}
                    tickFormatter={(v: number) => (v >= 1e6 ? `${v / 1e6}M` : v >= 1e3 ? `${v / 1e3}k` : String(v))}
                  />
                  <Tooltip labelFormatter={formatDate} formatter={(value: number) => `$${value.toFixed(2)}`} />
                  <Legend />
                  <Area type="monotone" dataKey="lower_bound" stackId="1" stroke="#8884d8" fill="#8884d8" fillOpacity={0.1} />
                  <Area type="monotone" dataKey="upper_bound" stackId="1" stroke="#8884d8" fill="#8884d8" fillOpacity={0.1} />
                  <Line type="monotone" dataKey="trend" stroke="#82ca9d" strokeWidth={2} />
                  <Line type="monotone" dataKey="observed" stroke="#ff7300" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <Typography color="text.secondary">No time series data available</Typography>
            )}
          </CardContent>
        </Card>
      )}

      {/* Benchmarks Tab - Enhanced with charts */}
      {tabValue === 1 && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 3 }}>
              Baseline Benchmarks
            </Typography>
            {/* Display baseline summary narrative if available */}
            {analysis.result?.baseline_summary_narrative && (
              <Box sx={{ mb: 3, p: 2, bgcolor: 'primary.light', borderRadius: 1, border: '1px solid', borderColor: 'primary.main' }}>
                <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1, color: 'primary.dark' }}>
                  Baseline Analysis Summary
                </Typography>
                {analysis.result.baseline_summary_narrative.summary && (
                  <Typography variant="body1" sx={{ mb: 2, color: 'text.primary', lineHeight: 1.7 }}>
                    {analysis.result.baseline_summary_narrative.summary}
                  </Typography>
                )}
                {analysis.result.baseline_summary_narrative.key_findings && analysis.result.baseline_summary_narrative.key_findings.length > 0 && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                      Key Findings:
                    </Typography>
                    {analysis.result.baseline_summary_narrative.key_findings.map((finding, i) => (
                      <Typography key={i} variant="body2" sx={{ mb: 0.5, pl: 1, lineHeight: 1.6 }}>
                        • {finding}
                      </Typography>
                    ))}
                  </Box>
                )}
                {analysis.result.baseline_summary_narrative.recommendations && analysis.result.baseline_summary_narrative.recommendations.length > 0 && (
                  <Box>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                      Recommendations:
                    </Typography>
                    {analysis.result.baseline_summary_narrative.recommendations.map((rec, i) => (
                      <Typography key={i} variant="body2" sx={{ mb: 0.5, pl: 1, lineHeight: 1.6 }}>
                        • {rec}
                      </Typography>
                    ))}
                  </Box>
                )}
              </Box>
            )}
            {analysis.result?.benchmarks && analysis.result.benchmarks.length > 0 ? (
              <Box>
                <Grid container spacing={3} sx={{ mb: 3 }}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle1" sx={{ mb: 2 }}>
                      Benchmark Values by Metric
                    </Typography>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={analysis.result.benchmarks.slice(0, 10)}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="metric_name" angle={-45} textAnchor="end" height={100} />
                        <YAxis />
                        <Tooltip formatter={(value: number, name: string, props: any) => [
                          formatMetricValue(value, props.payload.unit),
                          'Value'
                        ]} />
                        <Bar dataKey="metric_value" fill={healthForesightColors.primary.main} />
                      </BarChart>
                    </ResponsiveContainer>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle1" sx={{ mb: 2 }}>
                      Sample Sizes
                    </Typography>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={analysis.result.benchmarks.slice(0, 10)}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="metric_name" angle={-45} textAnchor="end" height={100} />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="sample_size" fill="#82ca9d" />
                      </BarChart>
                    </ResponsiveContainer>
                  </Grid>
                </Grid>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Metric</TableCell>
                        <TableCell>Value</TableCell>
                        <TableCell>Unit</TableCell>
                        <TableCell>Segment</TableCell>
                        <TableCell>Sample Size</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {analysis.result.benchmarks.map((benchmark, idx) => (
                        <TableRow key={idx}>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                                {benchmark.metric_name.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                              </Typography>
                              <MetricTooltip metricName={benchmark.metric_name} />
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" sx={{ fontWeight: 600 }}>
                              {formatMetricValue(benchmark.metric_value, benchmark.unit)}
                            </Typography>
                          </TableCell>
                          <TableCell>{benchmark.unit}</TableCell>
                          <TableCell>{benchmark.segment_value || 'Overall'}</TableCell>
                          <TableCell>{benchmark.sample_size.toLocaleString()}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            ) : (
              <Typography color="text.secondary">No benchmarks available</Typography>
            )}
          </CardContent>
        </Card>
      )}

      {/* Provider Archetypes Tab - Normalized radar charts for comparable profiles */}
      {tabValue === 2 && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 3 }}>
              Provider Archetypes
            </Typography>
            {analysis.result?.provider_archetypes && analysis.result.provider_archetypes.length > 0 ? (
              (() => {
                const preferredKeys = ['total_claims', 'total_cost', 'avg_cost_per_claim', 'claims_per_member']
                const archetypesList = analysis.result.provider_archetypes

                // Collect all numeric values per key across archetypes to compute min/max for normalization
                const keyMinMax: Record<string, { min: number; max: number }> = {}
                for (const arch of archetypesList) {
                  const chars = arch.characteristics || {}
                  for (const key of preferredKeys) {
                    const v = chars[key]
                    if (typeof v === 'number' && isFinite(v)) {
                      if (!keyMinMax[key]) keyMinMax[key] = { min: v, max: v }
                      else {
                        keyMinMax[key].min = Math.min(keyMinMax[key].min, v)
                        keyMinMax[key].max = Math.max(keyMinMax[key].max, v)
                      }
                    }
                  }
                }
                // If no preferred keys had data, use any numeric keys from first archetype
                const firstChars = archetypesList[0]?.characteristics || {}
                const fallbackKeys = Object.entries(firstChars)
                  .filter(([_, v]) => typeof v === 'number' && isFinite(v as number))
                  .map(([k]) => k)
                  .slice(0, 6)
                if (Object.keys(keyMinMax).length === 0 && fallbackKeys.length > 0) {
                  for (const arch of archetypesList) {
                    for (const key of fallbackKeys) {
                      const v = (arch.characteristics || {})[key]
                      if (typeof v === 'number' && isFinite(v)) {
                        if (!keyMinMax[key]) keyMinMax[key] = { min: v, max: v }
                        else {
                          keyMinMax[key].min = Math.min(keyMinMax[key].min, v)
                          keyMinMax[key].max = Math.max(keyMinMax[key].max, v)
                        }
                      }
                    }
                  }
                }
                const chartKeys = Object.keys(keyMinMax).length > 0 ? preferredKeys.filter(k => keyMinMax[k]) : fallbackKeys

                const charLabel: Record<string, string> = {
                  total_claims: 'Claims per provider',
                  total_cost: 'Cost per provider',
                  avg_cost_per_claim: 'Avg cost per claim',
                  claims_per_member: 'Claims per member',
                }

                return (
                  <Grid container spacing={3}>
                    {archetypesList.map((archetype, idx) => {
                      const chars = archetype.characteristics || {}
                      const radarData = chartKeys
                        .filter(key => typeof chars[key] === 'number' && isFinite(chars[key] as number))
                        .map(key => {
                          const raw = chars[key] as number
                          const { min, max } = keyMinMax[key] || { min: raw, max: raw }
                          const range = max - min || 1
                          const normalized = Math.min(100, Math.max(0, ((raw - min) / range) * 100))
                          return {
                            fullKey: key,
                            characteristic: charLabel[key] || key.replace(/_/g, ' '),
                            value: Math.round(normalized * 10) / 10,
                            rawValue: raw,
                          }
                        })

                      return (
                        <Grid item xs={12} md={6} key={archetype.archetype_id}>
                          <Paper sx={{ p: 3, height: '100%' }}>
                            <Typography variant="h6" sx={{ mb: 1 }}>
                              {archetype.archetype_name}
                            </Typography>
                            <Chip 
                              label={`${archetype.provider_count} providers`} 
                              color="primary" 
                              size="small" 
                              sx={{ mb: 2 }}
                            />
                            {radarData.length > 0 ? (
                              <Box sx={{ mb: 2 }}>
                                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                                  Relative profile (0 = lowest, 100 = highest across archetypes). Hover for actual values.
                                </Typography>
                                <ResponsiveContainer width="100%" height={250}>
                                  <RadarChart data={radarData}>
                                    <PolarGrid />
                                    <PolarAngleAxis dataKey="characteristic" tick={{ fontSize: 11 }} />
                                    <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 10 }} />
                                    <Radar
                                      name="Relative"
                                      dataKey="value"
                                      stroke={COLORS[idx % COLORS.length]}
                                      fill={COLORS[idx % COLORS.length]}
                                      fillOpacity={0.6}
                                    />
                                    <Tooltip
                                      formatter={(value: number, _name: string, props: { payload?: { rawValue?: number; fullKey?: string } }) => {
                                        const raw = props?.payload?.rawValue
                                        const key = props?.payload?.fullKey || ''
                                        if (raw !== undefined && raw !== null) {
                                          if (key.includes('cost') || key === 'total_cost') return [`$${Number(raw).toLocaleString(undefined, { maximumFractionDigits: 0 })}`, 'Actual']
                                          return [Number(raw).toLocaleString(undefined, { maximumFractionDigits: 2 }), 'Actual']
                                        }
                                        return [value, 'Score (0-100)']
                                      }}
                                      labelFormatter={(label: string) => label}
                                    />
                                  </RadarChart>
                                </ResponsiveContainer>
                              </Box>
                            ) : (
                          <Alert severity="info" sx={{ mb: 2 }}>
                            No characteristics data available for radar chart
                          </Alert>
                        )}
                        {/* Display narrative for this archetype */}
                        {analysis.result?.archetype_narratives && (() => {
                          const narrative = analysis.result.archetype_narratives.find(n => n.archetype_id === archetype.archetype_id)
                          if (narrative) {
                            return (
                              <Box sx={{ mb: 2, p: 2, bgcolor: 'background.paper', borderRadius: 1, border: '1px solid', borderColor: 'divider' }}>
                                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1, color: 'primary.main' }}>
                                  Analysis Summary
                                </Typography>
                                {narrative.interpretation && (
                                  <Typography variant="body2" sx={{ mb: 1.5, color: 'text.secondary', lineHeight: 1.6 }}>
                                    {narrative.interpretation}
                                  </Typography>
                                )}
                                {narrative.key_insights && narrative.key_insights.length > 0 && (
                                  <Box sx={{ mb: 1.5 }}>
                                    <Typography variant="caption" sx={{ fontWeight: 600, mb: 0.5, display: 'block' }}>
                                      Key Insights:
                                    </Typography>
                                    {narrative.key_insights.map((insight, i) => (
                                      <Typography key={i} variant="body2" sx={{ mb: 0.5, pl: 1, color: 'text.secondary', fontSize: '0.875rem' }}>
                                        • {insight}
                                      </Typography>
                                    ))}
                                  </Box>
                                )}
                                {narrative.recommendations && narrative.recommendations.length > 0 && (
                                  <Box>
                                    <Typography variant="caption" sx={{ fontWeight: 600, mb: 0.5, display: 'block' }}>
                                      Recommendations:
                                    </Typography>
                                    {narrative.recommendations.map((rec, i) => (
                                      <Typography key={i} variant="body2" sx={{ mb: 0.5, pl: 1, color: 'text.secondary', fontSize: '0.875rem' }}>
                                        • {rec}
                                      </Typography>
                                    ))}
                                  </Box>
                                )}
                              </Box>
                            )
                          }
                          return null
                        })()}
                        <Divider sx={{ my: 2 }} />
                        <Box>
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                            Key Metrics:
                          </Typography>
                          {Object.entries(archetype.characteristics)
                            .filter(([_, v]) => typeof v === 'number')
                            .slice(0, 5)
                            .map(([key, value]) => (
                            <Box key={key} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                <Typography variant="body2">
                                  {key === 'total_claims' ? 'avg claims per provider' : 
                                   key === 'total_cost' ? 'avg cost per provider' :
                                   key.replace(/_/g, ' ')}:
                                </Typography>
                                <MetricTooltip metricName={key} />
                              </Box>
                              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                                {typeof value === 'number' ? value.toFixed(2) : String(value)}
                              </Typography>
                            </Box>
                          ))}
                        </Box>
                      </Paper>
                    </Grid>
                  );
                })}
              </Grid>
            );
            })() ) : (
              <Typography color="text.secondary">No provider archetypes available</Typography>
            )}
          </CardContent>
        </Card>
      )}

      {/* Patient Segments Tab - Enhanced with visual cards */}
      {tabValue === 3 && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 3 }}>
              Patient Sensitivity Segments
            </Typography>
            {analysis.result?.patient_segments && analysis.result.patient_segments.length > 0 ? (
              <Grid container spacing={3}>
                {analysis.result.patient_segments.map((segment, idx) => {
                  const profileEntries = Object.entries(segment.utilization_profile || {})
                    .filter(([, v]) => typeof v === 'number' && isFinite(v as number))
                    .slice(0, 8)
                  const maxVal = Math.max(...profileEntries.map(([, v]) => v as number), 1)
                  const utilizationLabel: Record<string, string> = {
                    avg_cost_per_claim: 'Avg cost per claim',
                    avg_cost_per_member: 'Avg cost per member',
                    avg_claims_per_member: 'Avg claims per member',
                    utilization_per_1k: 'Utilization per 1k',
                    cost_pmpm: 'Cost PMPM',
                  }
                  const utilizationData = profileEntries.map(([key, value]) => ({
                    key,
                    name: utilizationLabel[key] || key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
                    value: (value as number) / maxVal * 100,
                    rawValue: value as number,
                  }))

                  const totalMembers = analysis.result?.patient_segments?.reduce((sum, s) => sum + s.member_count, 0) || segment.member_count
                  const percentage = (segment.member_count / totalMembers) * 100

                  const formatMetricValue = (v: number, k: string) => {
                    if (k.includes('cost') || k.includes('pmpm')) return `$${v.toLocaleString(undefined, { maximumFractionDigits: 2, minimumFractionDigits: 0 })}`
                    return v.toLocaleString(undefined, { maximumFractionDigits: 2 })
                  }
                  
                  return (
                    <Grid item xs={12} md={6} key={segment.segment_id}>
                      <Paper 
                        sx={{ 
                          p: 3, 
                          height: '100%',
                          border: `2px solid ${COLORS[idx % COLORS.length]}`,
                          borderRadius: 2,
                        }}
                      >
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                          <Typography variant="h6">
                            {segment.segment_name}
                          </Typography>
                          <Chip 
                            label={`${segment.member_count.toLocaleString()} members`} 
                            color="primary" 
                            size="small"
                          />
                        </Box>
                        <Box sx={{ mb: 2 }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                            <Typography variant="caption" color="text.secondary">
                              Population Share
                            </Typography>
                            <Typography variant="caption" sx={{ fontWeight: 600 }}>
                              {percentage.toFixed(1)}%
                            </Typography>
                          </Box>
                          <LinearProgress 
                            variant="determinate" 
                            value={percentage} 
                            sx={{ 
                              height: 8, 
                              borderRadius: 4,
                              backgroundColor: 'rgba(0,0,0,0.1)',
                              '& .MuiLinearProgress-bar': {
                                backgroundColor: COLORS[idx % COLORS.length],
                              },
                            }}
                          />
                        </Box>
                        {utilizationData.length > 0 && (
                          <Box sx={{ mb: 2 }}>
                            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                              Utilization Profile (relative within segment; hover for actual values):
                            </Typography>
                            <ResponsiveContainer width="100%" height={Math.max(180, utilizationData.length * 44)}>
                              <BarChart data={utilizationData} layout="vertical" margin={{ left: 8, right: 16 }}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis type="number" domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
                                <YAxis dataKey="name" type="category" width={160} tick={{ fontSize: 12 }} />
                                <Tooltip
                                  formatter={(value: number, _name: string, props: { payload?: { rawValue?: number; key?: string } }) => {
                                    const raw = props?.payload?.rawValue
                                    const k = props?.payload?.key || ''
                                    if (raw !== undefined && raw !== null) return [formatMetricValue(raw, k), 'Value']
                                    return [value, 'Relative %']
                                  }}
                                  labelFormatter={(label: string) => label}
                                />
                                <Bar dataKey="value" fill={COLORS[idx % COLORS.length]} name="Relative" />
                              </BarChart>
                            </ResponsiveContainer>
                          </Box>
                        )}
                        <Divider sx={{ my: 2 }} />
                        <Box>
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                            Detailed Metrics:
                          </Typography>
                          {Object.entries(segment.utilization_profile || {}).map(([key, value]) => (
                            <Box key={key} sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                              <Typography variant="body2">
                                {utilizationLabel[key] || key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}:
                              </Typography>
                              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                                {typeof value === 'number' ? formatMetricValue(value, key) : String(value)}
                              </Typography>
                            </Box>
                          ))}
                        </Box>
                      </Paper>
                    </Grid>
                  )
                })}
              </Grid>
            ) : (
              <Typography color="text.secondary">No patient segments available</Typography>
            )}
          </CardContent>
        </Card>
      )}

      {/* Confounder Calendar Tab */}
      {tabValue === 4 && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 3 }}>
              Confounder Calendar
            </Typography>
            {analysis.result?.confounder_events && analysis.result.confounder_events.length > 0 ? (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Date</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Description</TableCell>
                      <TableCell>Impact</TableCell>
                      <TableCell>Affected Segments</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {analysis.result.confounder_events.slice(0, 50).map((event, idx) => (
                      <TableRow key={idx}>
                        <TableCell>{formatDate(event.event_date)}</TableCell>
                        <TableCell>
                          <Chip label={event.event_type} size="small" />
                        </TableCell>
                        <TableCell>{event.event_description}</TableCell>
                        <TableCell>
                          {event.impact_magnitude !== null && event.impact_magnitude !== undefined
                            ? `${(event.impact_magnitude * 100).toFixed(0)}%`
                            : 'N/A'}
                        </TableCell>
                        <TableCell>{event.affected_segments.join(', ') || 'ALL'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            ) : (
              <Typography color="text.secondary">No confounder events available</Typography>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  )
}

// Component for comparison view
function ComparisonView({
  analysis1,
  analysis2,
  comparisonData,
  formatDate,
  formatMetricValue,
}: {
  analysis1: BaselineAnalysis
  analysis2: BaselineAnalysis
  comparisonData: ReturnType<typeof getComparisonData>
  formatDate: (d: string) => string
  formatMetricValue: (v: number, u: string) => string
}) {
  return (
    <Box>
      <Paper sx={{ mb: 3, p: 2, backgroundColor: 'primary.light', color: 'primary.contrastText' }}>
        <Typography variant="h6" sx={{ mb: 1 }}>
          Comparing Baselines
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2">Baseline 1: {analysis1.name || formatDate(analysis1.created_at)}</Typography>
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2">Baseline 2: {analysis2.name || formatDate(analysis2.created_at)}</Typography>
          </Grid>
        </Grid>
      </Paper>

      <Tabs value={0} sx={{ mb: 3 }}>
        <Tab label="Benchmarks Comparison" />
        <Tab label="Provider Archetypes Comparison" />
        <Tab label="Patient Segments Comparison" />
        <Tab label="Time Series Comparison" />
      </Tabs>

      {/* Benchmarks Comparison */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 3 }}>
            Benchmarks Comparison
          </Typography>
          {comparisonData.benchmarks && comparisonData.benchmarks.length > 0 ? (
            <Box>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={comparisonData.benchmarks.slice(0, 15)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="metric_name" angle={-45} textAnchor="end" height={100} />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="value1" fill="#8884d8" name={`${analysis1.name || 'Baseline 1'}`} />
                  <Bar dataKey="value2" fill="#82ca9d" name={`${analysis2.name || 'Baseline 2'}`} />
                </BarChart>
              </ResponsiveContainer>
              <TableContainer sx={{ mt: 3 }}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Metric</TableCell>
                      <TableCell>{analysis1.name || 'Baseline 1'}</TableCell>
                      <TableCell>{analysis2.name || 'Baseline 2'}</TableCell>
                      <TableCell>Change</TableCell>
                      <TableCell>Unit</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {comparisonData.benchmarks.map((benchmark, idx) => (
                      <TableRow key={idx}>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontWeight: 500 }}>
                            {benchmark.metric_name.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                          </Typography>
                        </TableCell>
                        <TableCell>{formatMetricValue(benchmark.value1, benchmark.unit)}</TableCell>
                        <TableCell>{formatMetricValue(benchmark.value2, benchmark.unit)}</TableCell>
                        <TableCell>
                          <Chip
                            label={`${benchmark.change > 0 ? '+' : ''}${benchmark.change.toFixed(1)}%`}
                            color={benchmark.change > 0 ? 'error' : 'success'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{benchmark.unit}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          ) : (
            <Typography color="text.secondary">No benchmark data available for comparison</Typography>
          )}
        </CardContent>
      </Card>

      {/* Time Series Comparison */}
      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 3 }}>
            Time Series Comparison
          </Typography>
          {comparisonData.timeSeries && comparisonData.timeSeries.length > 0 ? (
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={comparisonData.timeSeries}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tickFormatter={formatDate} />
                <YAxis />
                <Tooltip labelFormatter={formatDate} />
                <Legend />
                <Line type="monotone" dataKey="observed1" stroke="#8884d8" strokeWidth={2} name={`${analysis1.name || 'Baseline 1'} - Observed`} />
                <Line type="monotone" dataKey="observed2" stroke="#82ca9d" strokeWidth={2} name={`${analysis2.name || 'Baseline 2'} - Observed`} />
                <Line type="monotone" dataKey="trend1" stroke="#8884d8" strokeWidth={1} strokeDasharray="5 5" name={`${analysis1.name || 'Baseline 1'} - Trend`} />
                <Line type="monotone" dataKey="trend2" stroke="#82ca9d" strokeWidth={1} strokeDasharray="5 5" name={`${analysis2.name || 'Baseline 2'} - Trend`} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <Typography color="text.secondary">No time series data available for comparison</Typography>
          )}
        </CardContent>
      </Card>
    </Box>
  )
}

// Helper components
function AnalysisStatusView({ analysis, loadAnalysisResults }: { analysis: BaselineAnalysis; loadAnalysisResults: (id: string) => void }) {
  return (
    <Card>
      <CardContent>
        {analysis.status === 'PENDING' ? (
          <>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <CircularProgress size={24} />
              <Typography variant="h6">Analysis Pending</Typography>
            </Box>
            <Alert severity="warning" sx={{ mb: 2 }}>
              <Typography variant="body2" fontWeight="medium" gutterBottom>
                This analysis appears to be stuck in PENDING status.
              </Typography>
              <Typography variant="body2">
                This usually means the analysis failed or timed out.
              </Typography>
            </Alert>
          </>
        ) : analysis.status === 'FAILED' ? (
          <>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <CancelIcon color="error" />
              <Typography variant="h6" color="error">Analysis Failed</Typography>
            </Box>
            <Alert severity="error" sx={{ mb: 2 }}>
              <Typography variant="body2">
                This analysis failed to complete. Please check the error details or create a new analysis.
              </Typography>
            </Alert>
          </>
        ) : analysis.status === 'COMPLETED' ? (
          <>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <Typography variant="h6" color="text.secondary">
                No result data for this analysis
              </Typography>
            </Box>
            <Alert severity="info" sx={{ mb: 2 }}>
              <Typography variant="body2">
                This analysis is marked complete but no baseline result payload was returned. The result may not have been stored (e.g. older analyses or a failed write). Use &quot;Retry loading&quot; to fetch again, or run a new baseline analysis.
              </Typography>
            </Alert>
            <Button variant="outlined" startIcon={<RefreshIcon />} onClick={() => loadAnalysisResults(analysis.id)}>
              Retry loading results
            </Button>
          </>
        ) : (
          <>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <CircularProgress size={24} />
              <Typography variant="h6">
                Analysis {analysis.status.toLowerCase()}...
              </Typography>
            </Box>
          </>
        )}
      </CardContent>
    </Card>
  )
}

function EmptyStateView({ onRunAnalysis }: { onRunAnalysis: () => void }) {
  return (
    <Card>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 2 }}>
          No Baseline Analysis Found
        </Typography>
        <Typography color="text.secondary" sx={{ mb: 3 }}>
          Run a baseline analysis to establish baseline utilization and behavior profiles.
        </Typography>
        <Button variant="contained" startIcon={<RunIcon />} onClick={onRunAnalysis}>
          Run Baseline Analysis
        </Button>
      </CardContent>
    </Card>
  )
}

/** Keys stored in baseline_metrics as structured JSON — omit from flat metric tables. */
const STORED_BASELINE_NESTED_KEYS = new Set(['provider_archetypes', 'patient_segments', 'top_service_category_share'])

function scalarStoredBaselineMetricEntries(metrics: Record<string, unknown> | null | undefined): [string, unknown][] {
  return Object.entries(metrics || {}).filter(([key, value]) => {
    if (STORED_BASELINE_NESTED_KEYS.has(key)) return false
    const t = typeof value
    return t === 'number' || t === 'string' || t === 'boolean' || value === null
  })
}

type StoredBaselineArchetype = {
  archetype_id?: number
  archetype_name?: string
  provider_count?: number
  characteristics?: Record<string, unknown>
  representative_providers?: string[]
}

type StoredBaselinePatientSegment = {
  segment_id?: number
  segment_name?: string
  member_count?: number
  characteristics?: Record<string, unknown>
  utilization_profile?: Record<string, unknown>
}

function StoredProviderArchetypesSection({ metrics }: { metrics: Record<string, unknown> }) {
  const arches = (metrics?.provider_archetypes as StoredBaselineArchetype[] | undefined) || []
  if (!arches.length) {
    return (
      <>
        <Typography variant="h6" sx={{ mb: 2 }}>Provider archetypes</Typography>
        <Typography color="text.secondary" sx={{ mb: 2 }}>
          No provider clusters are stored on this baseline yet. They are computed when you refresh baselines from canonical claims (historical demo script) or run a full baseline analysis.
        </Typography>
        <Alert severity="info">Run <strong>Run Baseline Analysis</strong> or re-run baseline refresh from claims to populate archetypes.</Alert>
      </>
    )
  }
  return (
    <>
      <Typography variant="h6" sx={{ mb: 2 }}>Provider archetypes</Typography>
      <Typography color="text.secondary" sx={{ mb: 2 }}>
        Clusters derived from claim volume by dominant service category (stored baseline snapshot).
      </Typography>
      <Grid container spacing={2}>
        {arches.map((a, idx) => (
          <Grid item xs={12} md={6} key={a.archetype_id ?? `arch-${idx}`}>
            <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>{a.archetype_name}</Typography>
              <Chip label={`${a.provider_count ?? 0} providers`} size="small" color="primary" sx={{ mb: 1.5 }} />
              {a.characteristics && Object.keys(a.characteristics).length > 0 && (
                <Box sx={{ mb: 1.5 }}>
                  {Object.entries(a.characteristics).map(([k, v]) => (
                    <Typography key={k} variant="body2" color="text.secondary" sx={{ mb: 0.25 }}>
                      <strong>{k.replace(/_/g, ' ')}:</strong>{' '}
                      {typeof v === 'number' ? (Number.isInteger(v) ? v : v.toFixed(2)) : String(v)}
                    </Typography>
                  ))}
                </Box>
              )}
              {a.representative_providers && a.representative_providers.length > 0 && (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {a.representative_providers.slice(0, 6).map((id) => (
                    <Chip key={id} label={id.length > 20 ? `${id.slice(0, 18)}…` : id} size="small" variant="outlined" />
                  ))}
                </Box>
              )}
            </Paper>
          </Grid>
        ))}
      </Grid>
    </>
  )
}

function StoredPatientSegmentsSection({ metrics }: { metrics: Record<string, unknown> }) {
  const segs = (metrics?.patient_segments as StoredBaselinePatientSegment[] | undefined) || []
  if (!segs.length) {
    return (
      <>
        <Typography variant="h6" sx={{ mb: 2 }}>Patient segments</Typography>
        <Typography color="text.secondary" sx={{ mb: 2 }}>
          No patient segments are stored on this baseline yet. Refresh from canonical claims or run a full baseline analysis to populate LOB × utilization bands.
        </Typography>
        <Alert severity="info">Run <strong>Run Baseline Analysis</strong> or re-run baseline refresh from claims to populate segments.</Alert>
      </>
    )
  }
  return (
    <>
      <Typography variant="h6" sx={{ mb: 2 }}>Patient segments</Typography>
      <Typography color="text.secondary" sx={{ mb: 2 }}>
        Members grouped by line of business and utilization band (stored baseline snapshot).
      </Typography>
      <Grid container spacing={2}>
        {segs.map((s, idx) => (
          <Grid item xs={12} md={6} key={s.segment_id ?? `seg-${idx}`}>
            <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>{s.segment_name}</Typography>
              <Chip label={`${s.member_count ?? 0} members`} size="small" color="secondary" sx={{ mb: 1.5 }} />
              {s.characteristics && Object.keys(s.characteristics).length > 0 && (
                <Box sx={{ mb: 1 }}>
                  {Object.entries(s.characteristics).map(([k, v]) => (
                    <Typography key={k} variant="body2" color="text.secondary" sx={{ mb: 0.25 }}>
                      <strong>{k.replace(/_/g, ' ')}:</strong> {String(v)}
                    </Typography>
                  ))}
                </Box>
              )}
              {s.utilization_profile && Object.keys(s.utilization_profile).length > 0 && (
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>Utilization profile</Typography>
              )}
              {s.utilization_profile && Object.entries(s.utilization_profile).map(([k, v]) => (
                <Typography key={k} variant="body2" sx={{ mb: 0.25 }}>
                  {k.replace(/_/g, ' ')}: {typeof v === 'number' ? v.toFixed(2) : String(v)}
                </Typography>
              ))}
            </Paper>
          </Grid>
        ))}
      </Grid>
    </>
  )
}

/** Single stored baseline: full 5-tab detail (same tabs as full analysis). Used when user selects a stored baseline from the unified list. */
function StoredBaselineDetailView({
  baseline,
  formatDate,
  onBack,
}: {
  baseline: any
  formatDate: (d: string) => string
  onBack: () => void
}) {
  const [detailTab, setDetailTab] = useState(0)
  const formatMetricValue = (value: number, unit: string) => {
    if (unit === 'PMPM' || unit === 'currency') return `$${Number(value).toFixed(2)}`
    if (unit === 'per_1k') return Number(value).toFixed(2)
    if (unit === 'count') return Number(value).toLocaleString()
    return typeof value === 'number' ? value.toFixed(2) : String(value)
  }
  return (
    <Box>
      <Button startIcon={<BackIcon />} onClick={onBack} sx={{ mb: 2 }} size="small">
        Back to list
      </Button>
      <Paper sx={{ mb: 3, p: 2 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>
          Baseline – {baseline.policy_id ? 'Policy' : 'General'} – {(baseline.baseline_id || baseline.id || '').toString().slice(0, 8)}...
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <Typography variant="caption" color="text.secondary">Baseline ID</Typography>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>{(baseline.baseline_id || baseline.id || '—').toString().slice(0, 12)}...</Typography>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Typography variant="caption" color="text.secondary">Status</Typography>
            <Chip label="Stored" color="success" size="small" />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Typography variant="caption" color="text.secondary">Data coverage</Typography>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {(() => {
                const m = baseline.baseline_metrics || baseline.metrics || {}
                const n = m.total_claims ?? m.unique_members ?? m.member_months
                return n != null ? `${Number(n).toLocaleString()} ${m.total_claims != null ? 'claims' : m.unique_members != null ? 'members' : 'member-months'}` : '—'
              })()}
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Typography variant="caption" color="text.secondary">Date range</Typography>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {baseline.window_start_date && baseline.window_end_date
                ? `${formatDate(baseline.window_start_date)} – ${formatDate(baseline.window_end_date)}`
                : '—'}
            </Typography>
          </Grid>
        </Grid>
      </Paper>

      <Tabs value={detailTab} onChange={(_, v) => setDetailTab(v)} sx={{ mb: 3 }}>
        <Tab icon={<TrendingIcon />} iconPosition="start" label="Time Series" />
        <Tab icon={<BenchmarkIcon />} iconPosition="start" label="Benchmarks" />
        <Tab icon={<ProviderIcon />} iconPosition="start" label="Provider Archetypes" />
        <Tab icon={<PatientIcon />} iconPosition="start" label="Patient Segments" />
        <Tab icon={<CalendarIcon />} iconPosition="start" label="Confounder Calendar" />
      </Tabs>

      {detailTab === 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 3 }}>Baseline time-series analysis</Typography>
            <Typography color="text.secondary" sx={{ mb: 2 }}>
              This stored baseline is a single-period snapshot. Time series (trend, bounds, observed) are produced by a full baseline analysis run.
            </Typography>
            <Alert severity="info" sx={{ mb: 2 }}>
              Run <strong>Run Baseline Analysis</strong> above to get time-series charts, provider archetypes, patient segments, and confounder calendar.
            </Alert>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>Single-period metrics</Typography>
            <TableContainer>
              <Table size="small">
                <TableHead><TableRow><TableCell>Metric</TableCell><TableCell>Value</TableCell></TableRow></TableHead>
                <TableBody>
                  {scalarStoredBaselineMetricEntries(baseline.baseline_metrics || baseline.metrics).map(([key, value]: [string, any]) => (
                    <TableRow key={key}>
                      <TableCell>{(BASELINE_METRIC_LABELS[key]?.label) || key.replace(/_/g, ' ')}</TableCell>
                      <TableCell sx={{ fontWeight: 500 }}>
                        {typeof value === 'number' ? (key.includes('pmpm') || key.includes('paid') || key.includes('allowed') ? `$${value.toFixed(2)}` : value.toLocaleString()) : String(value)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {detailTab === 1 && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 3 }}>Baseline benchmarks</Typography>
            <TableContainer>
              <Table size="small">
                <TableHead><TableRow><TableCell>Metric</TableCell><TableCell>Value</TableCell><TableCell>Unit</TableCell></TableRow></TableHead>
                <TableBody>
                  {scalarStoredBaselineMetricEntries(baseline.baseline_metrics || baseline.metrics).map(([key, value]: [string, any]) => {
                    const meta = BASELINE_METRIC_LABELS[key]
                    const unit = meta?.unit || '—'
                    return (
                      <TableRow key={key}>
                        <TableCell>{(meta?.label) || key.replace(/_/g, ' ')}</TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>{typeof value === 'number' ? formatMetricValue(value, unit) : String(value)}</TableCell>
                        <TableCell>{unit}</TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {detailTab === 2 && (
        <Card><CardContent>
          <StoredProviderArchetypesSection metrics={(baseline.baseline_metrics || baseline.metrics || {}) as Record<string, unknown>} />
        </CardContent></Card>
      )}
      {detailTab === 3 && (
        <Card><CardContent>
          <StoredPatientSegmentsSection metrics={(baseline.baseline_metrics || baseline.metrics || {}) as Record<string, unknown>} />
        </CardContent></Card>
      )}
      {detailTab === 4 && (
        <Card><CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>Confounder calendar</Typography>
          <Typography color="text.secondary" sx={{ mb: 2 }}>Confounder events are identified in a full baseline analysis run.</Typography>
          <Alert severity="info">Use <strong>Run Baseline Analysis</strong> to get confounder events for this baseline.</Alert>
        </CardContent></Card>
      )}
    </Box>
  )
}

/** Metric key -> display label and unit for stored baseline metrics */
const BASELINE_METRIC_LABELS: Record<string, { label: string; unit: string }> = {
  util_rate_total_per_1000_mm: { label: 'Utilization (per 1k member-months)', unit: 'per_1k' },
  util_rate_target_per_1000_mm: { label: 'Utilization target (per 1k)', unit: 'per_1k' },
  utilization_per_1k: { label: 'Utilization per 1k', unit: 'per_1k' },
  allowed_pmpm_total: { label: 'Allowed PMPM', unit: 'PMPM' },
  allowed_pmpm_target: { label: 'Allowed PMPM (target)', unit: 'PMPM' },
  cost_pmpm: { label: 'Cost PMPM', unit: 'PMPM' },
  paid_pmpm_target: { label: 'Paid PMPM (target)', unit: 'PMPM' },
  total_claims: { label: 'Total claims', unit: 'count' },
  unique_members: { label: 'Unique members', unit: 'count' },
  member_months: { label: 'Member months', unit: 'count' },
  total_paid: { label: 'Total paid', unit: 'currency' },
  total_allowed: { label: 'Total allowed', unit: 'currency' },
}

/** Show stored baselines (from /baselines) when no BASELINE analyses exist yet (e.g. after migration). */
function StoredBaselinesView({
  baselines,
  onRunAnalysis,
  onRefreshList,
  formatDate,
}: {
  baselines: any[]
  onRunAnalysis: () => void
  onRefreshList: () => void
  formatDate: (d: string) => string
}) {
  const [selectedBaseline, setSelectedBaseline] = useState<any | null>(null)
  const [detailTab, setDetailTab] = useState(0)
  const formatMetric = (value: number, _unit: string) => {
    if (_unit === 'percentage' || (typeof value === 'number' && value <= 1 && value > 0)) return `${(value * 100).toFixed(1)}%`
    if (typeof value === 'number' && value >= 1000) return `$${(value / 1000).toFixed(1)}K`
    return typeof value === 'number' ? value.toFixed(2) : String(value)
  }
  const formatMetricValue = (value: number, unit: string) => {
    if (unit === 'PMPM' || unit === 'currency') return `$${Number(value).toFixed(2)}`
    if (unit === 'per_1k') return Number(value).toFixed(2)
    if (unit === 'count') return Number(value).toLocaleString()
    return typeof value === 'number' ? value.toFixed(2) : String(value)
  }
  return (
    <Box>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 1 }}>
            Stored baselines
          </Typography>
          <Typography color="text.secondary" sx={{ mb: 2 }}>
            {baselines.length} baseline(s) are available. Select a row to view details. Run a full baseline analysis for time series and behavior profiling.
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}>
            <Button variant="outlined" size="small" startIcon={<RefreshIcon />} onClick={() => { onRefreshList(); }}>
              Refresh list
            </Button>
            <Button variant="contained" startIcon={<RunIcon />} onClick={onRunAnalysis} sx={{ backgroundColor: healthForesightColors.primary.main, '&:hover': { backgroundColor: healthForesightColors.primary.dark } }}>
              Run Baseline Analysis
            </Button>
          </Box>
          <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: 400 }}>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>Type</TableCell>
                  <TableCell>Window</TableCell>
                  <TableCell>Computed</TableCell>
                  <TableCell>Utilization (per 1k)</TableCell>
                  <TableCell>Cost (PMPM)</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {baselines.slice(0, 50).map((b: any) => {
                  const metrics = b.baseline_metrics || b.metrics || {}
                  const util = metrics.util_rate_total_per_1000_mm ?? metrics.utilization_per_1k ?? metrics.util_rate_target_per_1000_mm
                  const cost = metrics.allowed_pmpm_total ?? metrics.cost_pmpm ?? metrics.allowed_pmpm_target
                  const windowStart = b.window_start_date ? formatDate(b.window_start_date) : '—'
                  const windowEnd = b.window_end_date ? formatDate(b.window_end_date) : '—'
                  const computedAt = b.computed_at ? formatDate(b.computed_at) : '—'
                  const isSelected = selectedBaseline && (selectedBaseline.baseline_id === b.baseline_id || selectedBaseline.id === b.id)
                  return (
                    <TableRow
                      key={b.baseline_id || b.id}
                      selected={!!isSelected}
                      onClick={() => setSelectedBaseline(b)}
                      sx={{ cursor: 'pointer' }}
                    >
                      <TableCell>
                        {b.policy_id ? (
                          <Chip label="Policy" size="small" color="secondary" />
                        ) : (
                          <Chip label="General" size="small" color="primary" />
                        )}
                      </TableCell>
                      <TableCell>{windowStart} – {windowEnd}</TableCell>
                      <TableCell>{computedAt}</TableCell>
                      <TableCell>{util != null ? formatMetric(Number(util), '') : '—'}</TableCell>
                      <TableCell>{cost != null ? `$${Number(cost).toFixed(2)}` : '—'}</TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </TableContainer>
          {baselines.length > 50 && (
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              Showing first 50 of {baselines.length} baselines.
            </Typography>
          )}
        </CardContent>
      </Card>

      {/* Detail view for selected baseline (same structure as full Baseline Analysis summary) */}
      {selectedBaseline && (
        <Box sx={{ mt: 3 }}>
          <Paper sx={{ mb: 3, p: 2 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Analysis Summary: Baseline – {selectedBaseline.policy_id ? 'Policy' : 'General'} – {(selectedBaseline.baseline_id || selectedBaseline.id || '').toString().slice(0, 8)}...
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="caption" color="text.secondary">Baseline ID</Typography>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {(selectedBaseline.baseline_id || selectedBaseline.id || '—').toString().slice(0, 12)}...
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="caption" color="text.secondary">Status</Typography>
                <Chip label="Stored" color="success" size="small" />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="caption" color="text.secondary">Data coverage</Typography>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {(() => {
                    const m = selectedBaseline.baseline_metrics || selectedBaseline.metrics || {}
                    const n = m.total_claims ?? m.unique_members ?? m.member_months
                    return n != null ? `${Number(n).toLocaleString()} ${m.total_claims != null ? 'claims' : m.unique_members != null ? 'members' : 'member-months'}` : '—'
                  })()}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="caption" color="text.secondary">Date range</Typography>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {selectedBaseline.window_start_date && selectedBaseline.window_end_date
                    ? `${formatDate(selectedBaseline.window_start_date)} – ${formatDate(selectedBaseline.window_end_date)}`
                    : '—'}
                </Typography>
              </Grid>
            </Grid>
          </Paper>

          <Tabs value={detailTab} onChange={(_, v) => setDetailTab(v)} sx={{ mb: 3 }}>
            <Tab icon={<TrendingIcon />} iconPosition="start" label="Time Series" />
            <Tab icon={<BenchmarkIcon />} iconPosition="start" label="Benchmarks" />
            <Tab icon={<ProviderIcon />} iconPosition="start" label="Provider Archetypes" />
            <Tab icon={<PatientIcon />} iconPosition="start" label="Patient Segments" />
            <Tab icon={<CalendarIcon />} iconPosition="start" label="Confounder Calendar" />
          </Tabs>

          {detailTab === 0 && (
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 3 }}>
                  Baseline time-series analysis
                </Typography>
                <Typography color="text.secondary" sx={{ mb: 2 }}>
                  This stored baseline is a single-period snapshot. Time series (trend, bounds, observed) are produced by a full baseline analysis run.
                </Typography>
                <Alert severity="info" sx={{ mb: 2 }}>
                  Run <strong>Run Baseline Analysis</strong> above to get time-series charts, provider archetypes, patient segments, and confounder calendar for this baseline.
                </Alert>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>Single-period metrics</Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Metric</TableCell>
                        <TableCell>Value</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {scalarStoredBaselineMetricEntries(selectedBaseline.baseline_metrics || selectedBaseline.metrics).map(([key, value]: [string, any]) => (
                        <TableRow key={key}>
                          <TableCell>
                            {(BASELINE_METRIC_LABELS[key]?.label) || key.replace(/_/g, ' ')}
                          </TableCell>
                          <TableCell sx={{ fontWeight: 500 }}>
                            {typeof value === 'number' ? (key.includes('pmpm') || key.includes('paid') || key.includes('allowed') ? `$${value.toFixed(2)}` : value.toLocaleString()) : String(value)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          )}

          {detailTab === 1 && (
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 3 }}>
                  Baseline benchmarks
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Metric</TableCell>
                        <TableCell>Value</TableCell>
                        <TableCell>Unit</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {scalarStoredBaselineMetricEntries(selectedBaseline.baseline_metrics || selectedBaseline.metrics).map(([key, value]: [string, any]) => {
                        const meta = BASELINE_METRIC_LABELS[key]
                        const unit = meta?.unit || '—'
                        return (
                          <TableRow key={key}>
                            <TableCell>{(meta?.label) || key.replace(/_/g, ' ')}</TableCell>
                            <TableCell sx={{ fontWeight: 600 }}>
                              {typeof value === 'number' ? formatMetricValue(value, unit) : String(value)}
                            </TableCell>
                            <TableCell>{unit}</TableCell>
                          </TableRow>
                        )
                      })}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          )}

          {detailTab === 2 && (
            <Card>
              <CardContent>
                <StoredProviderArchetypesSection metrics={(selectedBaseline.baseline_metrics || selectedBaseline.metrics || {}) as Record<string, unknown>} />
              </CardContent>
            </Card>
          )}

          {detailTab === 3 && (
            <Card>
              <CardContent>
                <StoredPatientSegmentsSection metrics={(selectedBaseline.baseline_metrics || selectedBaseline.metrics || {}) as Record<string, unknown>} />
              </CardContent>
            </Card>
          )}

          {detailTab === 4 && (
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Confounder calendar
                </Typography>
                <Typography color="text.secondary" sx={{ mb: 2 }}>
                  Confounder events and impact are identified in a full baseline analysis run.
                </Typography>
                <Alert severity="info">
                  Use <strong>Run Baseline Analysis</strong> to get confounder events, dates, and affected segments for this baseline.
                </Alert>
              </CardContent>
            </Card>
          )}
        </Box>
      )}
    </Box>
  )
}