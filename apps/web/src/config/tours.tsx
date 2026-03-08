import React from 'react'
import { Step } from 'react-joyride'

// Screenshot helper component
const ScreenshotImage = ({ 
  src, 
  alt, 
  width = '100%', 
  maxWidth = 500 
}: { 
  src: string
  alt: string
  width?: string
  maxWidth?: number
}) => (
  <img 
    src={src} 
    alt={alt}
    style={{ 
      width,
      maxWidth: `${maxWidth}px`,
      height: 'auto',
      marginTop: '12px',
      marginBottom: '8px',
      borderRadius: '8px',
      border: '1px solid #e0e0e0',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      display: 'block',
    }}
    onError={(e) => {
      // Fallback to placeholder if image doesn't exist
      const target = e.target as HTMLImageElement
      target.style.display = 'none'
      const placeholder = document.createElement('div')
      placeholder.style.cssText = `
        width: ${width};
        max-width: ${maxWidth}px;
        height: 200px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 600;
        margin-top: 12px;
        margin-bottom: 8px;
      `
      placeholder.textContent = '📸 Screenshot Placeholder'
      target.parentNode?.insertBefore(placeholder, target)
    }}
  />
)

export interface TourConfig {
  module: string
  steps: Step[]
  title: string
  description: string
}

// Enterprise Dashboard Tour - Comprehensive
export const dashboardTour: TourConfig = {
  module: 'dashboard',
  title: 'Executive Dashboard - Complete Overview',
  description: 'Master the executive dashboard with comprehensive insights into policy performance, risk management, and decision support',
  steps: [
    {
      target: '.dashboard-header',
      content: (
        <div style={{ padding: '20px' }}>
          <h3 style={{ 
            margin: '0 0 12px 0', 
            fontSize: '20px', 
            fontWeight: 600,
            color: '#1a1a1a',
            lineHeight: 1.3
          }}>
            Executive Dashboard Overview
          </h3>
          <p style={{ 
            fontSize: '14px', 
            lineHeight: 1.6,
            color: '#4a4a4a',
            margin: '0 0 16px 0'
          }}>
            Your command center for healthcare policy management. Monitor policy performance, 
            financial impact, and make data-driven decisions with confidence.
          </p>
          <div style={{ 
            background: '#f8f9fa',
            padding: '12px',
            borderRadius: '6px',
            borderLeft: '3px solid #1976d2',
            fontSize: '13px',
            lineHeight: 1.5,
            color: '#555'
          }}>
            <strong style={{ color: '#1976d2', display: 'block', marginBottom: '6px' }}>
              Key Features:
            </strong>
            <ul style={{ margin: '0', paddingLeft: '20px' }}>
              <li>Multi-persona views for different roles</li>
              <li>Real-time policy performance metrics</li>
              <li>Risk assessment and decision support</li>
            </ul>
          </div>
        </div>
      ),
      placement: 'bottom',
      disableBeacon: true,
      disableOverlayClose: false,
    },
    {
      target: '.key-metrics-row',
      content: (
        <div style={{ maxWidth: '500px' }}>
          <h3 style={{ 
            fontSize: '20px',
            fontWeight: 600,
            marginBottom: '12px',
            color: '#2c3e50',
            borderBottom: '2px solid #667eea',
            paddingBottom: '8px'
          }}>
            📊 Key Performance Indicators
          </h3>
          <p style={{ fontSize: '15px', lineHeight: '1.8', marginBottom: '16px' }}>
            These <strong>executive-level metrics</strong> provide instant visibility into your policy portfolio's financial 
            and operational impact. Each metric is calculated using advanced causal inference methods with confidence intervals.
          </p>
          <div style={{ 
            background: '#f8f9fa',
            padding: '14px',
            borderRadius: '6px',
            marginBottom: '12px'
          }}>
            <div style={{ marginBottom: '10px' }}>
              <strong style={{ color: '#667eea' }}>💰 Total Cost Impact:</strong>
              <p style={{ margin: '4px 0', fontSize: '14px' }}>
                Aggregate financial impact across all active policies. Positive values indicate cost increases, 
                negative values show savings. Includes uncertainty ranges.
              </p>
            </div>
            <div style={{ marginBottom: '10px' }}>
              <strong style={{ color: '#667eea' }}>📈 Utilization Change:</strong>
              <p style={{ margin: '4px 0', fontSize: '14px' }}>
                Average percentage change in healthcare utilization. Critical for understanding patient access 
                and care delivery patterns.
              </p>
            </div>
            <div style={{ marginBottom: '10px' }}>
              <strong style={{ color: '#667eea' }}>✅ Active Policies:</strong>
              <p style={{ margin: '4px 0', fontSize: '14px' }}>
                Count of policies currently in production. Track policy lifecycle states (Draft → Proposed → 
                Approved → Active → Monitoring).
              </p>
            </div>
            <div>
              <strong style={{ color: '#667eea' }}>⚠️ Decisions Pending:</strong>
              <p style={{ margin: '4px 0', fontSize: '14px' }}>
                High-priority actions requiring executive attention. Each decision includes audit trail, 
                evidence links, and confidence scores.
              </p>
            </div>
          </div>
          <p style={{ 
            marginTop: '12px', 
            fontSize: '13px', 
            color: '#666',
            padding: '8px',
            background: '#e8f4f8',
            borderRadius: '4px',
            borderLeft: '3px solid #2196F3'
          }}>
            🔍 <strong>Enterprise Feature:</strong> All metrics support drill-down analysis. Click any metric card 
            to view detailed breakdowns by policy, time period, or population segment.
          </p>
        </div>
      ),
      placement: 'bottom',
    },
    {
      target: '.decision-recommendations',
      content: (
        <div style={{ padding: '20px' }}>
          <h3 style={{ 
            margin: '0 0 12px 0', 
            fontSize: '20px', 
            fontWeight: 600,
            color: '#1a1a1a',
            lineHeight: 1.3
          }}>
            Decision Recommendations
          </h3>
          <p style={{ 
            fontSize: '14px', 
            lineHeight: 1.6,
            color: '#4a4a4a',
            margin: '0 0 12px 0'
          }}>
            Our <strong>AI-powered decision support system</strong> analyzes policy performance, risk indicators, 
            and data quality to provide actionable recommendations with full defensibility.
          </p>
          <div style={{ 
            background: '#fff3e0',
            padding: '14px',
            borderRadius: '6px',
            marginBottom: '12px',
            borderLeft: '4px solid #ff9800'
          }}>
            <strong style={{ color: '#e65100' }}>📋 Recommendation Components:</strong>
            <ul style={{ margin: '8px 0 0 20px', padding: 0, fontSize: '14px' }}>
              <li><strong>Priority Level:</strong> Critical, High, Medium (based on risk and impact)</li>
              <li><strong>Confidence Score:</strong> Statistical confidence in the recommendation (0-100%)</li>
              <li><strong>Evidence Links:</strong> Connected analyses, datasets, and baselines</li>
              <li><strong>Audit Trail:</strong> Complete history of decision-making process</li>
              <li><strong>Action Items:</strong> Specific steps to address the recommendation</li>
            </ul>
          </div>
          <div style={{ 
            background: '#f3e5f5',
            padding: '12px',
            borderRadius: '6px',
            marginBottom: '12px'
          }}>
            <strong style={{ color: '#7b1fa2' }}>🏢 Enterprise Value:</strong>
            <p style={{ margin: '6px 0 0 0', fontSize: '14px' }}>
              Every recommendation is <strong>fully defensible</strong> with complete audit trails, evidence 
              documentation, and methodology transparency. Essential for regulatory compliance and stakeholder communication.
            </p>
          </div>
          <p style={{ 
            marginTop: '12px', 
            fontSize: '13px', 
            color: '#666',
            padding: '8px',
            background: '#e8f5e9',
            borderRadius: '4px',
            borderLeft: '3px solid #4caf50'
          }}>
            💼 <strong>Demo Highlight:</strong> Show how recommendations link to policies, include evidence, 
            and provide complete audit trails for regulatory compliance.
          </p>
          <ScreenshotImage 
            src="/screenshots/tours/dashboard-decisions.png" 
            alt="Decision Recommendations Screenshot"
            maxWidth={500}
          />
        </div>
      ),
      placement: 'left',
    },
    {
      target: '.cost-trend-chart',
      content: (
        <div style={{ maxWidth: '500px' }}>
          <h3 style={{ 
            fontSize: '20px',
            fontWeight: 600,
            marginBottom: '12px',
            color: '#2c3e50',
            borderBottom: '2px solid #4caf50',
            paddingBottom: '8px'
          }}>
            📈 Cost Trend Forecast with Uncertainty Bands
          </h3>
          <p style={{ fontSize: '15px', lineHeight: '1.8', marginBottom: '16px' }}>
            Advanced <strong>probabilistic forecasting</strong> with confidence intervals. This visualization 
            combines historical data with forward-looking projections, explicitly showing uncertainty ranges.
          </p>
          <div style={{ 
            background: '#e8f5e9',
            padding: '14px',
            borderRadius: '6px',
            marginBottom: '12px',
            borderLeft: '4px solid #4caf50'
          }}>
            <strong style={{ color: '#2e7d32' }}>📊 Chart Components:</strong>
            <ul style={{ margin: '8px 0 0 20px', padding: 0, fontSize: '14px' }}>
              <li><strong>Historical Data (Green):</strong> Actual observed costs with trend analysis</li>
              <li><strong>Forecast (Purple):</strong> Projected costs based on policy impacts</li>
              <li><strong>Confidence Bands:</strong> P10/P50/P90 percentiles showing uncertainty ranges</li>
              <li><strong>Wider Bands:</strong> Indicate higher uncertainty (less data, more assumptions)</li>
            </ul>
          </div>
          <div style={{ 
            background: '#fff3e0',
            padding: '12px',
            borderRadius: '6px',
            marginBottom: '12px'
          }}>
            <strong style={{ color: '#e65100' }}>🎯 Business Value:</strong>
            <p style={{ margin: '6px 0 0 0', fontSize: '14px' }}>
              Enables <strong>risk-informed decision making</strong> by quantifying uncertainty. CFOs and 
              actuaries can assess forecast reliability and plan for multiple scenarios.
            </p>
          </div>
          <p style={{ 
            marginTop: '12px', 
            fontSize: '13px', 
            color: '#666',
            padding: '8px',
            background: '#e3f2fd',
            borderRadius: '4px',
            borderLeft: '3px solid #2196F3'
          }}>
            📊 <strong>Analytics Insight:</strong> Hover over any point to see detailed metrics including 
            confidence intervals, sample sizes, and underlying assumptions.
          </p>
        </div>
      ),
      placement: 'top',
    },
    {
      target: '.risk-register',
      content: (
        <div style={{ maxWidth: '500px' }}>
          <h3 style={{ 
            fontSize: '20px',
            fontWeight: 600,
            marginBottom: '12px',
            color: '#2c3e50',
            borderBottom: '2px solid #ff9800',
            paddingBottom: '8px'
          }}>
            ⚠️ Risk Register & Uncertainty Drivers
          </h3>
          <p style={{ fontSize: '15px', lineHeight: '1.8', marginBottom: '16px' }}>
            Comprehensive <strong>risk management framework</strong> identifying top uncertainty drivers that 
            could impact policy outcomes. Each risk includes severity assessment and mitigation strategies.
          </p>
          <div style={{ 
            background: '#fff3e0',
            padding: '14px',
            borderRadius: '6px',
            marginBottom: '12px',
            borderLeft: '4px solid #ff9800'
          }}>
            <strong style={{ color: '#e65100' }}>🔍 Risk Assessment Framework:</strong>
            <ul style={{ margin: '8px 0 0 20px', padding: 0, fontSize: '14px' }}>
              <li><strong>Severity Levels:</strong> HIGH (immediate action), MEDIUM (monitor closely), LOW (track)</li>
              <li><strong>Risk Drivers:</strong> Policy assumptions, data availability, model uncertainty, external factors</li>
              <li><strong>Mitigation Strategies:</strong> Specific actions to reduce risk exposure</li>
              <li><strong>Impact Analysis:</strong> Quantified potential impact on outcomes</li>
            </ul>
          </div>
          <div style={{ 
            background: '#fce4ec',
            padding: '12px',
            borderRadius: '6px',
            marginBottom: '12px'
          }}>
            <strong style={{ color: '#c2185b' }}>🛡️ Enterprise Risk Management:</strong>
            <p style={{ margin: '6px 0 0 0', fontSize: '14px' }}>
              Supports <strong>regulatory compliance</strong> and <strong>governance requirements</strong> by 
              documenting all identified risks with mitigation plans. Essential for audit trails and stakeholder reporting.
            </p>
          </div>
          <p style={{ 
            marginTop: '12px', 
            fontSize: '13px', 
            color: '#666',
            padding: '8px',
            background: '#fff9e6',
            borderRadius: '4px',
            borderLeft: '3px solid #ffc107'
          }}>
            🎯 <strong>Strategic Use:</strong> Use risk register to prioritize policy reviews, allocate resources, 
            and communicate uncertainty to executive leadership and board members.
          </p>
          <ScreenshotImage 
            src="/screenshots/tours/dashboard-risk-register.png" 
            alt="Risk Register Screenshot"
            maxWidth={500}
          />
        </div>
      ),
      placement: 'left',
    },
    {
      target: '.top-policies-chart',
      content: (
        <div style={{ maxWidth: '500px' }}>
          <h3 style={{ 
            fontSize: '20px',
            fontWeight: 600,
            marginBottom: '12px',
            color: '#2c3e50',
            borderBottom: '2px solid #9c27b0',
            paddingBottom: '8px'
          }}>
            🏆 Top Policy Performance Analysis
          </h3>
          <p style={{ fontSize: '15px', lineHeight: '1.8', marginBottom: '16px' }}>
            <strong>Performance benchmarking</strong> across your policy portfolio. Identify high-performing 
            policies for scaling and underperformers requiring intervention.
          </p>
          <div style={{ 
            background: '#f3e5f5',
            padding: '14px',
            borderRadius: '6px',
            marginBottom: '12px',
            borderLeft: '4px solid #9c27b0'
          }}>
            <strong style={{ color: '#7b1fa2' }}>📊 Analysis Features:</strong>
            <ul style={{ margin: '8px 0 0 20px', padding: 0, fontSize: '14px' }}>
              <li><strong>Cost Impact Ranking:</strong> Policies sorted by financial impact magnitude</li>
              <li><strong>Utilization Metrics:</strong> Percentage changes in healthcare utilization</li>
              <li><strong>Data Quality Indicators:</strong> Observed vs. predicted data flags</li>
              <li><strong>Confidence Scores:</strong> Statistical reliability of each measurement</li>
              <li><strong>Trend Analysis:</strong> Performance over time with variance tracking</li>
            </ul>
          </div>
          <div style={{ 
            background: '#e8f5e9',
            padding: '12px',
            borderRadius: '6px',
            marginBottom: '12px'
          }}>
            <strong style={{ color: '#2e7d32' }}>💡 Strategic Insights:</strong>
            <p style={{ margin: '6px 0 0 0', fontSize: '14px' }}>
              Use this analysis to <strong>scale successful policies</strong>, identify best practices, 
              and make data-driven decisions about policy expansion or modification.
            </p>
          </div>
          <p style={{ 
            marginTop: '12px', 
            fontSize: '13px', 
            color: '#666',
            padding: '8px',
            background: '#e1f5fe',
            borderRadius: '4px',
            borderLeft: '3px solid #03a9f4'
          }}>
            🎬 <strong>Demo Action:</strong> Click on any policy to drill down into detailed performance 
            metrics, view the complete analysis workspace, and explore evidence and audit trails.
          </p>
          <ScreenshotImage 
            src="/screenshots/tours/dashboard-policy-performance.png" 
            alt="Policy Performance Screenshot"
            maxWidth={500}
          />
        </div>
      ),
      placement: 'top',
    },
  ],
}

