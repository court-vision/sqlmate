from sqlmate.backend.classes.queries.update import UpdateQuery
from sqlmate.backend.classes.queries.base import BaseQuery
from sqlmate.backend.classes.metadata import metadata
from typing import List


def generate_query(queries: List[BaseQuery], options: dict) -> str:
    query = ""

    select_clause = "SELECT "
    for table_query in queries:
        select_clause += f"{table_query.get_SELECT_clause(len(queries))},"
    select_clause = select_clause[:-1]
    query += select_clause + '\n'
    
    from_clause = "FROM "
    from_clause += queries[0].get_FROM_clause()
    query += from_clause + '\n'

    joined_tables: set[str] = {queries[0].table_name}
    join_parts: list[str] = []
    for table_query in queries[1:]:
        target = table_query.table_name
        if target in joined_tables:
            continue
        path = metadata.shortest_path_from_set(joined_tables, target)
        for table, edge in path:
            if table not in joined_tables:
                join_parts.append(f"JOIN {table} ON {edge}")
                joined_tables.add(table)
    query += " ".join(join_parts) + '\n' if join_parts else ""

    where_clause = "WHERE "
    for table_query in queries:
        where_clause += f"{table_query.get_WHERE_clause()}"
    if where_clause != "WHERE ":
        where_clause = where_clause[:-5]
        query += where_clause + '\n'

    group_by_clause = "GROUP BY "
    for table_query in queries:
        temp_group_by_clause = f"{table_query.get_GROUP_BY_clause()}"
        if temp_group_by_clause:
            group_by_clause += f"{temp_group_by_clause},"
    if group_by_clause != "GROUP BY ":
        group_by_clause = group_by_clause[:-1]
        query += group_by_clause + '\n'

    order_by_clause = "ORDER BY "
    if order_by_list := options.get("order_by"):
        for order_by in order_by_list:
            table_name, attr_name = order_by.get("table_name"), order_by.get("attribute")
            order_by_clause += f"{lookup_alias(attr_name, table_name, queries)} {order_by.get('sort')},"
    if order_by_clause != "ORDER BY ":
        order_by_clause = order_by_clause[:-1]
        query += order_by_clause + '\n'

    limit_clause = "LIMIT "
    if limit := options.get("limit"):
        limit_clause += f"{limit}"
        query += limit_clause + '\n'
    
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