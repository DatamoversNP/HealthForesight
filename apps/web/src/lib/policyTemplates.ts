/**
 * Policy Templates - Pre-configured policy templates for quick start
 */

export interface PolicyTemplate {
  id: string
  name: string
  description: string
  policy_type: string
  data: any
}

export const POLICY_TEMPLATES: PolicyTemplate[] = [
  {
    id: 'prior_auth_mri_op',
    name: 'Prior Authorization - Outpatient MRI',
    description: 'Require PA for outpatient MRI to reduce inappropriate imaging',
    policy_type: 'PRIOR_AUTH',
    data: {
      name: 'Outpatient MRI Prior Authorization',
      policy_type: 'PRIOR_AUTH',
      description: 'Require prior authorization for outpatient MRI to reduce inappropriate imaging.',
      owner_role: 'UM_LEADER',
      scope: {
        lob: ['COMMERCIAL'],
        markets: ['NYC', 'DFW'],
        network: ['IN'],
      },
      effective_period: {
        start_date: new Date().toISOString().split('T')[0],
        end_date: null,
      },
      levers: [
        {
          lever_type: 'PRIOR_AUTH',
          targets: {
            code_type: 'CPT',
            codes: ['72148', '72149', '72158'],
            code_groups: [],
          },
          config: {
            requires_pa: true,
            pa_touchpoint: 'PA_WORKFLOW',
            override_allowed: false,
          },
          priority: 1,
        },
      ],
      apply_when: [
        {
          conditions: [
            {
              field: 'place_of_service',
              operator: 'IN',
              value: ['OUTPATIENT', 'OFFICE'],
            },
          ],
          operator: 'AND',
        },
      ],
      global_exceptions: [
        {
          field: 'place_of_service',
          operator: 'IN',
          value: ['ER', 'EMERGENCY'],
          description: 'Do not require PA in emergency situations',
        },
      ],
    },
  },
  {
    id: 'site_of_care_infusion',
    name: 'Site of Care - Infusion Optimization',
    description: 'Redirect infusion services from hospital OP to freestanding centers',
    policy_type: 'SITE_OF_CARE',
    data: {
      name: 'Infusion Site-of-Care Optimization',
      policy_type: 'SITE_OF_CARE',
      description: 'Redirect infusion services from hospital outpatient to freestanding centers.',
      owner_role: 'UM_LEADER',
      scope: {
        lob: ['COMMERCIAL', 'MA'],
        markets: ['ALL'],
        network: ['IN'],
      },
      effective_period: {
        start_date: new Date().toISOString().split('T')[0],
        end_date: null,
      },
      levers: [
        {
          lever_type: 'SITE_OF_CARE',
          targets: {
            code_type: 'CPT',
            codes: ['96413', '96415', '96417'],
            code_groups: [],
          },
          config: {
            allowed_sites: ['FREESTANDING', 'OFFICE'],
            disallowed_sites: ['HOSPITAL_OP'],
            redirect_to: 'FREESTANDING',
            deny_if_disallowed: false, // Redirect instead of deny
          },
          priority: 1,
        },
      ],
      apply_when: [],
      global_exceptions: [],
    },
  },
  {
    id: 'frequency_limit_pt',
    name: 'Frequency Limit - Physical Therapy',
    description: 'Limit PT visits to 20 per calendar year',
    policy_type: 'DURATION_FREQUENCY_LIMIT',
    data: {
      name: 'Physical Therapy Visit Limit',
      policy_type: 'DURATION_FREQUENCY_LIMIT',
      description: 'Limit PT visits to 20 per calendar year.',
      owner_role: 'UM_LEADER',
      scope: {
        lob: ['COMMERCIAL', 'MEDICAID'],
        markets: ['ALL'],
        network: ['ALL'],
      },
      effective_period: {
        start_date: new Date().toISOString().split('T')[0],
        end_date: null,
      },
      levers: [
        {
          lever_type: 'DURATION_FREQUENCY_LIMIT',
          targets: {
            code_type: 'CPT',
            codes: ['97110', '97112', '97140'],
            code_groups: [],
          },
          config: {
            max_visits: 20,
            time_period: 'YEAR',
            reset_date: 'CALENDAR_YEAR',
            accumulate_across_providers: true,
          },
          priority: 1,
        },
      ],
      apply_when: [],
      global_exceptions: [],
    },
  },
  {
    id: 'cost_sharing_uc',
    name: 'Cost Sharing - Urgent Care Copay',
    description: 'Increase copay for urgent care visits to discourage low-acuity use',
    policy_type: 'COST_SHARING',
    data: {
      name: 'Urgent Care Copay Increase',
      policy_type: 'COST_SHARING',
      description: 'Increase copay for urgent care visits to discourage low-acuity use.',
      owner_role: 'STRATEGY',
      scope: {
        lob: ['COMMERCIAL'],
        markets: ['ALL'],
        network: ['IN'],
      },
      effective_period: {
        start_date: new Date().toISOString().split('T')[0],
        end_date: null,
      },
      levers: [
        {
          lever_type: 'COST_SHARING',
          targets: {
            code_type: 'CPT',
            codes: ['99281', '99282', '99283'],
            code_groups: [],
          },
          config: {
            copay: 75.0,
            coinsurance: 0.0,
            deductible_applies: false,
            out_of_pocket_applies: true,
            differential_by_site: null,
          },
          priority: 1,
        },
      ],
      apply_when: [
        {
          conditions: [
            {
              field: 'place_of_service',
              operator: 'IN',
              value: ['URGENT_CARE'],
            },
          ],
          operator: 'AND',
        },
      ],
      global_exceptions: [],
    },
  },
  {
    id: 'network_restriction_oon',
    name: 'Network Restriction - OON Imaging',
    description: 'Restrict out-of-network imaging services',
    policy_type: 'NETWORK_RESTRICTION',
    data: {
      name: 'OON Imaging Restriction',
      policy_type: 'NETWORK_RESTRICTION',
      description: 'Restrict out-of-network imaging services to in-network alternatives.',
      owner_role: 'POLICY_ADMIN',
      scope: {
        lob: ['COMMERCIAL'],
        markets: ['NYC'],
        network: ['OUT'],
      },
      effective_period: {
        start_date: new Date().toISOString().split('T')[0],
        end_date: null,
      },
      levers: [
        {
          lever_type: 'NETWORK_RESTRICTION',
          targets: {
            code_type: 'CPT',
            codes: ['72141', '72142', '70450', '70460'],
            code_groups: ['ADVANCED_IMAGING'],
          },
          config: {
            allowed_network: ['IN'],
            oon_allowed: false,
            oon_cost_sharing: null,
          },
          priority: 1,
        },
      ],
      apply_when: [],
      global_exceptions: [
        {
          field: 'emergency',
          operator: 'EQUALS',
          value: 'true',
          description: 'Allow OON in emergencies',
        },
      ],
    },
  },
  {
    id: 'compound_imaging_bundle',
    name: 'Compound Policy - Advanced Imaging Bundle',
    description: 'Combined PA and frequency controls for advanced imaging',
    policy_type: 'COMPOSITE',
    data: {
      name: 'Advanced Imaging Control Bundle',
      policy_type: 'COMPOSITE',
      description: 'Combined PA and frequency controls for advanced imaging.',
      owner_role: 'UM_LEADER',
      scope: {
        lob: ['COMMERCIAL'],
        markets: ['NYC'],
        network: ['IN'],
      },
      effective_period: {
        start_date: new Date().toISOString().split('T')[0],
        end_date: null,
      },
      levers: [
        {
          lever_type: 'PRIOR_AUTH',
          targets: {
            code_type: 'CPT',
            codes: ['70551', '70552', '70553'],
            code_groups: [],
          },
          config: {
            requires_pa: true,
            pa_touchpoint: 'PA_WORKFLOW',
            override_allowed: false,
          },
          priority: 1,
        },
        {
          lever_type: 'DURATION_FREQUENCY_LIMIT',
          targets: {
            code_type: 'CPT',
            codes: ['70551', '70552', '70553'],
            code_groups: [],
          },
          config: {
            max_visits: 2,
            time_period: 'YEAR',
            reset_date: 'CALENDAR_YEAR',
            accumulate_across_providers: false,
          },
          priority: 2,
        },
      ],
      apply_when: [],
      global_exceptions: [],
    },
  },
]

