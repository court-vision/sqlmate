from collections import defaultdict, deque

from sqlalchemy import text
from sqlmate.backend.utils.constants import DB_NAME, DB_TYPE, DB_SCHEMA
from sqlmate.backend.utils.db import session_scope
from typing import List, Any

_is_postgres = DB_TYPE in ("postgresql", "postgres")
_schema_qualify = _is_postgres and DB_SCHEMA != "public"


class Edge:
	def __init__(self, source: str,  destination: str, source_column: str, destination_column: str) -> None:
		self.destination = destination
		self.source_column = f"{source}.{source_column}"
		self.destination_column = f"{destination}.{destination_column}"

	def __str__(self) -> str:
		return f"{self.source_column}={self.destination_column}"


# This class is used to manage the data types of the columns in the database.
class TableTypes:
	def __init__(self) -> None:
		self.types: dict[str, str] = {}

	def __str__(self) -> str:
		return "\n".join([f"{column}: {data_type}" for column, data_type in self.types.items()])

	def add(self, column: str, data_type: str) -> None:
		data_type = data_type.lower()
		if data_type in ["int", "integer", "bigint", "smallint", "tinyint", "serial"]:
			data_type = "INT"
		elif data_type in ["float", "double", "decimal", "numeric", "double precision", "real"] or data_type.startswith("decimal") or data_type.startswith("numeric"):
			data_type = "FLOAT"
		elif data_type in ["varchar", "character varying", "char", "text"] or data_type.startswith("varchar") or data_type.startswith("character"):
			data_type = "STR"
		elif data_type in ["datetime", "date", "timestamp", "timestamp without time zone", "timestamp with time zone"]:
			data_type = "DATE"
		elif data_type in ["boolean", "bool"]:
			data_type = "BOOL"

		self.types[column] = data_type

	def get(self, column: str) -> str:
		return self.types[column] if column in self.types else ""