// Comprehensive Policy Catalog Tour
export const policiesTour: TourConfig = {
  module: 'policies',
  title: 'Policy Catalog - Complete Management System',
  description: 'Master policy lifecycle management, search, filtering, and comprehensive policy operations',
  steps: [
    {
      target: '.policy-catalog-header',
      content: (
        <div style={{ maxWidth: '500px' }}>
          <div style={{ 
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white',
            padding: '20px',
            borderRadius: '8px 8px 0 0',
            margin: '-20px -20px 20px -20px'
          }}>
            <h2 style={{ margin: 0, fontSize: '24px', fontWeight: 600 }}>📋 Policy Catalog</h2>
            <p style={{ margin: '8px 0 0 0', opacity: 0.9, fontSize: '14px' }}>
              Centralized Policy Management & Lifecycle Control
            </p>
          </div>
          <div style={{ lineHeight: '1.8' }}>
            <p style={{ fontSize: '15px', marginBottom: '12px' }}>
              The <strong>Policy Catalog</strong> is your central command center for managing your entire 
              healthcare policy portfolio. From creation to retirement, track every policy through its complete lifecycle.
            </p>
            <div style={{ 
              background: '#f5f7fa',
              padding: '12px',
              borderRadius: '6px',
              marginTop: '12px',
              borderLeft: '4px solid #667eea'
            }}>
              <strong style={{ color: '#667eea' }}>🎯 Enterprise Capabilities:</strong>
              <ul style={{ margin: '8px 0 0 20px', padding: 0 }}>
                <li>Complete policy lifecycle management (Draft → Active → Monitoring → Sunset)</li>
                <li>Advanced search and filtering across all policy attributes</li>
                <li>Bulk operations for policy management</li>
                <li>Version control and change tracking</li>
                <li>Performance metrics and impact analysis</li>
              </ul>
            </div>
            <p style={{ 
              marginTop: '12px', 
              fontSize: '13px', 
              color: '#666',
              fontStyle: 'italic',
              padding: '8px',
              background: '#fff9e6',
              borderRadius: '4px'
            }}>
            💡 <strong>Workflow:</strong> Create policies → Configure scope and levers → Set assumptions and guardrails → 
            Activate and monitor → Iterate based on performance.
            </p>
            <ScreenshotImage 
              src="/screenshots/tours/policy-catalog-overview.png" 
              alt="Policy Catalog Overview Screenshot"
              maxWidth={500}
            />
          </div>
        </div>
      ),
      placement: 'bottom',
      disableBeacon: true,
    },
    {
      target: '.policy-search-filters',
      content: (
        <div style={{ maxWidth: '500px' }}>
          <h3 style={{ 
            fontSize: '20px',
            fontWeight: 600,
            marginBottom: '12px',
            color: '#2c3e50',
            borderBottom: '2px solid #2196F3',
            paddingBottom: '8px'
          }}>
            🔍 Advanced Search & Filtering
          </h3>
          <p style={{ fontSize: '15px', lineHeight: '1.8', marginBottom: '16px' }}>
            <strong>Enterprise-grade search and filtering</strong> capabilities to quickly locate and manage 
            policies across your entire portfolio. Supports complex queries and multi-criteria filtering.
          </p>
          <div style={{ 
            background: '#e3f2fd',
            padding: '14px',
            borderRadius: '6px',
            marginBottom: '12px',
            borderLeft: '4px solid #2196F3'
          }}>
            <strong style={{ color: '#1565c0' }}>🔎 Search Capabilities:</strong>
            <ul style={{ margin: '8px 0 0 20px', padding: 0, fontSize: '14px' }}>
              <li><strong>Full-text Search:</strong> Search by policy name, ID, description, or tags</li>
              <li><strong>Status Filtering:</strong> Filter by lifecycle state (Draft, Active, Monitoring, etc.)</li>
              <li><strong>Type Filtering:</strong> Filter by policy type (Prior Auth, Site of Care, Coverage, etc.)</li>
              <li><strong>Date Range:</strong> Filter by creation date, last modified, or activation date</li>
              <li><strong>Performance Filters:</strong> Filter by cost impact, utilization change, or confidence scores</li>
              <li><strong>Owner Filtering:</strong> Filter by policy owner or assigned team</li>
            </ul>
          </div>
          <div style={{ 
            background: '#fff3e0',
            padding: '12px',
            borderRadius: '6px',
            marginBottom: '12px'
          }}>
            <strong style={{ color: '#e65100' }}>⚡ Quick Actions:</strong>
            <p style={{ margin: '6px 0 0 0', fontSize: '14px' }}>
              Use filters to create <strong>custom views</strong> for different stakeholders. Save filter 
              combinations as bookmarks for quick access to frequently used policy sets.
            </p>
          </div>
          <p style={{ 
            marginTop: '12px', 
            fontSize: '13px', 
            color: '#666',
            padding: '8px',
            background: '#f3e5f5',
            borderRadius: '4px',
            borderLeft: '3px solid #9c27b0'
          }}>
            🎯 <strong>Demo Tip:</strong> Show how to quickly find policies by status, filter by performance 
            metrics, and use saved filter sets for different use cases.
          </p>
        </div>
      ),
      placement: 'bottom',
    },
    {
      target: '.policy-list',
      content: (
        <div style={{ maxWidth: '500px' }}>
          <h3 style={{ 
            fontSize: '20px',
            fontWeight: 600,
            marginBottom: '12px',
            color: '#2c3e50',
            borderBottom: '2px solid #4caf50',
            paddingBottom: '8px'
          }}>
            📊 Policy List & Performance Overview
          </h3>
          <p style={{ fontSize: '15px', lineHeight: '1.8', marginBottom: '16px' }}>
            Comprehensive <strong>policy inventory</strong> with real-time performance metrics, status indicators, 
            and quick access to detailed policy workspaces.
          </p>
          <div style={{ 
            background: '#e8f5e9',
            padding: '14px',
            borderRadius: '6px',
            marginBottom: '12px',
            borderLeft: '4px solid #4caf50'
          }}>
            <strong style={{ color: '#2e7d32' }}>📋 Policy Card Information:</strong>
            <ul style={{ margin: '8px 0 0 20px', padding: 0, fontSize: '14px' }}>
              <li><strong>Policy Name & ID:</strong> Unique identifier and descriptive name</li>
              <li><strong>Lifecycle Status:</strong> Current state with color-coded indicators</li>
              <li><strong>Policy Type:</strong> Classification (Prior Auth, Site of Care, etc.)</li>
              <li><strong>Performance Metrics:</strong> Cost impact, utilization change, confidence scores</li>
              <li><strong>Last Updated:</strong> Timestamp of most recent modification</li>
              <li><strong>Owner Information:</strong> Assigned policy owner and team</li>
            </ul>
          </div>
          <div style={{ 
            background: '#fff3e0',
            padding: '12px',
            borderRadius: '6px',
            marginBottom: '12px'
          }}>
            <strong style={{ color: '#e65100' }}>🎯 Quick Actions Available:</strong>
            <ul style={{ margin: '6px 0 0 20px', padding: 0, fontSize: '14px' }}>
              <li><strong>View:</strong> Open comprehensive Policy Workspace</li>
              <li><strong>Edit:</strong> Modify policy configuration</li>
              <li><strong>Duplicate:</strong> Create new policy from existing</li>
              <li><strong>Export:</strong> Download policy definition and metrics</li>
              <li><strong>Archive:</strong> Move to inactive status</li>
            </ul>
          </div>
          <p style={{ 
            marginTop: '12px', 
            fontSize: '13px', 
            color: '#666',
            padding: '8px',
            background: '#e1f5fe',
            borderRadius: '4px',
            borderLeft: '3px solid #03a9f4'
          }}>
            💼 <strong>Enterprise Feature:</strong> Bulk operations allow you to activate, deactivate, or 
            export multiple policies simultaneously. Essential for large-scale policy management.
          </p>
        </div>
      ),
      placement: 'top',
    },
    {
      target: '.create-policy-button',
      content: (
        <div style={{ maxWidth: '500px' }}>
          <h3 style={{ 
            fontSize: '20px',
            fontWeight: 600,
            marginBottom: '12px',
            color: '#2c3e50',
            borderBottom: '2px solid #ff9800',
            paddingBottom: '8px'
          }}>
            ➕ Create New Policy
          </h3>
          <p style={{ fontSize: '15px', lineHeight: '1.8', marginBottom: '16px' }}>
            Start building a new healthcare policy using our <strong>guided Policy Builder</strong>. 
            Create policies from scratch, import from templates, or duplicate existing policies.
          </p>
          <div style={{ 
            background: '#fff3e0',
            padding: '14px',
            borderRadius: '6px',
            marginBottom: '12px',
            borderLeft: '4px solid #ff9800'
          }}>
            <strong style={{ color: '#e65100' }}>🚀 Creation Options:</strong>
            <ul style={{ margin: '8px 0 0 20px', padding: 0, fontSize: '14px' }}>
              <li><strong>Quick Create:</strong> Fast entry form for simple policies</li>
              <li><strong>Policy Builder:</strong> Step-by-step wizard with validation</li>
              <li><strong>Import Policy:</strong> Upload policy definitions from external systems</li>
              <li><strong>Template Library:</strong> Start from pre-configured templates</li>
              <li><strong>Duplicate Existing:</strong> Copy and modify existing policies</li>
            </ul>
          </div>
          <div style={{ 
            background: '#f3e5f5',
            padding: '12px',
            borderRadius: '6px',
            marginBottom: '12px'
          }}>
            <strong style={{ color: '#7b1fa2' }}>📋 Policy Builder Workflow:</strong>
            <ol style={{ margin: '6px 0 0 20px', padding: 0, fontSize: '14px' }}>
              <li>Define policy overview and metadata</li>
              <li>Configure target scope (populations, regions, timeframes)</li>
              <li>Set policy levers (cost-sharing, prior auth, etc.)</li>
              <li>Document assumptions and guardrails</li>
              <li>Review and activate</li>
            </ol>
          </div>
          <p style={{ 
            marginTop: '12px', 
            fontSize: '13px', 
            color: '#666',
            padding: '8px',
            background: '#e8f5e9',
            borderRadius: '4px',
            borderLeft: '3px solid #4caf50'
          }}>
            🎬 <strong>Demo Flow:</strong> Show the complete policy creation workflow from initial setup 
            through activation, highlighting validation, assumptions documentation, and guardrail configuration.
          </p>
        </div>
      ),
      placement: 'left',
    },
  ],
}

