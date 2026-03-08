import React from 'react'
import { Step } from 'react-joyride'

export interface TourConfig {
  module: string
  steps: Step[]
  title: string
  description: string
}

// Enterprise-grade tour content with detailed descriptions
const createStep = (
  target: string,
  title: string,
  description: string,
  businessValue?: string,
  tips?: string,
  placement: 'top' | 'bottom' | 'left' | 'right' = 'bottom',
  route?: string
) => ({
  target,
  placement,
  route, // Route to navigate to for this step
  content: {
    title,
    description,
    businessValue,
    tips,
  },
  disableBeacon: true,
})

// Dashboard Tour - Enterprise-Grade with Detailed Content
export const dashboardTour: TourConfig = {
  module: 'dashboard',
  title: 'Executive Dashboard Tour',
  description: 'Master the command center for healthcare policy management and financial oversight',
  steps: [
    createStep(
      '.dashboard-header',
      'Executive Dashboard Overview',
      'The Executive Dashboard serves as your centralized command center for monitoring healthcare policy performance, financial impact, and strategic decision-making. This persona-specific view provides CFOs, Actuaries, and CMOs with real-time insights into policy portfolio health, cost trends, and risk indicators.',
      'Enables executive-level oversight with instant visibility into policy ROI, cost savings, and utilization impacts. Supports data-driven decision-making with comprehensive metrics and trend analysis.',
      'Switch between persona views (Executive, Analyst, Policy Owner, Ops/Clinical) to see role-specific insights tailored to your responsibilities.',
      'bottom',
      '/dashboard/executive'
    ),
    createStep(
      '.key-metrics-row',
      'Key Performance Metrics',
      'These executive-level metrics provide instant visibility into your policy portfolio\'s financial and operational performance. Track total cost impact (savings or increases), average utilization changes across all policies, active policy count, and pending decisions requiring attention. Each metric card displays trend indicators and contextual information.',
      'Delivers immediate financial and operational health indicators. Helps identify high-impact policies and areas requiring executive attention. Supports quick assessment of portfolio-wide performance.',
      'Click any metric card to drill down into detailed breakdowns. Use these metrics in executive briefings and board presentations. Monitor trends over time to identify patterns.',
      'bottom',
      '/dashboard/executive'
    ),
    createStep(
      '.decision-recommendations',
      'AI-Powered Decision Recommendations',
      'Our intelligent decision support system analyzes policy performance data, risk indicators, and historical outcomes to provide actionable recommendations. Each recommendation includes evidence links, confidence scores, priority levels (critical, high, medium), and specific action items. Recommendations are based on policy performance patterns, risk assessments, and cost-benefit analysis.',
      'Accelerates decision-making by surfacing critical actions. Reduces time-to-decision from days to minutes. Provides audit trail with evidence links for compliance and governance.',
      'Review recommendations regularly, especially those marked as critical or high priority. Click "View Policy" to examine the underlying policy details. Use confidence scores to prioritize actions.',
      'left',
      '/dashboard/executive'
    ),
    createStep(
      '.cost-trend-chart',
      'Cost Trend Forecast with Confidence Intervals',
      'This probabilistic forecasting visualization shows projected costs based on policy impacts with uncertainty ranges (P10/P50/P90 percentiles). The chart displays historical actual costs (green) and forecasted costs (purple) with confidence bands. Wider bands indicate higher uncertainty, while narrower bands suggest more reliable forecasts.',
      'Enables proactive financial planning with uncertainty quantification. Supports budget forecasting and risk management. Helps identify policies with high cost uncertainty requiring closer monitoring.',
      'Hover over any point to see detailed metrics including actual vs. forecast values. Wider confidence bands suggest the need for more observation data. Use this chart in financial planning and budget presentations.',
      'top',
      '/dashboard/executive'
    ),
    createStep(
      '.risk-register',
      'Risk Register: Uncertainty Drivers',
      'The Risk Register provides a comprehensive assessment dashboard showing policy risks, uncertainty drivers, and mitigation strategies. It identifies top uncertainty drivers such as high variance policies, cost uncertainty, data availability issues, and assumption risks. Each risk includes severity level, description, driver identification, and recommended mitigation actions.',
      'Proactively identifies and manages policy risks before they impact outcomes. Supports risk-based prioritization of policy reviews. Enables compliance with risk management frameworks.',
      'Review the risk register regularly, especially before major policy decisions. Prioritize high-severity risks for immediate attention. Use mitigation strategies to address identified risks proactively.',
      'left',
      '/dashboard/executive'
    ),
    createStep(
      '.top-policies-chart',
      'Top Policy Performance Analysis',
      'This visualization tracks top-performing policies ranked by cost impact, showing utilization changes, cost savings or increases, and prediction accuracy metrics. Policies are displayed with their performance indicators, allowing you to quickly identify high-impact policies, underperformers, and opportunities for scaling successful policies.',
      'Identifies best-performing policies for scaling and replication. Highlights underperforming policies requiring review or adjustment. Supports portfolio optimization decisions.',
      'Click on any policy in the chart to view detailed performance metrics. Use this view to identify policies for expansion or modification. Compare policy performance to identify best practices.',
      'top',
      '/dashboard/executive'
    ),
  ],
}

