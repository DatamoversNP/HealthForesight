import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import { AuthProvider } from './contexts/AuthContext'
import ApiUnavailableBanner from './components/ApiUnavailableBanner'
import { RoleProvider } from './contexts/RoleContext'
import { TourProvider } from './contexts/TourContext'
import { ErrorBoundary } from './components/ErrorBoundary'
import TourPanel from './components/tour/TourPanel'
import FirstTimeTourHandler from './components/tour/FirstTimeTourHandler'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'
import LoginPage from './pages/LoginPage'
import PolicyCatalogPage from './pages/PolicyCatalogPage'
import PolicyBuilderPage from './pages/PolicyBuilderPage'
import PolicyImportPage from './pages/PolicyImportPage'
import DataSpecificationsPage from './pages/DataSpecificationsPage'
import DataModelViewerPage from './pages/DataModelViewerPage'
import IngestionDashboardPage from './pages/IngestionDashboardPage'
import DataHealthPage from './pages/DataHealthPage'
import AnalysisWorkspacePage from './pages/AnalysisWorkspacePage'
import WhatIfAnalysisPage from './pages/WhatIfAnalysisPage'
import WhatIfScenariosListPage from './pages/WhatIfScenariosListPage'
import ScorecardsPage from './pages/ScorecardsPage'
import ExportsPage from './pages/ExportsPage'
import DecisionsPage from './pages/DecisionsPage'
import LineagePage from './pages/LineagePage'
import DashboardPage from './pages/DashboardPage'
import ExecutiveDashboardPage from './pages/persona/ExecutiveDashboardPage'
import PolicyOwnerDashboardPage from './pages/persona/PolicyOwnerDashboardPage'
import AnalystDashboardPage from './pages/persona/AnalystDashboardPage'
import OpsClinicalDashboardPage from './pages/persona/OpsClinicalDashboardPage'
import PipelinesPage from './pages/PipelinesPage'
import PipelineMonitoringPage from './pages/PipelineMonitoringPage'
import DataQualityDashboardPage from './pages/DataQualityDashboardPage'
import DataExplorerPage from './pages/DataExplorerPage'
import BaselineAnalysisPage from './pages/BaselineAnalysisPage'
import ObservationAnalysisPage from './pages/ObservationAnalysisPage'
import ObservationRunHistoryPage from './pages/ObservationRunHistoryPage'
import PredictedImpactsOverviewPage from './pages/PredictedImpactsOverviewPage'
import SchedulesPage from './pages/SchedulesPage'
import NotificationsPage from './pages/NotificationsPage'
import DashboardCustomizationPage from './pages/DashboardCustomizationPage'
import DocumentationPortalPage from './pages/DocumentationPortalPage'
import CohortsPage from './pages/CohortsPage'
import PolicyWorkspacePage from './pages/PolicyWorkspacePage'
import ProductManualPage from './pages/ProductManualPage'
import QATestingPage from './pages/QATestingPage'
import DatabaseViewerPage from './pages/DatabaseViewerPage'
import ObjectivesHealthPage from './pages/ObjectivesHealthPage'
import PolicyVerdictsPage from './pages/PolicyVerdictsPage'
import PolicyRolloutRecommendationsPage from './pages/PolicyRolloutRecommendationsPage'
import RunWorkflowPage from './pages/RunWorkflowPage'
import AuditLogPage from './pages/AuditLogPage'
import AdminPage from './pages/AdminPage'
import { healthForesightTheme } from './theme/healthForesightTheme'

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider theme={healthForesightTheme}>
        <CssBaseline />
        <BrowserRouter
          future={{
            v7_startTransition: true,
            v7_relativeSplatPath: true,
          }}
        >
          <AuthProvider>
            <ApiUnavailableBanner />
            <RoleProvider>
              <TourProvider>
                <TourPanel />
                <FirstTimeTourHandler />
                <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <Layout />
                  </ProtectedRoute>
                }
              >
                <Route index element={<DashboardPage />} />
                <Route path="dashboard/executive" element={<ExecutiveDashboardPage />} />
                <Route path="dashboard/policy-owner" element={<PolicyOwnerDashboardPage />} />
                <Route path="dashboard/analyst" element={<AnalystDashboardPage />} />
                <Route path="dashboard/ops-clinical" element={<OpsClinicalDashboardPage />} />
                <Route path="dashboard/customize" element={<DashboardCustomizationPage />} />
                <Route path="policies" element={<PolicyCatalogPage />} />
                <Route path="policy-verdicts" element={<PolicyVerdictsPage />} />
                <Route path="policy-rollout-recommendations" element={<PolicyRolloutRecommendationsPage />} />
                <Route path="objectives-health" element={<ObjectivesHealthPage />} />
                <Route path="run-workflow" element={<RunWorkflowPage />} />
                <Route path="audit-log" element={<AuditLogPage />} />
                <Route path="admin" element={<AdminPage />} />
                <Route path="policies/builder" element={<PolicyBuilderPage />} />
                <Route path="policies/builder/:id" element={<PolicyBuilderPage />} />
                <Route path="policies/workspace/:id" element={<PolicyWorkspacePage />} />
                <Route path="policies/import" element={<PolicyImportPage />} />
                    <Route path="data-specifications" element={<DataSpecificationsPage />} />
                    <Route path="data-model" element={<DataModelViewerPage />} />
                    <Route path="ingestions" element={<IngestionDashboardPage />} />
                    <Route path="pipelines" element={<PipelinesPage />} />
                    <Route path="pipeline-monitoring" element={<PipelineMonitoringPage />} />
                    <Route path="data-quality" element={<DataQualityDashboardPage />} />
                    <Route path="data-explorer" element={<DataExplorerPage />} />
                <Route path="data-health" element={<DataHealthPage />} />
                <Route path="analyses" element={<AnalysisWorkspacePage />} />
                    <Route path="baseline-analysis" element={<BaselineAnalysisPage />} />
                    <Route path="observation-analysis" element={<ObservationAnalysisPage />} />
                    <Route path="observation-run-history" element={<ObservationRunHistoryPage />} />
                    <Route path="predicted-impacts" element={<PredictedImpactsOverviewPage />} />
                    <Route path="whatif" element={<WhatIfAnalysisPage />} />
                    <Route path="whatif/scenarios" element={<WhatIfScenariosListPage />} />
                    <Route path="scorecards" element={<ScorecardsPage />} />
                    <Route path="cohorts" element={<CohortsPage />} />
                <Route path="exports" element={<ExportsPage />} />
                <Route path="schedules" element={<SchedulesPage />} />
                <Route path="notifications" element={<NotificationsPage />} />
              <Route path="decisions" element={<DecisionsPage />} />
              <Route path="lineage" element={<LineagePage />} />
              <Route path="documentation" element={<DocumentationPortalPage />} />
              <Route path="product-manual" element={<ProductManualPage />} />
              <Route path="qa-testing" element={<QATestingPage />} />
              <Route path="database-viewer" element={<DatabaseViewerPage />} />
            </Route>
              </Routes>
              </TourProvider>
            </RoleProvider>
          </AuthProvider>
        </BrowserRouter>
      </ThemeProvider>
    </ErrorBoundary>
  )
}

export default App
