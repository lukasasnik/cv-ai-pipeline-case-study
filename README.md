# CV AI Pipeline

A modular CV (curriculum vitae) processing pipeline built with FastAPI, Temporal, PostgreSQL, and React.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│   Frontend   │────▶│   API        │────▶│  File Server     │
│  React:3000  │     │ FastAPI:8002 │     │  FastAPI:8001    │
└─────────────┘     └──────┬───┬──┘     └─────────────────┘
                           │   │
                    ┌──────▼┐ ┌▼──────────┐
                    │  DB    │ │  Temporal   │
                    │PG:5433 │ │  gRPC:7233  │
                    └────────┘ │  UI:8080    │
                               └────────────┘
```

## Components

| Component | Technology | Port |
|---|---|---|
| **File Server** | FastAPI (Python) | 8001 |
| **API** | FastAPI (Python) | 8002 |
| **Worker** | Temporal Python SDK | — |
| **Database** | PostgreSQL 16 | 5433 |
| **Temporal** | temporalio/auto-setup | 7233 |
| **Temporal UI** | temporalio/ui | 8080 |
| **Frontend** | React + Vite + TypeScript | 3000 |

## Quick Start

```bash
# Start all services
docker compose up --build

# Access
# API:          http://localhost:8002
# Swagger Docs: http://localhost:8002/docs
# File Server:  http://localhost:8001
# Frontend:     http://localhost:3000
# Temporal UI:  http://localhost:8080
```

## Project Structure

```
├── docker-compose.yml      # Orchestrates all services
├── file-server/            # Standalone file storage microservice
├── api/                    # Main API + Temporal workflow definitions
├── database/               # PostgreSQL initialization scripts
└── frontend/               # React SPA
```
