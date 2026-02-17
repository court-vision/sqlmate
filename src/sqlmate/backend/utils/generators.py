from sqlmate.backend.classes.queries.update import UpdateQuery
from sqlmate.backend.classes.queries.base import BaseQuery
from sqlmate.backend.classes.metadata import metadata
from typing import List


def _cte_alias(table_name: str) -> str:
    """Generate a CTE alias from a table name. e.g., 'nba.players' -> 'cte_nba_players'."""
    return "cte_" + table_name.replace(".", "_")


def _remap_table(table_name: str, name_map: dict[str, str]) -> str:
    """Remap a table name using the CTE name map, or return it unchanged."""
    return name_map.get(table_name, table_name)


def _remap_columns(sql: str, name_map: dict[str, str]) -> str:
    """Remap all table.column references in a SQL fragment using the CTE name map.

    Replaces 'original_table.' with 'cte_alias.' throughout the string.
    Safe because column aliases use '_' separators (e.g., nba_players_name)
    while table references use '.' (e.g., nba.players.name), so aliases are
    never accidentally matched.
    """
    for original in sorted(name_map, key=len, reverse=True):
        sql = sql.replace(original + ".", name_map[original] + ".")
    return sql


def generate_query(queries: List[BaseQuery], options: dict) -> str:
    query = ""
    name_map: dict[str, str] = {}

    # --- CTEs for tables with constraints ---
    cte_parts: list[str] = []
    for table_query in queries:
        if table_query.constraints:
            alias = _cte_alias(table_query.table_name)
            name_map[table_query.table_name] = alias
            where_body = table_query.get_WHERE_clause()[:-5]  # strip trailing " AND "
            cte_parts.append(
                f"{alias} AS (\n    SELECT * FROM {table_query.table_name} WHERE {where_body}\n)"
            )
    if cte_parts:
        query += "WITH " + ",\n".join(cte_parts) + "\n"

    # --- SELECT ---
    select_clause = "SELECT "
    for table_query in queries:
        select_clause += f"{table_query.get_SELECT_clause(len(queries))},"
    select_clause = select_clause[:-1]
    query += _remap_columns(select_clause, name_map) + '\n'

    # --- FROM ---
    query += f"FROM {_remap_table(queries[0].table_name, name_map)}\n"

    # --- JOIN ---
    joined_tables: set[str] = {queries[0].table_name}
    join_parts: list[str] = []
    for table_query in queries[1:]:
        target = table_query.table_name
        if target in joined_tables:
            continue
        path = metadata.shortest_path_from_set(joined_tables, target)
        for table, edge in path:
            if table not in joined_tables:
                on_lhs = _remap_columns(edge.source_column, name_map)
                on_rhs = _remap_columns(edge.destination_column, name_map)
                join_parts.append(f"JOIN {_remap_table(table, name_map)} ON {on_lhs}={on_rhs}")
                joined_tables.add(table)
    query += " ".join(join_parts) + '\n' if join_parts else ""

    # --- WHERE (only for tables whose constraints are NOT in a CTE) ---
    where_clause = "WHERE "
    for table_query in queries:
        if table_query.table_name not in name_map:
            where_clause += table_query.get_WHERE_clause()
    if where_clause != "WHERE ":
        where_clause = where_clause[:-5]
        query += where_clause + '\n'

    # --- GROUP BY ---
    group_by_clause = "GROUP BY "
    for table_query in queries:
        temp_group_by_clause = table_query.get_GROUP_BY_clause()
        if temp_group_by_clause:
            group_by_clause += f"{temp_group_by_clause},"
    if group_by_clause != "GROUP BY ":
        group_by_clause = group_by_clause[:-1]
        query += _remap_columns(group_by_clause, name_map) + '\n'

    # --- ORDER BY ---
    order_by_clause = "ORDER BY "
    if order_by_list := options.get("order_by"):
        for order_by in order_by_list:
            table_name, attr_name = order_by.get("table_name"), order_by.get("attribute")
            order_by_clause += f"{lookup_alias(attr_name, table_name, queries)} {order_by.get('sort')},"
    if order_by_clause != "ORDER BY ":
        order_by_clause = order_by_clause[:-1]
        query += order_by_clause + '\n'

    # --- LIMIT ---
    if limit := options.get("limit"):
        query += f"LIMIT {limit}\n"

    return query

def generate_update_query(query: UpdateQuery):
    update_query = ""

    update_clause = "UPDATE " + query.get_UPDATE_clause()
    update_query += update_clause + '\n'

    set_clause = "SET " + query.get_SET_clause()
    update_query += set_clause + '\n'

    where_clause = "WHERE " + query.get_WHERE_clause()
    if where_clause != "WHERE ":
        where_clause = where_clause[:-5]
        update_query += where_clause
    
    update_query += ";"

    return update_query

def lookup_alias(attr_name: str, table_name: str, queries: List[BaseQuery]) -> str:
    for query in queries:
        if query.table_name == table_name:
            print(query.alias_map)
            return query.alias_map.get(f'{table_name}.{attr_name}', attr_name)
    return attr_name