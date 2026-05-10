-- Database initialization script for CV AI Pipeline
-- This runs automatically when the PostgreSQL container starts for the first time.

-- The database is created by the POSTGRES_DB env var in docker-compose.
-- This script sets up the initial schema.

-- Note: SQLAlchemy's Base.metadata.create_all() in the API handles table creation,
-- but this file serves as the canonical schema reference and can contain
-- any additional setup (extensions, roles, etc.).

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
