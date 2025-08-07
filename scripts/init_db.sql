-- Database initialization script for English Teacher Bot
-- This script runs automatically when PostgreSQL container starts

-- Ensure UTF8 encoding
ALTER DATABASE english_teacher_bot_db SET timezone TO 'UTC';

-- Create extension for UUID generation (if needed in future)
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Log initialization
\echo 'English Teacher Bot database initialized successfully!'
