-- Least-privilege database roles for sqlmate.
--
-- Run as a superuser against the Court Vision database:
--
--   psql "$SUPERUSER_URL" -f ops/roles.sql
--
-- Adjust :db_name below if the database is not named `railway`. Passwords are
-- prompted for at the end -- this file contains no secrets and is safe to commit.
--
-- Why two roles: routers/query.py is the only caller of session_scope("user"),
-- and it is the endpoint that executes client-authored SQL. Everything else
-- (saved tables) uses session_scope("sqlmate"). Splitting them lets the
-- arbitrary-query connection be READ ONLY at the database level, so even a
-- perfect injection through the string-concatenating generator cannot write.
--
-- This is the control that actually bounds this service. The validation in
-- utils/guard.py is defence in depth: a future call site can forget to validate,
-- but it cannot escape a role grant.

\set db_name railway

-- ---------------------------------------------------------------------------
-- 1. sqlmate_query -- runs client-authored SELECTs. Read-only, analytics only.
-- ---------------------------------------------------------------------------
-- Password is set below with \password, which prompts with hidden input and
-- issues the ALTER ROLE itself -- so it never appears in this file, in shell
-- history, or in the server log.
CREATE ROLE sqlmate_query LOGIN;

GRANT CONNECT ON DATABASE :db_name TO sqlmate_query;

GRANT USAGE ON SCHEMA nba, stats_s2 TO sqlmate_query;
GRANT SELECT ON ALL TABLES IN SCHEMA nba, stats_s2 TO sqlmate_query;
-- New pipeline tables should be readable without re-granting.
ALTER DEFAULT PRIVILEGES IN SCHEMA nba, stats_s2 GRANT SELECT ON TABLES TO sqlmate_query;

-- Saved user tables live in the sqlmate schema and must be readable back.
GRANT USAGE ON SCHEMA sqlmate TO sqlmate_query;
GRANT SELECT ON ALL TABLES IN SCHEMA sqlmate TO sqlmate_query;
ALTER DEFAULT PRIVILEGES IN SCHEMA sqlmate GRANT SELECT ON TABLES TO sqlmate_query;

-- Belt and braces: usr.* holds provider credentials and emails. Nothing in
-- sqlmate has any business there. (Not granted by default; stated explicitly so
-- the intent survives a future blanket GRANT.)
REVOKE ALL ON SCHEMA usr FROM sqlmate_query;
REVOKE ALL ON ALL TABLES IN SCHEMA usr FROM sqlmate_query;

-- Enforced by Postgres, not by application code.
ALTER ROLE sqlmate_query SET default_transaction_read_only = on;
ALTER ROLE sqlmate_query SET statement_timeout = '15s';
ALTER ROLE sqlmate_query SET idle_in_transaction_session_timeout = '30s';

-- ---------------------------------------------------------------------------
-- 2. sqlmate_app -- saved tables. Writes, but only inside the sqlmate schema.
-- ---------------------------------------------------------------------------
CREATE ROLE sqlmate_app LOGIN;

GRANT CONNECT ON DATABASE :db_name TO sqlmate_app;

-- CREATE TABLE ... AS <query> reads the analytics schemas and writes to sqlmate.
GRANT USAGE ON SCHEMA nba, stats_s2 TO sqlmate_app;
GRANT SELECT ON ALL TABLES IN SCHEMA nba, stats_s2 TO sqlmate_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA nba, stats_s2 GRANT SELECT ON TABLES TO sqlmate_app;

-- startup.py runs `CREATE SCHEMA IF NOT EXISTS sqlmate` on every boot, and
-- Postgres checks CREATE on the *database* before evaluating IF NOT EXISTS --
-- so without this the service crashes at startup even though the schema already
-- exists. sqlmate_query deliberately does NOT get this.
GRANT CREATE ON DATABASE :db_name TO sqlmate_app;

GRANT USAGE, CREATE ON SCHEMA sqlmate TO sqlmate_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA sqlmate TO sqlmate_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA sqlmate
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sqlmate_app;

REVOKE ALL ON SCHEMA usr FROM sqlmate_app;
REVOKE ALL ON ALL TABLES IN SCHEMA usr FROM sqlmate_app;

ALTER ROLE sqlmate_app SET statement_timeout = '30s';
ALTER ROLE sqlmate_app SET idle_in_transaction_session_timeout = '30s';

-- ---------------------------------------------------------------------------
-- 3. Close the default-public hole (PostgreSQL 14 and earlier grant CREATE on
--    schema public to PUBLIC, which every role inherits).
-- ---------------------------------------------------------------------------
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

-- ---------------------------------------------------------------------------
-- 4. Set the passwords. \password prompts twice with hidden input and issues
--    ALTER ROLE ... PASSWORD itself, correctly escaped.
--
--    Put the same two values in the Railway variables:
--      DB_QUERY_USER=sqlmate_query   DB_QUERY_PASS=<the first password>
--      DB_APP_USER=sqlmate_app       DB_APP_PASS=<the second password>
--
--    Until all four are set, utils/db.py falls back to DB_USER/DB_PASS, which is
--    still the superuser -- so setting them is what completes the fix.
-- ---------------------------------------------------------------------------
\password sqlmate_query
\password sqlmate_app

-- ---------------------------------------------------------------------------
-- 5. Verify. Both queries should return zero rows.
-- ---------------------------------------------------------------------------
-- Any grant outside the intended schemas:
SELECT grantee, table_schema, table_name, privilege_type
FROM information_schema.role_table_grants
WHERE grantee IN ('sqlmate_query', 'sqlmate_app')
  AND table_schema NOT IN ('nba', 'stats_s2', 'sqlmate');

-- Direct reachability of the credential table:
SELECT has_table_privilege('sqlmate_query', 'usr.teams', 'SELECT') AS query_can_read_teams,
       has_table_privilege('sqlmate_app',   'usr.teams', 'SELECT') AS app_can_read_teams;
