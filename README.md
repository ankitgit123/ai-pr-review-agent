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



### Step 2 — GitHub integration

**Implemented and verified**
- Read-only GitHub PR metadata and diff retrieval.
- Anonymous access to public pull requests.
- Validation of PR numbers and owner/repository path segments.
- Controlled handling of GitHub HTTP errors, timeouts, and connection failures.
- Diff truncation at 100,000 characters, with a truncation indicator.
- FastAPI route tests for successful responses, errors, invalid PR numbers, and oversized diffs.

**Validation**
- GitHub client tests: 14 passed.
- GitHub API route tests: 4 passed.
- Full backend test suite: 54 passed.

**Known limitation**
- GitHub client errors currently map to HTTP 502 at the API route.
- Authenticated requests require a valid GitHub token; public repository reads can work without one.


### Step 3 — Deterministic review

**Implemented and verified**
- Detects added `console.log()` statements in JavaScript and TypeScript file extensions.
- Reports rule ID, severity, file path, added line number, and evidence.
- Ignores removed statements and matching text on unchanged lines.
- Excludes unsupported file types such as CSS.
- Reports multiple matching lines independently.
- Uses a summary that does not claim the code is bug-free when no deterministic findings exist.

**Validation**
- Deterministic review tests: 15 passed.
- Full backend test suite: 69 passed.

**Known limitation**
- The current deterministic engine implements one rule (`JS001`). It is a debugging-pattern check, not a general-purpose bug detector.


### Step 4 — RAG retrieval and evidence handoff

**Implemented and verified**
- Markdown document ingestion and heading-aware chunking.
- Embedding generation and Chroma vector search.
- Multi-query retrieval, deduplication, similarity ranking, and configurable result limits.
- Preservation of source, section, content, similarity, and matched-query metadata.
- Empty retrieval handling and retrieval parameter validation.
- Retrieved policy evidence passed to the LLM and preserved in the workflow result.
- Empty evidence remains explicit rather than being represented as policy support.
- LLM findings are independently validated against the pull-request diff, with validation results reported separately.

**Validation**
- RAG-focused tests: 25 passed.
- Workflow tests: 7 passed.
- Full backend suite: 77 passed.

**Known limitation**
- Retrieval quality depends on the available coding standards and query generation. Retrieved evidence does not by itself prove a finding is correct.

### Step 5 — Groq structured output and error handling

**Implemented and verified**
- Groq integration using the configured model.
- Structured responses validated against `LLMReviewResult`.
- Required finding fields and allowed severity/classification values enforced by Pydantic.
- Controlled fallback retry for Groq's specific `json_validate_failed` response.
- Invalid policy citations rejected.
- Missing API credentials fail explicitly.
- Automated regression tests cover malformed structured responses, selective retry, fallback failure, and missing credentials.

**Validation**
- LLM regression tests: 9 passed.
- Full backend test suite: 82 passed.
- Real Groq smoke test: successful.
- Synthetic null-dereference diff: one structured finding returned with added-line evidence and no unsupported policy citations.

**Known limitation**
- A successful model response does not guarantee finding correctness or line-number accuracy. These require independent validation and representative review-quality evaluation.


### Step 5 — Groq structured output and error handling

**Implemented**
- Groq model integration with Pydantic-validated structured output.
- Controlled fallback retry for the specific `json_validate_failed` response.
- Policy citation validation against retrieved evidence.
- Explicit handling of missing Groq credentials.
- Controlled HTTP error responses for GitHub failures, AI-provider authentication/API failures, rate limits, and unexpected workflow errors.
- Independent validation of LLM findings against changed files, added lines, and quoted evidence.
- Validation reports preserve validity status and error details separately from original LLM findings.

**Validation**
- LLM regression tests: 9 passed.
- Real Groq smoke test: successful; one potential null-safety finding returned.
- Full backend suite: 86 passed, subject to the latest rerun.

**Known limitations**
- A valid structured response is not proof that a finding is correct.
- Frontend presentation and human-approval enforcement for invalid findings remain future work.
- Review quality still requires representative evaluation cases.


## Backend Validation and AI Review Evaluation

### Automated Tests

The backend test suite covers the main application components, including:

