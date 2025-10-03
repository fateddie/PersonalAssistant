import { test, expect, type Page } from '@playwright/test'
import { setupMockAuth } from './mocks/auth-mock'

/**
 * Personal Assistant App Health Tests
 *
 * These tests automatically verify the app is working correctly and
 * provide detailed error reporting for automated debugging.
 *
 * IMPORTANT: Uses mock authentication for testing only.
 * Production always uses real NextAuth/Supabase authentication.
 */

class AppHealthChecker {
  constructor(private page: Page) {}

  async checkPageLoad() {
    // Check if page loads without errors
    const errors: string[] = []

    this.page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(`Console Error: ${msg.text()}`)
      }
    })

    this.page.on('pageerror', error => {
      errors.push(`Page Error: ${error.message}`)
    })

    await this.page.goto('/')

    // Wait for main content to load
    await this.page.waitForSelector('h1', { timeout: 10000 })

    return { errors }
  }

  async checkUIComponents() {
    const issues: string[] = []

    // Check header exists
    const header = await this.page.locator('header').count()
    if (header === 0) {
      issues.push('Header component not found')
    }

    // Check voice control panel
    const voiceControl = await this.page.getByText(/voice assistant/i).count()
    if (voiceControl === 0) {
      issues.push('Voice Control component not found')
    }

    // Check task manager
    const taskManager = await this.page.getByText('Task Manager').count()
    if (taskManager === 0) {
      issues.push('Task Manager component not found')
    }

    // Check habit tracker
    const habitTracker = await this.page.getByText('Habit Tracker').count()
    if (habitTracker === 0) {
      issues.push('Habit Tracker component not found')
    }

    // Check Today's Focus section (wait for dashboard data to load)
    try {
      await this.page.waitForSelector('text=/today\'s focus/i', { timeout: 5000 })
    } catch (error) {
      issues.push('Today\'s Focus section not found')
    }

    return { issues }
  }

  async checkTaskManagement() {
    const issues: string[] = []

    try {
      // Check if task input exists using data-testid
      const taskInput = this.page.locator('[data-testid="task-input"]')
      if (await taskInput.count() === 0) {
        issues.push('Task input field not found')
        return { issues }
      }

      // Try to add a task
      await taskInput.fill('Test task from Playwright')
      await taskInput.press('Enter')

      // Wait for the task to appear in the list
      try {
        await this.page.waitForSelector('text=/Test task from Playwright/i', { timeout: 3000 })
      } catch (error) {
        issues.push('Task was not added successfully')
      }

      // Try to complete the task
      const taskCircle = this.page.locator('[data-testid="task-circle"]').first()
      if (await taskCircle.count() > 0) {
        await taskCircle.click()
        await this.page.waitForTimeout(500)
      } else {
        // Look for any circle/checkbox near the test task
        const circles = this.page.locator('button').filter({ hasText: /circle|check/i })
        if (await circles.count() > 0) {
          await circles.first().click()
          await this.page.waitForTimeout(500)
        }
      }

    } catch (error) {
      issues.push(`Task management error: ${error}`)
    }

    return { issues }
  }

  async checkHabitTracking() {
    const issues: string[] = []

    try {
      // Check if habit input exists using data-testid
      const habitInput = this.page.locator('[data-testid="habit-input"]')
      if (await habitInput.count() === 0) {
        issues.push('Habit input field not found')
        return { issues }
      }

      // Try to add a habit
      await habitInput.fill('Test habit from Playwright')
      await habitInput.press('Enter')

      // Wait for the habit to appear in the list
      try {
        await this.page.waitForSelector('text=/Test habit from Playwright/i', { timeout: 3000 })
      } catch (error) {
        issues.push('Habit was not added successfully')
      }

      // Look for completion buttons (circles, checkboxes, etc.)
      const completionButtons = this.page.locator('button').filter({
        has: this.page.locator('svg')
      })

      if (await completionButtons.count() > 0) {
        await completionButtons.first().click()
        await this.page.waitForTimeout(500)
      }

    } catch (error) {
      issues.push(`Habit tracking error: ${error}`)
    }

    return { issues }
  }

  async checkVoiceInterface() {
    const issues: string[] = []

    try {
      // Check for voice control elements
      const micButton = this.page.locator('button').filter({ hasText: /mic|voice/i })
      if (await micButton.count() === 0) {
        // Look for microphone icon
        const micIcon = this.page.locator('[data-testid="mic-button"], button:has(svg)').filter({
          has: this.page.locator('svg')
        })

        if (await micIcon.count() === 0) {
          issues.push('Voice control microphone button not found')
        }
      }

      // Check for voice status indicators
      const voiceStatus = await this.page.getByText(/listening|ready|voice/i).count()
      if (voiceStatus === 0) {
        issues.push('Voice status indicator not found')
      }

    } catch (error) {
      issues.push(`Voice interface error: ${error}`)
    }

    return { issues }
  }

  async checkResponsiveDesign() {
    const issues: string[] = []

    try {
      // Test mobile viewport
      await this.page.setViewportSize({ width: 375, height: 667 })
      await this.page.waitForTimeout(500)

      // Check if components are still visible
      const mainContent = await this.page.locator('main').count()
      if (mainContent === 0) {
        issues.push('Main content not visible on mobile viewport')
      }

      // Test tablet viewport
      await this.page.setViewportSize({ width: 768, height: 1024 })
      await this.page.waitForTimeout(500)

      // Test desktop viewport
      await this.page.setViewportSize({ width: 1280, height: 720 })
      await this.page.waitForTimeout(500)

    } catch (error) {
      issues.push(`Responsive design error: ${error}`)
    }

    return { issues }
  }

  async checkPerformance() {
    const issues: string[] = []

    try {
      // Measure load time
      const startTime = Date.now()
      await this.page.goto('/', { waitUntil: 'networkidle' })
      const loadTime = Date.now() - startTime

      if (loadTime > 5000) {
        issues.push(`Slow page load: ${loadTime}ms (should be under 5000ms)`)
      }

      // Check for large images or resources
      const responses = await this.page.evaluate(() => {
        return performance.getEntriesByType('navigation').map(entry => ({
          loadEventEnd: entry.loadEventEnd,
          domContentLoadedEventEnd: entry.domContentLoadedEventEnd
        }))
      })

      if (responses.length > 0 && responses[0].domContentLoadedEventEnd > 3000) {
        issues.push(`Slow DOM load: ${responses[0].domContentLoadedEventEnd}ms`)
      }

    } catch (error) {
      issues.push(`Performance check error: ${error}`)
    }

    return { issues }
  }
}

