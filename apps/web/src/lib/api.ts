/**
 * UEPI API Client
 */
import axios, { AxiosInstance, AxiosError } from 'axios'
import logger from './logger'

const TOKEN_KEY = 'uepi_token'

/** localStorage (default) keeps you signed in across visits; VITE_AUTH_STORAGE=session uses sessionStorage. */
function authStorage(): Storage | null {
  if (typeof window === 'undefined') return null
  return import.meta.env.VITE_AUTH_STORAGE === 'session' ? window.sessionStorage : window.localStorage
}

function clearTokenEverywhere() {
  if (typeof window === 'undefined') return
  try {
    window.localStorage.removeItem(TOKEN_KEY)
    window.sessionStorage.removeItem(TOKEN_KEY)
  } catch {
    /* ignore */
  }
}

// Determine API URL based on environment
// In production (Azure Static Web Apps), use full API URL
// In development, use localhost or relative path
const getApiBaseUrl = () => {
  const host = window.location.hostname.toLowerCase()

  // Local development
  if (host === 'localhost' || host === '127.0.0.1') {
    return import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
  }

  // Production build: prefer baked API URL so login works when the Web App only serves static
  // files or the Node proxy is not running. API CORS allows healthforesight-web*.azurewebsites.net.
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL
  }

  // App Service UI with Node proxy (no VITE_API_URL): same-origin /api/v1 → server.mjs → API
  if (host.endsWith('.azurewebsites.net') && !host.startsWith('healthforesight-api')) {
    return `${window.location.origin}/api/v1`
  }

  if (host.includes('azurestaticapps.net')) {
    return 'https://healthforesight-api.azurewebsites.net/api/v1'
  }

  return '/api/v1'
}

const API_BASE_URL = getApiBaseUrl()

export interface ApiError {
  message: string
  status?: number
  detail?: string
}

/** One-screen policy verdict: which policies save money, which backfire, and why */
export interface PolicyVerdictRow {
  policy_id: string
  policy_name: string
  policy_effective_date?: string | null
  verdict: string
  verdict_label: string
  savings_or_cost_impact_pmpm?: number | null
  cost_impact_pct?: number | null
  utilization_impact_pct?: number | null
  confidence_pct?: number | null
  verdict_reason: string
  recommendation: string
  observation_id?: string | null
  observation_period_end?: string | null
  has_backfire_risk: boolean
}

export class ApiClient {
  private client: AxiosInstance
  private token: string | null = null

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 90000, // 90s default when server is busy (with-claim-counts, analyses, etc.)
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor to add auth token and log requests
    this.client.interceptors.request.use(
      (config) => {
        // Log request start time
        ;(config as any).startTime = Date.now()
        
        // Add Bearer token only when present (no auto mock – login page must sign in)
        const token = this.getToken()
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        
        // Log request
        logger.debug('API_REQUEST', `${config.method?.toUpperCase()} ${config.url}`, {
          method: config.method,
          url: config.url,
          headers: config.headers,
          data: config.data,
        })
        
        return config
      },
      (error) => {
        logger.error('API_REQUEST', 'Request failed', error)
        return Promise.reject(error)
      }
    )

