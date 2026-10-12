\# AI PR Review Agent



An AI-assisted pull request review application built with React, TypeScript, FastAPI, MySQL, GitHub REST API integration, and retrieval-augmented generation (RAG).



\## Features



\- Retrieve pull request metadata and diffs from GitHub.

\- Detect selected code issues using deterministic checks.

\- Retrieve relevant coding-standard guidance using embeddings and Chroma.

\- Generate structured AI review findings using Groq.

\- Validate findings against added lines in a pull request diff.

\- Persist review records in MySQL.



The frontend currently provides a minimal startup screen. The review workflow is exposed through the backend API.



\## Technology Stack



\- Frontend: React, TypeScript, Vite

\- Backend: Python, FastAPI

\- Database: MySQL 8.4

\- AI: Groq API

\- Embeddings: FastEmbed

\- Vector store: Chroma

\- Database migrations: Alembic

\- Development environment: Docker Compose



\## Prerequisites



\- Docker Desktop with Docker Compose

\- A GitHub personal access token with read access to the repositories you want to review

\- A Groq API key



You do not need to install Python, Node.js, or MySQL directly on your host machine to run the Dockerized development setup.



\## Getting Started



\### 1. Clone the repository



```bash

git clone <your-repository-url>

cd ai-pr-review-agent

```



\### 2. Configure environment variables



Copy the example file:



\*\*PowerShell\*\*

```powershell

Copy-Item .env.example .env

```



Edit `.env` and provide your own credentials. Set strong, private database passwords as well.



Never commit `.env` or share API keys and access tokens.



\### 3. Build and start the application



```bash

docker compose up --build -d

```



\### 4. Apply database migrations



```bash

docker compose exec backend alembic upgrade head

```



\### 5. Open the application



\- Frontend: http://localhost:5173

\- Backend health: http://localhost:8000/health

\- Database health: http://localhost:8000/health/db

\- API documentation: http://localhost:8000/docs



\### 6. Run backend tests



```bash

docker compose exec backend python -m pytest -q tests

```



\## Useful Docker Commands



View container status:



```bash

docker compose ps

```



View logs:



```bash

docker compose logs --tail=100 backend frontend db

```



Stop the application:



```bash

docker compose down

```



The named MySQL and Chroma volumes persist when containers are stopped or recreated. `docker compose down -v` removes those volumes and their stored data; use it only when you intentionally want to delete that data.



\## Repository Structure



```text

backend/

&#x20; app/          API, integrations, services, and database code

&#x20; migrations/   Alembic database migrations

&#x20; tests/        Automated backend tests

&#x20; evaluation/   Synthetic pull request evaluation fixtures

frontend/       React + TypeScript application

knowledge/      Coding-standard documents for retrieval

docker-compose.yml

.env.example

```



\## Security Notes



\- Keep API credentials out of source control.

\- The GitHub integration is intended for read-only retrieval.

\- Review findings should be validated and assessed before being acted upon.

\- Do not use real secrets in test fixtures or evaluation data.



\## Development Status



This project is under active development. The frontend is a minimal initial screen, and additional UI and workflow functionality will be added incrementally.



