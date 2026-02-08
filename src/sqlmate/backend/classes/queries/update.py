from sqlmate.backend.classes.metadata import metadata
from sqlmate.backend.classes.queries.base import BaseQuery
from sqlmate.backend.classes.http import UpdateQueryParams
from typing import List, Any

# Update query class
class UpdateQuery(BaseQuery):
    def __init__(self, input: UpdateQueryParams, username: str) -> None:
        super().__init__(input, username)
        self.updates: List[Update] = [Update(details, self.table_name) for details in input.updates or []]
        
    def get_UPDATE_clause(self) -> str:
        return self.table_name

    def get_SET_clause(self) -> str:
        clause = ""
        for constraint in self.updates:
            clause += f"{constraint.attribute}={constraint.value},"
        clause = clause[:-1]

        return clause

class Update:
    def __init__(self, input: dict, table_name: str) -> None:
        self.table_name: str = table_name
        self.attribute: str = f'{table_name}.{input.get("attribute", "")}'
        self.value: str = self.process_value(input.get("value", ""))

    def process_value(self, value: Any) -> str:
        *table_parts, attribute_name = self.attribute.split(".")
        table_name = ".".join(table_parts)
        db_type = metadata.get_type(table_name, attribute_name)
        print(table_name, attribute_name)
        print("DB_TYPE:", db_type)
        if db_type in ["STR", "DATE"] :
            return f"'{str(value)}'"
        # db_type in ["INT", "BOOL", "FLOAT"]
        else:
            if str(value).isnumeric():
                return str(value)
            else:
                raise ValueError(f"Invalid value for update on {self.attribute}: {value}")
    
    def __str__(self) -> str:
        return f"""
            (
                'attribute': {self.attribute},
                'value': {self.value}
            )
        """