test.describe('Personal Assistant App Health', () => {
  let healthChecker: AppHealthChecker

  test.beforeEach(async ({ page }) => {
    // Setup mock authentication for tests
    // This ensures tests run consistently without real auth
    // Production always uses real NextAuth/Supabase
    await setupMockAuth(page, {
      authenticated: true,
      hasGoogleAccess: true
    })

    healthChecker = new AppHealthChecker(page)
  })

  test('Page loads without errors', async () => {
    const { errors } = await healthChecker.checkPageLoad()

    if (errors.length > 0) {
      console.log('🚨 Page Load Errors Detected:')
      errors.forEach(error => console.log(`  ❌ ${error}`))
    }

    expect(errors).toHaveLength(0)
  })

  test('All UI components are present', async () => {
    await healthChecker.checkPageLoad()
    const { issues } = await healthChecker.checkUIComponents()

    if (issues.length > 0) {
      console.log('🚨 UI Component Issues:')
      issues.forEach(issue => console.log(`  ❌ ${issue}`))
    }

    expect(issues).toHaveLength(0)
  })

  test('Task management works correctly', async () => {
    await healthChecker.checkPageLoad()
    const { issues } = await healthChecker.checkTaskManagement()

    if (issues.length > 0) {
      console.log('🚨 Task Management Issues:')
      issues.forEach(issue => console.log(`  ❌ ${issue}`))
    }

    expect(issues).toHaveLength(0)
  })

  test('Habit tracking works correctly', async () => {
    await healthChecker.checkPageLoad()
    const { issues } = await healthChecker.checkHabitTracking()

    if (issues.length > 0) {
      console.log('🚨 Habit Tracking Issues:')
      issues.forEach(issue => console.log(`  ❌ ${issue}`))
    }

    expect(issues).toHaveLength(0)
  })

  test('Voice interface is accessible', async () => {
    await healthChecker.checkPageLoad()
    const { issues } = await healthChecker.checkVoiceInterface()

    if (issues.length > 0) {
      console.log('🚨 Voice Interface Issues:')
      issues.forEach(issue => console.log(`  ❌ ${issue}`))
    }

    expect(issues).toHaveLength(0)
  })

  test('Responsive design works across viewports', async () => {
    await healthChecker.checkPageLoad()
    const { issues } = await healthChecker.checkResponsiveDesign()

    if (issues.length > 0) {
      console.log('🚨 Responsive Design Issues:')
      issues.forEach(issue => console.log(`  ❌ ${issue}`))
    }

    expect(issues).toHaveLength(0)
  })

  test('Performance meets standards', async () => {
    const { issues } = await healthChecker.checkPerformance()

    if (issues.length > 0) {
      console.log('🚨 Performance Issues:')
      issues.forEach(issue => console.log(`  ❌ ${issue}`))
    }

    expect(issues).toHaveLength(0)
  })
})

// Generate detailed error report for debugging
test.afterAll(async () => {
  console.log('\n📊 Personal Assistant Health Check Complete')
  console.log('Check test-results/ for detailed reports, screenshots, and videos')
})