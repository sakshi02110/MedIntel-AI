# MedIntel AI Database Schema

MedIntel AI uses Supabase PostgreSQL for persistent data storage.

## Tables

### 1. `users` (Managed by Supabase Auth)
- Handled automatically by Supabase GoTrue.

### 2. `uploaded_reports`
Stores metadata and structured analysis results for uploaded PDFs.
- `report_id` (UUID, PK)
- `user_id` (UUID, FK to auth.users)
- `report_name` (Text)
- `report_text` (Text) - Extracted PDF content
- `analysis_result` (JSONB) - Structured LLM output
- `upload_date` (Timestamptz)

### 3. `chat_sessions`
Groups RAG conversations by report.
- `session_id` (UUID, PK)
- `user_id` (UUID, FK to auth.users)
- `report_id` (UUID, FK to uploaded_reports)
- `session_name` (Text)
- `created_at` (Timestamptz)

### 4. `chat_messages`
Stores individual conversational turns.
- `id` (UUID, PK)
- `session_id` (UUID, FK to chat_sessions)
- `role` (Text) - 'user' or 'assistant'
- `message` (Text)
- `timestamp` (Timestamptz)

## Security
Row Level Security (RLS) is enabled on all tables, ensuring users can only access their own data via `auth.uid() = user_id`.