// Policy Catalog Tour - Enterprise-Grade
export const policiesTour: TourConfig = {
  module: 'policies',
  title: 'Policy Catalog Tour',
  description: 'Comprehensive guide to managing and navigating your healthcare policy portfolio',
  steps: [
    createStep(
      '.policy-catalog-header',
      'Policy Catalog Overview',
      'The Policy Catalog is your central repository for all healthcare policies in your organization. It provides a unified view of policy status, performance metrics, lifecycle states, and operational information. Use this catalog to track policy inventory, monitor compliance, assess performance, and manage policy changes across your entire portfolio.',
      'Centralizes policy management in a single location. Enables portfolio-wide visibility and governance. Supports policy discovery, review, and lifecycle management.',
      'Use the catalog to audit your policy inventory regularly. Check policy status to identify policies requiring attention. Review performance metrics to identify optimization opportunities.',
      'bottom',
      '/policies'
    ),
    createStep(
      '.policy-search-filters',
      'Advanced Search & Filtering',
      'Powerful search and filtering capabilities help you quickly locate specific policies from large portfolios. Search by policy name, description, or keywords. Filter by policy type (Prior Authorization, Step Therapy, Site of Care, etc.), status (Draft, Active, Monitoring, etc.), owner, creation date, or performance metrics. Advanced filters allow combining multiple criteria for precise results.',
      'Dramatically reduces time to find specific policies. Enables efficient portfolio analysis and reporting. Supports compliance audits and policy reviews.',
      'Use filters to create custom views for different stakeholders. Save frequently used filter combinations for quick access. Combine search and filters for precise policy discovery.',
      'bottom',
      '/policies'
    ),
    createStep(
      '.policy-list',
      'Policy List & Card View',
      'The policy list displays all policies with key information in an easy-to-scan format. Each policy card or row shows policy name, type, status, owner, key performance metrics (cost impact, utilization change), and quick action buttons. Color-coded status indicators provide instant visual feedback on policy state. Performance metrics help identify high-impact policies at a glance.',
      'Enables rapid assessment of policy portfolio health. Provides quick access to policy details and actions. Supports efficient policy management workflows.',
      'Click on any policy to view full details and edit. Use the status indicators to identify policies requiring attention. Review performance metrics to prioritize policy reviews.',
      'bottom',
      '/policies'
    ),
    createStep(
      '.create-policy-button',
      'Create New Policy',
      'The Policy Builder wizard guides you through creating structured, compliant policies step-by-step. You\'ll configure policy metadata, define scope (which claims/members/providers), set levers (prior auth, step therapy, etc.), establish conditions and exceptions, and review before activation. The builder ensures policy consistency and compliance with organizational standards.',
      'Standardizes policy creation process. Ensures policy completeness and compliance. Reduces errors through guided workflows.',
      'Start with a template if available for your policy type. Complete all required fields before proceeding. Review the policy summary before saving to ensure accuracy.',
      'bottom',
      '/policies'
    ),
  ],
}

