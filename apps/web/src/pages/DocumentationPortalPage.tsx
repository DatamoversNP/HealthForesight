/**
 * HealthForesight Enterprise Documentation Portal
 * Comprehensive product documentation, architecture diagrams, analytical models, and KPI definitions
 */
import { useState, useEffect } from 'react'
import {
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Typography,
  Container,
  Paper,
  Chip,
  Grid,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
  Breadcrumbs,
  Link,
  Alert,
  AlertTitle,
  Stack,
} from '@mui/material'
import {
  ExpandMore as ExpandMoreIcon,
  Code as CodeIcon,
  Architecture as ArchitectureIcon,
  Storage as StorageIcon,
  Api as ApiIcon,
  Description as DescriptionIcon,
  MenuBook as MenuBookIcon,
  ChevronRight as ChevronRightIcon,
  Analytics as AnalyticsIcon,
  Functions as FunctionsIcon,
  Psychology as PsychologyIcon,
  ShowChart as ShowChartIcon,
} from '@mui/icons-material'

const drawerWidth = 320

interface DocSection {
  id: string
  title: string
  icon: React.ReactNode
  subsections?: string[]
}

export default function DocumentationPortalPage() {
  const [selectedSection, setSelectedSection] = useState<string>('overview')
  const [selectedSubsection, setSelectedSubsection] = useState<string>('')

  const sections: DocSection[] = [
    {
      id: 'overview',
      title: 'Product Overview',
      icon: <DescriptionIcon />,
      subsections: ['introduction', 'architecture', 'workflow', 'principles'],
    },
    {
      id: 'architecture',
      title: 'System Architecture',
      icon: <ArchitectureIcon />,
      subsections: ['overview', 'components', 'data-flow', 'deployment'],
    },
    {
      id: 'models',
      title: 'Analytical Models',
      icon: <AnalyticsIcon />,
      subsections: ['baseline', 'elasticity', 'impact', 'substitution', 'clustering', 'time-series', 'whatif'],
    },
    {
      id: 'metrics',
      title: 'KPI & Metrics',
      icon: <ShowChartIcon />,
      subsections: ['dictionary', 'denominators', 'primary', 'mix', 'behavioral', 'learning'],
    },
    {
      id: 'technical',
      title: 'Technical Documentation',
      icon: <CodeIcon />,
      subsections: ['api', 'data-models', 'storage', 'algorithms', 'integrations'],
    },
    {
      id: 'data-specs',
      title: 'Data Specifications',
      icon: <StorageIcon />,
      subsections: ['source-data', 'schemas', 'contracts', 'quality'],
    },
  ]

  useEffect(() => {
    const currentSection = sections.find(s => s.id === selectedSection)
    if (currentSection && currentSection.subsections && currentSection.subsections.length > 0) {
      setSelectedSubsection(currentSection.subsections[0])
    }
  }, [selectedSection])

  const currentSection = sections.find(s => s.id === selectedSection) || sections[0]

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
      {/* Sidebar Navigation */}
      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
            position: 'fixed',
            height: '100vh',
            overflowY: 'auto',
            borderRight: '1px solid',
            borderColor: 'divider',
            bgcolor: 'grey.50',
          },
        }}
      >
        <Box sx={{ p: 3, borderBottom: 1, borderColor: 'divider', bgcolor: 'primary.main', color: 'primary.contrastText' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <MenuBookIcon />
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              HealthForesight
            </Typography>
          </Box>
          <Typography variant="caption" sx={{ opacity: 0.9, fontSize: '0.75rem' }}>
            Enterprise Documentation Portal
          </Typography>
        </Box>
        <List sx={{ pt: 1 }}>
          {sections.map((section) => (
            <ListItem key={section.id} disablePadding>
              <ListItemButton
                selected={selectedSection === section.id}
                onClick={() => setSelectedSection(section.id)}
                sx={{
                  py: 1.5,
                  px: 2,
                  '&.Mui-selected': {
                    bgcolor: 'primary.main',
                    color: 'primary.contrastText',
                    '&:hover': {
                      bgcolor: 'primary.dark',
                    },
                    '& .MuiListItemText-primary': {
                      fontWeight: 600,
                    },
                  },
                }}
              >
                <Box sx={{ mr: 2, display: 'flex', alignItems: 'center' }}>
                  {section.icon}
                </Box>
                <ListItemText 
                  primary={section.title}
                  primaryTypographyProps={{
                    fontSize: '0.9rem',
                  }}
                />
              </ListItemButton>
            </ListItem>
          ))}
        </List>

        {/* Subsection Navigation */}
        {currentSection.subsections && currentSection.subsections.length > 0 && (
          <Box sx={{ px: 2, pb: 2, mt: 2 }}>
            <Typography variant="caption" sx={{ textTransform: 'uppercase', fontWeight: 600, color: 'text.secondary', px: 2, mb: 1, display: 'block' }}>
              Sections
            </Typography>
            <List dense>
              {currentSection.subsections.map((subsection) => (
                <ListItem key={subsection} disablePadding>
                  <ListItemButton
                    selected={selectedSubsection === subsection}
                    onClick={() => setSelectedSubsection(subsection)}
                    sx={{
                      py: 0.75,
                      px: 2,
                      borderRadius: 1,
                      '&.Mui-selected': {
                        bgcolor: 'action.selected',
                        '&:hover': {
                          bgcolor: 'action.selected',
                        },
                      },
                    }}
                  >
                    <ListItemText 
                      primary={subsection.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                      primaryTypographyProps={{
                        fontSize: '0.85rem',
                        fontWeight: selectedSubsection === subsection ? 600 : 400,
                      }}
                    />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          </Box>
        )}
      </Drawer>

      {/* Main Content Area */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: `${drawerWidth}px`,
          minHeight: '100vh',
          bgcolor: 'background.default',
        }}
      >
        <Box sx={{ p: 3, maxWidth: '1400px', mx: 'auto' }}>
          {/* Breadcrumbs */}
          <Breadcrumbs separator={<ChevronRightIcon fontSize="small" />} sx={{ mb: 2 }}>
            <Typography color="text.primary">Documentation</Typography>
            <Typography color="primary">{currentSection.title}</Typography>
            {selectedSubsection && (
              <Typography color="text.secondary" sx={{ textTransform: 'capitalize' }}>
                {selectedSubsection.replace(/-/g, ' ')}
              </Typography>
            )}
          </Breadcrumbs>

          {/* Content */}
          <Paper elevation={0} sx={{ p: 3, borderRadius: 1, minHeight: 'calc(100vh - 120px)', bgcolor: 'background.paper' }}>
            {renderContent(selectedSection, selectedSubsection)}
          </Paper>
        </Box>
      </Box>
    </Box>
  )
}

function renderContent(section: string, subsection: string): React.ReactNode {
  switch (section) {
    case 'overview':
      return renderOverview(subsection)
    case 'architecture':
      return renderArchitecture(subsection)
    case 'models':
      return renderModels(subsection)
    case 'metrics':
      return renderMetrics(subsection)
    case 'technical':
      return renderTechnical(subsection)
    case 'data-specs':
      return renderDataSpecs(subsection)
    default:
      return <Typography>Content not found</Typography>
  }
}

function renderOverview(subsection: string) {
  switch (subsection) {
    case 'introduction':
      return (
        <Box>
          <Typography variant="h3" gutterBottom sx={{ mb: 4, fontWeight: 700 }}>
            HealthForesight
          </Typography>
          <Typography variant="h5" gutterBottom color="primary" sx={{ mb: 4 }}>
            Utilization Elasticity & Policy Impact Intelligence Platform
          </Typography>
          
          <Alert severity="info" sx={{ mb: 4 }}>
            <AlertTitle>Enterprise-Grade Analytics Platform</AlertTitle>
            HealthForesight is a continuous, learning-based system that enables healthcare payers to predict, measure, and optimize the impact of utilization management policies through advanced analytics, machine learning, and behavioral modeling.
          </Alert>

          <Typography variant="body1" paragraph sx={{ fontSize: '1.1rem', lineHeight: 1.9, mb: 4 }}>
            HealthForesight transforms healthcare policy management from reactive to predictive. Unlike traditional one-time impact analyses, 
            HealthForesight operates as a <strong>continuous learning system</strong> that evolves with every new data point, policy change, and observed outcome.
          </Typography>

          <Typography variant="h6" gutterBottom sx={{ mt: 5, mb: 3, fontWeight: 600 }}>
            Key Capabilities
          </Typography>
          
          <Grid container spacing={3} sx={{ mb: 6 }}>
            <Grid item xs={12} md={6}>
              <Card variant="outlined" sx={{ height: '100%', '&:hover': { boxShadow: 4 } }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom color="primary" sx={{ fontWeight: 600 }}>
                    📊 Predictive Analytics
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Forecast policy impact before implementation using elasticity models, behavioral simulations, and scenario analysis. 
                    Confidence scores and uncertainty intervals provide transparency in predictions.
                  </Typography>
                  <Chip label="Elasticity Modeling" size="small" sx={{ mr: 1, mt: 1 }} />
                  <Chip label="What-If Analysis" size="small" />
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card variant="outlined" sx={{ height: '100%', '&:hover': { boxShadow: 4 } }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom color="primary" sx={{ fontWeight: 600 }}>
                    🔍 Causal Impact Measurement
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Measure actual policy impact using rigorous causal inference methods including Difference-in-Differences (DiD) and 
                    Interrupted Time Series (ITS) analysis. Control for confounders and market events.
                  </Typography>
                  <Chip label="Causal Inference" size="small" sx={{ mr: 1, mt: 1 }} />
                  <Chip label="Control Groups" size="small" />
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card variant="outlined" sx={{ height: '100%', '&:hover': { boxShadow: 4 } }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom color="primary" sx={{ fontWeight: 600 }}>
                    🧠 Behavioral Intelligence
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Understand provider and patient behavior through archetype segmentation, substitution pattern detection, and 
                    response modeling. Explain why policies succeed or fail.
                  </Typography>
                  <Chip label="Provider Segmentation" size="small" sx={{ mr: 1, mt: 1 }} />
                  <Chip label="Substitution Detection" size="small" />
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card variant="outlined" sx={{ height: '100%', '&:hover': { boxShadow: 4 } }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom color="primary" sx={{ fontWeight: 600 }}>
                    🔄 Continuous Learning
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Automatically update elasticity models and prediction accuracy based on observed outcomes. 
                    Each observation improves future predictions through an automated learning loop.
                  </Typography>
                  <Chip label="Model Updates" size="small" sx={{ mr: 1, mt: 1 }} />
                  <Chip label="Accuracy Tracking" size="small" />
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          <Typography variant="h6" gutterBottom sx={{ mt: 6, mb: 3, fontWeight: 600 }}>
            Use Cases
          </Typography>
          <Grid container spacing={2} sx={{ mb: 4 }}>
            <Grid item xs={12} sm={6} md={4}>
              <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
                <Typography variant="subtitle2" fontWeight={600} gutterBottom>Prior Authorization Impact</Typography>
                <Typography variant="body2" color="text.secondary">
                  Predict utilization reduction and cost savings before implementing prior authorization policies for advanced imaging.
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
                <Typography variant="subtitle2" fontWeight={600} gutterBottom>Site of Care Steerage</Typography>
                <Typography variant="body2" color="text.secondary">
                  Forecast patient migration patterns when steering from hospital outpatient departments to ambulatory surgery centers.
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
                <Typography variant="subtitle2" fontWeight={600} gutterBottom>Network Optimization</Typography>
                <Typography variant="body2" color="text.secondary">
                  Measure actual network leakage and predict provider response to network restrictions.
                </Typography>
              </Paper>
            </Grid>
          </Grid>
        </Box>
      )
    case 'architecture':
      return (
        <Box>
          <Typography variant="h4" gutterBottom sx={{ mb: 2, fontWeight: 700 }}>
            System Architecture
          </Typography>
          <Typography variant="body1" paragraph sx={{ mb: 4 }}>
            HealthForesight is built on a modular, file-based architecture designed for enterprise scalability, traceability, and continuous learning.
          </Typography>
          
          {/* Architecture Diagram */}
          <Paper variant="outlined" sx={{ p: 4, mb: 4, bgcolor: 'grey.50' }}>
            <Typography variant="h6" gutterBottom sx={{ mb: 3, fontWeight: 600 }}>
              System Architecture Overview
            </Typography>
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px', position: 'relative' }}>
              <svg width="100%" height="400" viewBox="0 0 1000 400" style={{ maxWidth: '100%' }}>
                {/* Data Sources */}
                <rect x="50" y="50" width="150" height="80" rx="5" fill="#e3f2fd" stroke="#1976d2" strokeWidth="2" />
                <text x="125" y="85" textAnchor="middle" fontSize="14" fontWeight="600">Data Sources</text>
                <text x="125" y="105" textAnchor="middle" fontSize="11">Claims, Enrollment</text>
                <text x="125" y="120" textAnchor="middle" fontSize="11">Providers, Networks</text>
                
                {/* Arrow */}
                <path d="M 200 90 L 250 90" stroke="#1976d2" strokeWidth="2" markerEnd="url(#arrowhead)" />
                
                {/* Ingestion Layer */}
                <rect x="250" y="50" width="150" height="80" rx="5" fill="#f3e5f5" stroke="#7b1fa2" strokeWidth="2" />
                <text x="325" y="85" textAnchor="middle" fontSize="14" fontWeight="600">Ingestion</text>
                <text x="325" y="105" textAnchor="middle" fontSize="11">Schema Validation</text>
                <text x="325" y="120" textAnchor="middle" fontSize="11">Data Periods</text>
                
                {/* Arrow */}
                <path d="M 400 90 L 450 90" stroke="#7b1fa2" strokeWidth="2" markerEnd="url(#arrowhead)" />
                
                {/* Analytics Engine */}
                <rect x="450" y="20" width="200" height="140" rx="5" fill="#e8f5e9" stroke="#388e3c" strokeWidth="2" />
                <text x="550" y="50" textAnchor="middle" fontSize="14" fontWeight="600">Analytics Engine</text>
                <rect x="470" y="60" width="160" height="30" rx="3" fill="#fff" stroke="#388e3c" strokeWidth="1" />
                <text x="550" y="80" textAnchor="middle" fontSize="11">Baseline Analysis</text>
                <rect x="470" y="100" width="160" height="30" rx="3" fill="#fff" stroke="#388e3c" strokeWidth="1" />
                <text x="550" y="120" textAnchor="middle" fontSize="11">Impact Prediction</text>
                <rect x="470" y="140" width="160" height="15" rx="3" fill="#fff" stroke="#388e3c" strokeWidth="1" />
                <text x="550" y="150" textAnchor="middle" fontSize="11">Observation</text>
                
                {/* Arrow */}
                <path d="M 650 90 L 700 90" stroke="#388e3c" strokeWidth="2" markerEnd="url(#arrowhead)" />
                
                {/* Learning Loop */}
                <rect x="700" y="50" width="150" height="80" rx="5" fill="#fff3e0" stroke="#f57c00" strokeWidth="2" />
                <text x="775" y="85" textAnchor="middle" fontSize="14" fontWeight="600">Learning Loop</text>
                <text x="775" y="105" textAnchor="middle" fontSize="11">Elasticity Updates</text>
                <text x="775" y="120" textAnchor="middle" fontSize="11">Accuracy Tracking</text>
                
                {/* Policy Management */}
                <rect x="250" y="180" width="150" height="80" rx="5" fill="#fce4ec" stroke="#c2185b" strokeWidth="2" />
                <text x="325" y="215" textAnchor="middle" fontSize="14" fontWeight="600">Policy</text>
                <text x="325" y="235" textAnchor="middle" fontSize="11">Management</text>
                <text x="325" y="250" textAnchor="middle" fontSize="11">Versioning</text>
                
                {/* Connection from Policy to Analytics */}
                <path d="M 325 260 L 450 180" stroke="#c2185b" strokeWidth="2" strokeDasharray="5,5" />
                <circle cx="450" cy="180" r="3" fill="#c2185b" />
                
                {/* API Layer */}
                <rect x="450" y="200" width="200" height="60" rx="5" fill="#e1f5fe" stroke="#0277bd" strokeWidth="2" />
                <text x="550" y="230" textAnchor="middle" fontSize="14" fontWeight="600">REST API</text>
                <text x="550" y="250" textAnchor="middle" fontSize="11">FastAPI • OpenAPI 3.0</text>
                
                {/* UI Layer */}
                <rect x="700" y="180" width="150" height="80" rx="5" fill="#f1f8e9" stroke="#689f38" strokeWidth="2" />
                <text x="775" y="215" textAnchor="middle" fontSize="14" fontWeight="600">Web UI</text>
                <text x="775" y="235" textAnchor="middle" fontSize="11">React • TypeScript</text>
                <text x="775" y="250" textAnchor="middle" fontSize="11">Material-UI</text>
                
                {/* Arrow from API to UI */}
                <path d="M 650 230 L 700 220" stroke="#0277bd" strokeWidth="2" markerEnd="url(#arrowhead)" />
                
                {/* Storage Layer */}
                <rect x="50" y="320" width="200" height="60" rx="5" fill="#fafafa" stroke="#616161" strokeWidth="2" />
                <text x="150" y="350" textAnchor="middle" fontSize="14" fontWeight="600">File Storage</text>
                <text x="150" y="370" textAnchor="middle" fontSize="11">JSON • Parquet • Local/S3</text>
                
                {/* Connection from Analytics to Storage */}
                <path d="M 550 160 L 450 320" stroke="#616161" strokeWidth="2" strokeDasharray="5,5" />
                <circle cx="450" cy="320" r="3" fill="#616161" />
                
                {/* Arrow marker definition */}
                <defs>
                  <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
                    <polygon points="0 0, 10 3, 0 6" fill="#1976d2" />
                  </marker>
                </defs>
              </svg>
            </Box>
          </Paper>
          
          <Typography variant="h6" gutterBottom sx={{ mt: 4, mb: 3, fontWeight: 600 }}>
            Core Components
          </Typography>
          
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom color="primary" sx={{ fontWeight: 600 }}>
                    1. Data Period Management
                  </Typography>
                  <Typography variant="body2" paragraph>
                    Tracks and versions data snapshots over time, linking them to ingestions and determining baseline eligibility.
                    Each data period is immutable and versioned, ensuring full traceability of all analyses.
                  </Typography>
                  <Box sx={{ mt: 2 }}>
                    <Chip label="Immutable" size="small" sx={{ mr: 1 }} />
                    <Chip label="Versioned" size="small" sx={{ mr: 1 }} />
                    <Chip label="Traceable" size="small" />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom color="primary" sx={{ fontWeight: 600 }}>
                    2. Policy Lifecycle Management
                  </Typography>
                  <Typography variant="body2" paragraph>
                    Manages policy versions, lifecycle states (DRAFT → ACTIVE → PAUSED → RETIRED), and tracks changes.
                    Supports complex policy definitions with multiple levers, conditions, and exceptions.
                  </Typography>
                  <Box sx={{ mt: 2 }}>
                    <Chip label="Versioned" size="small" sx={{ mr: 1 }} />
                    <Chip label="Auditable" size="small" sx={{ mr: 1 }} />
                    <Chip label="Complex Logic" size="small" />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom color="primary" sx={{ fontWeight: 600 }}>
                    3. Baseline Management
                  </Typography>
                  <Typography variant="body2" paragraph>
                    Establishes and refreshes baselines as new data arrives, with automatic shift detection and versioning.
                    Computes comprehensive metrics including utilization rates, cost PMPM, provider archetypes, and time series.
                  </Typography>
                  <Box sx={{ mt: 2 }}>
                    <Chip label="Auto-refresh" size="small" sx={{ mr: 1 }} />
                    <Chip label="Shift Detection" size="small" sx={{ mr: 1 }} />
                    <Chip label="Versioned" size="small" />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom color="primary" sx={{ fontWeight: 600 }}>
                    4. Predicted Impact Management
                  </Typography>
                  <Typography variant="body2" paragraph>
                    Generates and versions predicted impacts using elasticity and behavioral models, with confidence scoring.
                    Integrates with learning loop to use latest elasticity coefficients and model versions.
                  </Typography>
                  <Box sx={{ mt: 2 }}>
                    <Chip label="ML-Driven" size="small" sx={{ mr: 1 }} />
                    <Chip label="Confidence Scored" size="small" sx={{ mr: 1 }} />
                    <Chip label="Auto-updated" size="small" />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom color="primary" sx={{ fontWeight: 600 }}>
                    5. Observed Impact Tracking
                  </Typography>
                  <Typography variant="body2" paragraph>
                    Measures actual outcomes using causal methods (DiD, ITS) and compares against baseline and predictions.
                    Provides behavioral explanations including substitution patterns, provider responses, and patient segmentation.
                  </Typography>
                  <Box sx={{ mt: 2 }}>
                    <Chip label="Causal Methods" size="small" sx={{ mr: 1 }} />
                    <Chip label="Comparison Analysis" size="small" sx={{ mr: 1 }} />
                    <Chip label="Behavioral Insights" size="small" />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom color="primary" sx={{ fontWeight: 600 }}>
                    6. Learning Loop System
                  </Typography>
                  <Typography variant="body2" paragraph>
                    Continuously updates elasticity models based on observed outcomes, tracking prediction accuracy.
                    Automatically triggers model refresh when sufficient observations (≥3) are available.
                  </Typography>
                  <Box sx={{ mt: 2 }}>
                    <Chip label="Auto-learning" size="small" sx={{ mr: 1 }} />
                    <Chip label="Accuracy Tracking" size="small" sx={{ mr: 1 }} />
                    <Chip label="Model Versioning" size="small" />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Box>
      )
    default:
      return <Typography>Content coming soon...</Typography>
  }
}

function renderArchitecture(subsection: string) {
  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: 4, fontWeight: 700 }}>
        System Architecture
      </Typography>
      <Typography variant="body1" paragraph sx={{ mb: 4 }}>
        Comprehensive architecture documentation covering components, data flows, and deployment patterns.
      </Typography>
      <Alert severity="info" sx={{ mb: 4 }}>
        <AlertTitle>Architecture Overview</AlertTitle>
        HealthForesight uses a modular, microservices-inspired architecture with file-based storage for local development and S3-compatible object storage for production deployments.
      </Alert>
      <Typography variant="body1">
        Detailed architecture documentation coming soon. See Overview → Architecture for initial content.
      </Typography>
    </Box>
  )
}

function renderModels(subsection: string) {
  const modelContent: Record<string, React.ReactNode> = {
    baseline: (
      <Box>
        <Typography variant="h4" gutterBottom sx={{ mb: 3, fontWeight: 700 }}>
          Baseline Analysis Model
        </Typography>
        <Typography variant="body1" paragraph sx={{ mb: 4 }}>
          The Baseline Analysis Model establishes the "normal" state of utilization and behavior before policy implementation.
          It uses time series decomposition, statistical benchmarking, and unsupervised learning to profile historical patterns.
        </Typography>

        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>Time Series Decomposition (STL)</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" paragraph>
              <strong>Method:</strong> Seasonal and Trend decomposition using Loess (STL) from statsmodels
            </Typography>
            <Typography variant="body2" paragraph>
              <strong>Purpose:</strong> Separates time series into trend, seasonal, and residual components to understand underlying patterns
            </Typography>
            <Typography variant="body2" paragraph>
              <strong>Parameters:</strong>
            </Typography>
            <Box component="ul" sx={{ pl: 4 }}>
              <li><strong>seasonal_period:</strong> 12 for monthly data, 4 for quarterly (must be odd integer ≥ 3)</li>
              <li><strong>robust:</strong> True to handle outliers</li>
              <li><strong>Fallback:</strong> Simple moving average trend if insufficient data points (less than 2×seasonal_period)</li>
            </Box>
            <Typography variant="body2" paragraph sx={{ mt: 2 }}>
              <strong>Output:</strong> For each time point: observed, trend, seasonal, residual, confidence bounds (95%)
            </Typography>
          </AccordionDetails>
        </Accordion>

        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>Provider Segmentation (K-Means Clustering)</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" paragraph>
              <strong>Algorithm:</strong> K-Means clustering with feature standardization (StandardScaler)
            </Typography>
            <Typography variant="body2" paragraph>
              <strong>Features:</strong>
            </Typography>
            <Box component="ul" sx={{ pl: 4 }}>
              <li>Total claims per provider</li>
              <li>Total cost per provider</li>
              <li>Average cost per claim</li>
              <li>Claims per member</li>
            </Box>
            <Typography variant="body2" paragraph sx={{ mt: 2 }}>
              <strong>Output:</strong> Provider archetypes with characteristics and representative providers
            </Typography>
            <Typography variant="body2" paragraph>
              <strong>Default Clusters:</strong> 5 (configurable via n_clusters parameter)
            </Typography>
          </AccordionDetails>
        </Accordion>

        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>Benchmark Calculation</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" paragraph>
              Computes utilization and cost benchmarks segmented by LOB, market, service category, and site of care.
            </Typography>
            <Typography variant="body2" paragraph>
              <strong>Metrics Computed:</strong>
            </Typography>
            <Box component="ul" sx={{ pl: 4 }}>
              <li>Utilization rate per 1,000 member-months (M1)</li>
              <li>Allowed PMPM (M2)</li>
              <li>Paid PMPM (M3)</li>
              <li>Site of care mix percentages</li>
              <li>Service mix percentages</li>
            </Box>
          </AccordionDetails>
        </Accordion>
      </Box>
    ),
    elasticity: (
      <Box>
        <Typography variant="h4" gutterBottom sx={{ mb: 3, fontWeight: 700 }}>
          Elasticity Modeling
        </Typography>
        <Typography variant="body1" paragraph sx={{ mb: 4 }}>
          Elasticity models estimate how utilization responds to policy friction (prior auth requirements, cost sharing, etc.).
          Models are continuously updated based on observed outcomes through the learning loop.
        </Typography>

        <Alert severity="info" sx={{ mb: 4 }}>
          <AlertTitle>Elasticity Coefficient</AlertTitle>
          Elasticity is negative (demand decreases with friction). Example: -0.35 means a 10% increase in friction leads to a 3.5% decrease in utilization.
        </Alert>

        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" gutterBottom>Default Elasticity by Policy Type</Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell><strong>Policy Type</strong></TableCell>
                        <TableCell align="right"><strong>Elasticity</strong></TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      <TableRow>
                        <TableCell>Prior Authorization</TableCell>
                        <TableCell align="right">-0.35</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Duration/Frequency Limit</TableCell>
                        <TableCell align="right">-0.40</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Cost Sharing</TableCell>
                        <TableCell align="right">-0.30</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Site of Care</TableCell>
                        <TableCell align="right">-0.25</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Network Restriction</TableCell>
                        <TableCell align="right">-0.20</TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" gutterBottom>Model Update Process</Typography>
                <Box component="ol" sx={{ pl: 2 }}>
                  <li>Observation created with observed vs predicted comparison</li>
                  <li>Prediction accuracy recorded automatically</li>
                  <li>When ≥3 observations exist, elasticity model updated</li>
                  <li>New coefficients calculated using observed/predicted ratios</li>
                  <li>Model version incremented</li>
                  <li>Affected policies marked for prediction refresh</li>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    ),
    impact: (
      <Box>
        <Typography variant="h4" gutterBottom sx={{ mb: 3, fontWeight: 700 }}>
          Impact Analysis Models
        </Typography>
        <Typography variant="body1" paragraph sx={{ mb: 4 }}>
          Impact analysis uses causal inference methods to measure actual policy effects, controlling for confounders and market events.
        </Typography>

        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>Difference-in-Differences (DiD)</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" paragraph>
              <strong>Formula:</strong> Impact = (Treatment_post - Treatment_pre) - (Control_post - Control_pre)
            </Typography>
            <Typography variant="body2" paragraph>
              <strong>Assumptions:</strong> Parallel trends (treatment and control groups follow similar trends pre-policy)
            </Typography>
            <Typography variant="body2" paragraph>
              <strong>Use Case:</strong> When control group available (same market, different LOB, or similar population)
            </Typography>
          </AccordionDetails>
        </Accordion>

        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>Interrupted Time Series (ITS)</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" paragraph>
              <strong>Method:</strong> Segmented regression with pre/post policy periods
            </Typography>
            <Typography variant="body2" paragraph>
              <strong>Use Case:</strong> When control group not available, uses historical baseline as counterfactual
            </Typography>
            <Typography variant="body2" paragraph>
              <strong>Controls for:</strong> Seasonality, trend, confounder events (via confounder calendar)
            </Typography>
          </AccordionDetails>
        </Accordion>
      </Box>
    ),
    substitution: (
      <Box>
        <Typography variant="h4" gutterBottom sx={{ mb: 3, fontWeight: 700 }}>
          Substitution Detection Model
        </Typography>
        <Typography variant="body1" paragraph>
          Detects when patients substitute restricted services with alternative services (e.g., ER visits when prior auth required).
        </Typography>
        <Typography variant="body2" paragraph sx={{ mt: 2 }}>
          <strong>Methods:</strong>
        </Typography>
        <Box component="ul" sx={{ pl: 4 }}>
          <li>Rule-based classification (temporal proximity, service category relationships)</li>
          <li>Statistical ranking (Chi-square test for independence)</li>
          <li>Lag analysis (detects timing shifts)</li>
          <li>Top pathway identification</li>
        </Box>
      </Box>
    ),
    clustering: (
      <Box>
        <Typography variant="h4" gutterBottom sx={{ mb: 3, fontWeight: 700 }}>
          Provider Clustering (K-Means)
        </Typography>
        <Typography variant="body1" paragraph>
          Groups providers into archetypes based on practice patterns using unsupervised learning.
        </Typography>
        <Typography variant="body2" paragraph sx={{ mt: 2 }}>
          <strong>Process:</strong>
        </Typography>
        <Box component="ol" sx={{ pl: 4 }}>
          <li>Extract provider features (utilization intensity, cost per claim, member concentration)</li>
          <li>Standardize features (StandardScaler)</li>
          <li>Apply K-Means clustering (default: 5 clusters)</li>
          <li>Label archetypes (Compliant, Adaptive, Resistant, Circumvention-prone, High-volume)</li>
          <li>Identify representative providers per archetype</li>
        </Box>
      </Box>
    ),
    'time-series': (
      <Box>
        <Typography variant="h4" gutterBottom sx={{ mb: 3, fontWeight: 700 }}>
          Time Series Analysis (STL Decomposition)
        </Typography>
        <Typography variant="body1" paragraph>
          Decomposes time series into trend, seasonal, and residual components for baseline projection and anomaly detection.
        </Typography>
        <Paper variant="outlined" sx={{ p: 3, mt: 3, bgcolor: 'grey.50' }}>
          <Typography variant="body2" paragraph>
            <strong>Implementation:</strong> statsmodels.tsa.seasonal.STL
          </Typography>
          <Typography variant="body2" paragraph>
            <strong>Fallback:</strong> Simple moving average if insufficient data points
          </Typography>
        </Paper>
      </Box>
    ),
    whatif: (
      <Box>
        <Typography variant="h4" gutterBottom sx={{ mb: 3, fontWeight: 700 }}>
          What-If Scenario Simulation
        </Typography>
        <Typography variant="body1" paragraph>
          Simulates policy impact with adjusted parameters using elasticity curves and Monte Carlo methods.
        </Typography>
        <Typography variant="body2" paragraph sx={{ mt: 2 }}>
          <strong>Process:</strong>
        </Typography>
        <Box component="ol" sx={{ pl: 4 }}>
          <li>Load baseline claims and metrics</li>
          <li>Apply policy parameter adjustments (lever settings, friction levels)</li>
          <li>Project utilization changes using elasticity curves</li>
          <li>Project cost changes accounting for utilization and inflation</li>
          <li>Run Monte Carlo simulation (1,000 iterations) for confidence intervals</li>
          <li>Compute tradeoff analysis (efficiency score, cost vs utilization tradeoffs)</li>
          <li>Compute risk analysis (worst-case, best-case scenarios)</li>
        </Box>
      </Box>
    ),
  }

  return modelContent[subsection] || (
    <Typography>Select a model section from the sidebar to view detailed documentation.</Typography>
  )
}

function renderMetrics(subsection: string) {
  if (subsection === 'dictionary') {
    return (
      <Box>
        <Typography variant="h4" gutterBottom sx={{ mb: 3, fontWeight: 700 }}>
          Metric Dictionary
        </Typography>
        <Typography variant="body1" paragraph sx={{ mb: 4 }}>
          Comprehensive definitions of all metrics used in baseline, predicted, and observed impact analyses.
          All metrics follow standardized naming, formulas, denominators, and units.
        </Typography>
        
        <Alert severity="info" sx={{ mb: 4 }}>
          <AlertTitle>Metric Categories</AlertTitle>
          Metrics are organized into: Denominators (D1-D3), Primary Outcomes (M1-M7), Mix Metrics (M8-M13), 
          Substitution/Spillover (M14-M16), Behavioral Attribution (M17-M19), and Learning Metrics (M20-M22).
        </Alert>
      </Box>
    )
  }

  if (subsection === 'denominators') {
    return (
      <Box>
        <Typography variant="h4" gutterBottom sx={{ mb: 3, fontWeight: 700 }}>
          Denominator Metrics (D1-D3)
        </Typography>
        <Typography variant="body1" paragraph sx={{ mb: 4 }}>
          Denominator definitions used for rate calculations across all analyses.
        </Typography>

        <TableContainer component={Paper} variant="outlined">
          <Table>
            <TableHead>
              <TableRow sx={{ bgcolor: 'grey.100' }}>
                <TableCell><strong>Metric ID</strong></TableCell>
                <TableCell><strong>Name</strong></TableCell>
                <TableCell><strong>Formula</strong></TableCell>
                <TableCell><strong>Unit</strong></TableCell>
                <TableCell><strong>Source</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              <TableRow>
                <TableCell>D1</TableCell>
                <TableCell>Member-Months</TableCell>
                <TableCell>Σ over members (number of months enrolled in period)</TableCell>
                <TableCell>member-months</TableCell>
                <TableCell>enrollment_table</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>D2</TableCell>
                <TableCell>Unique Members</TableCell>
                <TableCell>COUNT(DISTINCT member_id) with ≥1 eligible day</TableCell>
                <TableCell>members</TableCell>
                <TableCell>enrollment_table</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>D3</TableCell>
                <TableCell>Policy-Eligible Member-Months</TableCell>
                <TableCell>member_months restricted to policy scope filters</TableCell>
                <TableCell>member-months</TableCell>
                <TableCell>enrollment_table</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
    )
  }

  if (subsection === 'primary') {
    return (
      <Box>
        <Typography variant="h4" gutterBottom sx={{ mb: 3, fontWeight: 700 }}>
          Primary Outcome Metrics (M1-M7)
        </Typography>
        <Typography variant="body1" paragraph sx={{ mb: 4 }}>
          Core metrics computed in baseline, predicted, and observed impact analyses.
        </Typography>

        <TableContainer component={Paper} variant="outlined">
          <Table>
            <TableHead>
              <TableRow sx={{ bgcolor: 'grey.100' }}>
                <TableCell><strong>ID</strong></TableCell>
                <TableCell><strong>Name</strong></TableCell>
                <TableCell><strong>Formula</strong></TableCell>
                <TableCell><strong>Denominator</strong></TableCell>
                <TableCell><strong>Unit</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              <TableRow>
                <TableCell>M1</TableCell>
                <TableCell>Total Utilization Rate per 1,000 Member-Months</TableCell>
                <TableCell>(total_claim_lines / member_months) × 1000</TableCell>
                <TableCell>member_months</TableCell>
                <TableCell>per 1K MM</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>M2</TableCell>
                <TableCell>Target Utilization Rate per 1,000 Member-Months</TableCell>
                <TableCell>(target_claim_lines / policy_eligible_member_months) × 1000</TableCell>
                <TableCell>policy_eligible_member_months</TableCell>
                <TableCell>per 1K MM</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>M3</TableCell>
                <TableCell>Total Allowed PMPM</TableCell>
                <TableCell>total_allowed_amount / member_months</TableCell>
                <TableCell>member_months</TableCell>
                <TableCell>$ PMPM</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>M4</TableCell>
                <TableCell>Target Allowed PMPM</TableCell>
                <TableCell>target_allowed_amount / policy_eligible_member_months</TableCell>
                <TableCell>policy_eligible_member_months</TableCell>
                <TableCell>$ PMPM</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>M5</TableCell>
                <TableCell>Total Paid PMPM</TableCell>
                <TableCell>total_paid_amount / member_months</TableCell>
                <TableCell>member_months</TableCell>
                <TableCell>$ PMPM</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>M6</TableCell>
                <TableCell>Unique Members</TableCell>
                <TableCell>COUNT(DISTINCT member_id)</TableCell>
                <TableCell>N/A</TableCell>
                <TableCell>count</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>M7</TableCell>
                <TableCell>Allowed Total Annualized</TableCell>
                <TableCell>(total_allowed_amount / months_in_period) × 12</TableCell>
                <TableCell>period_months</TableCell>
                <TableCell>$ per year</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
    )
  }

  return <Typography>Select a metrics section to view detailed definitions.</Typography>
}

function renderTechnical(subsection: string) {
  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: 4, fontWeight: 700 }}>
        Technical Documentation
      </Typography>
      <Typography variant="body1">
        Technical documentation covering API endpoints, data models, algorithms, and integrations.
      </Typography>
    </Box>
  )
}

function renderDataSpecs(subsection: string) {
  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: 4, fontWeight: 700 }}>
        Data Specifications
      </Typography>
      <Typography variant="body1">
        Source data schemas, contracts, and quality requirements.
      </Typography>
    </Box>
  )
}
