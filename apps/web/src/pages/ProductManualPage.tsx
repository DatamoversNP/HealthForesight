/**
 * Product Manual Page - Comprehensive End-to-End Documentation
 * Complete guide with screenshots and workflow steps
 */
import React from 'react'
import {
  Box,
  Container,
  Typography,
  Paper,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Card,
  CardContent,
  Grid,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  ImageList,
  ImageListItem,
} from '@mui/material'
import {
  CheckCircle as CheckCircleIcon,
  ExpandMore as ExpandMoreIcon,
  Dashboard as DashboardIcon,
  Policy as PolicyIcon,
  Analytics as AnalyticsIcon,
  People as PeopleIcon,
  Security as SecurityIcon,
  Comment as CommentIcon,
  Assessment as AssessmentIcon,
  Description as DescriptionIcon,
  Timeline as TimelineIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material'

export default function ProductManualPage() {
  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4, textAlign: 'center' }}>
        <Typography variant="h3" component="h1" gutterBottom fontWeight="bold">
          HealthForesight Product Manual
        </Typography>
        <Typography variant="h6" color="text.secondary" paragraph>
          Complete End-to-End Guide to All Features and Functionalities
        </Typography>
        <Chip label="Version 1.0" color="primary" sx={{ mt: 2 }} />
      </Box>

      {/* Table of Contents */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h5" gutterBottom>
            Table of Contents
          </Typography>
          <List>
            <ListItem>
              <ListItemText primary="1. Introduction & Overview" />
            </ListItem>
            <ListItem>
              <ListItemText primary="2. Getting Started" />
            </ListItem>
            <ListItem>
              <ListItemText primary="3. Complete Workflow Steps" />
            </ListItem>
            <ListItem>
              <ListItemText primary="4. Epic 1: RBAC & Role-Based Experiences" />
            </ListItem>
            <ListItem>
              <ListItemText primary="5. Epic 2: Policy Lifecycle Management" />
            </ListItem>
            <ListItem>
              <ListItemText primary="6. Epic 3: Decision Audit & Defensibility" />
            </ListItem>
            <ListItem>
              <ListItemText primary="7. Epic 4: Uncertainty & Risk Visualization" />
            </ListItem>
            <ListItem>
              <ListItemText primary="8. Epic 5: Behavioral Signal Detection" />
            </ListItem>
            <ListItem>
              <ListItemText primary="9. Epic 6: Collaboration Workflows" />
            </ListItem>
            <ListItem>
              <ListItemText primary="10. Epic 7: Executive Narrative Layer" />
            </ListItem>
            <ListItem>
              <ListItemText primary="11. Dashboards & Analytics" />
            </ListItem>
            <ListItem>
              <ListItemText primary="12. Data Management" />
            </ListItem>
          </List>
        </CardContent>
      </Card>

      {/* Section 1: Introduction */}
      <Section title="1. Introduction & Overview" icon={<DashboardIcon />}>
        <Typography variant="body1" paragraph>
          HealthForesight is an enterprise-grade Policy Intelligence & Decision Assurance Platform that enables
          healthcare payers to manage policies throughout their complete lifecycle, from creation to sunset,
          with full traceability, defensibility, and continuous learning.
        </Typography>

        <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
          Core Principles
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                  Separation of Concerns
                </Typography>
                <Typography variant="body2">
                  Each stage of the policy lifecycle is clearly separated: baseline, predicted impact,
                  observed impact, and learning. This ensures traceability and auditability.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                  Full Traceability
                </Typography>
                <Typography variant="body2">
                  Every decision, assumption, and change is tracked with complete audit trails,
                  enabling full defensibility for regulatory inquiries.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                  Behavioral Modeling
                </Typography>
                <Typography variant="body2">
                  The system models provider and patient behavior, enabling accurate predictions
                  and understanding of policy impacts.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                  Transparency
                </Typography>
                <Typography variant="body2">
                  All assumptions, methods, and uncertainties are clearly documented and visible
                  to stakeholders at every level.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        <Box sx={{ mt: 3, p: 2, bgcolor: 'primary.light', borderRadius: 1, color: 'white' }}>
          <Typography variant="h6" gutterBottom>
            Product Flow Architecture
          </Typography>
          <Typography variant="body1">
            <strong>Closed-loop policy intelligence system:</strong>
          </Typography>
          <Typography variant="body2" component="div" sx={{ mt: 1, fontFamily: 'monospace' }}>
            Ingest → Baseline → Policy Define → Predict → Approve → Activate → Observe → Explain → Decide → Learn → Repeat
          </Typography>
        </Box>
      </Section>

      {/* Section 2: Getting Started */}
      <Section title="2. Getting Started" icon={<SettingsIcon />}>
        <Typography variant="h6" gutterBottom>
          Initial Setup
        </Typography>
        <Stepper orientation="vertical">
          <Step active>
            <StepLabel>Start API Server</StepLabel>
            <StepContent>
              <Typography variant="body2" paragraph>
                Navigate to the API directory and start the server:
              </Typography>
              <Paper sx={{ p: 2, bgcolor: 'grey.100', fontFamily: 'monospace' }}>
                cd apps/api<br />
                python3 -m uvicorn uepi_api.main:app --reload --port 8000
              </Paper>
            </StepContent>
          </Step>
          <Step active>
            <StepLabel>Start Frontend Server</StepLabel>
            <StepContent>
              <Typography variant="body2" paragraph>
                In a new terminal, start the web application:
              </Typography>
              <Paper sx={{ p: 2, bgcolor: 'grey.100', fontFamily: 'monospace' }}>
                cd apps/web<br />
                npm run dev
              </Paper>
            </StepContent>
          </Step>
          <Step active>
            <StepLabel>Access Application</StepLabel>
            <StepContent>
              <Typography variant="body2" paragraph>
                Open your browser and navigate to:
              </Typography>
              <Paper sx={{ p: 2, bgcolor: 'grey.100', fontFamily: 'monospace' }}>
                http://localhost:3050
              </Paper>
              <Typography variant="body2" sx={{ mt: 2 }}>
                You will be automatically logged in as a demo user. No authentication required for development.
              </Typography>
            </StepContent>
          </Step>
        </Stepper>
      </Section>

      {/* Section 3: Complete Workflow Steps */}
      <Section title="3. Complete Workflow Steps" icon={<TimelineIcon />}>
        <Typography variant="h6" gutterBottom>
          End-to-End Policy Lifecycle Workflow
        </Typography>
        
        <Stepper orientation="vertical" sx={{ mt: 2 }}>
          <Step active>
            <StepLabel>Step 1: Data Ingestion</StepLabel>
            <StepContent>
              <Typography variant="body2" paragraph>
                <strong>Purpose:</strong> Ingest claims, enrollment, and provider data into the system.
              </Typography>
              <Typography variant="body2" paragraph>
                <strong>How to Access:</strong> Navigate to "Ingestions" from the main menu.
              </Typography>
              <Typography variant="body2" paragraph>
                <strong>Features:</strong>
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Upload CSV files or connect to data sources" />
                </ListItem>
                <ListItem>
                  <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Automatic schema validation and mapping" />
                </ListItem>
                <ListItem>
                  <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Data quality checks and reporting" />
                </ListItem>
              </List>
              <Box sx={{ mt: 2, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                <Typography variant="caption" fontWeight="bold">Screenshot Placeholder:</Typography>
                <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                  [Image: Ingestion Dashboard showing data upload interface]
                </Typography>
              </Box>
            </StepContent>
          </Step>

          <Step active>
            <StepLabel>Step 2: Baseline Analysis</StepLabel>
            <StepContent>
              <Typography variant="body2" paragraph>
                <strong>Purpose:</strong> Establish historical baseline metrics before policy implementation.
              </Typography>
              <Typography variant="body2" paragraph>
                <strong>How to Access:</strong> Navigate to "Baseline Analysis" from the Analyses menu.
              </Typography>
              <Typography variant="body2" paragraph>
                <strong>Key Metrics:</strong>
              </Typography>
              <Grid container spacing={2} sx={{ mt: 1 }}>
                <Grid item xs={12} sm={6}>
                  <Chip label="Utilization per 1,000 members" color="primary" sx={{ mr: 1, mb: 1 }} />
                  <Chip label="Cost per member per month" color="primary" sx={{ mr: 1, mb: 1 }} />
                  <Chip label="Service mix distribution" color="primary" sx={{ mr: 1, mb: 1 }} />
                </Grid>
              </Grid>
              <Box sx={{ mt: 2, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                <Typography variant="caption" fontWeight="bold">Screenshot Placeholder:</Typography>
                <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                  [Image: Baseline Analysis results showing utilization trends and metrics]
                </Typography>
              </Box>
            </StepContent>
          </Step>

          <Step active>
            <StepLabel>Step 3: Policy Creation</StepLabel>
            <StepContent>
              <Typography variant="body2" paragraph>
                <strong>Purpose:</strong> Create new policies with complete configuration.
              </Typography>
              <Typography variant="body2" paragraph>
                <strong>How to Access:</strong> Navigate to "Policies" → "Create Policy" or use Policy Builder.
              </Typography>
              <Typography variant="body2" paragraph>
                <strong>Policy Configuration Steps:</strong>
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Basic Info: Classification and intent" />
                </ListItem>
                <ListItem>
                  <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Scope: Where/who it applies (LOB, market, network)" />
                </ListItem>
                <ListItem>
                  <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Levers: What is being controlled (prior auth, cost sharing, etc.)" />
                </ListItem>
                <ListItem>
                  <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Conditions: When it applies" />
                </ListItem>
                <ListItem>
                  <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Exceptions: When it does NOT apply" />
                </ListItem>
                <ListItem>
                  <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Review & Save: Human-readable summary + machine schema" />
                </ListItem>
              </List>
              <Box sx={{ mt: 2, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                <Typography variant="caption" fontWeight="bold">Screenshot Placeholder:</Typography>
                <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                  [Image: Policy Builder wizard showing all 6 configuration steps]
                </Typography>
              </Box>
            </StepContent>
          </Step>

          <Step active>
            <StepLabel>Step 4: Predicted Impact Generation</StepLabel>
            <StepContent>
              <Typography variant="body2" paragraph>
                <strong>Purpose:</strong> Generate forward-looking predictions of policy impact before activation.
              </Typography>
              <Typography variant="body2" paragraph>
                <strong>Automatic:</strong> Predicted impact is automatically generated when a policy is created.
              </Typography>
              <Typography variant="body2" paragraph>
                <strong>Components:</strong>
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Elasticity models for utilization changes" />
                </ListItem>
                <ListItem>
                  <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Behavioral models for provider/patient response" />
                </ListItem>
                <ListItem>
                  <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Uncertainty ranges (P10/P50/P90)" />
                </ListItem>
                <ListItem>
                  <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Confidence intervals" />
                </ListItem>
              </List>
              <Box sx={{ mt: 2, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                <Typography variant="caption" fontWeight="bold">Screenshot Placeholder:</Typography>
                <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                  [Image: Predicted Impact dashboard showing forecast distributions and uncertainty bands]
                </Typography>
              </Box>
            </StepContent>
          </Step>

          <Step active>
            <StepLabel>Step 5: Policy Approval & Activation</StepLabel>
            <StepContent>
              <Typography variant="body2" paragraph>
                <strong>Purpose:</strong> Review, approve, and activate policies through the lifecycle workflow.
              </Typography>
              <Typography variant="body2" paragraph>
                <strong>How to Access:</strong> Navigate to "Policies" → Select a policy → "Workspace" tab.
              </Typography>
              <Typography variant="body2" paragraph>
                <strong>Lifecycle States:</strong>
              </Typography>
              <Grid container spacing={2} sx={{ mt: 1 }}>
                <Grid item xs={12} sm={6} md={4}>
                  <Chip label="DRAFT" color="default" sx={{ mr: 1, mb: 1 }} />
                  <Chip label="PROPOSED" color="warning" sx={{ mr: 1, mb: 1 }} />
                  <Chip label="APPROVED" color="info" sx={{ mr: 1, mb: 1 }} />
                </Grid>
                <Grid item xs={12} sm={6} md={4}>
                  <Chip label="ACTIVE" color="success" sx={{ mr: 1, mb: 1 }} />
                  <Chip label="MONITORING" color="primary" sx={{ mr: 1, mb: 1 }} />
                  <Chip label="ITERATING" color="warning" sx={{ mr: 1, mb: 1 }} />
                </Grid>
                <Grid item xs={12} sm={6} md={4}>
                  <Chip label="SUNSET" color="default" sx={{ mr: 1, mb: 1 }} />
                </Grid>
              </Grid>
              <Box sx={{ mt: 2, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                <Typography variant="caption" fontWeight="bold">Screenshot Placeholder:</Typography>
                <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                  [Image: Policy Workspace showing state promotion workflow and approval interface]
                </Typography>
              </Box>
            </StepContent>
          </Step>

          <Step active>
            <StepLabel>Step 6: Observed Impact Analysis</StepLabel>
            <StepContent>
              <Typography variant="body2" paragraph>
                <strong>Purpose:</strong> Measure actual outcomes after policy implementation.
              </Typography>
              <Typography variant="body2" paragraph>
                <strong>How to Access:</strong> Navigate to "Observation Analysis" from the Analyses menu.
              </Typography>
              <Typography variant="body2" paragraph>
                <strong>Analysis Methods:</strong>
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Difference-in-Differences (DiD)" />
                </ListItem>
                <ListItem>
                  <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Interrupted Time Series" />
                </ListItem>
                <ListItem>
                  <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Pre/Post Analysis" />
                </ListItem>
              </List>
              <Typography variant="body2" paragraph sx={{ mt: 2 }}>
                <strong>Comparison:</strong> Observed impact is compared against both baseline and predicted impact,
                enabling learning and model calibration.
              </Typography>
              <Box sx={{ mt: 2, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                <Typography variant="caption" fontWeight="bold">Screenshot Placeholder:</Typography>
                <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                  [Image: Observation Analysis results showing observed vs predicted comparison charts]
                </Typography>
              </Box>
            </StepContent>
          </Step>

          <Step active>
            <StepLabel>Step 7: Learning Loop</StepLabel>
            <StepContent>
              <Typography variant="body2" paragraph>
                <strong>Purpose:</strong> Automatically improve prediction models based on observed accuracy.
              </Typography>
              <Typography variant="body2" paragraph>
                <strong>Automatic Process:</strong> The system automatically updates elasticity models when new
                observations are available, improving future predictions.
              </Typography>
              <Typography variant="body2" paragraph>
                <strong>Learning Metrics:</strong>
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Prediction accuracy scores" />
                </ListItem>
                <ListItem>
                  <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Model calibration adjustments" />
                </ListItem>
                <ListItem>
                  <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Elasticity curve refinements" />
                </ListItem>
              </List>
              <Box sx={{ mt: 2, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                <Typography variant="caption" fontWeight="bold">Screenshot Placeholder:</Typography>
                <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                  [Image: Learning Metrics dashboard showing prediction accuracy trends over time]
                </Typography>
              </Box>
            </StepContent>
          </Step>
        </Stepper>
      </Section>

      {/* Epic Sections */}
      <EpicSection
        number={1}
        title="RBAC & Role-Based Experiences"
        icon={<SecurityIcon />}
        description="Role-based access control and persona-specific dashboards"
        features={[
          "Role management and user assignments",
          "Permission checking and resource scopes",
          "Persona-specific dashboards (Executive, Policy Owner, Analyst, Ops/Clinical)",
          "Role switching in navigation",
        ]}
      />

      <EpicSection
        number={2}
        title="Policy Lifecycle Management"
        icon={<PolicyIcon />}
        description="Complete policy lifecycle with versioning, assumptions, and guardrails"
        features={[
          "Policy versioning with state transitions",
          "Assumptions management (elasticity, substitution, lag)",
          "Guardrails and rollback triggers",
          "Changelog and audit trail",
          "Policy Workspace with 19 integrated tabs",
        ]}
      />

      <EpicSection
        number={3}
        title="Decision Audit & Defensibility"
        icon={<AssessmentIcon />}
        description="Complete decision records with audit trails and evidence linking"
        features={[
          "Decision creation and management",
          "Complete audit trail entries",
          "Evidence linking to analyses, datasets, and models",
          "Reproducibility packs",
          "Decision and Evidence tabs in Policy Workspace",
        ]}
      />

      <EpicSection
        number={4}
        title="Uncertainty & Risk Visualization"
        icon={<AnalyticsIcon />}
        description="Forecast distributions, scenario analysis, and risk management"
        features={[
          "Forecast distributions with P10/P50/P90 ranges",
          "Fan chart visualizations",
          "Scenario runs with sensitivity analysis",
          "Risk registers with risk drivers",
          "Confidence intervals and uncertainty bands",
        ]}
      />

      <EpicSection
        number={5}
        title="Behavioral Signal Detection"
        icon={<PeopleIcon />}
        description="Provider behavior profiles, clusters, and alert management"
        features={[
          "Provider behavior profiles (Compliance, Adaptation, Resistance, Circumvention)",
          "Behavior clusters grouping similar providers",
          "Alert rules and event management",
          "Behavior dashboard with summary cards",
          "Alert management interface",
        ]}
      />

      <EpicSection
        number={6}
        title="Collaboration Workflows"
        icon={<CommentIcon />}
        description="Comments, tasks, approvals, and activity tracking"
        features={[
          "Comments on policies, analyses, and decisions",
          "Task management with assignments and due dates",
          "Approval request workflows",
          "Activity feed with event history",
          "Threaded comments and mentions",
        ]}
      />

      <EpicSection
        number={7}
        title="Executive Narrative Layer"
        icon={<DescriptionIcon />}
        description="Executive summaries, narratives, and export packs"
        features={[
          "Executive narrative generation",
          "Key findings and risk summaries",
          "Recommended actions",
          "Export templates (Board Pack, Regulator Pack, Provider Pack)",
          "Export pack generation and download",
        ]}
      />

      {/* Dashboards Section */}
      <Section title="11. Dashboards & Analytics" icon={<DashboardIcon />}>
        <Typography variant="h6" gutterBottom>
          Persona-Specific Dashboards
        </Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Executive Dashboard
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                    <ListItemText primary="Outcomes and ROI metrics" />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                    <ListItemText primary="Risk indicators" />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                    <ListItemText primary="Confidence scores" />
                  </ListItem>
                </List>
                <Box sx={{ mt: 2, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                  <Typography variant="caption">[Screenshot: Executive Dashboard]</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Policy Owner Dashboard
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                    <ListItemText primary="Policy lifecycle states" />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                    <ListItemText primary="Assumptions and guardrails" />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                    <ListItemText primary="Approval status" />
                  </ListItem>
                </List>
                <Box sx={{ mt: 2, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                  <Typography variant="caption">[Screenshot: Policy Owner Dashboard]</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Analyst Dashboard
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                    <ListItemText primary="Analysis methods and diagnostics" />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                    <ListItemText primary="Cohort definitions" />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                    <ListItemText primary="Statistical significance" />
                  </ListItem>
                </List>
                <Box sx={{ mt: 2, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                  <Typography variant="caption">[Screenshot: Analyst Dashboard]</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Ops/Clinical Dashboard
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                    <ListItemText primary="Provider behavior signals" />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                    <ListItemText primary="Appeals and denials" />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                    <ListItemText primary="Access risk indicators" />
                  </ListItem>
                </List>
                <Box sx={{ mt: 2, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                  <Typography variant="caption">[Screenshot: Ops/Clinical Dashboard]</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Section>

      {/* Data Management Section */}
      <Section title="12. Data Management" icon={<SettingsIcon />}>
        <Typography variant="h6" gutterBottom>
          Data Quality & Monitoring
        </Typography>
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="subtitle1" fontWeight="bold">
              Data Quality Dashboard
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" paragraph>
              The Data Quality Dashboard provides comprehensive monitoring of data quality across all datasets.
            </Typography>
            <List dense>
              <ListItem>
                <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                <ListItemText primary="Overall quality scores" />
              </ListItem>
              <ListItem>
                <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                <ListItemText primary="Completeness metrics" />
              </ListItem>
              <ListItem>
                <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                <ListItemText primary="Issue tracking by severity" />
              </ListItem>
            </List>
            <Box sx={{ mt: 2, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
              <Typography variant="caption">[Screenshot: Data Quality Dashboard]</Typography>
            </Box>
          </AccordionDetails>
        </Accordion>

        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="subtitle1" fontWeight="bold">
              Pipeline Monitoring
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" paragraph>
              Monitor data pipeline execution, status, and performance.
            </Typography>
            <List dense>
              <ListItem>
                <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                <ListItemText primary="Pipeline run history" />
              </ListItem>
              <ListItem>
                <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                <ListItemText primary="Success/failure rates" />
              </ListItem>
              <ListItem>
                <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                <ListItemText primary="Execution time tracking" />
              </ListItem>
            </List>
            <Box sx={{ mt: 2, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
              <Typography variant="caption">[Screenshot: Pipeline Monitoring Page]</Typography>
            </Box>
          </AccordionDetails>
        </Accordion>
      </Section>

      {/* Footer */}
      <Box sx={{ mt: 6, p: 3, bgcolor: 'grey.100', borderRadius: 2, textAlign: 'center' }}>
        <Typography variant="h6" gutterBottom>
          Need Help?
        </Typography>
        <Typography variant="body2" color="text.secondary">
          For additional support or questions, please refer to the Documentation Portal or contact your system administrator.
        </Typography>
      </Box>
    </Container>
  )
}

// Helper Components
function Section({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <Paper sx={{ p: 4, mb: 4 }}>
      <Box display="flex" alignItems="center" gap={2} mb={3}>
        {icon}
        <Typography variant="h4" component="h2">
          {title}
        </Typography>
      </Box>
      <Divider sx={{ mb: 3 }} />
      {children}
    </Paper>
  )
}

function EpicSection({
  number,
  title,
  icon,
  description,
  features,
}: {
  number: number
  title: string
  icon: React.ReactNode
  description: string
  features: string[]
}) {
  return (
    <Section title={`${number}. Epic ${number}: ${title}`} icon={icon}>
      <Typography variant="body1" paragraph sx={{ mb: 3 }}>
        {description}
      </Typography>

      <Typography variant="h6" gutterBottom>
        Key Features
      </Typography>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {features.map((feature, idx) => (
          <Grid item xs={12} sm={6} key={idx}>
            <Box display="flex" alignItems="center" gap={1}>
              <CheckCircleIcon color="success" fontSize="small" />
              <Typography variant="body2">{feature}</Typography>
            </Box>
          </Grid>
        ))}
      </Grid>

      <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
        How to Access
      </Typography>
      <Typography variant="body2" paragraph>
        Navigate to the relevant section from the main menu or Policy Workspace tabs.
      </Typography>

      <Box sx={{ mt: 3, p: 3, bgcolor: 'info.light', borderRadius: 1 }}>
        <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
          Screenshots:
        </Typography>
        <ImageList cols={2} gap={16} sx={{ mt: 1 }}>
          <ImageListItem>
            <Box sx={{ p: 2, bgcolor: 'white', borderRadius: 1, textAlign: 'center', minHeight: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Typography variant="caption" color="text.secondary">
                [Screenshot 1: {title} Main Interface]
              </Typography>
            </Box>
          </ImageListItem>
          <ImageListItem>
            <Box sx={{ p: 2, bgcolor: 'white', borderRadius: 1, textAlign: 'center', minHeight: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Typography variant="caption" color="text.secondary">
                [Screenshot 2: {title} Detailed View]
              </Typography>
            </Box>
          </ImageListItem>
        </ImageList>
      </Box>
    </Section>
  )
}

