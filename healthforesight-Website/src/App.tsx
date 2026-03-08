/**
 * HealthForesight Marketing Website App
 * Standalone marketing site entry point
 */
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import { ErrorBoundary } from './components/ErrorBoundary'
import MarketingLayout from './components/MarketingLayout'
import HomePage from './pages/HomePage'
import PlatformPage from './pages/PlatformPage'
import SolutionsPage from './pages/SolutionsPage'
import HowItWorksPage from './pages/HowItWorksPage'
import WhoItsForPage from './pages/WhoItsForPage'
import InsightsPage from './pages/InsightsPage'
import WhitepaperElasticityPage from './pages/WhitepaperElasticityPage'
import BlogWhyPoliciesBackfirePage from './pages/BlogWhyPoliciesBackfirePage'
import ExecutiveBriefCostOfUncertaintyPage from './pages/ExecutiveBriefCostOfUncertaintyPage'
import CompanyPage from './pages/CompanyPage'
import RequestDemoPage from './pages/RequestDemoPage'
import { healthForesightTheme } from './theme/healthForesightTheme'

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider theme={healthForesightTheme}>
        <CssBaseline />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<MarketingLayout />}>
              <Route index element={<HomePage />} />
              <Route path="platform" element={<PlatformPage />} />
              <Route path="solutions" element={<SolutionsPage />} />
              <Route path="how-it-works" element={<HowItWorksPage />} />
              <Route path="who-its-for" element={<WhoItsForPage />} />
              <Route path="insights" element={<InsightsPage />} />
              <Route path="insights/measuring-elasticity" element={<WhitepaperElasticityPage />} />
              <Route path="insights/why-policies-backfire" element={<BlogWhyPoliciesBackfirePage />} />
              <Route path="insights/cost-of-policy-uncertainty" element={<ExecutiveBriefCostOfUncertaintyPage />} />
              <Route path="company" element={<CompanyPage />} />
              <Route path="request-demo" element={<RequestDemoPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </ThemeProvider>
    </ErrorBoundary>
  )
}

export default App