// Policy Builder Tour - Enterprise-Grade
export const policyBuilderTour: TourConfig = {
  module: 'policy-builder',
  title: 'Policy Builder Tour',
  description: 'Master the comprehensive policy creation workflow for structured, compliant healthcare policies',
  steps: [
    createStep(
      '.policy-builder-header',
      'Policy Builder Overview',
      'The Policy Builder is a comprehensive wizard that guides you through creating structured, compliant healthcare policies. It ensures consistency, completeness, and compliance with organizational standards. The builder supports multiple policy types including Prior Authorization, Step Therapy, Site of Care restrictions, and custom policy configurations. Each policy is built with clear scope definitions, lever configurations, conditions, exceptions, and review processes.',
      'Standardizes policy creation across the organization. Reduces errors and ensures compliance. Accelerates policy development with guided workflows.',
      'Start with a template if available for your policy type. Review the policy summary before saving. Use the stepper to navigate between sections easily.',
      'bottom',
      '/policies/builder'
    ),
    createStep(
      '.policy-builder-stepper',
      'Step-by-Step Policy Creation',
      'The policy builder uses a structured stepper workflow: (1) Basic Info - policy name, type, description, owner; (2) Scope - define which claims, members, or providers the policy applies to; (3) Levers - configure policy mechanisms like prior auth requirements; (4) Conditions - set eligibility and application rules; (5) Exceptions - define special cases and overrides; (6) Review & Save - validate and activate the policy. You can navigate back to any step to make changes before finalizing.',
      'Ensures all required policy components are completed. Prevents incomplete policies from being activated. Provides clear progress tracking through the creation process.',
      'You can go back to previous steps at any time to make changes. Complete all required fields before proceeding. Review the final summary carefully before saving.',
      'bottom',
      '/policies/builder'
    ),
    createStep(
      '.scope-selector',
      'Policy Scope Configuration',
      'Define the precise scope of your policy by specifying which claims, members, providers, or services it applies to. Use filters to narrow scope based on diagnosis codes, procedure codes, member demographics, provider types, geographic regions, or other criteria. Scope definition is critical for ensuring the policy applies only to intended populations and situations.',
      'Prevents policy misapplication. Ensures policies target the correct populations. Supports precise policy impact measurement.',
      'Use multiple filters to create precise scope definitions. Test scope with sample data before finalizing. Document scope decisions for future reference.',
      'top',
      '/policies/builder'
    ),
    createStep(
      '.levers-config',
      'Policy Levers Configuration',
      'Policy levers are the mechanisms through which policies achieve their objectives. Configure levers such as Prior Authorization requirements, Step Therapy protocols, Site of Care restrictions, Quantity Limits, or custom lever types. Each lever has specific parameters you can adjust, including approval criteria, documentation requirements, and enforcement levels.',
      'Enables precise policy mechanism configuration. Supports various policy types and objectives. Provides flexibility for different use cases.',
      'Each lever type has specific configuration options. Review lever documentation for best practices. Test lever configurations before activation.',
      'top',
      '/policies/builder'
    ),
  ],
}

// Policy Workspace Tour - Enterprise-Grade
export const policyWorkspaceTour: TourConfig = {
  module: 'policy-workspace',
  title: 'Policy Workspace Tour',
  description: 'Comprehensive guide to managing policy lifecycle, assumptions, guardrails, and version control',
  steps: [
    createStep(
      '.workspace-tabs',
      'Policy Workspace Navigation',
      'The Policy Workspace provides a comprehensive view of all policy management aspects through organized tabs. Navigate between Overview (policy summary and status), Assumptions (documented design assumptions), Guardrails (safety limits and constraints), Versions (change history and version control), and additional tabs for specific policy management functions. Each tab provides focused functionality for different aspects of policy governance.',
      'Centralizes all policy management functions in one location. Enables efficient navigation between policy aspects. Supports comprehensive policy governance workflows.',
      'Use tabs to organize your policy review process. Start with Overview to get the big picture, then dive into specific tabs as needed. Each tab maintains context as you navigate.',
      'bottom',
      '/policies'
    ),
    createStep(
      '.assumptions-manager',
      'Assumptions Documentation & Tracking',
      'The Assumptions Manager enables you to document and track all assumptions made during policy design and implementation. This includes clinical assumptions, financial assumptions, behavioral assumptions, and data quality assumptions. Each assumption should be documented with rationale, evidence, and review dates. This transparency is essential for policy audits, future reviews, and understanding policy limitations.',
      'Ensures transparency in policy decision-making. Supports policy audits and compliance reviews. Enables future policy reviewers to understand design rationale.',
      'Document assumptions as you design policies, not after. Include evidence or rationale for each assumption. Review assumptions regularly, especially when policy outcomes differ from expectations.',
      'top',
      '/policies'
    ),
    createStep(
      '.guardrails-manager',
      'Policy Guardrails & Safety Limits',
      'Guardrails are safety limits and constraints that prevent unintended policy consequences. Configure guardrails such as maximum cost impact thresholds, minimum data quality requirements, maximum utilization change limits, or custom business rules. Guardrails automatically trigger alerts or policy adjustments when thresholds are exceeded, protecting against adverse outcomes.',
      'Prevents unintended policy consequences. Provides automated safety mechanisms. Supports risk management and compliance.',
      'Set guardrails based on organizational risk tolerance. Review guardrail triggers regularly. Adjust guardrails based on policy performance and organizational priorities.',
      'top',
      '/policies'
    ),
    createStep(
      '.versions-list',
      'Policy Version Control & History',
      'The Version Control system tracks all policy versions with complete change history. View effective dates, state transitions (Draft → Proposed → Approved → Active → Monitoring), changelog entries, and version comparisons. Each version maintains a complete audit trail including who made changes, when, and why. This supports compliance, rollback capabilities, and policy evolution tracking.',
      'Maintains complete policy change audit trail. Enables policy rollback if needed. Supports compliance and governance requirements.',
      'Review version history before making policy changes. Use version comparison to understand what changed. Document reasons for version changes in changelog entries.',
      'top',
      '/policies'
    ),
  ],
}

