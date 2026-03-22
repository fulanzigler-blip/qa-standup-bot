-- Migration: Add review_status to weekly_reports
-- Implements ADR-1: Tasks share one review lifecycle per report submission

ALTER TABLE weekly_reports
ADD COLUMN IF NOT EXISTS review_status VARCHAR(20) NOT NULL DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

-- Index for faster lookup by user and week (ADR-2)
CREATE INDEX IF NOT EXISTS idx_weekly_reports_user_date
ON weekly_reports (user_id, report_date);
