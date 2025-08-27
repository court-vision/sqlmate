from sqlmate.backend.utils.serialization import query_output_to_table
from sqlmate.backend.utils.auth import check_user
from sqlmate.backend.utils.generators import generate_update_query
from sqlmate.backend.utils.db import get_cursor, get_timestamp
from sqlmate.backend.classes.http import StatusResponse, Table, UpdateQueryParams
from sqlmate.backend.classes.queries.update import UpdateQuery
from sqlmate.backend.classes.metadata import metadata


from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Header, status, Response
from pydantic import BaseModel
import mysql.connector

router = APIRouter()

# =============================== USER DATA ENDPOINTS ===============================

class SaveTableRequest(BaseModel):
	table_name: str
	query: str
class SaveTableResponse(BaseModel):
	details: StatusResponse
@router.post("/save_table", response_model=SaveTableResponse, status_code=status.HTTP_201_CREATED)
def save_table(req: SaveTableRequest, response: Response, authorization: Optional[str] = Header(None)):
	# Check the authentication of the user
	user_id, username, error = check_user(authorization)
	if error:
		response.status_code = status.HTTP_401_UNAUTHORIZED
		return SaveTableResponse(
			details=StatusResponse(
				status="error",
				message=error
			)
		)

	table_name = req.table_name
	query = req.query

	if not table_name or not query:
		response.status_code = status.HTTP_400_BAD_REQUEST
		return SaveTableResponse(
			details=StatusResponse(
				status="error",
				message="Missing table name or query"
			)
		)
	
	
	# Execute the stored procedure to create the table (this checks if the table already exists as well)
	created_at = get_timestamp()
	with get_cursor() as cur:
		try:
			cur.callproc("save_user_table", [user_id, username, table_name, created_at, query])
		except mysql.connector.IntegrityError as e:
			print(e)
			response.status_code = status.HTTP_409_CONFLICT
			return SaveTableResponse(
				details=StatusResponse(
					status="warning",
					message="Table already exists"
				)
			)
		except mysql.connector.Error as e:
			print(e)
			response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
			return SaveTableResponse(
				details=StatusResponse(
					status="error",
					message="Failed to create table"
				)
			)
		
	# After we save the table, we need to update metadata to include the new table
	full_table_name = f"u_{username}_{table_name}"
	metadata.add_table(full_table_name)
		
	return SaveTableResponse(
		details=StatusResponse(
			status="success",
			message="Table saved successfully"
		)
	)

class DeleteTableRequest(BaseModel):
	table_names: list[str]
class DeleteTableResponse(BaseModel):
	details: StatusResponse
	deleted_tables: list[str] | None = None
@router.post("/delete_table", response_model=DeleteTableResponse, status_code=status.HTTP_200_OK)
def drop_table(req: DeleteTableRequest, response: Response, authorization: Optional[str] = Header(None)):
	# Check the authentication of the user
	user_id, _, error = check_user(authorization)
	if error:
		response.status_code = status.HTTP_401_UNAUTHORIZED
		return DeleteTableResponse(
			details=StatusResponse(
				status="error",
				message=error
			)
		)

	# We allow both a single table name and a list of table names, however we convert it to a list regardless for ease of processing
	temp = req.table_names
	if isinstance(temp, str) and temp:
		table_names = [temp]
	elif isinstance(temp, list):
		table_names = temp
	else:
		response.status_code = status.HTTP_400_BAD_REQUEST
		return DeleteTableResponse(
			details=StatusResponse(
				status="error",
				message="Invalid table names format"
			)
		)
	
	if not table_names:
		response.status_code = status.HTTP_400_BAD_REQUEST
		return DeleteTableResponse(
			details=StatusResponse(
				status="error",
				message="No table names provided"
			)
		)
	
	# Execute the query to delete the entries from the user_tables table, which triggers insertion into tables_to_drop
	with get_cursor("sqlmate") as cur:
		try:
			for table_name in table_names:
				if not table_name:
					response.status_code = status.HTTP_400_BAD_REQUEST
					return DeleteTableResponse(
						details=StatusResponse(
							status="error",
							message="Invalid table name"
						)
					)
				cur.execute("DELETE FROM user_tables WHERE user_id = %s AND table_name = %s", (user_id, table_name))
		except mysql.connector.Error as e:
			print(e)
			response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
			return DeleteTableResponse(
				details=StatusResponse(
					status="error",
					message="Failed to drop table"
				)
			)
	
	# Execute the stored procedure to drop the tables that were marked for deletion in the previous step
	with get_cursor("sqlmate") as cur:
		try:
			cur.callproc("process_tables_to_drop")
		except mysql.connector.Error as e:
			print(e)
			response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
			return DeleteTableResponse(
				details=StatusResponse(
					status="error",
					message="Failed to drop table"
				)
			)
	
	return DeleteTableResponse(
		details=StatusResponse(
			status="success",
			message="Table(s) dropped successfully"
		),
		deleted_tables=list(map(str, table_names))
	)

