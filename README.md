# SQLMate

A no-code, visual SQL query builder that abstracts database querying into a drag-and-drop interface. Users build multi-table queries without writing SQL — SQLMate automatically resolves foreign key relationships, generates JOIN clauses via BFS graph traversal, and executes the query against a connected relational database.

Originally developed as a university course project (CS411, UIUC — Team 006: 0.1xDevelopers). This fork is integrated into the Court Vision platform as a backend-only query service at `sqlmate-backend.courtvision.dev`, connected to the Court Vision PostgreSQL database instead of the original music dataset.

---

## What it does

- Drag tables from a sidebar panel onto a canvas workspace
- Select columns, add filter constraints, apply aggregations (SUM, COUNT, AVG, MIN, MAX), GROUP BY, ORDER BY, and LIMIT
- SQLMate generates the full SQL query with automatic multi-table JOINs
- Results display in a paginated table; export as CSV or save to your account
- Saved tables can be queried again, joined with other tables, and exported or deleted
- UPDATE operations are supported via a separate table update panel

---

## Tech stack

### Backend
| Technology | Purpose |
|---|---|
| Python 3.10+ | Runtime |
| FastAPI | REST API framework |
| SQLAlchemy 2.0 | Database ORM, connection pooling, schema introspection |
| Pydantic v2 | Request/response validation |
| PyJWT + bcrypt | Auth (legacy; see Auth section below) |
| Uvicorn | ASGI server |
| MySQL / PostgreSQL | Supported databases |

### Frontend

Removed. The Next.js client that used to live in `frontend/` is gone — see
"Frontend removal" below. SQLMate is now a backend-only service; its API is
consumed directly.

### Infrastructure
| Technology | Purpose |
|---|---|
| Docker + docker-compose | Containerized local dev and deployment |
| Railway.app | Backend hosting |

---

## Directory structure

```
sqlmate/
├── src/sqlmate/              # Python package (installed via pyproject.toml)
│   ├── backend/              # FastAPI application
│   │   ├── main.py           # App entry point, CORS, lifespan
│   │   ├── startup.py        # Schema introspection + db_schema.json generation
│   │   ├── routers/
│   │   │   ├── auth.py       # GET /auth/me (Clerk token verification)
│   │   │   ├── query.py      # POST /query (run visual query)
│   │   │   └── user_data.py  # GET/POST /users/* (saved tables)
│   │   ├── classes/
│   │   │   ├── database.py   # SQLAlchemyDB: connection pooling, metadata fetch
│   │   │   ├── metadata.py   # Metadata/graph class with BFS shortest-path JOIN resolver
│   │   │   └── queries/
│   │   │       ├── base.py   # BaseQuery: SELECT/FROM/JOIN/WHERE/GROUP BY/ORDER BY builders
│   │   │       └── update.py # UpdateQuery: UPDATE/SET/WHERE builders
│   │   └── utils/
│   │       ├── constants.py  # Env var loading (DB_*, CLERK_*, SQLMATE_*)
│   │       ├── generators.py # generate_query() — assembles final SQL from BaseQuery list
│   │       ├── clerk_auth.py # Clerk JWT verification dependency
│   │       └── serialization.py # Query result → Table response object
│   └── cli/                  # `sqlmate` CLI tool
│       ├── cli.py            # Commands: init, run, cleanup
│       └── setup/
│           ├── env_setup.py  # Interactive credential prompting, secrets.env creation
│           ├── db_setup.py   # DB init DDL, schema JSON generation, table selection
│           └── sql/          # DDL templates for MySQL and PostgreSQL
├── docker/
│   └── backend.Dockerfile    # Python 3.13-slim, installs package, runs uvicorn
├── docker-compose.yaml       # backend (8081) with a shared schema volume
├── pyproject.toml            # Python package config, CLI entry point
├── data/
│   ├── raw/                  # Original CSV datasets (Spotify/music — original project)
│   ├── processed/            # ETL output CSVs
│   └── worker.py             # Data preprocessing script (Spotify dataset → normalized CSVs)
└── TECHNICAL_SURVEY.md       # Architecture overview and design pattern docs
```

