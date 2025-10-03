/**
 * Supabase JWT Generation
 *
 * This module creates valid Supabase JWTs from NextAuth sessions
 * to enable proper Row Level Security with Supabase + NextAuth
 */

import jwt from 'jsonwebtoken'
import { createClient } from '@supabase/supabase-js'

/**
 * Generate a Supabase-compatible JWT from user info
 * This JWT will work with Supabase RLS policies using auth.uid() and auth.jwt()
 */
export function generateSupabaseJWT(userId: string, email: string): string {
  const jwtSecret = process.env.SUPABASE_JWT_SECRET

  if (!jwtSecret) {
    throw new Error('SUPABASE_JWT_SECRET is not configured. Get it from Supabase Dashboard > Project Settings > API > JWT Secret')
  }

  const payload = {
    aud: 'authenticated',
    exp: Math.floor(Date.now() / 1000) + 60 * 60, // 1 hour from now
    sub: userId,
    email: email,
    role: 'authenticated',
    aal: 'aal1', // Authentication Assurance Level
    session_id: `${Date.now()}-${userId}` // Unique session identifier
  }

  return jwt.sign(payload, jwtSecret)
}

/**
 * Create or get Supabase Auth user
 * Syncs NextAuth user with Supabase Auth to enable proper RLS
 */
export async function ensureSupabaseUser(email: string, name?: string): Promise<string> {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
  const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY!

  // Create admin client with service role
  const supabase = createClient(supabaseUrl, supabaseServiceKey, {
    auth: {
      autoRefreshToken: false,
      persistSession: false
    }
  })

  // Check if user exists in Supabase Auth
  const { data: existingUsers } = await supabase.auth.admin.listUsers()
  const existingUser = existingUsers?.users?.find(u => u.email === email)

  if (existingUser) {
    return existingUser.id
  }

  // Create new user in Supabase Auth
  const { data: newUser, error } = await supabase.auth.admin.createUser({
    email,
    email_confirm: true, // Auto-confirm since they're authenticated via Google
    user_metadata: {
      name: name || email.split('@')[0],
      provider: 'google'
    }
  })

  if (error) {
    console.error('Error creating Supabase user:', error)
    throw error
  }

  if (!newUser.user) {
    throw new Error('Failed to create Supabase user')
  }

  return newUser.user.id
}

/**
 * Create Supabase client with authenticated session
 * Use this instead of the basic client to get RLS working
 */
export function createAuthenticatedSupabaseClient(supabaseJWT: string) {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

  const client = createClient(supabaseUrl, supabaseAnonKey)

  // Set the session with our custom JWT
  client.auth.setSession({
    access_token: supabaseJWT,
    refresh_token: 'dummy-refresh-token' // Not used in this flow
  })

  return client
}