// Comprehensive Policy Workspace Tour
export const policyWorkspaceTour: TourConfig = {
  module: 'policy-workspace',
  title: 'Policy Workspace - Complete Feature Tour',
  description: 'Explore all advanced features: lifecycle management, assumptions, guardrails, decisions, evidence, forecasts, risks, and collaboration',
  steps: [
    {
      target: '.workspace-tabs',
      content: (
        <div style={{ maxWidth: '550px' }}>
          <div style={{ 
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white',
            padding: '20px',
            borderRadius: '8px 8px 0 0',
            margin: '-20px -20px 20px -20px'
          }}>
            <h2 style={{ margin: 0, fontSize: '24px', fontWeight: 600 }}>🏢 Policy Workspace</h2>
            <p style={{ margin: '8px 0 0 0', opacity: 0.9, fontSize: '14px' }}>
              Comprehensive Policy Management & Analysis Platform
            </p>
          </div>
          <div style={{ lineHeight: '1.8' }}>
            <p style={{ fontSize: '15px', marginBottom: '12px' }}>
              The <strong>Policy Workspace</strong> provides a complete suite of tools for managing every 
              aspect of your healthcare policies. Navigate through specialized tabs to access advanced features.
            </p>
            <div style={{ 
              background: '#f5f7fa',
              padding: '14px',
              borderRadius: '6px',
              marginTop: '12px',
              borderLeft: '4px solid #667eea'
            }}>
              <strong style={{ color: '#667eea' }}>📑 Workspace Tabs Overview:</strong>
              <div style={{ marginTop: '10px', fontSize: '14px' }}>
                <div style={{ marginBottom: '8px' }}>
                  <strong>📊 Overview:</strong> Policy summary, metrics, and quick actions
                </div>
                <div style={{ marginBottom: '8px' }}>
                  <strong>🎯 Scope:</strong> Target populations, regions, and service categories
                </div>
                <div style={{ marginBottom: '8px' }}>
                  <strong>⚙️ Levers:</strong> Policy parameters and configuration settings
                </div>
                <div style={{ marginBottom: '8px' }}>
                  <strong>📝 Assumptions:</strong> Key assumptions documentation and validation
                </div>
                <div style={{ marginBottom: '8px' }}>
                  <strong>🛡️ Guardrails:</strong> Safety limits and automatic triggers
                </div>
                <div style={{ marginBottom: '8px' }}>
                  <strong>📈 Monitoring:</strong> Real-time performance tracking
                </div>
                <div style={{ marginBottom: '8px' }}>
                  <strong>📚 Versions:</strong> Complete version history and comparisons
                </div>
                <div style={{ marginBottom: '8px' }}>
                  <strong>📋 Changelog:</strong> Detailed change tracking and audit trail
                </div>
                <div style={{ marginBottom: '8px' }}>
                  <strong>⚖️ Decisions:</strong> Decision records and recommendations
                </div>
                <div style={{ marginBottom: '8px' }}>
                  <strong>🔗 Evidence:</strong> Link analyses, datasets, and baselines
                </div>
                <div style={{ marginBottom: '8px' }}>
                  <strong>📊 Forecasts:</strong> Uncertainty quantification and projections
                </div>
                <div style={{ marginBottom: '8px' }}>
                  <strong>🎲 Scenarios:</strong> What-if analysis and sensitivity testing
                </div>
                <div style={{ marginBottom: '8px' }}>
                  <strong>⚠️ Risk Register:</strong> Risk drivers and mitigation strategies
                </div>
                <div style={{ marginBottom: '8px' }}>
                  <strong>👥 Behavior:</strong> Provider/patient adaptation detection
                </div>
                <div style={{ marginBottom: '8px' }}>
                  <strong>🔔 Alerts:</strong> Automated monitoring and notifications
                </div>
                <div style={{ marginBottom: '8px' }}>
                  <strong>💬 Comments:</strong> Team collaboration and discussions
                </div>
                <div style={{ marginBottom: '8px' }}>
                  <strong>✅ Tasks:</strong> Action items and workflow management
                </div>
                <div style={{ marginBottom: '8px' }}>
                  <strong>📜 Activity:</strong> Complete activity feed and audit log
                </div>
                <div>
                  <strong>📄 Narrative:</strong> Executive summaries and export packs
                </div>
              </div>
            </div>
            <p style={{ 
              marginTop: '12px', 
              fontSize: '13px', 
              color: '#666',
              fontStyle: 'italic',
              padding: '8px',
              background: '#fff9e6',
              borderRadius: '4px'
            }}>
              💡 <strong>Navigation Tip:</strong> Use the scrollable tabs to access all features. Each tab 
              provides specialized tools for different aspects of policy management.
            </p>
          </div>
        </div>
      ),
      placement: 'bottom',
      disableBeacon: true,
    },
    {
      target: '.assumptions-manager',
      content: (
        <div style={{ maxWidth: '500px' }}>
          <h3 style={{ 
            fontSize: '20px',
            fontWeight: 600,
            marginBottom: '12px',
            color: '#2c3e50',
            borderBottom: '2px solid #2196F3',
            paddingBottom: '8px'
          }}>
            📝 Assumptions Manager
          </h3>
          <p style={{ fontSize: '15px', lineHeight: '1.8', marginBottom: '16px' }}>
            <strong>Document and validate key assumptions</strong> that underpin your policy decisions. 
            Essential for defensibility, reproducibility, and stakeholder communication.
          </p>
          <div style={{ 
            background: '#e3f2fd',
            padding: '14px',
            borderRadius: '6px',
            marginBottom: '12px',
            borderLeft: '4px solid #2196F3'
          }}>
            <strong style={{ color: '#1565c0' }}>📋 Assumption Components:</strong>
            <ul style={{ margin: '8px 0 0 20px', padding: 0, fontSize: '14px' }}>
              <li><strong>Description:</strong> Clear statement of the assumption</li>
              <li><strong>Rationale:</strong> Why this assumption is made</li>
              <li><strong>Evidence:</strong> Supporting data or research</li>
              <li><strong>Impact:</strong> How assumption affects policy outcomes</li>
              <li><strong>Validation Status:</strong> Whether assumption has been tested</li>
              <li><strong>Risk Level:</strong> Impact if assumption proves incorrect</li>
            </ul>
          </div>
          <div style={{ 
            background: '#fff3e0',
            padding: '12px',
            borderRadius: '6px',
            marginBottom: '12px'
          }}>
            <strong style={{ color: '#e65100' }}>🏢 Enterprise Value:</strong>
            <p style={{ margin: '6px 0 0 0', fontSize: '14px' }}>
              Assumptions documentation is <strong>critical for regulatory compliance</strong> and audit 
              trails. Provides transparency and enables stakeholders to understand decision rationale.
            </p>
          </div>
          <p style={{ 
            marginTop: '12px', 
            fontSize: '13px', 
            color: '#666',
            padding: '8px',
            background: '#e8f5e9',
            borderRadius: '4px',
            borderLeft: '3px solid #4caf50'
          }}>
            🎯 <strong>Best Practice:</strong> Document assumptions before policy activation. Review and 
            update assumptions regularly as new data becomes available.
          </p>
        </div>
      ),
      placement: 'top',
    },
    {
      target: '.guardrails-manager',
      content: (
        <div style={{ maxWidth: '500px' }}>
          <h3 style={{ 
            fontSize: '20px',
            fontWeight: 600,
            marginBottom: '12px',
            color: '#2c3e50',
            borderBottom: '2px solid #f44336',
            paddingBottom: '8px'
          }}>
            🛡️ Guardrails Manager
          </h3>
          <p style={{ fontSize: '15px', lineHeight: '1.8', marginBottom: '16px' }}>
            Define <strong>safety limits and automatic triggers</strong> to protect against unintended 
            policy consequences. Guardrails automatically pause or modify policies when thresholds are exceeded.
          </p>
          <div style={{ 
            background: '#ffebee',
            padding: '14px',
            borderRadius: '6px',
            marginBottom: '12px',
            borderLeft: '4px solid #f44336'
          }}>
            <strong style={{ color: '#c62828' }}>⚙️ Guardrail Types:</strong>
            <ul style={{ margin: '8px 0 0 20px', padding: 0, fontSize: '14px' }}>
              <li><strong>Cost Limits:</strong> Maximum acceptable cost impact thresholds</li>
              <li><strong>Utilization Limits:</strong> Bounds on utilization changes</li>
              <li><strong>Access Protection:</strong> Minimum access guarantees</li>
              <li><strong>Quality Metrics:</strong> Minimum quality score requirements</li>
              <li><strong>Data Quality:</strong> Minimum data coverage thresholds</li>
              <li><strong>Confidence Thresholds:</strong> Minimum statistical confidence levels</li>
            </ul>
          </div>
          <div style={{ 
            background: '#fff3e0',
            padding: '12px',
            borderRadius: '6px',
            marginBottom: '12px'
          }}>
            <strong style={{ color: '#e65100' }}>🔄 Automatic Actions:</strong>
            <p style={{ margin: '6px 0 0 0', fontSize: '14px' }}>
              When guardrails are triggered, the system can <strong>automatically pause policies</strong>, 
              send alerts, or escalate to policy owners. Prevents adverse outcomes before they occur.
            </p>
          </div>
          <p style={{ 
            marginTop: '12px', 
            fontSize: '13px', 
            color: '#666',
            padding: '8px',
            background: '#fce4ec',
            borderRadius: '4px',
            borderLeft: '3px solid #e91e63'
          }}>
            🎯 <strong>Risk Management:</strong> Guardrails provide proactive risk management, ensuring 
            policies operate within acceptable parameters and protecting patient access and quality of care.
          </p>
        </div>
      ),
      placement: 'top',
    },
    {
      target: '.versions-list',
      content: (
        <div style={{ maxWidth: '500px' }}>
          <h3 style={{ 
            fontSize: '20px',
            fontWeight: 600,
            marginBottom: '12px',
            color: '#2c3e50',
            borderBottom: '2px solid #9c27b0',
            paddingBottom: '8px'
          }}>
            📚 Policy Version Control
          </h3>
          <p style={{ fontSize: '15px', lineHeight: '1.8', marginBottom: '16px' }}>
            Complete <strong>version history and change tracking</strong> for every policy modification. 
            Maintain full audit trail and enable rollback to previous versions.
          </p>
          <div style={{ 
            background: '#f3e5f5',
            padding: '14px',
            borderRadius: '6px',
            marginBottom: '12px',
            borderLeft: '4px solid #9c27b0'
          }}>
            <strong style={{ color: '#7b1fa2' }}>📋 Version Management Features:</strong>
            <ul style={{ margin: '8px 0 0 20px', padding: 0, fontSize: '14px' }}>
              <li><strong>Version History:</strong> Complete record of all policy versions</li>
              <li><strong>Change Tracking:</strong> Detailed diff of what changed between versions</li>
              <li><strong>Rollback Capability:</strong> Restore previous versions if needed</li>
              <li><strong>Version Comparison:</strong> Side-by-side comparison of versions</li>
              <li><strong>Change Attribution:</strong> Who made changes and when</li>
              <li><strong>Approval Workflow:</strong> Version approval and activation process</li>
            </ul>
          </div>
          <div style={{ 
            background: '#e8f5e9',
            padding: '12px',
            borderRadius: '6px',
            marginBottom: '12px'
          }}>
            <strong style={{ color: '#2e7d32' }}>🏢 Compliance & Governance:</strong>
            <p style={{ margin: '6px 0 0 0', fontSize: '14px' }}>
              Version control ensures <strong>complete auditability</strong> and supports regulatory 
              compliance requirements. Essential for demonstrating policy evolution and decision-making processes.
            </p>
          </div>
          <p style={{ 
            marginTop: '12px', 
            fontSize: '13px', 
            color: '#666',
            padding: '8px',
            background: '#e1f5fe',
            borderRadius: '4px',
            borderLeft: '3px solid #03a9f4'
          }}>
            🔄 <strong>Workflow:</strong> Create new version → Document changes → Review and approve → 
            Activate version → Monitor performance → Iterate as needed.
          </p>
        </div>
      ),
      placement: 'top',
    },
  ],
}

