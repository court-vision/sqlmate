from collections import defaultdict, deque

from sqlalchemy import text
from sqlmate.backend.utils.constants import DB_NAME
from sqlmate.backend.utils.db import session_scope
from typing import List, Any


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
		if data_type in ["int", "bigint", "smallint", "tinyint"]:
			data_type = "INT"
		elif data_type in ["float", "double", "decimal"] or data_type.startswith("decimal"):
			data_type = "FLOAT"
		elif data_type == "varchar" or data_type.startswith("varchar"):
			data_type = "STR"
		elif data_type in ["datetime", "date"]:
			data_type = "DATE"
		elif data_type == "boolean":
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
		with session_scope("user") as cur:
			result = cur.execute(
				text("""
				SELECT COLUMN_NAME, DATA_TYPE
				FROM INFORMATION_SCHEMA.COLUMNS
				WHERE TABLE_SCHEMA = :db_name AND TABLE_NAME = :table_name;
				"""), {"db_name": DB_NAME, "table_name": table_name}
			)
			rows: Any = result.fetchall()
			for column, data_type in rows:
				self.col_types[table_name].add(column, data_type)
	
	def get_col_types(self) -> None:
		with session_scope("user") as cur:
			result = cur.execute(
				text("""
				SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
				FROM INFORMATION_SCHEMA.COLUMNS
				WHERE TABLE_SCHEMA = 'sqlmate'
					OR (TABLE_SCHEMA = :db_name AND TABLE_NAME NOT LIKE 'u_%')
				ORDER BY TABLE_NAME, ORDINAL_POSITION;
				"""),
				{"db_name": DB_NAME}
			)
		rows: Any = result.fetchall()
		for table, column, data_type in rows:
			if table == "u_mee_yessuh":
				print(column, data_type)
			self.col_types[table].add(column, data_type)

	def generate_graph(self) -> None:
		with session_scope("user") as cur:
			result = cur.execute(
				text("""
				SELECT TABLE_NAME
				FROM INFORMATION_SCHEMA.TABLES
				WHERE TABLE_SCHEMA = :db_name;
				"""), {"db_name": DB_NAME}
			)
		rows: Any = result.fetchall()
		tables: List[str] = [table[0] for table in rows]

		for table in tables:
			result = cur.execute(text("""
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
    		"""), {"db_name": DB_NAME, "table_name": table})
			metadata: Any = result.fetchall()

			for column, referenced_table, referenced_column in metadata:
				self.graph[table].append(
					Edge(table, referenced_table, column, referenced_column)
				)
				self.graph[referenced_table].append(
					Edge(referenced_table, table, referenced_column, column)
				)
	
    # Finds shortest path using DFS
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

with session_scope("user") as cur:
	metadata: Metadata = Metadata()
	# with open("logs/metadata.txt", "w") as f:
	# 		f.write(str(metadata))

"""tracks JOIN artists -> tracks JOIN track_artists ON ... JOIN artists ON ...

Node(tracks) --FK(tracks.id: track_artists.track_id)-> Node(track_artists) --FK(track_artists.artist_id: artists.id)-> Node(artists)

"""