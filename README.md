# CV AI Pipeline

> This case study is in its final state. It is still being improved, tuned, tested, and cleaned up, so it should not be treated as representative of the final code quality expected from its creator.

A modular CV processing pipeline built with FastAPI, Temporal, PostgreSQL, React, Docker Compose, Loki, and Grafana.

## Requirements

- Docker with Docker Compose support
- An OpenAI-compatible AI endpoint and token

## Running The App

Configure the AI connection before starting the stack. The Docker Compose services currently read these values from `docker-compose.yml` under both the `api` and `worker` services:

```yaml
AI_API_URL: "http://host.docker.internal:1234/v1"
AI_API_TOKEN: "YOUR_TOKEN"
AI_MODEL: "google/gemma-4-e4b"
```

Set `AI_API_URL` to your OpenAI-compatible base URL, `AI_API_TOKEN` to the token expected by that service, and `AI_MODEL` to a model name supported by that endpoint. For a local LM Studio-style server, `http://host.docker.internal:1234/v1` is the intended Docker-to-host URL.

Start everything from the repository root:

```bash
docker compose up --build
```

Useful URLs:

- Frontend: http://localhost:3001
- API: http://localhost:8002
- Swagger docs: http://localhost:8002/docs
- File server: http://localhost:8001
- Temporal UI: http://localhost:8080
- Grafana: http://localhost:3002
- Loki: http://localhost:3100

To run the pipeline:

1. Open the frontend at http://localhost:3001.
2. Upload a CV.
3. Open the CV detail view.
4. Click the process button.
5. Use the detail view, Temporal UI, logs, or Grafana/Loki to inspect progress and results.

## What It Does

The pipeline currently:

1. Uploads and stores a CV file.
2. Extracts text from the uploaded PDF.
3. Uses an LLM to extract structured CV information.
4. Runs deterministic heuristic generators:
   - seniority scoring
   - salary estimation
   - improvement recommendations
5. Uses an LLM to explain the generated analysis.
6. Stores every intermediate result as an execution artifact.

## Design Rationale

Docker was chosen so the case study can be started with one command and run consistently across machines.

Temporal was added to provide resilient workflows for the CV processing pipeline. The pipeline has multiple steps, external service calls, and generated artifacts, so modeling it as a workflow makes retries, failures, and future extension easier to reason about.

The observability stack uses Loki and Grafana to make debugging easier. This is especially useful because the pipeline spans multiple services and asynchronous workflow execution.

## Heuristic Analysis Rationale

The seniority score and salary estimation are intentionally heuristic rather than LLM-decided.

The structured CV extraction uses an LLM, but the later scoring and salary estimation are calculated deterministically from the extracted data. This was chosen to make the analysis explainable, repeatable, testable, and easier to tune. An LLM can be useful for extraction and explanation, but using it as the source of truth for scoring would make the output harder to validate and compare.

The seniority heuristic rewards:

- years of software engineering experience
- technical breadth
- leadership and ownership signals
- relevant education
- product and production experience
- public or market credibility signals

The salary heuristic uses the seniority score together with market-relevant signals such as high-value skills, company experience, technical breadth, production ownership, leadership, and public signals. It is a coarse estimate, not a compensation benchmark.

## Current Limitations

This project still needs significant improvement:

- The structured model is only validated syntactically, not semantically.
- Extracted structured data should go through semantic checks, correction, and possibly a correction loop.
- If automated correction fails, the pipeline should leave the result for human review.
- The final LLM explanation could also be produced as JSON and validated.
- The final response could use a retry/correction loop when syntactic or semantic errors are detected.
- The heuristics need further tuning against realistic examples.
- More validation checks could be implemented, such as CV size, file type, page count, and content sanity checks.
- More tests need to be added.
- Code structure needs cleanup and refactoring.
- Logging needs to be improved and made more consistent.
- Error handling and retry policies need more careful classification.

## Python Development

Python dependencies are managed with `uv` from the workspace root.

```bash
# Install/sync the API + worker environment
uv sync --project api

# Run API tests
cd api
uv run pytest

# Install/sync the file server environment
uv sync --project file-server

# Update the lockfile after changing Python dependencies
uv lock
```

## Components

| Component | Technology | Port |
|---|---|---|
| File Server | FastAPI (Python) | 8001 |
| API | FastAPI (Python) | 8002 |
| Worker | Temporal Python SDK | internal |
| Database | PostgreSQL 16 | 5433 |
| Temporal | temporalio/auto-setup | 7233 |
| Temporal UI | temporalio/ui | 8080 |
| Frontend | React + Vite + TypeScript | 3001 |
| Loki | grafana/loki | 3100 |
| Grafana | grafana/grafana | 3002 |

## Project Structure

```text
docker-compose.yml      # Orchestrates all services
file-server/            # Standalone file storage microservice
api/                    # Main API, domain logic, and Temporal workflow definitions
database/               # Database models and initialization scripts
frontend/               # React SPA
observability/          # Loki, Promtail, and Grafana configuration
shared/                 # Shared Python utilities and clients
```
