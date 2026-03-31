-- Migration: Add Squads and Reminder System
-- Created: Backend Agent
-- Description: Adds tables to support squads, membership, and reminder idempotency.

BEGIN;

-- Create squads table
CREATE TABLE IF NOT EXISTS squads (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    telegram_chat_id BIGINT, -- Nullable to support squads without a shared channel
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create squad_members table
CREATE TABLE IF NOT EXISTS squad_members (
    id SERIAL PRIMARY KEY,
    squad_id INTEGER NOT NULL REFERENCES squads(id) ON DELETE CASCADE,
    telegram_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(squad_id, telegram_id) -- A user can only belong to a squad once
);

-- Create reminder_log table
CREATE TABLE IF NOT EXISTS reminder_log (
    id SERIAL PRIMARY KEY,
    squad_id INTEGER NOT NULL REFERENCES squads(id) ON DELETE CASCADE,
    week_date DATE NOT NULL, -- ISO Monday of the week
    reminded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reminded_by_telegram_id BIGINT NOT NULL, -- Who triggered the reminder
    UNIQUE(squad_id, week_date) -- Idempotency: one reminder per squad per week
);

-- Indexes for performance
CREATE INDEX idx_squad_members_squad_id ON squad_members(squad_id);
CREATE INDEX idx_squad_members_telegram_id ON squad_members(telegram_id);
CREATE INDEX idx_reminder_log_week ON reminder_log(week_date);

COMMIT;