// Comprehensive Analysis Workspace Tour
export const analysisWorkspaceTour: TourConfig = {
  module: 'analysis-workspace',
  title: 'Analysis Workspace - Advanced Analytics',
  description: 'Master causal inference analysis, method validation, substitution detection, and provider segmentation',
  steps: [
    {
      target: '.analysis-header',
      content: (
        <div style={{ maxWidth: '500px' }}>
          <div style={{ 
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white',
            padding: '20px',
            borderRadius: '8px 8px 0 0',
            margin: '-20px -20px 20px -20px'
          }}>
            <h2 style={{ margin: 0, fontSize: '24px', fontWeight: 600 }}>🔬 Analysis Workspace</h2>
            <p style={{ margin: '8px 0 0 0', opacity: 0.9, fontSize: '14px' }}>
              Advanced Causal Inference & Impact Analysis Platform
            </p>
          </div>
          <div style={{ lineHeight: '1.8' }}>
            <p style={{ fontSize: '15px', marginBottom: '12px' }}>
              The <strong>Analysis Workspace</strong> provides enterprise-grade causal inference analytics 
              to measure policy impacts with statistical rigor. Every analysis includes method validation, 
              confidence scoring, and uncertainty quantification.
            </p>
            <div style={{ 
              background: '#f5f7fa',
              padding: '12px',
              borderRadius: '6px',
              marginTop: '12px',
              borderLeft: '4px solid #667eea'
            }}>
              <strong style={{ color: '#667eea' }}>🎯 Analysis Capabilities:</strong>
              <ul style={{ margin: '8px 0 0 20px', padding: 0 }}>
                <li>Causal inference using Difference-in-Differences (DiD) methodology</li>
                <li>Method validation and robustness checks</li>
                <li>Substitution detection (provider/patient adaptation)</li>
                <li>Provider segmentation and behavioral analysis</li>
                <li>Confidence intervals and statistical significance testing</li>
              </ul>
            </div>
            <p style={{ 
              marginTop: '12px', 
              fontSize: '13px', 
              color: '#666',
              fontStyle: 'italic',
              padding: '8px',
              background: '#fff9e6',
              borderRadius: '4px'
            }}>
              💡 <strong>Scientific Rigor:</strong> All analyses follow peer-reviewed methodologies with 
              complete transparency in assumptions, methods, and limitations.
            </p>
          </div>
        </div>
      ),
      placement: 'bottom',
      disableBeacon: true,
    },
    {
      target: '.analysis-tabs',
      content: (
        <div style={{ maxWidth: '500px' }}>
          <h3 style={{ 
            fontSize: '20px',
            fontWeight: 600,
            marginBottom: '12px',
            color: '#2c3e50',
            borderBottom: '2px solid #2196F3',
            paddingBottom: '8px'
          }}>
            📊 Analysis Tabs & Workflows
          </h3>
          <p style={{ fontSize: '15px', lineHeight: '1.8', marginBottom: '16px' }}>
            Navigate through specialized analysis views, each providing different insights into policy impacts 
            and underlying mechanisms.
          </p>
          <div style={{ 
            background: '#e3f2fd',
            padding: '14px',
            borderRadius: '6px',
            marginBottom: '12px',
            borderLeft: '4px solid #2196F3'
          }}>
            <strong style={{ color: '#1565c0' }}>📑 Analysis Views:</strong>
            <ul style={{ margin: '8px 0 0 20px', padding: 0, fontSize: '14px' }}>
              <li><strong>Results:</strong> Primary impact estimates with confidence intervals</li>
              <li><strong>Method Checks:</strong> Validation of causal inference assumptions</li>
              <li><strong>Substitution:</strong> Detection of provider/patient behavioral adaptation</li>
              <li><strong>Segmentation:</strong> Provider response patterns and clustering</li>
              <li><strong>Trust Panel:</strong> Data quality and result reliability assessment</li>
            </ul>
          </div>
          <div style={{ 
            background: '#fff3e0',
            padding: '12px',
            borderRadius: '6px',
            marginBottom: '12px'
          }}>
            <strong style={{ color: '#e65100' }}>🔬 Scientific Methodology:</strong>
            <p style={{ margin: '6px 0 0 0', fontSize: '14px' }}>
              Each analysis uses <strong>rigorous causal inference methods</strong> (primarily Difference-in-Differences) 
              with comprehensive validation checks to ensure reliable, defensible results.
            </p>
          </div>
          <p style={{ 
            marginTop: '12px', 
            fontSize: '13px', 
            color: '#666',
            padding: '8px',
            background: '#e8f5e9',
            borderRadius: '4px',
            borderLeft: '3px solid #4caf50'
          }}>
            🎯 <strong>Enterprise Standard:</strong> All analyses meet publication-quality standards with 
            complete methodology documentation and assumption validation.
          </p>
        </div>
      ),
      placement: 'bottom',
    },
    {
      target: '.impact-results',
      content: (
        <div style={{ maxWidth: '500px' }}>
          <h3 style={{ 
            fontSize: '20px',
            fontWeight: 600,
            marginBottom: '12px',
            color: '#2c3e50',
            borderBottom: '2px solid #4caf50',
            paddingBottom: '8px'
          }}>
            📈 Impact Results & Metrics
          </h3>
          <p style={{ fontSize: '15px', lineHeight: '1.8', marginBottom: '16px' }}>
            <strong>Primary policy impact estimates</strong> with statistical confidence intervals, 
            significance testing, and comprehensive metrics.
          </p>
          <div style={{ 
            background: '#e8f5e9',
            padding: '14px',
            borderRadius: '6px',
            marginBottom: '12px',
            borderLeft: '4px solid #4caf50'
          }}>
            <strong style={{ color: '#2e7d32' }}>📊 Key Metrics:</strong>
            <ul style={{ margin: '8px 0 0 20px', padding: 0, fontSize: '14px' }}>
              <li><strong>Effect Size:</strong> Magnitude of policy impact</li>
              <li><strong>Confidence Intervals:</strong> 95% CI showing uncertainty range</li>
              <li><strong>P-Value:</strong> Statistical significance testing</li>
              <li><strong>Percent Change:</strong> Relative impact on utilization/costs</li>
              <li><strong>Absolute Impact:</strong> Dollar amounts and utilization counts</li>
              <li><strong>Time Series:</strong> Impact evolution over time</li>
            </ul>
          </div>
          <div style={{ 
            background: '#fff3e0',
            padding: '12px',
            borderRadius: '6px',
            marginBottom: '12px'
          }}>
            <strong style={{ color: '#e65100' }}>🎯 Interpretation Guide:</strong>
            <p style={{ margin: '6px 0 0 0', fontSize: '14px' }}>
              Results include <strong>interpretation guidance</strong> to help stakeholders understand 
              statistical findings in business terms. Confidence intervals show uncertainty ranges.
            </p>
          </div>
          <p style={{ 
            marginTop: '12px', 
            fontSize: '13px', 
            color: '#666',
            padding: '8px',
            background: '#e1f5fe',
            borderRadius: '4px',
            borderLeft: '3px solid #03a9f4'
          }}>
            📊 <strong>Visualization:</strong> Results are presented with clear visualizations including 
            confidence intervals, time series charts, and comparison views.
          </p>
        </div>
      ),
      placement: 'top',
    },
    {
      target: '.trust-panel',
      content: (
        <div style={{ maxWidth: '500px' }}>
          <h3 style={{ 
            fontSize: '20px',
            fontWeight: 600,
            marginBottom: '12px',
            color: '#2c3e50',
            borderBottom: '2px solid #ff9800',
            paddingBottom: '8px'
          }}>
            🛡️ Trust Panel & Result Reliability
          </h3>
          <p style={{ fontSize: '15px', lineHeight: '1.8', marginBottom: '16px' }}>
            Comprehensive <strong>reliability assessment</strong> evaluating data quality, methodology 
            validity, and result confidence. Essential for understanding when results can be trusted.
          </p>
          <div style={{ 
            background: '#fff3e0',
            padding: '14px',
            borderRadius: '6px',
            marginBottom: '12px',
            borderLeft: '4px solid #ff9800'
          }}>
            <strong style={{ color: '#e65100' }}>🔍 Trust Assessment Components:</strong>
            <ul style={{ margin: '8px 0 0 20px', padding: 0, fontSize: '14px' }}>
              <li><strong>Data Quality Score:</strong> Coverage, completeness, and accuracy metrics</li>
              <li><strong>Methodology Validation:</strong> Causal inference assumption checks</li>
              <li><strong>Statistical Power:</strong> Sample size adequacy assessment</li>
              <li><strong>Confounder Analysis:</strong> Potential bias identification</li>
              <li><strong>Robustness Checks:</strong> Sensitivity to assumptions and specifications</li>
              <li><strong>Limitations:</strong> Transparent disclosure of analysis constraints</li>
            </ul>
          </div>
          <div style={{ 
            background: '#f3e5f5',
            padding: '12px',
            borderRadius: '6px',
            marginBottom: '12px'
          }}>
            <strong style={{ color: '#7b1fa2' }}>🏢 Enterprise Transparency:</strong>
            <p style={{ margin: '6px 0 0 0', fontSize: '14px' }}>
              The Trust Panel ensures <strong>complete transparency</strong> about result reliability, 
              enabling informed decision-making and supporting regulatory compliance.
            </p>
          </div>
          <p style={{ 
            marginTop: '12px', 
            fontSize: '13px', 
            color: '#666',
            padding: '8px',
            background: '#e8f5e9',
            borderRadius: '4px',
            borderLeft: '3px solid #4caf50'
          }}>
            🎯 <strong>Decision Support:</strong> Use trust scores to prioritize actions. High-trust results 
            can drive policy decisions, while low-trust results may require additional data collection.
          </p>
        </div>
      ),
      placement: 'left',
    },
  ],
}

