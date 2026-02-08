from sqlmate.backend.utils.serialization import query_output_to_table
from sqlmate.backend.utils.clerk_auth import verify_clerk_token
from sqlmate.backend.utils.user_provisioning import get_or_create_sqlmate_user
from sqlmate.backend.utils.generators import generate_update_query
from sqlmate.backend.utils.db import get_timestamp, session_scope
from sqlmate.backend.utils.user_tables import save_user_table, drop_user_tables
from sqlmate.backend.classes.http import StatusResponse, Table, UpdateQueryParams
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmate.backend.classes.queries.update import UpdateQuery
from sqlmate.backend.classes.metadata import metadata


from typing import Any, Dict, List
from fastapi import APIRouter, Depends, status, Response
from pydantic import BaseModel

router = APIRouter()

# =============================== USER DATA ENDPOINTS ===============================

class SaveTableRequest(BaseModel):
	table_name: str
	query: str
class SaveTableResponse(BaseModel):
	details: StatusResponse
@router.post("/save_table", response_model=SaveTableResponse, status_code=status.HTTP_201_CREATED)
def save_table(req: SaveTableRequest, response: Response, current_user: dict = Depends(verify_clerk_token)):
	clerk_user_id = current_user.get("clerk_user_id")
	email = current_user.get("email")

	with session_scope("sqlmate") as session:
		user_id = get_or_create_sqlmate_user(session, clerk_user_id, email)

	# Use clerk_user_id as the "username" for table naming
	username = clerk_user_id

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

	created_at = get_timestamp()
	try:
		with session_scope("sqlmate") as session:
			save_user_table(session, user_id, username, table_name, created_at, query)
	except IntegrityError:
		response.status_code = status.HTTP_409_CONFLICT
		return SaveTableResponse(
			details=StatusResponse(
				status="warning",
				message="Table already exists"
			)
		)
	except (SQLAlchemyError, ValueError) as e:
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
def drop_table(req: DeleteTableRequest, response: Response, current_user: dict = Depends(verify_clerk_token)):
	clerk_user_id = current_user.get("clerk_user_id")
	email = current_user.get("email")

	with session_scope("sqlmate") as session:
		user_id = get_or_create_sqlmate_user(session, clerk_user_id, email)

	username = clerk_user_id

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

	try:
		with session_scope("sqlmate") as session:
			dropped = drop_user_tables(session, user_id, username, table_names)
	except SQLAlchemyError as e:
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
		deleted_tables=dropped
	)

class GetTablesReponse(BaseModel):
	details: StatusResponse
	tables: List[Dict[str, Any]] | None = None
@router.get("/get_tables", response_model=GetTablesReponse, status_code=status.HTTP_200_OK)
def get_tables(response: Response, current_user: dict = Depends(verify_clerk_token)) -> GetTablesReponse:
	clerk_user_id = current_user.get("clerk_user_id")
	email = current_user.get("email")

	with session_scope("sqlmate") as session:
		user_id = get_or_create_sqlmate_user(session, clerk_user_id, email)

	rows = []
	with session_scope("sqlmate") as session:
		try:
			result = session.execute(
				text("SELECT table_name, created_at FROM user_tables WHERE user_id = :user_id"),
				{"user_id": user_id}
			)
			rows = result.fetchall()
		except SQLAlchemyError as e:
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

	tables: List[Dict[str, Any]] = [{"table_name": row.table_name, "created_at": row.created_at} for row in rows]
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
def get_table_data(table_name: str, response: Response, current_user: dict = Depends(verify_clerk_token)) -> GetTableDataResponse:
	clerk_user_id = current_user.get("clerk_user_id")
	username = clerk_user_id

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
	with session_scope("sqlmate") as session:
		try:
			result = session.execute(text(query))
			rows = result.fetchall()
			if not rows and not result.keys():
				return GetTableDataResponse(
					status=StatusResponse(
						status="error",
						message="No data found"
					)
				)
			column_names = list(result.keys())
		except SQLAlchemyError as e:
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

	# Convert SQLAlchemy Row objects directly to tuples for query_output_to_table
	formatted_rows = [tuple(row) for row in rows]

	table = query_output_to_table(formatted_rows, column_names, query, 1)
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
def update(req: UpdateTableRequest, response: Response, current_user: dict = Depends(verify_clerk_token)):
	clerk_user_id = current_user.get("clerk_user_id")
	username = clerk_user_id

	# Guard: only allow updating u_ prefixed tables (user-owned tables)
	target_table = req.query_params.table
	if not target_table.startswith("u_"):
		response.status_code = status.HTTP_403_FORBIDDEN
		return UpdateTableResponse(
			status=StatusResponse(
				status="error",
				message="Can only update user-owned tables (u_ prefix)"
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

	if not query_body:
		return UpdateTableResponse(
			status=StatusResponse(
				status="error",
				message="Invalid query"
			)
		)

	try:
		with session_scope("sqlmate") as session:
			result = session.execute(text(query_body))
			# Get the number of affected rows from the result
			rows_affected = result.rowcount
	except SQLAlchemyError as e:
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
		rows_affected=rows_affected
	)
