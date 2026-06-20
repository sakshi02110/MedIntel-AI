-- ============================================================
-- MedIntel AI – Database Schema (Supabase PostgreSQL)
-- Run this script in the Supabase SQL Editor.
-- ============================================================

-- 1. Create table for uploaded reports
CREATE TABLE public.uploaded_reports (
    report_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    report_name TEXT NOT NULL,
    report_text TEXT NOT NULL,
    analysis_result JSONB NOT NULL,
    upload_date TIMESTAMPTZ DEFAULT now()
);

-- Enable RLS for reports
ALTER TABLE public.uploaded_reports ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can only access their own reports"
ON public.uploaded_reports
FOR ALL
USING (auth.uid() = user_id);

-- 2. Create table for chat sessions
CREATE TABLE public.chat_sessions (
    session_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    report_id UUID REFERENCES public.uploaded_reports(report_id) ON DELETE CASCADE,
    session_name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Enable RLS for sessions
ALTER TABLE public.chat_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can only access their own sessions"
ON public.chat_sessions
FOR ALL
USING (auth.uid() = user_id);

-- 3. Create table for chat messages
CREATE TABLE public.chat_messages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID REFERENCES public.chat_sessions(session_id) ON DELETE CASCADE,
    role TEXT CHECK (role IN ('user', 'assistant')) NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT now()
);

-- Enable RLS for messages
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can access messages of their sessions"
ON public.chat_messages
FOR ALL
USING (
    session_id IN (
        SELECT session_id FROM public.chat_sessions WHERE user_id = auth.uid()
    )
);

-- Note: Ensure Supabase Auth is enabled for users.
