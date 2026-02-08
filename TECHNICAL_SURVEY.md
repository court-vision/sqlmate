# SQLMate Technical Survey

## Project Overview

**SQLMate** is a web-based, no-code visual query builder that abstracts SQL complexity into an intuitive drag-and-drop interface. It enables non-technical users to construct multi-table database queries without writing SQL, automatically generating and executing queries based on visual selections.

---

## Problem Solved

- Eliminates the need for SQL knowledge when querying relational databases
- Automatically resolves table relationships and generates JOIN clauses using graph traversal algorithms
- Provides persistent storage for query results, enabling users to save and manage their data
- Supports both data retrieval (SELECT) and modification (UPDATE) operations through a visual interface

---

## Technology Stack

### Frontend
| Technology | Purpose |
|------------|---------|
| **Next.js 15** (App Router) | React framework with server-side rendering |
| **React 19** | UI component library |
| **TypeScript 5** | Type-safe JavaScript |
| **Tailwind CSS 4** | Utility-first styling |
| **Radix UI** | Accessible component primitives (Dialog, Dropdown, Tooltip, etc.) |
| **dnd-kit** | Drag-and-drop functionality |
| **react-resizable-panels** | Adjustable split-pane layout |
| **Vercel Analytics** | Usage tracking |

### Backend
| Technology | Purpose |
|------------|---------|
| **FastAPI** | High-performance Python API framework |
| **SQLAlchemy 2.0** | Database ORM and connection management |
| **Pydantic** | Request/response data validation |
| **PyJWT + bcrypt** | Authentication and password security |
| **Uvicorn** | ASGI server |

### Infrastructure
| Technology | Purpose |
|------------|---------|
| **Docker + docker-compose** | Containerized development/deployment |
| **Vercel** | Frontend hosting |
| **Railway.app** | Backend hosting |
| **MySQL** | Primary database (PostgreSQL-ready) |

---

## Architecture

### System Design
```
Frontend (Next.js)  →  API Layer (FastAPI)  →  Database Layer
     ↓                       ↓                      ↓
 Drag-Drop UI         Query Generation        SQLAlchemy ORM
 State Management     Authentication          Connection Pooling
 Result Display       User Management         Multi-DB Support
```

### Design Patterns Implemented

1. **Repository/DAO Pattern** - `SQLAlchemyDB` class encapsulates all database access with unified interface for MySQL/PostgreSQL

2. **Builder Pattern** - `BaseQuery` and `UpdateQuery` classes construct SQL incrementally through method chaining

3. **Metadata/Reflection Pattern** - Runtime database schema introspection builds graph representation of table relationships

4. **Service Layer Pattern** - Frontend services (`queryService`, `authService`) separate API calls from business logic

5. **Context Pattern** - `AuthContext` provides global authentication state with localStorage persistence

---

## Key Technical Features

### Graph-Based JOIN Resolution
- Builds directed graph from database foreign key relationships at startup
- Uses **Breadth-First Search (BFS)** to find shortest path between tables
- Automatically generates minimal JOIN clauses without user specification
- Enables intuitive multi-table queries through simple drag-and-drop

### Dynamic Query Generation Engine
```
UI Selections → QueryRequest (Pydantic) → BaseQuery Builder → SQL String → Execution → Serialized Response
```

**Supports:**
- Multi-table SELECT with automatic JOINs
- WHERE constraints with type-aware value formatting
- Aggregation functions (SUM, COUNT, AVG, MIN, MAX)
- GROUP BY and ORDER BY clauses
- Result pagination with LIMIT/OFFSET

### Type-Aware Constraint Processing
- Inspects column metadata for data types
- Automatically formats values (strings quoted, numbers raw)
- Supports operators: `=`, `!=`, `>`, `<`, `>=`, `<=`, `LIKE` with wildcards

### User Table Isolation (Multi-Tenancy)
- Saved tables prefixed: `u_{username}_{table_name}`
- Prevents cross-user data access at application level
- User tables automatically added to metadata graph for JOIN capability

