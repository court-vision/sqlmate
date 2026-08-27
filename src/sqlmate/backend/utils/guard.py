"""
Input validation for the SQL generator.

This codebase builds SQL by string concatenation, so every value the client
sends -- table, attribute, operator, comparison value, LIMIT, sort direction --
reaches the query text directly. These helpers are the choke point that keeps
each of them to a shape that cannot change the statement's meaning.

They are defence in depth, not the primary control. The control that actually
bounds this surface is the database role: sqlmate must connect as a
least-privilege user with SELECT on the exposed analytics schemas only and no
access whatsoever to `usr.*`. Validation can be bypassed by a call site that
forgets to use it; a role grant cannot.

`quote_literal` assumes `standard_conforming_strings = on` (the PostgreSQL
default since 9.1), under which doubling a single quote is the complete escape.
"""

import re

from sqlmate.backend.utils.constants import (
    SQLMATE_ALLOWED_SCHEMAS,
    SQLMATE_BLOCKED_TABLES,
)


class UnsafeQuery(ValueError):
    """A client-supplied fragment that is not safe to interpolate."""


# Operators the query builder UI can emit. SUBSTRING/PREFIX/SUFFIX are
# pseudo-operators that Constraint rewrites into LIKE.
ALLOWED_OPERATORS = frozenset({
    "=", "!=", "<", "<=", ">", ">=", "LIKE", "SUBSTRING", "PREFIX", "SUFFIX",
})

ALLOWED_SORTS = frozenset({"ASC", "DESC"})

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
# Explicit [0-9], not \d: Python's \d also matches Unicode decimal digits
# such as "\u0661\u0662\u0663", which Postgres rejects as a syntax error.
_NUMERIC = re.compile(r"^-?[0-9]+(\.[0-9]+)?$")

DEFAULT_LIMIT = 1000
MAX_LIMIT = 10_000


def assert_identifier(name: str, what: str = "identifier") -> str:
    """A bare SQL identifier: letters, digits and underscores, not starting with a digit."""
    if not isinstance(name, str) or not _IDENTIFIER.match(name):
        raise UnsafeQuery(f"Invalid {what}: {name!r}")
    return name


def assert_table(table_name: str) -> str:
    """A `schema.table` the client is allowed to name, or a bare sqlmate-owned table.

    Unqualified names are the per-user saved tables (`u_<username>_<name>`),
    which live in the sqlmate schema. Qualified names must sit in an allowed
    schema -- this is the check the metadata loader never applied to queries,
    only to the table graph the UI is offered.
    """
    if not isinstance(table_name, str) or not table_name:
        raise UnsafeQuery("Missing table name")

    parts = table_name.split(".")
    if len(parts) == 1:
        assert_identifier(parts[0], "table name")
        schema, bare = None, parts[0]
    elif len(parts) == 2:
        schema, bare = parts
        assert_identifier(schema, "schema name")
        assert_identifier(bare, "table name")
    else:
        raise UnsafeQuery(f"Invalid table name: {table_name!r}")

    if bare in SQLMATE_BLOCKED_TABLES or table_name in SQLMATE_BLOCKED_TABLES:
        raise UnsafeQuery(f"Table is not available: {table_name}")

    if schema is not None and SQLMATE_ALLOWED_SCHEMAS:
        if schema not in SQLMATE_ALLOWED_SCHEMAS and schema != "sqlmate":
            raise UnsafeQuery(f"Schema is not available: {schema}")

    return table_name


def assert_operator(operator: str) -> str:
    if operator not in ALLOWED_OPERATORS:
        raise UnsafeQuery(f"Invalid operator: {operator!r}")
    return operator


def sort_direction(value: object) -> str:
    """Normalise a sort direction, defaulting to ASC rather than trusting the input."""
    candidate = str(value or "").strip().upper()
    if candidate not in ALLOWED_SORTS:
        raise UnsafeQuery(f"Invalid sort direction: {value!r}")
    return candidate


def safe_limit(value: object, default: int = DEFAULT_LIMIT, maximum: int = MAX_LIMIT) -> int:
    """Coerce LIMIT to a bounded positive integer.

    This was interpolated raw, so a string reached the statement verbatim. The
    cap also keeps a single request from pulling the whole database into memory.
    """
    if value is None:
        return default
    try:
        limit = int(value)
    except (TypeError, ValueError):
        raise UnsafeQuery(f"Invalid limit: {value!r}")
    if limit < 1:
        raise UnsafeQuery(f"Invalid limit: {value!r}")
    return min(limit, maximum)


def quote_literal(value: object) -> str:
    """Quote a string literal for interpolation. See the module docstring's caveat."""
    text = str(value)
    if "\x00" in text:
        raise UnsafeQuery("Null byte in comparison value")
    return "'" + text.replace("'", "''") + "'"


def safe_numeric(value: object) -> str:
    """A numeric literal safe to interpolate.

    Stricter than `str.isnumeric()`, which accepts non-ASCII digit forms such as
    "\u0661\u0662\u0663" -- those pass the check and then fail as a syntax
    error in Postgres. Also permits the leading sign and decimal point that
    `isnumeric()` rejects, so negative and fractional stats work.
    """
    text = str(value).strip()
    if not _NUMERIC.match(text):
        raise UnsafeQuery(f"Invalid numeric value: {value!r}")
    return text