# This class is used to manage the metadata of the database in the form of a graph.
# It fetches the foreign key relationships between tables to construct the graph.
class Metadata:
	def __init__(self) -> None:
		self.col_types: defaultdict[str, TableTypes] = defaultdict(TableTypes)
		self.graph: dict[str, List[Edge]] = defaultdict(list)
		self.get_col_types()
		self.generate_graph()

	def __str__(self) -> str:
		return "\n".join(
			[
				f"{table}: {', '.join([str(edge) for edge in edges])}"
				for table, edges in self.graph.items()
			]
		)

	def add_table(self, table_name: str) -> None:
		if _is_postgres:
			query = text("""
				SELECT column_name, data_type
				FROM information_schema.columns
				WHERE table_schema = 'sqlmate' AND table_name = :table_name;
			""")
		else:
			query = text("""
				SELECT COLUMN_NAME, DATA_TYPE
				FROM INFORMATION_SCHEMA.COLUMNS
				WHERE TABLE_SCHEMA = :db_name AND TABLE_NAME = :table_name;
			""")

		with session_scope("sqlmate") as session:
			result = session.execute(query, {"db_name": DB_NAME, "table_name": table_name})
			rows: Any = result.fetchall()
			for column, data_type in rows:
				self.col_types[table_name].add(column, data_type)

	def get_col_types(self) -> None:
		if _is_postgres:
			if DB_SCHEMA == "*":
				query = text("""
					SELECT table_schema, table_name, column_name, data_type
					FROM information_schema.columns
					WHERE table_schema = 'sqlmate'
						OR (table_schema NOT IN ('pg_catalog', 'information_schema', 'sqlmate')
							AND table_name NOT LIKE 'u_%')
					ORDER BY table_schema, table_name, ordinal_position;
				""")
				params: dict = {}
			else:
				query = text("""
					SELECT table_schema, table_name, column_name, data_type
					FROM information_schema.columns
					WHERE table_schema = 'sqlmate'
						OR (table_schema = :db_schema AND table_name NOT LIKE 'u_%')
					ORDER BY table_name, ordinal_position;
				""")
				params = {"db_schema": DB_SCHEMA}

			with session_scope("user") as session:
				result = session.execute(query, params)
				rows: Any = result.fetchall()
			for schema, table, column, data_type in rows:
				table_key = f"{schema}.{table}" if _schema_qualify and schema != "sqlmate" else table
				self.col_types[table_key].add(column, data_type)
		else:
			query = text("""
				SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
				FROM INFORMATION_SCHEMA.COLUMNS
				WHERE TABLE_SCHEMA = 'sqlmate'
					OR (TABLE_SCHEMA = :db_name AND TABLE_NAME NOT LIKE 'u_%')
				ORDER BY TABLE_NAME, ORDINAL_POSITION;
			""")
			params = {"db_name": DB_NAME}

			with session_scope("user") as session:
				result = session.execute(query, params)
				rows = result.fetchall()
			for table, column, data_type in rows:
				self.col_types[table].add(column, data_type)

	def generate_graph(self) -> None:
		if _is_postgres:
			if DB_SCHEMA == "*":
				tables_query = text("""
					SELECT table_schema, table_name
					FROM information_schema.tables
					WHERE table_schema NOT IN ('pg_catalog', 'information_schema', 'sqlmate')
						AND table_type = 'BASE TABLE';
				""")
				tables_params: dict = {}
			else:
				tables_query = text("""
					SELECT table_schema, table_name
					FROM information_schema.tables
					WHERE table_schema = :db_schema;
				""")
				tables_params = {"db_schema": DB_SCHEMA}

			with session_scope("user") as session:
				result = session.execute(tables_query, tables_params)
				rows: Any = result.fetchall()
				# Each row is (schema, table_name)
				table_entries = [(r[0], r[1]) for r in rows]

				for table_schema, table_name in table_entries:
					full_name = f"{table_schema}.{table_name}" if _schema_qualify else table_name

					fk_query = text("""
						SELECT
							kcu.column_name,
							ccu.table_schema AS referenced_table_schema,
							ccu.table_name AS referenced_table_name,
							ccu.column_name AS referenced_column_name
						FROM information_schema.table_constraints AS tc
						JOIN information_schema.key_column_usage AS kcu
							ON tc.constraint_name = kcu.constraint_name
							AND tc.table_schema = kcu.table_schema
						JOIN information_schema.constraint_column_usage AS ccu
							ON ccu.constraint_name = tc.constraint_name
							AND ccu.constraint_schema = tc.constraint_schema
						WHERE tc.constraint_type = 'FOREIGN KEY'
							AND tc.table_schema = :schema
							AND tc.table_name = :table_name;
					""")
					fk_result = session.execute(fk_query, {"schema": table_schema, "table_name": table_name})
					fk_rows: Any = fk_result.fetchall()

					for column, ref_schema, ref_table, ref_column in fk_rows:
						ref_full_name = f"{ref_schema}.{ref_table}" if _schema_qualify else ref_table
						self.graph[full_name].append(
							Edge(full_name, ref_full_name, column, ref_column)
						)
						self.graph[ref_full_name].append(
							Edge(ref_full_name, full_name, ref_column, column)
						)
		else:
			tables_query = text("""
				SELECT TABLE_NAME
				FROM INFORMATION_SCHEMA.TABLES
				WHERE TABLE_SCHEMA = :db_name;
			""")
			tables_params = {"db_name": DB_NAME}

			with session_scope("user") as session:
				result = session.execute(tables_query, tables_params)
				rows = result.fetchall()
				tables: List[str] = [table[0] for table in rows]

				for table in tables:
					fk_query = text("""
						SELECT
							kcu.COLUMN_NAME,
							kcu.REFERENCED_TABLE_NAME,
							kcu.REFERENCED_COLUMN_NAME
						FROM
							INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS kcu
						WHERE
							kcu.TABLE_SCHEMA = :db_name
							AND kcu.TABLE_NAME = :table_name
							AND kcu.REFERENCED_TABLE_NAME IS NOT NULL;
					""")
					fk_params: dict = {"db_name": DB_NAME, "table_name": table}

					fk_result = session.execute(fk_query, fk_params)
					fk_rows = fk_result.fetchall()

					for column, referenced_table, referenced_column in fk_rows:
						self.graph[table].append(
							Edge(table, referenced_table, column, referenced_column)
						)
						self.graph[referenced_table].append(
							Edge(referenced_table, table, referenced_column, column)
						)

	# Finds shortest path using BFS
	def shortest_path(self, source: str, destination: str) -> str:
		queue = deque([(source, "")])
		visited = set([source])

		while queue:
			node, clause = queue.popleft()
			if node == destination:
				return clause
			for edge in self.get_edges(node):
				if edge.destination not in visited:
					visited.add(edge.destination)
					queue.append((edge.destination, f'{clause}{"" if node == source else " "}JOIN {edge.destination} ON {str(edge)}'))

		raise ValueError(f"No path found between {source} and {destination}")

	def get_edge(self, source: str, destination: str) -> str:
		for edge in self.graph[source]:
			if edge.destination == destination:
				return str(edge)
		raise ValueError(f"No edge found between {source} and {destination}")

	def get_edges(self, source: str) -> List[Edge]:
		return self.graph[source]

	def get_type(self, table_name: str, column_name: str) -> str:
		return self.col_types[table_name].get(column_name)

metadata: Metadata = Metadata()
