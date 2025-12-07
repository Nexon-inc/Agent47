/**
 * Frontend End-to-End Test Suite for Agent47
 * Tests the complete user journey through the frontend interface
 */

import { test, expect, Page, BrowserContext } from '@playwright/test';

interface TestUser {
  email: string;
  password: string;
  username: string;
  fullName: string;
}

class FrontendTestSuite {
  private page: Page;
  private context: BrowserContext;
  private testUser: TestUser;
  private testResults: Array<{
    test: string;
    success: boolean;
    details: string;
    error?: string;
    timestamp: string;
  }> = [];

  constructor(page: Page, context: BrowserContext) {
    this.page = page;
    this.context = context;
    this.testUser = {
      email: `test_${Date.now()}_${Math.random().toString(36).substr(2, 6)}@example.com`,
      password: 'TestPassword123!',
      username: `testuser_${Date.now()}`,
      fullName: 'Test User'
    };
  }

  private logTestResult(testName: string, success: boolean, details: string = '', error: string = '') {
    const result = {
      test: testName,
      success,
      details,
      error,
      timestamp: new Date().toISOString()
    };
    this.testResults.push(result);
    
    const status = success ? '✅ PASS' : '❌ FAIL';
    console.log(`${status} ${testName}`);
    if (details) console.log(`   Details: ${details}`);
    if (error) console.log(`   Error: ${error}`);
  }

  async testFrontendHealth(): Promise<boolean> {
    try {
      await this.page.goto('http://localhost:3000');
      await this.page.waitForLoadState('networkidle');
      
      const title = await this.page.title();
      if (title.includes('Agent47') || title.includes('Agent')) {
        this.logTestResult('Frontend Health Check', true, `Page loaded: ${title}`);
        return true;
      } else {
        this.logTestResult('Frontend Health Check', false, `Unexpected title: ${title}`);
        return false;
      }
    } catch (error) {
      this.logTestResult('Frontend Health Check', false, '', String(error));
      return false;
    }
  }

  async testSignupFlow(): Promise<boolean> {
    try {
      // Navigate to signup page
      await this.page.goto('http://localhost:3000/auth');
      await this.page.waitForLoadState('networkidle');

      // Fill signup form
      await this.page.fill('input[name="email"]', this.testUser.email);
      await this.page.fill('input[name="password"]', this.testUser.password);
      await this.page.fill('input[name="username"]', this.testUser.username);
      await this.page.fill('input[name="fullName"]', this.testUser.fullName);

      // Submit form
      await this.page.click('button[type="submit"]');
      
      // Wait for redirect or success message
      await this.page.waitForTimeout(3000);
      
      // Check if we're redirected to onboarding or dashboard
      const currentUrl = this.page.url();
      if (currentUrl.includes('/onboarding') || currentUrl.includes('/dashboard')) {
        this.logTestResult('User Signup', true, `Redirected to: ${currentUrl}`);
        return true;
      } else {
        this.logTestResult('User Signup', false, `Unexpected redirect: ${currentUrl}`);
        return false;
      }
    } catch (error) {
      this.logTestResult('User Signup', false, '', String(error));
      return false;
    }
  }

  async testOnboardingFlow(): Promise<boolean> {
    try {
      // Wait for onboarding page to load
      await this.page.waitForSelector('[data-testid="onboarding-form"]', { timeout: 10000 });
      
      // Fill profile information
      await this.page.fill('input[name="fullName"]', 'Test User');
      await this.page.fill('input[name="company"]', 'Test Company');
      await this.page.fill('input[name="jobTitle"]', 'Software Engineer');
      await this.page.fill('input[name="location"]', 'Test City');
      await this.page.fill('input[name="website"]', 'https://test.com');
      
      // Select role and industry
      await this.page.selectOption('select[name="role"]', 'developer');
      await this.page.selectOption('select[name="industry"]', 'technology');
      
      // Fill business information
      await this.page.fill('input[name="businessName"]', 'Test Business');
      await this.page.fill('input[name="businessWebsite"]', 'https://testbusiness.com');
      await this.page.selectOption('select[name="businessSize"]', 'small');
      await this.page.selectOption('select[name="businessStage"]', 'startup');
      
      // Select primary goals
      await this.page.check('input[value="Increase Productivity"]');
      await this.page.check('input[value="Automate Tasks"]');
      
      // Fill main purpose
      await this.page.fill('textarea[name="mainPurpose"]', 'Testing the system');
      
      // Complete onboarding
      await this.page.click('button[type="submit"]');
      
      // Wait for redirect to pricing
      await this.page.waitForTimeout(3000);
      
      const currentUrl = this.page.url();
      if (currentUrl.includes('/pricing')) {
        this.logTestResult('Onboarding Flow', true, `Redirected to pricing: ${currentUrl}`);
        return true;
      } else {
        this.logTestResult('Onboarding Flow', false, `Unexpected redirect: ${currentUrl}`);
        return false;
      }
    } catch (error) {
      this.logTestResult('Onboarding Flow', false, '', String(error));
      return false;
    }
  }

