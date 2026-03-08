/**
 * Utility to generate placeholder screenshots for tours
 * Creates simple placeholder images until real screenshots are available
 */

export function getScreenshotPath(imageName: string): string {
  // Check if screenshot exists, otherwise use placeholder
  return `/screenshots/tours/${imageName}`
}

export function createScreenshotPlaceholder(
  width: number = 800,
  height: number = 450,
  text: string = 'Screenshot Placeholder'
): string {
  // Create a data URL for a simple placeholder
  // In production, this would check if the actual image exists
  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  const ctx = canvas.getContext('2d')
  
  if (ctx) {
    // Gradient background
    const gradient = ctx.createLinearGradient(0, 0, width, height)
    gradient.addColorStop(0, '#667eea')
    gradient.addColorStop(1, '#764ba2')
    ctx.fillStyle = gradient
    ctx.fillRect(0, 0, width, height)
    
    // Text
    ctx.fillStyle = 'white'
    ctx.font = 'bold 24px Arial'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(text, width / 2, height / 2)
    
    // Icon placeholder
    ctx.font = '48px Arial'
    ctx.fillText('📸', width / 2, height / 2 - 40)
  }
  
  return canvas.toDataURL()
}

export const SCREENSHOT_PLACEHOLDERS: Record<string, { width: number; height: number; text: string }> = {
  'dashboard-overview': { width: 1200, height: 600, text: 'Dashboard Overview' },
  'dashboard-metrics': { width: 1200, height: 400, text: 'Key Metrics Cards' },
  'dashboard-decisions': { width: 1200, height: 500, text: 'Decision Recommendations' },
  'dashboard-cost-trend': { width: 1200, height: 500, text: 'Cost Trend Forecast' },
  'dashboard-risk-register': { width: 1200, height: 500, text: 'Risk Register' },
  'dashboard-policy-performance': { width: 1200, height: 500, text: 'Policy Performance' },
  'policy-catalog-overview': { width: 1200, height: 700, text: 'Policy Catalog' },
  'policy-search-filters': { width: 1200, height: 200, text: 'Search & Filters' },
  'policy-list': { width: 1200, height: 800, text: 'Policy List' },
  'policy-create-options': { width: 800, height: 400, text: 'Create Policy Options' },
  'policy-builder-header': { width: 1200, height: 300, text: 'Policy Builder' },
  'policy-builder-steps': { width: 1200, height: 150, text: 'Builder Steps' },
  'policy-builder-scope': { width: 1200, height: 800, text: 'Scope Configuration' },
  'policy-builder-levers': { width: 1200, height: 600, text: 'Levers Configuration' },
  'workspace-tabs': { width: 1200, height: 100, text: 'Workspace Tabs' },
  'workspace-assumptions': { width: 1200, height: 600, text: 'Assumptions Manager' },
  'workspace-guardrails': { width: 1200, height: 600, text: 'Guardrails Manager' },
  'workspace-versions': { width: 1200, height: 600, text: 'Version Control' },
  'analysis-overview': { width: 1200, height: 300, text: 'Analysis Workspace' },
  'analysis-tabs': { width: 1200, height: 100, text: 'Analysis Tabs' },
  'analysis-results': { width: 1200, height: 700, text: 'Impact Results' },
  'analysis-trust-panel': { width: 400, height: 600, text: 'Trust Panel' },
  'whatif-overview': { width: 1200, height: 300, text: 'What-If Analysis' },
  'whatif-scenario-builder': { width: 1200, height: 700, text: 'Scenario Builder' },
  'whatif-comparison': { width: 1200, height: 800, text: 'Scenario Comparison' },
  'ingestion-dashboard': { width: 1200, height: 600, text: 'Ingestion Dashboard' },
  'ingestion-upload': { width: 800, height: 500, text: 'Upload Interface' },
  'ingestion-history': { width: 1200, height: 700, text: 'Ingestion History' },
}