// Analysis Workspace Tour - Enterprise-Grade
export const analysisWorkspaceTour: TourConfig = {
  module: 'analysis-workspace',
  title: 'Analysis Workspace Tour',
  description: 'Master causal inference analysis to measure policy impact with confidence and rigor',
  steps: [
    createStep(
      '.analysis-header',
      'Analysis Workspace Overview',
      'The Analysis Workspace enables you to run rigorous causal inference analyses to measure policy impact. Every analysis uses advanced statistical methods (difference-in-differences, regression discontinuity, propensity score matching, etc.) to estimate true policy effects. Each analysis includes confidence scores, method validation checks, data sufficiency assessments, and limitations documentation. This ensures reliable, defensible impact measurements.',
      'Provides rigorous, defensible policy impact measurements. Supports evidence-based decision-making. Enables policy performance evaluation with statistical confidence.',
      'Review method checks before interpreting results. Higher confidence scores indicate more reliable estimates. Consider data limitations when making decisions based on analyses.',
      'bottom',
      '/analyses'
    ),
    createStep(
      '.analysis-tabs',
      'Analysis Navigation Tabs',
      'Navigate between different analysis components: Analyses (list of all analyses), Results (detailed impact results), Method Checks (statistical validation), Substitution Analysis (service substitution effects), Provider Segmentation (provider-level impacts), and other specialized analysis views. Each tab provides focused insights into different aspects of policy impact.',
      'Organizes complex analysis information into digestible views. Enables focused exploration of specific analysis aspects. Supports comprehensive impact understanding.',
      'Start with Results to see impact estimates, then review Method Checks to assess reliability. Use Provider Segmentation to understand heterogeneous effects across providers.',
      'bottom',
      '/analyses'
    ),
    createStep(
      '.impact-results',
      'Detailed Impact Results',
      'Impact Results display comprehensive analysis outcomes including effect size (absolute and percentage changes), confidence intervals (uncertainty ranges), statistical significance, and percent changes. Results are broken down by outcome type (cost, utilization, quality metrics) and may include subgroup analyses. Each result includes methodology information and data coverage details.',
      'Provides clear, actionable impact estimates. Quantifies uncertainty through confidence intervals. Enables evidence-based policy decisions.',
      'Focus on confidence intervals, not just point estimates. Wider intervals indicate more uncertainty. Review methodology to understand how results were calculated.',
      'top',
      '/analyses'
    ),
    createStep(
      '.trust-panel',
      'Trust & Validation Panel',
      'The Trust Panel provides comprehensive assessment of analysis reliability including confidence scores (0-100 scale), validation checks (method appropriateness, data quality, assumptions), data sufficiency indicators, and documented limitations. Use this panel to assess whether you can trust the analysis results for decision-making. Higher confidence scores and passing validation checks indicate more reliable results.',
      'Enables assessment of analysis reliability. Supports informed decision-making. Prevents decisions based on unreliable analyses.',
      'Always review the Trust Panel before making decisions. Low confidence scores or failed validation checks suggest the analysis may not be reliable. Consider limitations when interpreting results.',
      'left',
      '/analyses'
    ),
  ],
}

