'use client'

import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'
import { Header } from '@/components/layout/Header'
import { VoiceControl } from '@/components/features/VoiceControl'
import { TaskManager } from '@/components/features/TaskManager'
import { HabitTracker } from '@/components/features/HabitTracker'
import { DailyCheckin } from '@/components/features/DailyCheckin'
import GoogleAccountPrompt from '@/components/features/GoogleAccountPrompt'
import SyncStatus from '@/components/features/SyncStatus'
import { getGreeting } from '@/lib/utils'
import { useUser } from '@/hooks/useUser'
import { useDashboardData } from '@/hooks/useDashboardData'
import { generateDemoUUID } from '@/lib/uuid'
import type { Habit } from '@/types'

export default function HomePage() {
  const { data: session } = useSession()
  const { user, isAuthenticated, isLoading: userLoading, hasGoogleAccess } = useUser()
  const { data: dashboardData, loading: loadingData, invalidateCache } = useDashboardData()
  const [isListening, setIsListening] = useState(false)
  const [habits, setHabits] = useState<Habit[]>([])
  const greeting = getGreeting()

  // Fetch habits for daily check-in
  useEffect(() => {
    const fetchHabits = async () => {
      try {
        const response = await fetch('/api/habits')
        if (response.ok) {
          const data = await response.json()
          setHabits(data.habits || [])
        }
      } catch (error) {
        console.error('Error fetching habits:', error)
      }
    }

    if (isAuthenticated) {
      fetchHabits()
    }
  }, [isAuthenticated])

  const handleVoiceCommand = async (command: string) => {
    console.log('🎤 Voice command received:', command)

    try {
      // Send to OpenAI for processing
      const response = await fetch('/api/voice/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transcript: command })
      })

      if (response.ok) {
        const data = await response.json()

        // Show the AI-generated response
        if (data.response) {
          alert(data.response)

          // Speak the response if available
          if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(data.response)
            speechSynthesis.speak(utterance)
          }
        }

        // Invalidate cache if task or habit was created
        if (data.command?.intent === 'create_task' || data.command?.intent === 'create_habit') {
          invalidateCache()
        }
      } else {
        const error = await response.json()
        alert(`Error: ${error.error || 'Failed to process command'}`)
      }
    } catch (error) {
      console.error('Voice command error:', error)
      alert(`Failed to process: "${command}"`)
    }
  }

  const toggleVoiceListening = () => {
    setIsListening(!isListening)
  }

  // No loading screen needed - show content immediately
  // Authentication only required when using voice commands or real data features

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#f8fafc'
    }}>
      <Header onVoiceToggle={toggleVoiceListening} isListening={isListening} />

      <main style={{
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '32px 16px'
      }}>
        {/* Welcome Section */}
        <section style={{ marginBottom: '32px' }}>
          <h1 style={{
            fontSize: '30px',
            fontWeight: 'bold',
            marginBottom: '8px',
            color: '#1f2937'
          }}>
            {greeting}{user ? `, ${user.name?.split(' ')[0] || 'User'}` : ''}!
          </h1>
          <p style={{
            color: '#64748b',
            lineHeight: '1.6'
          }}>
            {hasGoogleAccess
              ? `Let's review your progress and plan your day with real data from Gmail and Calendar.`
              : 'Connect your Google account to unlock personalized productivity features with real Gmail and Calendar data.'
            }
          </p>
        </section>

        {/* Google Connection Status - Simplified */}
        {isAuthenticated && (
          <section style={{ marginBottom: '24px' }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '16px',
              backgroundColor: '#f0fdf4',
              border: '1px solid #bbf7d0',
              borderRadius: '8px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div style={{
                  width: '8px',
                  height: '8px',
                  backgroundColor: '#10b981',
                  borderRadius: '50%'
                }}></div>
                <span style={{
                  fontSize: '14px',
                  fontWeight: '500',
                  color: '#166534'
                }}>Connected to Google</span>
              </div>
              <div style={{
                fontSize: '12px',
                color: '#16a34a'
              }}>Gmail & Calendar synced</div>
            </div>
          </section>
        )}

        {/* Development Panels removed for performance */}

        {/* Connection Prompt for Users Without Google Access */}
        <section style={{ marginBottom: '32px' }}>
          {!hasGoogleAccess ? (
            <GoogleAccountPrompt />
          ) : (
            <div style={{
              fontSize: '14px',
              color: '#16a34a'
            }}>✅ Google account connected</div>
          )}
        </section>

        {/* Sync Status for Users with Google Access */}
        {hasGoogleAccess && (
          <section style={{ marginBottom: '32px' }}>
            <SyncStatus compact={true} showDetails={false} />
          </section>
        )}

        {/* Voice Control - Primary Interface */}
        <section style={{ marginBottom: '32px' }}>
          <div style={{
            maxWidth: '672px',
            margin: '0 auto'
          }}>
            <VoiceControl
              onCommand={handleVoiceCommand}
              prominent={true}
            />
          </div>
        </section>

        {/* Daily Check-in */}
        {isAuthenticated && habits.length > 0 && (
          <section style={{ marginBottom: '32px' }}>
            <DailyCheckin habits={habits} onUpdate={invalidateCache} />
          </section>
        )}

        {/* Dashboard Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr',
          gap: '24px'
        }}>
          {/* Tasks Column */}
          <div>
            <TaskManager />
          </div>

          {/* Habits Column */}
          <div>
            <HabitTracker />
          </div>
        </div>

        {/* Today's Summary */}
        {hasGoogleAccess && (
          <section className="mt-8">
            <div className="bg-accent/50 rounded-lg p-6">
              <h2 className="text-lg font-semibold mb-4">Today's Summary</h2>
              {loadingData ? (
                <div className="space-y-3">
                  <div className="animate-pulse">
                    <div className="h-4 bg-muted rounded w-3/4 mb-2"></div>
                    <div className="h-4 bg-muted rounded w-1/2 mb-2"></div>
                    <div className="h-4 bg-muted rounded w-2/3 mb-2"></div>
                    <div className="h-4 bg-muted rounded w-1/2"></div>
                  </div>
                </div>
              ) : dashboardData ? (
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
                  <div className="text-center">
                    <div className="text-2xl font-bold">{dashboardData.tasks.completedToday}</div>
                    <div className="text-muted-foreground">Tasks Done</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">{dashboardData.habits.completedToday}</div>
                    <div className="text-muted-foreground">Habits Done</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">{dashboardData.calendar.todayEvents}</div>
                    <div className="text-muted-foreground">Meetings</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">{dashboardData.email.unreadCount}</div>
                    <div className="text-muted-foreground">Emails</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">{dashboardData.habits.longestStreak}</div>
                    <div className="text-muted-foreground">Best Streak</div>
                  </div>
                </div>
              ) : (
                <div className="text-sm text-muted-foreground">
                  Unable to load summary data
                </div>
              )}
            </div>
          </section>
        )}


        {/* Today's Focus Section */}
        {hasGoogleAccess && dashboardData && (
          <section className="mt-12 bg-primary/5 rounded-lg p-6">
            <h2 className="text-2xl font-semibold mb-6">Today's Focus</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <h3 className="font-medium text-primary mb-3 flex items-center gap-2">
                  🎯 Priority Tasks
                </h3>
                {dashboardData.tasks.highPriority > 0 ? (
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                      {dashboardData.tasks.highPriority} high priority task{dashboardData.tasks.highPriority !== 1 ? 's' : ''} remaining
                    </li>
                    <li className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                      {dashboardData.tasks.pending - dashboardData.tasks.highPriority} other task{(dashboardData.tasks.pending - dashboardData.tasks.highPriority) !== 1 ? 's' : ''} pending
                    </li>
                    <li className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      {dashboardData.tasks.completed} task{dashboardData.tasks.completed !== 1 ? 's' : ''} completed
                    </li>
                  </ul>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    {dashboardData.tasks.pending > 0
                      ? `${dashboardData.tasks.pending} task${dashboardData.tasks.pending !== 1 ? 's' : ''} pending`
                      : 'All caught up! 🎉'
                    }
                  </p>
                )}
              </div>

              <div>
                <h3 className="font-medium text-primary mb-3 flex items-center gap-2">
                  💪 Habits Progress
                </h3>
                {dashboardData.habits.currentStreaks.length > 0 ? (
                  <ul className="space-y-2 text-sm">
                    {dashboardData.habits.currentStreaks.slice(0, 3).map((habit, index) => (
                      <li key={index} className="flex items-center gap-2">
                        <span className="text-green-600">✓</span>
                        {habit.name} ({habit.streak} day streak)
                      </li>
                    ))}
                    {dashboardData.habits.total > dashboardData.habits.completedToday && (
                      <li className="flex items-center gap-2">
                        <span className="text-muted-foreground">○</span>
                        {dashboardData.habits.total - dashboardData.habits.completedToday} habit{(dashboardData.habits.total - dashboardData.habits.completedToday) !== 1 ? 's' : ''} remaining today
                      </li>
                    )}
                  </ul>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    {dashboardData.habits.total > 0
                      ? 'Start building your habits!'
                      : 'Create your first habit to get started'
                    }
                  </p>
                )}
              </div>

              <div>
                <h3 className="font-medium text-primary mb-3 flex items-center gap-2">
                  📅 Coming Up
                </h3>
                {dashboardData.calendar.upcomingEvents.length > 0 ? (
                  <ul className="space-y-2 text-sm">
                    {dashboardData.calendar.upcomingEvents.slice(0, 3).map((event, index) => (
                      <li key={index} className="flex items-center gap-2">
                        <span className="text-muted-foreground">
                          {new Date(event.startTime).toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </span>
                        <span className="truncate">{event.title}</span>
                      </li>
                    ))}
                    {dashboardData.calendar.weekEvents > 3 && (
                      <li className="text-xs text-muted-foreground">
                        +{dashboardData.calendar.weekEvents - 3} more this week
                      </li>
                    )}
                  </ul>
                ) : dashboardData.email.accounts > 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No upcoming events today
                  </p>
                ) : (
                  <div className="text-sm text-muted-foreground">
                    <p className="mb-2">Connect your Google Calendar to see upcoming events</p>
                    <button
                      onClick={() => window.location.href = '/settings'}
                      className="text-primary hover:underline"
                    >
                      Connect Calendar →
                    </button>
                  </div>
                )}
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  )
}