---

## How it works

### Graph-based JOIN resolution

At startup, `startup.py` introspects the connected database using SQLAlchemy's `information_schema` queries. It builds a `Metadata` object (`classes/metadata.py`) that represents all tables as nodes and foreign key relationships as directed edges. When a user queries multiple tables, `generate_query()` calls `metadata.shortest_path_from_set()` — a multi-source BFS — to find the minimal JOIN path between tables, automatically inserting intermediate tables if needed.

### Query generation pipeline

```
UI selections
  → serializeTablesForQuery() [queryService.tsx]
  → POST /query [QueryRequest JSON]
  → [BaseQuery()] per table [backend]
  → generate_query() → SQL string
  → read-only keyword check
  → SQLAlchemy execute
  → serialized Table response
  → ConsolePanel renders results
```

Generated SQL uses CTEs for tables with constraints (improves query planner performance), then builds SELECT → FROM → JOIN → WHERE → GROUP BY → ORDER BY → LIMIT in order.

### Schema introspection and filtering

On backend startup, the schema is written to `db_schema.json` and served at `GET /schema`, which API clients use to populate a table browser. You can restrict which tables are exposed using environment variables:

- `SQLMATE_ALLOWED_SCHEMAS` — comma-separated list of schemas to include (e.g., `nba,stats_s2`)
- `SQLMATE_BLOCKED_TABLES` — comma-separated list of tables to exclude
- Tables prefixed `u_` (user-created saved tables) are always excluded from the schema browser

---

## Setup and installation

### Prerequisites

- Python 3.10+
- Bun (or Node.js 18+)
- Docker and Docker Compose (for containerized run)
- A MySQL or PostgreSQL database

### Option 1: CLI + Docker (recommended)

The `sqlmate` CLI guides you through setup and then launches the app via Docker Compose.

```bash
# Install the Python package
pip install .

# Run interactive setup (prompts for DB credentials, writes ~/.sqlmate/secrets.env)
sqlmate init

# Start the app (builds and runs Docker containers)
sqlmate run

# Cleanup: removes the sqlmate schema/database SQLMate created
sqlmate cleanup
```

After `sqlmate run`, the API is available at http://localhost:8081.

### Option 2: Docker Compose directly

Copy and populate your environment variables, then run:

```bash
docker compose up --build
```

The `docker-compose.yaml` reads from environment variables (see Configuration below).

### Option 3: Manual local development

**Backend:**
```bash
cd src
pip install -e ..
# Set environment variables (see Configuration)
uvicorn sqlmate.backend.main:app --reload --port 8081
```

---

## Configuration

All configuration is via environment variables. In local development, the backend looks for `~/.sqlmate/secrets.env` (created by `sqlmate init`) or a `secrets.env` file in the working directory. In production/Docker, set these directly.

| Variable | Required | Default | Description |
|---|---|---|---|
| `DB_HOST` | Yes | — | Database host |
| `DB_USER` | Yes | — | Database user |
| `DB_PASS` | Yes | — | Database password |
| `DB_NAME` | Yes | — | Database name |
| `DB_PORT` | No | `3306` (MySQL) / `5432` (PG) | Database port |
| `DB_TYPE` | No | `mysql` | `mysql` or `postgresql` |
| `DB_SCHEMA` | No | `public` | PostgreSQL schema to introspect; use `*` for all schemas |
| `PORT` | No | `8080` | Backend server port |
| `CLERK_JWKS_URL` | Yes (fork) | — | Clerk JWKS endpoint for JWT verification |
| `CLERK_SECRET_KEY` | Yes (fork) | — | Clerk secret key |
| `SQLMATE_ALLOWED_SCHEMAS` | No | (all) | Comma-separated schemas to expose in the query builder |
| `SQLMATE_BLOCKED_TABLES` | No | (none) | Comma-separated tables to hide from users |
| `SQLMATE_SCHEMA_DIR` | No | `/app/schema` | Directory where `db_schema.json` is written |

