/**
 * Data Model Viewer Page
 * Displays source data models, target data model, analytical data models, and data quality metrics
 */
import { useState, useEffect } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tabs,
  Tab,
  Alert,
  CircularProgress,
  LinearProgress,
} from '@mui/material'
import {
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material'
import { healthForesightColors } from '../theme/healthForesightTheme'
import { apiClient } from '../lib/api'

interface FieldDefinition {
  name: string
  type: string
  required: boolean
  description: string
}

interface ModelDefinition {
  name: string
  grain: string
  description: string
  domain: string
  fields: FieldDefinition[]
}

const COMPREHENSIVE_DATA_MODEL: Record<string, ModelDefinition[]> = {
  'Member & Eligibility': [
    {
      name: 'MemberMaster',
      grain: 'member_id (slowly changing)',
      description: 'Member dimension with SDOH, clinical flags, and demographics',
      domain: 'Member & Eligibility',
      fields: [
        { name: 'member_id', type: 'string', required: true, description: 'Member identifier (de-identified)' },
        { name: 'subscriber_id', type: 'string', required: false, description: 'Subscriber identifier' },
        { name: 'family_id', type: 'string', required: false, description: 'Family identifier' },
        { name: 'dob', type: 'date', required: false, description: 'Date of birth' },
        { name: 'age', type: 'int', required: false, description: 'Age' },
        { name: 'gender', type: 'enum', required: false, description: 'Gender (M/F/O/U)' },
        { name: 'race', type: 'string', required: false, description: 'Race' },
        { name: 'ethnicity', type: 'string', required: false, description: 'Ethnicity' },
        { name: 'address_zip5', type: 'string', required: false, description: 'ZIP code (5 digits)' },
        { name: 'county', type: 'string', required: false, description: 'County' },
        { name: 'state', type: 'string', required: false, description: 'State (2-letter code)' },
        { name: 'rural_flag', type: 'bool', required: false, description: 'Rural flag' },
        { name: 'income_band', type: 'string', required: false, description: 'Income band' },
        { name: 'education_band', type: 'string', required: false, description: 'Education band' },
        { name: 'employment_status', type: 'enum', required: false, description: 'Employment status' },
        { name: 'housing_insecurity_flag', type: 'bool', required: false, description: 'Housing insecurity flag' },
        { name: 'food_insecurity_flag', type: 'bool', required: false, description: 'Food insecurity flag' },
        { name: 'transportation_barrier_flag', type: 'bool', required: false, description: 'Transportation barrier flag' },
        { name: 'neighborhood_deprivation_index', type: 'decimal', required: false, description: 'Neighborhood deprivation index' },
        { name: 'area_vulnerability_index', type: 'decimal', required: false, description: 'Area vulnerability index (SVI/ADI)' },
        { name: 'pregnancy_flag', type: 'bool', required: false, description: 'Pregnancy flag' },
        { name: 'frailty_flag', type: 'bool', required: false, description: 'Frailty flag' },
        { name: 'disability_flag', type: 'bool', required: false, description: 'Disability flag' },
        { name: 'hospice_flag', type: 'bool', required: false, description: 'Hospice flag' },
        { name: 'ESRD_flag', type: 'bool', required: false, description: 'End-stage renal disease flag' },
        { name: 'dual_eligible_flag', type: 'bool', required: false, description: 'Dual eligible (Medicare/Medicaid) flag' },
        { name: 'portal_user_flag', type: 'bool', required: false, description: 'Portal user flag' },
        { name: 'preferred_contact_channel', type: 'string', required: false, description: 'Preferred contact channel' },
      ],
    },
    {
      name: 'EligibilityEnrollment',
      grain: 'member_id × coverage_month × plan_id',
      description: 'Coverage fact table - enrollment by month and plan',
      domain: 'Member & Eligibility',
      fields: [
        { name: 'member_id', type: 'string', required: true, description: 'Member identifier' },
        { name: 'coverage_month', type: 'string', required: true, description: 'Coverage month (YYYY-MM)' },
        { name: 'plan_id', type: 'string', required: true, description: 'Plan identifier' },
        { name: 'line_of_business', type: 'string', required: true, description: 'Line of business (Commercial/MA/Medicaid/Exchange)' },
        { name: 'product_id', type: 'string', required: false, description: 'Product identifier' },
        { name: 'benefit_package_id', type: 'string', required: false, description: 'Benefit package identifier' },
        { name: 'group_id', type: 'string', required: false, description: 'Group identifier (employer)' },
        { name: 'segment', type: 'string', required: false, description: 'Segment (ASO/FI)' },
        { name: 'network_id', type: 'string', required: false, description: 'Network identifier' },
        { name: 'network_tier', type: 'string', required: false, description: 'Network tier' },
        { name: 'enrollment_start_date', type: 'date', required: false, description: 'Enrollment start date' },
        { name: 'enrollment_end_date', type: 'date', required: false, description: 'Enrollment end date' },
        { name: 'coverage_status', type: 'enum', required: true, description: 'Coverage status (ACTIVE/TERMED/SUSPENDED/PENDING)' },
        { name: 'reason_code', type: 'string', required: false, description: 'Termination reason code' },
        { name: 'member_cost_share_level', type: 'string', required: false, description: 'Member cost share level (plan tier)' },
        { name: 'PCP_id', type: 'string', required: false, description: 'Primary care provider identifier (if assigned)' },
        { name: 'care_management_program_id', type: 'string', required: false, description: 'Care management program identifier (if enrolled)' },
      ],
    },
    {
      name: 'MemberRiskStratification',
      grain: 'member_id × month (or risk_run_date)',
      description: 'Risk scores and predictions for members',
      domain: 'Member & Eligibility',
      fields: [
        { name: 'member_id', type: 'string', required: true, description: 'Member identifier' },
        { name: 'risk_run_date', type: 'date', required: true, description: 'Risk run date' },
        { name: 'month', type: 'string', required: false, description: 'Month (YYYY-MM) - alternative to risk_run_date' },
        { name: 'risk_score', type: 'decimal', required: true, description: 'Risk score (HCC/ACG/custom)' },
        { name: 'risk_model_name', type: 'string', required: false, description: 'Risk model name' },
        { name: 'risk_model_version', type: 'string', required: false, description: 'Risk model version' },
        { name: 'predicted_cost_pmpm', type: 'decimal', required: false, description: 'Predicted cost per member per month' },
        { name: 'predicted_admission_risk', type: 'decimal', required: false, description: 'Predicted admission risk (0-1)' },
        { name: 'predicted_ed_risk', type: 'decimal', required: false, description: 'Predicted ED risk (0-1)' },
        { name: 'predicted_readmission_risk', type: 'decimal', required: false, description: 'Predicted readmission risk (0-1)' },
        { name: 'gaps_in_care_count', type: 'int', required: false, description: 'Gaps in care count' },
        { name: 'chronic_condition_count', type: 'int', required: false, description: 'Chronic condition count' },
        { name: 'utilization_intensity_index', type: 'decimal', required: false, description: 'Utilization intensity index' },
        { name: 'pharmacy_risk_score', type: 'decimal', required: false, description: 'Pharmacy risk score' },
        { name: 'behavioral_health_risk_score', type: 'decimal', required: false, description: 'Behavioral health risk score' },
      ],
    },
  ],
  'Claims & Utilization': [
    {
      name: 'ClaimHeader',
      grain: 'claim_id',
      description: 'Institutional or professional claim header',
      domain: 'Claims & Utilization',
      fields: [
        { name: 'claim_id', type: 'string', required: true, description: 'Claim identifier' },
        { name: 'claim_type', type: 'enum', required: true, description: 'Claim type (INSTITUTIONAL/PROFESSIONAL)' },
        { name: 'bill_type', type: 'string', required: false, description: 'Bill type code' },
        { name: 'form_type', type: 'enum', required: false, description: 'Form type (CMS1500/UB04)' },
        { name: 'member_id', type: 'string', required: true, description: 'Member identifier' },
        { name: 'billing_provider_id', type: 'string', required: false, description: 'Billing provider identifier' },
        { name: 'pay_to_provider_id', type: 'string', required: false, description: 'Pay-to provider identifier' },
        { name: 'claim_received_date', type: 'date', required: false, description: 'Claim received date' },
        { name: 'claim_processed_date', type: 'date', required: false, description: 'Claim processed date' },
        { name: 'claim_status', type: 'enum', required: true, description: 'Claim status (PAID/DENIED/ADJUSTED/VOID/PENDING)' },
        { name: 'denial_category', type: 'string', required: false, description: 'Denial category' },
        { name: 'denial_reason_codes', type: 'list[string]', required: false, description: 'Denial reason codes' },
        { name: 'total_allowed', type: 'decimal', required: true, description: 'Total allowed amount' },
        { name: 'total_paid', type: 'decimal', required: true, description: 'Total paid amount' },
        { name: 'total_member_resp', type: 'decimal', required: false, description: 'Total member responsibility' },
        { name: 'pricing_method', type: 'enum', required: false, description: 'Pricing method (FFS/BUNDLE/CAPITATED_SHADOW/PER_DIEM/DRG)' },
        { name: 'payment_arrangement_id', type: 'string', required: false, description: 'Payment arrangement identifier (links to contracts)' },
        { name: 'adjustment_indicator', type: 'bool', required: false, description: 'Adjustment indicator' },
        { name: 'original_claim_id', type: 'string', required: false, description: 'Original claim identifier (if adjusted)' },
        { name: 'DRG', type: 'string', required: false, description: 'DRG code' },
        { name: 'APR_DRG', type: 'string', required: false, description: 'APR-DRG code' },
        { name: 'MS_DRG', type: 'string', required: false, description: 'MS-DRG code' },
        { name: 'admission_date', type: 'date', required: false, description: 'Admission date' },
        { name: 'discharge_date', type: 'date', required: false, description: 'Discharge date' },
        { name: 'discharge_status', type: 'string', required: false, description: 'Discharge status' },
        { name: 'admission_type', type: 'enum', required: false, description: 'Admission type (ELECTIVE/EMERGENT/URGENT/OBSERVATION)' },
        { name: 'readmission_flag', type: 'bool', required: false, description: 'Readmission flag' },
      ],
    },
    {
      name: 'ClaimLine',
      grain: 'claim_line_id',
      description: 'Primary analytical table for utilization analysis',
      domain: 'Claims & Utilization',
      fields: [
        { name: 'claim_line_id', type: 'string', required: true, description: 'Claim line identifier' },
        { name: 'claim_id', type: 'string', required: true, description: 'Claim identifier (links to ClaimHeader)' },
        { name: 'member_id', type: 'string', required: true, description: 'Member identifier' },
        { name: 'cpt_hcpcs', type: 'string', required: false, description: 'CPT/HCPCS code' },
        { name: 'modifier_1', type: 'string', required: false, description: 'Modifier 1' },
        { name: 'modifier_2', type: 'string', required: false, description: 'Modifier 2' },
        { name: 'modifier_3', type: 'string', required: false, description: 'Modifier 3' },
        { name: 'modifier_4', type: 'string', required: false, description: 'Modifier 4' },
        { name: 'revenue_code', type: 'string', required: false, description: 'Revenue code' },
        { name: 'ndc', type: 'string', required: false, description: 'NDC code (for J-codes/infusion)' },
        { name: 'drg', type: 'string', required: false, description: 'DRG code (if line-level)' },
        { name: 'diagnosis_pointers', type: 'list[string]', required: false, description: 'Diagnosis pointers (dx1..dxN)' },
        { name: 'diagnosis_list', type: 'list[string]', required: false, description: 'Diagnosis codes list' },
        { name: 'service_date_from', type: 'date', required: true, description: 'Service date from' },
        { name: 'service_date_to', type: 'date', required: false, description: 'Service date to' },
        { name: 'place_of_service', type: 'string', required: true, description: 'Place of service code' },
        { name: 'type_of_service', type: 'string', required: false, description: 'Type of service' },
        { name: 'betos', type: 'string', required: false, description: 'BETOS code' },
        { name: 'service_category', type: 'string', required: true, description: 'Service category' },
        { name: 'site_of_care_class', type: 'enum', required: false, description: 'Site of care class (OFFICE/ASC/HOPD/ER/INPATIENT/HOME/etc.)' },
        { name: 'units', type: 'decimal', required: true, description: 'Units' },
        { name: 'unit_type', type: 'string', required: false, description: 'Unit type' },
        { name: 'rendering_provider_id', type: 'string', required: false, description: 'Rendering provider identifier' },
        { name: 'referring_provider_id', type: 'string', required: false, description: 'Referring provider identifier' },
        { name: 'ordering_provider_id', type: 'string', required: false, description: 'Ordering provider identifier' },
        { name: 'facility_id', type: 'string', required: false, description: 'Facility identifier' },
        { name: 'in_network_flag', type: 'bool', required: true, description: 'In-network flag' },
        { name: 'network_id', type: 'string', required: false, description: 'Network identifier' },
        { name: 'network_tier', type: 'string', required: false, description: 'Network tier' },
        { name: 'benefit_category', type: 'enum', required: false, description: 'Benefit category (INPATIENT/OUTPATIENT/PROFESSIONAL/DME/etc.)' },
        { name: 'prior_auth_required_flag', type: 'bool', required: false, description: 'Prior authorization required flag' },
        { name: 'prior_auth_id', type: 'string', required: false, description: 'Prior authorization identifier (if linked)' },
        { name: 'referral_required_flag', type: 'bool', required: false, description: 'Referral required flag' },
        { name: 'referral_id', type: 'string', required: false, description: 'Referral identifier (if linked)' },
        { name: 'billed_amount', type: 'decimal', required: false, description: 'Billed amount' },
        { name: 'allowed_amount', type: 'decimal', required: true, description: 'Allowed amount' },
        { name: 'paid_amount', type: 'decimal', required: true, description: 'Paid amount' },
        { name: 'copay_amount', type: 'decimal', required: false, description: 'Copay amount' },
        { name: 'coinsurance_amount', type: 'decimal', required: false, description: 'Coinsurance amount' },
        { name: 'deductible_amount', type: 'decimal', required: false, description: 'Deductible amount' },
        { name: 'member_resp_amount', type: 'decimal', required: false, description: 'Member responsibility amount' },
        { name: 'cob_amount', type: 'decimal', required: false, description: 'Coordination of benefits amount' },
        { name: 'coordination_of_benefits_flag', type: 'bool', required: false, description: 'Coordination of benefits flag' },
        { name: 'emergency_flag', type: 'bool', required: false, description: 'Emergency flag' },
        { name: 'avoidable_ed_flag', type: 'bool', required: false, description: 'Avoidable ED flag (if derived)' },
        { name: 'preventable_hosp_flag', type: 'bool', required: false, description: 'Preventable hospitalization flag (if derived)' },
        { name: 'low_value_care_flag', type: 'bool', required: false, description: 'Low-value care flag (if derived)' },
        { name: 'guideline_concordant_flag', type: 'bool', required: false, description: 'Guideline concordant flag (if derived)' },
      ],
    },
    {
      name: 'EpisodeOfCare',
      grain: 'episode_id',
      description: 'Derived or provided episode grouping',
      domain: 'Claims & Utilization',
      fields: [
        { name: 'episode_id', type: 'string', required: true, description: 'Episode identifier' },
        { name: 'member_id', type: 'string', required: true, description: 'Member identifier' },
        { name: 'episode_type', type: 'enum', required: true, description: 'Episode type (SURGERY/MATERNITY/CHRONIC/ACUTE/OTHER)' },
        { name: 'start_date', type: 'date', required: true, description: 'Episode start date' },
        { name: 'end_date', type: 'date', required: true, description: 'Episode end date' },
        { name: 'attributed_provider_id', type: 'string', required: false, description: 'Attributed provider identifier' },
        { name: 'attributed_system_id', type: 'string', required: false, description: 'Attributed system identifier' },
        { name: 'episode_cost_total', type: 'decimal', required: true, description: 'Total episode cost' },
        { name: 'claim_count', type: 'int', required: false, description: 'Claim count within episode' },
        { name: 'claim_line_count', type: 'int', required: false, description: 'Claim line count within episode' },
        { name: 'admission_count', type: 'int', required: false, description: 'Admission count' },
        { name: 'ed_visit_count', type: 'int', required: false, description: 'ED visit count' },
        { name: 'readmission_count', type: 'int', required: false, description: 'Readmission count' },
      ],
    },
  ],
  'Pharmacy': [
    {
      name: 'PharmacyClaim',
      grain: 'rx_claim_id',
      description: 'Pharmacy utilization claims',
      domain: 'Pharmacy',
      fields: [
        { name: 'rx_claim_id', type: 'string', required: true, description: 'Pharmacy claim identifier' },
        { name: 'member_id', type: 'string', required: true, description: 'Member identifier' },
        { name: 'fill_date', type: 'date', required: true, description: 'Fill date' },
        { name: 'ndc', type: 'string', required: true, description: 'NDC code' },
        { name: 'gpi', type: 'string', required: false, description: 'GPI code' },
        { name: 'rxnorm', type: 'string', required: false, description: 'RxNorm code' },
        { name: 'drug_name', type: 'string', required: false, description: 'Drug name' },
        { name: 'therapeutic_class', type: 'string', required: false, description: 'Therapeutic class' },
        { name: 'days_supply', type: 'int', required: true, description: 'Days supply' },
        { name: 'quantity', type: 'decimal', required: true, description: 'Quantity' },
        { name: 'quantity_uom', type: 'string', required: false, description: 'Quantity unit of measure' },
        { name: 'refills', type: 'int', required: false, description: 'Refills' },
        { name: 'prescriber_id', type: 'string', required: false, description: 'Prescriber identifier' },
        { name: 'pharmacy_id', type: 'string', required: false, description: 'Pharmacy identifier' },
        { name: 'paid_amount', type: 'decimal', required: true, description: 'Paid amount' },
        { name: 'allowed_amount', type: 'decimal', required: true, description: 'Allowed amount' },
        { name: 'member_pay', type: 'decimal', required: false, description: 'Member pay amount' },
        { name: 'formulary_tier', type: 'string', required: false, description: 'Formulary tier' },
        { name: 'pa_required_flag', type: 'bool', required: false, description: 'Prior authorization required flag' },
        { name: 'step_therapy_flag', type: 'bool', required: false, description: 'Step therapy flag' },
        { name: 'specialty_flag', type: 'bool', required: false, description: 'Specialty flag' },
        { name: 'generic_flag', type: 'bool', required: false, description: 'Generic flag' },
        { name: 'mail_order_flag', type: 'bool', required: false, description: 'Mail order flag' },
      ],
    },
  ],
  'Provider & Network': [
    {
      name: 'ProviderMaster',
      grain: 'provider_id (SCD)',
      description: 'Provider dimension with specialties and capabilities',
      domain: 'Provider & Network',
      fields: [
        { name: 'provider_id', type: 'string', required: true, description: 'Provider identifier' },
        { name: 'npi', type: 'string', required: false, description: 'National Provider Identifier (10 digits)' },
        { name: 'provider_name', type: 'string', required: false, description: 'Provider name' },
        { name: 'provider_type', type: 'enum', required: true, description: 'Provider type (INDIVIDUAL/FACILITY)' },
        { name: 'specialty_primary', type: 'string', required: false, description: 'Primary specialty' },
        { name: 'specialty_secondary', type: 'string', required: false, description: 'Secondary specialty' },
        { name: 'taxonomy_codes', type: 'list[string]', required: false, description: 'Taxonomy codes' },
        { name: 'org_id', type: 'string', required: false, description: 'Organization identifier' },
        { name: 'system_affiliation_id', type: 'string', required: false, description: 'System affiliation identifier' },
        { name: 'practice_location_zip', type: 'string', required: false, description: 'Practice location ZIP code' },
        { name: 'practice_location_county', type: 'string', required: false, description: 'Practice location county' },
        { name: 'practice_location_state', type: 'string', required: false, description: 'Practice location state' },
        { name: 'accepting_new_patients_flag', type: 'bool', required: false, description: 'Accepting new patients flag' },
        { name: 'telehealth_capable_flag', type: 'bool', required: false, description: 'Telehealth capable flag' },
        { name: 'languages', type: 'list[string]', required: false, description: 'Languages spoken' },
        { name: 'quality_scores', type: 'dict', required: false, description: 'Quality scores (if available)' },
        { name: 'capacity_indicators', type: 'dict', required: false, description: 'Capacity indicators (panel size, appt wait)' },
      ],
    },
    {
      name: 'FacilityMaster',
      grain: 'facility_id',
      description: 'Facility dimension',
      domain: 'Provider & Network',
      fields: [
        { name: 'facility_id', type: 'string', required: true, description: 'Facility identifier' },
        { name: 'facility_name', type: 'string', required: false, description: 'Facility name' },
        { name: 'facility_type', type: 'string', required: true, description: 'Facility type (HOPD, ASC, freestanding imaging, SNF, etc.)' },
        { name: 'trauma_level', type: 'string', required: false, description: 'Trauma level' },
        { name: 'bed_count', type: 'int', required: false, description: 'Bed count' },
        { name: 'ownership_type', type: 'string', required: false, description: 'Ownership type' },
        { name: 'facility_zip', type: 'string', required: false, description: 'Facility ZIP code' },
        { name: 'facility_county', type: 'string', required: false, description: 'Facility county' },
        { name: 'facility_state', type: 'string', required: false, description: 'Facility state' },
        { name: 'geo_lat', type: 'decimal', required: false, description: 'Latitude' },
        { name: 'geo_lon', type: 'decimal', required: false, description: 'Longitude' },
      ],
    },
    {
      name: 'NetworkConfiguration',
      grain: 'network_id × provider_id × effective_period',
      description: 'Provider-network relationships',
      domain: 'Provider & Network',
      fields: [
        { name: 'network_id', type: 'string', required: true, description: 'Network identifier' },
        { name: 'network_name', type: 'string', required: false, description: 'Network name' },
        { name: 'network_tier', type: 'string', required: false, description: 'Network tier' },
        { name: 'provider_id', type: 'string', required: true, description: 'Provider identifier' },
        { name: 'in_network_flag', type: 'bool', required: true, description: 'In-network flag' },
        { name: 'effective_start', type: 'date', required: true, description: 'Effective start date' },
        { name: 'effective_end', type: 'date', required: false, description: 'Effective end date' },
        { name: 'exclusions', type: 'list[string]', required: false, description: 'Exclusions' },
        { name: 'referral_required_rules', type: 'dict', required: false, description: 'Referral required rules (high-level)' },
      ],
    },
    {
      name: 'ProviderContract',
      grain: 'contract_id × code × effective_period',
      description: 'Contract and rate information',
      domain: 'Provider & Network',
      fields: [
        { name: 'contract_id', type: 'string', required: true, description: 'Contract identifier' },
        { name: 'provider_id', type: 'string', required: false, description: 'Provider identifier' },
        { name: 'facility_id', type: 'string', required: false, description: 'Facility identifier' },
        { name: 'code', type: 'string', required: true, description: 'Code (CPT/HCPCS/DRG/revenue)' },
        { name: 'effective_start', type: 'date', required: true, description: 'Effective start date' },
        { name: 'effective_end', type: 'date', required: false, description: 'Effective end date' },
        { name: 'rate_type', type: 'enum', required: true, description: 'Rate type (FFS/DRG/PER_DIEM/CAPITATION/BUNDLE)' },
        { name: 'fee_schedule_id', type: 'string', required: false, description: 'Fee schedule identifier' },
        { name: 'code_type', type: 'enum', required: true, description: 'Code type (CPT/HCPCS/DRG/REVENUE)' },
        { name: 'allowed_rate', type: 'decimal', required: false, description: 'Allowed rate' },
        { name: 'percent_of_medicare', type: 'decimal', required: false, description: 'Percent of Medicare' },
        { name: 'stoploss_terms', type: 'dict', required: false, description: 'Stoploss terms (optional)' },
      ],
    },
  ],
  'Benefits & Accumulators': [
    {
      name: 'BenefitDesign',
      grain: 'plan_id × benefit_component × effective_period',
      description: 'Plan benefit structure',
      domain: 'Benefits & Accumulators',
      fields: [
        { name: 'plan_id', type: 'string', required: true, description: 'Plan identifier' },
        { name: 'benefit_package_id', type: 'string', required: false, description: 'Benefit package identifier' },
        { name: 'service_category', type: 'string', required: true, description: 'Service category' },
        { name: 'effective_start', type: 'date', required: true, description: 'Effective start date' },
        { name: 'effective_end', type: 'date', required: false, description: 'Effective end date' },
        { name: 'copay', type: 'decimal', required: false, description: 'Copay amount' },
        { name: 'coinsurance', type: 'decimal', required: false, description: 'Coinsurance rate (0-1)' },
        { name: 'deductible', type: 'decimal', required: false, description: 'Deductible amount' },
        { name: 'oop_max', type: 'decimal', required: false, description: 'Out-of-pocket maximum' },
        { name: 'visit_limit', type: 'int', required: false, description: 'Visit limit' },
        { name: 'unit_limit', type: 'int', required: false, description: 'Unit limit' },
        { name: 'prior_auth_indicator', type: 'bool', required: false, description: 'Prior authorization indicator (plan-level)' },
        { name: 'referral_indicator', type: 'bool', required: false, description: 'Referral indicator' },
        { name: 'tiered_cost_sharing_by_site', type: 'dict', required: false, description: 'Tiered cost sharing by site (structured)' },
      ],
    },
    {
      name: 'MemberAccumulator',
      grain: 'member_id × month',
      description: 'Member benefit accumulator status',
      domain: 'Benefits & Accumulators',
      fields: [
        { name: 'member_id', type: 'string', required: true, description: 'Member identifier' },
        { name: 'month', type: 'string', required: true, description: 'Month (YYYY-MM)' },
        { name: 'deductible_met', type: 'decimal', required: false, description: 'Deductible met amount' },
        { name: 'deductible_remaining', type: 'decimal', required: false, description: 'Deductible remaining amount' },
        { name: 'oop_met', type: 'decimal', required: false, description: 'Out-of-pocket met amount' },
        { name: 'oop_remaining', type: 'decimal', required: false, description: 'Out-of-pocket remaining amount' },
        { name: 'remaining_visits', type: 'dict', required: false, description: 'Remaining visits by category' },
        { name: 'remaining_units', type: 'dict', required: false, description: 'Remaining units by category' },
      ],
    },
  ],
  'UM Operations': [
    {
      name: 'PriorAuthorizationRequest',
      grain: 'pa_request_id',
      description: 'Prior authorization request tracking',
      domain: 'UM Operations',
      fields: [
        { name: 'pa_request_id', type: 'string', required: true, description: 'Prior authorization request identifier' },
        { name: 'member_id', type: 'string', required: true, description: 'Member identifier' },
        { name: 'requesting_provider_id', type: 'string', required: true, description: 'Requesting provider identifier' },
        { name: 'service_codes', type: 'list[string]', required: true, description: 'Service code(s)' },
        { name: 'code_type', type: 'string', required: true, description: 'Code type (CPT/HCPCS)' },
        { name: 'requested_units', type: 'decimal', required: false, description: 'Requested units' },
        { name: 'request_date', type: 'date', required: true, description: 'Request date' },
        { name: 'decision_date', type: 'date', required: false, description: 'Decision date' },
        { name: 'decision', type: 'enum', required: true, description: 'Decision (APPROVED/DENIED/PARTIAL/PENDED)' },
        { name: 'denial_reason_codes', type: 'list[string]', required: false, description: 'Denial reason code(s)' },
        { name: 'turnaround_time_days', type: 'int', required: false, description: 'Turnaround time (days)' },
        { name: 'peer_to_peer_flag', type: 'bool', required: false, description: 'Peer-to-peer flag' },
        { name: 'expedited_flag', type: 'bool', required: false, description: 'Expedited flag' },
        { name: 'site_of_care_requested', type: 'string', required: false, description: 'Site of care requested' },
        { name: 'site_of_care_authorized', type: 'string', required: false, description: 'Site of care authorized' },
        { name: 'auth_valid_from', type: 'date', required: false, description: 'Authorization valid from date' },
        { name: 'auth_valid_to', type: 'date', required: false, description: 'Authorization valid to date' },
        { name: 'auth_number', type: 'string', required: false, description: 'Authorization number' },
        { name: 'linked_claim_ids', type: 'list[string]', required: false, description: 'Linked claim identifier(s)' },
      ],
    },
    {
      name: 'AppealGrievance',
      grain: 'appeal_id',
      description: 'Appeals and grievances tracking',
      domain: 'UM Operations',
      fields: [
        { name: 'appeal_id', type: 'string', required: true, description: 'Appeal identifier' },
        { name: 'related_pa_id', type: 'string', required: false, description: 'Related prior authorization identifier' },
        { name: 'related_claim_id', type: 'string', required: false, description: 'Related claim identifier' },
        { name: 'member_id', type: 'string', required: true, description: 'Member identifier' },
        { name: 'filed_date', type: 'date', required: true, description: 'Filed date' },
        { name: 'resolved_date', type: 'date', required: false, description: 'Resolved date' },
        { name: 'outcome', type: 'enum', required: true, description: 'Outcome (UPHELD/OVERTURNED/PARTIAL/WITHDRAWN/PENDING)' },
        { name: 'overturn_flag', type: 'bool', required: false, description: 'Overturn flag' },
        { name: 'reason_categories', type: 'list[string]', required: false, description: 'Reason categories' },
        { name: 'external_review_flag', type: 'bool', required: false, description: 'External review flag' },
      ],
    },
  ],
}

const ALL_MODELS = Object.values(COMPREHENSIVE_DATA_MODEL).flat()

// Source data models (from pipelines)
const SOURCE_DATA_MODELS = [
  { name: 'Claims Source', description: 'Raw claims data from source systems', format: 'CSV/Parquet', fields: ['claim_id', 'member_id', 'service_date', 'cpt_code', 'billed_amount'] },
  { name: 'Enrollment Source', description: 'Raw enrollment data from source systems', format: 'CSV/Parquet', fields: ['member_id', 'coverage_month', 'plan_id', 'lob'] },
  { name: 'Provider Source', description: 'Raw provider data from source systems', format: 'CSV/Parquet', fields: ['provider_id', 'npi', 'specialty', 'location'] },
  { name: 'Pharmacy Source', description: 'Raw pharmacy claims from source systems', format: 'CSV/Parquet', fields: ['rx_claim_id', 'member_id', 'ndc', 'fill_date', 'paid_amount'] },
]

// Analytical data models (derived/computed)
const ANALYTICAL_DATA_MODELS = [
  { name: 'Policy Impact Metrics', description: 'Computed policy impact metrics and outcomes', grain: 'policy_id × period', fields: ['policy_id', 'period', 'utilization_rate', 'cost_pmpm', 'impact_score'] },
  { name: 'Provider Archetypes', description: 'Clustered provider segments based on utilization patterns', grain: 'provider_id', fields: ['provider_id', 'archetype', 'utilization_profile', 'cost_profile'] },
  { name: 'Member Risk Segments', description: 'Member risk stratification and sensitivity segments', grain: 'member_id', fields: ['member_id', 'risk_segment', 'sensitivity_score', 'utilization_trend'] },
  { name: 'Baseline Time Series', description: 'Time-series baseline metrics for trend analysis', grain: 'period', fields: ['period', 'utilization_rate', 'cost_pmpm', 'trend', 'seasonality'] },
]

export default function DataModelViewerPage() {
  const [selectedTab, setSelectedTab] = useState<number>(0)
  const [selectedDomain, setSelectedDomain] = useState<string>('Member & Eligibility')
  const [expandedModel, setExpandedModel] = useState<string | null>(null)
  const [dataQualitySummary, setDataQualitySummary] = useState<any>(null)
  const [dataQualityReport, setDataQualityReport] = useState<any>(null)
  const [loadingQuality, setLoadingQuality] = useState<boolean>(false)
  const [pipelines, setPipelines] = useState<any[]>([])

  const domains = Object.keys(COMPREHENSIVE_DATA_MODEL)

  const handleModelExpand = (modelName: string) => {
    setExpandedModel(expandedModel === modelName ? null : modelName)
  }

  // Load data quality metrics
  useEffect(() => {
    const loadDataQuality = async () => {
      setLoadingQuality(true)
      try {
        const summary = await apiClient.getDataQualitySummary()
        setDataQualitySummary(summary)
        
        try {
          const report = await apiClient.getDataQualityReport()
          setDataQualityReport(report)
        } catch (e) {
          // Report may not exist yet
          console.log('Data quality report not available')
        }
      } catch (error) {
        console.error('Error loading data quality:', error)
      } finally {
        setLoadingQuality(false)
      }
    }

    const loadPipelines = async () => {
      try {
        const pipelineList = await apiClient.getPipelines()
        setPipelines(Array.isArray(pipelineList) ? pipelineList : [])
      } catch (error) {
        console.error('Error loading pipelines:', error)
      }
    }

    if (selectedTab === 3) { // Data Quality tab
      loadDataQuality()
    }
    if (selectedTab === 0) { // Source Models tab
      loadPipelines()
    }
  }, [selectedTab])

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
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
          Data Model Viewer
        </Typography>
        <Typography
          variant="body1"
          sx={{
            color: healthForesightColors.neutral.mid,
            lineHeight: 1.6,
            mb: 2,
          }}
        >
          View source data models, target canonical data model, analytical data models, and data quality metrics.
        </Typography>
      </Box>

      <Tabs
        value={selectedTab}
        onChange={(_, newValue) => setSelectedTab(newValue)}
        sx={{ mb: 3 }}
        variant="scrollable"
        scrollButtons="auto"
      >
        <Tab label="Source Data Models" />
        <Tab label="Target Data Model" />
        <Tab label="Analytical Data Models" />
        <Tab label="Data Quality Metrics" />
      </Tabs>

      {/* Source Data Models Tab */}
      {selectedTab === 0 && (
        <Box>
          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="body2">
              <strong>Source Data Models:</strong> Raw data formats ingested from source systems via pipelines.
              These are transformed into the target canonical data model.
            </Typography>
          </Alert>

          <Grid container spacing={3} sx={{ mb: 3 }}>
            {SOURCE_DATA_MODELS.map((model) => (
              <Grid item xs={12} md={6} key={model.name}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>{model.name}</Typography>
                    <Typography variant="body2" color="text.secondary" paragraph>
                      {model.description}
                    </Typography>
                    <Chip label={model.format} size="small" sx={{ mb: 2 }} />
                    <Typography variant="subtitle2" gutterBottom>Key Fields:</Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {model.fields.map((field) => (
                        <Chip key={field} label={field} size="small" variant="outlined" />
                      ))}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>

          {pipelines.length > 0 && (
            <Card sx={{ mt: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>Active Pipelines</Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  {pipelines.length} pipeline(s) configured for data ingestion
                </Typography>
              </CardContent>
            </Card>
          )}
        </Box>
      )}

      {/* Target Data Model Tab */}
      {selectedTab === 1 && (
        <Box>
          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="body2">
              <strong>Target Data Model:</strong> Complete specification of all canonical data models used in HealthForesight.
              All models extend CanonicalBase which includes tenant_id, source_system, source_file_id, ingestion_id,
              created_at, updated_at, and record_hash.
            </Typography>
          </Alert>

          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Model Statistics
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="text.secondary">
                    Total Models
                  </Typography>
                  <Typography variant="h4">{ALL_MODELS.length}</Typography>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="text.secondary">
                    Domains
                  </Typography>
                  <Typography variant="h4">{domains.length}</Typography>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="text.secondary">
                    Total Fields
                  </Typography>
                  <Typography variant="h4">
                    {ALL_MODELS.reduce((sum, model) => sum + model.fields.length, 0)}
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          <Tabs
            value={selectedDomain}
            onChange={(_, newValue) => setSelectedDomain(newValue)}
            sx={{ mb: 3 }}
            variant="scrollable"
            scrollButtons="auto"
          >
            {domains.map((domain) => (
              <Tab key={domain} label={domain} value={domain} />
            ))}
          </Tabs>

          {COMPREHENSIVE_DATA_MODEL[selectedDomain]?.map((model) => (
        <Accordion
          key={model.name}
          expanded={expandedModel === model.name}
          onChange={() => handleModelExpand(model.name)}
          sx={{ mb: 2 }}
        >
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ width: '100%', display: 'flex', alignItems: 'center', gap: 2 }}>
              <Typography variant="h6" sx={{ flexGrow: 1 }}>
                {model.name}
              </Typography>
              <Chip label={`${model.fields.length} fields`} size="small" color="primary" variant="outlined" />
              <Chip
                label={model.grain}
                size="small"
                color="secondary"
                variant="outlined"
                icon={<InfoIcon />}
              />
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary" paragraph>
                {model.description}
              </Typography>
            </Box>

            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>
                      <strong>Field Name</strong>
                    </TableCell>
                    <TableCell>
                      <strong>Type</strong>
                    </TableCell>
                    <TableCell>
                      <strong>Required</strong>
                    </TableCell>
                    <TableCell>
                      <strong>Description</strong>
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {model.fields.map((field) => (
                    <TableRow key={field.name}>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                          {field.name}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip label={field.type} size="small" variant="outlined" />
                      </TableCell>
                      <TableCell>
                        {field.required ? (
                          <Chip
                            icon={<CheckCircleIcon />}
                            label="Required"
                            size="small"
                            color="error"
                          />
                        ) : (
                          <Chip
                            icon={<WarningIcon />}
                            label="Optional"
                            size="small"
                            color="default"
                          />
                        )}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">{field.description}</Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </AccordionDetails>
        </Accordion>
      ))}
        </Box>
      )}

      {/* Analytical Data Models Tab */}
      {selectedTab === 2 && (
        <Box>
          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="body2">
              <strong>Analytical Data Models:</strong> Derived and computed models used for analytics, predictions, and insights.
            </Typography>
          </Alert>

          <Grid container spacing={3}>
            {ANALYTICAL_DATA_MODELS.map((model) => (
              <Grid item xs={12} md={6} key={model.name}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>{model.name}</Typography>
                    <Typography variant="body2" color="text.secondary" paragraph>
                      {model.description}
                    </Typography>
                    <Chip label={model.grain} size="small" sx={{ mb: 2 }} />
                    <Typography variant="subtitle2" gutterBottom>Key Fields:</Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {model.fields.map((field) => (
                        <Chip key={field} label={field} size="small" variant="outlined" />
                      ))}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {/* Data Quality Metrics Tab */}
      {selectedTab === 3 && (
        <Box>
          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="body2">
              <strong>Data Quality Metrics:</strong> Validation results, completeness scores, and data quality indicators
              for all datasets in the target data model.
            </Typography>
          </Alert>

          {loadingQuality ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <>
              {dataQualitySummary && (
                <Card sx={{ mb: 3 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                      <Typography variant="h6">Data Quality Summary</Typography>
                      <Chip
                        label={dataQualitySummary.overall_status?.toUpperCase() || 'UNKNOWN'}
                        color={
                          dataQualitySummary.overall_status === 'excellent' ? 'success' :
                          dataQualitySummary.overall_status === 'good' ? 'info' :
                          dataQualitySummary.overall_status === 'fair' ? 'warning' : 'error'
                        }
                      />
                    </Box>
                    
                    {dataQualitySummary.overall_score !== undefined && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Overall Score: {dataQualitySummary.overall_score}%
                        </Typography>
                        <LinearProgress
                          variant="determinate"
                          value={dataQualitySummary.overall_score}
                          sx={{ height: 8, borderRadius: 4 }}
                        />
                      </Box>
                    )}

                    <Grid container spacing={2} sx={{ mt: 2 }}>
                      {dataQualitySummary.datasets && Object.entries(dataQualitySummary.datasets).map(([name, info]: [string, any]) => (
                        <Grid item xs={12} sm={6} md={4} key={name}>
                          <Card variant="outlined">
                            <CardContent>
                              <Typography variant="subtitle1" gutterBottom>{name}</Typography>
                              <Typography variant="body2" color="text.secondary">
                                {info.exists ? (
                                  <>
                                    <CheckCircleIcon sx={{ fontSize: 16, color: 'success.main', verticalAlign: 'middle', mr: 0.5 }} />
                                    Available ({info.size_mb} MB)
                                  </>
                                ) : (
                                  <>
                                    <WarningIcon sx={{ fontSize: 16, color: 'warning.main', verticalAlign: 'middle', mr: 0.5 }} />
                                    Not Available
                                  </>
                                )}
                              </Typography>
                            </CardContent>
                          </Card>
                        </Grid>
                      ))}
                    </Grid>

                    {dataQualitySummary.issues_count !== undefined && dataQualitySummary.issues_count > 0 && (
                      <Alert severity="warning" sx={{ mt: 2 }}>
                        {dataQualitySummary.issues_count} data quality issue(s) detected
                      </Alert>
                    )}
                  </CardContent>
                </Card>
              )}

              {dataQualityReport && (
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Detailed Quality Report</Typography>
                    {dataQualityReport.overall_score !== undefined && (
                      <Typography variant="body1" paragraph>
                        Overall Score: <strong>{dataQualityReport.overall_score}%</strong>
                      </Typography>
                    )}
                    {dataQualityReport.datasets && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="subtitle1" gutterBottom>Dataset Quality Scores</Typography>
                        <TableContainer component={Paper} variant="outlined">
                          <Table size="small">
                            <TableHead>
                              <TableRow>
                                <TableCell><strong>Dataset</strong></TableCell>
                                <TableCell><strong>Score</strong></TableCell>
                                <TableCell><strong>Status</strong></TableCell>
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              {Object.entries(dataQualityReport.datasets).map(([name, info]: [string, any]) => (
                                <TableRow key={name}>
                                  <TableCell>{name}</TableCell>
                                  <TableCell>
                                    {info.score !== undefined ? `${info.score}%` : 'N/A'}
                                  </TableCell>
                                  <TableCell>
                                    <Chip
                                      label={info.status || 'unknown'}
                                      size="small"
                                      color={
                                        info.status === 'excellent' ? 'success' :
                                        info.status === 'good' ? 'info' :
                                        info.status === 'fair' ? 'warning' : 'default'
                                      }
                                    />
                                  </TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </TableContainer>
                      </Box>
                    )}
                  </CardContent>
                </Card>
              )}

              {!dataQualitySummary && !loadingQuality && (
                <Alert severity="warning">
                  Data quality metrics not available. Run data quality validation to generate metrics.
                </Alert>
              )}
            </>
          )}
        </Box>
      )}
    </Box>
  )
}

