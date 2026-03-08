/**
 * Data Specifications Page
 * Shows expected data formats and input specifications for payer clients
 */
import { Box, Typography, Paper, Accordion, AccordionSummary, AccordionDetails, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip, Alert } from '@mui/material'
import { ExpandMore as ExpandMoreIcon, FileUpload as FileUploadIcon } from '@mui/icons-material'
import { healthForesightColors } from '../theme/healthForesightTheme'

export default function DataSpecificationsPage() {
  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <FileUploadIcon fontSize="large" />
        <Box>
          <Typography
            variant="h4"
            component="h1"
            sx={{
              fontFamily: 'IBM Plex Sans, Inter, sans-serif',
              fontWeight: 600,
              mb: 1,
              color: healthForesightColors.neutral.dark,
            }}
          >
            Data Specifications
          </Typography>
          <Typography
            variant="body1"
            sx={{
              color: healthForesightColors.neutral.mid,
              lineHeight: 1.6,
            }}
          >
            Expected data formats and schema requirements for payer-provided datasets. Review canonical data contracts and validation rules.
          </Typography>
        </Box>
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        All datasets must be provided in CSV or Parquet format. Use deterministic file naming conventions and include manifest.json for batch ingestion.
      </Alert>

      {/* Claims Lines Dataset */}
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">1. Claims Lines Dataset (Required)</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Box>
            <Typography variant="body2" color="text.secondary" paragraph>
              The claims lines dataset is the core dataset for utilization analysis. Required fields must be present for all records.
            </Typography>
            
            <TableContainer component={Paper} variant="outlined" sx={{ mb: 2 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Field</strong></TableCell>
                    <TableCell><strong>Type</strong></TableCell>
                    <TableCell><strong>Required</strong></TableCell>
                    <TableCell><strong>Description</strong></TableCell>
                    <TableCell><strong>Example</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>member_id</TableCell>
                    <TableCell>string</TableCell>
                    <TableCell><Chip label="Required" size="small" color="error" /></TableCell>
                    <TableCell>Unique member identifier</TableCell>
                    <TableCell>MEM_12345678</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>claim_id</TableCell>
                    <TableCell>string</TableCell>
                    <TableCell><Chip label="Required" size="small" color="error" /></TableCell>
                    <TableCell>Unique claim identifier</TableCell>
                    <TableCell>CLM_987654321</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>claim_line_id</TableCell>
                    <TableCell>string</TableCell>
                    <TableCell><Chip label="Required" size="small" color="error" /></TableCell>
                    <TableCell>Unique claim line identifier</TableCell>
                    <TableCell>CLM_987654321_L1</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>service_date</TableCell>
                    <TableCell>date (YYYY-MM-DD)</TableCell>
                    <TableCell><Chip label="Required" size="small" color="error" /></TableCell>
                    <TableCell>Date of service</TableCell>
                    <TableCell>2024-01-15</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>paid_date</TableCell>
                    <TableCell>date (YYYY-MM-DD)</TableCell>
                    <TableCell><Chip label="Required" size="small" color="error" /></TableCell>
                    <TableCell>Date claim was paid</TableCell>
                    <TableCell>2024-03-01</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>lob</TableCell>
                    <TableCell>enum</TableCell>
                    <TableCell><Chip label="Required" size="small" color="error" /></TableCell>
                    <TableCell>Line of business: COMMERCIAL, MA, MEDICAID</TableCell>
                    <TableCell>COMMERCIAL</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>market</TableCell>
                    <TableCell>string</TableCell>
                    <TableCell><Chip label="Required" size="small" color="error" /></TableCell>
                    <TableCell>Geographic market identifier</TableCell>
                    <TableCell>NYC, DFW, BOS</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>cpt_code</TableCell>
                    <TableCell>string</TableCell>
                    <TableCell><Chip label="Required" size="small" color="error" /></TableCell>
                    <TableCell>CPT or HCPCS procedure code</TableCell>
                    <TableCell>72148, 97110</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>service_category</TableCell>
                    <TableCell>string</TableCell>
                    <TableCell><Chip label="Recommended" size="small" color="warning" /></TableCell>
                    <TableCell>Service category: MRI, CT, PT, INFUSION, ER, UC</TableCell>
                    <TableCell>MRI</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>place_of_service</TableCell>
                    <TableCell>string</TableCell>
                    <TableCell><Chip label="Recommended" size="small" color="warning" /></TableCell>
                    <TableCell>Place of service code (11=Office, 22=Hospital OP, 23=ER)</TableCell>
                    <TableCell>11, 22, 23</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>units</TableCell>
                    <TableCell>float</TableCell>
                    <TableCell><Chip label="Required" size="small" color="error" /></TableCell>
                    <TableCell>Service units (visits, days, etc.)</TableCell>
                    <TableCell>1.0, 2.5</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>allowed_amount</TableCell>
                    <TableCell>float</TableCell>
                    <TableCell><Chip label="Required" size="small" color="error" /></TableCell>
                    <TableCell>Allowed amount (billed amount)</TableCell>
                    <TableCell>1250.00</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>paid_amount</TableCell>
                    <TableCell>float</TableCell>
                    <TableCell><Chip label="Required" size="small" color="error" /></TableCell>
                    <TableCell>Amount actually paid</TableCell>
                    <TableCell>1100.00</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>in_network</TableCell>
                    <TableCell>boolean</TableCell>
                    <TableCell><Chip label="Required" size="small" color="error" /></TableCell>
                    <TableCell>Whether provider is in-network</TableCell>
                    <TableCell>true, false</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>provider_id</TableCell>
                    <TableCell>string</TableCell>
                    <TableCell><Chip label="Recommended" size="small" color="warning" /></TableCell>
                    <TableCell>Provider identifier (NPI or internal ID)</TableCell>
                    <TableCell>PROV_123456</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>diag_1</TableCell>
                    <TableCell>string</TableCell>
                    <TableCell><Chip label="Optional" size="small" /></TableCell>
                    <TableCell>Primary diagnosis code (ICD-10)</TableCell>
                    <TableCell>M54.5</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>modifier_1</TableCell>
                    <TableCell>string</TableCell>
                    <TableCell><Chip label="Optional" size="small" /></TableCell>
                    <TableCell>CPT modifier code</TableCell>
                    <TableCell>26, TC, 59</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>

            <Alert severity="warning" sx={{ mb: 2 }}>
              <strong>File Naming:</strong> Use format <code>claims_lines_YYYYMM.csv</code> or <code>claims_lines_YYYYMM.parquet</code> for monthly partitions.
            </Alert>

            <Typography variant="subtitle2" gutterBottom>
              Example File Structure (CSV):
            </Typography>
            <Paper sx={{ p: 2, bgcolor: 'grey.50', fontFamily: 'monospace', fontSize: '0.875rem' }}>
              <pre>{`member_id,claim_id,claim_line_id,service_date,paid_date,lob,market,cpt_code,service_category,place_of_service,units,allowed_amount,paid_amount,in_network
MEM_000001,CLM_001,L1,2024-01-15,2024-03-01,COMMERCIAL,NYC,72148,MRI,11,1.0,1250.00,1100.00,true
MEM_000002,CLM_002,L1,2024-01-20,2024-03-05,COMMERCIAL,DFW,97110,PT,11,1.0,150.00,140.00,true`}</pre>
            </Paper>
          </Box>
        </AccordionDetails>
      </Accordion>

      {/* Member Enrollment Dataset */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">2. Member Enrollment Dataset (Required)</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Box>
            <Typography variant="body2" color="text.secondary" paragraph>
              Monthly enrollment snapshots for denominator calculations (per-1k metrics, cohort creation, risk stratification).
            </Typography>
            
            <TableContainer component={Paper} variant="outlined" sx={{ mb: 2 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Field</strong></TableCell>
                    <TableCell><strong>Type</strong></TableCell>
                    <TableCell><strong>Required</strong></TableCell>
                    <TableCell><strong>Description</strong></TableCell>
                    <TableCell><strong>Example</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>member_id</TableCell>
                    <TableCell>string</TableCell>
                    <TableCell><Chip label="Required" size="small" color="error" /></TableCell>
                    <TableCell>Unique member identifier (must match claims)</TableCell>
                    <TableCell>MEM_12345678</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>lob</TableCell>
                    <TableCell>enum</TableCell>
                    <TableCell><Chip label="Required" size="small" color="error" /></TableCell>
                    <TableCell>COMMERCIAL, MA, MEDICAID</TableCell>
                    <TableCell>COMMERCIAL</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>market</TableCell>
                    <TableCell>string</TableCell>
                    <TableCell><Chip label="Required" size="small" color="error" /></TableCell>
                    <TableCell>Geographic market</TableCell>
                    <TableCell>NYC, DFW, BOS</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>enrollment_month</TableCell>
                    <TableCell>string (YYYY-MM)</TableCell>
                    <TableCell><Chip label="Required" size="small" color="error" /></TableCell>
                    <TableCell>Month of enrollment snapshot</TableCell>
                    <TableCell>2024-01</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>age_band</TableCell>
                    <TableCell>string</TableCell>
                    <TableCell><Chip label="Recommended" size="small" color="warning" /></TableCell>
                    <TableCell>0-17, 18-34, 35-49, 50-64, 65+</TableCell>
                    <TableCell>35-49</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>gender</TableCell>
                    <TableCell>enum</TableCell>
                    <TableCell><Chip label="Optional" size="small" /></TableCell>
                    <TableCell>M, F, U</TableCell>
                    <TableCell>M</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>risk_score</TableCell>
                    <TableCell>float</TableCell>
                    <TableCell><Chip label="Recommended" size="small" color="warning" /></TableCell>
                    <TableCell>Member risk score (0.5-3.0)</TableCell>
                    <TableCell>1.25</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>network_tier</TableCell>
                    <TableCell>enum</TableCell>
                    <TableCell><Chip label="Optional" size="small" /></TableCell>
                    <TableCell>STANDARD, NARROW</TableCell>
                    <TableCell>STANDARD</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>enrolled_flag</TableCell>
                    <TableCell>boolean</TableCell>
                    <TableCell><Chip label="Required" size="small" color="error" /></TableCell>
                    <TableCell>Whether member is enrolled this month</TableCell>
                    <TableCell>true</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>

            <Alert severity="info">
              <strong>File Naming:</strong> Use format <code>enrollment_monthly.csv</code> or <code>enrollment_monthly.parquet</code>. Include all months in a single file or partition by month.
            </Alert>
          </Box>
        </AccordionDetails>
      </Accordion>

      {/* Provider Directory Dataset */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">3. Provider Directory Dataset (Required)</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Box>
            <Typography variant="body2" color="text.secondary" paragraph>
              Provider directory for segmentation, behavior modeling, and site-of-care analysis.
            </Typography>
            
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Field</strong></TableCell>
                    <TableCell><strong>Type</strong></TableCell>
                    <TableCell><strong>Description</strong></TableCell>
                    <TableCell><strong>Example</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>provider_id</TableCell>
                    <TableCell>string</TableCell>
                    <TableCell>Unique provider identifier (must match claims)</TableCell>
                    <TableCell>PROV_123456</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>npi</TableCell>
                    <TableCell>string</TableCell>
                    <TableCell>National Provider Identifier (10 digits)</TableCell>
                    <TableCell>1234567890</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>provider_type</TableCell>
                    <TableCell>enum</TableCell>
                    <TableCell>PHYSICIAN, FACILITY</TableCell>
                    <TableCell>PHYSICIAN</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>specialty</TableCell>
                    <TableCell>string</TableCell>
                    <TableCell>Provider specialty: RADIOLOGY, ONCOLOGY, PT, PRIMARY_CARE, ER, ORTHOPEDICS</TableCell>
                    <TableCell>RADIOLOGY</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>facility_type</TableCell>
                    <TableCell>string</TableCell>
                    <TableCell>HOSPITAL_OP, FREESTANDING, ASC, ER, OFFICE</TableCell>
                    <TableCell>FREESTANDING</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>market</TableCell>
                    <TableCell>string</TableCell>
                    <TableCell>Geographic market</TableCell>
                    <TableCell>NYC</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>network_status</TableCell>
                    <TableCell>enum</TableCell>
                    <TableCell>IN, OUT</TableCell>
                    <TableCell>IN</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>system_affiliation</TableCell>
                    <TableCell>string</TableCell>
                    <TableCell>Provider system/group affiliation (optional)</TableCell>
                    <TableCell>SYSTEM_001</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        </AccordionDetails>
      </Accordion>

      {/* Policy Events Dataset */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">4. Policy Events Dataset (Required for Pre/Post Analysis)</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Box>
            <Typography variant="body2" color="text.secondary" paragraph>
              Policy activation/modification/retirement events for pre/post analysis. Critical for causal impact measurement.
            </Typography>
            
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Field</strong></TableCell>
                    <TableCell><strong>Type</strong></TableCell>
                    <TableCell><strong>Description</strong></TableCell>
                    <TableCell><strong>Example</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>policy_id</TableCell>
                    <TableCell>string</TableCell>
                    <TableCell>Unique policy identifier</TableCell>
                    <TableCell>POL_001</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>event_type</TableCell>
                    <TableCell>enum</TableCell>
                    <TableCell>ACTIVATED, MODIFIED, RETIRED</TableCell>
                    <TableCell>ACTIVATED</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>event_date</TableCell>
                    <TableCell>date (YYYY-MM-DD)</TableCell>
                    <TableCell>Date policy event occurred</TableCell>
                    <TableCell>2024-07-01</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>change_description</TableCell>
                    <TableCell>string</TableCell>
                    <TableCell>Human-readable description of change</TableCell>
                    <TableCell>Require PA for outpatient MRI</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        </AccordionDetails>
      </Accordion>

      {/* Benefit Design Dataset */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">5. Benefit Design / Cost Sharing Dataset (Optional but Recommended)</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Box>
            <Typography variant="body2" color="text.secondary" paragraph>
              Cost-sharing rules (copay, coinsurance) for financial behavior modeling.
            </Typography>
            
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Field</strong></TableCell>
                    <TableCell><strong>Type</strong></TableCell>
                    <TableCell><strong>Description</strong></TableCell>
                    <TableCell><strong>Example</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>lob</TableCell>
                    <TableCell>enum</TableCell>
                    <TableCell>COMMERCIAL, MA, MEDICAID</TableCell>
                    <TableCell>COMMERCIAL</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>service_category</TableCell>
                    <TableCell>string</TableCell>
                    <TableCell>ER, UC, OFFICE, IMAGING, INFUSION</TableCell>
                    <TableCell>URGENT_CARE</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>copay</TableCell>
                    <TableCell>float</TableCell>
                    <TableCell>Copay amount ($)</TableCell>
                    <TableCell>75.0</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>coinsurance</TableCell>
                    <TableCell>float</TableCell>
                    <TableCell>Coinsurance percentage (0.0-1.0)</TableCell>
                    <TableCell>0.1 (10%)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>effective_date</TableCell>
                    <TableCell>date (YYYY-MM-DD)</TableCell>
                    <TableCell>Date benefit design became effective</TableCell>
                    <TableCell>2024-01-01</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        </AccordionDetails>
      </Accordion>

      {/* Policy Metadata (For Policy Extraction) */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">6. Policy Metadata / Rules (For Policy Extraction)</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Box>
            <Alert severity="info" sx={{ mb: 2 }}>
              If providing policy documents/rules, we can extract structured PolicyLogic JSON. Supported formats: JSON, CSV, or structured documents.
            </Alert>
            
            <Typography variant="body2" paragraph>
              For policy extraction, provide one of:
            </Typography>
            <ul>
              <li><strong>Structured JSON:</strong> PolicyLogic JSON schema (see Policy Builder output)</li>
              <li><strong>CSV:</strong> Policy metadata with code sets, scope, effective dates</li>
              <li><strong>Documents:</strong> Policy documents with structured sections (under development)</li>
            </ul>

            <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
              Minimum Required Fields for Policy Extraction:
            </Typography>
            <ul>
              <li>Policy ID</li>
              <li>Policy Name</li>
              <li>Policy Type</li>
              <li>Effective Dates</li>
              <li>Scope (LOB, markets, network)</li>
              <li>Target Codes (CPT/HCPCS)</li>
              <li>Lever Type</li>
              <li>Lever Configuration</li>
            </ul>
          </Box>
        </AccordionDetails>
      </Accordion>

      {/* Ingestion Process */}
      <Paper sx={{ p: 3, mt: 3, bgcolor: 'primary.light', color: 'primary.contrastText' }}>
        <Typography variant="h6" gutterBottom>
          📦 Ingestion Process
        </Typography>
        <ol>
          <li>Prepare datasets in CSV or Parquet format following the schemas above</li>
          <li>Create a <code>manifest.json</code> file listing all dataset files</li>
          <li>Upload files to your configured object storage (S3-compatible) or provide URIs</li>
          <li>Submit ingestion request via API or UI with manifest URI</li>
          <li>System validates, curates, and partitions data for analytics</li>
          <li>Monitor ingestion status and errors via Ingestion Dashboard</li>
        </ol>
      </Paper>
    </Box>
  )
}

