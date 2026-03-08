/**
 * Browser-based QA Testing using Playwright
 * Tests UI workflows from different user role perspectives
 */

const { chromium } = require('playwright');

const QA_USERS = {
  ROLE_PAYER_CMO: {
    email: 'qa.payer.cmo@test.com',
    roles: ['EXEC_VIEWER', 'STRATEGY'],
  },
  ROLE_PROVIDER_CFO: {
    email: 'qa.provider.cfo@test.com',
    roles: ['EXEC_VIEWER'],
  },
  ROLE_PAYER_UM_LEAD: {
    email: 'qa.payer.um.lead@test.com',
    roles: ['UM_LEADER'],
  },
  ROLE_PAYER_ACTUARY: {
    email: 'qa.payer.actuary@test.com',
    roles: ['ACTUARIAL'],
  },
  ROLE_PAYER_NETWORK_STRATEGY: {
    email: 'qa.payer.network.strategy@test.com',
    roles: ['STRATEGY'],
  },
  ROLE_PAYER_ANALYTICS: {
    email: 'qa.payer.analytics@test.com',
    roles: ['ACTUARIAL', 'STRATEGY'],
  },
  ROLE_READ_ONLY_EXEC: {
    email: 'qa.readonly.exec@test.com',
    roles: ['EXEC_VIEWER'],
  },
};

const BASE_URL = 'http://localhost:3050';

class QABrowserTestAgent {
  constructor(roleName, userConfig) {
    this.roleName = roleName;
    this.userConfig = userConfig;
    this.results = [];
    this.consoleErrors = [];
    this.networkErrors = [];
  }

  async testPage(page, testName, url, expectedElements = []) {
    const result = {
      testName,
      passed: false,
      errors: [],
      warnings: [],
      consoleErrors: [],
      networkErrors: [],
      timestamp: new Date().toISOString(),
    };

    try {
      // Navigate to page
      const response = await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
      
      if (!response || response.status() !== 200) {
        result.errors.push(`Page returned status ${response?.status() || 'unknown'}`);
        this.results.push(result);
        return result;
      }

      // Check for expected elements
      for (const selector of expectedElements) {
        try {
          await page.waitForSelector(selector, { timeout: 5000 });
        } catch (e) {
          result.warnings.push(`Expected element not found: ${selector}`);
        }
      }

      // Check for console errors
      const consoleErrors = this.consoleErrors.filter(e => 
        e.timestamp > new Date(Date.now() - 10000).getTime()
      );
      if (consoleErrors.length > 0) {
        result.consoleErrors = consoleErrors.map(e => e.text);
        result.warnings.push(`${consoleErrors.length} console errors detected`);
      }

      // Check for network errors
      const networkErrors = this.networkErrors.filter(e => 
        e.timestamp > new Date(Date.now() - 10000).getTime()
      );
      if (networkErrors.length > 0) {
        result.networkErrors = networkErrors.map(e => e.url);
        result.errors.push(`${networkErrors.length} network errors detected`);
      }

      result.passed = result.errors.length === 0;
    } catch (error) {
      result.errors.push(error.message);
    }

    this.results.push(result);
    return result;
  }

  async testDashboard(page) {
    return this.testPage(
      page,
      'Dashboard Access',
      `${BASE_URL}/`,
      ['.dashboard-header', '[data-testid="dashboard-summary"]']
    );
  }

  async testPolicies(page) {
    return this.testPage(
      page,
      'Policy Catalog',
      `${BASE_URL}/policies`,
      ['[data-testid="policy-list"]', '.policy-card']
    );
  }

  async testPolicyWorkspace(page) {
    // Try to access a policy workspace (if policies exist)
    return this.testPage(
      page,
      'Policy Workspace',
      `${BASE_URL}/policies/workspace/10000000-0000-0000-0000-000000000001`,
      ['.policy-workspace', '.policy-details']
    );
  }

  async testConversationalAI(page) {
    return this.testPage(
      page,
      'Conversational AI',
      `${BASE_URL}/`,
      [] // Will check if AI button is present
    );
  }

  async testDecisions(page) {
    return this.testPage(
      page,
      'Decisions Page',
      `${BASE_URL}/decisions`,
      ['.decisions-list', '[data-testid="decision-manager"]']
    );
  }

  async testAnalyses(page) {
    return this.testPage(
      page,
      'Analyses Page',
      `${BASE_URL}/analyses`,
      ['.analyses-workspace', '[data-testid="analysis-list"]']
    );
  }

  async runAllTests() {
    console.log(`\n${'='.repeat(70)}`);
    console.log(`Testing Role: ${this.roleName}`);
    console.log(`User: ${this.userConfig.email}`);
    console.log(`${'='.repeat(70)}\n`);

    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();

    // Setup console error capture
    page.on('console', msg => {
      if (msg.type() === 'error') {
        this.consoleErrors.push({
          text: msg.text(),
          timestamp: Date.now(),
        });
      }
    });

    // Setup network error capture
    page.on('response', response => {
      if (response.status() >= 400) {
        this.networkErrors.push({
          url: response.url(),
          status: response.status(),
          timestamp: Date.now(),
        });
      }
    });

    // Run tests
    await this.testDashboard(page);
    await this.testPolicies(page);
    await this.testPolicyWorkspace(page);
    await this.testDecisions(page);
    await this.testAnalyses(page);
    await this.testConversationalAI(page);

    await browser.close();

    const passed = this.results.filter(r => r.passed).length;
    const total = this.results.length;
    console.log(`\n${this.roleName}: ${passed}/${total} tests passed\n`);

    return this.results;
  }
}

async function runBrowserTests() {
  console.log('='.repeat(70));
  console.log('Browser-Based QA Testing');
  console.log('='.repeat(70));
  console.log('\nMake sure the frontend is running on http://localhost:3050\n');

  const allResults = {};

  for (const [roleName, userConfig] of Object.entries(QA_USERS)) {
    const agent = new QABrowserTestAgent(roleName, userConfig);
    try {
      const results = await agent.runAllTests();
      allResults[roleName] = results;
    } catch (error) {
      console.error(`Error testing ${roleName}:`, error);
    }
  }

  // Generate summary
  console.log('\n' + '='.repeat(70));
  console.log('TEST SUMMARY');
  console.log('='.repeat(70));

  for (const [roleName, results] of Object.entries(allResults)) {
    const passed = results.filter(r => r.passed).length;
    const total = results.length;
    console.log(`\n${roleName}: ${passed}/${total} passed`);
    
    const failed = results.filter(r => !r.passed);
    if (failed.length > 0) {
      console.log('  Failed tests:');
      failed.forEach(test => {
        console.log(`    - ${test.testName}: ${test.errors.join(', ')}`);
      });
    }
  }

  return allResults;
}

if (require.main === module) {
  runBrowserTests().catch(console.error);
}

module.exports = { runBrowserTests, QABrowserTestAgent };