    // Response interceptor for error handling and logging
    this.client.interceptors.response.use(
      (response) => {
        // Calculate duration
        const startTime = (response.config as any).startTime
        const duration = startTime ? Date.now() - startTime : 0
        const method = response.config.method?.toUpperCase() || 'UNKNOWN'
        const url = response.config.url || ''

        // 404 on predicted-impact is expected when a policy has no prediction yet; log at debug to avoid console noise
        if (response.status === 404 && url.includes('predicted-impact')) {
          logger.debug('API', `${method} ${url} -> 404 (${duration}ms) (no prediction yet)`, {
            method, url, status: 404, duration,
          })
        } else {
          logger.logApiCall(method, url, response.status, duration, response.config.data, response.data)
        }

        return response
      },
      (error: AxiosError) => {
        // Calculate duration
        const startTime = error.config ? (error.config as any).startTime : undefined
        const duration = startTime ? Date.now() - startTime : 0
        
        // Handle network errors gracefully (including timeouts)
        if (!error.response) {
          // Log network errors
          logger.logApiCall(
            error.config?.method?.toUpperCase() || 'UNKNOWN',
            error.config?.url || '',
            0,
            duration,
            error.config?.data,
            undefined,
            error
          )
          
          // Don't log timeout errors - they're expected when API is unavailable
          if (!error.code || (error.code !== 'ECONNABORTED' && !error.message?.includes('timeout'))) {
            logger.error('API_NETWORK', 'Network error', error, {
              url: error.config?.url,
              method: error.config?.method,
            })
          }
          
          return Promise.reject({
            message: error.code === 'ECONNABORTED' ? 'API timeout' : 'Network error: Unable to connect to API',
            status: 0,
            detail: error.message,
            code: error.code,
          })
        }
        
        // Log error response
        logger.logApiCall(
          error.config?.method?.toUpperCase() || 'UNKNOWN',
          error.config?.url || '',
          error.response.status,
          duration,
          error.config?.data,
          error.response.data,
          error
        )
        
        if (error.response?.status === 401) {
          // Token expired or invalid - don't redirect immediately, let components handle it
          this.setToken(null)
          logger.warn('API_AUTH', 'Authentication failed', { url: error.config?.url })
        }
        
        return Promise.reject(this.formatError(error))
      }
    )
  }

  setToken(token: string | null) {
    this.token = token
    if (typeof window === 'undefined') return
    if (token) {
      const s = authStorage()
      if (s) s.setItem(TOKEN_KEY, token)
      const other =
        import.meta.env.VITE_AUTH_STORAGE === 'session' ? window.localStorage : window.sessionStorage
      try {
        other.removeItem(TOKEN_KEY)
      } catch {
        /* ignore */
      }
    } else {
      clearTokenEverywhere()
    }
  }

  /** Returns stored token, or null. Treats legacy dev/mock tokens as invalid and clears them so login is required. */
  getToken(): string | null {
    const s = authStorage()
    let t = this.token || (s?.getItem(TOKEN_KEY) ?? null)
    if (!t) return null
    if (t.startsWith('dev-token-') || t.startsWith('mock-') || t === 'dev-token-123') {
      this.setToken(null)
      return null
    }
    return t
  }

  private formatError(error: AxiosError): ApiError {
    const apiError: ApiError = {
      message: error.message,
      status: error.response?.status,
    }

    if (error.response?.data) {
      const data = error.response.data as any
      apiError.detail = data.detail || data.message || JSON.stringify(data)
    }

    return apiError
  }

  // Auth endpoints (supports AD/SSO and local email+password)
  async getMe() {
    const response = await this.client.get('/auth/me')
    return response.data
  }

  /** Session check at startup — short timeout so users reach login quickly if API/CORS is down */
  async getMeSessionVerify(timeoutMs = 12000) {
    const response = await this.client.get('/auth/me', { timeout: timeoutMs })
    return response.data
  }

  /** Local login (email + password). Returns { access_token, token_type, user_id, email, roles }. Use access_token as Bearer. */
  async login(email: string, password: string) {
    const response = await this.client.post('/auth/login', { email, password })
    return response.data
  }

  // Policy endpoints
  async getPolicies(params?: { skip?: number; limit?: number; policy_type?: string }) {
    // Use longer timeout for policies endpoint since it may load many files
    const response = await this.client.get('/policies', { params, timeout: 60000 }) // 60 seconds
    return response.data
  }

  /** Policies with claim counts (sorted by claim_count desc). Use to pick policy with most data for what-if. */
  async getPoliciesWithClaimCounts(limit = 20) {
    const response = await this.client.get('/policies/with-claim-counts', { params: { limit }, timeout: 120000 })
    return response.data
  }

  async getPolicy(id: string) {
    const response = await this.client.get(`/policies/${id}`)
    return response.data
  }

  async getPolicyClaimCountsBreakdown(policyId: string) {
    const response = await this.client.get(`/policies/${policyId}/claim-counts-breakdown`)
    return response.data
  }

  async createPolicy(data: any) {
    const response = await this.client.post('/policies', data)
    return response.data
  }

  async updatePolicy(id: string, data: any) {
    const response = await this.client.put(`/policies/${id}`, data)
    return response.data
  }

  async activatePolicy(id: string) {
    const response = await this.client.patch(`/policies/${id}/status`, { status: 'ACTIVE' })
    return response.data
  }

  async deactivatePolicy(id: string) {
    const response = await this.client.patch(`/policies/${id}/status`, { status: 'INACTIVE' })
    return response.data
  }

  async getPolicyVersions(policyId: string) {
    const response = await this.client.get(`/policies/${policyId}/versions`)
    return response.data
  }

  async createPolicyVersion(policyId: string, data: any) {
    const response = await this.client.post(`/policies/${policyId}/versions`, data)
    return response.data
  }

  async getPolicyPredictedImpact(policyId: string) {
    try {
      // Accept 404 so axios doesn't throw (avoids console errors for policies without predicted impact)
      const response = await this.client.get(`/policies/${policyId}/predicted-impact`, {
        timeout: 15000,
        validateStatus: (status) =>
          status === 200 || status === 204 || status === 404 || status === 500,
      })
      if (response.status === 404 || response.status === 204 || response.status === 500) return null
      return response.data
    } catch (error: any) {
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout') || !error.response) return null
      throw error
    }
  }

  async generatePolicyPredictedImpact(policyId: string) {
    const response = await this.client.post(`/policies/${policyId}/predicted-impact`)
    return response.data
  }

  async generateAllPoliciesPredictedImpact(force: boolean = false) {
    const response = await this.client.post('/policies/generate-predicted-impact', null, {
      params: { force: force }
    })
    return response.data
  }

  async completePolicyConfigurations() {
    const response = await this.client.post('/policies/complete-configurations')
    return response.data
  }

  // Policy import endpoints
  async uploadPolicyPackage(file: File, sourceSystem: string, sourceFormat: string) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('source_system', sourceSystem)
    formData.append('source_format', sourceFormat)
    
    const response = await this.client.post('/policies/import/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  }

  async reviewAndSavePolicyImport(reviewData: any) {
    const response = await this.client.post('/policies/import/review', reviewData)
    return response.data
  }

  // Ingestion endpoints
  async getIngestions() {
    const response = await this.client.get('/ingestions')
    return response.data
  }

  async getLastExecutedIngestion() {
    const response = await this.client.get('/ingestions/last-executed')
    return response.data
  }

  async getIngestion(id: string) {
    const response = await this.client.get(`/ingestions/${id}`)
    return response.data
  }

  async createIngestion(data: any) {
    const response = await this.client.post('/ingestions', data)
    return response.data
  }

  async runIngestion(ingestionId: string) {
    const response = await this.client.post(`/ingestions/${ingestionId}/run`)
    return response.data
  }

  async viewSourceData(ingestionId: string, limit: number = 100, offset: number = 0) {
    const response = await this.client.get(`/ingestions/${ingestionId}/view-source`, {
      params: { limit, offset },
    })
    return response.data
  }

  async viewCuratedData(ingestionId: string, limit: number = 100, offset: number = 0) {
    const response = await this.client.get(`/ingestions/${ingestionId}/view-curated`, {
      params: { limit, offset },
    })
    return response.data
  }

  async uploadAndIngest(file: File, ingestionType: string, autoDetect: boolean = true, mappingConfig?: any) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('ingestion_type', ingestionType)
    formData.append('auto_detect', String(autoDetect))
    if (mappingConfig) {
      formData.append('mapping_config', JSON.stringify(mappingConfig))
    }
    const response = await this.client.post('/ingestions/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  }

  async analyzeSchema(file: File, ingestionType: string) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('ingestion_type', ingestionType)
    const response = await this.client.post('/ingestions/analyze-schema', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  }

  async getIngestionErrors(ingestionId: string) {
    const response = await this.client.get(`/ingestions/${ingestionId}/errors`)
    return response.data
  }

  async getDatasets(params?: { dataset_type?: string; year?: number; month?: number; lob?: string; market?: string }) {
    const response = await this.client.get('/datasets', { params })
    return response.data
  }

  // Pipeline endpoints
  async getPipelines(params?: { skip?: number; limit?: number; active_only?: boolean }) {
    const response = await this.client.get('/pipelines', { params })
    return response.data
  }

  async getPipeline(pipelineId: string) {
    const response = await this.client.get(`/pipelines/${pipelineId}`)
    return response.data
  }

  async createPipeline(data: any) {
    const response = await this.client.post('/pipelines', data)
    return response.data
  }

  async updatePipeline(pipelineId: string, data: any) {
    const response = await this.client.put(`/pipelines/${pipelineId}`, data)
    return response.data
  }

  async deletePipeline(pipelineId: string) {
    const response = await this.client.delete(`/pipelines/${pipelineId}`)
    return response.data
  }

  async activatePipeline(pipelineId: string, active: boolean) {
    const response = await this.client.post(`/pipelines/${pipelineId}/activate`, null, {
      params: { active },
    })
    return response.data
  }

  async runPipeline(pipelineId: string, file: File) {
    const formData = new FormData()
    formData.append('file', file)
    const response = await this.client.post(`/pipelines/${pipelineId}/run`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  }

  async getPipelineRuns(pipelineId: string, params?: { skip?: number; limit?: number }) {
    const response = await this.client.get(`/pipelines/${pipelineId}/runs`, { 
      params,
      timeout: 60000 // 60 seconds for pipeline runs
    })
    return response.data
  }

  async getPipelineRun(pipelineId: string, runId: string) {
    const response = await this.client.get(`/pipelines/${pipelineId}/runs/${runId}`)
    return response.data
  }

  // Pipeline monitoring endpoints
  async getPipelineHealth(pipelineId: string) {
    const response = await this.client.get(`/pipelines/${pipelineId}/health`, {
      timeout: 60000 // 60 seconds for pipeline health
    })
    return response.data
  }

  async getPipelineAlerts(pipelineId: string, params?: { severity?: string; limit?: number }) {
    const response = await this.client.get(`/pipelines/${pipelineId}/alerts`, { params })
    return response.data
  }

  async getPipelineMetrics(pipelineId: string, limit: number = 50) {
    const response = await this.client.get(`/pipelines/${pipelineId}/metrics`, { params: { limit } })
    return response.data
  }

  async getRunQualityReport(pipelineId: string, runId: string) {
    const response = await this.client.get(`/pipelines/${pipelineId}/runs/${runId}/quality`)
    return response.data
  }

  async acknowledgeAlert(pipelineId: string, alertId: string) {
    const response = await this.client.post(`/pipelines/${pipelineId}/alerts/${alertId}/acknowledge`)
    return response.data
  }

  async resolveAlert(pipelineId: string, alertId: string) {
    const response = await this.client.post(`/pipelines/${pipelineId}/alerts/${alertId}/resolve`)
    return response.data
  }

  // Data Explorer endpoints
  async listDataFiles(path: string = '', includeFiles: boolean = true, includeFolders: boolean = true) {
    const response = await this.client.get('/data-explorer/list', {
      params: { path, include_files: includeFiles, include_folders: includeFolders },
    })
    return response.data
  }

  async viewDataFile(path: string, limit: number = 100, offset: number = 0) {
    const response = await this.client.get('/data-explorer/view', {
      params: { path, limit, offset },
    })
    return response.data
  }

  async previewDataFile(path: string, rows: number = 10) {
    const response = await this.client.get('/data-explorer/preview', {
      params: { path, rows },
    })
    return response.data
  }

  // Stage 2 Policy API
  async getPolicyTypes(category?: string) {
    const response = await this.client.get('/policy-types', {
      params: category ? { category } : {},
    })
    return response.data
  }

  async getPolicyTypeMetadata(leverType: string) {
    const response = await this.client.get(`/policy-types/${leverType}`)
    return response.data
  }

  async validatePolicy(policy: any) {
    const response = await this.client.post('/policies/validate', policy)
    return response.data
  }

  async importPolicies(file: File, fileFormat: string = 'auto', mappingConfig?: any) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('file_format', fileFormat)
    if (mappingConfig) {
      formData.append('mapping_config_json', JSON.stringify(mappingConfig))
    }
    const response = await this.client.post('/policies/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  }

  async checkPolicySimilarity(policyId: string, policy: any) {
    const response = await this.client.post(`/policies/${policyId}/check-similarity`, policy)
    return response.data
  }

  async getPolicyReadiness(policyId: string) {
    const response = await this.client.get(`/policies/${policyId}/readiness`)
    return response.data
  }

  async getDatasetSchema(datasetId: string) {
    const response = await this.client.get(`/datasets/${datasetId}/schema`)
    return response.data
  }

  async viewDataset(
    datasetId: string,
    params?: {
      limit?: number
      offset?: number
      lob?: string
      market?: string
      year?: number
      month?: number
      cpt_code?: string
      place_of_service?: string
      service_category?: string
      member_id?: string
      provider_id?: string
    }
  ) {
    const response = await this.client.get(`/datasets/${datasetId}/view`, { params })
    return response.data
  }

  // Analysis endpoints
  async createImpactAnalysis(data: any) {
    const response = await this.client.post('/analyses/impact', data)
    return response.data
  }

  async createSimulateAnalysis(data: any) {
    const response = await this.client.post('/analyses/simulate', data, { timeout: 120000 })
    return response.data
  }

  async createElasticityAnalysis(data: { policy_id: string; service_categories?: string[] }) {
    const response = await this.client.post('/analyses/elasticity', data)
    return response.data
  }

  /**
   * Refresh baseline (general or policy-specific)
   */
  async refreshBaseline(policyId?: string, baselineType: string = 'ROLLING', windowMonths: number = 12) {
    const response = await this.client.post('/baselines/refresh', {
      policy_id: policyId || null,
      baseline_type: baselineType,
      window_months: windowMonths,
      refresh_reason: 'MANUAL',
    })
    return response.data
  }

  /**
   * Refresh general baseline and all policy-specific baselines in one go (stored metrics only).
   * Uses a long timeout since it may run many baseline computations.
   */
  async refreshAllBaselines(baselineType: string = 'ROLLING', windowMonths: number = 12) {
    const longTimeoutClient = axios.create({
      baseURL: API_BASE_URL,
      timeout: 300000, // 5 minutes
      headers: {
        'Content-Type': 'application/json',
      },
    })
    const token = this.getToken()
    if (token) {
      longTimeoutClient.defaults.headers.common.Authorization = `Bearer ${token}`
    }
    const response = await longTimeoutClient.post('/baselines/refresh-all', null, {
      params: { baseline_type: baselineType, window_months: windowMonths },
    })
    return response.data
  }

  /**
   * Generate full baseline analyses (with all 5 tabs) for general + every policy.
   * Prefer using the frontend loop (createBaselineAnalysis per scope) to avoid
   * proxy/server timeouts; this single long request may still time out.
   */
  async generateAllFullBaselines(): Promise<{ analyses_created: Array<{ id: string; name: string; status: string }>; errors: Array<{ name: string; detail: string }> }> {
    const longTimeoutClient = axios.create({
      baseURL: API_BASE_URL,
      timeout: 3600000, // 1 hour
      headers: {
        'Content-Type': 'application/json',
      },
    })
    const token = this.getToken()
    if (token) {
      longTimeoutClient.defaults.headers.common.Authorization = `Bearer ${token}`
    }
    const response = await longTimeoutClient.post('/analyses/baseline/generate-all')
    return response.data
  }

  /**
   * List baselines
   */
  async listBaselines(policyId?: string, baselineType?: string) {
    const response = await this.client.get('/baselines', {
      params: {
        policy_id: policyId,
        baseline_type: baselineType,
      },
    })
    return response.data
  }

  /**
   * Get latest baseline
   */
  async getLatestBaseline(policyId?: string) {
    const response = await this.client.get('/baselines/latest', {
      params: {
        policy_id: policyId,
      },
    })
    return response.data
  }

  async createBaselineAnalysis(data: {
    name: string
    start_date?: string
    end_date?: string
    group_by?: string[]
    n_clusters?: number
    baseline_type?: 'GENERAL' | 'POLICY_SPECIFIC'
    policy_id?: string | null
  }) {
    // Baseline analysis can take several minutes, use longer timeout per request
    const longTimeoutClient = axios.create({
      baseURL: API_BASE_URL,
      timeout: 600000, // 10 minutes per analysis
      headers: {
        'Content-Type': 'application/json',
        'Authorization': this.getToken() ? `Bearer ${this.getToken()}` : undefined,
      },
    })
    const response = await longTimeoutClient.post('/analyses/baseline', data)
    return response.data
  }

  async getBaselineAnalysis(id: string) {
    // Use longer timeout for baseline results as they can be large
    const response = await this.client.get(`/analyses/${id}/baseline`, {
      timeout: 120000, // 2 minutes for large baseline results
    })
    return response.data
  }

  async getAnalyses(params?: { skip?: number; limit?: number; analysis_type?: string }) {
    const response = await this.client.get('/analyses', { params, timeout: 90000 })
    return response.data
  }

  async getAnalysis(id: string) {
    const response = await this.client.get(`/analyses/${id}`)
    return response.data
  }

  async getAnalysisResults(id: string, resultType?: string) {
    const params = resultType ? { result_type: resultType } : {}
    const response = await this.client.get(`/analyses/${id}/results`, { params })
    return response.data
  }

  async getAnalysisMethodChecks(id: string) {
    const response = await this.client.get(`/analyses/${id}/method-checks`)
    return response.data
  }

  async getAnalysisTrustPanel(id: string) {
    const response = await this.client.get(`/analyses/${id}/trust-panel`)
    return response.data
  }

  async getAnalysisTimeseries(id: string) {
    const response = await this.client.get(`/analyses/${id}/timeseries`)
    return response.data
  }

  // Scorecard endpoints
  async getScorecards(params?: { period?: string; lob?: string; market?: string }) {
    const response = await this.client.get('/scorecards/policies', { params })
    return response.data
  }

  async getPolicyScorecard(policyId: string, period?: string) {
    const params = period ? { period } : {}
    const response = await this.client.get(`/scorecards/policies/${policyId}`, { params })
    return response.data
  }

  async getPolicyScorecardTrends(policyId: string, periods: number = 4) {
    const params = { periods }
    const response = await this.client.get(`/scorecards/policies/${policyId}/trends`, { params })
    return response.data
  }

  // Policy verdicts – one-screen view: which policies save money, which backfire, and why
  async getPolicyVerdicts(): Promise<{ items: PolicyVerdictRow[]; count: number }> {
    const response = await this.client.get<{ items: PolicyVerdictRow[]; count: number }>('/policy-verdicts')
    return response.data
  }

  async getObservationEvidencePack(observationId: string) {
    const response = await this.client.get(`/observations/${observationId}/evidence-pack`)
    return response.data
  }

  // Observation endpoints
  async listObservations(params?: { policy_id?: string; data_period_id?: string; observation_type?: string; include_trends?: boolean; latest_only?: boolean }) {
    const response = await this.client.get('/observations', { params })
    return response.data
  }

  async getObservation(observationId: string) {
    const response = await this.client.get(`/observations/${observationId}`)
    return response.data
  }

  async getObservationForecast(
    observationId: string,
    policyId: string,
    metricType: 'utilization' | 'cost' = 'utilization',
    timeHorizonMonths: number = 12
  ) {
    const response = await this.client.get(`/observations/${observationId}/forecast`, {
      params: {
        policy_id: policyId,
        metric_type: metricType,
        time_horizon_months: timeHorizonMonths,
      },
    })
    return response.data
  }

  async getObservationComparison(observationId: string) {
    const response = await this.client.get(`/observations/${observationId}/comparison`)
    return response.data
  }

  async createObservationFromAnalysis(analysisId: string, policyId: string, dataPeriodId?: string) {
    const params: any = { policy_id: policyId }
    if (dataPeriodId) {
      params.data_period_id = dataPeriodId
    }
    // Long timeout: from-analysis loads claims, computes metrics, and can take 2–5+ min for large data
    const response = await this.client.post(`/observations/from-analysis/${analysisId}`, {}, { params, timeout: 300000 })
    return response.data
  }

  async generateScorecards(data: { period?: string; policy_ids?: string[] }) {
    const response = await this.client.post('/scorecards/generate', data)
    return response.data
  }

  async compareScorecards(policyIds: string[], period?: string) {
    const response = await this.client.post('/scorecards/compare', policyIds, {
      params: period ? { period } : {},
    })
    return response.data
  }

  // Export endpoints
  async createAuditPack(analysisId: string) {
    const response = await this.client.post('/exports/audit-pack', {
      analysis_id: analysisId,
      export_type: 'AUDIT_PACK',
    })
    return response.data
  }

  async getExport(id: string) {
    const response = await this.client.get(`/exports/${id}`)
    return response.data
  }

  async downloadExport(id: string): Promise<string> {
    // Download export file - returns blob URL
    const response = await this.client.get(`/exports/${id}/download`, {
      responseType: 'blob',
    })
    // Create blob URL for download
    const blob = new Blob([response.data])
    const url = window.URL.createObjectURL(blob)
    return url
  }

  async listExports(params?: { export_type?: string; analysis_id?: string }) {
    const response = await this.client.get('/exports', { params })
    return response.data
  }

  async createExport(data: { analysis_id: string; export_type: string; parent_export_id?: string; change_description?: string }) {
    const response = await this.client.post('/exports', data)
    return response.data
  }

  async getExportVersions(exportId: string) {
    const response = await this.client.get(`/exports/${exportId}/versions`)
    return response.data
  }

  async createExportVersion(exportId: string, changeDescription: string) {
    const response = await this.client.post(`/exports/${exportId}/versions`, null, {
      params: { change_description: changeDescription },
    })
    return response.data
  }

  // Cohort endpoints
  async getCohorts() {
    const response = await this.client.get('/cohorts')
    return response.data
  }

  async getCohort(id: string) {
    const response = await this.client.get(`/cohorts/${id}`)
    return response.data
  }

  async createCohort(data: any) {
    const response = await this.client.post('/cohorts', data)
    return response.data
  }

  async updateCohort(id: string, data: any) {
    const response = await this.client.put(`/cohorts/${id}`, data)
    return response.data
  }

  async deleteCohort(id: string) {
    await this.client.delete(`/cohorts/${id}`)
  }

  async getCohortMembers(cohortId: string, skip: number = 0, limit: number = 100) {
    const response = await this.client.get(`/cohorts/${cohortId}/members`, {
      params: { skip, limit },
    })
    return response.data
  }

  // Decision endpoints
  async getDecisions(params?: {
    quarter?: string
    status?: string
    lob?: string
    market?: string
    owner?: string
  }) {
    const response = await this.client.get('/decisions', { params })
    return response.data
  }

  async getDecision(id: string) {
    const response = await this.client.get(`/decisions/${id}`)
    return response.data
  }

  async createDecision(data: any) {
    const response = await this.client.post('/decisions', data)
    return response.data
  }

  async updateDecision(id: string, data: any) {
    const response = await this.client.put(`/decisions/${id}`, data)
    return response.data
  }

  // Decision attachment endpoints
  async getDecisionAttachments(decisionId: string) {
    const response = await this.client.get(`/decisions/${decisionId}/attachments`)
    return response.data
  }

  async uploadDecisionAttachment(decisionId: string, file: File, label: string) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('label', label)
    const response = await this.client.post(`/decisions/${decisionId}/attachments`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  }

  async attachExportToDecision(decisionId: string, exportId: string, label: string) {
    const formData = new FormData()
    formData.append('export_id', exportId)
    formData.append('label', label)
    const response = await this.client.post(`/decisions/${decisionId}/attachments`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  }

  async attachExternalUriToDecision(decisionId: string, uri: string, label: string) {
    const formData = new FormData()
    formData.append('external_uri', uri)
    formData.append('label', label)
    const response = await this.client.post(`/decisions/${decisionId}/attachments`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  }

  async downloadDecisionAttachment(decisionId: string, attachmentId: string) {
    const response = await this.client.get(`/decisions/${decisionId}/attachments/${attachmentId}/download`, {
      responseType: 'blob',
    })
    const blob = new Blob([response.data])
    const url = window.URL.createObjectURL(blob)
    return url
  }

  async deleteDecisionAttachment(decisionId: string, attachmentId: string) {
    await this.client.delete(`/decisions/${decisionId}/attachments/${attachmentId}`)
  }

  // Lineage endpoints
  async getDataCoverage() {
    const response = await this.client.get('/lineage/coverage')
    return response.data
  }

  async getRecentIngestions() {
    const response = await this.client.get('/lineage/ingestions')
    return response.data
  }

  async getAnalysisRuns() {
    const response = await this.client.get('/lineage/analysis-runs')
    return response.data
  }

  async getFullLineage() {
    const response = await this.client.get('/lineage/full')
    return response.data
  }

  // Data Health endpoints
  async getDataCompleteness(params?: { dataset_type?: string; start_year?: number; end_year?: number }) {
    const response = await this.client.get('/data-health/completeness', { params })
    return response.data
  }

  async getValidationErrors(params?: { ingestion_id?: string; error_type?: string; limit?: number }) {
    const response = await this.client.get('/data-health/validation-errors', { params })
    return response.data
  }

  async getDataLineage(params?: { dataset_id?: string; ingestion_id?: string }) {
    const response = await this.client.get('/data-health/lineage', { params })
    return response.data
  }

  async getDataHealthRefreshStatus() {
    const response = await this.client.get('/data-health/refresh-status')
    return response.data
  }

  // Traceability endpoints
  async queryTraceability(params: {
    entityType?: string
    entityId?: string
    dataPeriodId?: string
    policyId?: string
    policyVersionId?: string
  }) {
    const queryParams = new URLSearchParams()
    if (params.entityType) queryParams.append('entity_type', params.entityType)
    if (params.entityId) queryParams.append('entity_id', params.entityId)
    if (params.dataPeriodId) queryParams.append('data_period_id', params.dataPeriodId)
    if (params.policyId) queryParams.append('policy_id', params.policyId)
    if (params.policyVersionId) queryParams.append('policy_version_id', params.policyVersionId)
    const response = await this.client.get(`/traceability/query?${queryParams.toString()}`)
    return response.data
  }

  async getRefreshStatus(params: {
    entityType: string
    entityId: string
    lastRefreshTimestamp: string
  }) {
    const queryParams = new URLSearchParams()
    queryParams.append('entity_type', params.entityType)
    queryParams.append('entity_id', params.entityId)
    queryParams.append('last_refresh_timestamp', params.lastRefreshTimestamp)
    const response = await this.client.get(`/traceability/refresh-status?${queryParams.toString()}`)
    return response.data
  }

  async getAuditTrail(entityType: string, entityId: string) {
    const queryParams = new URLSearchParams()
    queryParams.append('entity_type', entityType)
    queryParams.append('entity_id', entityId)
    const response = await this.client.get(`/traceability/audit-trail?${queryParams.toString()}`)
    return response.data
  }

  // Learning endpoints
  // Scenario Accuracy Tracking (Phase 7)
  async linkScenarioToPolicy(scenarioAnalysisId: string, policyId: string, metadata?: any) {
    const response = await this.client.post('/scenario-accuracy/link', {
      scenario_analysis_id: scenarioAnalysisId,
      policy_id: policyId,
      metadata: metadata || {},
    })
    return response.data
  }

  async computeScenarioAccuracy(scenarioAnalysisId: string, observationId: string) {
    const response = await this.client.post('/scenario-accuracy/compute', {
      scenario_analysis_id: scenarioAnalysisId,
      observation_id: observationId,
    })
    return response.data
  }

  async getObservations(params?: { policy_id?: string; period_id?: string; observation_id?: string }) {
    const response = await this.client.get('/observations', { params, timeout: 90000 })
    return response.data
  }

  async getScenarioAccuracy(scenarioAnalysisId?: string, policyId?: string) {
    const params: any = {}
    if (scenarioAnalysisId) params.scenario_analysis_id = scenarioAnalysisId
    if (policyId) params.policy_id = policyId

    const response = await this.client.get('/scenario-accuracy', { params, timeout: 90000 })
    return response.data
  }

  async getScenarioLinks(scenarioAnalysisId?: string, policyId?: string) {
    const params: any = {}
    if (scenarioAnalysisId) params.scenario_analysis_id = scenarioAnalysisId
    if (policyId) params.policy_id = policyId

    const response = await this.client.get('/scenario-accuracy/links', { params })
    return response.data
  }

  async getPredictionAccuracy(policyId: string) {
    const response = await this.client.get(`/learning/accuracy/${policyId}`)
    return response.data
  }

  async getAccuracyHistory(policyId: string, limit: number = 10) {
    const response = await this.client.get(`/learning/accuracy/history/${policyId}`, {
      params: { limit },
    })
    return response.data
  }

  async listElasticityModels(policyType?: string, serviceCategory?: string) {
    const params: any = {}
    if (policyType) params.policy_type = policyType
    if (serviceCategory) params.service_category = serviceCategory
    const response = await this.client.get('/learning/elasticity-models', { params })
    return response.data
  }

  async getElasticityModel(modelId: string) {
    const response = await this.client.get(`/learning/elasticity-models/${modelId}`)
    return response.data
  }

  // Data Quality endpoints
  async getDataQualityReport() {
    const response = await this.client.get('/data-quality/report')
    return response.data
  }

  async runDataQualityValidation() {
    const response = await this.client.post('/data-quality/validate')
    return response.data
  }

  async getDataQualitySummary() {
    const response = await this.client.get('/data-quality/summary')
    return response.data
  }

  // Daily Jobs endpoints
  async triggerDailyJob(targetDate?: string, runObservations: boolean = true) {
    const params: any = {}
    if (targetDate) {
      params.target_date = targetDate
    }
    params.run_observations = runObservations
    const response = await this.client.post('/jobs/daily-data-and-observations', null, { params })
    return response.data
  }

  async getDailyJobStatus(jobId: string) {
    const response = await this.client.get(`/jobs/daily-data-and-observations/status/${jobId}`)
    return response.data
  }

  // Dashboard endpoints (Phase 9)
  async getDashboardSummary() {
    const response = await this.client.get('/dashboard/summary')
    return response.data
  }

  async getPolicyPerformance(limit: number = 10) {
    const response = await this.client.get('/dashboard/policy-performance', {
      params: { limit },
    })
    return response.data
  }

  // Schedules endpoints (Phase 9)
  async createSchedule(data: {
    name: string
    schedule_type: string
    frequency: string
    time: string
    day_of_week?: number
    day_of_month?: number
    config?: any
    enabled?: boolean
  }) {
    const response = await this.client.post('/schedules', data)
    return response.data
  }

  async getSchedules() {
    const response = await this.client.get('/schedules')
    return response.data
  }

  async getSchedule(scheduleId: string) {
    const response = await this.client.get(`/schedules/${scheduleId}`)
    return response.data
  }

  async updateSchedule(scheduleId: string, data: any) {
    const response = await this.client.put(`/schedules/${scheduleId}`, data)
    return response.data
  }

  async deleteSchedule(scheduleId: string) {
    await this.client.delete(`/schedules/${scheduleId}`)
  }

  // Notifications endpoints (Phase 9)
  async getNotifications(unreadOnly: boolean = false, limit: number = 50) {
    const response = await this.client.get('/notifications', {
      params: { unread_only: unreadOnly, limit },
    })
    return response.data
  }

  async getUnreadNotificationCount() {
    const response = await this.client.get('/notifications/unread-count')
    return response.data
  }

  async markNotificationRead(notificationId: string) {
    const response = await this.client.post(`/notifications/${notificationId}/read`)
    return response.data
  }

  async markAllNotificationsRead() {
    const response = await this.client.post('/notifications/mark-all-read')
    return response.data
  }

  // RBAC / Access endpoints (Epic 1)
  async getRoles() {
    const response = await this.client.get('/roles')
    return response.data
  }

  /** List roles from access router (for user management). Requires POLICY_ADMIN. */
  async getAccessRoles() {
    const response = await this.client.get('/access/roles')
    return response.data
  }

  async getRole(roleId: string) {
    const response = await this.client.get(`/roles/${roleId}`)
    return response.data
  }

  async createRole(data: any) {
    const response = await this.client.post('/roles', data)
    return response.data
  }

  async updateRole(roleId: string, data: any) {
    const response = await this.client.put(`/roles/${roleId}`, data)
    return response.data
  }

  async deleteRole(roleId: string) {
    const response = await this.client.delete(`/roles/${roleId}`)
    return response.data
  }

  async getUserRoles(userId: string) {
    try {
      // Access router is at /api/v1/access, so the path is /access/users/{id}/roles
      const response = await this.client.get(`/access/users/${userId}/roles`, { timeout: 90000 })
      return response.data
    } catch (err: any) {
      console.warn('Failed to get user roles:', err)
      // Return empty array on error
      return { user_id: userId, role_names: [] }
    }
  }

  async assignUserRole(userId: string, roleId: string, resourceScopes?: any[]) {
    const response = await this.client.post(`/users/${userId}/roles`, {
      role_id: roleId,
      resource_scopes: resourceScopes,
    })
    return response.data
  }

  async removeUserRole(userId: string, roleId: string) {
    const response = await this.client.delete(`/users/${userId}/roles/${roleId}`)
    return response.data
  }

  async checkPermission(resource: string, action: string, resourceId?: string) {
    const response = await this.client.get('/access/check-permission', {
      params: { resource, action, resource_id: resourceId },
    })
    return response.data
  }

  // User management (access router)
  async listUsers(params?: { skip?: number; limit?: number }) {
    const response = await this.client.get('/access/users', { params: params ?? {} })
    return response.data
  }

  async getAccessUser(userId: string) {
    const response = await this.client.get(`/access/users/${userId}`)
    return response.data
  }

  async createUser(data: { email: string; full_name?: string; role_names?: string[]; password?: string }) {
    const response = await this.client.post('/access/users', data)
    return response.data
  }

  async updateAccessUser(userId: string, data: { full_name?: string; is_active?: string; role_names?: string[]; password?: string }) {
    const response = await this.client.patch(`/access/users/${userId}`, data)
    return response.data
  }

  async assignUserRoles(userId: string, roleNames: string[]) {
    const response = await this.client.post(`/access/users/${userId}/roles`, {
      user_id: userId,
      role_names: roleNames,
    })
    return response.data
  }

  async getUserPermissions(userId: string) {
    try {
      // Access router is at /api/v1/access, so the path is /access/users/{id}/permissions
      const response = await this.client.get(`/access/users/${userId}/permissions`, { timeout: 90000 })
      return response.data
    } catch (err: any) {
      console.warn('Failed to get user permissions:', err)
      // Return empty array on error
      return []
    }
  }

  // Persona dashboard endpoints
  async getExecutiveDashboard() {
    const response = await this.client.get('/dashboards/executive')
    return response.data
  }

  async getPolicyOwnerDashboard() {
    const response = await this.client.get('/dashboards/policy-owner')
    return response.data
  }

  async getAnalystDashboard() {
    const response = await this.client.get('/dashboards/analyst')
    return response.data
  }

  async getOpsClinicalDashboard() {
    const response = await this.client.get('/dashboards/ops-clinical')
    return response.data
  }

  // Epic 2: Policy Workspace API
  async getPolicyWorkspace(policyId: string) {
    const response = await this.client.get(`/policies/${policyId}/workspace`)
    return response.data
  }

  async getPolicyVersion(policyId: string, versionNumber: number) {
    const response = await this.client.get(`/policies/${policyId}/versions/${versionNumber}`)
    return response.data
  }

  async updatePolicyState(policyId: string, newState: string, reason: string, userId: string) {
    const response = await this.client.put(`/policies/${policyId}/state`, {
      new_state: newState,
      reason,
      user_id: userId,
    })
    return response.data
  }

  async getPolicyAssumptions(policyId: string) {
    const response = await this.client.get(`/policies/${policyId}/assumptions`)
    return response.data
  }

  async createAssumption(policyId: string, assumptionData: any) {
    const response = await this.client.post(`/policies/${policyId}/assumptions`, assumptionData)
    return response.data
  }

  async updateAssumption(policyId: string, assumptionId: string, updates: any) {
    const response = await this.client.put(`/policies/${policyId}/assumptions/${assumptionId}`, updates)
    return response.data
  }

  async deleteAssumption(policyId: string, assumptionId: string) {
    await this.client.delete(`/policies/${policyId}/assumptions/${assumptionId}`)
  }

  async getPolicyGuardrails(policyId: string) {
    const response = await this.client.get(`/policies/${policyId}/guardrails`)
    return response.data
  }

  async createGuardrail(policyId: string, guardrailData: any) {
    const response = await this.client.post(`/policies/${policyId}/guardrails`, guardrailData)
    return response.data
  }

  async updateGuardrail(policyId: string, guardrailId: string, updates: any) {
    const response = await this.client.put(`/policies/${policyId}/guardrails/${guardrailId}`, updates)
    return response.data
  }

  async deleteGuardrail(policyId: string, guardrailId: string) {
    await this.client.delete(`/policies/${policyId}/guardrails/${guardrailId}`)
  }

  async checkGuardrails(policyId: string, metrics: Record<string, number>) {
    const response = await this.client.post(`/policies/${policyId}/guardrails/check`, metrics)
    return response.data
  }

  async getPolicyChangelog(policyId: string, limit: number = 100) {
    const response = await this.client.get(`/policies/${policyId}/changelog`, { params: { limit } })
    return response.data
  }

  // Epic 3: Decision Audit & Defensibility API
  async getDecisionsWorkspace(params?: { policy_id?: string; status?: string }) {
    const response = await this.client.get('/decisions', { params })
    return response.data
  }

  async createDecisionWorkspace(decisionData: any) {
    const response = await this.client.post('/decisions', decisionData)
    return response.data
  }

  async getDecisionWorkspace(decisionId: string) {
    const response = await this.client.get(`/decisions/${decisionId}`)
    return response.data
  }

  async updateDecisionWorkspace(decisionId: string, updates: any) {
    const response = await this.client.put(`/decisions/${decisionId}`, updates)
    return response.data
  }

  async finalizeDecision(decisionId: string) {
    const response = await this.client.post(`/decisions/${decisionId}/finalize`)
    return response.data
  }

  async addDecisionApproval(decisionId: string, approvalData: any) {
    const response = await this.client.post(`/decisions/${decisionId}/approvals`, approvalData)
    return response.data
  }

  async getDecisionAuditTrail(decisionId: string) {
    const response = await this.client.get(`/decisions/${decisionId}/audit-trail`)
    return response.data
  }

  async createAuditEntry(decisionId: string, entryData: any) {
    const response = await this.client.post(`/decisions/${decisionId}/audit-trail`, entryData)
    return response.data
  }

  async getDecisionEvidence(decisionId: string) {
    const response = await this.client.get(`/decisions/${decisionId}/evidence`)
    return response.data
  }

  async linkEvidence(decisionId: string, evidenceLink: any) {
    const response = await this.client.post(`/decisions/${decisionId}/evidence`, evidenceLink)
    return response.data
  }

  async getReproducibilityPack(decisionId: string) {
    const response = await this.client.get(`/decisions/${decisionId}/reproducibility-pack`)
    return response.data
  }

  async getPolicyDecisions(policyId: string) {
    const response = await this.client.get(`/policies/${policyId}/decisions`)
    return response.data
  }

  // Epic 4: Uncertainty & Risk Visualization
  async createForecast(forecastData: any) {
    const response = await this.client.post('/forecasts', forecastData)
    return response.data
  }

  async getForecasts(params?: { metric_name?: string }) {
    const response = await this.client.get('/forecasts', { params })
    return response.data
  }

  async getForecast(forecastId: string) {
    const response = await this.client.get(`/forecasts/${forecastId}`)
    return response.data
  }

  async createScenario(scenarioData: any) {
    const response = await this.client.post('/scenarios', scenarioData)
    return response.data
  }

  async getScenarios(params?: { scenario_name?: string }) {
    const response = await this.client.get('/scenarios', { params })
    return response.data
  }

  async getScenario(scenarioId: string) {
    const response = await this.client.get(`/scenarios/${scenarioId}`)
    return response.data
  }

  async updateScenario(scenarioId: string, updates: any) {
    const response = await this.client.put(`/scenarios/${scenarioId}`, updates)
    return response.data
  }

  async createOrUpdateRiskRegister(riskData: any) {
    const response = await this.client.post('/risks', riskData)
    return response.data
  }

  async getRiskRegisters(params?: { min_risk_score?: number }) {
    const response = await this.client.get('/risks', { params })
    return response.data
  }

  async getRiskRegisterForPolicy(policyId: string) {
    const response = await this.client.get(`/risks/policy/${policyId}`)
    return response.data
  }

  async updateRiskDriver(policyId: string, driverName: string, updates: any) {
    const response = await this.client.put(`/risks/policy/${policyId}/drivers/${driverName}`, updates)
    return response.data
  }

  // Epic 5: Behavioral Signal Detection
  async createBehaviorProfile(profileData: any) {
    const response = await this.client.post('/behavior-profiles', profileData)
    return response.data
  }

  async getBehaviorProfiles(params?: { behavior_type?: string; min_confidence?: number }) {
    const response = await this.client.get('/behavior-profiles', { params })
    return response.data
  }

  async getBehaviorProfile(providerId: string) {
    const response = await this.client.get(`/behavior-profiles/${providerId}`)
    return response.data
  }

  async updateBehaviorProfile(providerId: string, updates: any) {
    const response = await this.client.put(`/behavior-profiles/${providerId}`, updates)
    return response.data
  }

  async createBehaviorCluster(clusterData: any) {
    const response = await this.client.post('/behavior-clusters', clusterData)
    return response.data
  }

  async getBehaviorClusters(params?: { behavior_type?: string }) {
    const response = await this.client.get('/behavior-clusters', { params })
    return response.data
  }

  async getBehaviorCluster(clusterId: string) {
    const response = await this.client.get(`/behavior-clusters/${clusterId}`)
    return response.data
  }

  async createAlertRule(ruleData: any) {
    const response = await this.client.post('/alert-rules', ruleData)
    return response.data
  }

  async getAlertRules(params?: { enabled_only?: boolean }) {
    const response = await this.client.get('/alert-rules', { params })
    return response.data
  }

  async getAlertRule(ruleId: string) {
    const response = await this.client.get(`/alert-rules/${ruleId}`)
    return response.data
  }

  async updateAlertRule(ruleId: string, updates: any) {
    const response = await this.client.put(`/alert-rules/${ruleId}`, updates)
    return response.data
  }

  async createAlertEvent(eventData: any) {
    const response = await this.client.post('/alert-events', eventData)
    return response.data
  }

  async getAlertEvents(params?: { policy_id?: string; provider_id?: string; acknowledged_only?: boolean }) {
    const response = await this.client.get('/alert-events', { params })
    return response.data
  }

  // Epic 6: Collaboration Workflows
  async createComment(commentData: any) {
    const response = await this.client.post('/comments', commentData)
    return response.data
  }

  async getComments(params?: { resource_type?: string; resource_id?: string }) {
    const response = await this.client.get('/comments', { params })
    return response.data
  }

  async getComment(commentId: string) {
    const response = await this.client.get(`/comments/${commentId}`)
    return response.data
  }

  async createTask(taskData: any) {
    const response = await this.client.post('/tasks', taskData)
    return response.data
  }

  async getTasks(params?: { assigned_to?: string; status?: string }) {
    const response = await this.client.get('/tasks', { params })
    return response.data
  }

  async getTask(taskId: string) {
    const response = await this.client.get(`/tasks/${taskId}`)
    return response.data
  }

  async createApprovalRequest(requestData: any) {
    const response = await this.client.post('/approvals', requestData)
    return response.data
  }

  async getApprovalRequests(params?: { resource_id?: string; status?: string }) {
    const response = await this.client.get('/approvals', { params })
    return response.data
  }

  async getApprovalRequest(requestId: string) {
    const response = await this.client.get(`/approvals/${requestId}`)
    return response.data
  }

  async createActivityEvent(eventData: any) {
    const response = await this.client.post('/activity', eventData)
    return response.data
  }

  async getActivityEvents(params?: { resource_type?: string; resource_id?: string; limit?: number }) {
    const response = await this.client.get('/activity', { params })
    return response.data
  }

  // Epic 7: Executive Narrative Layer
  async createNarrative(narrativeData: any) {
    const response = await this.client.post('/narratives', narrativeData)
    return response.data
  }

  async getNarratives(params?: { resource_type?: string; resource_id?: string }) {
    const response = await this.client.get('/narratives', { params })
    return response.data
  }

  async getNarrative(narrativeId: string) {
    const response = await this.client.get(`/narratives/${narrativeId}`)
    return response.data
  }

  async createExportTemplate(templateData: any) {
    const response = await this.client.post('/export-templates', templateData)
    return response.data
  }

  async getExportTemplate(templateType: string) {
    const response = await this.client.get(`/export-templates/${templateType}`)
    return response.data
  }

  async createExportPack(packData: any) {
    const response = await this.client.post('/export-packs', packData)
    return response.data
  }

  async getExportPacks(params?: { resource_id?: string; template_type?: string }) {
    const response = await this.client.get('/export-packs', { params })
    return response.data
  }

  async getExportPack(exportId: string) {
    const response = await this.client.get(`/export-packs/${exportId}`)
    return response.data
  }

  // ==================== Conversational AI ====================
  
  async createConversation(mode: 'DRAFT' | 'EXPLAIN' | 'QUERY', domain?: 'POLICY' | 'DATA' | 'BASELINE' | 'IMPACT' | 'GOVERNANCE', title?: string) {
    const response = await this.client.post('/conversational-ai/conversations', {
      mode,
      domain,
      title
    })
    return response.data
  }

  async listConversations(status?: string, limit: number = 50) {
    const response = await this.client.get('/conversational-ai/conversations', {
      params: { status, limit }
    })
    return response.data
  }

  async getConversation(conversationId: string) {
    const response = await this.client.get(`/conversational-ai/conversations/${conversationId}`)
    return response.data
  }

  async sendMessage(conversationId: string, content: string) {
    const response = await this.client.post(`/conversational-ai/conversations/${conversationId}/messages`, {
      conversation_id: conversationId,
      content
    })
    return response.data
  }

  async submitArtifact(conversationId: string, artifactId: string) {
    const response = await this.client.post(`/conversational-ai/conversations/${conversationId}/artifacts/${artifactId}/submit`)
    return response.data
  }

  async getAuditLogs(limit: number = 100) {
    const response = await this.client.get('/conversational-ai/audit-logs', {
      params: { limit }
    })
    return response.data
  }

  /**
   * Generate claims data for demonstration
   */
  async generateClaimsData(targetDate?: string, memberCount: number = 10000, claimsPerMember: number = 2.5) {
    const response = await this.client.post('/data/generate-claims', {
      target_date: targetDate,
      member_count: memberCount,
      claims_per_member: claimsPerMember,
    })
    return response.data
  }

  /**
   * Generate claims data for yesterday (quick endpoint)
   */
  async generateClaimsDataYesterday(memberCount: number = 10000, claimsPerMember: number = 2.5) {
    const response = await this.client.post('/data/generate-claims/yesterday', null, {
      params: {
        member_count: memberCount,
        claims_per_member: claimsPerMember,
      },
    })
    return response.data
  }
}

// Singleton instance
export const apiClient = new ApiClient()

