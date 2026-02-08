from sqlalchemy import text
from sqlmate.backend.utils.serialization import query_output_to_table
from sqlmate.backend.utils.generators import generate_query
from sqlmate.backend.utils.db import get_timestamp, session_scope
from sqlmate.backend.classes.http import StatusResponse, Table, QueryParams
from sqlmate.backend.classes.queries.base import BaseQuery

from sqlalchemy.exc import SQLAlchemyError
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, status, Response
from pydantic import BaseModel

router = APIRouter()

# ================================= QUERY ENDPOINTS =================================

class QueryRequest(BaseModel):
	query_params: List[QueryParams]
	options: Optional[Dict[str, Any]] = None
class QueryResponse(BaseModel):
	status: StatusResponse
	table: Table | None = None
@router.post("", response_model=QueryResponse, status_code=status.HTTP_200_OK)
def run_query(req: QueryRequest, response: Response) -> QueryResponse:
	# Validate the input data
	try:
		if not req.query_params:
			raise ValueError("No query parameters provided")
		query: List[BaseQuery] = [BaseQuery(details) for details in req.query_params]
	except ValueError as e:
		print(e)
		response.status_code = status.HTTP_400_BAD_REQUEST
		return QueryResponse(
			status=StatusResponse(
				status="error",
				message=str(e)
			),
			table=None
		)


	query_body = generate_query(query, req.options or {})
	# with open("logs/query_log.txt", "w") as f:
	#     f.write(query_body)

	try:
		with session_scope("user") as session:
			result = session.execute(text(query_body))
			if result is None:
				# If there are no results, return an error
				print("No data found")
				response.status_code = status.HTTP_404_NOT_FOUND
				return QueryResponse(
					status=StatusResponse(
						status="error",
						message="No data found"
					),
					table=None
				)
			column_names = list(result.keys())
			rows: Any = result.fetchall()
	except SQLAlchemyError as e:
		print(e)
		response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
		return QueryResponse(
			status=StatusResponse(
				status="error",
				message="Failed to execute query"
			),
			table=None
		)

	table: Table = query_output_to_table(rows, column_names, query_body, len(query))
	table.created_at = get_timestamp()
	return QueryResponse(
		status=StatusResponse(
			status="success",
			message="Query executed successfully"
		),
		table=table
	)