- GitHub API client and read-only integration
- Pull request review workflow
- Deterministic review rules
- LLM structured output and policy citation validation
- Finding validation against changed files, added lines, and quoted evidence
- Document ingestion, embeddings, and retrieval
- API route error handling

Run the backend tests:

```bash
docker compose exec backend pytest -q
```

**Latest verified result:** 97 tests passed.

### LLM Evaluation

A small synthetic evaluation dataset is maintained in `backend/evaluation/`.

It currently includes six pull-request diff scenarios:

1. CSS layering policy concern
2. JavaScript null dereference
3. TypeScript asynchronous error-handling regression
4. Python authorization regression
5. SQL tenant-isolation regression
6. Harmless JavaScript refactor

Run the evaluation:

```bash
docker compose exec backend python -m evaluation.run_evaluation
```

The runner saves a JSON report under `backend/evaluation/reports/`. Reports include per-case execution status, model findings, retrieved policy evidence, finding-validation results, and timing information.

**Latest verified result:** 6 of 6 cases completed; 0 execution failures.

Successful execution does not guarantee that every finding is correct. Evaluation results must also be reviewed for false positives, missed issues, duplicate findings, severity calibration, evidence accuracy, and unsupported conclusions.

The dataset is an initial regression-checking baseline, not a statistically representative benchmark. Its expected labels and scenarios should be refined as the reviewer evolves.

### Finding Validation and Safety

LLM-generated findings are validated independently against the supplied pull-request diff. Validation checks whether the reported file is changed, the quoted evidence matches an added line, and the reported line number points to that added line.

Validation results are returned separately from the original model findings. An invalid finding is not silently treated as a confirmed bug.

The GitHub integration is read-only. The application does not automatically post review comments, approve pull requests, or merge changes.


## Implemented Features

### 1. GitHub Pull Request Integration

- Fetch pull request metadata using the GitHub REST API.
- Retrieve pull request diffs using read-only requests.
- Support optional GitHub personal access token configuration.
- Validate repository identifiers and pull request numbers.
- Handle GitHub request failures with clear application errors.
- Truncate oversized diffs to a maximum of 100,000 characters.
- No automatic GitHub comments, approvals, or merges.

### 2. Pull Request Review Workflow

The review workflow combines deterministic checks, retrieval-augmented generation (RAG), LLM analysis, and independent finding validation.

1. Fetch pull request metadata and diff from GitHub.
2. Run deterministic review rules.
3. Generate queries for relevant coding standards.
4. Retrieve and rank relevant policy evidence.
5. Ask the LLM to produce structured review findings.
6. Validate findings against the actual added lines in the diff.
7. Return the findings, policy evidence, and validation results.

### 3. Deterministic Code Review

- Detect newly added `console.log()` statements in JavaScript and TypeScript files.
- Report the rule identifier, severity, category, file, line number, evidence, and summary.
- Inspect added lines rather than treating removed code as newly introduced code.

The deterministic engine currently implements a limited set of rules. No findings does not mean that a pull request is bug-free.

### 4. LLM-Powered Review

- Integrate Groq using LangChain's `ChatGroq`.
- Configure the model through environment variables.
- Use temperature 0 for review generation.
- Request structured output using a Pydantic schema.
- Include the pull request title, branches, diff, and retrieved policy evidence.
- Classify findings as `evidence_backed` or `uncertain`.
- Include severity, category, explanation, exact code evidence, file path, line number, and policy citations.
- Retry once with a simplified prompt for the specific structured-output JSON validation error.
- Validate policy citations against the retrieved evidence.

### 5. RAG and Coding-Standard Retrieval

- Load Markdown coding standards recursively from the knowledge directory.
- Split documents into heading-aware chunks.
- Generate embeddings using FastEmbed with `BAAI/bge-small-en-v1.5`.
- Store and retrieve chunks using ChromaDB with cosine-distance ranking.
- Generate multiple search queries from the pull request diff.
- Deduplicate retrieved chunks and retain their best similarity scores.
- Preserve source filenames, section paths, and matched queries for traceability.
- Supply retrieved policy evidence to the LLM during review.

### 6. Finding Validation and Safety

