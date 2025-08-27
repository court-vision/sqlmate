from sqlmate.backend.classes.http import Table

def query_output_to_table(query_output: list[tuple], column_names: list[str], query_body: str, num_tables: int) -> Table:
	if not query_output:
		return Table(
			query=query_body,
			created_at=None,  # This can be set to None as we don't have this information in the query output yet
			columns=column_names,
			rows=[]
		)
	
	# If the query is a single table query, we can remove the table name from the column names
	if num_tables == 1:
		cleaned_column_names = []
		for col_name in column_names:
			for i in range(len(col_name)):
				if col_name[i] == "_":
					cleaned_column_names.append(col_name[i + 1:])
					break
			else: # Executed if the for loop is not broken out of (even though it should be)
				cleaned_column_names.append(col_name)
		column_names = cleaned_column_names

	# Convert each row to a list
	rows = [
		[val for val in row] for row in query_output
	]

	# This is what the frontend expects to be able to deserialize into the table
	response: Table = Table(
		query=query_body,
		created_at=None,  # This can be set to None as we don't have this information in the query output yet
		columns=column_names,
		rows=rows
	)
	return response