---

## API endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/` | — | Health welcome message |
| `GET` | `/health` | — | Health check |
| `GET` | `/schema` | — | Returns `db_schema.json` (table/column list for clients) |
| `GET` | `/auth/me` | Clerk JWT | Returns authenticated user info |
| `POST` | `/query` | — | Executes a visual query; returns paginated result table |
| `GET` | `/users/get_tables` | Clerk JWT | Lists user's saved tables |
| `POST` | `/users/save_table` | Clerk JWT | Saves query result as a named table |
| `POST` | `/users/update_table` | Clerk JWT | Executes an UPDATE query on a saved table |
| `POST` | `/users/delete_tables` | Clerk JWT | Deletes one or more saved tables |

The `POST /query` endpoint enforces read-only access — it rejects any generated SQL containing `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `TRUNCATE`, `REPLACE`, `MERGE`, `GRANT`, or `REVOKE`.

---

## Key features

- **No SQL required**: full query construction through drag-and-drop, checkboxes, and dropdowns
- **Automatic JOIN resolution**: BFS on foreign key graph finds minimal join path between any tables
- **CTE-based filtering**: tables with WHERE constraints are materialized as CTEs before the main SELECT
- **Aggregations**: SUM, COUNT, AVG, MIN, MAX with GROUP BY support
- **Type-aware constraints**: string columns use LIKE/quoted comparisons; numeric columns use raw values
- **Column aliases**: rename any output column inline
- **ORDER BY priority**: multi-column ordering with ASC/DESC direction
- **LIMIT control**: configurable result size (max 1000)
- **CSV export**: download any result set
- **Saved tables**: persist query results as `u_{username}_{name}` tables; rejoin them with other tables in future queries
- **UPDATE interface**: modify saved table rows through the edit-table page
- **Multi-database support**: MySQL and PostgreSQL with unified SQLAlchemy layer
- **Schema filtering**: restrict exposed tables per deployment via env vars

---

## Data preprocessing (original project)

`data/worker.py` is a one-time ETL script that processes the original Spotify dataset used in the university project. It normalizes a flat CSV into three relational tables (tracks, albums, artists) with proper foreign key links, and writes them to `data/processed/`. This is not needed for the Court Vision fork.

---

## Fork notes

This is a fork of the original SQLMate project (CS411 Team 006, UIUC). Key differences from the original:

- **Authentication**: The original used a custom JWT + bcrypt auth system (`/auth/register`, `/auth/login`). This fork replaces it entirely with [Clerk](https://clerk.com) — the `verify_clerk_token` FastAPI dependency validates Clerk JWTs.
- **Database**: Connected to the Court Vision PostgreSQL database (NBA stats, player data) instead of the original Music database. `SQLMATE_ALLOWED_SCHEMAS=nba,stats_s2` restricts the query builder to relevant schemas.
- **CORS**: Extended to include `courtvision.dev` subdomains with an `allow_origin_regex`.
- **Deployment**: Backend hosted at `sqlmate-backend.courtvision.dev` (Railway).
- **Frontend removal**: the Next.js client under `frontend/` was deleted (see
  `docs/PRODUCTION_READINESS.md` item 8). Its `next.config.js` rewrote `/query`,
  `/schema`, `/users/*` and `/auth/*` straight through to `BACKEND_URL`, so
  deploying it anywhere would have re-opened a path to the backend that bypassed
  the credential boundary closed in item 3. Recover it from git history if a UI
  is ever wanted again — but re-audit those rewrites first.
- **Schema introspection**: Added `SQLMATE_ALLOWED_SCHEMAS` and `SQLMATE_BLOCKED_TABLES` env vars for fine-grained control over which tables are exposed.
- **PostgreSQL multi-schema support**: `DB_SCHEMA=*` mode introspects all user schemas; schema-qualified table names (e.g., `nba.players`) are handled throughout the query builder.