class GetTablesReponse(BaseModel):
	details: StatusResponse
	tables: List[Dict[str, Any]] | None = None
@router.get("/get_tables", response_model=GetTablesReponse, status_code=status.HTTP_200_OK)
def get_tables(response: Response, authorization: Optional[str] = Header(None)) -> GetTablesReponse:
	# Check the authentication of the user
	user_id, username, error = check_user(authorization)
	if error:
		response.status_code = status.HTTP_401_UNAUTHORIZED
		return GetTablesReponse(
			details=StatusResponse(
				status="error",
				message=error
			)
		)

	rows = []
	with get_cursor("sqlmate") as cur:
		try:
			cur.execute("SELECT table_name, created_at FROM user_tables WHERE user_id = %s", (user_id,))
			rows: List[Any] = cur.fetchall()
		except mysql.connector.Error as e:
			print(e)
			return GetTablesReponse(
				details=StatusResponse(
					status="error",
					message="Failed to get tables"
				)
			)
	if not rows:
		return GetTablesReponse(
			details=StatusResponse(
				status="warning",
				message="No tables found"
			)
		)
	
	tables: List[Dict[str, Any]] = [{"table_name": row[0], "created_at": row[1]} for row in rows]
	return GetTablesReponse(
		details=StatusResponse(
			status="success",
			message="Tables retrieved successfully"
		),
		tables=tables
	)

class GetTableDataResponse(BaseModel):
	status: StatusResponse
	table: Table | None = None
@router.get("/get_table_data", response_model=GetTableDataResponse, status_code=status.HTTP_200_OK)
def get_table_data(table_name: str, response: Response, authorization: Optional[str] = Header(None)) -> GetTableDataResponse:
	# Check the authentication of the user
	user_id, username, error = check_user(authorization)
	if error:
		response.status_code = status.HTTP_401_UNAUTHORIZED
		return GetTableDataResponse(
			status=StatusResponse(
				status="error",
				message=error
			)
		)
	
	if not table_name:
		response.status_code = status.HTTP_400_BAD_REQUEST
		return GetTableDataResponse(
			status=StatusResponse(
				status="error",
				message="Missing table name"
			)
		)
	
	formatted_table_name = f"u_{username}_{table_name}"
	query = f"SELECT * FROM {formatted_table_name};"
	with get_cursor("sqlmate") as cur:
		try:
			cur.execute(query)
			rows: List[Any] = cur.fetchall()
			if cur.description is None:
				return GetTableDataResponse(
					status=StatusResponse(
						status="error",
						message="No data found"
					)
				)
			column_names: List[str] = [i[0] for i in cur.description]
		except mysql.connector.Error as e:
			print(e)
			response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
			return GetTableDataResponse(
				status=StatusResponse(
					status="error",
					message="Failed to get table data"
				)
			)
	if not rows:
		response.status_code = status.HTTP_404_NOT_FOUND
		return GetTableDataResponse(
			status=StatusResponse(
				status="success",
				message="No data found"
			)
		)
	
	table = query_output_to_table(rows, column_names, query, 1)
	table.created_at = get_timestamp()
	return GetTableDataResponse(
		status=StatusResponse(
			status="success",
			message="Table data retrieved successfully"
		),
		table=table
	)

class UpdateTableRequest(BaseModel):
	query_params: UpdateQueryParams
class UpdateTableResponse(BaseModel):
	status: StatusResponse
	rows_affected: int | None = None
@router.post("/update_table", response_model=UpdateTableResponse, status_code=status.HTTP_200_OK)
def update(req: UpdateTableRequest, response: Response, authorization: Optional[str] = Header(None)):
	# Check the authentication of the user
	user_id, username, error = check_user(authorization)
	if error:
		response.status_code = status.HTTP_401_UNAUTHORIZED
		return UpdateTableResponse(
			status=StatusResponse(
				status="error",
				message="UNAUTHORIZED:" + error
			)
		)
	
	print(f"User {username} is updating a table with query: {req.query_params}")

	# Validate the input data
	try:
		query = UpdateQuery(req.query_params, username)
	except ValueError as e:
		print("Here:", e)
		return UpdateTableResponse(
			status=StatusResponse(
				status="error",
				message=str(e)
			)
		)


	query_body = generate_update_query(query)
	# with open("logs/update_log.txt", "w") as f:
	#     f.write(query_body)

	if not query_body:
		return UpdateTableResponse(
			status=StatusResponse(
				status="error",
				message="Invalid query"
			)
		)
	
	try:
		with get_cursor("sqlmate") as cursor:
			cursor.execute(query_body)
			result = cursor.rowcount
	except mysql.connector.Error as e:
		print(e)
		return UpdateTableResponse(
			status=StatusResponse(
				status="error",
				message="Failed to update table"
			)
		)

	return UpdateTableResponse(
		status=StatusResponse(
			status="success",
			message="Table updated successfully"
		),
		rows_affected=result
	)