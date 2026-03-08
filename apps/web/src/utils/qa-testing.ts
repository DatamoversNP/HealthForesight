/**
 * Frontend QA Testing Utilities
 * Tests UI workflows from different user role perspectives
 */

import { apiClient } from '../lib/api'

export interface QATestResult {
  testName: string
  role: string
  passed: boolean
  errors: string[]
  warnings: string[]
  consoleErrors: string[]
  timestamp: string
}

export interface QATestSuite {
  role: string
  tests: QATestResult[]
  summary: {
    total: number
    passed: number
    failed: number
    passRate: string
  }
}

// QA Test Users Configuration
export const QA_USERS = {
  ROLE_PAYER_CMO: {
    email: 'qa.payer.cmo@test.com',
    userId: '10000000-0000-0000-0000-000000000001',
    roles: ['EXEC_VIEWER', 'STRATEGY'],
  },
  ROLE_PROVIDER_CFO: {
    email: 'qa.provider.cfo@test.com',
    userId: '10000000-0000-0000-0000-000000000002',
    roles: ['EXEC_VIEWER'],
  },
  ROLE_PAYER_UM_LEAD: {
    email: 'qa.payer.um.lead@test.com',
    userId: '10000000-0000-0000-0000-000000000003',
    roles: ['UM_LEADER'],
  },
  ROLE_PAYER_ACTUARY: {
    email: 'qa.payer.actuary@test.com',
    userId: '10000000-0000-0000-0000-000000000004',
    roles: ['ACTUARIAL'],
  },
  ROLE_PAYER_NETWORK_STRATEGY: {
    email: 'qa.payer.network.strategy@test.com',
    userId: '10000000-0000-0000-0000-000000000005',
    roles: ['STRATEGY'],
  },
  ROLE_PAYER_ANALYTICS: {
    email: 'qa.payer.analytics@test.com',
    userId: '10000000-0000-0000-0000-000000000006',
    roles: ['ACTUARIAL', 'STRATEGY'],
  },
  ROLE_READ_ONLY_EXEC: {
    email: 'qa.readonly.exec@test.com',
    userId: '10000000-0000-0000-0000-000000000007',
    roles: ['EXEC_VIEWER'],
  },
}

export class QATestAgent {
  private role: string
  private userConfig: typeof QA_USERS[keyof typeof QA_USERS]
  private results: QATestResult[] = []
  private consoleErrors: string[] = []

  constructor(role: string, userConfig: typeof QA_USERS[keyof typeof QA_USERS]) {
    this.role = role
    this.userConfig = userConfig
    
    // Capture console errors
    this.setupConsoleErrorCapture()
  }

  private setupConsoleErrorCapture() {
    const originalError = console.error
    console.error = (...args: any[]) => {
      this.consoleErrors.push(args.map(a => String(a)).join(' '))
      originalError.apply(console, args)
    }
  }

  async testEndpoint(
    testName: string,
    apiCall: () => Promise<any>,
    expectedSuccess: boolean = true
  ): Promise<QATestResult> {
    const result: QATestResult = {
      testName,
      role: this.role,
      passed: false,
      errors: [],
      warnings: [],
      consoleErrors: [...this.consoleErrors],
      timestamp: new Date().toISOString(),
    }

    try {
      await apiCall()
      result.passed = expectedSuccess
      if (!expectedSuccess) {
        result.errors.push('Expected failure but call succeeded')
      }
    } catch (error: any) {
      if (expectedSuccess) {
        result.errors.push(error.message || String(error))
        if (error.response?.status === 403) {
          result.errors.push('Permission denied - role may not have access')
        } else if (error.response?.status === 404) {
          result.errors.push('Resource not found')
        } else if (error.response?.status === 500) {
          result.errors.push('Internal server error')
        }
      } else {
        result.passed = true // Expected failure
      }
    }

    this.results.push(result)
    return result
  }

  async testDashboardAccess(): Promise<QATestResult> {
    return this.testEndpoint('Dashboard Access', async () => {
      await apiClient.getDashboardSummary()
    })
  }

  async testPolicyList(): Promise<QATestResult> {
    return this.testEndpoint('List Policies', async () => {
      await apiClient.listPolicies({ limit: 10 })
    })
  }

  async testPolicyCreate(): Promise<QATestResult> {
    const canCreate = this.userConfig.roles.includes('UM_LEADER') || 
                     this.userConfig.roles.includes('POLICY_ADMIN')
    
    return this.testEndpoint('Create Policy', async () => {
      await apiClient.createPolicy({
        name: `QA Test Policy - ${this.role}`,
        description: 'Test policy',
        policy_type: 'PRIOR AUTH',
        status: 'DRAFT',
      })
    }, canCreate)
  }

  async testConversationalAI(): Promise<QATestResult> {
    return this.testEndpoint('Conversational AI Access', async () => {
      await apiClient.listConversations()
    })
  }

  async testDecisionsAccess(): Promise<QATestResult> {
    return this.testEndpoint('Decisions Access', async () => {
      await apiClient.listDecisions({ limit: 10 })
    })
  }

  async runAllTests(): Promise<QATestSuite> {
    console.log(`\n${'='.repeat(70)}`)
    console.log(`Testing Role: ${this.role}`)
    console.log(`User: ${this.userConfig.email}`)
    console.log(`${'='.repeat(70)}\n`)

    await this.testDashboardAccess()
    await this.testPolicyList()
    await this.testPolicyCreate()
    await this.testConversationalAI()
    await this.testDecisionsAccess()

    const passed = this.results.filter(r => r.passed).length
    const total = this.results.length

    return {
      role: this.role,
      tests: this.results,
      summary: {
        total,
        passed,
        failed: total - passed,
        passRate: `${((passed / total) * 100).toFixed(1)}%`,
      },
    }
  }

  getResults(): QATestResult[] {
    return this.results
  }
}

export async function runQATests(): Promise<QATestSuite[]> {
  const suites: QATestSuite[] = []

  for (const [roleName, userConfig] of Object.entries(QA_USERS)) {
    const agent = new QATestAgent(roleName, userConfig)
    const suite = await agent.runAllTests()
    suites.push(suite)
  }

  return suites
}