// What-If Analysis Tour - Enterprise-Grade
export const whatIfTour: TourConfig = {
  module: 'whatif',
  title: 'What-If Analysis Tour',
  description: 'Explore policy scenarios and compare projected outcomes before implementation',
  steps: [
    createStep(
      '.whatif-header',
      'What-If Scenario Analysis',
      'What-If Analysis enables you to adjust policy parameters and examine projected impact before implementation. Create multiple scenarios with different lever settings, projection horizons, and assumptions. Compare scenarios side-by-side to evaluate trade-offs, understand sensitivity to parameter changes, and make informed decisions. This forward-looking analysis helps optimize policy design and anticipate outcomes.',
      'Enables policy optimization before implementation. Reduces risk by exploring scenarios. Supports evidence-based policy design decisions.',
      'Create multiple scenarios to explore different options. Compare scenarios to understand trade-offs. Use sensitivity analysis to identify critical parameters.',
      'bottom',
      '/whatif'
    ),
    createStep(
      '.scenario-builder',
      'Scenario Configuration Builder',
      'The Scenario Builder allows you to configure scenario parameters including policy lever adjustments (prior auth requirements, step therapy protocols, etc.), projection horizon (3, 6, 12, 24 months), cost inflation assumptions, elasticity parameters, substitution rates, and lag effects. Each parameter can be adjusted independently to create different scenarios. The builder provides real-time feedback on parameter impacts.',
      'Enables flexible scenario creation. Supports exploration of parameter space. Provides immediate feedback on parameter changes.',
      'Start with baseline scenario, then adjust one parameter at a time to understand its impact. Create multiple scenarios to explore different options. Document scenario assumptions for future reference.',
      'top',
      '/whatif'
    ),
    createStep(
      '.scenario-comparison',
      'Scenario Comparison & Analysis',
      'The Scenario Comparison view displays multiple scenarios side-by-side, showing key metrics (cost impact, utilization change, confidence scores) for each scenario. Use this view to evaluate trade-offs, identify optimal scenarios, and understand sensitivity to parameter changes. The comparison includes visualizations (charts, tables) and detailed metrics to support decision-making.',
      'Enables informed scenario selection. Supports trade-off analysis. Facilitates evidence-based decision-making.',
      'Compare scenarios across multiple dimensions (cost, utilization, confidence). Look for scenarios that balance multiple objectives. Consider uncertainty ranges, not just point estimates.',
      'top',
      '/whatif'
    ),
  ],
}

// Data Ingestion Tour - Enterprise-Grade
export const ingestionsTour: TourConfig = {
  module: 'ingestions',
  title: 'Data Ingestion Tour',
  description: 'Comprehensive guide to uploading, managing, and monitoring data ingestion pipelines',
  steps: [
    createStep(
      '.ingestion-header',
      'Data Ingestion Dashboard',
      'The Data Ingestion Dashboard provides centralized management of all data ingestion pipelines and ingested datasets. Monitor ingestion status (pending, processing, completed, failed), view dataset inventory, track data quality metrics, and manage ingestion schedules. The dashboard provides real-time visibility into data pipeline health and enables quick identification of issues requiring attention.',
      'Centralizes data pipeline management. Enables proactive issue identification. Supports data governance and quality monitoring.',
      'Monitor ingestion status regularly to catch issues early. Review data quality metrics after each ingestion. Use the dashboard to track data freshness and completeness.',
      'bottom',
      '/ingestions'
    ),
    createStep(
      '.upload-section',
      'Data Upload & Connection Interface',
      'The Upload Interface supports multiple data ingestion methods: file upload (CSV, Parquet, JSON), database connections (SQL Server, PostgreSQL, etc.), API integrations, and scheduled imports. The system automatically detects schema, validates data formats, checks for required fields, and provides immediate feedback on data quality issues. Supported formats include claims data, member data, provider data, and custom datasets.',
      'Streamlines data ingestion process. Reduces manual data preparation. Ensures data quality through automated validation.',
      'Use templates for common data formats to speed up ingestion. Review validation results before completing ingestion. Document data source information for future reference.',
      'top',
      '/ingestions'
    ),
    createStep(
      '.ingestion-list',
      'Ingestion History & Monitoring',
      'The Ingestion History provides a complete audit trail of all data ingestions including status, timestamps, file sizes, record counts, error information, data quality metrics, and processing duration. Use this history to monitor ingestion patterns, identify recurring issues, track data freshness, and audit data lineage. Failed ingestions include detailed error messages to facilitate troubleshooting.',
      'Maintains complete ingestion audit trail. Enables troubleshooting of ingestion issues. Supports data lineage tracking and compliance.',
      'Review ingestion history regularly to identify patterns. Investigate failed ingestions promptly. Use history to track data freshness and completeness over time.',
      'top',
      '/ingestions'
    ),
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

