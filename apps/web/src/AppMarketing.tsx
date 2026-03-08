/**
 * Marketing Website App
 * Separate app entry point for public-facing marketing site
 */
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import { ErrorBoundary } from './components/ErrorBoundary'
import MarketingLayout from './components/marketing/MarketingLayout'
import HomePage from './pages/marketing/HomePage'
import PlatformPage from './pages/marketing/PlatformPage'
import SolutionsPage from './pages/marketing/SolutionsPage'
import HowItWorksPage from './pages/marketing/HowItWorksPage'
import WhoItsForPage from './pages/marketing/WhoItsForPage'
import InsightsPage from './pages/marketing/InsightsPage'
import WhitepaperElasticityPage from './pages/marketing/WhitepaperElasticityPage'
import BlogWhyPoliciesBackfirePage from './pages/marketing/BlogWhyPoliciesBackfirePage'
import ExecutiveBriefCostOfUncertaintyPage from './pages/marketing/ExecutiveBriefCostOfUncertaintyPage'
import CompanyPage from './pages/marketing/CompanyPage'
import RequestDemoPage from './pages/marketing/RequestDemoPage'
import { healthForesightTheme } from './theme/healthForesightTheme'

function AppMarketing() {
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

export default AppMarketing