- Verify that a finding refers to a changed file.
- Verify that quoted evidence matches an added source line.
- Verify that the reported line number is an added line in the diff.
- Return validation errors for unsupported findings.
- Preserve the original LLM output separately from its validation status.
- Treat code diffs and retrieved policy content as untrusted input in the review prompt.
- Avoid treating a policy deviation alone as proof of a functional bug.
- Keep GitHub integration read-only.

**Important:** A finding that passes diff validation has supported file, line, and evidence references. This does not independently prove that the underlying issue is a real bug.

### 7. Backend API

The FastAPI backend currently exposes:

| Endpoint | Purpose |
|---|---|
| `GET /health` | Check application health |
| `GET /health/db` | Check MySQL connectivity |
| `GET /api/github/pull-requests/{owner}/{repository}/{pull_request_number}` | Fetch PR metadata and diff |
| `POST /api/review-workflow/{owner}/{repository}/{pull_request_number}` | Execute the review workflow |
| `POST /api/reviews` | Create a persisted review record |
| `GET /api/reviews` | List persisted review records |
| `GET /api/reviews/{review_id}` | Retrieve a persisted review record |

The review workflow endpoint currently executes the review and returns its results. The persistence endpoints are separate; do not assume the workflow automatically saves every review.

### 8. Database and Infrastructure

- FastAPI backend and React + TypeScript + Vite frontend.
- MySQL 8.4 database.
- SQLAlchemy for database access.
- Alembic for schema migrations.
- Docker Compose for local development.
- ChromaDB persistent storage through a Docker named volume.
- Local environment configuration through `.env`.
- `.env.example` for documenting required environment variables without committing secrets.
- Docker-based backend test execution.

### 9. Evaluation Dataset

A small synthetic evaluation dataset is maintained under `backend/evaluation/`.

It contains six pull request diff fixtures:

| Case | Expected behavior |
|---|---|
| CSS layering | No confirmed bug; a policy concern may remain |
| JavaScript null dereference | Detect a potential runtime bug |
| TypeScript async error handling | Identify a conditional regression |
| Python authorization | Identify a potential security issue |
| SQL tenant isolation | Identify a potential data-isolation issue |
| Harmless refactor | Return no findings |

Run the evaluation suite with:

```powershell
docker compose exec backend python -m evaluation.run_evaluation
```

The runner records per-case status, duration, review results, policy evidence, finding validations, and errors in a JSON report under `backend/evaluation/reports/`.

Evaluation reports are generated artifacts and should not be confused with the source fixtures or automated unit tests.

### 10. Automated Tests

The backend test suite covers:

- GitHub client request behavior and error handling.
- GitHub API routes.
- Pull request workflow orchestration.
- Deterministic review rules.
- LLM structured review and policy-citation validation.
- Finding validation against unified diffs.
- Document loading and chunking.
- Embedding behavior.
- Query generation.
- Retrieval and result deduplication.
- Evaluation dataset and workflow-related behavior.

Run all backend tests:

```powershell
docker compose exec backend pytest -q
```

Run a focused test module:

```powershell
docker compose exec backend pytest -q tests/test_finding_validation_service.py
```

### 11. Latest Verification Results

**Last verified: 13 October 2026**

- Backend automated tests: **97 passed**.
- Evaluation cases completed: **6/6**.
- Evaluation execution failures: **0/6**.
- TypeScript async-error fixture: one finding, reported at line 2, with validation passing.
- Harmless refactor fixture: zero findings.
- Groq smoke test: successfully returned a structured review result in the latest successful run.

These are results from the recorded local runs, not a guarantee of future model behavior. LLM findings can still be incomplete, duplicated, overly confident, or incorrect.

### 12. Current Scope and Next Steps

The current implementation focuses on the backend review pipeline and its verification.

Planned next steps:

- Build the React pull request review interface.
- Display deterministic and LLM findings, severity, source evidence, policy citations, and validation status.
- Add clearer handling for invalid or uncertain findings.
- Expand the synthetic evaluation dataset gradually with carefully selected cases.
- Evaluate precision, missed findings, duplicate findings, and false positives as reliable expected labels become available.
- Improve real-world accuracy using additional verified test cases.

The project does not currently include automatic GitHub review comments, approval or merge operations, model fine-tuning, or a dedicated large-scale evaluation platform.