  async testPricingFlow(): Promise<boolean> {
    try {
      // Wait for pricing page to load
      await this.page.waitForSelector('[data-testid="pricing-plans"]', { timeout: 10000 });
      
      // Select free tier
      await this.page.click('button[data-tier="free"]');
      
      // Wait for confirmation or redirect
      await this.page.waitForTimeout(3000);
      
      const currentUrl = this.page.url();
      if (currentUrl.includes('/dashboard')) {
        this.logTestResult('Pricing Flow', true, `Redirected to dashboard: ${currentUrl}`);
        return true;
      } else {
        this.logTestResult('Pricing Flow', false, `Unexpected redirect: ${currentUrl}`);
        return false;
      }
    } catch (error) {
      this.logTestResult('Pricing Flow', false, '', String(error));
      return false;
    }
  }

  async testAgentSelectionModal(): Promise<boolean> {
    try {
      // Wait for dashboard to load
      await this.page.waitForSelector('[data-testid="dashboard"]', { timeout: 10000 });
      
      // Check if agent selection modal appears
      const modalVisible = await this.page.isVisible('[data-testid="agent-selection-modal"]');
      
      if (modalVisible) {
        // Select Aria agent (free tier can select 1 agent)
        await this.page.click('input[value="aria"]');
        
        // Confirm selection
        await this.page.click('button[data-testid="confirm-agent-selection"]');
        
        // Wait for modal to close
        await this.page.waitForTimeout(2000);
        
        const modalStillVisible = await this.page.isVisible('[data-testid="agent-selection-modal"]');
        if (!modalStillVisible) {
          this.logTestResult('Agent Selection Modal', true, 'Agent selected and modal closed');
          return true;
        } else {
          this.logTestResult('Agent Selection Modal', false, 'Modal did not close after selection');
          return false;
        }
      } else {
        this.logTestResult('Agent Selection Modal', false, 'Agent selection modal did not appear');
        return false;
      }
    } catch (error) {
      this.logTestResult('Agent Selection Modal', false, '', String(error));
      return false;
    }
  }

  async testDashboardTabs(): Promise<boolean> {
    try {
      // Test each dashboard tab
      const tabs = [
        { name: 'Home', testId: 'home-tab' },
        { name: 'Agents', testId: 'agents-tab' },
        { name: 'Account', testId: 'account-tab' },
        { name: 'Analytics', testId: 'analytics-tab' },
        { name: 'Platforms', testId: 'platforms-tab' },
        { name: 'History', testId: 'history-tab' }
      ];

      let allTabsWorking = true;

      for (const tab of tabs) {
        try {
          // Click on tab
          await this.page.click(`[data-testid="${tab.testId}"]`);
          await this.page.waitForTimeout(1000);
          
          // Check if tab content is visible
          const contentVisible = await this.page.isVisible(`[data-testid="${tab.testId}-content"]`);
          
          if (contentVisible) {
            this.logTestResult(`${tab.name} Tab`, true, 'Tab content loaded successfully');
          } else {
            this.logTestResult(`${tab.name} Tab`, false, 'Tab content not visible');
            allTabsWorking = false;
          }
        } catch (error) {
          this.logTestResult(`${tab.name} Tab`, false, '', String(error));
          allTabsWorking = false;
        }
      }

      return allTabsWorking;
    } catch (error) {
      this.logTestResult('Dashboard Tabs', false, '', String(error));
      return false;
    }
  }

  async testAccountTabData(): Promise<boolean> {
    try {
      // Navigate to account tab
      await this.page.click('[data-testid="account-tab"]');
      await this.page.waitForTimeout(2000);
      
      // Check if user data is displayed
      const emailVisible = await this.page.isVisible('[data-testid="user-email"]');
      const profileDataVisible = await this.page.isVisible('[data-testid="profile-data"]');
      
      if (emailVisible && profileDataVisible) {
        this.logTestResult('Account Tab Data', true, 'User data displayed in account tab');
        return true;
      } else {
        this.logTestResult('Account Tab Data', false, 'User data not displayed in account tab');
        return false;
      }
    } catch (error) {
      this.logTestResult('Account Tab Data', false, '', String(error));
      return false;
    }
  }

