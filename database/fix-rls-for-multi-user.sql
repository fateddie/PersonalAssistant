-- Fix RLS policies to work with text-based user_id without Supabase Auth
-- This allows the app to use NextAuth with email-based user IDs

-- Disable RLS temporarily or make it permissive for authenticated API calls
-- Since we're using server-side API routes with NextAuth, we can trust the server

-- Option 1: Disable RLS (simpler, but less secure - only use if app is behind authentication)
ALTER TABLE public.habits DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.habit_entries DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.daily_checkins DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.tasks DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.notes DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.goals DISABLE ROW LEVEL SECURITY;

-- Option 2: Use Service Role on server (more secure)
-- This is already handled in the code by using SUPABASE_SERVICE_ROLE_KEY
-- No SQL changes needed, just update the database.ts to use service role

-- If you want to keep RLS enabled but make it work, use this approach:
-- ALTER TABLE public.habits ENABLE ROW LEVEL SECURITY;
-- DROP POLICY IF EXISTS "Service role can manage all habits" ON public.habits;
-- CREATE POLICY "Service role can manage all habits" ON public.habits
--   FOR ALL USING (true);
