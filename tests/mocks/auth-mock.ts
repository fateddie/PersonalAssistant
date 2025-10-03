/**
 * Test Authentication Mock
 * Provides mock authentication ONLY for Playwright tests
 * Production always uses real NextAuth/Supabase authentication
 */

import { Page } from '@playwright/test'

export interface MockUser {
  id: string
  email: string
  name: string
  avatar_url?: string
}

export interface MockSession {
  user: MockUser
  expires: string
}

export const TEST_USER: MockUser = {
  id: 'test-user-123',
  email: 'test@example.com',
  name: 'Test User',
  avatar_url: null
}

export const TEST_SESSION: MockSession = {
  user: TEST_USER,
  expires: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
}

export const MOCK_DASHBOARD_DATA = {
  tasks: {
    total: 12,
    pending: 5,
    completed: 7,
    completedToday: 3,
    highPriority: 2
  },
  habits: {
    total: 4,
    completedToday: 2,
    longestStreak: 15,
    currentStreaks: [
      { name: 'Morning Exercise', streak: 7 },
      { name: 'Read 30 min', streak: 5 },
      { name: 'Meditation', streak: 3 }
    ]
  },
  calendar: {
    todayEvents: 3,
    weekEvents: 12,
    upcomingEvents: [
      {
        title: 'Team Meeting',
        startTime: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString()
      },
      {
        title: 'Project Review',
        startTime: new Date(Date.now() + 4 * 60 * 60 * 1000).toISOString()
      }
    ]
  },
  email: {
    unreadCount: 8,
    accounts: 1
  }
}

/**
 * Setup mock authentication for Playwright tests
 * This ONLY affects the test environment
 */
export async function setupMockAuth(page: Page, options: {
  authenticated?: boolean
  hasGoogleAccess?: boolean
  user?: MockUser
  dashboardData?: any
} = {}) {
  const {
    authenticated = true,
    hasGoogleAccess = true,
    user = TEST_USER,
    dashboardData = MOCK_DASHBOARD_DATA
  } = options

  // Mock NextAuth session endpoint
  await page.route('**/api/auth/session', async (route) => {
    if (authenticated) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          user,
          expires: TEST_SESSION.expires
        })
      })
    } else {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({})
      })
    }
  })

  // Mock user profile endpoint
  await page.route('**/api/user/profile', async (route) => {
    if (authenticated) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          user: {
            ...user,
            has_google_access: hasGoogleAccess
          }
        })
      })
    } else {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Unauthorized' })
      })
    }
  })

  // Mock dashboard data endpoint
  await page.route('**/api/dashboard', async (route) => {
    if (authenticated && hasGoogleAccess) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: dashboardData
        })
      })
    } else {
      await route.fulfill({
        status: authenticated ? 403 : 401,
        contentType: 'application/json',
        body: JSON.stringify({
          error: authenticated ? 'Google access required' : 'Unauthorized'
        })
      })
    }
  })

  // Mock tasks endpoint
  await page.route('**/api/tasks*', async (route) => {
    const method = route.request().method()

    if (!authenticated) {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Unauthorized' })
      })
      return
    }

    if (method === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: [
            {
              id: 'task-1',
              user_id: user.id,
              title: 'Test Task 1',
              status: 'pending',
              priority: 'high',
              created_at: new Date().toISOString()
            },
            {
              id: 'task-2',
              user_id: user.id,
              title: 'Test Task 2',
              status: 'completed',
              priority: 'medium',
              completed_at: new Date().toISOString(),
              created_at: new Date().toISOString()
            }
          ]
        })
      })
    } else if (method === 'POST') {
      const postData = await route.request().postDataJSON()
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          task: {
            id: `task-${Date.now()}`,
            ...postData,
            created_at: new Date().toISOString()
          }
        })
      })
    } else {
      await route.continue()
    }
  })

  // Mock habits endpoint
  await page.route('**/api/habits*', async (route) => {
    const method = route.request().method()

    if (!authenticated) {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Unauthorized' })
      })
      return
    }

    if (method === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: [
            {
              id: 'habit-1',
              user_id: user.id,
              name: 'Morning Exercise',
              frequency: 'daily',
              target_count: 1,
              is_active: true,
              created_at: new Date().toISOString()
            },
            {
              id: 'habit-2',
              user_id: user.id,
              name: 'Read 30 min',
              frequency: 'daily',
              target_count: 1,
              is_active: true,
              created_at: new Date().toISOString()
            }
          ]
        })
      })
    } else if (method === 'POST') {
      const postData = await route.request().postDataJSON()
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          habit: {
            id: `habit-${Date.now()}`,
            ...postData,
            created_at: new Date().toISOString()
          }
        })
      })
    } else {
      await route.continue()
    }
  })

  // Mock habit entries endpoint
  await page.route('**/api/habits/*/entries*', async (route) => {
    if (!authenticated) {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Unauthorized' })
      })
      return
    }

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        entries: []
      })
    })
  })

  // Mock Google auth providers endpoint
  await page.route('**/api/auth/providers*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        google: {
          id: 'google',
          name: 'Google',
          type: 'oauth',
          signinUrl: '/api/auth/signin/google',
          callbackUrl: '/api/auth/callback/google'
        }
      })
    })
  })
}

/**
 * Setup unauthenticated session for testing login flows
 */
export async function setupUnauthenticatedMock(page: Page) {
  await setupMockAuth(page, {
    authenticated: false,
    hasGoogleAccess: false
  })
}

/**
 * Setup authenticated session WITHOUT Google access
 */
export async function setupAuthWithoutGoogleMock(page: Page) {
  await setupMockAuth(page, {
    authenticated: true,
    hasGoogleAccess: false
  })
}
