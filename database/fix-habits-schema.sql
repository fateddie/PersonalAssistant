-- Fix habits table to work with text-based user_id like tasks table
-- Drop the foreign key constraint and change user_id to text

ALTER TABLE public.habits
  DROP CONSTRAINT IF EXISTS habits_user_id_fkey;

ALTER TABLE public.habits
  ALTER COLUMN user_id TYPE TEXT;

-- Update RLS policy for habits
DROP POLICY IF EXISTS "Users can manage own habits" ON public.habits;

CREATE POLICY "Users can manage own habits" ON public.habits
  FOR ALL USING (user_id = current_setting('app.current_user_id', true)::text);

-- Do the same for habit_entries
ALTER TABLE public.habit_entries
  DROP CONSTRAINT IF EXISTS habit_entries_user_id_fkey;

ALTER TABLE public.habit_entries
  ALTER COLUMN user_id TYPE TEXT;

DROP POLICY IF EXISTS "Users can manage own habit entries" ON public.habit_entries;

CREATE POLICY "Users can manage own habit entries" ON public.habit_entries
  FOR ALL USING (user_id = current_setting('app.current_user_id', true)::text);

-- Do the same for daily_checkins if it exists
ALTER TABLE public.daily_checkins
  DROP CONSTRAINT IF EXISTS daily_checkins_user_id_fkey;

-- user_id is already text in daily_checkins, just update the policy
DROP POLICY IF EXISTS "Users can manage own check-ins" ON public.daily_checkins;

CREATE POLICY "Users can manage own check-ins" ON public.daily_checkins
  FOR ALL USING (user_id = current_setting('app.current_user_id', true)::text);