  async testPlatformConnections(): Promise<boolean> {
    try {
      // Navigate to platforms tab
      await this.page.click('[data-testid="platforms-tab"]');
      await this.page.waitForTimeout(2000);
      
      // Check if platforms are listed
      const platformsVisible = await this.page.isVisible('[data-testid="platforms-list"]');
      
      if (platformsVisible) {
        // Try to connect to a platform (if available)
        const connectButtons = await this.page.$$('[data-testid="connect-platform"]');
        if (connectButtons.length > 0) {
          await connectButtons[0].click();
          await this.page.waitForTimeout(2000);
          
          this.logTestResult('Platform Connections', true, 'Platform connection initiated');
          return true;
        } else {
          this.logTestResult('Platform Connections', true, 'Platforms listed but no connect buttons');
          return true;
        }
      } else {
        this.logTestResult('Platform Connections', false, 'Platforms not visible');
        return false;
      }
    } catch (error) {
      this.logTestResult('Platform Connections', false, '', String(error));
      return false;
    }
  }

  async testAgentChat(): Promise<boolean> {
    try {
      // Navigate to agents tab
      await this.page.click('[data-testid="agents-tab"]');
      await this.page.waitForTimeout(2000);
      
      // Check if selected agents are displayed
      const agentsVisible = await this.page.isVisible('[data-testid="selected-agents"]');
      
      if (agentsVisible) {
        // Try to send a message to an agent
        const chatInput = await this.page.$('[data-testid="agent-chat-input"]');
        if (chatInput) {
          await chatInput.fill('Hello, this is a test message');
          await this.page.click('[data-testid="send-message"]');
          await this.page.waitForTimeout(2000);
          
          this.logTestResult('Agent Chat', true, 'Message sent to agent');
          return true;
        } else {
          this.logTestResult('Agent Chat', true, 'Agents visible but no chat input');
          return true;
        }
      } else {
        this.logTestResult('Agent Chat', false, 'Selected agents not visible');
        return false;
      }
    } catch (error) {
      this.logTestResult('Agent Chat', false, '', String(error));
      return false;
    }
  }

  async runCompleteTestSuite(): Promise<boolean> {
    console.log('🚀 Starting Frontend Test Suite');
    console.log('=' * 50);
    
    // Test frontend health
    if (!await this.testFrontendHealth()) {
      console.log('❌ Frontend is not running. Please start the frontend server first.');
      return false;
    }

    // Authentication flow
    console.log('\n📝 Testing Authentication Flow');
    console.log('-'.repeat(30));
    await this.testSignupFlow();

    // Onboarding flow
    console.log('\n📋 Testing Onboarding Flow');
    console.log('-'.repeat(30));
    await this.testOnboardingFlow();

    // Pricing flow
    console.log('\n💳 Testing Pricing Flow');
    console.log('-'.repeat(30));
    await this.testPricingFlow();

    // Agent selection
    console.log('\n🤖 Testing Agent Selection');
    console.log('-'.repeat(30));
    await this.testAgentSelectionModal();

    // Dashboard functionality
    console.log('\n📊 Testing Dashboard Functionality');
    console.log('-'.repeat(30));
    await this.testDashboardTabs();
    await this.testAccountTabData();
    await this.testPlatformConnections();
    await this.testAgentChat();

    // Generate report
    this.generateTestReport();

    return true;
  }

  generateTestReport(): void {
    console.log('\n📊 Frontend Test Results Summary');
    console.log('=' * 50);
    
    const totalTests = this.testResults.length;
    const passedTests = this.testResults.filter(r => r.success).length;
    const failedTests = totalTests - passedTests;
    
    console.log(`Total Tests: ${totalTests}`);
    console.log(`Passed: ${passedTests}`);
    console.log(`Failed: ${failedTests}`);
    console.log(`Success Rate: ${(passedTests/totalTests)*100:.1f}%`);
    
    if (failedTests > 0) {
      console.log('\n❌ Failed Tests:');
      this.testResults
        .filter(r => !r.success)
        .forEach(result => {
          console.log(`  - ${result.test}: ${result.error || result.details}`);
        });
    }
  }
}

// Playwright test configuration
test.describe('Agent47 Frontend E2E Tests', () => {
  test('Complete User Journey', async ({ page, context }) => {
    const testSuite = new FrontendTestSuite(page, context);
    await testSuite.runCompleteTestSuite();
  });
});

export { FrontendTestSuite };