// Comprehensive What-If Analysis Tour
export const whatIfTour: TourConfig = {
  module: 'whatif',
  title: 'What-If Analysis - Scenario Planning',
  description: 'Master scenario simulation, sensitivity analysis, and policy alternative comparison',
  steps: [
    {
      target: '.whatif-header',
      content: (
        <div style={{ maxWidth: '500px' }}>
          <div style={{ 
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white',
            padding: '20px',
            borderRadius: '8px 8px 0 0',
            margin: '-20px -20px 20px -20px'
          }}>
            <h2 style={{ margin: 0, fontSize: '24px', fontWeight: 600 }}>🎲 What-If Analysis</h2>
            <p style={{ margin: '8px 0 0 0', opacity: 0.9, fontSize: '14px' }}>
              Scenario Simulation & Policy Alternative Evaluation
            </p>
          </div>
          <div style={{ lineHeight: '1.8' }}>
            <p style={{ fontSize: '15px', marginBottom: '12px' }}>
              <strong>Simulate policy scenarios</strong> before implementation to evaluate potential outcomes, 
              compare alternatives, and make data-driven decisions with full uncertainty quantification.
            </p>
            <div style={{ 
              background: '#f5f7fa',
              padding: '12px',
              borderRadius: '6px',
              marginTop: '12px',
              borderLeft: '4px solid #667eea'
            }}>
              <strong style={{ color: '#667eea' }}>🎯 Scenario Capabilities:</strong>
              <ul style={{ margin: '8px 0 0 20px', padding: 0 }}>
                <li>Adjust policy parameters (levers, scope, assumptions)</li>
                <li>Compare multiple scenarios side-by-side</li>
                <li>Quantify uncertainty with confidence bands</li>
                <li>Assess tradeoffs and risk profiles</li>
                <li>Export scenarios for stakeholder review</li>
              </ul>
            </div>
            <p style={{ 
              marginTop: '12px', 
              fontSize: '13px', 
              color: '#666',
              fontStyle: 'italic',
              padding: '8px',
              background: '#fff9e6',
              borderRadius: '4px'
            }}>
              💡 <strong>Strategic Planning:</strong> Use scenarios to explore policy alternatives, 
              understand sensitivity to assumptions, and prepare for different outcomes.
            </p>
          </div>
        </div>
      ),
      placement: 'bottom',
      disableBeacon: true,
    },
    {
      target: '.scenario-builder',
      content: (
        <div style={{ maxWidth: '500px' }}>
          <h3 style={{ 
            fontSize: '20px',
            fontWeight: 600,
            marginBottom: '12px',
            color: '#2c3e50',
            borderBottom: '2px solid #2196F3',
            paddingBottom: '8px'
          }}>
            🏗️ Scenario Builder
          </h3>
          <p style={{ fontSize: '15px', lineHeight: '1.8', marginBottom: '16px' }}>
            Create custom scenarios by adjusting policy parameters, assumptions, and target populations. 
            Build multiple scenarios to compare alternatives.
          </p>
          <div style={{ 
            background: '#e3f2fd',
            padding: '14px',
            borderRadius: '6px',
            marginBottom: '12px',
            borderLeft: '4px solid #2196F3'
          }}>
            <strong style={{ color: '#1565c0' }}>⚙️ Adjustable Parameters:</strong>
            <ul style={{ margin: '8px 0 0 20px', padding: 0, fontSize: '14px' }}>
              <li><strong>Policy Levers:</strong> Cost-sharing, prior auth, network restrictions</li>
              <li><strong>Target Scope:</strong> Populations, regions, service categories</li>
              <li><strong>Assumptions:</strong> Elasticity, substitution rates, utilization patterns</li>
              <li><strong>Time Horizons:</strong> Short-term vs. long-term projections</li>
              <li><strong>External Factors:</strong> Market conditions, regulatory changes</li>
            </ul>
          </div>
          <div style={{ 
            background: '#fff3e0',
            padding: '12px',
            borderRadius: '6px',
            marginBottom: '12px'
          }}>
            <strong style={{ color: '#e65100' }}>🎯 Use Cases:</strong>
            <p style={{ margin: '6px 0 0 0', fontSize: '14px' }}>
              Explore "what if we increase cost-sharing by 10%?" or "what if we expand to additional 
              populations?" scenarios to inform strategic planning.
            </p>
          </div>
          <p style={{ 
            marginTop: '12px', 
            fontSize: '13px', 
            color: '#666',
            padding: '8px',
            background: '#e8f5e9',
            borderRadius: '4px',
            borderLeft: '3px solid #4caf50'
          }}>
            🔄 <strong>Iterative Design:</strong> Build scenarios incrementally, save drafts, and refine 
            based on initial results before finalizing.
          </p>
        </div>
      ),
      placement: 'top',
    },
    {
      target: '.scenario-comparison',
      content: (
        <div style={{ maxWidth: '500px' }}>
          <h3 style={{ 
            fontSize: '20px',
            fontWeight: 600,
            marginBottom: '12px',
            color: '#2c3e50',
            borderBottom: '2px solid #4caf50',
            paddingBottom: '8px'
          }}>
            📊 Scenario Comparison & Analysis
          </h3>
          <p style={{ fontSize: '15px', lineHeight: '1.8', marginBottom: '16px' }}>
            <strong>Compare multiple scenarios side-by-side</strong> to evaluate tradeoffs, assess 
            risk profiles, and make informed decisions about policy alternatives.
          </p>
          <div style={{ 
            background: '#e8f5e9',
            padding: '14px',
            borderRadius: '6px',
            marginBottom: '12px',
            borderLeft: '4px solid #4caf50'
          }}>
            <strong style={{ color: '#2e7d32' }}>📈 Comparison Features:</strong>
            <ul style={{ margin: '8px 0 0 20px', padding: 0, fontSize: '14px' }}>
              <li><strong>Cost Impact Comparison:</strong> Financial outcomes across scenarios</li>
              <li><strong>Utilization Analysis:</strong> Patient access and care delivery impacts</li>
              <li><strong>Risk Assessment:</strong> Uncertainty ranges and confidence intervals</li>
              <li><strong>Tradeoff Analysis:</strong> Cost vs. access vs. quality tradeoffs</li>
              <li><strong>Visual Comparison:</strong> Charts and graphs for easy comparison</li>
              <li><strong>Export Options:</strong> Generate comparison reports for stakeholders</li>
            </ul>
          </div>
          <div style={{ 
            background: '#fff3e0',
            padding: '12px',
            borderRadius: '6px',
            marginBottom: '12px'
          }}>
            <strong style={{ color: '#e65100' }}>💼 Executive Decision Support:</strong>
            <p style={{ margin: '6px 0 0 0', fontSize: '14px' }}>
              Comparison views enable <strong>data-driven decision making</strong> by clearly showing 
              tradeoffs and outcomes across policy alternatives. Essential for executive and board presentations.
            </p>
          </div>
          <p style={{ 
            marginTop: '12px', 
            fontSize: '13px', 
            color: '#666',
            padding: '8px',
            background: '#e1f5fe',
            borderRadius: '4px',
            borderLeft: '3px solid #03a9f4'
          }}>
            🎬 <strong>Demo Highlight:</strong> Show how to compare scenarios, identify optimal policy 
            configurations, and export comparison reports for stakeholder review.
          </p>
        </div>
      ),
      placement: 'top',
    },
  ],
}

