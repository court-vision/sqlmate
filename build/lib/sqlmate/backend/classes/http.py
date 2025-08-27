from pydantic import BaseModel
from typing import Optional, Literal, List, Any, Dict

class StatusResponse(BaseModel):
	status: Literal['success', 'error', 'warning']
	message: Optional[str] = None
	code: Optional[int] = None

class Table(BaseModel):
	query: str
	created_at: Optional[str] = None
	columns: List[str] = []
	rows: List[Any] = []

class QueryParams(BaseModel):
	table: str
	attributes: List[Dict[Literal['attribute', 'alias'], str]]
	constraints: Optional[List[Dict[Literal['attribute', 'operator', 'value'], str]]] = None
	group_by: Optional[List[str]] = None
	aggregations: Optional[List[Dict[Literal['attribute', 'type'], str]]] = None

	def get(self, key: str, default=None) -> Any:
		"""Get a value from the query parameters."""
		return getattr(self, key, default)

class UpdateQueryParams(BaseModel):
	table: str
	updates: List[Dict[Literal['attribute', 'value'], str]]
	constraints: List[Dict[Literal['attribute', 'operator', 'value'], str]]

	def get(self, key: str, default=None) -> Any:
		"""Get a value from the query parameters."""
		return getattr(self, key, default)