### Authentication System
- JWT token-based authentication with configurable expiration
- bcrypt password hashing
- Protected API endpoints with token validation middleware
- Session persistence via localStorage with auto-validation on mount

---

## Frontend Components

| Component | Functionality |
|-----------|---------------|
| **StudioCanvas** | Main query builder workspace with drag-drop zones, table management, limit/order controls |
| **TablePanel** | Sidebar browser displaying available database tables as draggable items |
| **TableCustomizationPanel** | Column selection, filtering constraints, aggregations, aliases, GROUP BY |
| **ConsolePanel** | Query results display with tabs, pagination, CSV export, save functionality |
| **QueryResultTable** | Paginated data table with sortable columns and value truncation |
| **TableUpdatePanel** | Data mutation interface for UPDATE operations |

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/auth/register` | POST | User registration |
| `/auth/login` | POST | JWT token generation |
| `/auth/me` | GET | Retrieve authenticated user |
| `/query` | POST | Execute visual query |
| `/users/save_table` | POST | Persist query results as table |
| `/users/get_tables` | GET | List user's saved tables |
| `/users/update_table` | POST | Execute UPDATE queries |

---

## Data Flow

### Query Execution
1. User drags tables onto canvas, selects columns, adds filters
2. Frontend serializes selections into `QueryRequest` JSON
3. Backend validates and instantiates `BaseQuery` object
4. Query generator builds SQL (SELECT → FROM → JOIN → WHERE → GROUP BY → ORDER BY → LIMIT)
5. SQLAlchemy executes query against database
6. Results serialized and returned as JSON
7. Frontend renders in paginated table with export options

### Authentication
1. User registers/logs in via form
2. Backend hashes password (bcrypt), generates JWT
3. Token stored in localStorage, included in subsequent request headers
4. Backend validates token, extracts user ID for query scoping

---

## Database Schema

### User Management
```sql
users (id, username, password, email)
user_tables (id, user_id, table_name, created_at, query)
```

### Connection Pooling Configuration
- Pool size: 5 connections
- Max overflow: 10 connections
- Connection recycling: 30 minutes
- Pre-ping enabled for validation

---

## Security Measures

- JWT authentication with expiration
- bcrypt password hashing with salt
- Restrictive CORS (localhost + production domain only)
- SQL injection protection via SQLAlchemy parameterized queries
- Pydantic validation on all API inputs
- User isolation through table prefixing

---

## Deployment Configuration

### Production
- **Frontend**: Vercel (Next.js optimized hosting)
- **Backend**: Railway.app (Python/FastAPI)
- **Database**: Remote MySQL server

### Development
- Docker Compose with separate frontend/backend containers
- Environment variables via secrets file
- Next.js API rewrites proxy requests to backend

---

## Technical Highlights for Resume

**Graph Algorithms**: Implemented BFS-based shortest path algorithm for automatic foreign key relationship traversal, enabling intuitive multi-table query construction without manual JOIN specification.

**Full-Stack TypeScript/Python**: Built type-safe frontend with Next.js 15, React 19, and TypeScript; performant backend with FastAPI, SQLAlchemy, and Pydantic validation.

**Dynamic SQL Generation**: Designed query builder engine that transforms visual UI selections into optimized SQL with support for JOINs, aggregations, filtering, and sorting.

**Authentication & Multi-Tenancy**: Implemented JWT-based auth with bcrypt hashing and user-isolated table storage using prefixing strategy.

**Modern UI/UX**: Created drag-and-drop interface using dnd-kit with visual feedback, Radix UI components, and resizable panel layouts.

**Database Abstraction**: Built unified database layer supporting MySQL and PostgreSQL with connection pooling and automatic reconnection.

**Production Deployment**: Containerized application with Docker, deployed to Vercel (frontend) and Railway (backend) with environment-based configuration.