// Comprehensive Data Ingestion Tour
export const ingestionsTour: TourConfig = {
  module: 'ingestions',
  title: 'Data Ingestion - Complete Workflow',
  description: 'Master data upload, validation, pipeline configuration, and ingestion monitoring',
  steps: [
    {
      target: '.ingestion-header',
      content: (
        <div style={{ maxWidth: '500px' }}>
          <div style={{ 
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white',
            padding: '20px',
            borderRadius: '8px 8px 0 0',
            margin: '-20px -20px 20px -20px'
          }}>
            <h2 style={{ margin: 0, fontSize: '24px', fontWeight: 600 }}>📥 Data Ingestion Dashboard</h2>
            <p style={{ margin: '8px 0 0 0', opacity: 0.9, fontSize: '14px' }}>
              Enterprise Data Pipeline Management & Monitoring
            </p>
          </div>
          <div style={{ lineHeight: '1.8' }}>
            <p style={{ fontSize: '15px', marginBottom: '12px' }}>
              The <strong>Data Ingestion Dashboard</strong> provides comprehensive tools for importing, 
              validating, and monitoring healthcare data. Manage your entire data pipeline from upload to analysis.
            </p>
            <div style={{ 
              background: '#f5f7fa',
              padding: '12px',
              borderRadius: '6px',
              marginTop: '12px',
              borderLeft: '4px solid #667eea'
            }}>
              <strong style={{ color: '#667eea' }}>🎯 Ingestion Capabilities:</strong>
              <ul style={{ margin: '8px 0 0 20px', padding: 0 }}>
                <li>Multiple upload methods (file upload, API, scheduled imports)</li>
                <li>Automatic data validation and quality checks</li>
                <li>Schema mapping and transformation</li>
                <li>Pipeline monitoring and error tracking</li>
                <li>Data lineage and traceability</li>
              </ul>
            </div>
            <p style={{ 
              marginTop: '12px', 
              fontSize: '13px', 
              color: '#666',
              fontStyle: 'italic',
              padding: '8px',
              background: '#fff9e6',
              borderRadius: '4px'
            }}>
              💡 <strong>Data Quality:</strong> All ingested data undergoes automatic validation to ensure 
              completeness, accuracy, and compliance with data specifications.
            </p>
          </div>
        </div>
      ),
      placement: 'bottom',
      disableBeacon: true,
    },
    {
      target: '.upload-section',
      content: (
        <div style={{ maxWidth: '500px' }}>
          <h3 style={{ 
            fontSize: '20px',
            fontWeight: 600,
            marginBottom: '12px',
            color: '#2c3e50',
            borderBottom: '2px solid #2196F3',
            paddingBottom: '8px'
          }}>
            📤 Data Upload & Import
          </h3>
          <p style={{ fontSize: '15px', lineHeight: '1.8', marginBottom: '16px' }}>
            Upload healthcare data files or connect to external data sources. Supports multiple formats 
            and automated processing pipelines.
          </p>
          <div style={{ 
            background: '#e3f2fd',
            padding: '14px',
            borderRadius: '6px',
            marginBottom: '12px',
            borderLeft: '4px solid #2196F3'
          }}>
            <strong style={{ color: '#1565c0' }}>📋 Supported Formats:</strong>
            <ul style={{ margin: '8px 0 0 20px', padding: 0, fontSize: '14px' }}>
              <li><strong>CSV Files:</strong> Comma-separated values with schema validation</li>
              <li><strong>JSON Files:</strong> Structured JSON with nested data support</li>
              <li><strong>Database Connections:</strong> Direct connection to SQL databases</li>
              <li><strong>API Integrations:</strong> RESTful API endpoints for automated imports</li>
              <li><strong>Scheduled Imports:</strong> Automated recurring data ingestion</li>
            </ul>
          </div>
          <div style={{ 
            background: '#fff3e0',
            padding: '12px',
            borderRadius: '6px',
            marginBottom: '12px'
          }}>
            <strong style={{ color: '#e65100' }}>🔒 Security & Compliance:</strong>
            <p style={{ margin: '6px 0 0 0', fontSize: '14px' }}>
              All data uploads are <strong>encrypted in transit and at rest</strong>, with complete audit 
              trails for compliance with HIPAA and other regulatory requirements.
            </p>
          </div>
          <p style={{ 
            marginTop: '12px', 
            fontSize: '13px', 
            color: '#666',
            padding: '8px',
            background: '#e8f5e9',
            borderRadius: '4px',
            borderLeft: '3px solid #4caf50'
          }}>
            ✅ <strong>Validation:</strong> Files are automatically validated against data specifications 
            before processing. Errors are flagged with detailed feedback for correction.
          </p>
        </div>
      ),
      placement: 'top',
    },
    {
      target: '.ingestion-list',
      content: (
        <div style={{ maxWidth: '500px' }}>
          <h3 style={{ 
            fontSize: '20px',
            fontWeight: 600,
            marginBottom: '12px',
            color: '#2c3e50',
            borderBottom: '2px solid #4caf50',
            paddingBottom: '8px'
          }}>
            📊 Ingestion History & Monitoring
          </h3>
          <p style={{ fontSize: '15px', lineHeight: '1.8', marginBottom: '16px' }}>
            <strong>Complete ingestion history</strong> with status tracking, error monitoring, and 
            data quality metrics. Monitor pipeline health and troubleshoot issues.
          </p>
          <div style={{ 
            background: '#e8f5e9',
            padding: '14px',
            borderRadius: '6px',
            marginBottom: '12px',
            borderLeft: '4px solid #4caf50'
          }}>
            <strong style={{ color: '#2e7d32' }}>📈 Monitoring Features:</strong>
            <ul style={{ margin: '8px 0 0 20px', padding: 0, fontSize: '14px' }}>
              <li><strong>Status Tracking:</strong> Real-time ingestion status (Pending, Processing, Complete, Failed)</li>
              <li><strong>Error Logging:</strong> Detailed error messages with resolution guidance</li>
              <li><strong>Data Quality Metrics:</strong> Coverage, completeness, and accuracy scores</li>
              <li><strong>Processing Time:</strong> Performance metrics and optimization insights</li>
              <li><strong>Lineage Tracking:</strong> Complete data lineage from source to analysis</li>
              <li><strong>Alert System:</strong> Automated notifications for failures or quality issues</li>
            </ul>
          </div>
          <div style={{ 
            background: '#fff3e0',
            padding: '12px',
            borderRadius: '6px',
            marginBottom: '12px'
          }}>
            <strong style={{ color: '#e65100' }}>🔍 Troubleshooting:</strong>
            <p style={{ margin: '6px 0 0 0', fontSize: '14px' }}>
              Detailed error logs and validation reports help <strong>quickly identify and resolve</strong> 
              data quality issues. Drill down into specific records for detailed inspection.
            </p>
          </div>
          <p style={{ 
            marginTop: '12px', 
            fontSize: '13px', 
            color: '#666',
            padding: '8px',
            background: '#e1f5fe',
            borderRadius: '4px',
            borderLeft: '3px solid #03a9f4'
          }}>
            📊 <strong>Analytics:</strong> Track ingestion trends, identify patterns in data quality, 
            and optimize pipeline performance over time.
          </p>
        </div>
      ),
      placement: 'top',
    },
  ],
}

// Comprehensive Policy Builder Tour
export const policyBuilderTour: TourConfig = {
  module: 'policy-builder',
  title: 'Policy Builder - Step-by-Step Guide',
  description: 'Master the complete policy creation workflow from basic info through activation',
  steps: [
    {
      target: '.policy-builder-header',
      content: (
        <div style={{ maxWidth: '500px' }}>
          <div style={{ 
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white',
            padding: '20px',
            borderRadius: '8px 8px 0 0',
            margin: '-20px -20px 20px -20px'
          }}>
            <h2 style={{ margin: 0, fontSize: '24px', fontWeight: 600 }}>🏗️ Policy Builder</h2>
            <p style={{ margin: '8px 0 0 0', opacity: 0.9, fontSize: '14px' }}>
              Guided Policy Creation Wizard
            </p>
          </div>
          <div style={{ lineHeight: '1.8' }}>
            <p style={{ fontSize: '15px', marginBottom: '12px' }}>
              The <strong>Policy Builder</strong> guides you through creating comprehensive healthcare policies 
              using a step-by-step wizard. Each step includes validation, best practices, and real-time preview.
            </p>
            <div style={{ 
              background: '#f5f7fa',
              padding: '12px',
              borderRadius: '6px',
              marginTop: '12px',
              borderLeft: '4px solid #667eea'
            }}>
              <strong style={{ color: '#667eea' }}>📋 Builder Workflow:</strong>
              <ol style={{ margin: '8px 0 0 20px', padding: 0 }}>
                <li><strong>Basic Info:</strong> Policy name, type, description, and metadata</li>
                <li><strong>Scope:</strong> Target populations, regions, and service categories</li>
                <li><strong>Levers:</strong> Policy parameters (cost-sharing, prior auth, etc.)</li>
                <li><strong>Conditions:</strong> When the policy applies (rule groups)</li>
                <li><strong>Exceptions:</strong> Special cases and overrides</li>
                <li><strong>Review:</strong> Final validation and activation</li>
              </ol>
            </div>
            <p style={{ 
              marginTop: '12px', 
              fontSize: '13px', 
              color: '#666',
              fontStyle: 'italic',
              padding: '8px',
              background: '#fff9e6',
              borderRadius: '4px'
            }}>
              💡 <strong>Best Practice:</strong> Complete each step thoroughly. The builder validates your 
              inputs and provides guidance to ensure policy completeness and correctness.
            </p>
          </div>
        </div>
      ),
      placement: 'bottom',
      disableBeacon: true,
    },
    {
      target: '.builder-steps',
      content: (
        <div style={{ maxWidth: '500px' }}>
          <h3 style={{ 
            fontSize: '20px',
            fontWeight: 600,
            marginBottom: '12px',
            color: '#2c3e50',
            borderBottom: '2px solid #2196F3',
            paddingBottom: '8px'
          }}>
            📍 Step Navigation & Progress
          </h3>
          <p style={{ fontSize: '15px', lineHeight: '1.8', marginBottom: '16px' }}>
            The <strong>stepper component</strong> shows your progress through the policy creation process. 
            Navigate between steps to review and modify your policy configuration.
          </p>
          <div style={{ 
            background: '#e3f2fd',
            padding: '14px',
            borderRadius: '6px',
            marginBottom: '12px',
            borderLeft: '4px solid #2196F3'
          }}>
            <strong style={{ color: '#1565c0' }}>🔄 Step Features:</strong>
            <ul style={{ margin: '8px 0 0 20px', padding: 0, fontSize: '14px' }}>
              <li><strong>Progress Tracking:</strong> Visual indicator of completion status</li>
              <li><strong>Step Validation:</strong> Each step validates before allowing progression</li>
              <li><strong>Save & Resume:</strong> Save drafts and continue later</li>
              <li><strong>Step Navigation:</strong> Jump to any completed step for review</li>
              <li><strong>Error Indicators:</strong> Visual flags for incomplete or invalid steps</li>
            </ul>
          </div>
          <div style={{ 
            background: '#fff3e0',
            padding: '12px',
            borderRadius: '6px',
            marginBottom: '12px'
          }}>
            <strong style={{ color: '#e65100' }}>✅ Validation:</strong>
            <p style={{ margin: '6px 0 0 0', fontSize: '14px' }}>
              Each step includes <strong>real-time validation</strong> to catch errors early. Required fields 
              are clearly marked, and helpful error messages guide corrections.
            </p>
          </div>
          <p style={{ 
            marginTop: '12px', 
            fontSize: '13px', 
            color: '#666',
            padding: '8px',
            background: '#e8f5e9',
            borderRadius: '4px',
            borderLeft: '3px solid #4caf50'
          }}>
            🎯 <strong>Workflow Tip:</strong> Complete steps in order for best results. You can always go 
            back to previous steps to make adjustments before finalizing.
          </p>
        </div>
      ),
      placement: 'right',
    },
    {
      target: '.scope-selector',
      content: (
        <div style={{ maxWidth: '500px' }}>
          <h3 style={{ 
            fontSize: '20px',
            fontWeight: 600,
            marginBottom: '12px',
            color: '#2c3e50',
            borderBottom: '2px solid #4caf50',
            paddingBottom: '8px'
          }}>
            🎯 Policy Scope Configuration
          </h3>
          <p style={{ fontSize: '15px', lineHeight: '1.8', marginBottom: '16px' }}>
            Define <strong>exactly who and what</strong> your policy applies to. Precise scope definition 
            is critical for accurate impact analysis and policy effectiveness.
          </p>
          <div style={{ 
            background: '#e8f5e9',
            padding: '14px',
            borderRadius: '6px',
            marginBottom: '12px',
            borderLeft: '4px solid #4caf50'
          }}>
            <strong style={{ color: '#2e7d32' }}>📋 Scope Dimensions:</strong>
            <ul style={{ margin: '8px 0 0 20px', padding: 0, fontSize: '14px' }}>
              <li><strong>Line of Business:</strong> Commercial, Medicare, Medicaid, etc.</li>
              <li><strong>Geographic Regions:</strong> States, counties, or custom regions</li>
              <li><strong>Network Tiers:</strong> In-network, out-of-network, tiered networks</li>
              <li><strong>Member Demographics:</strong> Age ranges, gender, special populations</li>
              <li><strong>Provider Types:</strong> Specialties, facility types, provider categories</li>
              <li><strong>Service Categories:</strong> Medical, pharmacy, behavioral health, etc.</li>
              <li><strong>Time Periods:</strong> Effective dates and expiration</li>
            </ul>
          </div>
          <div style={{ 
            background: '#fff3e0',
            padding: '12px',
            borderRadius: '6px',
            marginBottom: '12px'
          }}>
            <strong style={{ color: '#e65100' }}>🎯 Best Practice:</strong>
            <p style={{ margin: '6px 0 0 0', fontSize: '14px' }}>
              Be <strong>specific and comprehensive</strong> in scope definition. Overly broad scopes can 
              lead to unintended consequences, while overly narrow scopes may limit policy effectiveness.
            </p>
          </div>
          <p style={{ 
            marginTop: '12px', 
            fontSize: '13px', 
            color: '#666',
            padding: '8px',
            background: '#e1f5fe',
            borderRadius: '4px',
            borderLeft: '3px solid #03a9f4'
          }}>
            📊 <strong>Impact Analysis:</strong> Scope directly affects impact calculations. Use the preview 
            to see estimated population size and coverage before finalizing.
          </p>
        </div>
      ),
      placement: 'top',
    },
    {
      target: '.levers-config',
      content: (
        <div style={{ maxWidth: '500px' }}>
          <h3 style={{ 
            fontSize: '20px',
            fontWeight: 600,
            marginBottom: '12px',
            color: '#2c3e50',
            borderBottom: '2px solid #ff9800',
            paddingBottom: '8px'
          }}>
            ⚙️ Policy Levers Configuration
          </h3>
          <p style={{ fontSize: '15px', lineHeight: '1.8', marginBottom: '16px' }}>
            Configure <strong>adjustable policy parameters</strong> that control policy behavior. Levers 
            are the mechanisms through which policies influence healthcare utilization and costs.
          </p>
          <div style={{ 
            background: '#fff3e0',
            padding: '14px',
            borderRadius: '6px',
            marginBottom: '12px',
            borderLeft: '4px solid #ff9800'
          }}>
            <strong style={{ color: '#e65100' }}>🔧 Common Policy Levers:</strong>
            <ul style={{ margin: '8px 0 0 20px', padding: 0, fontSize: '14px' }}>
              <li><strong>Cost-Sharing:</strong> Copays, coinsurance, deductibles</li>
              <li><strong>Prior Authorization:</strong> Requirements and approval processes</li>
              <li><strong>Network Restrictions:</strong> In-network vs. out-of-network rules</li>
              <li><strong>Quantity Limits:</strong> Maximum units, days supply, frequency limits</li>
              <li><strong>Step Therapy:</strong> Required treatment sequences</li>
              <li><strong>Site of Care:</strong> Preferred locations for services</li>
              <li><strong>Formulary Tiers:</strong> Drug tier assignments and cost-sharing</li>
            </ul>
          </div>
          <div style={{ 
            background: '#f3e5f5',
            padding: '12px',
            borderRadius: '6px',
            marginBottom: '12px'
          }}>
            <strong style={{ color: '#7b1fa2' }}>📊 Impact Modeling:</strong>
            <p style={{ margin: '6px 0 0 0', fontSize: '14px' }}>
              Lever settings directly influence <strong>utilization and cost outcomes</strong>. Use 
              elasticity models and historical data to estimate impacts before activation.
            </p>
          </div>
          <p style={{ 
            marginTop: '12px', 
            fontSize: '13px', 
            color: '#666',
            padding: '8px',
            background: '#e8f5e9',
            borderRadius: '4px',
            borderLeft: '3px solid #4caf50'
          }}>
            🎯 <strong>Configuration Tip:</strong> Start with conservative lever settings and adjust based 
            on observed outcomes. Use guardrails to set safety limits.
          </p>
        </div>
      ),
      placement: 'top',
    },
  ],
}

// Export all tours
export const allTours: Record<string, TourConfig> = {
  dashboard: dashboardTour,
  policies: policiesTour,
  'policy-builder': policyBuilderTour,
  'policy-workspace': policyWorkspaceTour,
  'analysis-workspace': analysisWorkspaceTour,
  whatif: whatIfTour,
  ingestions: ingestionsTour,
}
